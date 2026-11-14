"""Second line of defence (PRD M10, M11): change-stream detector + compensation worker.

The gate stops a burst on its own (G4/G5/G6 inside the transaction). The detector watches every
approval after commit and suspends a reviewer when:
  - rate:    >= rate_max approvals within rate_window_ms           (PRD rule)
  - median:  median active dwell of the last median_n < the floor  (PRD rule)
  - cusum:   the reviewer's own review-time stream has shifted down (calibrated CUSUM, pg/cusum.py)
The resume token is saved after every event; on restart the stream resumes from it.
"""
from __future__ import annotations

import math
import statistics
import threading
import time
from datetime import datetime, timedelta

from pymongo.errors import DuplicateKeyError, OperationFailure, PyMongoError

from pg import gate
from pg import observability as obs
from pg.cusum import Cusum, HonestModel, SelfCusum, SelfCusumState
from pg.db import get_db, now
from pg.stats import floor_cluster
from pg.target import compensate

STATE_ID = "rubber_stamp_detector"
PIPELINE = [{"$match": {"operationType": "insert", "ns.coll": "approvals"}},
            {"$project": {"_id": 1, "operationType": 1, "fullDocument.tenant_id": 1, "fullDocument.reviewer_id": 1,
                          "fullDocument.proposal_id": 1, "fullDocument.approval_id": 1, "fullDocument.active_dwell_ms": 1,
                          "fullDocument.created_at": 1, "fullDocument.attestation_id": 1}}]  # ship only what handle() reads


def cusum_for(policy: dict):
    """Default mode 'self' (each reviewer vs their own baseline: catches drift, spares fast honest reviewers).
    Mode 'population' (vs the honest population) is kept for the trade-off analysis only: in simulation it
    suspends every consistently fast honest reviewer."""
    c = policy.get("detector", {}).get("cusum")
    if not c:
        return None
    if c.get("mode", "self") == "self":
        return SelfCusum(c["sigma"], c.get("drop", math.log(2)), c["h"], c.get("warmup", 5))
    return Cusum(HonestModel(c["mu0"], c["sigma"]), c["shift_to_s"], c["h"])


def _scaled(policy: dict, ms: int) -> float:
    return max(ms, 1) / 1000 * policy.get("detector", {}).get("time_scale", 1)


def _rate_and_median(db, tenant: str, reviewer_id: str, policy: dict) -> tuple[str, dict] | None:
    """Rate and median rules. Both are index-bounded: count over (tenant, reviewer, created_at) window, and the last
    `median_n` approvals via the same index. O(log N + w + median_n), independent of how long the reviewer has worked."""
    r = policy["rules"]
    t = now()
    n = db.approvals.count_documents({"tenant_id": tenant, "reviewer_id": reviewer_id,
                                      "created_at": {"$gte": t - timedelta(milliseconds=r["rate_window_ms"])}})
    if n >= r["rate_max_approvals"]:
        return "RATE", {"count": n, "window_ms": r["rate_window_ms"]}
    last = [a["active_dwell_ms"] for a in db.approvals.find({"tenant_id": tenant, "reviewer_id": reviewer_id},
                                                            {"active_dwell_ms": 1}).sort("created_at", -1).limit(r["median_n"])]
    if len(last) >= r["median_n"] and statistics.median(last) < r["min_active_dwell_ms"]:
        return "MEDIAN_DWELL", {"median_dwell_ms": statistics.median(last), "n": len(last)}
    return None


def _history(db, tenant: str, reviewer_id: str):
    """The reviewer's approvals oldest-first, streamed from the (tenant, reviewer, created_at) index: O(N) time, O(1) memory.
    The CUSUM baseline is the reviewer's FIRST approvals, so a rebuild must start at the beginning, not at a recent window."""
    return db.approvals.find({"tenant_id": tenant, "reviewer_id": reviewer_id},
                             {"active_dwell_ms": 1, "created_at": 1, "approval_id": 1}).sort("created_at", 1)


def check_reviewer(db, tenant: str, reviewer_id: str, policy: dict) -> tuple[str, dict] | None:
    """BATCH check: replays the reviewer's whole history. O(N). Used for catch-up after downtime and as the reference
    the streaming detector is tested against. The per-event path is `check_streaming` (O(1))."""
    hit = _rate_and_median(db, tenant, reviewer_id, policy)
    if hit:
        return hit
    c = cusum_for(policy)
    if c is not None:
        dwells = [_scaled(policy, a["active_dwell_ms"]) for a in _history(db, tenant, reviewer_id)]
        at = c.run(dwells)
        if at is not None:
            return "CUSUM", {"approvals_seen": len(dwells), "alarm_at": at, "h": c.h,
                             "mode": "self" if isinstance(c, SelfCusum) else "population"}
    return None


def check_streaming(db, tenant: str, reviewer_id: str, ap: dict, policy: dict) -> tuple[str, dict] | None:
    """Per-event check in O(1) CUSUM work. The reviewer's CUSUM state lives in its own document `reviewer_stats`
    (never in `reviewer_state`: bumping that version would make the detector conflict with live gate transactions).

    Idempotent across restarts: an event at or before (last_created_at, last_approval_id) is not counted twice.
    A missing state document is rebuilt once from history (O(W)), then updated incrementally."""
    hit = _rate_and_median(db, tenant, reviewer_id, policy)
    if hit:
        return hit
    c = cusum_for(policy)
    if c is None:
        return None
    if not isinstance(c, SelfCusum):  # population mode is the trade-off analysis only; use the batch path
        return check_reviewer(db, tenant, reviewer_id, policy)
    sid = f"{tenant}|{reviewer_id}"
    for _ in range(6):  # optimistic: if another detector wrote first, re-read and redo (no lost or backwards update)
        doc = db.reviewer_stats.find_one({"_id": sid})
        if doc is None:
            state, last = SelfCusumState(c.sigma, c.drop, c.h, c.warmup), (None, None)
            for a in _history(db, tenant, reviewer_id):
                state.push(_scaled(policy, a["active_dwell_ms"]))
                key = (a["created_at"], a["approval_id"])
                last = key if last[0] is None or key > last else last  # MAX, not last-seen: approvals tied on the same
                # millisecond arrive in arbitrary order, and the replay guard compares against this exact key
            fresh = {**state.to_doc(), "tenant_id": tenant, "reviewer_id": reviewer_id,
                     "last_created_at": last[0], "last_approval_id": last[1], "ver": 1}
            try:
                db.reviewer_stats.insert_one({"_id": sid, **fresh})
            except DuplicateKeyError:
                continue
        else:
            state = SelfCusumState.from_doc(doc, c.sigma, c.drop, c.h, c.warmup)
            last = (doc.get("last_created_at"), doc.get("last_approval_id"))
            if last[0] is not None and (ap["created_at"], ap["approval_id"]) <= last:
                break  # already counted (restart replay)
            state.push(_scaled(policy, ap["active_dwell_ms"]))
            r = db.reviewer_stats.update_one(
                {"_id": sid, "ver": doc.get("ver", 1)},
                {"$set": {**state.to_doc(), "last_created_at": ap["created_at"], "last_approval_id": ap["approval_id"]},
                 "$inc": {"ver": 1}})
            if r.matched_count == 0:
                continue
        break
    if state.alarm_at is not None:
        return "CUSUM", {"approvals_seen": state.n, "alarm_at": state.alarm_at, "h": c.h, "mode": "self"}
    return None


def flag_attestation(db, ap: dict) -> None:
    """Voice evidence is flagged for the examiner, NEVER used to suspend (no calibration data; STT outages must not suspend)."""
    if not ap.get("attestation_id"):
        return
    a = db.attestations.find_one({"tenant_id": ap["tenant_id"], "attestation_id": ap["attestation_id"]})
    if not a:
        return
    sc = a["score"]
    flags = [f for f, hit in (("BOILERPLATE", sc["boilerplate"] >= 0.8), ("UNVIEWED_EVIDENCE_NAMED", bool(sc.get("unviewed_hits"))),
                              ("PACE_IMPLAUSIBLE", sc["pace"].get("plausible") is False)) if hit]
    if flags:
        db.attestations.update_one({"_id": a["_id"]}, {"$set": {"flags": flags}})
        obs.CLOSER_EVENTS.labels("voice_flag").inc()


def flag_floor_clustering(db, tenant: str, reviewer_id: str, policy: dict) -> None:
    """Record an examiner flag when approvals bunch just above the floor (pg.stats.floor_cluster). Never suspends.
    One indexed read of the reviewer's last FLOOR_WINDOW approvals: constant work per event, independent of history."""
    cfg = policy.get("detector", {}).get("floor_cluster", {})
    if cfg.get("enabled", True) is False:
        return
    recent = [a["active_dwell_ms"] for a in db.approvals.find({"tenant_id": tenant, "reviewer_id": reviewer_id},
                                                              {"active_dwell_ms": 1}).sort("created_at", -1).limit(FLOOR_WINDOW)]
    r = floor_cluster(recent, policy["rules"]["min_active_dwell_ms"], cfg.get("delta", 0.25), cfg.get("p0", 0.25),
                      cfg.get("alpha", 0.001), cfg.get("min_n", 8))
    if r["flagged"]:
        res = db.reviewer_flags.update_one({"tenant_id": tenant, "reviewer_id": reviewer_id, "kind": "FLOOR_CLUSTERING"},
                                           {"$set": {"observed": r, "last_seen": now(), "policy_version": policy["version"]},
                                            "$setOnInsert": {"first_seen": now()}}, upsert=True)
        if res.upserted_id is not None:
            obs.CLOSER_EVENTS.labels("flag_floor_clustering").inc()


def handle(db, change: dict) -> str | None:
    ap = change["fullDocument"]
    tenant, rid = ap["tenant_id"], ap["reviewer_id"]
    flag_attestation(db, ap)
    prop = db.proposals.find_one({"tenant_id": tenant, "proposal_id": ap["proposal_id"]}) or {}
    action = prop.get("action_type", "claim_denial")
    policy = gate.active_policy(db, tenant, action)
    flag_floor_clustering(db, tenant, rid, policy)  # examiner flag only; recorded even for an already-suspended reviewer
    if db.suspensions.find_one({"tenant_id": tenant, "reviewer_id": rid, "active": True}):
        return None
    hit = check_streaming(db, tenant, rid, ap, policy)
    if hit:
        rule, observed = hit
        gate.suspend(tenant, rid, "change_stream", rule, observed, action)
        obs.CLOSER_EVENTS.labels(f"suspend_{rule.lower()}").inc()
        return rule
    return None


CATCHUP_DEFAULT_MIN = 15
RESYNC_CODES = {136, 280, 286}  # CappedPositionLost, ChangeStreamFatalError, ChangeStreamHistoryLost


def catch_up(db, since) -> int:
    """Check every reviewer who approved anything since `since`, once, with the batch detector.

    Why: a change stream only delivers events from its resume point. On the very first start there is no token, and
    after a long outage MongoDB may have dropped the oplog the token points into (ChangeStreamHistoryLost). Either
    way approvals could have been written while no detector was watching. Runs at startup only: it scans `approvals`
    by created_at, O(approvals in the gap)."""
    suspended = 0
    pairs = db.approvals.aggregate([{"$match": {"created_at": {"$gte": since}}},
                                    {"$group": {"_id": {"t": "$tenant_id", "r": "$reviewer_id", "p": "$proposal_id"}}},
                                    {"$group": {"_id": {"t": "$_id.t", "r": "$_id.r"}, "p": {"$first": "$_id.p"}}}])
    for g in pairs:
        tenant, rid = g["_id"]["t"], g["_id"]["r"]
        if db.suspensions.find_one({"tenant_id": tenant, "reviewer_id": rid, "active": True}):
            continue
        prop = db.proposals.find_one({"tenant_id": tenant, "proposal_id": g["p"]}) or {}
        action = prop.get("action_type", "claim_denial")
        policy = gate.active_policy(db, tenant, action)
        hit = check_reviewer(db, tenant, rid, policy)
        db.reviewer_stats.delete_one({"_id": f"{tenant}|{rid}"})  # rebuilt from the full history on the next event
        if hit:
            gate.suspend(tenant, rid, "detector_catchup", hit[0], hit[1], action)
            obs.CLOSER_EVENTS.labels(f"suspend_{hit[0].lower()}").inc()
            suspended += 1
    return suspended


def _since(db) -> "datetime":
    """Where a catch-up scan starts: the newest approval the detector handled (its created_at, not the detector's
    wall clock, so detector lag cannot under-scan the gap), minus a minute of slack for clock skew."""
    st = db.detector_state.find_one({"_id": STATE_ID}) or {}
    base = st.get("last_created_at") or (now() - timedelta(minutes=CATCHUP_DEFAULT_MIN))
    return base - timedelta(minutes=1)


def _cluster_time(db):
    try:
        return db.client.admin.command("ping").get("$clusterTime", {}).get("clusterTime")
    except PyMongoError:
        return None


MAX_EVENT_FAILURES = 5
FLOOR_WINDOW = 30


def run(stop: threading.Event | None = None) -> None:
    """Watch approvals forever. Survives transient errors (reconnects, timeouts) by resuming from the last saved token;
    a poison event that fails MAX_EVENT_FAILURES times is logged and skipped so it cannot wedge the detector."""
    db = get_db()
    failures = 0
    while not (stop and stop.is_set()):
        st = db.detector_state.find_one({"_id": STATE_ID}) or {}
        kw: dict = {}
        if st.get("resume_token"):
            kw["resume_after"] = st["resume_token"]
        else:
            # No token: note the cluster time FIRST, scan the gap, then watch from that exact time, so an approval
            # written between the scan and the watch is still delivered.
            ts = _cluster_time(db)
            n = catch_up(db, _since(db))
            if ts is not None:
                kw["start_at_operation_time"] = ts
            obs.log_event("detector_start", resumed=False, catch_up_suspensions=n)
        try:
            with db.watch(PIPELINE, **kw) as cs:
                last_idle_save = 0.0
                while not (stop and stop.is_set()):
                    ch = cs.try_next()
                    if ch is None:
                        # Idle: persist the stream's position (a token that precedes any undelivered event). Without
                        # this a failing FIRST event has no token to replay from and would be skipped on restart.
                        if cs.resume_token and time.time() - last_idle_save > 5:
                            db.detector_state.update_one({"_id": STATE_ID}, {"$set": {"resume_token": cs.resume_token}}, upsert=True)
                            last_idle_save = time.time()
                        time.sleep(0.05)
                        continue
                    try:
                        handle(db, ch)
                        failures = 0
                    except Exception as e:  # noqa: BLE001 - one bad event must never stop the detector
                        failures += 1
                        obs.log_event("detector_event_failed", error=type(e).__name__, attempt=failures)
                        if failures < MAX_EVENT_FAILURES:
                            raise  # leave the with-block; resume from the last saved token and replay this event
                        obs.log_event("detector_event_skipped", error=type(e).__name__)
                        failures = 0
                    created = (ch.get("fullDocument") or {}).get("created_at")
                    upd = {"resume_token": cs.resume_token, "last_event_at": now()}
                    if created:
                        lag = (now() - created).total_seconds()
                        obs.DETECTOR_LAG.set(lag)
                        obs.record_telemetry(db, "detector_lag_s", lag, tenant_id=ch["fullDocument"]["tenant_id"])
                        upd["last_created_at"] = created
                    db.detector_state.update_one({"_id": STATE_ID}, {"$set": upd, "$inc": {"events_processed": 1}}, upsert=True)
            return
        except OperationFailure as e:
            if e.code in RESYNC_CODES:  # token fell off the oplog, or the stream died: drop it, scan the gap, watch fresh
                obs.log_event("detector_resync", code=e.code)
                db.detector_state.update_one({"_id": STATE_ID}, {"$unset": {"resume_token": ""}}, upsert=True)
            else:
                obs.log_event("detector_error", code=e.code)
                time.sleep(1)
        except Exception as e:  # noqa: BLE001 - never let the safety net die; back off, then resume from the saved token
            obs.log_event("detector_error", error=type(e).__name__)
            time.sleep(1)


def compensation_worker(stop: threading.Event | None = None, interval_s: float = 1.0) -> None:
    """Retries with backoff; a compensation is confirmed only after read-back shows compensate_status."""
    db = get_db()
    while not (stop and stop.is_set()):
        for c in db.compensations.find({"status": "pending", "next_attempt_at": {"$lte": now()}}).limit(50):
            try:
                compensate(c["tenant_id"], c["kind"], c["record_id"], c["to_status"], c["denial_id"], "compensation-worker")
                rec = db.target_records.find_one({"tenant_id": c["tenant_id"], "record_id": c["record_id"]})
                if rec and rec["status"] == c["to_status"] and c["denial_id"] in rec.get("reopened_for", []):
                    db.compensations.update_one({"_id": c["_id"]}, {"$set": {"status": "confirmed",
                                                                             "readback": {"status": rec["status"], "at": now()}}})
                    d = db.denials.find_one_and_update({"tenant_id": c["tenant_id"], "denial_id": c["denial_id"]},
                                                       {"$set": {"status": "REVERSED"}})
                    if d:  # only the proposal this denial executed, not every proposal on the case
                        db.proposals.update_one({"tenant_id": c["tenant_id"], "proposal_id": d["proposal_id"]},
                                                {"$set": {"status": "reversed"}})
                    continue
            except Exception as e:  # keep pending; R6 stays red until confirmed
                obs.log_event("compensation_failed", denial=c["denial_id"], error=str(e))
            n = c.get("attempts", 0) + 1
            db.compensations.update_one({"_id": c["_id"]}, {"$set": {"next_attempt_at": now() + timedelta(seconds=min(30, 2 ** n))},
                                                            "$inc": {"attempts": 1}})
        time.sleep(interval_s)


def start_background() -> threading.Event:
    stop = threading.Event()
    threading.Thread(target=run, args=(stop,), daemon=True, name="detector").start()
    threading.Thread(target=compensation_worker, args=(stop,), daemon=True, name="compensation").start()
    return stop


if __name__ == "__main__":  # run as its own process for the live kill-and-restart demo
    ev = threading.Event()
    threading.Thread(target=compensation_worker, args=(ev,), daemon=True).start()
    run(ev)
    _ = math  # keep import for time-scale maths in custom policies

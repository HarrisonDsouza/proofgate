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
from datetime import timedelta

from pymongo.errors import OperationFailure

from pg import gate
from pg import observability as obs
from pg.cusum import Cusum, HonestModel, SelfCusum, SelfCusumState
from pg.db import get_db, now
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


def check_reviewer(db, tenant: str, reviewer_id: str, policy: dict) -> tuple[str, dict] | None:
    """BATCH check: replays the reviewer's last 200 approvals. O(W). Used for catch-up after downtime and as the
    reference the streaming detector is tested against. The per-event path is `check_streaming` (O(1))."""
    hit = _rate_and_median(db, tenant, reviewer_id, policy)
    if hit:
        return hit
    c = cusum_for(policy)
    if c is not None:
        recent = list(db.approvals.find({"tenant_id": tenant, "reviewer_id": reviewer_id},
                                        {"active_dwell_ms": 1, "created_at": 1}).sort("created_at", -1).limit(200))
        dwells = [_scaled(policy, a["active_dwell_ms"]) for a in reversed(recent)]
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
    doc = db.reviewer_stats.find_one({"_id": sid})
    if doc is None:
        state, last = SelfCusumState(c.sigma, c.drop, c.h, c.warmup), (None, None)
        for a in reversed(list(db.approvals.find({"tenant_id": tenant, "reviewer_id": reviewer_id},
                                                 {"active_dwell_ms": 1, "created_at": 1, "approval_id": 1})
                               .sort("created_at", -1).limit(200))):
            state.push(_scaled(policy, a["active_dwell_ms"]))
            last = (a["created_at"], a["approval_id"])
    else:
        state = SelfCusumState.from_doc(doc, c.sigma, c.drop, c.h, c.warmup)
        last = (doc.get("last_created_at"), doc.get("last_approval_id"))
        if last[0] is not None and (ap["created_at"], ap["approval_id"]) <= last:
            return ("CUSUM", {"approvals_seen": state.n, "alarm_at": state.alarm_at, "h": c.h, "mode": "self"}) \
                if state.alarm_at is not None else None  # already counted (restart replay)
        state.push(_scaled(policy, ap["active_dwell_ms"]))
        last = (ap["created_at"], ap["approval_id"])
    db.reviewer_stats.update_one({"_id": sid}, {"$set": {**state.to_doc(), "tenant_id": tenant, "reviewer_id": reviewer_id,
                                                           "last_created_at": last[0], "last_approval_id": last[1]}}, upsert=True)
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


def handle(db, change: dict) -> str | None:
    ap = change["fullDocument"]
    flag_attestation(db, ap)
    tenant, rid = ap["tenant_id"], ap["reviewer_id"]
    if db.suspensions.find_one({"tenant_id": tenant, "reviewer_id": rid, "active": True}):
        return None
    prop = db.proposals.find_one({"tenant_id": tenant, "proposal_id": ap["proposal_id"]}) or {}
    policy = gate.active_policy(db, tenant, prop.get("action_type", "claim_denial"))
    hit = check_streaming(db, tenant, rid, ap, policy)
    if hit:
        rule, observed = hit
        gate.suspend(tenant, rid, "change_stream", rule, observed, prop.get("action_type", "claim_denial"))
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
        db.reviewer_stats.delete_one({"_id": f"{tenant}|{rid}"})  # rebuilt from history on the next event
        if hit:
            gate.suspend(tenant, rid, "detector_catchup", hit[0], hit[1], action)
            obs.CLOSER_EVENTS.labels(f"suspend_{hit[0].lower()}").inc()
            suspended += 1
    return suspended


def run(stop: threading.Event | None = None) -> None:
    db = get_db()
    st = db.detector_state.find_one({"_id": STATE_ID}) or {}
    since = st.get("last_event_at") or (now() - timedelta(minutes=CATCHUP_DEFAULT_MIN))
    kw: dict = {}
    if st.get("resume_token"):
        kw["resume_after"] = st["resume_token"]
    while not (stop and stop.is_set()):
        n = 0 if kw else catch_up(db, since)  # a resume token already guarantees no gap; catch up only without one
        obs.log_event("detector_start", resumed=bool(kw), catch_up_suspensions=n)
        try:
            with db.watch(PIPELINE, **kw) as cs:
                while not (stop and stop.is_set()):
                    ch = cs.try_next()
                    if ch is None:
                        time.sleep(0.05)
                        continue
                    handle(db, ch)
                    created = (ch.get("fullDocument") or {}).get("created_at")
                    if created:
                        lag = (now() - created).total_seconds()
                        obs.DETECTOR_LAG.set(lag)
                        obs.record_telemetry(db, "detector_lag_s", lag)
                    db.detector_state.update_one({"_id": STATE_ID}, {"$set": {"resume_token": cs.resume_token, "last_event_at": now()},
                                                                     "$inc": {"events_processed": 1}}, upsert=True)
            return
        except OperationFailure as e:  # token fell off the oplog, or the stream died: re-sync, then watch fresh
            if e.code not in RESYNC_CODES:
                raise
            obs.log_event("detector_resync", code=e.code)
            since = (db.detector_state.find_one({"_id": STATE_ID}) or {}).get("last_event_at") \
                or now() - timedelta(minutes=CATCHUP_DEFAULT_MIN)
            db.detector_state.update_one({"_id": STATE_ID}, {"$unset": {"resume_token": ""}}, upsert=True)
            kw = {}


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
                    db.denials.update_one({"denial_id": c["denial_id"]}, {"$set": {"status": "REVERSED"}})
                    db.proposals.update_one({"tenant_id": c["tenant_id"], "case_id": c["record_id"]}, {"$set": {"status": "reversed"}})
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

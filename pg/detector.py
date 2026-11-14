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

from pg import gate
from pg import observability as obs
from pg.cusum import Cusum, HonestModel, SelfCusum
from pg.db import get_db, now
from pg.target import compensate

STATE_ID = "rubber_stamp_detector"
PIPELINE = [{"$match": {"operationType": "insert", "ns.coll": "approvals"}}]


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


def check_reviewer(db, tenant: str, reviewer_id: str, policy: dict) -> tuple[str, dict] | None:
    r = policy["rules"]
    t = now()
    recent = list(db.approvals.find({"tenant_id": tenant, "reviewer_id": reviewer_id},
                                    {"active_dwell_ms": 1, "created_at": 1}).sort("created_at", -1).limit(200))
    in_window = [a for a in recent if a["created_at"] >= t - timedelta(milliseconds=r["rate_window_ms"])]
    if len(in_window) >= r["rate_max_approvals"]:
        return "RATE", {"count": len(in_window), "window_ms": r["rate_window_ms"]}
    last = [a["active_dwell_ms"] for a in recent[: r["median_n"]]]
    if len(last) >= r["median_n"] and statistics.median(last) < r["min_active_dwell_ms"]:
        return "MEDIAN_DWELL", {"median_dwell_ms": statistics.median(last), "n": len(last)}
    c = cusum_for(policy)
    if c is not None:
        dwells = [max(a["active_dwell_ms"], 1) / 1000 * policy.get("detector", {}).get("time_scale", 1)
                  for a in reversed(recent)]
        hit = c.run(dwells)
        if hit is not None:
            return "CUSUM", {"approvals_seen": len(dwells), "alarm_at": hit, "h": c.h,
                             "mode": "self" if isinstance(c, SelfCusum) else "population"}
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
    hit = check_reviewer(db, tenant, rid, policy)
    if hit:
        rule, observed = hit
        gate.suspend(tenant, rid, "change_stream", rule, observed, prop.get("action_type", "claim_denial"))
        obs.CLOSER_EVENTS.labels(f"suspend_{rule.lower()}").inc()
        return rule
    return None


def run(stop: threading.Event | None = None) -> None:
    db = get_db()
    st = db.detector_state.find_one({"_id": STATE_ID}) or {}
    kw = {"full_document": "updateLookup"}
    if st.get("resume_token"):
        kw["resume_after"] = st["resume_token"]
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

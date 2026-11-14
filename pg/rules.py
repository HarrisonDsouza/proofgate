"""Rules over stored state (PRD M14, R1-R8). Pass/fail is computed from Atlas, never from the UI."""
from __future__ import annotations

import hashlib
import json

from pg.db import get_db


def _r(violations: list) -> dict:
    return {"pass": not violations, "violations": violations[:20], "count": len(violations)}


def verify_session_chain(db, tenant: str, session_id: str) -> bool:
    prev = "0" * 64
    for ev in db.review_events.find({"tenant_id": tenant, "session_id": session_id}).sort("seq", 1):
        body = json.dumps({k: ev.get(k) for k in ("session_id", "seq", "case_id", "evidence_id", "type", "credited_ms")}, sort_keys=True)
        if ev.get("prev_hash") != prev or ev.get("hash") != hashlib.sha256((prev + body).encode()).hexdigest():
            return False
        prev = ev["hash"]
    return True


def run_rules(tenant: str) -> dict:
    db = get_db()
    out = {}
    confirmed = list(db.denials.find({"tenant_id": tenant, "status": {"$in": ["CONFIRMED", "REVERSED"]}}))
    ap = {a["approval_id"]: a for a in db.approvals.find({"tenant_id": tenant, "approval_id": {"$in": [d["approval_id"] for d in confirmed]}})}
    props = {p["proposal_id"]: p for p in db.proposals.find({"tenant_id": tenant, "proposal_id": {"$in": [d["proposal_id"] for d in confirmed]}})}
    pols = {(p["policy_id"], p["version"]): p for p in db.review_policies.find({"tenant_id": tenant})}

    out["R1"] = _r([d["denial_id"] for d in confirmed
                    if not (a := ap.get(d["approval_id"])) or a["case_id"] != d["case_id"] or a["proposal_id"] != d["proposal_id"]])
    out["R2"] = _r([d["denial_id"] for d in confirmed
                    if not {c["hash"] for c in props.get(d["proposal_id"], {}).get("cited_evidence", [])}
                    <= set(ap.get(d["approval_id"], {}).get("evidence_hashes_viewed", []))])

    def r3_bad(d):
        a, p = ap.get(d["approval_id"], {}), pols.get((d["policy_id"], d["policy_version"]))
        if not p or p["rules"].get("baseline_only_existence"):
            return False
        items = {v["evidence_id"]: v["active_ms"] for v in a.get("views", [])}
        cited = props.get(d["proposal_id"], {}).get("cited_evidence", [])
        return a.get("active_dwell_ms", 0) < p["rules"]["min_active_dwell_ms"] or any(
            items.get(c["evidence_id"], 0) < p["rules"]["min_item_active_ms"] for c in cited)
    out["R3"] = _r([d["denial_id"] for d in confirmed if r3_bad(d)])

    def r4_bad(d):
        a = ap.get(d["approval_id"], {})
        snap = a.get("credential_snapshot", {})
        return not snap or snap.get("license_expires_at") is None or snap["license_expires_at"] <= d["created_at"]
    out["R4"] = _r([d["denial_id"] for d in confirmed if r4_bad(d)])

    susp = list(db.suspensions.find({"tenant_id": tenant}))
    out["R5"] = _r([d["denial_id"] for d in db.denials.find({"tenant_id": tenant})
                    if any(s["reviewer_id"] == d["reviewer_id"] and s["ts"] < d["created_at"] and s.get("active") for s in susp)])

    bad6 = []
    for s in susp:
        pol = pols.get((s["policy_id"], s["policy_version"]))
        if not pol:
            continue
        for d in db.denials.find({"tenant_id": tenant, "reviewer_id": s["reviewer_id"], "status": {"$in": ["CONFIRMED", "REVERSED"]},
                                  "confirmed_at": {"$lte": s["ts"]}}):
            c = db.compensations.find_one({"denial_id": d["denial_id"]})
            if not c or c["status"] != "confirmed" or (c.get("readback") or {}).get("status") != pol["effect"]["compensate_status"]:
                bad6.append(d["denial_id"])
    out["R6"] = _r(bad6)

    applied_status = {p["effect"]["apply_status"] for p in pols.values()}
    bad7 = []
    for rec in db.target_records.find({"tenant_id": tenant, "status": {"$in": list(applied_status)}}):
        g = (rec.get("last_apply") or {}).get("grant_id")
        if not g or not db.denials.find_one({"tenant_id": tenant, "grant_id": g, "status": {"$in": ["CONFIRMED", "REVERSED", "AUTHORIZED"]}}):
            bad7.append(rec["record_id"])
    out["R7"] = _r(bad7)

    bad8 = [s["session_id"] for s in db.reviewer_sessions.find({"tenant_id": tenant}) if not verify_session_chain(db, tenant, s["session_id"])]
    out["R8"] = _r(bad8)
    return out


def examiner(tenant: str, case_id: str) -> dict:
    """Rebuild one case: proposal -> views -> approval -> gate checks -> grant -> target -> suspension/compensation."""
    db = get_db()
    q = {"tenant_id": tenant, "case_id": case_id}
    case = db.cases.find_one(q, {"_id": 0})
    prop = db.proposals.find_one(q, {"_id": 0})
    approval = db.approvals.find_one(q, {"_id": 0}, sort=[("created_at", -1)])
    views = []
    for v in (approval or {}).get("views", []):
        views.append(v | {"idle_flag": v["open_ms"] >= 3 * max(v["active_ms"], 1)})
    denial = db.denials.find_one(q, {"_id": 0}, sort=[("created_at", -1)])
    grant = db.grants.find_one({"_id": denial["grant_id"]}, {"_id": 0}) if denial else None
    susp = db.suspensions.find_one({"tenant_id": tenant, "reviewer_id": (approval or {}).get("reviewer_id")}, {"_id": 0},
                                   sort=[("ts", -1)]) if approval else None
    comp = db.compensations.find_one({"denial_id": denial["denial_id"]}, {"_id": 0}) if denial else None
    recomputed = sum(e["credited_ms"] for e in db.review_events.find(
        {"tenant_id": tenant, "session_id": (approval or {}).get("session_id"), "case_id": case_id, "type": "heartbeat"})) if approval else 0
    return {"case": case, "proposal": prop, "views": views, "approval": approval,
            "gate_decisions": list(db.gate_decisions.find(q, {"_id": 0}).sort("ts", 1)),
            "denial": denial, "grant": grant, "target_log": list(db.target_log.find({"tenant_id": tenant, "record_id": case_id}, {"_id": 0}).sort("ts", 1)),
            "suspension": susp, "compensation": comp,
            "chain": {"review_events_ok": verify_session_chain(db, tenant, approval["session_id"]) if approval else None,
                      "dwell_recomputed_ms": recomputed,
                      "dwell_matches": (recomputed == approval["active_dwell_ms"]) if approval else None}}

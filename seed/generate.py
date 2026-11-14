"""Deterministic seed (PRD Section 10). SYNTHETIC cases; real public-domain ICD-10-CM / HCPCS descriptions.

    python -m seed.generate --reset --seed 20261114
    python -m seed.generate --tenant payer-eval --cases 600 --seed 1 --scale 10   # time-scaled eval tenant
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from pg.agent import triage
from pg.config import OPERATOR_ID
from pg.db import get_db, setup

CODES = json.loads(Path("data/processed/specialty_codes.json").read_text())
SPECS = ["orthopedics", "cardiology", "sleep_medicine"]

CLAUSE_TEMPLATES = [
    "requires a prior authorization on file before the service date",
    "requires a documented diagnostic study within 12 months",
    "is covered only after 6 weeks of documented conservative therapy",
    "requires the ordering clinician's notes to state medical necessity",
    "limits replacement to once every 5 years unless the device is lost or damaged",
    "requires a face-to-face evaluation within 6 months before the order",
]

REVIEWERS = [  # (id, specialty, licence expiry, purpose)
    ("dr-demo", "orthopedics", "2027-06-30", "the judge's honest seat"),
    ("dr-stamper", "orthopedics", "2027-06-30", "the bulk-button seat"),
    ("dr-prep", "orthopedics", "2027-06-30", "policy-edit demo"),
    ("dr-late", "orthopedics", "2027-06-30", "compensation demo"),
    ("dr-skim", "orthopedics", "2027-06-30", "floor-gaming demo (CUSUM)"),
    ("dr-expired", "orthopedics", "2026-10-01", "shows G3 expiry"),
    ("dr-cardio", "cardiology", "2027-06-30", "shows a specialty mismatch"),
    ("op-ops-1", "orthopedics", "2027-06-30", "same id as the operator: shows G8"),
]

BASE_RULES = {"min_active_dwell_ms": 30000, "min_item_active_ms": 5000, "rate_max_approvals": 10, "rate_window_ms": 60000,
              "median_n": 5, "require_all_cited_evidence": True, "require_specialty_match": True,
              "require_unexpired_license": True, "separation_of_duties": True, "max_proposal_age_ms": 86400000,
              "compensation_lookback_ms": 3600000}
RATIONALE = ("30 s is a demo floor. ProPublica reported about 1.2 s per claim (as reported; Cigna disputes it). "
             "10 approvals per 60 s cannot be reached with honest 30 s per-case review under exclusive focus.")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def make_case(rng: random.Random, tenant: str, i: int, spec: str, t0: datetime) -> dict:
    icd = rng.choice(CODES[spec]["icd10cm"])
    hc = rng.choice(CODES[spec]["hcpcs"])
    billed = rng.choice([120, 240, 480, 960, 1850, 3200])
    no_pa = rng.random() < 0.6
    cid = f"CLM-{tenant.split('-')[-1][0].upper()}-{i:04d}"
    ev = [("E1", "Claim line 1", f"HCPCS {hc[0]}: {hc[1]}. Billed ${billed}. Diagnosis ICD-10-CM {icd[0]}: {icd[1]}."),
          ("E2", "Clinical note excerpt (synthetic)", f"Synthetic note: patient seen for {icd[1].lower()}. "
                 f"{rng.choice(['Symptoms for 3 weeks.', 'Symptoms for 4 months.', 'Follow-up visit.', 'New complaint.'])} "
                 f"{rng.choice(['Conservative therapy documented.', 'No therapy documented.', 'Imaging referenced but not attached.'])}"),
          ("E3", "Prior-auth record", "Prior-auth record: none on file" if no_pa else f"Prior-auth record: PA-{rng.randint(10000, 99999)} approved"),
          ("E4", "Member eligibility", f"Member active since {2015 + rng.randint(0, 10)}; plan tier {rng.choice(['bronze', 'silver', 'gold'])}.")]
    evidence = [{"evidence_id": e, "label": lab, "content": c, "hash": sha(c)} for e, lab, c in ev[: rng.choice([3, 4])]]
    return {"tenant_id": tenant, "case_id": cid, "kind": "claim", "specialty": spec, "member_ref": f"M-{rng.randint(100000, 999999)}",
            "summary": f"{hc[1][:80]} for {icd[1][:80]}", "codes": {"icd10": [icd[0]], "hcpcs": [hc[0]]},
            "billed_amount": billed, "evidence": evidence, "created_at": t0, "synthetic": True}


def seed_tenant(db, tenant: str, n_cases: int, seed: int, scale: int = 1, reviewers=REVIEWERS):
    rng = random.Random(seed)
    t0 = datetime.now(timezone.utc)
    clauses = [{"tenant_id": tenant, "clause_id": f"MP-{i + 1:03d}", "action_type": "claim_denial",
                "title": f"Acme Medical Policy MP-{i + 1:03d}",
                "text": f"MP-{i + 1:03d}: {rng.choice(['DME', 'Orthotics', 'Cardiac devices', 'Sleep therapy'])} "
                        f"{CLAUSE_TEMPLATES[i % len(CLAUSE_TEMPLATES)]}. (Made-up policy for the demo.)"} for i in range(30)]
    db.policy_clauses.insert_many(clauses)
    cases, recs, props = [], [], []
    for i in range(n_cases):
        spec = "orthopedics" if i % 2 == 0 else rng.choice(SPECS)  # half ortho so the demo seats have work
        c = make_case(rng, tenant, i + 1, spec, t0)
        cases.append(c)
        recs.append({"tenant_id": tenant, "kind": "claim", "record_id": c["case_id"], "status": "PENDING", "history": [], "reopened_for": []})
        tri = triage(c, clauses)
        props.append({"tenant_id": tenant, "proposal_id": c["case_id"].replace("CLM", "P"), "case_id": c["case_id"],
                      "action_type": "claim_denial", "agent_id": "triage-agent-v1", "model_version": "rules-v1",
                      "operator_id": OPERATOR_ID, **tri, "status": "pending_review", "requeue_reasons": [], "created_at": t0})
    db.cases.insert_many(cases)
    db.target_records.insert_many(recs)
    db.proposals.insert_many(props)
    for rid, spec, exp, _ in reviewers:
        db.reviewers.insert_one({"tenant_id": tenant, "reviewer_id": rid, "name": rid, "license_no": f"LIC-{sha(rid)[:8]}",
                                 "specialty": spec, "license_expires_at": datetime.fromisoformat(exp).replace(tzinfo=timezone.utc),
                                 "active": True})
        db.reviewer_state.insert_one({"_id": f"{tenant}|{rid}", "tenant_id": tenant, "reviewer_id": rid, "version": 0,
                                      "suspended": False, "suspension_id": None, "approval_ts": [], "last_gate_at": None})
    rules = {k: (v // scale if k.endswith("_ms") and k not in ("max_proposal_age_ms", "compensation_lookback_ms") else v)
             for k, v in BASE_RULES.items()}
    db.review_policies.insert_one({"tenant_id": tenant, "policy_id": f"{tenant.split('-')[-1]}-claim_denial", "action_type": "claim_denial",
                                   "version": 1, "status": "active", "rationale": RATIONALE + (f" Time-scaled /{scale}." if scale > 1 else ""),
                                   "created_by": "seed", "created_at": t0, "rules": rules,
                                   "effect": {"kind": "claim", "apply_status": "DENIED", "compensate_status": "OPEN"}})
    db.agent_control.update_one({"_id": f"executor|{tenant}"}, {"$set": {"paused": False}}, upsert=True)
    return {"cases": len(cases), "deny_proposals": sum(p["recommendation"] == "deny" for p in props)}


def reset(db, tenant: str):
    for c in ["cases", "target_records", "target_log", "policy_clauses", "proposals", "reviewers", "reviewer_sessions", "view_tokens",
              "review_events", "approvals", "review_policies", "reviewer_state", "gate_decisions", "denials", "grants",
              "suspensions", "compensations", "audit", "agent_control"]:
        db[c].delete_many({"tenant_id": tenant} if c not in ("reviewer_state", "agent_control") else {"_id": {"$regex": f"{tenant}"}})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tenant", default="payer-acme")
    ap.add_argument("--cases", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20261114)
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--volunteers", type=int, default=0, help="add vol-1..N orthopedics reviewers (real honest sessions)")
    a = ap.parse_args()
    db = get_db()
    setup(db)
    if a.reset:
        reset(db, a.tenant)
        db.detector_state.delete_many({})
    revs = REVIEWERS + [(f"vol-{i}", "orthopedics", "2027-06-30", "volunteer") for i in range(1, a.volunteers + 1)]
    print(seed_tenant(db, a.tenant, a.cases, a.seed, a.scale, reviewers=revs))


if __name__ == "__main__":
    main()

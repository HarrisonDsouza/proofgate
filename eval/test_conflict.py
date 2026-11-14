"""PRD M16: prove serialisation on reviewer_state. Needs DEMO_DEBUG_HOOKS=true and a seeded payer-acme.

    DEMO_DEBUG_HOOKS=true python -m eval.test_conflict
Prints PASS/FAIL per assertion. Show it on stage.
"""
from __future__ import annotations

import secrets
import threading
import time

from pg import gate, review
from pg.config import AGENT_ID, OPERATOR_ID, settings
from pg.db import get_db, now

T = "payer-acme"


def seeded_honest_approval(db, reviewer_id: str) -> tuple[dict, dict]:
    """A valid approval for the next pending ortho deny proposal (inserted directly: a test fixture)."""
    p = db.proposals.find_one({"tenant_id": T, "status": "pending_review", "recommendation": "deny",
                               "case_id": {"$in": [c["case_id"] for c in db.cases.find({"tenant_id": T, "specialty": "orthopedics"})]}})
    rv = db.reviewers.find_one({"tenant_id": T, "reviewer_id": reviewer_id})
    pol = gate.active_policy(db, T, "claim_denial")
    views = [{"evidence_id": c["evidence_id"], "hash": c["hash"], "active_ms": 20000, "open_ms": 21000} for c in p["cited_evidence"]]
    ap = {"tenant_id": T, "approval_id": f"AP-T{secrets.token_hex(3)}", "case_id": p["case_id"], "proposal_id": p["proposal_id"],
          "reviewer_id": reviewer_id, "session_id": "S-test", "credential_snapshot": {k: rv[k] for k in ("license_no", "specialty", "license_expires_at")},
          "views": views, "evidence_hashes_viewed": [v["hash"] for v in views], "active_dwell_ms": 40000,
          "policy_version_at_approval": pol["version"], "attestation_text": "Test fixture approval, honest review.",
          "client_supplied_ignored": {}, "status": "submitted", "created_at": now()}
    db.approvals.insert_one(ap)
    db.proposals.update_one({"_id": p["_id"]}, {"$set": {"status": "approved", "approved_by": reviewer_id, "approval_id": ap["approval_id"]}})
    return p, ap


def report(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    return ok


def main():
    assert settings.debug_hooks, "set DEMO_DEBUG_HOOKS=true"
    db = get_db()
    db.suspensions.delete_many({"tenant_id": T, "reviewer_id": {"$in": ["dr-late", "dr-prep"]}})
    for r in ("dr-late", "dr-prep"):
        db.reviewer_state.update_one({"_id": f"{T}|{r}"}, {"$set": {"suspended": False}})

    # (a) suspension in flight
    p, ap = seeded_honest_approval(db, "dr-late")
    out = {}
    th = threading.Thread(target=lambda: out.update(gate.execute(T, p["proposal_id"], ap["approval_id"], AGENT_ID, OPERATOR_ID, 3000)))
    th.start()
    time.sleep(0.5)
    gate.suspend(T, "dr-late", "supervisor", "TEST_IN_FLIGHT", {})
    th.join()
    report("(a) in-flight denial refused with G2 after suspension",
           out.get("decision") == "REFUSE" and any(r["rule"] == "G2_NOT_SUSPENDED" for r in out.get("reasons", [])))
    report(f"(a) txn_attempts >= 2 (got {out.get('txn_attempts')})", out.get("txn_attempts", 0) >= 2)
    report("(a) no denial written", db.denials.count_documents({"tenant_id": T, "approval_id": ap["approval_id"]}) == 0)

    # (b) two denials, same reviewer, both paused
    (p1, a1), (p2, a2) = seeded_honest_approval(db, "dr-prep"), seeded_honest_approval(db, "dr-prep")
    res = []
    ts = [threading.Thread(target=lambda p=p, a=a: res.append(gate.execute(T, p["proposal_id"], a["approval_id"], AGENT_ID, OPERATOR_ID, 2000)))
          for p, a in ((p1, a1), (p2, a2))]
    [t.start() for t in ts]
    [t.join() for t in ts]
    report(f"(b) exactly one decision retried (attempts {[r['txn_attempts'] for r in res]})",
           sum(r["txn_attempts"] >= 2 for r in res) == 1)

    # (c) forged burst: client dwell 45 s on 50 approvals, executes 0
    sess = review.open_session(T, "dr-stamper")["session_id"]
    ids = [x["proposal_id"] for x in db.proposals.find({"tenant_id": T, "status": "pending_review", "recommendation": "deny",
                                                         "case_id": {"$in": [c["case_id"] for c in db.cases.find({"tenant_id": T, "specialty": "orthopedics"})]}}).limit(50)]
    aps = [review.approve(T, sess, i, "Reviewed in batch.", {"dwell_ms": 45000}) for i in ids]
    results = [gate.execute(T, a["proposal_id"], a["approval_id"], AGENT_ID, OPERATOR_ID) for a in aps]
    report(f"(c) forged burst executes 0 of {len(results)}", all(r["decision"] == "REFUSE" for r in results))
    report("(c) client dwell_ms stored as ignored", all(a["client_supplied_ignored"].get("dwell_ms") == 45000 for a in aps))


if __name__ == "__main__":
    main()

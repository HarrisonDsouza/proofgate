"""The one-aggregation read path must return exactly what the nine separate reads returned (live DB)."""
import os

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("MONGODB_URI"), reason="needs MongoDB")


def reference_reads(db, s, tenant, proposal_id, approval_id, t):
    """The original implementation: nine sequential reads."""
    from pg.checks import window_start
    from pg.gate import active_policy
    prop = db.proposals.find_one({"tenant_id": tenant, "proposal_id": proposal_id}, session=s)
    if not prop:
        raise LookupError("unknown proposal")
    approval = db.approvals.find_one({"tenant_id": tenant, "approval_id": approval_id}, session=s)
    case = db.cases.find_one({"tenant_id": tenant, "case_id": prop["case_id"]}, session=s)
    policy = active_policy(db, tenant, prop["action_type"], s)
    rid = (approval or {}).get("reviewer_id", "unknown")
    reviewer = db.reviewers.find_one({"tenant_id": tenant, "reviewer_id": rid}, session=s)
    rstate = db.reviewer_state.find_one({"_id": f"{tenant}|{rid}"}, session=s) or {"_id": f"{tenant}|{rid}", "version": -1, "suspended": True}
    susp = db.suspensions.find_one({"tenant_id": tenant, "reviewer_id": rid, "active": True}, session=s)
    paused = bool((db.agent_control.find_one({"_id": f"executor|{tenant}"}, session=s) or {}).get("paused"))
    window = db.approvals.count_documents({"tenant_id": tenant, "reviewer_id": rid,
                                           "created_at": {"$gte": window_start(t, policy), "$lte": t}}, session=s)
    return {"prop": prop, "approval": approval, "case": case, "policy": policy, "reviewer": reviewer, "rstate": rstate,
            "susp": susp, "paused": paused, "window": window}


def test_aggregation_matches_nine_reads_for_every_kind_of_case(scratch):
    import eval.test_conflict as tc
    from eval.test_conflict import seeded_honest_approval
    from pg import gate
    from pg.db import client, get_db, now
    tc.T = scratch
    db = get_db()
    cases = []
    p, ap = seeded_honest_approval(db, "dr-demo")
    cases.append((p["proposal_id"], ap["approval_id"]))                     # a normal approval
    p2, ap2 = seeded_honest_approval(db, "dr-late")
    db.reviewer_state.update_one({"_id": f"{scratch}|dr-late"}, {"$set": {"suspended": True}})
    gate.suspend(scratch, "dr-late", "supervisor", "T", {})
    cases.append((p2["proposal_id"], ap2["approval_id"]))                   # suspended reviewer
    p3, _ = seeded_honest_approval(db, "dr-prep")
    cases.append((p3["proposal_id"], "AP-DOES-NOT-EXIST"))                  # no such approval -> reviewer "unknown"
    p4, ap4 = seeded_honest_approval(db, "dr-stamper")
    db.agent_control.update_one({"_id": f"executor|{scratch}"}, {"$set": {"paused": True}})
    cases.append((p4["proposal_id"], ap4["approval_id"]))                   # executor paused
    db.reviewer_state.delete_one({"_id": f"{scratch}|dr-stamper"})           # state row missing: must fail closed
    for _ in range(4):                                                      # rate window has several approvals
        seeded_honest_approval(db, "dr-demo")
    for pid, aid in cases:
        t = now()
        with client().start_session() as s:
            got = gate.load_gate_inputs(db, s, scratch, pid, aid, t)
            want = reference_reads(db, s, scratch, pid, aid, t)
        for k in want:
            assert got[k] == want[k], f"{k} differs for {pid}/{aid}"
    with pytest.raises(LookupError):
        with client().start_session() as s:
            gate.load_gate_inputs(db, s, scratch, "P-NOPE", "AP-NOPE", now())

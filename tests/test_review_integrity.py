"""Live-DB integrity tests for the bugs an independent review found (skipped without MONGODB_URI)."""
import os
import threading
import time

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("MONGODB_URI"), reason="needs MongoDB")
T = "payer-acme"


def _clean(db, reviewer):
    db.suspensions.delete_many({"tenant_id": T, "reviewer_id": reviewer})
    db.reviewer_state.update_one({"_id": f"{T}|{reviewer}"}, {"$set": {"suspended": False}, "$unset": {"suspension_id": ""}})


def test_applied_but_unconfirmed_denial_is_reopened_when_reviewer_is_suspended():
    from eval.test_conflict import seeded_honest_approval
    from pg import gate, target
    from pg.config import AGENT_ID, OPERATOR_ID
    from pg.db import get_db
    db = get_db()
    _clean(db, "dr-prep")
    p, ap = seeded_honest_approval(db, "dr-prep")
    res = gate.execute(T, p["proposal_id"], ap["approval_id"], AGENT_ID, OPERATOR_ID)
    assert res["decision"] == "ALLOW"
    t = res["target"]
    target.apply(T, t["kind"], t["record_id"], t["to_status"], f"Grant {res['grant_id']}", AGENT_ID)  # applied, NOT yet confirmed
    gate.suspend(T, "dr-prep", "supervisor", "TEST", {})
    assert db.compensations.count_documents({"denial_id": res["denial_id"]}) == 1  # case A: suspension after apply
    gate.confirm(T, res["denial_id"])
    assert db.proposals.find_one({"tenant_id": T, "proposal_id": p["proposal_id"]})["status"] != "executed"


def test_confirm_after_suspension_queues_compensation_and_does_not_mark_executed():
    from eval.test_conflict import seeded_honest_approval
    from pg import gate, target
    from pg.config import AGENT_ID, OPERATOR_ID
    from pg.db import get_db
    db = get_db()
    _clean(db, "dr-prep")
    p, ap = seeded_honest_approval(db, "dr-prep")
    res = gate.execute(T, p["proposal_id"], ap["approval_id"], AGENT_ID, OPERATOR_ID)
    t = res["target"]
    target.apply(T, t["kind"], t["record_id"], t["to_status"], f"Grant {res['grant_id']}", AGENT_ID)
    db.denials.update_one({"denial_id": res["denial_id"]}, {"$set": {"status": "AUTHORIZED"}})
    gate.suspend(T, "dr-prep", "supervisor", "TEST", {})
    db.compensations.delete_many({"denial_id": res["denial_id"]})  # case B: suspension committed before confirm ran
    out = gate.confirm(T, res["denial_id"])
    assert out["status"] == "CONFIRMED"
    assert db.compensations.count_documents({"denial_id": res["denial_id"]}) == 1
    assert db.proposals.find_one({"tenant_id": T, "proposal_id": p["proposal_id"]})["status"] != "executed"


def test_parallel_heartbeats_are_credited_once():
    from pg import review
    from pg.db import get_db
    db = get_db()
    rv = db.reviewers.find_one({"tenant_id": T, "reviewer_id": "dr-demo"})
    sid = review.open_session(T, rv["reviewer_id"])["session_id"]
    pr = db.proposals.find_one({"tenant_id": T, "status": "pending_review"})
    ev = db.cases.find_one({"tenant_id": T, "case_id": pr["case_id"]})["evidence"][0]["evidence_id"]
    tok = review.fetch_evidence(T, sid, pr["case_id"], ev)["view_token"]
    time.sleep(2.0)
    res = []
    ths = [threading.Thread(target=lambda: res.append(review.heartbeat(T, tok, True, 100))) for _ in range(10)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    credited = sum(r["credited_ms"] for r in res)
    assert 1500 <= credited <= 3500, f"10 parallel heartbeats credited {credited} ms for ~2 s of wall time"


def test_parallel_evidence_opens_leave_one_open_token():
    from pg import review
    from pg.db import get_db
    db = get_db()
    rv = db.reviewers.find_one({"tenant_id": T, "reviewer_id": "dr-demo"})
    sid = review.open_session(T, rv["reviewer_id"])["session_id"]
    pr = db.proposals.find_one({"tenant_id": T, "status": "pending_review"})
    evs = [e["evidence_id"] for e in db.cases.find_one({"tenant_id": T, "case_id": pr["case_id"]})["evidence"]]
    ths = [threading.Thread(target=review.fetch_evidence, args=(T, sid, pr["case_id"], evs[i % len(evs)])) for i in range(8)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    assert db.view_tokens.count_documents({"tenant_id": T, "session_id": sid, "closed_at": None}) == 1


def test_a_proposal_cannot_be_approved_or_denied_twice():
    from eval.test_conflict import seeded_honest_approval
    from pg import gate, review
    from pg.config import AGENT_ID, OPERATOR_ID
    from pg.db import get_db
    db = get_db()
    _clean(db, "dr-prep")
    p, ap = seeded_honest_approval(db, "dr-prep")
    assert gate.execute(T, p["proposal_id"], ap["approval_id"], AGENT_ID, OPERATOR_ID)["decision"] == "ALLOW"
    sid = review.open_session(T, "dr-prep")["session_id"]
    with pytest.raises(review.BadRequest):  # proposal is now `authorized`
        review.approve(T, sid, p["proposal_id"], "Reviewed again for the same case.")


def test_concurrent_detectors_do_not_lose_cusum_updates():
    import math

    from pg import detector, review
    from pg.db import get_db
    db = get_db()
    _clean(db, "dr-demo")
    db.reviewer_stats.delete_one({"_id": f"{T}|dr-demo"})
    sid = review.open_session(T, "dr-demo")["session_id"]
    ids = [p["proposal_id"] for p in db.proposals.find({"tenant_id": T, "status": "pending_review"}).limit(9)]
    for i in ids:
        review.approve(T, sid, i, "Reviewed in batch of one.")
    # re-read as the change stream would deliver them: BSON dates are millisecond precision, the in-memory dicts are not
    aps = list(db.approvals.find({"tenant_id": T, "reviewer_id": "dr-demo", "session_id": sid}))
    db.reviewer_stats.delete_one({"_id": f"{T}|dr-demo"})
    pol = {"rules": {"rate_window_ms": 60000, "rate_max_approvals": 999, "median_n": 5, "min_active_dwell_ms": 0},
           "detector": {"cusum": {"mode": "self", "sigma": 0.4, "drop": math.log(2), "h": 1e9, "warmup": 5}}}
    ths = [threading.Thread(target=detector.check_streaming, args=(db, T, "dr-demo", a, pol)) for a in aps for _ in range(2)]
    [t.start() for t in ths]
    [t.join() for t in ths]  # two "detectors" handle every event
    st = db.reviewer_stats.find_one({"_id": f"{T}|dr-demo"})
    total = db.approvals.count_documents({"tenant_id": T, "reviewer_id": "dr-demo"})  # earlier tests may have approved too
    assert st["n"] == total, f"expected {total} counted, got {st['n']}"


def test_approve_cannot_reset_a_proposal_that_moved_on_mid_transaction():
    """The pre-check passes, then a gate call moves the proposal on before the approval commits: the conditional
    update must abort the transaction, leave the proposal alone and store no approval."""
    from pg import review
    from pg.db import get_db
    db = get_db()
    sid = review.open_session(T, "dr-demo")["session_id"]
    p = db.proposals.find_one({"tenant_id": T, "status": "pending_review"})
    real = review._rid
    n_before = db.approvals.count_documents({"tenant_id": T, "proposal_id": p["proposal_id"]})

    def moved_on(prefix):  # runs after the pre-check, before the transaction body
        db.proposals.update_one({"_id": p["_id"]}, {"$set": {"status": "authorized"}})
        return real(prefix)

    review._rid = moved_on
    try:
        with pytest.raises(review.BadRequest):
            review.approve(T, sid, p["proposal_id"], "Reviewed this case in detail.")
    finally:
        review._rid = real
    assert db.proposals.find_one({"_id": p["_id"]})["status"] == "authorized"
    assert db.approvals.count_documents({"tenant_id": T, "proposal_id": p["proposal_id"]}) == n_before

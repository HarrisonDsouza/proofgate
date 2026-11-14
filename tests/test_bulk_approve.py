"""approve_bulk (one transaction) must produce what a loop of approve() produces (live DB, throwaway tenant)."""
import os

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("MONGODB_URI"), reason="needs MongoDB")
VOLATILE = {"_id", "approval_id", "proposal_id", "case_id", "created_at", "session_id", "views", "evidence_hashes_viewed",
            "active_dwell_ms"}


def _pending(db, t, n):
    return [p["proposal_id"] for p in db.proposals.find({"tenant_id": t, "status": "pending_review"}).limit(n)]


def test_bulk_equals_a_loop_of_single_approvals(scratch):
    from pg import review, rules
    from pg.db import get_db
    db = get_db()
    ids = _pending(db, scratch, 12)
    loop_sess = review.open_session(scratch, "dr-demo")["session_id"]
    bulk_sess = review.open_session(scratch, "dr-demo")["session_id"]
    for pid in ids[:6]:
        review.approve(scratch, loop_sess, pid, "Reviewed in batch.")
    out = review.approve_bulk(scratch, bulk_sess, ids[6:], "Reviewed in batch.")
    assert out["submitted"] == 6 and len(set(out["approval_ids"])) == 6
    single = db.approvals.find_one({"tenant_id": scratch, "session_id": loop_sess})
    bulk = list(db.approvals.find({"tenant_id": scratch, "session_id": bulk_sess}))
    assert len(bulk) == 6
    for b in bulk:
        assert set(b) == set(single)                                         # same document shape
        assert {k: v for k, v in b.items() if k not in VOLATILE} == {k: v for k, v in single.items() if k not in VOLATILE}
    for pid, aid in zip(ids[6:], out["approval_ids"], strict=True):                       # each proposal points at its own approval
        p = db.proposals.find_one({"tenant_id": scratch, "proposal_id": pid})
        assert p["status"] == "approved" and p["approval_id"] == aid and p["approved_by"] == "dr-demo"
    rs = db.reviewer_state.find_one({"_id": f"{scratch}|dr-demo"})
    assert len(rs["approval_ts"]) == 12                                      # 6 + 6 timestamps recorded for the G6 window
    assert rules.verify_session_chain(db, scratch, bulk_sess) is True        # chained events, intact
    assert db.review_events.count_documents({"tenant_id": scratch, "session_id": bulk_sess, "type": "approve"}) == 6


def test_bulk_carries_server_timed_views_like_a_single_approval(scratch):
    from pg import review
    from pg.db import get_db
    db = get_db()
    ids = _pending(db, scratch, 3)
    sid = review.open_session(scratch, "dr-demo")["session_id"]
    case = db.proposals.find_one({"tenant_id": scratch, "proposal_id": ids[0]})["case_id"]
    ev = db.cases.find_one({"tenant_id": scratch, "case_id": case})["evidence"][0]["evidence_id"]
    tok = review.fetch_evidence(scratch, sid, case, ev)["view_token"]
    db.view_tokens.update_one({"token": tok}, {"$set": {"active_ms": 12345}})
    review.approve_bulk(scratch, sid, ids, "Reviewed in batch.")
    got = db.approvals.find_one({"tenant_id": scratch, "proposal_id": ids[0]})
    assert got["active_dwell_ms"] == 12345 and got["views"][0]["evidence_id"] == ev
    assert db.approvals.find_one({"tenant_id": scratch, "proposal_id": ids[1]})["active_dwell_ms"] == 0  # no views for it


def test_bulk_is_all_or_nothing_when_a_proposal_moves_on(scratch, monkeypatch):
    from pg import review, rules
    from pg.db import get_db
    db = get_db()
    ids = _pending(db, scratch, 5)
    sid = review.open_session(scratch, "dr-demo")["session_id"]
    real = review._build_approval
    seen = {"n": 0}

    def sneaky(*a, **k):  # after validation, before the transaction: a gate call moves the last proposal on
        seen["n"] += 1
        if seen["n"] == len(ids):
            db.proposals.update_one({"tenant_id": scratch, "proposal_id": ids[-1]}, {"$set": {"status": "authorized"}})
        return real(*a, **k)

    monkeypatch.setattr(review, "_build_approval", sneaky)
    with pytest.raises(review.BadRequest):
        review.approve_bulk(scratch, sid, ids, "Reviewed in batch.")
    assert db.approvals.count_documents({"tenant_id": scratch, "session_id": sid}) == 0
    assert db.proposals.count_documents({"tenant_id": scratch, "proposal_id": {"$in": ids[:-1]}, "status": "pending_review"}) == 4
    assert db.review_events.count_documents({"tenant_id": scratch, "session_id": sid}) == 0
    assert rules.verify_session_chain(db, scratch, sid) is True

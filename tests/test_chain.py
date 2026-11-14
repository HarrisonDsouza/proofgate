"""Live-DB test (skipped without MONGODB_URI): concurrent events never fork the hash chain; tampering is located."""
import os
import threading

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("MONGODB_URI"), reason="needs MongoDB")


def test_concurrent_events_keep_one_chain_and_tamper_is_found():
    from pg import review, rules
    from pg.db import get_db
    db = get_db()
    rv = db.reviewers.find_one({})
    t = rv["tenant_id"]
    sid = review.open_session(t, rv["reviewer_id"])["session_id"]
    ths = [threading.Thread(target=review._event, args=(db, t, sid, rv["reviewer_id"], "C", "heartbeat", 5000)) for _ in range(12)]
    [x.start() for x in ths]
    [x.join() for x in ths]
    assert db.review_events.count_documents({"tenant_id": t, "session_id": sid}) == 12
    assert rules.verify_session_chain(db, t, sid) is True
    db.review_events.update_one({"tenant_id": t, "session_id": sid, "seq": 5}, {"$set": {"credited_ms": 999999}})
    assert rules.verify_session_chain(db, t, sid, first_bad_seq=True) == 5
    db.review_events.update_one({"tenant_id": t, "session_id": sid, "seq": 5}, {"$set": {"credited_ms": 5000}})
    db.review_events.update_one({"tenant_id": t, "session_id": sid, "seq": 7}, {"$set": {"ts": __import__("datetime").datetime(2020, 1, 1, tzinfo=__import__("datetime").timezone.utc)}})
    assert rules.verify_session_chain(db, t, sid, first_bad_seq=True) == 7

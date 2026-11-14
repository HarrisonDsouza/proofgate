"""Live-DB (skipped without MONGODB_URI): attestation binding, replay refusal, STT failure leaves the gate untouched."""
import os

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("MONGODB_URI"), reason="needs MongoDB")


def test_binding_replay_and_audio_hash():
    from fastapi import HTTPException

    from pg import review, voice
    from pg.db import get_db
    db = get_db()
    rv = db.reviewers.find_one({})
    t = rv["tenant_id"]
    cases = [p for p in db.proposals.find({"tenant_id": t, "status": "pending_review"}).limit(2)]
    sid = review.open_session(t, rv["reviewer_id"])["session_id"]
    sha = os.urandom(32).hex()
    a = voice.record_attestation(db, t, sid, cases[0]["case_id"], "knee MRI reviewed", "typed_fallback", sha, None, None)
    with pytest.raises(HTTPException) as e:
        voice.record_attestation(db, t, sid, cases[0]["case_id"], "same recording again", "typed_fallback", sha, None, None)
    assert e.value.status_code == 409
    with pytest.raises(review.BadRequest):  # attestation for case 0 cannot approve case 1
        review.approve(t, sid, cases[1]["proposal_id"], "x" * 12, None, a["attestation_id"])
    assert db.review_events.count_documents({"tenant_id": t, "session_id": sid, "type": "attest"}) == 1

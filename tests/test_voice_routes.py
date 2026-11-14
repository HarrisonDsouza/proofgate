"""HTTP-level checks of the voice routes (live DB; skipped without MONGODB_URI). ElevenLabs is always mocked."""
import dataclasses
import os
import threading
import time

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("MONGODB_URI"), reason="needs MongoDB")
KEY = "k" * 32
T = "payer-acme"


@pytest.fixture()
def client(monkeypatch):
    from fastapi.testclient import TestClient

    from pg import auth, voice
    from pg.main import app
    monkeypatch.setattr(auth, "settings", dataclasses.replace(auth.settings, console_key=KEY))
    monkeypatch.setattr(voice, "settings", dataclasses.replace(voice.settings, elevenlabs_api_key="test"))
    calls = {"stt": 0, "tts": 0}
    monkeypatch.setattr(voice, "transcribe", lambda *a, **k: calls.__setitem__("stt", calls["stt"] + 1) or {"text": "x", "model": "m", "audio_seconds": 1})
    monkeypatch.setattr(voice, "synthesize", lambda *a, **k: calls.__setitem__("tts", calls["tts"] + 1) or b"mp3")
    c = TestClient(app)
    c.calls = calls
    return c


def H(extra=None):
    return {"X-Console-Key": KEY, "X-Tenant-Id": T, **(extra or {})}


def test_voice_routes_need_the_console_key(client):
    assert client.post("/api/voice/attest", content=b"x", headers={"X-Tenant-Id": T, "X-Session-Id": "s", "X-Case-Id": "c"}).status_code == 401
    assert client.get("/api/voice/receipt/CLM-A-0001", headers={"X-Tenant-Id": T}).status_code == 401
    assert client.calls == {"stt": 0, "tts": 0}


def test_unknown_case_or_session_is_refused_before_any_elevenlabs_call(client):
    assert client.get("/api/voice/receipt/NOPE", headers=H()).status_code == 404
    r = client.post("/api/voice/attest", content=b"audio", headers=H({"X-Session-Id": "S-none", "X-Case-Id": "CLM-A-0001"}))
    assert r.status_code == 404
    assert client.calls == {"stt": 0, "tts": 0}


def test_oversized_audio_is_rejected_on_content_length(client):
    r = client.post("/api/voice/attest", content=b"x" * (10 * 1024 * 1024 + 1), headers=H({"X-Session-Id": "S", "X-Case-Id": "C"}))
    assert r.status_code == 413 and client.calls["stt"] == 0


def test_slow_speech_to_text_does_not_block_heartbeats(client, monkeypatch):
    from pg import review, voice
    from pg.db import get_db
    db = get_db()
    sid = review.open_session(T, "dr-demo")["session_id"]
    case = db.cases.find_one({"tenant_id": T})["case_id"]
    monkeypatch.setattr(voice, "transcribe", lambda *a, **k: time.sleep(1.5) or {"text": "knee mri reviewed", "model": "m", "audio_seconds": 2})
    t = threading.Thread(target=lambda: client.post("/api/voice/attest", content=os.urandom(64),
                                                    headers=H({"X-Session-Id": sid, "X-Case-Id": case})))
    t.start()
    time.sleep(0.3)
    t0 = time.perf_counter()
    assert client.get("/healthz").status_code == 200
    assert time.perf_counter() - t0 < 0.8, "the event loop was blocked by the Scribe call"
    t.join()


def test_examiner_never_exposes_session_or_grant_ids(client):
    from pg import auth, rules
    from pg.db import get_db
    db = get_db()
    from pg import review
    sid = review.open_session(T, "dr-demo")["session_id"]
    prop = db.proposals.find_one({"tenant_id": T, "status": "pending_review"})
    ap = review.approve(T, sid, prop["proposal_id"], "Reviewed this case thoroughly.")
    out = rules.examiner(T, ap["case_id"])
    def keys(x):
        if isinstance(x, dict):
            for k, v in x.items():
                yield k
                yield from keys(v)
        elif isinstance(x, list):
            for v in x:
                yield from keys(v)
    assert not ({"session_id", "grant_id"} & set(keys(out)))
    assert auth  # silence unused import


def test_ops_is_tenant_scoped_and_bounded(client):
    from pg.db import get_db
    from pg.observability import record_telemetry
    db = get_db()
    record_telemetry(db, "gate_latency_ms", 123.0, tenant_id="tenant-ops-test")
    mine = client.get("/api/ops", headers={"X-Tenant-Id": "tenant-ops-test"}).json()
    other = client.get("/api/ops", headers={"X-Tenant-Id": "some-other-tenant"}).json()
    assert mine.get("gate_latency_ms", {}).get("n", 0) >= 1 and "gate_latency_ms" not in other
    assert client.get("/api/ops?minutes=0", headers={"X-Tenant-Id": T}).status_code == 422
    assert client.get("/api/ops?minutes=999999", headers={"X-Tenant-Id": T}).status_code == 422

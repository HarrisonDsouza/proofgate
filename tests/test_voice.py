import dataclasses

import httpx
import pytest

from pg import voice


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setattr(voice, "settings", dataclasses.replace(voice.settings, elevenlabs_api_key="test-key"))


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_stt_falls_back_to_v2_when_v3_rejected():
    seen = []

    def h(req):
        body = req.read()
        model = b"scribe_v3" in body and "scribe_v3" or "scribe_v2"
        seen.append(model)
        assert req.headers["xi-api-key"] == "test-key"
        if model == "scribe_v3":
            return httpx.Response(422)
        return httpx.Response(200, json={"text": " knee MRI shows loss ", "words": [{"end": 3.2}]})

    r = voice.transcribe(b"abc", "audio/webm", client(h))
    assert seen == ["scribe_v3", "scribe_v2"] and r["model"] == "scribe_v2"
    assert r["text"] == "knee MRI shows loss" and r["audio_seconds"] == 3.2


def test_stt_all_models_fail_raises_unavailable():
    with pytest.raises(voice.VoiceUnavailable):
        voice.transcribe(b"abc", "audio/webm", client(lambda r: httpx.Response(500)))


def test_no_key_means_unavailable(monkeypatch):
    monkeypatch.setattr(voice, "settings", dataclasses.replace(voice.settings, elevenlabs_api_key=""))
    with pytest.raises(voice.VoiceUnavailable):
        voice.synthesize("hi")


def test_tts_returns_bytes_and_truncates():
    def h(req):
        assert req.url.params["output_format"] == "mp3_44100_128"
        assert len(__import__("json").loads(req.read())["text"]) <= 1500
        return httpx.Response(200, content=b"ID3mp3")

    assert voice.synthesize("x" * 5000, http=client(h)) == b"ID3mp3"


def test_receipt_text_is_plain_facts_from_state():
    ex = {"approval": {"case_id": "C1", "reviewer_id": "dr-demo", "active_dwell_ms": 41000},
          "gate_decisions": [{"decision": "REFUSE", "policy_version": 2, "checks": [{"rule": "G5_DWELL", "pass": False}]}],
          "denial": None, "suspension": {"rule": "G6_RATE"}}
    t = voice.receipt_text(ex)
    assert "41 seconds" in t and "REFUSE" in t and "G5_DWELL" in t and "G6_RATE" in t

"""ElevenLabs voice layer: spoken attestation (Scribe STT) and the examiner's voice receipt (TTS).

Voice is EVIDENCE, never a decision (CLAUDE.md rule 7). Nothing here is read by gate.execute or checks.evaluate:
a voice outage cannot block or allow a denial. The ElevenLabs key stays on the server.

Stored in Atlas (`attestations`): transcript, audio SHA-256 and duration (NOT the audio itself, which is
personal data), the STT model, a deterministic attestation score (pg/attest_score.py) and its parts.
The detector reads the score as a second signal; see detector.check_reviewer.
"""
from __future__ import annotations

import hashlib
import secrets
import time

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response
from pymongo.errors import DuplicateKeyError

from pg import attest_score, review
from pg import observability as obs
from pg.config import settings
from pg.db import get_db, now

router = APIRouter()
API = "https://api.elevenlabs.io/v1"
STT_MODELS = ("scribe_v3", "scribe_v2")          # scribe_v1 is deprecated (verified 2026-11-14)
TTS_MODEL = "eleven_flash_v2_5"                   # ~100 ms; receipts are short
DEFAULT_VOICE = "JBFqnCBsd6RMkjVDRZzb"            # ElevenLabs quickstart voice
MAX_AUDIO_BYTES = 10 * 1024 * 1024
_http = httpx.Client(timeout=httpx.Timeout(30.0, connect=5.0))


class VoiceUnavailable(Exception):
    pass


def configured() -> bool:
    return bool(settings.elevenlabs_api_key)


def transcribe(audio: bytes, content_type: str, http: httpx.Client | None = None) -> dict:
    """Scribe speech-to-text. Tries scribe_v3 then scribe_v2. Returns {text, model, audio_seconds}."""
    if not configured():
        raise VoiceUnavailable("ELEVENLABS_API_KEY not set")
    c = http or _http
    last = "no model tried"
    for model in STT_MODELS:
        t0 = time.perf_counter()
        try:
            r = c.post(f"{API}/speech-to-text", headers={"xi-api-key": settings.elevenlabs_api_key},
                       data={"model_id": model, "timestamps_granularity": "word", "tag_audio_events": "false"},
                       files={"file": ("attestation.webm", audio, content_type or "audio/webm")})
        except httpx.HTTPError as e:
            last = f"{model}: {type(e).__name__}"
            obs.STT_CALLS.labels("false").inc()
            continue
        ms = (time.perf_counter() - t0) * 1000
        obs.STT_SECONDS.observe(ms / 1000)
        if r.status_code == 200:
            j = r.json()
            words = j.get("words") or []
            dur = j.get("audio_duration_secs") or (max((w.get("end") or 0) for w in words) if words else None)
            obs.STT_CALLS.labels("true").inc()
            obs.log_event("stt", model=model, ms=round(ms, 1), words=len(words))
            return {"text": (j.get("text") or "").strip(), "model": model, "audio_seconds": dur}
        obs.STT_CALLS.labels("false").inc()
        last = f"{model}: HTTP {r.status_code}"
    raise VoiceUnavailable(last)


def synthesize(text: str, voice_id: str = DEFAULT_VOICE, http: httpx.Client | None = None) -> bytes:
    if not configured():
        raise VoiceUnavailable("ELEVENLABS_API_KEY not set")
    c = http or _http
    r = c.post(f"{API}/text-to-speech/{voice_id}", params={"output_format": "mp3_44100_128"},
               headers={"xi-api-key": settings.elevenlabs_api_key},
               json={"text": text[:1500], "model_id": TTS_MODEL})
    if r.status_code != 200:
        raise VoiceUnavailable(f"tts HTTP {r.status_code}")
    return r.content


def _corpus(db, tenant: str) -> tuple[dict[str, int], int]:
    """Document frequency of every term across the tenant's cases. O(total evidence tokens), cached per tenant."""
    hit = _DF_CACHE.get(tenant)
    if hit and time.time() - hit[2] < 300:
        return hit[0], hit[1]
    df: dict[str, int] = {}
    n = 0
    for case in db.cases.find({"tenant_id": tenant}, {"codes": 1, "evidence": 1}):
        n += 1
        for t in attest_score.case_terms(case):
            df[t] = df.get(t, 0) + 1
    _DF_CACHE[tenant] = (df, n, time.time())
    return df, n


_DF_CACHE: dict[str, tuple[dict[str, int], int, float]] = {}


def record_attestation(db, tenant: str, session_id: str, case_id: str, transcript: str, source: str,
                       audio_sha256: str | None, audio_seconds: float | None, stt_model: str | None) -> dict:
    sess = db.reviewer_sessions.find_one({"tenant_id": tenant, "session_id": session_id})
    if not sess:
        raise HTTPException(404, "unknown session")
    case = db.cases.find_one({"tenant_id": tenant, "case_id": case_id})
    if not case:
        raise HTTPException(404, "unknown case")
    prev = [a["transcript"] for a in db.attestations.find({"tenant_id": tenant, "reviewer_id": sess["reviewer_id"]},
                                                          {"transcript": 1}).sort("created_at", -1).limit(10)]
    df, n = _corpus(db, tenant)
    opened = {t["evidence_id"] for t in db.view_tokens.find({"tenant_id": tenant, "session_id": session_id, "case_id": case_id},
                                                            {"evidence_id": 1})}
    sc = attest_score.score(transcript, case, prev, audio_seconds, df, max(n, 1), opened_ids=opened)
    doc = {"tenant_id": tenant, "attestation_id": f"AT-{secrets.token_hex(5)}", "session_id": session_id,
           "reviewer_id": sess["reviewer_id"], "case_id": case_id, "transcript": transcript, "source": source,
           "audio_sha256": audio_sha256, "audio_seconds": audio_seconds, "stt_model": stt_model,
           "score": sc, "created_at": now()}
    try:
        db.attestations.insert_one(doc)
    except DuplicateKeyError as e:  # same recording replayed: refused by MongoDB's unique index on audio_sha256
        raise HTTPException(409, "this exact recording was already used as an attestation") from e
    review._event(db, tenant, session_id, sess["reviewer_id"], case_id, "attest", 0, None, audio_sha256=audio_sha256)
    doc.pop("_id", None)
    return doc


@router.get("/api/voice/status")
def status():
    return {"configured": configured(), "stt_models": list(STT_MODELS), "tts_model": TTS_MODEL}


@router.post("/api/voice/attest", status_code=201)
async def attest(request: Request, x_tenant_id: str = Header(...), x_session_id: str = Header(...),
                 x_case_id: str = Header(...), x_fallback_text: str | None = Header(None)):
    """Body: raw audio bytes (MediaRecorder webm/opus). On any voice failure the reviewer's typed text is
    stored instead (source='typed_fallback'); the approval flow never depends on ElevenLabs."""
    audio = await request.body()
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "audio too large")
    db = get_db()
    sha = hashlib.sha256(audio).hexdigest() if audio else None
    try:
        if not audio:
            raise VoiceUnavailable("empty audio")
        r = transcribe(audio, request.headers.get("content-type", "audio/webm"))
        if not r["text"]:
            raise VoiceUnavailable("empty transcript")
        doc = record_attestation(db, x_tenant_id, x_session_id, x_case_id, r["text"], "elevenlabs_stt", sha,
                                 r["audio_seconds"], r["model"])
    except VoiceUnavailable as e:
        if not x_fallback_text:
            raise HTTPException(503, f"voice unavailable ({e}); type the attestation instead") from e
        obs.log_event("voice_fallback", reason=str(e))
        doc = record_attestation(db, x_tenant_id, x_session_id, x_case_id, x_fallback_text, "typed_fallback", sha, None, None)
    return doc


@router.get("/api/voice/receipt/{case_id}")
def receipt(case_id: str, x_tenant_id: str = Header(...)):
    """Spoken audit receipt: the examiner hears the case's chain of custody in about 15 seconds."""
    from pg import rules
    ex = rules.examiner(x_tenant_id, case_id)
    text = receipt_text(ex)
    try:
        audio = synthesize(text)
    except VoiceUnavailable as e:
        raise HTTPException(503, f"voice unavailable ({e})") from e
    return Response(audio, media_type="audio/mpeg", headers={"X-Receipt-Text": text[:200].replace("\n", " ")})


def receipt_text(ex: dict) -> str:
    """Plain facts only, assembled from stored state. No model writes this text."""
    ap, den = ex.get("approval") or {}, ex.get("denial") or {}
    gates = ex.get("gate_decisions") or []
    parts = [f"Case {ap.get('case_id', 'unknown')}."]
    if ap:
        parts.append(f"Reviewed by {ap.get('reviewer_id')} for {round((ap.get('active_dwell_ms') or 0) / 1000)} seconds, "
                     f"timed by the server.")
    if gates:
        g = gates[-1]
        failed = [c["rule"] for c in g.get("checks", []) if not c["pass"]]
        parts.append(f"Gate said {g['decision']} under policy version {g['policy_version']}"
                     + (f", failing {', '.join(failed)}." if failed else "."))
    if den:
        parts.append(f"Denial status {den.get('status')}, read back from the claims system.")
    if ex.get("suspension"):
        parts.append(f"The reviewer was suspended by {ex['suspension'].get('rule')}.")
    return " ".join(parts)

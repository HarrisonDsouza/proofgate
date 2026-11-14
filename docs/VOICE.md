# Voice layer (ElevenLabs): evidence, never a decision

Owner of the idea: Sukhman (built on branch `sukhman`; `pg/voice.py` and `ui/src/voice/` are Neil's folders in WORKFLOW.md, so hand over before a PR).

| Feature | Endpoint | ElevenLabs call | Stored in Atlas | If ElevenLabs is down |
|---|---|---|---|---|
| Spoken attestation | `POST /api/voice/attest` (raw audio body; headers X-Session-Id, X-Case-Id) | Scribe `POST /v1/speech-to-text`, `scribe_v3` then `scribe_v2` | `attestations`: transcript, `audio_sha256`, speech seconds, score parts. **No audio is stored.** | Typed text is stored (`source=typed_fallback`); the approval never waits on voice |
| Voice receipt | `GET /api/voice/receipt/{case_id}` | TTS `POST /v1/text-to-speech/{voice}` (`eleven_flash_v2_5`) | nothing (regenerated on demand) | 503; the examiner JSON is still shown |

Verified API facts (checked 2026-11-14): scribe_v1 is deprecated; only `model_id` is required for STT; TTS `output_format=mp3_44100_128`.
Not verified: that the quickstart voice id works on every plan; WebM from `MediaRecorder` (docs list WebM/Opus as supported). **Test both with a real key before the demo.**

## Why this helps the audit story (and is hard to fake)
- A spoken, case-specific statement cannot be bulk-stamped: 50 attestations take 50x real time.
- `pg/attest_score.py` scores it deterministically (no LLM): IDF-weighted specificity, boilerplate overlap with the reviewer's last 10, speech pace from word timestamps, and **unviewed-evidence terms**: words the reviewer said that appear only in evidence the server never saw them open. Speech joined with server-timed views is the signal no other tool has.
- `audio_sha256` has a unique index (`one_use_per_recording`): replaying one recording is refused by MongoDB itself (HTTP 409).
- `review.approve` rejects an `attestation_id` from another session or case (HTTP 400): one good recording cannot cover 50 cases.
- An `attest` event with the audio hash is appended to the session hash chain (verify: `GET /api/verify/chain/{session_id}`).

## What it must never do
- No G9, no change to `checks.evaluate`. A missing or failed attestation is never penalised.
- The detector only **flags** attestations (`BOILERPLATE`, `UNVIEWED_EVIDENCE_NAMED`, `PACE_IMPLAUSIBLE`) for the examiner; it never suspends on voice (no calibration data; an STT outage must not suspend honest reviewers).
- The ElevenLabs key is server-side only (`ELEVENLABS_API_KEY` in `.env`).

## Check commands
```bash
make ci                                   # includes mocked ElevenLabs tests (no network)
curl -s localhost:8080/api/voice/status   # {"configured": true|false, ...}
# live DB: binding, replay refusal, chain
pytest -q tests/test_voice_live.py tests/test_chain.py
```

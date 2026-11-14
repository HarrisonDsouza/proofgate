# Handoff board

The orchestrator (assistant) keeps this current. One row per handoff.
**Done means the check command passes against Atlas.** Someone saying it works does not count.
Status values: `todo` · `in progress` · `ready` · `accepted` · `cut`.

| Id | From → To | What | Done check | Needed by | Status |
|---|---|---|---|---|---|
| H1 | Harry → all | `.env` values (shared privately, **never in git or chat**) + smoke test passes | `make smoke` prints PASS for the transaction and the change stream | 12:40 | todo |
| H2 | Harry → Sukhman | `setup_db` + seed: collections, validators, indexes, `dr-demo`, `dr-stamper`, 50 cases, policy v1 | Atlas Data Explorer shows `proofgate.cases` count; Sukhman's `GET /api/queue` returns proposals | 12:40 | todo |
| H3 | Sukhman → Harry | Gate endpoints per PRD §8: sessions, evidence + view tokens, heartbeat, approvals (+ bulk), `gate/execute`, `gate/confirm` | curl sequence for an honest approval → ALLOW; bulk 50 → 0 ALLOW | 13:30 | todo |
| H4 | Harry → Sukhman | Mock claims system on :8000: apply with grant (atomic consume), 403 + `target_log` otherwise, GET read-back, idempotent compensate | `make bypass` → 403; apply with a valid grant → 200 then a second use → 403 | 13:15 | todo |
| H5 | Harry → Neil | Agent code (`py/agent/triage.py`, `executor.py`) runs end to end | `make agent` processes one approved proposal | 14:00 | todo |
| H6 | Neil → Harry | `@traceable` on triage and executor steps; grant ids redacted | LangSmith shows triage → gate → apply → confirm for one case | 14:45 | todo |
| H7 | Neil → Harry | Angular "Speak attestation" component + `POST /voice/attest` + `attestations` writes | Recording a clip creates an `attestations` doc with a transcript | 15:00 (go/no-go) | todo |
| H8 | Neil → Sukhman | Approvals accept `attestation_id`; examiner API returns the attestation | `POST /api/approvals` with `attestation_id` stores it; examiner JSON shows it | 15:00 | todo |
| H9 | Sukhman → Harry | Suspension txn, detector (resume token), compensation worker, `X-Debug-Pause-Ms` hook | `make test-conflict` (a) and (d) PASS | 14:45 | todo |
| H10 | Sukhman → Harry | Examiner API `GET /api/examiner/cases/{id}` | JSON shows views, checks, grant, `target_log`, suspension | 14:30 | todo |
| H11 | Neil → all | 1-minute video voiceover (ElevenLabs) + edited video | Plays with audio from the uploaded link | 16:15 | todo |

## Interface rules

- The API shapes in PRD §8 are the contract. Anyone who changes one updates this board and tells the other person **before** pushing.
- Never put secrets in this file, commits, chat or traces.

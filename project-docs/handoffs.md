# Handoff board

The orchestrator (assistant) keeps this current. One row per handoff. Owners and folders follow `COMBINED-PLAN.md` §2.
**Done means the check command passes against Atlas.** Someone saying it works does not count.
Status values: `todo` · `in progress` · `ready` · `accepted` · `cut`.

| Id | From → To | What | Done check | Needed by | Status |
|---|---|---|---|---|---|
| H0 | Orchestrator → all | Sukhman's code (`pg/`, `seed/`, `eval/`, `tests/`, `data/`, `static/`, `Makefile`, CI) imported to `main` without the Claude attribution trailer | `make install test` passes on a fresh clone | asap | accepted (PR #1, 15 tests pass) |
| H1 | Harry → all | Sandbox cluster + `.env` values (shared by private DM, **never in git or chat**) + smoke | `make smoke` prints PASS for the transaction and the change stream | 13:15 | todo |
| H2 | Harry → Sukhman | `make setup seed` on the sandbox: collections, validators, indexes, reviewers, cases, policy v1 | Atlas shows `proofgate.cases`; `curl -H 'X-Tenant-Id: payer-acme' :8080/api/queue` returns proposals | 13:15 | todo |
| H3 | Sukhman → Harry | Gate + review flow live: sessions, evidence views, heartbeats, approvals, bulk, gate execute/confirm | `DEMO_DEBUG_HOOKS=true make test-conflict` all PASS; bulk 50 → executed 0 | 13:45 | todo |
| H4 | Harry → Sukhman | Mock claims system live: apply with grant, 403 otherwise, read-back, idempotent reopen | `make bypass` → two PASS lines | 13:15 | todo |
| H5 | Harry → Neil | Agent (`pg/agent.py`) runs end to end against the sandbox | One approved proposal executes and is CONFIRMED by read-back | 14:00 | todo |
| H6 | Neil → Harry | Tracing on agent steps; grant ids redacted | LangSmith shows triage → gate → apply → confirm for one case | 14:45 | todo |
| H7 | Neil → Harry | `POST /api/voice/attest` + `attestations` + React "Speak attestation" button | A recorded clip creates an `attestations` doc with a transcript | 15:00 (go/no-go) | todo |
| H8 | Neil → Sukhman/Harry | Approvals accept `attestation_id`; examiner shows it | `POST /api/approvals` with `attestation_id` stores it; examiner JSON shows it | 15:00 | todo |
| H9 | Sukhman → Harry | Detector kill/restart demo + `make explain` IXSCAN | Kill `make detector` mid-burst, restart → exactly one active suspension | 14:45 | todo |
| H10 | Harry → all | React reviewer + examiner pages on the live API (fallback: `static/`) | Bulk 50 and an honest review both work from http://localhost:4200 | 15:15 | todo |
| H11 | Neil → all | 1-minute video voiceover (ElevenLabs) + edited video | Plays with audio from the uploaded link | 16:30 | todo |

## Interface rules

- The API shapes in PRD §8 (as implemented in `pg/main.py`) are the contract. Anyone who changes one updates this board and tells the others **before** pushing.
- Never put secrets in this file, commits, chat or traces.

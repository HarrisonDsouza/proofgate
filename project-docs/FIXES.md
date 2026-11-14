# Must-fix list, by owner

Merged from [research/security-review.md](research/security-review.md) (S#) and [research/code-review-baseline.md](research/code-review-baseline.md) (C#). Both are source-only reviews, so confirm each fix on Atlas.

**Order:** first run `make smoke setup seed bypass test-conflict rules` and fix whatever fails. Then work through P1 before 13:45 and P2 before 16:00. P3 only if there is time.
The tech lead ticks items off here when the PR that fixes them is merged.

## Sukhman (`pg/review.py`, `gate.py`, `checks.py`, `detector.py`, `eval/test_conflict.py`)

| P | Id | Fix | File | Status |
|---|---|---|---|---|
| P1 | S3 / C8 | Heartbeat credit must be atomic: put `last_hb_at` in the update filter, give 0 credit on a miss, ignore heartbeats under 1 s apart, and clamp `active_ms <= open_ms` | `review.py:83-95, 107-114` | todo |
| P1 | C4 | Detector: try/except per event (log and continue); fresh watch on `ChangeStreamHistoryLost` | `detector.py:84-92` | todo |
| P1 | S9 / C6 | `approve` only from `pending_review`/`needs_review` (conditional update, abort on 0 matched); G1 requires `proposal.status == approved` and a matching `approval_id` | `review.py:117-149`, `checks.py:39` | todo |
| P1 | S2 | Policy update: allow-list keys with int types, reject `baseline_only_existence`, allow tightening only | `gate.py:199-213` | todo |
| P2 | S4 | Exclusive focus per reviewer across sessions; cap open sessions per reviewer | `review.py:58-61` | todo |
| P2 | S12 / C5 | Suspension also compensates `AUTHORIZED` denials; `confirm()` guards on `AUTHORIZED` and refuses if the reviewer is suspended | `gate.py:69, 183-196` | todo |
| P2 | A3 | Detector: save the resume token while idle (`cs.resume_token`), check `cs.alive`, and use `error_labels=` instead of `_add_error_label` on `VersionMoved` | `detector.py:84-92`, `gate.py` | todo |
| P2 | C7 | Bulk: validate all ids before the first approval | `review.py:152-155` | todo |
| P2 | C9 | `_event`: one transaction, or build the chain by `seq` order (otherwise R8 goes red under concurrency) | `review.py:28-37` | todo |
| P2 | C11 | Add `test-conflict` (d) detector crash and resume; make (c) really stop the detector | `eval/test_conflict.py` | todo |
| P3 | C11 | Seed acme policy with `detector.cusum` so the drifter beat can fire. **Seed is Harry's folder; Sukhman supplies the values.** | `seed/generate.py` | todo |

## Harry (`pg/target.py`, `pg/agent.py`, `pg/rules.py`, `seed/`, `Makefile`, `static/`)

| P | Id | Fix | File | Status |
|---|---|---|---|---|
| P1 | S1 / C1 | Delete the HTTP `/compensate` route (the worker calls `compensate()` directly) | `target.py:66-69` | done: PR #6 |
| P1 | C3 | `executor_loop(once=True)`: return when paused | `agent.py:49-51` | done: PR #6 |
| P1 | C2 | Banner shows "Executed X of N" with N = `bulk.submitted`; demo with `RUN_BACKGROUND=0` | `static/index.html`, `.env` | done: PR #6 (banner; choose RUN_BACKGROUND on the day) |
| P2 | — | `make bypass` also curls `/target/.../apply` (and compensate is gone) over HTTP | `eval/bypass.py` | todo |
| P2 | — | `make e2e`: the honest path end to end, then suspend, compensate and check R6. Run it before every dry run. | `eval/`, `Makefile` | done: PR #9 |
| P2 | — | Missing `make burst-forged` (demo.md uses it); save `make test-conflict > docs/test-conflict.txt` | `Makefile` | todo |
| P1 | A1 | `make smoke` exits 0 even on FAIL, and its watcher uses a fixed 1 s sleep (false FAIL). Exit non-zero on FAIL; wait for the stream to open | `pg/db.py:137-153` | todo |
| P2 | A2 | `apply`: abort (don't consume the grant) if the record update matched 0; set snapshot and majority concerns | `target.py:29, 37` | todo |
| P3 | low | `innerHTML` → `textContent` for data fields | `static/index.html:39,41` | todo |

## Shared files (`pg/main.py`, `pg/config.py`): one person, tell the others first

| P | Id | Fix | Status |
|---|---|---|---|
| P1 | S6 / S2 / S5 | One `SUPERVISOR_KEY` header on `/api/policies`, `/api/suspensions`, `/api/agent/pause`, `/api/agent/run-once`; `DEMO_REVIEWER_KEY` on `/api/sessions` | done: PR #6, one `CONSOLE_KEY` (`X-Console-Key`) on sessions + all control routes |
| P1 | S7 | Refuse to start if `AGENT_SERVICE_KEY` is the default or under 24 characters; use `secrets.compare_digest` | done: PR #6 |
| P1 | S8 | Remove the `X-Debug-Pause-Ms` header (`test_conflict` calls Python directly); demo with `DEMO_DEBUG_HOOKS=false` | done: PR #6 |
| P2 | S10 | Pydantic models (`str`, `max_length`, bounded `list[str]`) instead of `body: dict` | todo |
| P2 | S11 | Cap `limit` and bulk at 100; lock `run-once` | todo |
| P2 | — | Unsuspend or reseed path for the demo seat | todo |

## Setup notes from [research/atlas-tier.md](research/atlas-tier.md)

- **Database user:** give it **Atlas admin**, or add `dbAdmin` on `proofgate`. The plain "read and write" role can't run `collMod`, so a second `make setup` would fail.
- **Free tier (M0):** throttled at 100 ops/s, so "approve 50" (about 750 ops) takes several seconds. Flex allows 500 ops/s. Transactions are capped at 60 s on Free and Flex.

## Say on stage instead of fixing

- Reviewer identity is demo-grade (no SSO).
- Dwell measures attention, not reading.
- The hash chain is unkeyed.
- The target shares the process with the gate.
- Tenant isolation is query-level.
- The data is synthetic.

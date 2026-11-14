# Harry: starting prompt

## What to pull

```bash
git clone https://github.com/HarrisonDsouza/proofgate.git && cd proofgate
git checkout harry
cp .env.example .env     # then fill MONGODB_URI (README "Sandbox setup" step 3)
```

## What you own

- **Engineer A (Python), in `py/`:**
  - Atlas setup and the smoke test
  - `setup_db` (collections, validators, indexes, TTL) and seed data
  - the mock claims system (FastAPI :8000; refuses without a grant)
  - the triage agent and executor loop
  - rules R1-R8, the evaluation, the `test-conflict` script, reset
  - `py/requirements.txt` and the `Makefile`
- **Reduced Engineer C (Angular), in `ui/`:**
  - the review page: evidence panel, heartbeats, Approve, the red "approve 50" button, the result banner
  - the examiner page
- PRD items: M1, M2, M3, M8, M9, M12, M13 (page), M14, M15, M16, M17.

Use two Claude Code sessions, one for `py/` and one for `ui/`, so two writers never touch the same files.

## First steps, in order

1. **Atlas cluster in the hackathon sandbox:** README step 2. Then DM the connection string to Sukhman and Neil.
2. Python session: paste the prompt below. The first output is `py/requirements.txt`, `py/db/smoke.py` and a `Makefile` with `smoke`.
3. Run `make smoke`. Both the transaction and the change stream must PASS. If either fails, tell MongoDB staff immediately.
4. `setup_db.py` + `seed/generate.py` → `make setup`. Open a PR. Mark handoff H2 `ready` for Sukhman.
5. Then the mock claims system (H4) → executor → `make bypass`, before 13:45.
6. UI session (from about 12:40): scaffold `ui/` with the proxy, and build the review page against mock JSON shaped like PRD §8.

## Paste into Claude Code (Python session)

```
You are helping a 3-person hackathon team build "ProofGate". Read CLAUDE.md, START-HERE.md and docs/PRD.md
completely before writing code, then follow the PRD exactly (Section 7 data model, 8 architecture and API
contract, 11 hour plan, 12 tests and eval). Also read README.md and WORKFLOW.md.

My role: Engineer A (Python) - py/ : smoke test, setup_db, seed, target FastAPI (mock claims system),
agent triage + executor, rules R1-R8, eval, test_conflict, reset, plus py/requirements.txt and the Makefile.
I work on branch `harry` and only touch py/ (not py/voice/), Makefile, and docs/.

Non-negotiable rules:
1. MongoDB Atlas is the only state store; URI from env MONGODB_URI, DB from DB_NAME (load .env with
   python-dotenv first). Never hard-code or commit secrets.
2. Every document has tenant_id; every compound index leads with it; every query filters by it.
3. The target applies a status change only by atomically consuming a valid grant in a transaction;
   otherwise 403 + a target_log entry.
4. Never invent results. Numbers come only from running make eval / make rules / Atlas queries.
5. Build MUST items first, in the Section 11 order for Engineer A. Keep it simple: no Docker, no auth framework.
6. After each piece, give me the exact command that proves it works against Atlas.

Start now: create py/requirements.txt, py/db/smoke.py (one multi-document transaction + one change-stream
event, prints PASS/FAIL for each) and a Makefile with `smoke`. Then tell me what to run.
```

## Paste into Claude Code (UI session, from about 12:40)

```
Read CLAUDE.md, docs/PRD.md (Sections 6 M12-M13, 8 API contract, 13 demo), README.md and WORKFLOW.md.
My role: reduced Engineer C (Angular) in ui/ only (not ui/src/app/voice/). Build only two pages: the review
page (one case at a time, cited evidence buttons, heartbeat every 5 s only while the tab is visible and there
was input in the last 15 s, attestation + Approve, the red "Select all, approve 50" button, a result banner
polling /api/dashboard) and the examiner page /examiner/:caseId. Scaffold with Angular CLI, routing, CSS,
and proxy.conf.json (/api -> :8080, /py -> :8000 with pathRewrite /py -> ""). Start against mock JSON
shaped exactly like PRD Section 8, then switch to the real API when Sukhman's endpoints land on main.
Never compute or send dwell time from the browser.
```

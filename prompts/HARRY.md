# Harry: starting prompt

## What to pull

```bash
git clone https://github.com/HarrisonDsouza/proofgate.git && cd proofgate
git checkout harry
cp .env.example .env     # then fill MONGODB_URI (README "Sandbox setup" step 3)
```

## What you own (COMBINED-PLAN §2)

- **Atlas setup**: the sandbox cluster, `make smoke`.
- **Data**: `pg/db.py` (validators, indexes, TTL), `seed/`, `data/`.
- **Mock claims system**: `pg/target.py` (consume a grant, or 403).
- **Agent**: `pg/agent.py` (triage + executor).
- **Rules and examiner replay**: `pg/rules.py`.
- **Evaluation**: `eval/simulate.py`, `eval/calibrate_detector.py`, `eval/bypass.py`, `docs/PREREGISTRATION.md`.
- **React UI in `ui/`**: the reviewer page and the examiner page.
- `Makefile`, `README.md`.

Use two Claude Code sessions, one for the Python work and one for `ui/`, so two writers never touch the same files.

## First steps, in order

1. **Atlas cluster in the hackathon sandbox** (README step 2). DM the connection string to Sukhman and Neil.
2. **`make install smoke`.** Both the transaction and the change stream must PASS. If either fails, tell MongoDB staff immediately.
3. **`make setup seed`, then `make dev`, then `make bypass`.** You need two PASS lines. This is the 13:15 checkpoint.
4. **UI session:** scaffold `ui/` with Vite + React + TypeScript, React Router and TanStack Query. Set the dev server to port 4200 with a proxy for `/api`, `/target`, `/rules` and `/metrics` to :8080. Build the reviewer page against the live API.
5. **Agent and rules live**, then `make rules`. Mark handoff H5 `ready` for Neil.
6. **Examiner page.** If time runs short, `static/` is the fallback.
7. **Eval:** `make calibrate-prd` (or `calibrate-detector` if volunteers ran) → `make eval` → merge PREREGISTRATION → `make eval-heldout` **once** → `make baseline` → paste the output into the README unedited.

## Paste into Claude Code (Python session)

```
You are helping a 3-person team build "ProofGate" at a MongoDB hackathon today. Read CLAUDE.md, README.md,
WORKFLOW.md, project-docs/COMBINED-PLAN.md, project-docs/hackathon-rules.md and docs/HANDOFF.md first, then
docs/PRD.md (behaviour spec). Precedence: COMBINED-PLAN -> HANDOFF -> PRD.

My role (Harry): Atlas setup, data (pg/db.py, seed/, data/), the mock claims system (pg/target.py), the agent
(pg/agent.py), rules + examiner replay (pg/rules.py), and evaluation (eval/ except test_conflict.py,
docs/PREREGISTRATION.md). I work on branch `harry` and stay in those files. I ask before touching shared files
(pg/main.py routes, pg/config.py, requirements, .env.example).

Before building, check the hackathon must-dos in project-docs/hackathon-rules.md and the invariants in CLAUDE.md:
Atlas sandbox only; tenant_id on every document and first in every compound index; the target changes a record
only by atomically consuming a valid grant (else 403 + target_log); never invent results: numbers come only
from make eval / make rules / make test-conflict / Atlas queries run today; never quote simulated numbers from
planning docs. Do not rewrite working code: run it live, fix what fails.

Start now: walk me through `make install smoke` against the sandbox, then `make setup seed`, `make dev` and
`make bypass`, fixing anything that fails. After each step, tell me the exact command that proves it worked.
```

## Paste into Claude Code (UI session)

```
Read CLAUDE.md, README.md, WORKFLOW.md, project-docs/COMBINED-PLAN.md (sections 1, 4, 5) and docs/PRD.md
(M12, M13, Section 8 API contract, Section 13 demo). My role: the React UI in ui/ only (not ui/src/voice/).

Build with Vite + React + TypeScript, React Router (routes /review and /examiner/:caseId) and TanStack Query
(1 s polling of /api/dashboard). Dev server on port 4200, proxying /api, /target, /rules and /metrics to
http://localhost:8080. Plain CSS reusing the variables in static/index.html; text >= 16 px; red only for
refused/suspended, green only for executed and read back.

Reviewer page: one case at a time; cited evidence buttons (GET /api/cases/{id}/evidence/{eid}); a heartbeat
every 5 s only while the tab is visible and there was key/pointer input in the last 15 s (Page Visibility
API); show the server's credited time, never compute or send dwell from the browser; attestation text +
Approve; the red "Select all, approve 50" button; the result banner. Examiner page: the timeline from
GET /api/examiner/cases/{id}. Keep static/index.html working as the fallback. Start with the scaffold and
the reviewer page against the live API, and tell me how to check each piece.
```

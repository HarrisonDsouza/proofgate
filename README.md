# ProofGate

**A claim denial proposed by an AI agent can only execute if MongoDB Atlas holds proof that a qualified human really reviewed that specific case.**

- The server times how long the reviewer spends on each piece of evidence the agent cited.
- One Atlas transaction checks the proof and issues a single-use permission slip (a *grant*).
- The mock claims system refuses anything without a grant.
- Clicking "approve 50" executes 0, and the reviewer is suspended mid-run.

Built today at the MongoDB "Agents in Context" hackathon, Toronto, Nov 14 2026. Entry: **Statement One, Agents You Can Audit.** Synthetic cases built on real public-domain ICD-10-CM and HCPCS codes; not a medical tool.

**New here? Read in this order:**
1. This README.
2. [project-docs/COMBINED-PLAN.md](project-docs/COMBINED-PLAN.md): the plan, the work split, and the libraries to use.
3. [WORKFLOW.md](WORKFLOW.md).
4. Your prompt in [prompts/](prompts/).
5. [project-docs/hackathon-rules.md](project-docs/hackathon-rules.md): the must-dos.
6. [docs/PRD.md](docs/PRD.md): the behaviour spec.

**Precedence:** COMBINED-PLAN → `docs/HANDOFF.md` → PRD.

## Team

| Person | Owns | Folders | Prompt |
|---|---|---|---|
| Harry | Atlas setup, data, mock claims system, agent, rules, evaluation, React reviewer + examiner pages | `pg/db.py`, `pg/target.py`, `pg/agent.py`, `pg/rules.py`, `seed/`, `data/`, `eval/` (except `test_conflict.py`), `ui/` (except `ui/src/voice/`), `Makefile`, `README.md` | [prompts/HARRY.md](prompts/HARRY.md) |
| Sukhman *(role to confirm)* | Gate and detector working live: review flow, gate transaction, suspensions, conflict test, detector kill/restart; data notes and pitch figures | `pg/review.py`, `pg/checks.py`, `pg/gate.py`, `pg/detector.py`, `pg/cusum.py`, `pg/riskcontrol.py`, `pg/stats.py`, `eval/test_conflict.py`, `docs/DATA.md` | [prompts/SUKHMAN.md](prompts/SUKHMAN.md) |
| Neil | LangSmith tracing and ElevenLabs (video voiceover, optional spoken attestation) | `pg/voice.py`, `pg/observability.py` (tracing lines), `ui/src/voice/` | [prompts/NEIL.md](prompts/NEIL.md) |

## How the parts connect

```
Browser ── React (Vite) :4200 ──proxy /api /target /rules /metrics──┐
           fallback UI: static/index.html at :8080/                 ▼
                                    FastAPI pg.main :8080 (one Python process)
                                      reviewer API, gate transaction, mock claims system (/target),
                                      agent, rules + examiner, detector (thread, or `make detector`)
                                                     │
                                    MongoDB Atlas Hackathon Sandbox (all state)
```

The HTTP API shapes in **PRD §8** are the contract between the backend and the UI.

> **Status:** the Python backend (`pg/`, `seed/`, `eval/`, `Makefile`) comes from Sukhman's code and is being imported. The `make` commands below work once that import PR is merged to `main`.

---

## Sandbox setup (do these in order)

### Step 1. Install the tools

| Tool | Who | Check |
|---|---|---|
| git + a GitHub account added to this repo | everyone | `git --version` |
| Python 3.11+ | everyone | `python3 --version` |
| Node 22.13+ | Harry, Neil | `node -v` |
| Claude Code | everyone | `claude --version` |

### Step 2. The Atlas cluster (Harry does this once for the team)

> **It must be the MongoDB Atlas Hackathon Sandbox** from the organisers' invite email (org "Agents in Context Toronto"). A personal or free Atlas account makes the team **ineligible as a finalist**.

1. Open the invite email link → the hackathon organisation → our project.
2. Create the cluster **in that project**. If you can choose, avoid M0: shared tiers throttle operations.
3. **Network Access → Add Current IP.** Teammates on the venue Wi-Fi usually share it. If someone can't connect, add their IP, or for the venue only add `0.0.0.0/0` and remove it after the event.
4. **Database Access → Add user** `gate_app` with password auth and readWrite on `proofgate`.
5. **Connect → Drivers → copy** the `mongodb+srv://...` string. If the password has special characters, URL-encode them.
6. Send it to Sukhman and Neil by **private DM only**. Never put it in git, an issue, a PR or a chat with an AI.

### Step 3. Your local `.env` (everyone)

From the repo root, run `cp .env.example .env`, then edit `.env`:
- `MONGODB_URI`: the string from step 2.
- `DB_NAME=proofgate`.
- `GATE_URL=http://localhost:8080` and `TARGET_URL=http://localhost:8080`. It's one process.
- `AGENT_SERVICE_KEY` and `CONSOLE_KEY`: Harry generates them and DMs them with the URI. Everyone uses the same values. The API refuses to start with an empty, default or short key.
- Keep `DEMO_DEBUG_HOOKS=false` and `RUN_BACKGROUND=1`.
- In the UI, type the console key into the "Console key" box before "Start session". Without it, sessions and control actions get 401.
- Neil also fills `LANGSMITH_*` and `ELEVENLABS_API_KEY`.

`.env` is git-ignored. Check with `git status`: it must never appear.

### Step 4. Install and prove the cluster works

```bash
python3 -m venv .venv && source .venv/bin/activate
make install          # Python dependencies
make smoke            # must print PASS for the transaction AND the change stream
```

**If either check fails, ask MongoDB staff for a different tier immediately.** The whole design depends on both.

Harry then runs `make setup seed` once for the team: collections, validators, indexes, seed data. Afterwards everyone can see `proofgate` in Atlas → Browse Collections.

### Step 5. Run it locally

The `Makefile` loads `.env` for you.

| What | Command | Where |
|---|---|---|
| Backend (API, gate, claims system, detector thread, fallback UI) | `make dev` | http://localhost:8080 |
| Detector as its own process (kill/restart demo) | set `RUN_BACKGROUND=0` in `.env`, then `make detector` in a second terminal | - |
| React UI (once `ui/` exists) | `cd ui && npm install && npm run dev` | http://localhost:4200 |
| Tests and lint (before every PR) | `make test lint` | - |

### Step 6. End to end

1. Start `make dev`. Then optionally start the React UI.
2. Check that it all connects:
   - `make bypass` prints two PASS lines: no grant → 403, fake grant → 403.
   - `make rules` prints R1-R8 JSON.
   - `curl -s -H 'X-Tenant-Id: payer-acme' localhost:8080/api/queue` returns proposals.
3. Run the demo checks in the UI:
   - as `dr-stamper`, "Select all, approve 50" → executed 0, reviewer suspended
   - as `dr-demo`, open each cited item, approve → executed and read back

## Results

Filled **only** from `make eval-heldout`, `make baseline`, `make test-conflict` and `make rules` run today, pasted unedited.

_pending_

## Rules everyone follows

- Atlas sandbox is the only state store. Every document has `tenant_id`.
- Never commit secrets: no `.env` and no keys.
- All code is written today. Copy nothing from other projects.
- **Never invent results.** Every number in the README, video or pitch comes from `make eval`, `make rules`, `make test-conflict` or an Atlas query run today.
- MUST items first (PRD §6), using the cut order in COMBINED-PLAN §3.

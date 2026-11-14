# ProofGate

**A claim denial proposed by an AI agent can only execute if MongoDB Atlas holds proof that a qualified human really reviewed that specific case.**

- The server times how long the reviewer spends on each piece of evidence the agent cited.
- One Atlas transaction checks the proof and issues a single-use permission slip (a *grant*).
- The mock claims system refuses anything without a grant.
- Clicking "approve 50" executes 0, and the reviewer is suspended mid-run.

Built today at the MongoDB "Agents in Context" hackathon, Toronto, Nov 14 2026. Entry: **Statement One, Agents You Can Audit.** Synthetic data only; not a medical tool.

**New here? Read in this order:**
1. This README.
2. [WORKFLOW.md](WORKFLOW.md).
3. Your prompt in [prompts/](prompts/).
4. [START-HERE.md](START-HERE.md).
5. [docs/PRD.md](docs/PRD.md), the build spec.

The plan, demo, design and judge Q&A are in [project-docs/](project-docs/README.md).

## Team

| Person | Owns | Folders | Prompt |
|---|---|---|---|
| Harry | Atlas setup, data, mock claims system, agent, rules, evaluation, plus the review and examiner pages | `py/`, `ui/`, `Makefile` | [prompts/HARRY.md](prompts/HARRY.md) |
| Sukhman | The gate service (Spring Boot): views, approvals, the gate transaction, suspensions, detector, examiner API | `gate/` | [prompts/SUKHMAN.md](prompts/SUKHMAN.md) |
| Neil | LangSmith tracing and ElevenLabs (video voiceover, spoken attestation) | `py/voice/`, `ui/src/app/voice/` | [prompts/NEIL.md](prompts/NEIL.md) |

## How the parts connect

```
Browser  ui/ (Angular, :4200)
   │ /api ──────────────► gate/ (Spring Boot, :8080) ──┐
   │ /py  ──► py/ (FastAPI, :8000)                     │
            mock claims system, rules, voice           ├──► MongoDB Atlas (all state)
            py/agent: triage + executor ─► gate ─► claims system
            gate/ "detector" profile: change stream ───┘
```

Nobody's code talks to another person's code except through the HTTP API shapes in **PRD §8**. That is the contract between us.

---

## Sandbox setup (do these in order)

### Step 1. Install the tools for your part

| Tool | Who needs it | Check |
|---|---|---|
| git + a GitHub account with access to this repo | everyone | `git --version` |
| Python 3.11+ | Harry, Neil | `python3 --version` |
| Node 22.13+ | Harry, Neil (UI) | `node -v` |
| Java 21 + Maven | Sukhman | `java -version` shows 21 (on a Mac, run `export JAVA_HOME=$(/usr/libexec/java_home -v 21)` first if it shows 1.8) |
| Claude Code | everyone | `claude --version` |

### Step 2. The Atlas cluster (Harry does this once for the team)

> **It must be the MongoDB Atlas Hackathon Sandbox** from the organisers' invite email (org "Agents in Context Toronto"). A personal or free Atlas account makes the team **ineligible as a finalist**.

1. Open the invite email link, then the hackathon organisation, then our project.
2. Create the cluster **in that project**. If you can choose, avoid M0: shared tiers throttle operations.
3. **Network Access → Add Current IP.** Teammates on the venue Wi-Fi usually share that IP. If someone can't connect, add their IP, or for the venue only add `0.0.0.0/0` and remove it after the event.
4. **Database Access → Add user** `gate_app` with password auth and readWrite on `proofgate`.
5. **Connect → Drivers → copy** the `mongodb+srv://...` string. If the password has special characters, URL-encode them.
6. Send that string to Sukhman and Neil by **private DM only**. Never put it in git, an issue, a PR or a chat with an AI.

### Step 3. Your local `.env` (everyone)

From the repo root:
```bash
cp .env.example .env
```
Edit `.env`:
- `MONGODB_URI`: the string from step 2.
- `DB_NAME=proofgate`.
- Keep the defaults for `GATE_URL`, `TARGET_URL`, `AGENT_SERVICE_KEY` and `DEMO_DEBUG_HOOKS`. They must be the same on every machine.
- Neil also fills `LANGSMITH_*` and `ELEVENLABS_API_KEY`.

`.env` is git-ignored. Check with `git status`: it must never appear.

### Step 4. Prove the cluster works (Harry, first task)

Harry's first code is `py/db/smoke.py` (`make smoke`). It runs one multi-document transaction and catches one change-stream event. **If either fails, ask MongoDB staff for a different tier immediately.** The whole design depends on both.

When it passes, Harry runs `make setup` to create the collections, validators, indexes and seed data. Everyone can then see `proofgate` in Atlas → Browse Collections.

### Step 5. Run your part locally

Each part exists once its owner has pushed it to `main` (see WORKFLOW.md). Load `.env` first in every terminal:
```bash
set -a; source .env; set +a
```

| Part | Owner | First-time install | Run |
|---|---|---|---|
| Python (target, rules, agent) | Harry | `python3 -m venv .venv && source .venv/bin/activate && pip install -r py/requirements.txt` | `uvicorn py.target.app:app --port 8000` · agent: `python -m py.agent.executor` |
| Gate | Sukhman | `cd gate && mvn -q -DskipTests package` | `cd gate && mvn spring-boot:run -Dspring-boot.run.profiles=gate` |
| Detector (same jar) | Sukhman | (as above) | `cd gate && mvn spring-boot:run -Dspring-boot.run.profiles=detector` |
| UI | Harry | `cd ui && npm install` | `cd ui && npx ng serve --proxy-config proxy.conf.json` → http://localhost:4200 |

The `Makefile` wraps these as `make target`, `make gate`, `make detector`, `make agent` and `make ui` once Harry adds it.

### Step 6. End to end

1. Start the parts in this order: target (:8000) → gate (:8080) → detector → agent → UI (:4200).
2. Open http://localhost:4200.
3. Check that it all connects:
   - `curl -s localhost:8000/rules?tenant=payer-acme` returns JSON.
   - `curl -s -H 'X-Tenant-Id: payer-acme' localhost:8080/api/queue` returns proposals.
   - The UI shows the queue.

## Rules everyone follows

- Atlas is the only state store. Every document has `tenant_id`.
- Never commit secrets: no `.env` and no keys.
- All code is written today. Copy nothing from other projects.
- Never invent results. Every number in the README, video or pitch comes from `make eval`, `make rules` or an Atlas query run today.
- Build all MUST items (PRD §6) before anything else.

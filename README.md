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
| Sukhman | Gate and detector working live: review flow, gate transaction, suspensions, conflict test, detector kill/restart; data notes and pitch figures | `pg/review.py`, `pg/checks.py`, `pg/gate.py`, `pg/detector.py`, `pg/cusum.py`, `pg/riskcontrol.py`, `pg/stats.py`, `eval/test_conflict.py`, `docs/DATA.md` | [prompts/SUKHMAN.md](prompts/SUKHMAN.md) |
| Neil | LangSmith tracing and ElevenLabs (video voiceover, optional spoken attestation) | `pg/voice.py`, `pg/observability.py` (tracing lines), `ui/src/voice/` | [prompts/NEIL.md](prompts/NEIL.md) |

Sukhman's commits show the author "Your Name" (git identity was not set on his machine); they arrived through the `sukhman` branch and PR #8. Neil's ElevenLabs and LangSmith setup notes are in `project-docs/elevenlabs.md` and `project-docs/langsmith-setup.md`.

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

How it works, step by step: [project-docs/design/proofgate-flow.svg](project-docs/design/proofgate-flow.svg). Which line of code stops each attack: [docs/enforcement-map.md](docs/enforcement-map.md).

### MongoDB Atlas features used

All state lives in a cluster in the **MongoDB Atlas Hackathon Sandbox** project.

- **Multi-document transactions** (snapshot read, majority write) for the gate, approvals, suspensions and policy versions, with a version-guarded write to `reviewer_state` so a concurrent approval and suspension conflict instead of both succeeding. `txn_attempts` is stored on every gate decision.
- **Change streams with a saved resume token** for the rubber-stamp detector (rate, median dwell, self-baselined CUSUM). A restarted detector misses nothing (`make test-restart`).
- **`$jsonSchema` validators** on every decision-bearing collection; the API ignores client-sent dwell.
- **Partial unique indexes** (one open view per session, one active policy version), **TTL indexes** (view tokens, grants) and a **time-series collection** for gate telemetry.
- Thresholds live in a versioned `review_policies` document, never in code; the Supervisor page can only tighten them.

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

## The triage agent (LangGraph, sponsor resources only)

`pg/graph_agent.py`. Run it from the Supervisor page ("Run agent on new claims"), `make triage-new`, or `POST /api/agent/triage-new`.

```
load_case -> retrieve_clauses -> rerank -> decide -> validate -> write_proposal
```

| Node | What it does | Resource |
|---|---|---|
| retrieve_clauses | Embeds the claim and finds candidate policy clauses with `$vectorSearch` (filtered by tenant) | Voyage `voyage-3.5`, Atlas Vector Search |
| rerank | Orders the candidates against the claim's evidence; the top one governs | Voyage `rerank-2.5` |
| decide | Scores the evidence against "condition met" vs "not met"; proposes **deny only if "not met" wins by 0.05**, otherwise pay; picks the documents a reviewer must read | Voyage `rerank-2.5` |
| validate | Code, not the model, fixes the record: cited ids must exist, hashes come from the case, the clause must be real. A failed check falls back to the rule, labelled | Python |
| write_proposal | The agent's action: writes the case, target record and a `pending_review` proposal with `proposer`, `agent_trace`, `agent_scores` | Atlas |
| (all) | Graph state checkpointed per case (`agent_checkpoints`) so a crash resumes mid-case; nodes traced | `langgraph-checkpoint-mongodb`, LangSmith |

The agent proposes only. It never sees a grant or calls the claims system; a reviewer and the gate still decide every denial.

### Resource guide checklist

| Guide resource | Used? | Where |
|---|---|---|
| MongoDB Atlas Hackathon Sandbox | Yes | All state; transactions, `$jsonSchema`, change streams |
| Atlas Vector Search | Yes | `pg/graph_agent.py` `vector_search`, index `policy_clause_vec` |
| Voyage AI (embeddings + reranker) | Yes, needs `VOYAGE_API_KEY` | `pg/graph_agent.py` |
| LangGraph + MongoDB checkpointer | Yes | `pg/graph_agent.py` `build_graph`, `_checkpointer` |
| LangSmith | Wired, needs `LANGSMITH_API_KEY` + `LANGSMITH_TRACING=true` | `pg/observability.py`, graph nodes |
| ElevenLabs | Wired, needs `ELEVENLABS_API_KEY` | `pg/voice.py` (speech-to-text attestation, voice) |
| MongoDB Agent Skills, MCP Server | Used while building (dev tooling), not in the app | — |
| Atlas Search, Automated Embeddings, GraphRAG, LangChain memory | Not used | — |

## Results

Filled **only** from runs on the Atlas sandbox today, pasted unedited. Full output: [docs/eval-heldout.txt](docs/eval-heldout.txt), [docs/eval-baseline.txt](docs/eval-baseline.txt). Pre-registration: [docs/PREREGISTRATION.md](docs/PREREGISTRATION.md).

The evaluation is **simulated and time-scaled ÷10** (thresholds scaled to match) with synthetic reviewers and synthetic cases. It is not a study of real reviewers. `n` = simulated reviewers, `att` = denials attempted.

**Held-out run** (`make eval-heldout`, seed 20261114, run once, 14:31 EST, ProofGate policy v1):

```
commit 7df270e seed 20261114 baseline=False cusum=True
group         n   att  exec refused  susp  reasons
honest       12    96    95       1     0  {'G5_DWELL': 1} {}
fast-honest   4    32    28       4     0  {'G5_DWELL': 4} {}
stamper       4   200     0     200     4  {'G1_APPROVAL_FOR_CASE': 28, 'G2_NOT_SUSPENDED': 200, 'G4_EVIDENCE_COVERAGE': 200, 'G5_DWELL': 200} {'MEDIAN_DWELL': 4}
tab-idler     4    32     0      32     4  {'G4_EVIDENCE_COVERAGE': 32, 'G5_DWELL': 32, 'G2_NOT_SUSPENDED': 10, 'G1_APPROVAL_FOR_CASE': 1} {'MEDIAN_DWELL': 4}
skimmer       4    32     1      31     4  {'G5_DWELL': 30, 'G2_NOT_SUSPENDED': 12, 'G1_APPROVAL_FOR_CASE': 1} {'MEDIAN_DWELL': 4}
hb-forger     2    16    16       0     0  {} {}
floor-gamer   4    32    32       0     0  {} {}
drifter       4    64    61       3     2  {'G5_DWELL': 1, 'G2_NOT_SUSPENDED': 2} {'CUSUM': 2}
```

- False refusal (honest + fast-honest): **5/128 (3.9%, 95% CI 1.7–8.8%)**, all for dwell below the floor.
- False suspension: **0/16 (95% CI 0–19.4%)**.
- Median server-verified active review time per executed denial: **59.25 s**.
- Invariants R1–R8 over stored state: **all true**.

**Baseline** (`make baseline`, same seed and workload, policy v0 = "an approval exists" only):

```
commit 7597a52 seed 20261114 baseline=True cusum=True
group         n   att  exec refused  susp  reasons
honest       12    96    96       0     0  {} {}
fast-honest   4    32    32       0     0  {} {}
stamper       4   200   164      36     4  {'G1_APPROVAL_FOR_CASE': 36} {'MEDIAN_DWELL': 4}
tab-idler     4    32    31       1     4  {'G1_APPROVAL_FOR_CASE': 1} {'MEDIAN_DWELL': 4}
skimmer       4    32    32       0     4  {} {'MEDIAN_DWELL': 4}
hb-forger     2    16    16       0     0  {} {}
floor-gamer   4    32    32       0     0  {} {}
drifter       4    64    64       0     0  {} {}
```

- Without the gate, stampers executed **164 of 200** denials and skimmers **32 of 32**; with it, **0 of 200** and **1 of 32**.
- R2 and R5 (every executed denial has qualifying review) are **false** under the baseline.

**Live UI check today:** "Select all, approve 50" → "Executed 0 of 50", reviewer suspended mid-run, already-executed denials reopened with read-back. An honest review of CLM-A-0005 (51.7 s server-credited, 2 of 2 cited items) → executed and read back. 80 automated tests pass against Atlas (`make test`).

### Disclosures and limits

- **What gets through:** the heartbeat-forger group (a script that fakes visibility and input, 16 of 16 executed) and the floor-gamer group (reviews just above the floor, 32 of 32). Both were predicted in the pre-registration. Server timing raises the cost of faking review from one click to sustained scripted work per item; it cannot prove that someone read.
- **Detector calibration** used the PRD's synthetic reviewer models; **n = 0 real reviewer sessions**.
- **Timestamps:** `PREREGISTRATION.md` says "Committed at: 14:58 EST"; that line is a typo. Git shows the pre-registration commit `7df270e` at **14:25** and the held-out results commit `350d06c` at **14:31**.
- The held-out run used commit `7df270e`; the baseline used `7597a52` (after the gate hardening PR merged). An earlier baseline attempt was discarded because its detector thread crashed when tests ran on the cluster at the same time.
- After both runs, "approve 50" was changed to write its 50 approval records in one transaction (it took ~5 minutes on the sandbox before). The gate logic and what it checks did not change.
- The triage agent for **new** claims is a LangGraph graph (`pg/graph_agent.py`, added 16:05-16:20, after the eval). The seeded demo data and both eval runs above used the deterministic rule (`rules-v1`), so no result above comes from the graph agent. Its decision quality has not been measured. Without `VOYAGE_API_KEY` it runs the rule and labels every proposal `rules-v1`.
- Not built today: an LLM-written rationale (no sponsor offers a text LLM, and we chose not to add a non-sponsor one), the account-freeze action, a read-only MCP server in the app. LangSmith traces the agent's graph nodes (never the executor, whose output carries the grant token) and only records when `LANGSMITH_TRACING=true`.
- Synthetic cases built on real public-domain ICD-10-CM and HCPCS codes. Not a medical or claims tool.

## Rules everyone follows

- Atlas sandbox is the only state store. Every document has `tenant_id`.
- Never commit secrets: no `.env` and no keys.
- All code is written today. Copy nothing from other projects.
- **Never invent results.** Every number in the README, video or pitch comes from `make eval`, `make rules`, `make test-conflict` or an Atlas query run today.
- MUST items first (PRD §6), using the cut order in COMBINED-PLAN §3.

# ProofGate: combined team plan

**Status:** draft for team review. Written 12:40 EST, Nov 14 2026, from the decisions below.

**Inputs:**
- the handoff docs in this repo: `docs/PRD.md`, `CLAUDE.md`, `START-HERE.md`, `project-docs/*`, `README.md`, `WORKFLOW.md`, `prompts/*`
- Sukhman's "ProofGate Team Build Plan" (docx)
- Sukhman's `proofgate-repo.zip`: a working single-process Python implementation (`pg/`, about 1,700 lines plus seed, eval and tests; 15 offline tests), **never yet run against Atlas**

**Precedence:** this file → `docs/HANDOFF.md` (from the zip) → `docs/PRD.md`.
- The PRD stays the spec for *behaviour*: gate rules G1-G8, the data model, the API contract, the evaluation and the demo.
- Sukhman's code already implements that contract.
- This file only changes *how* we build it and *who* does what.

> **Harry's directions that change earlier repo decisions:**
> - The backend is **Python** (no Spring Boot gate).
> - The frontend is **React** (no Angular).
>
> `README.md`, `WORKFLOW.md`, `CLAUDE.md`, `prompts/*` and `project-docs/*` have been updated to match (Q4 done). `project-docs/PLAN.md` §6 is superseded by this file. Everything else in those docs stands.

> **Note:** the build plan and the zip are **not on GitHub yet**. `main` holds only the first commit. Importing the zip is step 0 below.

---

## 1. Architecture

```
Browser ── React (Vite) dev server :4200 ──proxy /api /target /rules /metrics──┐
           fallback: static/index.html served at :8080/                         ▼
                                                           FastAPI  pg.main  :8080   (one Python process)
                                                             review.py   sessions, view tokens, heartbeats, approvals, bulk-50
                                                             checks.py   G1-G8 + dwell crediting (pure, property-tested)
                                                             gate.py     ONE transaction + reviewer_state version write, grants,
                                                                         suspension txn, confirm by read-back
                                                             target.py   mock claims system at /target: consume grant or 403
                                                             agent.py    rules triage + executor (gate → target → confirm)
                                                             rules.py    R1-R8 + examiner replay
                                                             voice.py    [Neil] POST /api/voice/attest → ElevenLabs STT
                                                             observability.py  JSON logs, /metrics, LangSmith hook
                                                           detector: thread in the API (RUN_BACKGROUND=1), or its own
                                                             process `make detector` (RUN_BACKGROUND=0) for the
                                                             live kill/restart demo
                                                                         │
                                                           MongoDB Atlas Hackathon Sandbox (all state)
```

**Kept from both plans (unchanged):**
- Atlas sandbox only.
- `tenant_id` everywhere, leading every compound index.
- Server-only dwell time.
- One transaction (snapshot read, majority write) that always writes `reviewer_state`, with `session=s` on every operation and `txn_attempts` stored.
- The claims system accepts only a grant, otherwise 403 plus `target_log`.
- Policy is versioned data.
- The change stream has a resume token stored in `detector_state`.
- Compensations are idempotent and verified by read-back.
- The LLM only drafts text.
- Never invent numbers.

**Folders:**
- `pg/`, `seed/`, `eval/`, `data/`, `tests/`, `static/` (from the zip)
- `ui/` (new React app)
- `docs/` and `project-docs/`

**Ports:**
- **API :8080.** The README already puts the gate on :8080. The claims system moves from :8000 into the same process, at `/target`.
- **UI :4200.** Unchanged from the README; Vite is configured to use port 4200.

**Dev system** (as already set up in the repo; no new one):
- **README "Sandbox setup" steps 1-4:** tools, the Atlas sandbox cluster, `.env`, `make smoke`.
- **WORKFLOW.md:** one branch per person, pull requests into the protected `main`, handoff rows in `project-docs/handoffs.md`.
- **The `dev-system` plugin** for each slice: `dev-system:feature`, then `dev-system:check` before a PR. The orchestrator (Claude, in Harry's session) runs `dev-system:reviewer` and `security-reviewer` on the gate.
- **Commands from Sukhman's Makefile:** `make install smoke setup seed dev test lint bypass test-conflict rules explain eval eval-heldout baseline calibrate-detector calibrate-prd detector`.

## 2. Work split

| Who | Owns (folders) | First tasks, in order |
|---|---|---|
| **Harry** | Atlas setup; data (`pg/db.py`, `seed/`, `data/`); claims system (`pg/target.py`); agent (`pg/agent.py`); rules (`pg/rules.py`); evaluation (`eval/simulate.py`, `eval/calibrate_detector.py`, `docs/PREREGISTRATION.md`); **React pages** in `ui/` (reviewer, examiner) | 1. Sandbox cluster + `.env` + `make install smoke` (both PASS). 2. `make setup seed`, `make dev`, `make bypass` (two 403 PASS lines). 3. Scaffold `ui/`; build the reviewer page against the live API. 4. Agent and rules live; `make rules`. 5. Examiner page. 6. Eval (§4 order). |
| **Sukhman** *(role open: Q1)* | Gate and detector, live: `pg/review.py`, `pg/checks.py`, `pg/gate.py`, `pg/detector.py`, `pg/cusum.py`, `pg/riskcontrol.py`, `pg/stats.py`, `eval/test_conflict.py`. He wrote this code. With a Python backend his role no longer depends on Java. | 1. With Harry's `.env`: `DEMO_DEBUG_HOOKS=true make test-conflict` all PASS on Atlas; fix what fails. 2. Bulk 50 → executed 0; reviewer suspended; forged `dwell_ms` → 0. 3. Detector kill/restart demo (`RUN_BACKGROUND=0 make detector`). 4. `make explain` IXSCAN. 5. Data notes (`docs/DATA.md`) and pitch figures. 6. Volunteers, only if Q2 = yes. |
| **Neil** | LangSmith and ElevenLabs only (`project-docs/langsmith-setup.md`, `project-docs/elevenlabs.md`). Code: `pg/voice.py`, `@traceable` through `pg/observability.py`, `ui/src/voice/`. | 1. LangSmith key + hello trace. 2. ElevenLabs key + text-to-speech/speech-to-text spikes. 3. Tracing on `pg/agent.py` steps, grant ids redacted (after Harry's agent runs live). 4. After 13:45, if the core is green: `POST /api/voice/attest` + `attestations` (validator, `tenant_id`) + React "Speak attestation" button. 15:00 go/no-go. 5. Video voiceover. |
| **Orchestrator (Claude)** | Imports the zip, keeps `handoffs.md`, calls checkpoints and cuts, reviews PRs, drafts the README results and Q&A | Step 0 below |

**Step 0 (orchestrator, on approval):**
- Import the zip into the repo through a PR, re-committed **without** its Claude attribution trailer.
- Keep our `CLAUDE.md`, `README.md` and `WORKFLOW.md`, merging in the zip's invariants, Results section and `.env` keys (`TARGET_URL=http://localhost:8080`, `RUN_BACKGROUND`).
- Do not commit the zip file itself.

## 3. Timeline (EST)

| Time | Checkpoint | Source |
|---|---|---|
| 13:15 | Smoke, setup and seed on the sandbox; fallback UI loads; `make bypass` PASS | Sukhman (the PRD's 12:40 has passed) |
| 13:45 | **Core demo:** honest approval executes + read-back; bulk 50 → 0; forged dwell → 0; bypass 403; `test-conflict` PASS. Tag `core-ok`. | Both |
| 14:30 | Calibration done; `docs/PREREGISTRATION.md` committed **before** the held-out run | Both (PRD 14:15 + Sukhman 14:30) |
| 15:00 | Spoken attestation go/no-go | Ours |
| 15:15 | Held-out eval + baseline stored; React reviewer + examiner live | Sukhman |
| 15:30 | Fallback burst video recorded (PRD M17) | PRD |
| **16:00** | **Feature freeze** | Compromise; see D5 |
| 16:00-16:30 | 1-minute video with ElevenLabs voiceover (audio checked); README results pasted verbatim | Both |
| 16:45 | Submitted on Cerebral Valley; repo public (checked logged out); all teammates added | Both |

**Cut order** (Sukhman's list, which extends the PRD's):
1. S7 clause search
2. LLM rationale
3. spoken attestation
4. tenant B
5. second action type
6. hash-chain UI
7. CUSUM (keep the rate + median rules)
8. React examiner (fall back to `static/`)

**Never cut:** the gate transaction, server dwell, grant-or-403, suspension + verified rollback, the examiner (React or fallback), the evaluation.

## 4. Libraries per task

| Task | Library | Why |
|---|---|---|
| HTTP API | **FastAPI** + **Uvicorn** | Already used in `pg/`; request models via **Pydantic v2** (bundled) |
| MongoDB access and transactions | **PyMongo** (sync `ClientSession.with_transaction`) | Already used. Not Motor: deprecated in favour of PyMongo's own async API, and sync is simpler for the transaction code |
| Service-to-service HTTP (agent → gate → target, eval simulator, bypass test) | **httpx** | Already used |
| Statistics: CUSUM, Learn Then Test, Wilson, McNemar, bootstrap | **NumPy** + **SciPy** | Vectorised, enough for these sizes |
| ICD-10/HCPCS cleaning (one-off, already done) | **pandas** | Offline pipeline only (`data/pipeline/codes.py`) |
| Tests / property tests / lint | **pytest**, **Hypothesis**, **ruff** | Already in CI |
| Metrics / logs | **prometheus-client**; stdlib `logging` (JSON) | Already in `pg/observability.py` |
| Agent tracing | **langsmith** (`@traceable`) | Neil; no-op when `LANGSMITH_TRACING=false` |
| Optional LLM rationale (S6) | **anthropic** SDK | Cut early; never decides |
| Speech-to-text / voiceover | **elevenlabs** Python SDK, pinned `<3` | Server side only; the key never reaches the browser |
| Frontend build | **Vite** + **React** + **TypeScript** | A static single-page app talking to FastAPI. Not Next.js: its server rendering and Node server add a second backend we don't need |
| Routing | **React Router** | Two routes: `/review`, `/examiner/:caseId` |
| Server state and 1 s polling (dashboard banner, examiner) | **TanStack Query** (`refetchInterval`) | Caching and retries without hand-written effects |
| Heartbeats (tab visible + input within 15 s) | Browser **Page Visibility API** + key/pointer listeners in one custom hook | No library needed. The server still decides the credited time. |
| Audio capture | Browser **MediaRecorder API** | No library needed |
| Styling | Plain CSS with variables reused from `static/index.html` | No setup time. Red = refused/suspended, green = executed + read back, text ≥ 16 px for the projector |
| CI | **GitHub Actions** (`ci.yml` from the zip) + a `ui` job (`npm ci && npm run build`) | Ruff, pytest, secret scan. **Cloud Run deploy left off** (PRD: no extra services) |
| C++ | **None** | Nothing needs it. The only heavy job, `make calibrate-*` (Monte Carlo over thresholds), runs in NumPy. If it takes over 2 minutes, lower the simulation count or vectorise the inner loop. C++ (pybind11) only if profiling then shows a loop NumPy can't vectorise. Not expected. |

## 5. Disagreements and recommendations

"Repo" means the handoff docs in this repo; "Sukhman" means his plan and zip.

| # | Topic | Repo says | Sukhman says | Recommend | Why |
|---|---|---|---|---|---|
| D1 | Backend | Spring gate + Python target/agent (3 services) | One Python FastAPI process | **One Python process** | Harry's direction; the code exists; fewer moving parts |
| D2 | Frontend | Angular (PRD, README) | `static/index.html`; Angular optional | **React for reviewer + examiner; keep `static/` as fallback and for supervisor/evidence** | Harry's direction; the fallback protects the demo |
| D3 | Folder layout | `py/`, `gate/`, `ui/` | `pg/`, `seed/`, `eval/`, `data/`, `static/` | **Zip layout + `ui/`** | Matches the working code |
| D4 | Ports | gate :8080, target :8000, UI :4200 | All on :8080 | **API + target :8080; UI :4200** | Keeps the README's :8080 and :4200 |
| D5 | Feature freeze | 15:30 | 16:15 (video 16:15-16:35) | **16:00; fallback video at 15:30** | React is new work, so 15:30 is too early. 20 minutes for the video plus an audio check is too tight. |
| D6 | First checkpoint | 12:40 | 13:15 | **13:15** | 12:40 has passed |
| D7 | Precedence | "Follow the PRD exactly" | HANDOFF overrides PRD | **This file → HANDOFF → PRD; PRD for behaviour** | One source of truth |
| D8 | Detector | Rate + median | + self-baselined CUSUM, Learn Then Test | **Include, second from last in the cut order** | Built and tested; strong answer on fast honest reviewers |
| D9 | Eval groups | 6 | 8 (+ floor-gamer, drifter) | **8** | Already coded; reports the floor-gamer limit honestly |
| D10 | Honest-reviewer model | Synthetic | Real volunteer sessions 13:00-14:30 | **Optional (Q2), only after 13:45 green, 14:00-14:45; `calibrate-prd` fallback** | 13:00-14:30 overlaps the core checkpoint |
| D11 | Seed data | Synthetic codes; ortho/cardio/radiology | Real ICD-10-CM + HCPCS; sleep replaces radiology | **Sukhman's** | Real public-domain codes; the CPAP example works; still no CPT |
| D12 | Pitch opener | PxDx 1.2 s | KFF Medicare Advantage figures | **KFF first, then PxDx with Cigna's dispute; both [VERIFY]** | Bigger, more neutral problem size; only after verification |
| D13 | Simulated results in the plan | None | Simulated detection and false-suspension percentages | **Never quote them; show only numbers printed by `make eval`, `make rules` or `make test-conflict` today** | Rule: no number not produced today |
| D14 | ElevenLabs | Neil: voiceover + spoken attestation | Skip | **Keep, contained (cut 3rd)** | Recorded decision; a separate prize; no core time |
| D15 | LangSmith | Neil traces the agent | Only with the LLM rationale | **Neil traces the agent through the existing hook** | Recorded decision; the hook exists |
| D16 | Roles | Harry A+C, Sukhman Spring, Neil LS/EL | A/B/C + Sukhman (data, volunteers, pitch) | **§2 split** | Three people; Python backend |
| D17 | CI/CD | None | GitHub Actions + Cloud Run deploy | **CI yes, deploy off** | PRD: no extra services |
| D18 | Build helpers | `dev-system` plugin, Agent Skills, MCP | + ponytail, hallmark, impeccable, ui-ux-pro-max, graphify, last30days, Scrapling | **dev-system + Agent Skills + MCP only** | Use the existing dev system; no install time |
| D19 | Git | Branches + PRs to protected `main` | "Don't push to GitHub"; merge hourly after `make test lint`; no untested pushes after 15:00 | **Ours + both of Sukhman's merge rules** | Compatible |
| D20 | Commit attribution | No Claude attribution (Harry's rule) | Zip commit has a Claude trailer + session URL | **Re-commit without it** | Harry's rule |
| D21 | Screens | Reviewer + examiner | + supervisor + evidence | **React: reviewer + examiner; supervisor + evidence from `static/`** | Scope |
| D22 | "Fast honest reviewers?" answer | Reported separately; policy sets the floor | Plan: population detector flagged all; handoff: reported separately | **Use both, with the number from today's eval** | Consistent and measured |

## 6. Carried over from Sukhman's files

**Carry:**
- All of `pg/`, `seed/`, `eval/`, `tests/`, `data/` (pipeline + processed codes, `problem_figures.json`), `static/`, `Makefile`, `requirements*.txt`, `pyproject.toml`
- `.github/workflows/ci.yml` (deploy job disabled)
- `docs/HANDOFF.md`, `docs/DATA.md`, `docs/PREREGISTRATION.md`
- The live-check order from `docs/KICKOFF_PROMPT.md`
- The cut order and never-cut list
- The CUSUM finding and its limits
- The new judge answers
- The limits line ("volunteers aren't physicians", only if volunteers are used)
- The merge rules

**Don't carry:**
- the Cloud Run deploy (`Dockerfile` kept but unused)
- the third-party plugin list (`docs/TOOLS.md` kept as reference only)
- the zip's `CLAUDE.md`/`README.md`/`START-HERE.md` as files (merged into ours instead)
- "skip ElevenLabs"
- the four-owner role table
- the Claude-attributed commit

## 7. Open questions

1. **Sukhman:** will you own the Python gate and detector live (§2)? Java isn't needed any more. If you'd rather do data, volunteers and the pitch, Harry takes the gate and the examiner page moves to the fallback UI.
2. **Volunteer sessions** (5-10 people, 14:00-14:45, aliases only): yes or no?
3. **Zip import:** OK for the orchestrator to import it through a PR now (step 0)?
4. ~~Follow-up: align `README.md`, `WORKFLOW.md`, `prompts/*`, `CLAUDE.md` and `handoffs.md` with this plan.~~ Done on the `harry` branch; it reaches `main` with the plan's PR.
5. **Feature freeze at 16:00** instead of 15:30 or 16:15: agreed?
6. **Researchers:** start the five from `PLAN.md` §7 now, adding the KFF figures to R1's list?
7. **Atlas:** is the sandbox cluster created, and which tier? Nothing runs until `make smoke` passes.
8. **GitHub usernames** for Sukhman and Neil (collaborator access).

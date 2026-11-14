# ProofGate: team plan for today

**Status: DRAFT.** Where this differs from [COMBINED-PLAN.md](COMBINED-PLAN.md) (stack, ports, work split, timeline), COMBINED-PLAN wins.
Written 12:16 EST, Sat Nov 14 2026. The build spec is still `docs/PRD.md`. This plan only adds who does what, how we coordinate, and the two partner add-ons.

## 1. Your requirements, restated

| # | Requirement | Where it is answered |
|---|---|---|
| 1 | Summarise the rules, judging criteria and deliverables | `hackathon-rules.md` |
| 2 | Can ElevenLabs improve our chances, and how | `elevenlabs.md`; summary in §4 |
| 3 | Fold anything relevant from `Resources.md` into the plan | §5 |
| 4 | A project documentation folder: the demo, the design and decisions, judge Q&A | this folder: `demo.md`, `design-and-decisions.md`, `judge-qa.md` |
| 5 | A MongoDB explainer: how and why we use it | `mongodb-explainer.md` |
| 6 | Plan the researcher agents; spawn them only after approval | §7 |
| 7 | LangSmith tracing set up, with help | `langsmith-setup.md`; Neil's track in §6 |
| 8 | Work split: Neil = LangSmith + ElevenLabs only; Harry + Sukhman = everything else; the assistant orchestrates and manages handoffs | §6, §8, `handoffs.md` |
| 9 | Confirm understanding first | §1 and the chat reply |
| - | Do not start building until the plan is reviewed | Gate at §11 |

## 2. Where we are (honest)

- **It is 12:16.** The PRD expected setup to finish at 12:00.
- **Not done yet:**
  - the Atlas sandbox cluster
  - `.env`
  - the smoke test, which does not exist yet and needs writing
  - a git repo
  - the MCP server
  - role assignment
- **The 12:40 checkpoint is at risk.** Atlas setup (Harry) can start right now, in parallel with reviewing this plan.
- **The PRD assumed three core engineers. We now have two.** Neil is only on LangSmith and ElevenLabs. This is the biggest risk today; see §9.

## 3. Rules that shape this plan (from `hackathon-rules.md`)

- Build inside the **Atlas Hackathon Sandbox**, or we cannot be a finalist.
- All code is original and written today.
- Submit on Cerebral Valley by 5:00 PM (our target is 4:45):
  - a public GitHub repo
  - a 1-minute video with working audio
  - a description
  - all three teammates added
- Judging: live at our table from 5:15. Criteria are impact, innovation and feasibility (no weights published).

## 4. ElevenLabs decision (detail in `elevenlabs.md`)

- **Main prizes:** little effect. Our judges care about the gate, transactions and bypasses.
- **"Best Project Built with ElevenLabs" (a separate prize):** a real extra chance at no cost to the core, because Neil works in parallel.
- **Do:**
  1. A text-to-speech voiceover for the 1-minute video. This guarantees clean audio.
  2. **Spoken attestation:**
     - The reviewer speaks; ElevenLabs speech-to-text transcribes it on our server.
     - The transcript and audio hash are stored in Atlas.
     - The examiner page shows them. It never affects gate rules.
- **Cut rule:** if (2) is not working by 15:00, ship (1) only.
- **Change from the PRD:** the PRD listed voice as a non-goal (C4, "cut by default"). Item (2) is a deliberate, contained exception at your request. It stays at the top of the cut order.

## 5. What `Resources.md` adds

`Resources.md` is the same official resource guide as the one you attached, with four updated links. Relevant items:

| Resource | Use in ProofGate |
|---|---|
| MongoDB Agent Skills + MongoDB MCP Server ("recommended starting point") | Install both in Claude Code during setup (PRD §9 step 3). Keep MCP **read-only**. Judges from MongoDB will notice we followed the recommended path. |
| Natural Language to MongoDB Queries guide | Prompting reference while writing rules R1-R8 and the examiner queries. |
| Atlas Managed MCP Server | Alternative to the local MCP server if the local one fails. Uses a service account, not your login. |
| Data Modeling in MongoDB | Background for `mongodb-explainer.md` (why case + evidence sit in one document). |
| Automated Embeddings / Vector Search / Voyage AI | Only for S7 (citing policy clauses). That is cut early, so probably unused. |
| LangGraph + MongoDB, State & Persistence blog | **Not used.** Our agent is rules-based by design. Mention the blog only if asked about crash recovery: our detector resumes from a stored resume token. |
| ElevenLabs Hacker Guide | Check it for the ElevenLabs prize criteria (researcher R3). |
| LangSmith credits form | Neil submits it (within 10 days). |
| Starter code (GenAI Showcase, quickstarts) | Reference only. **Copy no code**; all work must be original. |

## 6. Work split

The PRD has three code roles: A = Python, B = Spring Boot gate, C = Angular UI. With two core people:

| Person | Owns | PRD items |
|---|---|---|
| **Sukhman** | **Engineer B, the gate service (Spring Boot, Java 21).** Sessions, view tokens and heartbeats; server-computed approvals and bulk-50; versioned policies; **the gate transaction G1-G8**; confirm by read-back; the suspension transaction; the detector (change stream + resume token); the compensation worker; the examiner API; the `X-Debug-Pause-Ms` hook. | M4, M5, M6, M7, M10, M11, M13 (API) |
| **Harry** | **Engineer A, Python**: Atlas setup, `.env`, smoke test, `setup_db`, seed, the mock claims system (grant-only, 403 otherwise), triage agent, executor loop, rules R1-R8, eval, the `test-conflict` script, reset. **Plus Engineer C at reduced scope (Angular)**: the review page (evidence panel, heartbeats, Approve, red bulk-50 button, banner) and the examiner page. | M1, M2, M3, M8, M9, M12, M13 (page), M14, M15, M16, M17 |
| **Neil** | **LangSmith and ElevenLabs only.** LangSmith account, key, tracing on the agent; ElevenLabs video voiceover; spoken attestation (speech-to-text endpoint + Angular button component). | C3, C4 (scoped) |
| **Assistant (this session)** | Orchestrator. Keeps the plan and `handoffs.md` current. Calls checkpoints and cuts at 12:40, 13:45, 14:45 and 15:30. Runs the dev-system workflow: a plan per slice, `dev-system:check` (tests + review) before anything is "done", `dev-system:reviewer` and `security-reviewer` on the gate. Spawns the researchers. Drafts the README, the demo script and the Q&A. | - |

**Why this split:**
- The gate is the heart of the product and the hardest piece, so one person owns it whole.
- Harry's Python work feeds the gate (data, target, agent).
- The UI is cut to the two pages the demo needs. The supervisor page (S5) is already a SHOULD.
- **Please check:** does Sukhman know Java/Spring, and does Harry know Python and Angular? If not, swap roles. If neither of you knows Spring, see the alternative in §9.

**How each person works:** everyone runs their own Claude Code session in the shared repo and pastes PRD §17 with their role. Harry probably needs two sessions (Python and Angular) in separate folders, so that two writers never touch the same files.

**Neil's timeline (never on the critical path):**

| Time | Neil |
|---|---|
| now-12:50 | LangSmith account + key + `.env` + hello trace (`langsmith-setup.md` steps 1-5). ElevenLabs coupon + key. |
| 12:50-13:45 | ElevenLabs spikes: text-to-speech of one script line; speech-to-text of a 10-second clip. Draft the 1-minute video script from PRD §13. |
| 13:45-14:45 | Once Harry's agent runs: add `@traceable` (handoff H5). Build `/voice/attest` + `attestations` writes. |
| 14:45-15:00 | Angular "Speak attestation" component; hand it to Harry (H7). **15:00 go/no-go on spoken attestation.** |
| 15:30-16:15 | Generate the voiceover; help record and edit the 1-minute video and the fallback burst video. |
| 16:15-16:45 | Check the video plays with audio; upload; confirm all teammates are on the submission. |

## 7. Researcher agents (spawn only after approval)

Each runs in the background and writes one file under `project-docs/research/`. They never write code.

| Id | Agent type | Question | Output | Why it matters |
|---|---|---|---|---|
| R1 | `dev-system:domain-expert` (field: US health-insurance utilisation management and claims compliance) | Verify every [VERIFY] claim in the PRD: the ProPublica PxDx figures and Cigna's response; CA SB 1120 and AZ HB 2175 bill numbers and scope; the UnitedHealth nH Predict suit status; the FINRA 2026 report. Produce stage-safe wording. | `research/claims-facts.md` | We must never say an unchecked fact on stage. |
| R2 | `general-purpose` | Atlas sandbox tiers: do multi-document transactions and change streams work on M0/Flex? Operation throttling on shared tiers. Transaction lifetime limits. Java sync driver `withTransaction` retry behaviour. | `research/atlas-tier.md` | Backs up the smoke test and the conflict-test answers. |
| R3 | `general-purpose` | For Neil: ElevenLabs speech-to-text current model ids and Python SDK 2.x call; browser recording to a backend; the "Best Project Built with ElevenLabs" criteria (Hacker Guide). LangSmith: `traceable` input-redaction hooks, region endpoint, public trace sharing. | `research/neil-tools.md` | Removes the [VERIFY] marks in `elevenlabs.md` and `langsmith-setup.md`. |
| R4 | `dev-system:security-reviewer` (threat-model mode) | Attack the PRD design as a judge would: bypass the target, forge dwell, replay grants, cross-tenant leaks, race the suspension. | `research/threat-model.md` | Several judges (Okta, Cohere, Microsoft) will try exactly this. |
| R5 | `dev-system:plan-critic` | Review this plan for gaps, over-scope and hidden risks, given two core engineers and the 4:45 target. | `research/plan-critique.md` | A second look before we commit. |

At most 5 agents, all started at once in one batch. I relay what each finds and update the docs. Their results are inputs, not decisions; anything that changes scope comes back to you.

## 8. Orchestration and handoffs

- **One shared repo.** Every teammate needs it within minutes.
  - You asked me not to create GitHub repos unless you say so. **Please create it** (public is required at submission; it can be public from the start) and add Sukhman and Neil. Or tell me to do it with `gh`.
  - Until then I will `git init` locally (after approval) and commit as we go.
- **The contract between people is PRD §8** (the API shapes). Nobody changes an endpoint shape without updating `handoffs.md` and telling the other person.
- **`handoffs.md`** is the shared board. Each handoff says who, what, the "done" check (a curl or test command) and its status.
- **Checkpoints.** At each one I check the real state against Atlas and the running services, not anyone's report. I then call go, or cut using PRD §6 cut order and the START-HERE §3 minimum core.
- **Dev-system usage:**
  - The PRD already exists, so we skip `dev-system:start` and the architect.
  - For each slice: `dev-system:feature` (plan check → build test-first → verify), then `dev-system:check` before it counts as done.
  - The UI uses a light design pass only, with no three-direction exploration; there is no time.
- **My limit:** I can only see this machine. Teammates' work reaches me through the shared repo (git pull) and what you paste.

## 9. Risks and open decisions

| Risk | Plan |
|---|---|
| **Two core people for a three-role PRD** | Cut UI to the review and examiner pages. Build in START-HERE §3 "minimum core" order. Apply PRD cut order at 13:45 if not green. SHOULD items likely won't happen; that is acceptable. |
| Nobody on the team knows Spring well | **Your decision:** move the gate into Python (FastAPI + pymongo transactions), so the stack is Python + Angular. This reopens a PRD decision, so I won't do it unless you say so. If Sukhman is fluent in Java, keep Spring. |
| The sandbox tier blocks transactions or change streams | The smoke test runs first. If it fails, ask MongoDB staff for another tier immediately. |
| Java 8 is the default on this Mac | Set `JAVA_HOME` to the installed Temurin 21 for the gate. |
| Voice or tracing eats core time | Neil works alone on these; there are no core-critical handoffs before 13:45; 15:00 go/no-go. |
| Invented numbers | Every figure comes from `make eval`, `make rules` or an Atlas query run today. [VERIFY] facts are checked by R1 before the stage. |

## 10. Timeline (EST)

| Time | Gate |
|---|---|
| now | Harry: Atlas sandbox cluster, IP, DB user (you can start this while reviewing). Neil: LangSmith and ElevenLabs accounts. Sukhman: Java 21 + Spring scaffold. |
| 12:40 | **Checkpoint 1:** data in Atlas; smoke test passes (transaction + change stream). |
| 13:45 | **Checkpoint 2 (core demo):** honest approval executes with read-back; bulk 50 → 0; forged dwell → 0; bypass → 403. Commit and tag `core-ok`. |
| 14:15 | `docs/preregistration.md` committed before any eval run. |
| 14:45 | **Checkpoint 3:** full UI path; detector kill and restart; `test-conflict` passes; R1-R8 pass. |
| 15:00 | Spoken attestation go/no-go (Neil). |
| 15:30 | **Feature freeze.** Videos: fallback burst + 1-minute with ElevenLabs voiceover. |
| 16:15-16:45 | README (eval pasted verbatim), description, public-repo check from a logged-out browser, all teammates added, **submit**. |

## 11. Approval gate

Nothing below starts until you say "approved", or tell me what to change:
- [ ] Spawn researchers R1-R5
- [ ] `git init` and the first local commit of docs
- [ ] Write the smoke test and start Harry's Python setup
- [ ] Teammates start their sessions with PRD §17

**Questions for you:**
1. Does the A+C / B split match Harry's and Sukhman's skills?
2. Keep Spring, or move the gate to Python?
3. Will you create the public GitHub repo, or should I?

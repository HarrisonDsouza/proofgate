# ProofGate: instructions for any AI coding session in this project

You are helping a 3-person team build **ProofGate** at the MongoDB "Agents in Context" hackathon in Toronto, **today, Saturday Nov 14, 2026**. Submissions close at **5:00 PM EST**. Every decision below was already made in an earlier planning session; do not reopen them unless the user asks.

## Read before writing any code
1. `START-HERE.md`: what the project is, the minimum core, and today's order of work.
2. `docs/PRD.md`: **the build spec. Follow it exactly.** Section 7 = data model, 8 = architecture and API contract, 11 = hour plan, 12 = evaluation and tests, 13 = demo, 14 = judge Q&A, 16 = submission checklist, 17 = per-engineer first prompt.
3. `docs/OFFICIAL-RESOURCE-GUIDE.md`: the organizers' rules and resources (authoritative over anything else here).
4. `docs/SETUP-RESEARCH.md`: verified setup commands (MongoDB Agent Skills, MCP Server, Vector Search, Voyage AI, LangGraph checkpointer, ElevenLabs, LangSmith).
5. `docs/DECISION-RECORD.md`: why ProofGate was chosen, the researched evidence, rejected ideas, and every simulated judge's must-fix and killer question.
`background/` holds earlier, **superseded** planning documents; read only for context.

## What we are building (one paragraph)
An AI agent proposes adverse decisions (insurance claim denials). A denial can execute only if MongoDB Atlas holds per-case proof that a credentialed human reviewer opened every piece of evidence the agent cited, timed **by the server**, at or above a policy floor, and is not stamping in bulk. One Atlas transaction checks this and mints a single-use grant; the mock claims system refuses anything without a grant. Rubber-stamping (e.g. "approve 50") suspends the reviewer mid-run, revokes grants, and reopens denials already executed, with read-back. An examiner page reconstructs any case. Entered under **Statement One: Agents You Can Audit**.

## Hard rules from the organizers (losing these loses the event)
- Build in the **MongoDB Atlas Hackathon Sandbox** project from the invite email. A personal Atlas account makes the team ineligible as a finalist.
- **All work original and written today.** Do not copy code from other projects in this machine or repo.
- Submission (by the user, on the Cerebral Valley platform, before 5:00 PM): a **public GitHub repo** link, a **1-minute demo video with working audio**, a concise description, **all teammates added**.
- Live in-person judging at the team's table from 5:15 PM; top 6 present on stage at 7:00 PM.

## Engineering rules (non-negotiable, from the PRD and the judges)
1. MongoDB Atlas is the only state store. URI and DB name come from `.env` (`MONGODB_URI`, `DB_NAME`). **Never hard-code or commit secrets**; commit `.env.example` only.
2. Every document has `tenant_id`; every compound index leads with it; every query filters by it.
3. **Dwell time is computed only on the server** from view tokens and heartbeats. Ignore any client-supplied `dwell_ms` (store it under `client_supplied_ignored`).
4. **The gate is one transaction** (snapshot read concern, majority write concern) that always writes the per-reviewer `reviewer_state` document with a version guard, so concurrent approvals and suspensions conflict instead of slipping through. **Pass the session to every operation inside it** (the number-one bug). Store `txn_attempts`.
5. `$jsonSchema` validators check required fields and types; thresholds live in the versioned `review_policies` document, never in code.
6. The target system changes a record only by atomically consuming a valid grant; otherwise 403 plus a `target_log` entry.
7. **The LLM proposes, code decides.** The LLM (optional, S6) may draft a rationale; it never sees grants, never calls the target, never decides anything.
8. **Never invent results.** Every number in the README, video or pitch comes from `make eval`, `make rules` or a stored-state query run today. Facts marked [VERIFY] in the PRD must be checked before they are said on stage.
9. Build all **MUST** items before any SHOULD/COULD. If behind, apply the PRD cut order (Section 6) immediately. Keep it simple: no auth framework, no Docker, no extra services.
10. After each endpoint, give the user a curl command or test that proves it works against Atlas.

## Git and GitHub
- The team repo is https://github.com/HarrisonDsouza/proofgate (public). Follow `WORKFLOW.md`: work on your own branch (`harry`, `sukhman`, `neil`), stay in your own folders, land work on `main` only through pull requests.
- Commit often on your branch. **Push or open a PR only when the user asks.** Never push to `main` directly, never force-push, never change repo settings.
- Before submission, check the repo is public from a logged-out browser.

## Time discipline (EST, absolute times)
- 12:40 checkpoint: data in Atlas; **transactions and change streams confirmed on the sandbox tier** (`make smoke`).
- 13:45 checkpoint: core demo works (honest approval executes; bulk 50 executes 0; forged dwell executes 0; bypass gets 403).
- 14:15: commit `docs/preregistration.md` before the first evaluation run.
- 15:30: **feature freeze.**
- 15:30-16:15: record the fallback video and the 1-minute submission video.
- 16:45: submitted.
If the clock is past a checkpoint and it is not met, say so plainly and propose cuts; do not keep adding scope.

## Communication
The user is new to AI agents, MongoDB and voice APIs. Explain what you did and how to check it in plain language, briefly.

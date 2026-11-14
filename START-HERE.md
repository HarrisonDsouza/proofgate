# START HERE: ProofGate handoff

You are picking this up in a new session. Everything decided so far is in this folder. Read this page, then `docs/PRD.md`.

## 1. What ProofGate is

**Pitch:** "An AI agent can queue thousands of claim denials an hour. ProofGate lets a denial execute only if MongoDB Atlas holds per-case proof that a credentialed reviewer opened every piece of evidence the agent cited and spent real time on it, timed by the server. A batch of 50 rubber-stamps executes 0."

- **Official problem statement:** Statement One, *Agents You Can Audit*. It answers all three questions: enforce before the action (the transactional gate), record who/what/why (approvals, gate decisions, examiner replay), stop or roll back mid-run (suspension, grant revocation, reopened claims).
- **The real problem it rests on:** ProPublica (2023) reported Cigna's PxDx process denying 300,000+ claims in two months at about 1.2 seconds of physician review each ("50 at a time"); a class action followed. Cigna disputes the report and says PxDx is not AI, so always say "the pattern as reported". Supporting evidence: 2025-2026 incidents of agents acting past a "stop" or "freeze" instruction (Meta's Summer Yue, Replit); FINRA's 2026 report on reconstructing agent actions. **Every figure is marked [VERIFY] in the PRD; check before saying it on stage.**
- **Buyer:** the insurer's Chief Compliance Officer or General Counsel, exposed to PxDx-style suits and state laws requiring individual clinician review (e.g. California SB 1120 [VERIFY]).
- **Originality:** three independent searches found no hackathon project, repo or product that gates a denial on server-timed per-evidence review and suspends rubber-stampers mid-run. Closest: Airia approval checkpoints, generic approval gates (agent-approval-gate, past hackathon projects RunwayOps, LabRat, Aegis), a DEF CON research poster on rubber-stamping. **"None found" is not "proven new"**; PRD Section 2 has the exact line to say if a judge says "this exists".

## 2. Before writing code (the first 15 minutes)
- [ ] Every teammate checked in, approved on the Cerebral Valley platform, and in the Discord.
- [ ] Atlas sandbox invite accepted; cluster created **in the sandbox project**; IP on the Network Access list; DB user created; connection string in `.env` (copy `.env.example`).
- [ ] Run the smoke test as early as possible: **one multi-document transaction and one change-stream event must work on the sandbox tier.** If either fails, ask a MongoDB staff member for a different tier immediately; the design depends on both.
- [ ] MongoDB Agent Skills and the MongoDB MCP Server installed in Claude Code (PRD Section 9 step 3; `docs/SETUP-RESEARCH.md`). Keep the MCP server **read-only**.
- [ ] Keys: LLM API key (an API balance, not a chat subscription) only if you will build S6; Voyage AI key only for S7 path B.
- [ ] Decide who is Engineer A (Python), B (Spring Boot), C (Angular). Each pastes PRD Section 17 into their own session with their role.
- [ ] Public GitHub repo: the submission requires one. The user creates it (or tells the session to); add all teammates.

## 3. If you fall behind: the minimum core that still wins
The PRD has 17 MUST items across three services, which is a lot for about 5 hours with a team new to this. If the 13:45 checkpoint is at risk, protect this core and cut everything else in the PRD's cut order:

1. Seed data: one tenant, ~50 cases, reviewers `dr-demo` and `dr-stamper` (M1, M2).
2. Server-timed evidence views and heartbeats (M4) and server-computed approvals, including the bulk-50 endpoint (M5).
3. **The gate transaction** with G1, G2, G4, G5, G6 and the `reviewer_state` version write (M7), reading thresholds from one policy document (M6).
4. Mock claims system that applies only with a valid grant, 403 otherwise, plus read-back (M8, M9).
5. Inline suspension on G6 that revokes grants and reopens already-confirmed denials (M10, M11 without the worker UI).
6. Review page with the red "approve 50" button and the result banner (M12); a simple examiner page (M13).
7. The rules check R1-R7 (M14) and a small honest evaluation (M15), even if only the honest, stamper and tab-idler groups.

The demo that must work no matter what: **bulk 50 → executed 0 with reasons → reviewer suspended; one honest 30-second review → executed and read back; curl without a grant → 403; examiner page rebuilds the case.**

## 4. Today's timeline (EST)
| Time | What |
|---|---|
| now-12:00 | Setup checklist above |
| 12:40 | Checkpoint: data in Atlas, transactions and change streams confirmed |
| 13:45 | Checkpoint: core demo works; commit and tag |
| 14:15 | Commit `docs/preregistration.md` before any eval run |
| 15:30 | **Feature freeze** |
| 15:30-16:15 | Fallback video and the **1-minute** submission video (PRD Section 13) |
| 16:15-16:45 | README, description (PRD Section 16), public repo check, all teammates added, **submit on the Cerebral Valley platform** |
| 17:00 | Hacking closes |
| 17:15-18:45 | Live judging at your table (PRD Section 13 three-minute demo, Section 14 Q&A) |
| 19:00 | Top 6 present on stage |

## 5. Partner credits (from the official guide)
- **Voyage AI:** 200M free tokens (dashboard.voyageai.com; save the key immediately; add a payment method to lift rate limits, no charge within the allowance). Only needed for S7.
- **ElevenLabs:** Creator plan for those checked in by 11 AM (ElevenLabs Discord `#coupon-codes`). ProofGate does not use voice by design; skip unless everything else is done.
- **LangSmith:** $50 credits by form within 10 days (C3 tracing is optional).

## 6. What's in this folder
| Path | What it is |
|---|---|
| `CLAUDE.md` | Rules any AI session must follow; read automatically by Claude Code |
| `START-HERE.md` | This page |
| `docs/PRD.md` | The full build spec |
| `docs/OFFICIAL-RESOURCE-GUIDE.md` | The organizers' resource guide, as provided |
| `docs/SETUP-RESEARCH.md` | Verified setup commands and gotchas |
| `docs/DECISION-RECORD.md` | How the idea was chosen: researched problems, rejected ideas, all judge statements |
| `background/` | Earlier planning (superseded): first handoff, four earlier PRDs, a beginner's learning guide to every technology used |
| `.env.example`, `.gitignore` | Starter files for the repo |

## 7. Honest limits to state when asked (PRD Section 15)
Dwell time is a proxy and a scripted "heartbeat forger" passes the gate (shown on purpose as the null result); the evaluation is simulated and time-scaled; synthetic data only, not a medical tool; demo login is a reviewer picker; all judge opinions in these documents came from simulated personas, not the real judges.

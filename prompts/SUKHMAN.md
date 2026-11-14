# Sukhman: starting prompt

## Before anything: the Java check

This role is **Spring Boot 3.5 on Java 21**. If you are not comfortable with Java and Spring, **tell Harry before you start**. The team then decides whether the gate moves to Python. Don't start until that's settled.

## What to pull

```bash
git clone https://github.com/HarrisonDsouza/proofgate.git && cd proofgate
git checkout sukhman
cp .env.example .env     # paste MONGODB_URI from Harry's DM (README "Sandbox setup" step 3)
export JAVA_HOME=$(/usr/libexec/java_home -v 21)   # Mac; java -version must say 21
```

## What you own

**Engineer B, the gate service, in `gate/` only:**
- reviewer sessions; evidence fetch with view tokens and exclusive focus; heartbeats and close
- server-computed approvals, plus the bulk "approve 50" endpoint
- versioned policies
- **the gate transaction (G1-G8)**, with the `reviewer_state` version write and `txn_attempts`
- `/api/gate/confirm` (read-back)
- the suspension transaction
- the **detector** profile (change stream + resume token) and the compensation worker
- the examiner API
- the `X-Debug-Pause-Ms` test hook
- PRD items: M4, M5, M6, M7, M10, M11, M13 (API).

## First steps, in order

1. Scaffold `gate/` (PRD §9 step 9: start.spring.io, Boot 3.5.x, Java 21, web + data-mongodb + validation) and add a MongoClient bean reading `MONGODB_URI` and `DB_NAME`.
2. `POST /api/sessions` → `GET /api/cases/{caseId}/evidence/{evidenceId}` (view tokens, exclusive focus) → heartbeat and close (`review_events`).
   - These work once Harry's seed data is in Atlas (handoff H2, around 12:40). Until then, insert one test case by hand.
3. Open a PR at each working endpoint, with its curl in the description.
4. Before 13:45: approvals (+ bulk), policies, **the gate transaction**, confirm. Mark handoff H3 `ready`.
5. After 13:45: suspension transaction, detector, compensation worker, debug hook (H9), examiner API (H10).

## Paste into Claude Code

```
You are helping a 3-person hackathon team build "ProofGate". Read CLAUDE.md, START-HERE.md and docs/PRD.md
completely before writing code, then follow the PRD exactly (Section 7 data model, 8 architecture and API
contract, 11 hour plan, 12 tests). Also read README.md and WORKFLOW.md.

My role: Engineer B (Spring Boot 3.5 / Java 21) - gate/ only: sessions, view tokens, heartbeats, approvals
(server-computed, bulk), versioned policies, the gate transaction, /gate/confirm, the suspension transaction,
the detector profile (change stream + resume token in detector_state), the compensation worker, the examiner
API, and the X-Debug-Pause-Ms hook. I work on branch `sukhman`.

Non-negotiable rules:
1. MongoDB Atlas is the only state store; URI from env MONGODB_URI, DB from DB_NAME. Never commit secrets.
2. Every document and compound index leads with tenant_id; every query filters by it.
3. Dwell is computed ONLY on the server from view tokens + heartbeats (credit min(gap,7000) ms only if
   gap<=7000 and visible and interacted within 15 s; one open token per session). Ignore any client dwell_ms
   and store it under client_supplied_ignored.
4. The gate is ONE transaction (sync driver ClientSession.withTransaction, snapshot read concern, majority
   write concern). Pass the session to EVERY operation. Always write reviewer_state {_id:"<tenant>|<reviewer>",
   version: v_read} with $inc version. Count callback invocations and store txn_attempts.
5. Thresholds come only from the active review_policies document.
6. Build MUST items first, in the Section 11 order for Engineer B. No auth framework, no Docker.
7. After each endpoint, give me a curl that proves it works against Atlas.

Start now: list the files you will create with a one-line purpose each, then scaffold gate/ and implement
POST /api/sessions.
```

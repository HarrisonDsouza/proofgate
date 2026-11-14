# Sukhman: starting prompt

## What to pull

```bash
git clone https://github.com/HarrisonDsouza/proofgate.git && cd proofgate
git checkout sukhman
cp .env.example .env     # paste MONGODB_URI from Harry's DM (README "Sandbox setup" step 3)
```

## What you own (COMBINED-PLAN §2; role marked open until you confirm)

The gate and detector **working live on Atlas**. It's your own code from the zip, now the team's base, so no Java is needed:
- `pg/review.py`: sessions, view tokens, heartbeats, approvals, bulk-50
- `pg/checks.py`: G1-G8 and dwell crediting
- `pg/gate.py`: the transaction, `reviewer_state`, grants, suspensions, confirm
- `pg/detector.py`, `pg/cusum.py`, `pg/riskcontrol.py`, `pg/stats.py`
- `eval/test_conflict.py`
- `docs/DATA.md`, and the pitch figures (KFF and ProPublica, verified before use)

If you'd rather do data, volunteers and the pitch instead, tell Harry now. Harry then takes the gate.

## First steps, in order

1. README steps 1, 3 and 4: tools, `.env`, `make install`. Harry creates the cluster and runs `make setup seed`.
2. Run `DEMO_DEBUG_HOOKS=true make test-conflict` against Atlas. It must print all PASS; fix what fails.
3. Run `make dev`. Bulk 50 as `dr-stamper` → executed 0, reviewer suspended. A forged `dwell_ms` → 0. This is the 13:45 checkpoint.
4. Detector kill/restart demo: `RUN_BACKGROUND=0`, `make detector`, kill it mid-burst, restart, check it ends with one suspension.
5. Run `make explain` and confirm an IXSCAN.
6. Data notes and pitch figures. Volunteer sessions only if the team agrees (open question Q2), 14:00-14:45.

## Paste into Claude Code

```
You are helping a 3-person team build "ProofGate" at a MongoDB hackathon today. Read CLAUDE.md, README.md,
WORKFLOW.md, project-docs/COMBINED-PLAN.md, project-docs/hackathon-rules.md and docs/HANDOFF.md first, then
docs/PRD.md (behaviour spec). Precedence: COMBINED-PLAN -> HANDOFF -> PRD.

My role (Sukhman): make the gate and detector work live on the Atlas sandbox: pg/review.py, pg/checks.py,
pg/gate.py, pg/detector.py, pg/cusum.py, pg/riskcontrol.py, pg/stats.py, eval/test_conflict.py, docs/DATA.md.
I work on branch `sukhman` and stay in those files; I ask Harry before touching shared files (pg/main.py
routes, pg/config.py, requirements, .env.example).

Before building, check the hackathon must-dos in project-docs/hackathon-rules.md and the invariants in CLAUDE.md:
the gate is ONE transaction (snapshot read, majority write) that always writes reviewer_state with a version
guard; pass session=s to EVERY operation inside it; store txn_attempts; dwell is computed only on the server and
client dwell_ms goes to client_supplied_ignored; tenant_id leads every index and filters every query;
thresholds come only from the active review_policies document. Never invent results, and never quote the
simulated percentages in the planning docs: numbers come only from make eval / make test-conflict / make rules
run today. Do not rewrite working code: run it live, fix what fails.

Start now: run DEMO_DEBUG_HOOKS=true make test-conflict against the sandbox with me, explain each PASS/FAIL in
plain words, and fix failures one at a time. Then help me verify bulk 50 -> executed 0 in the UI.
```

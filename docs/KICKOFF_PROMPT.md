# Paste this into each Claude Code session

> **Team note (combined plan):** where this file differs from `project-docs/COMBINED-PLAN.md`, the combined plan wins (roles, UI stack, timeline, tools, ElevenLabs). Simulated figures in this file are not results; never quote them.

> Each teammate's starting prompt is now in `prompts/` (HARRY, SUKHMAN, NEIL). Keep this file for its live-check list.

```
Read CLAUDE.md, START-HERE.md and docs/HANDOFF.md fully. The repo already contains a single-process Python
implementation of ProofGate (pg/), tested offline (pytest: property tests for G1-G8 and dwell crediting,
CUSUM calibration). It has NOT yet run against a live Atlas cluster. Do not rewrite it; run it, fix what the
live run shows, and extend it.

My role is <A | B | C | Sukhman>.

Step 1 (everyone, once): with .env filled from the SANDBOX cluster, run `make install smoke setup seed`, then
`make dev`. Verify against the live database, and fix any failure before anything else:
  - make bypass               -> two PASS 403 lines, record unchanged
  - DEMO_DEBUG_HOOKS=true make test-conflict -> all PASS
  - in the UI as dr-stamper: "Select all, approve 50" -> "Executed: 0 of N", reviewer suspended
  - as dr-demo: open the cited evidence ~20 s each, approve -> executed, read back, examiner shows the timeline
  - make rules -> R1-R8 pass
Add pytest integration tests for these, skipped when MONGODB_URI is unset.

Then follow docs/HANDOFF.md section 10 for my role. Keep every invariant in CLAUDE.md. Pass session=s to every
operation inside a transaction. Never show a number that is not in eval_runs or printed by a make target.
```

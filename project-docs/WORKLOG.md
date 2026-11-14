# Work log

The tech lead (Harry's Claude Code session) keeps this log. Every PR, review verdict and notable event is recorded here, newest at the bottom. Times are EST, Sat Nov 14 2026.

## Pull requests

| PR | Author / branch | What | Review | Proof run | Verdict | Merged |
|---|---|---|---|---|---|---|
| #1 | Harry (import of Sukhman's code) / `harry` | Combined plan, aligned docs, Sukhman's Python implementation | tech lead | `make ci`: ruff clean, 15 passed | OK | 12:49 |
| #2 | Harry / `harry` | `make ci` (local lint, tests, secret scan), because GitHub Actions is billing-locked | tech lead | `make ci` PASS | OK | 12:52 |
| #3 | Harry / `harry` | Tech-lead PR review replaces the API-key reviewer; work log; plan critique | tech lead | `make ci` PASS | OK | 13:03 |
| #4 | Harry / `harry` | Research reports, FIXES.md must-fix list, doc corrections (docs only) | tech lead | `make ci` PASS | OK | 13:07 |
| #5 | Harry / `harry` | Atlas-tier research, FIXES.md A1-A3, work-log time fixes (docs only) | tech lead | `make ci` PASS | OK | 13:08 |
| #6 | Harry / `harry` | Security P1: console key on sessions and the control plane, refuse weak agent key, removed HTTP compensate and debug pause, paused run-once fix, bulk banner | tech lead | `make ci` 46 passed; live curl 401/401/405 | OK | 13:12 |

## Events

- **12:49** Sukhman's code imported (H0 accepted).
- **12:52** GitHub Actions is unavailable ("account locked due to billing"). `make ci` is the required check instead.
- **12:55** Research and review agents launched. Their output goes in `project-docs/research/`:
  - claims-facts: on-stage facts verified
  - atlas-tier: transactions and change streams on our tier
  - neil-tools: ElevenLabs and LangSmith APIs
  - security-review: attacker review of `pg/`
  - plan-critique
  - code-review-baseline: M1-M17 status and demo-breaking bugs
- **13:00** The plan critique is in: [research/plan-critique.md](research/plan-critique.md). The automatic PR reviewer was removed (no API key). Reviews now happen in the tech lead's session.
- **13:04** Security review is in: **FAIL**, with 7 must-fix items before the demo ([research/security-review.md](research/security-review.md)).
- **13:07** Claims fact-check is in ([research/claims-facts.md](research/claims-facts.md)). The KFF figures are verified; the list of things not to say on stage is in the file.
- **13:07** Neil's tools research is in ([research/neil-tools.md](research/neil-tools.md)): use `scribe_v3`, then `scribe_v2`; LangSmith redaction hooks are confirmed; no ElevenLabs prize criteria are published. Fixed elevenlabs.md and langsmith-setup.md to match.
- **13:07** Baseline code review is in: **FAIL** ([research/code-review-baseline.md](research/code-review-baseline.md)). Security review and code review merged into one owner-by-owner list: [FIXES.md](FIXES.md).
- **13:08** Atlas-tier research is in ([research/atlas-tier.md](research/atlas-tier.md)): transactions and change streams work on Free, Flex and M10; every in-transaction operation passes the session; the smoke test's exit code can't be trusted. Rows A1-A3 added to FIXES.md. All six agents are done.
- **13:39** Atlas is live: an M10 cluster in the hackathon sandbox project. On it:
  - `make smoke`: PASS (transaction and change stream)
  - `make setup` and `make seed`: 200 cases, 123 proposed denials (setup re-runs fine, so the role is OK)
  - `make bypass`: 3 PASS (no grant → 403, made-up grant → 403, record unchanged)
  - `make test-conflict`: (a), (b) and (c) all PASS, including the forged burst executing 0 of 50
  - `/rules`: R1-R8 all pass
  - the API starts with the new keys, and `/api/sessions` without the console key returns 401
  - **Note:** each gate call takes about 1.7 s from this laptop, so a 50-item burst takes about 90 s; the demo plan should allow for it.

## Checkpoints

| Time | Checkpoint | Status |
|---|---|---|
| 13:15 | smoke, setup and seed on the sandbox; `make bypass` PASS | **met at 13:39** (late) |
| 13:45 | core demo works; tag `core-ok` | |
| 14:30 | PREREGISTRATION merged before the held-out eval | |
| 16:00 | feature freeze | |
| 16:45 | submitted | |

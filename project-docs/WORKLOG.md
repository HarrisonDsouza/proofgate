# Work log

The tech lead (Harry's Claude Code session) keeps this log. Every PR, review verdict and notable event is recorded here, newest at the bottom. Times are EST, Sat Nov 14 2026.

## Pull requests

| PR | Author / branch | What | Review | Proof run | Verdict | Merged |
|---|---|---|---|---|---|---|
| #1 | Harry (import of Sukhman's code) / `harry` | Combined plan, aligned docs, Sukhman's Python implementation | tech lead | `make ci`: ruff clean, 15 passed | OK | 12:49 |
| #2 | Harry / `harry` | `make ci` (local lint, tests, secret scan), because GitHub Actions is billing-locked | tech lead | `make ci` PASS | OK | 12:52 |

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

## Checkpoints

| Time | Checkpoint | Status |
|---|---|---|
| 13:15 | smoke, setup and seed on the sandbox; `make bypass` PASS | blocked: no Atlas cluster yet |
| 13:45 | core demo works; tag `core-ok` | |
| 14:30 | PREREGISTRATION merged before the held-out eval | |
| 16:00 | feature freeze | |
| 16:45 | submitted | |

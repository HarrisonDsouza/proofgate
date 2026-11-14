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
| #8 | Sukhman / `sukhman` | Gate + detector hardening, streaming CUSUM, restart demo, voice evidence | tech lead + reviewer + security-reviewer | 8 must-fixes re-reviewed (7 fixed, #5 partly); ruff clean; 80 tests on Atlas (1 test bound fixed for Atlas latency); e2e, bypass, test-conflict ALL PASS | OK, merged | 14:47 |
| #9 | Harry / `harry` | `make e2e` honest path + halt; core-ok logged; tag `core-ok` | tech lead | `make e2e` ALL PASS on Atlas | OK | 14:01 |
| #10 | Harry / `harry` | React reviewer + examiner UI; make ui; make demo-case | tech lead | build clean; examiner checked live on Atlas; demo-case ALL PASS | OK | 14:08 |
| #11 | Harry / `harry` | UI design pass from the design critique | design-critic + tech lead | build clean; checked live | OK | 14:10 |
| #12 | Harry / `harry` | Ledger + Case File UI (directions A + C chosen by Harry), Supervisor page, self-hosted fonts, flow diagram | tech lead + Impeccable detector | build clean; detector 0 findings; Examiner, Supervisor, Review checked live; approve flow tested with the console key; 80 tests on Atlas on the final commit; GitHub Actions not started (account billing lock) | OK, merged | 15:27 |

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
- **14:01** Added `make e2e` (honest path over HTTP, then a supervisor halt) and ran it on Atlas: **ALL PASS**.
  - dr-demo's review of CLM-A-0003 was credited by the server at about 22 s per cited item.
  - The approval was accepted; the executor executed 1 of 1; the denial is CONFIRMED by read-back; the claims record is DENIED.
  - R1-R8 pass.
  - The halt created 1 compensation, which was confirmed; the record is OPEN again; R1-R8 still pass.
  - Together with test-conflict (forged burst 0 of 50) and bypass (403), **the core demo works: `core-ok`**.
- 14:17 PR #12 opened: professional UI redesign + Supervisor page. Alignment audit (plan vs PRD, judge must-fixes, organizer rules) started; report goes to project-docs/research/alignment-audit.md.
- 14:30 Alignment audit written (project-docs/research/alignment-audit.md): eval crash found (int dict keys in eval/simulate.py) and fixed; Makefile calibrate targets passed an unsupported --floor flag, fixed.
- 14:20 Dev eval (seed 1) ran clean on Atlas; numbers not reported. 14:25 PREREGISTRATION.md committed (7df270e) before the held-out run (its "Committed at 14:58" line is a typo; git time is authoritative).
- 14:31 Held-out eval (seed 20261114) run once on Atlas; output committed unedited to docs/eval-heldout.txt (350d06c).
- 14:45 First baseline run discarded: its detector thread died on a scratch tenant created by PR #8 tests run at the same time (old detector did not catch LookupError). Re-run after merge.
- 14:47 PR #8 merged after Atlas checks. Verdict comment on the PR lists follow-ups (gate.confirm 500 on unknown denial, /rules unauthenticated, seed not clearing attestations).
- 14:55 PR #12 updated with the Ledger + Case File design; Impeccable and Diagram Design skills installed for Harry (files read first). Flow diagram in project-docs/design/.
- 15:06 Browser test of the new UI with the console key: honest approval of CLM-A-0005 (51.7 s server-credited, 2 of 2 cited) → "Executed 1 of 1", DENIED stamp. "Select all · approve 50" → "Executed 0 of 50 · dr-demo suspended", both executed denials reopened. **Problem: the bulk click took about 5 minutes end to end** (50 sequential approval transactions, then 50 gate calls). Demo data reseeded (`make seed && make demo-case`, ALL PASS).
- 15:15 Bulk speed-up (Harry approved): approve_bulk writes the 50 approvals, proposal updates, reviewer_state and hash-chained events in one transaction; the executor re-reads status and skips proposals a suspension already sent back. Scratch tenant: 50 approvals 2.1 s (was ~80 s), agent run 5.9 s. Browser: bulk 4.3 s + run-once 16.1 s, "Executed 0 of 50 · suspended". `make test` 80 passed, lint clean.
- 15:20 Status audit (PRD, first handoff, combined plan vs code). README Results + disclosures filled from docs/eval-*.txt; baseline committed; enforcement map refreshed; judge Q&A placeholders filled and a do-not-claim list added; LangSmith hook applied to agent steps.
- 15:27 PR #12 merged to main (17a6ab2). Open for teammates: Sukhman's DATA.md commit on `sukhman` is not merged; Neil has no commits.
- 15:37 Persona (4 non-technical domain experts) and judge-archetype (4) review workflow; findings and prioritized actions in project-docs/research/persona-and-judge-review.md. Fix from it: executor no longer LangSmith-traced (grant token). PR #13 opened, awaiting Harry's merge.

## Checkpoints

| Time | Checkpoint | Status |
|---|---|---|
| 13:15 | smoke, setup and seed on the sandbox; `make bypass` PASS | **met at 13:39** (late) |
| 13:45 | core demo works; tag `core-ok` | **met at 14:01** (late) |
| 14:30 | PREREGISTRATION merged before the held-out eval | |
| 16:00 | feature freeze | |
| 16:45 | submitted | |

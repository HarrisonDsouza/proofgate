# Baseline code review (R6, dev-system:reviewer, 13:07 EST)

The reviewer is read-only, so the tech lead saved its report here.
**Verdict: FAIL (baseline).** This review comes from reading the code only: nothing was run, and the code has never touched Atlas.

## Top 5 (ranked by "will it break the demo")

1. **`/compensate` writes any status without a grant.**
   - Where: `pg/target.py:43-57, 66-69`.
   - Problem: a judge can curl it to bypass the gate.
   - Fix: delete the route, or require the service key plus a matching denial for the same tenant and record, plus the policy's `compensate_status`. Otherwise return 403 and write `target_log`.
2. **The bulk-50 banner won't say "0 of 50", and the run is slow.**
   - Where: `review.py:152-155`, `gate.py:62-66`.
   - Problem: the detector suspends the reviewer at about approval 10. The earlier approvals are invalidated, so `run-once` sees about 40 proposals and the banner reads "0 of ~40". It is also about 90 sequential transactions with no UI timeout.
   - Fix: take N from `bulk.submitted` and compute refused = N − executed. Use a thread pool, or demo with `RUN_BACKGROUND=0` so the gate's inline G6 does the suspending.
3. **`executor_loop(once=True)` hangs while paused.**
   - Where: `pg/agent.py:49-51`.
   - Problem: `continue` skips `if once: return`.
   - Fix: when paused and `once` is true, return `results`.
4. **The detector dies silently.**
   - Where: `pg/detector.py:84-92`.
   - Problem: there is no try/except around `handle()`, and a stale resume token crashes `run()`. Also, `make dev` (`RUN_BACKGROUND=1`) plus `make detector` gives two detectors sharing one `detector_state`, so the kill/restart demo proves nothing.
   - Fix: catch errors per event and fall back to a fresh watch on `ChangeStreamHistoryLost`. Demo with `RUN_BACKGROUND=0`.
5. **Nothing has been proven on Atlas, and the gate has no automated test.**
   - Fix: run `make smoke setup seed bypass test-conflict rules` first and fix whatever fails.

## M1-M17 status

| M | Status | Notes |
|---|---|---|
| M1 | implemented, gaps | `pg/db.py`. No validators for cases, target_records, view_tokens, reviewer_sessions or reviewer_state. No `demo_invalid_insert`. |
| M2 | partial | `seed/generate.py`: Acme only; no payer-birch, no 40 accounts, no dr-shared or dr-fraud-ops; `created_at` uses `now()`; reads a path relative to the current directory. |
| M3 | partial | `triage()` runs inline from seed; there is no loop; the "cited ids exist" check is vacuous. |
| M4 | implemented | `review.py:64-104`. Has the heartbeat race (bug 8). |
| M5 | implemented | Client dwell is ignored. No proposal-status guard (bug 6). Bulk is not atomic. |
| M6 | implemented | `gate.py:199-213`. |
| M7 | implemented, unproven | Session passed everywhere, snapshot and majority concerns, `VersionMoved` labelled transient, `txn_attempts` stored. |
| M8 | partial (hole) | apply is correct; `/compensate` is the bypass. |
| M9 | partial | only `/api/agent/run-once`; the paused hang. |
| M10 | implemented, gaps | Top 5 #4 and bug 5. |
| M11 | partial | compensation runs in-process; no `FAIL_NEXT_COMPENSATE` (C6). |
| M12 | partial | `static/` only. The banner lacks the timestamp, policy version and rule. It sends `dwell_ms:45000` (harmless). |
| M13 | partial | No audit hash chain. Shows the latest approval, not necessarily the one tied to the denial. The examiner is a JSON dump. |
| M14 | implemented | R8 checks the session chain only. |
| M15 | implemented, unrun | `eval/simulate.py` calls Python directly, not HTTP. |
| M16 | partial | `test_conflict` (a), (b) and (c) only; (d) detector crash missing; (c) doesn't stop the detector. |
| M17 | partial | `reset()` skips `chain_heads`; reset time not measured; no fallback video yet. |

## Other demo-path bugs

5. **Suspension misses a denial that is applied but not yet confirmed** (`gate.py:69-70, 183-196`).
   - `confirm` crashes on an unknown denial and can overwrite REVERSED.
   - Fix: guard on `status == AUTHORIZED`, and refuse or compensate if the reviewer is suspended.
6. **The same proposal can be approved and executed twice** (`review.py:140`, `checks.py:39`).
   - Fix: `approve` requires `pending_review`; G1 requires `proposal.status == approved` and a matching `approval_id`.
   - Also: a refused proposal goes to `needs_review` and never comes back to the queue.
7. **Bulk fails partway** on an unknown id: the earlier approvals stay committed and the client gets a 404. Fix: validate all ids first.
8. **Heartbeat race** (`review.py:85-93`).
   - Concurrent heartbeats double-credit dwell.
   - Fix: add `last_hb_at` to the update filter and give 0 credit on a miss.
9. **`_event` is not atomic** (`review.py:28-37`).
   - Concurrent events share a `prev_hash`, so R8 goes red.
   - Fix: one transaction, or build the chain by `seq` order.
10. **`.env` is loaded only by make.** python-dotenv isn't in the requirements, so always run things through `make`.
11. **Seed gaps.**
    - The acme policy has no `detector.cusum`, so the drifter/CUSUM beat can't fire on payer-acme.
    - The seed doesn't clear `chain_heads`.
12. **Policy flags are never read:** `require_unexpired_license`, `require_all_cited_evidence` and `separation_of_duties`. They are fail-closed, but they are dead settings.

## Invariant violations

- **`tenant_id` missing from a query:**
  - `gate.py:173, 188`
  - `detector.py:106`
  - `rules.py:65, 94, 97`
  - `detector.py:99` (a cross-tenant compensation scan, by design)
- **Indexes not leading with `tenant_id`:** `denials{approval_id}`, `compensations{denial_id}`, `compensations{status,next_attempt_at}`. The TTL indexes must be single-field, so they are exempt.
- **Thresholds in code:**
  - 7 s heartbeat gap and 15 s input window (`checks.py:11-12`); both are PRD constants.
  - 60 s grant life (`gate.py:149`).
  - 2 h view-token TTL (`review.py:77`).
  - `require_specialty_match` defaults to True.
- **Client dwell:** not trusted. The client-sent `visible` and `interacted_within_ms` are trusted, which is the known heartbeat-forger limit.
- **LLM deciding:** none.
- **Control plane:** policies, suspensions, pause, run-once and compensate have no authentication (see security-review.md).

## Tests that matter

- **No tests** for `gate.execute`, `target.apply`, `review.approve` or `rules.run_rules`. There is no Mongo fixture.
- **`make bypass`** calls Python directly, so it never tests the HTTP routes or `/compensate`. Add curls against :8080.
- **`test-conflict`:**
  - add (d), detector crash and resume
  - make (c) actually stop the detector
  - after a bulk run, assert that every proposal was refused
- **End-to-end script:** add one for the honest path. Open E1 and E3 for at least 30 s, approve, run-once, check CONFIRMED and that `/rules` is all PASS. Then suspend, compensate and check R6. Run it before every dry run.

## Suggested order

1. Run `make smoke setup seed bypass test-conflict rules` and fix whatever fails.
2. Fix Top 5 #1, #3 and #4.
3. Fix the banner "of N" (Top 5 #2) and add the proposal-status guard (bug 6).
4. Run the honest path end to end.

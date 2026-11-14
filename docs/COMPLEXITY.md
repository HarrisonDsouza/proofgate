# Time and space complexity, and what was fixed today

N = documents in a collection, W = detector window (200), E = events in a session, R = records, D = denials.

| Path | Before | Now | Where |
|---|---|---|---|
| Gate, after the transaction | one `update_one` on `gate_decisions` by unindexed `decision_id`: full collection scan, O(N) per call | removed (`txn_attempts` is already written inside the transaction) | `pg/gate.py:execute` |
| Confirm read-back | `target_records` lookup without `kind`: tenant-wide scan | uses `(tenant_id, kind, record_id)` index: O(log N) | `pg/gate.py:confirm` |
| Rule R7 grant lookup | unindexed `grant_id`: O(R x D) | index `(tenant_id, grant_id)` on `denials` | `pg/db.py` |
| Review-event hash chain | two concurrent heartbeats could read the same `prev` and **fork the chain** (R8 fails); `ts` not hashed | event is one transaction, so concurrent events conflict and retry; `ts` (ms) is in the hash. Proven with 12 concurrent threads against MongoDB (`tests/test_chain.py`) | `pg/review.py:_event` |
| Chain verification | boolean only | streams O(E) time, O(1) memory over the `(tenant_id, session_id, seq)` index; returns the first broken `seq` | `pg/rules.py`, `GET /api/verify/chain/{id}` |
| Telemetry | wrote to a collection that did not exist; never called | real Atlas time-series collection, 24 h TTL; gate latency and detector lag recorded; `/api/ops` does one `$group` with `$percentile` | `pg/db.py`, `pg/observability.py` |
| Attestation scoring | n/a | O(T + E) per attestation; corpus document frequencies cached 5 min per tenant, O(total evidence tokens) rebuild | `pg/attest_score.py`, `pg/voice.py` |

| Detector, per approval event | re-read 200 approvals and replayed CUSUM: O(W) per event | `check_streaming`: O(1) CUSUM work from a small `reviewer_stats` document (optimistic `ver` guard, safe with two detectors); rate and median stay index-bounded, O(log N + w). The streaming state is property-tested equal to the batch detector on 300 random sequences | `pg/detector.py`, `pg/cusum.py:SelfCusumState` |
| Detector after downtime | events written while no detector watched (first start, or oplog history lost) were never seen | clusterTime is read, then the gap is scanned, then the stream starts at that clusterTime; resume token otherwise; transient errors resume from the token; a poison event is skipped after 5 tries | `pg/detector.py:run` |
| Dwell credit | parallel heartbeats could each be credited the same gap (10 parallel = 10x credit); parallel evidence opens left several tokens accruing | compare-and-set on `last_hb_at`; unique partial index allows one open view token per session | `pg/review.py` |
| Suspension reopening | only CONFIRMED denials were reopened; one applied but not yet read back stood forever | AUTHORIZED denials whose grant is `used` are reopened too; `confirm()` after a suspension queues the compensation | `pg/gate.py` |
| Gate G1 | an executed proposal could be approved again and denied twice | G1 needs the proposal `approved` by THIS approval; `approve()` refuses finished proposals | `pg/checks.py`, `pg/review.py` |

| Gate reads | nine sequential reads per call (proposal, approval, case, policy, reviewer, reviewer_state, suspension, executor flag, window count) | ONE aggregation with `$lookup`s on the transaction's session (`gate.load_gate_inputs`); identical results (`tests/test_gate_inputs.py` compares it with the nine reads for normal, suspended, paused, missing-approval and missing-state cases). Measured on the Atlas M10 from a laptop: median gate call 1537 ms to 786 ms (12 calls each) | `pg/gate.py` |
| Bulk approve | a loop of `approve()`: about 15 round trips per proposal, measured 1.2 s each, about 61 s for 50 | `approve_bulk` is ONE transaction: batched reads, `insert_many`, one `bulk_write` of conditional proposal updates, one `reviewer_state` update, and the hash-chained events in one batch. Measured 1.9 s for 50 on Atlas. All-or-nothing; same documents as the loop (`tests/test_bulk_approve.py`) | `pg/review.py` |
| Floor-gaming | a reviewer who learned the floor and reviews at 31-37 s from their FIRST case passed every check and defeated the self-baselined CUSUM (the documented null result) | exact one-sided binomial test of how many of the last 30 approvals sit in `[floor, 1.25 x floor]` (H0: at most 25% do). Needs no honest-session data. Raises an examiner flag in `reviewer_flags`, NEVER a suspension (time alone cannot prove intent). Constant work per event: one indexed read of 30 documents | `pg/stats.py:floor_cluster`, `pg/detector.py` |

## Known and deliberately not changed
- The batch `detector.check_reviewer` replays the reviewer's whole history, O(N). It is only used at startup catch-up and as the test reference.
- `compensations (status, next_attempt_at)` does not lead with `tenant_id` because the worker is cross-tenant.
- Per-event rate check uses the `(tenant_id, reviewer_id, created_at)` index (IXSCAN, see `make explain`).
- `pg/target.py:compensate` checks `reopened_for` and then writes in two steps (not atomic under two compensation workers), and `/compensate` has no auth. That file is Harry's: reported, not changed.
- The replay guard compares `(created_at, approval_id)`: approvals tied on the same millisecond are handled by comparing against the maximum key at rebuild; an out-of-order event from a concurrent detector is skipped by the CAS retry, so under two detectors the CUSUM can miss one sample rather than double-count.

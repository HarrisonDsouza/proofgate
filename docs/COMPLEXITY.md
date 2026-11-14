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

## Known and deliberately not changed
- `detector.check_reviewer` re-reads up to W=200 approvals and replays the CUSUM on every event: O(W) per event, O(N x W) over a run. An incremental O(1) version (per-reviewer running state in its own document, never in `reviewer_state`, with an equivalence test against batch `SelfCusum`) is designed but **not built**; it is only worth shipping with the Hypothesis equivalence test.
- `compensations (status, next_attempt_at)` does not lead with `tenant_id` because the worker is cross-tenant.
- Per-event rate check uses the `(tenant_id, reviewer_id, created_at)` index (IXSCAN, see `make explain`).

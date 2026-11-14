# Security review (R4, dev-system:security-reviewer, 13:04 EST)

The reviewer is read-only, so the tech lead saved its report here.
**Verdict: FAIL.** This is a static, source-only review: nothing was run, so the exploits are not yet replayed against a live server.

**Root cause:** no endpoint has real authentication. The tenant, reviewer and supervisor are trust-me headers or body fields. Only `/api/gate/*` checks a key, and that key's default value is public.

## Must fix before the live demo

| # | Sev | Where | Problem | Smallest fix | Owner |
|---|---|---|---|---|---|
| 1 | Critical | `pg/target.py:43-69` | `POST /target/claim/{id}/compensate` has no auth, and `to_status` comes from the body. Any curl can set a claim to DENIED **without a grant**. `make bypass` doesn't test this route. | Delete the HTTP route: the worker calls `compensate()` directly (`detector.py:101`). If the route stays, require the key, look up the denial, and use `policy.effect.compensate_status`. | Harry |
| 2 | Critical | `pg/main.py:148-151`, `gate.py:199-213` | `POST /api/policies` has no auth and merges `rules` without validating them. `{"rules":{"baseline_only_existence":true}}` turns the gate off. A non-int value causes a 500 on every gate call. | Supervisor key; allow-list the keys with int types; reject `baseline_only_existence`; allow tightening only. | Sukhman (`gate.py`) + shared `main.py` |
| 3 | High | `pg/review.py:83-95` | Parallel heartbeats each credit the same gap (read, then an unconditional `$inc`): 20 parallel calls credit about 120 s for 6 s of real time. The examiner still shows `dwell_matches: true`. | Conditional `find_one_and_update` on `last_hb_at` + `closed_at: None`, credit 0 on a miss; ignore heartbeats under 1 s apart; clamp `active_ms <= open_ms`. | Sukhman |
| 4 | High | `review.py:58-61`, `main.py:52-54` | Exclusive focus applies per session, and sessions are free, so 50 sessions can accrue dwell at once. | Close open tokens per `reviewer_id` across sessions; cap open sessions per reviewer. | Sukhman |
| 5 | High | `main.py:52-54` + every tenant header | Anyone can start a session as any reviewer. G3 and G8 become decorative. Changing `X-Tenant-Id` reads another tenant's examiner, dashboard, rules and queue. | One `DEMO_REVIEWER_KEY` on `/api/sessions`; derive the tenant from the session document. Otherwise declare it as a known limit. | Sukhman + shared |
| 6 | High | `main.py:122-139, 154-156` | Suspensions, agent pause and run-once have no auth, and there is no unsuspend. One curl kills the demo seat. | Supervisor key on all of them; add a resume path or a one-command reseed. | shared `main.py` |
| 7 | High | `config.py:11`, `main.py:41-43` | The default agent key `dev-agent-key-change-me` is public, and the comparison is not constant-time. | Fail at startup if the key is the default or under 24 characters; use `secrets.compare_digest`; set a random key in the demo `.env`. | shared `config.py` |

## Next if time allows

| # | Sev | Where | Problem | Fix |
|---|---|---|---|---|
| 8 | Medium | `main.py:109`, `gate.py:122` | The `X-Debug-Pause-Ms` header with `DEMO_DEBUG_HOOKS=true` (the documented default) sleeps inside a transaction, so about 40 calls exhaust the threadpool. Separately, `int()` on a bad value causes a 500. | Remove the header (`test_conflict.py` calls Python directly) or clamp it to 5000 ms. Run the demo with hooks off. |
| 9 | Medium | `review.py:117-149` | `approve()` doesn't check `prop.status`, so an executed proposal can be re-approved and re-executed using the same dwell. | Conditional status update inside the transaction; consume views per approval. |
| 10 | Medium | `main.py` `body: dict` routes, `target.py:63` | Operator injection: `{"proposal_id":{"$ne":null}}`, or bulk with `[{"$ne":null}]`. | Pydantic models with `str` fields, `max_length`, and a bounded `list[str]`. |
| 11 | Medium | `/rules`, `/api/queue?limit`, bulk, run-once | Unbounded work. Concurrent `run-once` calls re-gate the same approval. | Cap `limit` and bulk at 100; add a simple rate limit; lock `run-once`. |
| 12 | Medium | `gate.py:69, 183-196` | Suspension compensates only CONFIRMED denials, so a denial that is applied but not yet confirmed escapes. | Include `AUTHORIZED`; make `confirm()` refuse if a newer suspension exists. |

## Low

- **`static/index.html:39,41`:** builds HTML with `innerHTML` from data fields. Escape them or use `textContent`.
- **Grant ids exposed:** the examiner and target_log show `grant_id` on an unauthenticated GET. The 60 s life keeps the window small.
- **`client_supplied_ignored`:** stores the whole request body uncapped. Store only a numeric `dwell_ms`.
- **Short ids:** session and approval ids have 32 bits (`token_hex(4)`).
- **Evidence:** served for any case in the tenant.
- **Headers:** no security headers and no CORS config. `/metrics` has no auth (no secrets leak).
- **Grants TTL:** the TTL of 7 days removes grant documents from the audit trail.
- **Error handling:** an unknown id causes a generic 500.
- **Atlas network access:** `0.0.0.0/0` is fine for the event only.

## Honest limits to say on stage

1. Reviewer identity is demo-grade (no SSO); in production the tenant and reviewer come from a verified token.
2. Dwell is a proxy for attention, not proof of reading.
3. The hash chain is unkeyed SHA-256.
4. The mock target shares a process and database with the gate.
5. Tenant isolation is query-level.
6. The data is synthetic, and no LLM is in the decision path.

## Not covered

Runtime behaviour, dependency advisories (unpinned `>=` ranges), git history, `ui/`, `simulate.py`, `calibrate_detector.py`, cusum and stats.

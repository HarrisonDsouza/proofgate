# Enforcement map: which line stops each attack

For the judge question "which line of code stops them?". Line numbers are for the `harry` branch at the time of writing; the function names are stable.

| Attempt | What stops it | Where |
|---|---|---|
| Agent calls the claims system with no grant, or a forged/used/expired one | `find_one_and_update` consumes the grant only if `status: issued`, unexpired, same tenant, record, audience and target status; otherwise 403 `NO_VALID_GRANT` plus a `target_log` row | `pg/target.py:20-39` (`apply`) |
| Browser sends its own `dwell_ms` | Ignored. Dwell is summed from server-credited views and the client value is stored under `client_supplied_ignored` | `pg/review.py:132-134` (`approve`) |
| Leave a tab open and walk away | A heartbeat is credited only if the tab is visible, there was input in the last 15 s, and the gap is ≤ 7 s | `pg/checks.py:15-24` (`credit_heartbeat`) |
| Approve without opening every cited item | G4 evidence coverage | `pg/checks.py:66-75` |
| Skim below the policy floor | G5 server-timed dwell ≥ `min_active_dwell_ms` from the active `review_policies` version (no threshold in code) | `pg/checks.py:76-82` |
| "Select all, approve 50" | Each approval goes through the gate one by one (`pg/review.py:152-155`); G6 rate refuses past the window limit and the gate suspends the reviewer in the same transaction | `pg/checks.py:84-88`, `pg/gate.py:96-171` |
| Suspended, expired or wrong-specialty reviewer | G2 not suspended, G3 credential and specialty | `pg/checks.py:46-63` |
| Approve your own proposal | G8 separation of duties | `pg/checks.py:95-99` |
| Stale proposal | G7 freshness | `pg/checks.py:90-93` |
| Race: approval and suspension at the same instant | One transaction (snapshot read, majority write) that always does a version-guarded write to `reviewer_state`; the loser retries and re-reads `suspended` | `pg/gate.py:112-129`, `pg/gate.py:171` |
| Grants already issued when a reviewer is suspended | Revoked, approvals sent back to review, executed denials queued for reopen, all inside the suspension transaction | `pg/gate.py:52-85` (`suspend_in_txn`) |
| Rubber-stamping spread over time | Change stream detector (rate, median, CUSUM) suspends the reviewer; resume token saved after every event so a restart misses nothing | `pg/detector.py:62-91` |
| Changing the rules quietly | New policy version supersedes the old in one transaction; every gate decision stores the version it used | `pg/gate.py:199-213` |
| Calling control routes without authority | `X-Console-Key` required on sessions, policies, suspensions, pause, run-once; agent routes need `AGENT_SERVICE_KEY`; the API refuses to start with weak keys | `pg/main.py` (`console_only`), `pg/config.py` (`key_problems`) |
| Undoing a denial over HTTP | No such route; compensation runs only in-process from a stored compensation document | `pg/target.py:66-68` |

## How to show it
- `make bypass`: agent calls without a grant get 403 and a `target_log` entry.
- `make test-conflict`: races (approval vs suspension, double spend, forged burst).
- `make rules`: R1-R8 invariants over stored state.
- Examiner page: any case rebuilt from Atlas, including every gate check.

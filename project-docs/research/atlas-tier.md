# Atlas tier research: transactions, change streams, indexes, and our code

Checked against official MongoDB docs and the installed PyMongo on 2026-11-14. Nothing below came from a live run against our cluster. The code was read only; no files were edited.

## What to do if the smoke test fails on our tier

First find out which tier you are on. Atlas UI → cluster card shows "Free", "Flex" or "M10". In Python, `client().admin.command("hello")` should return a `setName`; if it does, you are on a replica set.

| Smoke output | Most likely cause | Do this |
|---|---|---|
| `PASS transaction` then `FAIL change stream` | Usually a **race in the smoke test**, not the tier: the watcher thread opens the stream in the background and the insert happens after a fixed 1 s sleep (db.py:142-151). On a slow or throttled Free cluster, the stream may open after the insert. | Run `make smoke` again 2-3 times. If it passes even once, change streams work. Then apply fix S1 below. Only go to MongoDB staff if it fails every time *and* a traceback in the thread shows an `OperationFailure`. |
| Thread traceback that says `$changeStream ... is not allowed` / `OperationFailure` | The tier really does not allow change streams. Per the docs this should not happen on Free, Flex or M10. | Ask MongoDB staff for another tier. Meanwhile, the gate's inline G6 rate check still stops bursts without the detector (the PRD cut order allows this). |
| `Transaction numbers are only allowed on a replica set member or mongos` / `IllegalOperation` | You are connected to something that is not an Atlas replica set (e.g. a local standalone mongod). | Check `MONGODB_URI` in `.env` is the sandbox `mongodb+srv://` string. |
| `NetworkTimeout` / `ServerSelectionTimeoutError` | Network access list or URI problem, not the tier. | Add your IP in Atlas → Network Access; check the user and password in the URI. |
| `not authorized ... to execute command { collMod ... }` during `make setup` (second run) | The sandbox database user has only "read and write" rights. `collMod` needs the `dbAdmin` role (see section 4). | Ask staff for `dbAdmin` on our database, or drop and recreate the collections (first-run `create_collection` path), or skip the `collMod` branch. |
| Smoke passes but the demo crawls during "approve 50" | Free tier is throttled to **100 operations/s** (Flex: 500). One gate transaction is roughly 15 operations. | Expect ~1 s cooldowns on Free. Run the burst at a smaller N for rehearsals, or ask for Flex/M10. |

Important: `make smoke` **exits 0 even on `FAIL change stream`** (db.py:153 only prints). Read the output; do not trust the exit code.

---

## 1. Multi-document transactions on Free (M0) / Flex / M10

**Supported on all three.** Transactions need a replica set. Free clusters have "Replication Factor ... `3 Nodes`" and run MongoDB 8.0. Flex runs "at least MongoDB 8.0". M10+ are dedicated replica sets. None of the Atlas limits pages or the unsupported-commands page lists `startTransaction`, `commitTransaction` or `abortTransaction` as unsupported or limited on any tier.

| Limit | Free (M0) | Flex | M10 |
|---|---|---|---|
| Throughput throttle | **100 ops/s**. When exceeded, the network is throttled and there is a "one second cooldown period before resuming the cluster's operations on a given connection". Queued operations can wait more than 1 s. | **500 ops/s**, with a "sub-second cooldown" per connection | No ops/s throttle documented |
| Max transaction lifetime (`transactionLifetimeLimitSeconds`) | **60 s** default, cannot be changed (`setParameter` is unsupported; runtime options are M10+ only) | 60 s, cannot be changed | 60 s default; can be changed in Atlas → Additional Settings → "Set Transaction Lifetime" (minimum 1 s) |
| Lock wait inside a transaction (`maxTransactionLockRequestTimeoutMillis`) | 5 ms default (server default); not changeable | same | Changeable only through Atlas Support |
| Snapshot read concern in transactions | Supported (server feature: transactions accept `"snapshot"`, `"local"` and `"majority"`) | Supported | Supported |
| Max connections | 500 | 500 | Depends on tier |
| Aggregate `maxTimeMS` | Capped at 300 s (applies to `count_documents`, which is an aggregate) | same | none |

When a transaction runs longer than its lifetime, it "will be aborted by a periodic cleanup process". Our debug hook sleeps 3 s, so we are well within the limit.

Write conflicts: "If a transaction is in progress and a write outside the transaction modifies a document that an operation in the transaction later tries to modify, the transaction aborts because of a write conflict." A write that targets a document already locked by an in-progress transaction waits until that transaction ends. Two transactions that write the same document: the second gets `WriteConflict` (server code 112) with the `TransientTransactionError` label, and the driver retries it.

Sources:
- https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/ (version, 3 nodes, 100 ops/s, 500 connections)
- https://www.mongodb.com/docs/atlas/reference/flex-limitations/ (version, 500 ops/s, 500 connections)
- https://www.mongodb.com/docs/atlas/unsupported-commands/ (`setParameter` unsupported; aggregate `maxTimeMS` 300 s on Free/Flex; no transaction commands listed)
- https://www.mongodb.com/docs/atlas/cluster-additional-settings/ ("Set Transaction Lifetime", "default ... 60 seconds", mongod runtime options "on `M10+` dedicated clusters")
- https://www.mongodb.com/docs/manual/core/transactions-production-consideration/ (1-minute runtime, write conflicts, stale reads, Atlas restricts `setParameter`)
- https://www.mongodb.com/docs/manual/reference/parameters/ (`transactionLifetimeLimitSeconds`; `maxTransactionLockRequestTimeoutMillis` default 5 ms)
- https://www.mongodb.com/docs/manual/reference/read-concern-snapshot/ (snapshot read concern is available in multi-document transactions; its guarantees hold only with a majority-acknowledged commit)
- https://www.mongodb.com/docs/manual/core/transactions/ (collections can be created inside transactions unless the transaction is a cross-shard write; `countDocuments` works in transactions)

## 2. Change streams on Free / Flex

**Supported.** Change streams need a replica set or a sharded cluster running WiredTiger with protocol version 1, which all Atlas tiers are. The only Free/Flex-specific restriction: "you can use only strings and regular expressions in filters on database names (namespace `ns` fields) ... You can't use commands, such as `$in`, in database namespace filters. This limit doesn't apply to filtering on collection names." Our detector filters on `ns.coll` with a plain string (detector.py:25), so this restriction does not affect us.

- **Number of change streams:** no documented cap per tier. Each open stream holds one connection in a waiting `getMore`. The docs warn that if the number of open streams exceeds the connection pool size, notifications slow down. Free and Flex allow 500 connections in total.
- **Oplog window on Free/Flex:** not documented. The Atlas oplog-access page "applies to Atlas Infinite clusters and Atlas Core clusters"; setting oplog size or minimum oplog window is a dedicated-cluster setting (default 24 h retention on Core). On Free/Flex, assume the window is small and outside our control. **Do not rely on resuming after a long outage.** Within a demo (minutes), resume is fine.
- **Resume behaviour:**
  - `resumeAfter` needs the oplog to still contain the token's entry. It cannot resume after an invalidate event (for example a collection or database drop or rename); `startAfter` can.
  - Every event's `_id` is its resume token. `getMore` also returns `postBatchResumeToken`, a "highwatermark" token that moves forward even when no event matches.
  - PyMongo's `ChangeStream.resume_token` returns the latest token of either kind. On a resumable error, the driver automatically resumes once from it.
- **Throughput:** each `try_next()` is one `getMore` and counts toward the 100/500 ops/s limit.

Sources:
- https://www.mongodb.com/docs/manual/changeStreams/ (availability, connection pool note, resumeAfter/startAfter, resume tokens, highwatermark tokens)
- https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/ and https://www.mongodb.com/docs/atlas/reference/flex-limitations/ (namespace filter limit)
- https://www.mongodb.com/docs/atlas/reference/atlas-oplog/ (oplog page applies to Infinite and Core only)
- https://www.mongodb.com/docs/atlas/cluster-additional-settings/ (minimum oplog window; 24 h default on Core)

## 3. PyMongo `ClientSession.with_transaction` semantics

Verified in the installed driver (`.venv/.../pymongo/synchronous/client_session.py`, PyMongo **4.20.0**) and https://pymongo.readthedocs.io/en/stable/api/pymongo/client_session.html (4.20.0). Also https://www.mongodb.com/docs/manual/core/transactions-in-applications/.

1. Start a transaction with the given `read_concern` and `write_concern`, then run `callback(session)`.
2. If the callback raises **any** exception, the driver aborts the transaction. If the exception `isinstance(exc, PyMongoError)` and `exc.has_error_label("TransientTransactionError")`, and less than 120 s have passed, it **re-runs the whole callback**. Otherwise it re-raises the exception.
3. Commit:
   - `UnknownTransactionCommitResult` (and not a `MaxTimeMSExpired`): retry **only the commit**, without re-running the callback, until the result is known.
   - `TransientTransactionError` on commit: re-run the whole callback.
   - Anything else: re-raise.
4. **Backoff (new in recent 4.x, not mentioned on the docs page):** before each whole-transaction retry, the driver sleeps `random() * min(5 ms * 1.5^n, 500 ms)`.
5. **The 120 s timeout cannot be configured**, unless you use client-side operation timeout (`timeoutMS`). In 4.20, when the time runs out, the driver raises `NetworkTimeout` (or `ExecutionTimeout` with `timeoutMS`) carrying the last error's labels. **The caller then sees a `NetworkTimeout`, not our `VersionMoved` and not `OperationFailure`.**
6. The callback must be safe to run several times, and must not swallow command errors (the server will reject the commit with `NoSuchTransaction`).

**How a WriteConflict surfaces:** inside a transaction, the conflicting write (our `update_one` on `reviewer_state`) raises `pymongo.errors.OperationFailure` with `code == 112` (`WriteConflict`) and the `TransientTransactionError` label. `with_transaction` catches it, aborts and re-runs the callback. Our code never sees it unless the 120 s budget runs out.

**Is raising a custom exception with the `TransientTransactionError` label right when the version-guarded update matches 0 documents?** It works: the driver retries any `PyMongoError` that has the label. Two caveats:
- `_add_error_label` is private API. The public way is the constructor: `super().__init__("reviewer_state version moved", error_labels=["TransientTransactionError"])`.
- Under snapshot isolation this branch is close to unreachable. If another transaction committed a change to the document after our snapshot, the `update_one` itself raises `WriteConflict` before `matched_count` can be 0. Keep it as belt and braces; it is harmless.

The documented alternative avoids stale reads by taking the write lock first, with `findOneAndUpdate` as the first operation (production-considerations page, "In-progress Transactions and Stale Reads"). **Do not switch to it today**: it reverses who loses the conflict, so `eval/test_conflict.py` test (a) would see an ALLOW instead of a G2 REFUSE.

## 4. Partial unique indexes, TTL indexes, `$jsonSchema` on these tiers

- **No tier-specific restriction is documented** for partial, unique, TTL indexes or `$jsonSchema` validators on Free, Flex or M10. `createIndexes` and `collMod` are not listed as unsupported. The only index-related tier limit: Free and Flex don't support *rolling* index builds, which we don't use.
- **TTL indexes** (server rules):
  - Single-field only; on a compound index `expireAfterSeconds` is ignored.
  - Not on `_id`.
  - Deletion runs in the background and starts "0 to 60 seconds" after expiry.
  - Only the primary deletes.
  - To change `expireAfterSeconds`, use `collMod`; `createIndex` cannot change it.
  - Our `view_tokens.expire_at` and `grants.ttl_at` indexes satisfy these rules. They are single-field, so they cannot lead with `tenant_id`; that is acceptable under engineering rule 2, which is about compound indexes.
  - TTL deletes produce `delete` change events. Our detector filters to inserts, so they are ignored.
- **Partial unique indexes:** the unique constraint applies only to documents that match the filter, so duplicates outside the filter are allowed.
  - A partial index can't also be `sparse`, can't be an `_id` index, and can't be a shard-key index.
  - A query uses the partial index only if its predicate implies the filter.
  - `one_active_policy` and `one_active_suspension` comply.
  - In `new_policy_version`, the order inside the transaction (supersede first, then insert the new active version) is correct.
- **`$jsonSchema` validators:**
  - Not allowed on collections in `admin`, `local` or `config`, or on system collections.
  - Validators can't use `$near`, `$nearSphere`, `$text`, `$where`, or `$expr` with `$function`.
  - We use none of these.
- **Permission gotcha (not a tier limit):** `collMod` requires the `collMod` action, which `dbAdmin` provides. The built-in `readWrite` role, and Atlas's "Read and write to any database" (`readWriteAnyDatabase`), **do not include `collMod`**; they do include `createCollection`, `createIndex` and `changeStream`. So `make setup` may fail on its **second** run (db.py:117-118) if the sandbox user is not Atlas admin.

Sources:
- https://www.mongodb.com/docs/manual/core/index-ttl/
- https://www.mongodb.com/docs/manual/core/index-partial/
- https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema/
- https://www.mongodb.com/docs/manual/core/schema-validation/specify-query-expression-rules/
- https://www.mongodb.com/docs/manual/reference/command/collMod/ (Access Control)
- https://www.mongodb.com/docs/manual/reference/built-in-roles/ (`readWrite` actions)
- https://www.mongodb.com/docs/atlas/unsupported-commands/

## 5. Our code against these facts

### What is already right
- **`session=s` on every operation inside each transaction.** I checked every call:
  - `_audit` gate.py:41; `active_policy` :46
  - `suspend_in_txn` :56, 58, 60, 62, 65, 69, 71, 79, 83
  - `execute` body :103-118, 126, 139, 145, 150, 151, 156, 157, 162, 164, 165
  - `new_policy_version` :204, 205, 209
  - `target.apply` target.py:21, 26, 29, 33

  None is missing. Running other operations while iterating the `denials` cursor in the same session (gate.py:69-76) is allowed (single thread, one session).
- `execute` (gate.py:171) and `suspend` (gate.py:91-93) use `ReadConcern("snapshot")` with `WriteConcern("majority")`.
- `count_documents` inside the transaction (gate.py:117) is supported.
- The conflict design is sound. Gate and suspension both write `reviewer_state`. A suspension that commits during a gate's 3 s debug pause makes the gate's guarded `update_one` raise `WriteConflict`. The callback is re-run, re-reads `suspended`, and refuses. `txn_attempts` counts callback runs; a commit-only retry does not re-run the callback, so the count stays correct.
- `detector.run` saves `cs.resume_token` after each handled event, and reads it back as `resume_after` on startup. That is at-least-once processing. `handle` is effectively idempotent: it returns early if an active suspension exists, `suspend_in_txn` reuses an existing suspension, and the partial unique index blocks a second active one.

### Concrete problems (file:line → fix)

**Smoke test (db.py `smoke`): it does not fully prove what the 12:40 checkpoint needs.**

- **S1. Race, can give a false FAIL.** db.py:142-151: the stream is opened inside the thread, and the insert happens after a fixed `time.sleep(1.0)`. If opening the stream takes more than 1 s (TLS, Free-tier throttling), the insert is missed. Fix: open the stream in the main thread first (`cs = db.smoke.watch()` runs the aggregate synchronously, so the stream is positioned), then insert, then poll `cs.try_next()` for up to 10 s. No thread is needed.
- **S2. Exit code is always 0.** db.py:153 only prints FAIL. If the thread raises (e.g. `OperationFailure`), the traceback is printed by the thread and the main thread still prints FAIL and exits 0. Fix: `sys.exit(1)` on any FAIL, and re-raise thread errors (S1's fix removes the thread).
- **S3. Does not test the transaction settings the gate uses.** db.py:137 calls `with_transaction` with no read/write concern. Fix: pass `read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority")`, the same as gate.py:171.
- **S4. Does not prove atomicity or retry.** "2 docs present" only shows that inserts work. Fix:
  - add an abort case: the callback inserts and then raises `ValueError` → assert count unchanged;
  - add a conflict case: two sessions `$inc` the same doc inside transactions → the second raises an `OperationFailure` with code 112 (`WriteConflict`) and the `TransientTransactionError` label.

  `make test-conflict` covers the conflict case end to end, but only after seeding.
- **S5. Does not test what the detector actually uses.** The detector uses a database-level stream (`db.watch`) with a `$match` on `ns.coll`, plus `resume_after`. The smoke test uses a collection-level stream. Fix: in smoke, use `db.watch([{"$match": {"ns.coll": "smoke"}}])`. Save `cs.resume_token`, close, insert one more doc, reopen with `resume_after=token`, and assert that doc arrives. That proves resume on this tier.
- **S6. Minor.** db.py:135 drops `smoke`, then the transaction implicitly re-creates it. That is allowed on a replica set, but a "catalog changed" transient error right after a drop is possible. `with_transaction` retries it. Better: `create_collection("smoke")` before the transaction.

**Detector (pg/detector.py).**

- **D1. Any exception silently kills the detector.** detector.py:84-92 has no try/except, and in the API process it runs in a daemon thread (detector.py:119), so nothing notices. Things that can raise:
  - `gate.active_policy` → `LookupError` (detector.py:68)
  - `KeyError` on `change["fullDocument"]`
  - a non-resumable `try_next` error, including `ChangeStreamHistoryLost` (code 286) when the saved token has fallen off the small Free/Flex oplog

  Fix: wrap the body in an outer `while not stop.is_set()` loop with `try/except PyMongoError/Exception`: log the error, sleep 1-2 s, and reopen from the saved token. On `OperationFailure` code 286, clear `resume_token` and reopen without it. Also scan approvals created since `last_event_at` so nothing is missed.
- **D2. Token not saved while idle.** detector.py:86-89: when `try_next()` returns `None`, `cs.resume_token` still advances (highwatermark token), but it is never saved. After a restart, the stream must resume from the last *approval*, which on a busy database (heartbeats, review_events) may already be out of the oplog. Fix: in the `None` branch, save `cs.resume_token` when it changed, throttled to about every 5 s to stay inside the ops/s limit.
- **D3. Invalidated stream spins forever.** After an invalidate event (database dropped), PyMongo marks the stream closed, and `try_next()` returns `None` forever. The loop at detector.py:85-89 then spins silently. Fix: `if not cs.alive: break` and reopen (inside D1's outer loop). Use `start_after=` instead of `resume_after=` (detector.py:83) so a token from before an invalidate still works.
- **D4. Possibly two detectors at once.** `make detector` runs a separate process (Makefile:12 sets `RUN_BACKGROUND=0` for that process only). If `make dev` is also running with the default `RUN_BACKGROUND=1`, two detectors share `STATE_ID` and both act on every event. The partial unique index and the `reviewer_state` conflict keep this correct, but it causes duplicate work and confusing logs. Fix: start the API with `RUN_BACKGROUND=0` during the kill/restart demo.
- **D5. Nit.** detector.py:81: `full_document="updateLookup"` does nothing for insert events (inserts always carry `fullDocument`). Harmless. `detector_state` has no `tenant_id` (rule 2); it is global by design, so mention that if a judge asks.

**Gate and transactions (pg/gate.py, pg/target.py).**

- **G1. Private API, and unclear failure after 120 s.** gate.py:25-33: `VersionMoved` works with PyMongo 4.20 but uses the private `_add_error_label`. Fix: `super().__init__("reviewer_state version moved", error_labels=["TransientTransactionError"])`. Also, after 120 s of retries, PyMongo 4.20 raises `NetworkTimeout`, not `VersionMoved`. main.py has no handler for `PyMongoError` (the only exception handler is for `review.NotFound`, main.py:46), so `/api/gate/execute` would return a 500. Fix: catch `PyMongoError` in `gate_execute` and return 503 `{"error": "GATE_BUSY_RETRY"}`. The client must not treat it as ALLOW.
- **G2. Missing `reviewer_state` breaks the conflict guarantee.** gate.py:58: `suspend_in_txn` updates `reviewer_state` without `upsert`. If the document is missing, the suspension creates no write conflict and `suspended` is never set. The gate still fails closed (gate.py:113-114), but serialization depends on the seed. Fix: `upsert=True`, plus `$setOnInsert: {"tenant_id": tenant, "reviewer_id": reviewer_id}` and `version` handled via `$inc`.
- **G3. Not snapshot + majority everywhere.** gate.py:213 (`new_policy_version`) and target.py:37 (`apply`, the grant consumption) call `with_transaction` with no read/write concern. They inherit the client defaults (read concern `local`; write concern is majority by default on Atlas 5.0+ but not set explicitly). This does not match engineering rule 4 or what we will tell judges. Fix: pass `read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority")` to both. Simpler: one helper `txn(fn)` in db.py that every caller uses, or `start_session(default_transaction_options=TransactionOptions(read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority")))`.
- **G4. Redundant post-commit write without `tenant_id`.** gate.py:173: the `update_one` runs after commit, outside the session, and its filter has no `tenant_id` (rule 2). It is redundant, because `gd["txn_attempts"]` (gate.py:133) is already the final attempt count: commit-only retries don't re-run the callback. Fix: delete the line, or add `"tenant_id": tenant` to the filter.
- **G5. Grant consumed even when no record was updated.** target.py:29-32: if `target_records.update_one` matches 0 documents, the grant is still marked `used` and the log says `APPLIED`. Fix: check `matched_count`; if it is 0, raise `LookupError` so the transaction aborts and the route returns 404/403.
- **G6. Compensation is not atomic.** target.py:49-56: `compensate` checks `reopened_for` and then updates, without a transaction. It also opens sessions it never uses for a transaction (target.py:50, 55), and the update and the log write are separate operations. Fix: one guarded update, `update_one({"_id": rec["_id"], "reopened_for": {"$ne": denial_id}}, ...)`; treat `modified_count == 0` as NOOP_IDEMPOTENT. Optionally put the log write in the same transaction.
- **G7. Free-tier throughput will slow the burst demo.** One `execute` is about 15 server operations: 8 reads, the count, the guarded update, 2-4 inserts or updates, the audit write, the commit, and the post-commit update. An "approve 50" burst is roughly 750 operations, plus detector `getMore` calls and compensation polling. On Free (100 ops/s) expect several seconds with 1 s cooldowns per connection. On Flex it is about 5× better. This is not a correctness problem: the 60 s lifetime applies to each transaction, and each transaction is short.
- **G8. Note on the debug hook.** gate.py:122-123: `debug_pause_ms` sleeps inside an open transaction. Keep it far below the fixed 60 s lifetime on Free/Flex. The current value of 3000 ms is fine.

# MongoDB in ProofGate: how and why

Plain-language guide for the team. Use it to answer "why MongoDB?" at the table.

## The one-sentence version

**MongoDB Atlas is ProofGate's identity, policy and audit layer.**
- Every reviewer, policy, approval, decision, grant and audit entry lives there.
- One Atlas transaction decides whether a denial may run.
- Atlas's live change feed catches rubber-stampers mid-run.

That is word for word what Statement One asks for: "collections, schema validation, change streams".

## Quick vocabulary

| Term | Plain meaning |
|---|---|
| **Atlas** | MongoDB's cloud service. We must use the hackathon **sandbox** project. |
| **Database / collection / document** | Database = `proofgate`. Collection ≈ a table. Document ≈ a row, stored as JSON, which can hold nested lists. |
| **Index** | A sorted lookup that makes a query fast, and can enforce "only one of these". |
| **Transaction** | A group of reads and writes that all succeed together or none happen. |
| **Write conflict** | Two transactions try to change the same document at once; MongoDB makes one retry. |
| **Change stream** | A live feed of changes to a collection that a program can subscribe to. |
| **Resume token** | A bookmark in that feed, so a restarted program carries on where it left off. |
| **`$jsonSchema` validator** | Rules a document must meet before MongoDB will store it. |
| **TTL index** | Deletes documents automatically after a time. |
| **Aggregation pipeline** | A multi-step query (filter → join → group) run inside the database. |

## Feature by feature: what we use, where, and why

### 1. Collections as the system of record
- About 20 collections (PRD §7): `cases`, `proposals`, `reviewers`, `view_tokens`, `review_events`, `approvals`, `review_policies`, `reviewer_state`, `gate_decisions`, `denials`, `grants`, `suspensions`, `compensations`, `target_records`, `target_log`, `audit` and more.
- **Why documents fit:** a claim and its 2-4 evidence items (each with a SHA-256 hash) are naturally one document. A policy's rules and effect are one nested object we can version as a whole.

### 2. Schema validation (`$jsonSchema`)
- Every key collection rejects documents missing required fields. For example, an approval with no `tenant_id` or no `evidence_hashes_viewed` fails with "Document failed validation".
- Validators check **shape only**. Thresholds live in the policy document, so compliance can change them without a deploy.
- **Demo line:** `py/db/demo_invalid_insert.py` shows a bad insert being refused by the database itself.

### 3. Multi-document transactions: the gate
- `POST /api/gate/execute` runs **one** transaction with snapshot read concern and majority write concern.
  - It reads the approval, proposal, case, active policy, reviewer, `reviewer_state` and suspensions.
  - It checks rules G1-G8.
  - It writes the decision, denial, grant and audit, or the refusal and requeue.
- **Why it matters:** if anything fails, nothing is written. There is never a grant without a decision, or a denial without an audit entry.
- **The clever part, the write conflict:**
  - Every gate call, approval and suspension for a reviewer also writes that reviewer's single `reviewer_state` document.
  - If a suspension lands while an approval is in flight, MongoDB raises a write conflict. The driver retries, and the retry sees `suspended: true` and refuses.
  - We store `txn_attempts`, so you can see it happened. `make test-conflict` proves it.
- The mock claims system also uses a transaction: consume the grant + change the record + log, all together.

### 4. Change streams with a stored resume token: the detector
- A separate process watches new `approvals` live. If a reviewer approves too fast, or their median review time is too low, it runs the suspension transaction:
  - suspend the reviewer
  - revoke their grants
  - send pending approvals back to review
  - create compensations for denials already executed
- After every event it saves the **resume token** in `detector_state`. Kill it mid-burst and restart it: it continues from the bookmark and misses nothing. It ends with exactly one suspension, thanks to a partial unique index.

### 5. Indexes that enforce rules, not just speed
- **Partial unique index:** only one `active` policy per tenant and action type.
- **Partial unique index:** only one active suspension per reviewer.
- **Unique `denials.approval_id`:** an approval can authorise at most one denial.
- **Unique `compensations.denial_id`:** a denial is reopened at most once (idempotent).
- **Compound indexes lead with `tenant_id`:** fast per-tenant queries, and one insurer's data never mixes with another's. `make explain` shows the IXSCAN (index scan) plan.
- **TTL indexes** clean up `view_tokens` and old `grants`. Code still checks expiry itself, because TTL deletion runs only about once a minute.

### 6. Aggregation for the rules check
- Rules R1-R8 (`make rules`) are queries over stored state. For example: "every CONFIRMED denial has exactly one matching approval", "no claim is DENIED without a consumed grant" (no bypass).
- This lets an examiner audit from the database alone.

### 7. Optional: Vector Search with automated embeddings (S7, probably cut)
- The agent could find the 3 most relevant made-up policy clauses for a case by meaning, with Atlas embedding the text automatically (Voyage models).
- It is cut early because it doesn't strengthen the core proof.

### 8. Developer tooling
- **MongoDB Agent Skills** and the **MongoDB MCP Server** (read-only) in Claude Code, as the organisers recommend. They let the AI assistant inspect our real collections while we build.

## Why MongoDB and not something else?

1. **The event requires Atlas,** and Statement One names exactly the features we use.
2. **Transactions and change streams in the same database** as the data. No separate queue or event bus to keep in sync, so suspension and enforcement can't drift apart.
3. **The document model fits** cases with nested evidence, policies with nested rules, and audit records with variable references.
4. **Validators, partial unique indexes and TTL** give database-level guarantees: no second active policy, no second active suspension, no double reopen.

## How this answers Statement One

| Question | MongoDB features doing the work |
|---|---|
| Enforce before the action | Transaction (gate) + `reviewer_state` write conflict + grants consumed in a transaction |
| Record what, why, whose authority | Collections + `$jsonSchema` + audit (hash chain if S3 ships) + aggregation rules R1-R8 |
| Stop or roll back mid-run | Change stream + resume token + suspension transaction + idempotent compensations (unique index) |

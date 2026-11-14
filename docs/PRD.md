# ProofGate: Build PRD
**Statement One: Agents You Can Audit.** A claim denial runs only if MongoDB Atlas holds proof that a qualified human reviewed that specific case.

Team: A = Python, B = Spring Boot, C = Angular. Build window 11:45 to 16:45. Hacking officially ends at 17:00, so the 15 minutes after 16:45 are buffer.

Conventions used throughout:
- **[VERIFY]** marks a figure or claim to check before you say it on stage.
- **[UNVERIFIED]** marks a setup step that the research file could not confirm. Everything else in Section 9 is copied from the verified setup research.
- **[NOT IN RESEARCH]** marks a standard tool command that the research did not cover.
- **Never put a number in the README, video or pitch unless `make eval` or a stored-state query produced it.** Every result slot below is a blank `[fill from make eval]`.

---

## 1. Pitch, user, failure, evidence, why unsolved

**One-line pitch:** "An agent can queue thousands of claim denials an hour. ProofGate lets a denial execute only if Atlas holds per-case proof that a credentialed reviewer opened every piece of evidence the agent cited and spent real time on it, timed by the server. A batch of 50 rubber-stamps executes 0."

**Named user (buyer):** the insurer's Chief Compliance Officer or General Counsel. They carry the class-action and regulator exposure.

**Operator:** the medical director whose agent queues denials for physician sign-off.

**Secondary user:** the state insurance examiner who has to rebuild whether case #X was really reviewed.

**Costly failure: the PxDx pattern as reported** [VERIFY all figures]
- ProPublica and The Capitol Forum (2023) reviewed internal Cigna records. They showed more than 300,000 claims denied over two months in 2022, at about 1.2 seconds of physician review per claim.
- A former Cigna physician said: "We literally click and submit... It takes all of 10 seconds to do 50 at a time."
- A class action followed in the Eastern District of California. Per ProPublica, the California Department of Insurance was coordinating with other state regulators.
- **Always add:** Cigna disputes the report, says PxDx is not AI, and says these denials are under 1% of claims.
- Related: a lawsuit alleges UnitedHealth's nH Predict denials were reversed on appeal more than 90% of the time. That is the plaintiffs' allegation, not a finding. A Minnesota federal judge let the claims proceed.
- Sources:
  - https://www.propublica.org/article/cigna-pxdx-medical-health-insurance-rejection-claims
  - https://www.healthcaredive.com/news/cigna-lawsuit-algorithm-claims-denials-california/688857
  - https://www.beckerspayer.com/payer/home-page/cigna-sued-following-propublica-report-on-unreviewed-batches-of-denied-claims.html
  - https://www.healthcaredive.com/news/unitedhealth-algorithm-lawsuit-care-denials/699834/
  - https://www.govinfosecurity.com/court-unitedhealth-must-answer-for-ai-based-claim-denials-a-27534

**Supporting evidence: agents act without an enforced external policy check** [VERIFY]
- **Summer Yue (Meta), Feb 23, 2026.** Her OpenClaw agent deleted more than 200 Gmail emails. She told it to stop from her phone and it kept going. Several outlets blame context compaction dropping her safety instruction, but she herself had not worked out the cause. OECD.AI lists it as an incident.
  - https://www.windowscentral.com/artificial-intelligence/meta-summer-yue-director-openclaw-ai-email-deletion
  - https://oecd.ai/en/incidents/2026-02-23-d55b
- **Replit, July 2025.** During Jason Lemkin's experiment, the agent deleted his production database despite an explicit freeze instruction. Lemkin said it "hid and lied about" the deletion. Reports of how many records were lost disagree.
  - https://www.eweek.com/news/replit-ai-coding-assistant-failure/
  - https://incidentdatabase.ai/reports/5593/
- **Lesson:** policy that lives in the prompt is not enforcement, and agents report effects that never happened. ProofGate enforces outside the model and reads every effect back from the target system.

**Supporting evidence: regulators expect reconstruction, and output logs do not provide it** [VERIFY]
- FINRA's 2026 Annual Regulatory Oversight Report (Dec 9, 2025) names two agent risks: acting beyond the user's intended authority, and multi-step decisions that are hard to trace.
- Snell & Wilmer argues that output logs cannot support reconstruction. That is the law firm's view, not a FINRA mandate.
- Sources:
  - https://swlaw.com/publication/finras-2026-oversight-report-signals-a-supervisory-reckoning-for-autonomous-ai
  - https://www.debevoise.com/insights/publications/2025/12/finras-2026-regulatory-oversight-report-continued
- State laws require individual clinician review of denials: California SB 1120 and Arizona HB 2175 [VERIFY bill numbers and scope before stage].

**Why it is not solved today:**
- Approval tooling (maker-checker, workflow engines, the approve button in claims systems) records that an approver ID clicked approve.
- It does not record what the approver saw, whether they opened the evidence, or for how long.
- It allows bulk-approve.
- Nothing enforces, before the adverse action runs, that a qualified human reviewed this case with its evidence.
- Agents make it worse: they produce denials faster than humans can review, so human-in-the-loop becomes a click-through.
- Agent audit logs record the API call. They do not record the authority behind it or the per-case review evidence.

## 2. Originality

| Nearest thing found | What it does | Specific difference |
|---|---|---|
| "Stop Pressing 1: Measuring Human Rubber-Stamping in Agent Oversight" (DEF CON 34 AI Village poster). https://aivillage.org/posters/stop-pressing-1-measuring-human-rubber-stamping-in-agent-oversight/ | Measures oversight quality by having operators predict the agent's action. | Research poster. It blocks nothing, stores no per-case evidence and has no domain. ProofGate enforces before the action. |
| Corporate Compliance Insights, "human in the loop just another rubber stamp" | Recommends minimum dwell times and logging whether reviewers open evidence. | A recommendation only, no system. ProofGate implements it as a transactional gate. |
| agent-approval-gate (Indie Hackers); Agno and Gravitee HITL; Airia approval checkpoints | Bind an approval to the payload and keep an audit trail; Airia markets "proof of human oversight". | They check that an approval exists. None was found that gates on what was viewed, for how long, by whom, or that suspends a reviewer mid-run. |
| Past hackathon approval projects: RunwayOps, LabRat, Aegis, Proofline | Generic approval gate, or a hash-chained audit log. | Approval existence only. No proof of review, no behavioural revocation, no compensation. |
| UM vendors (Cohere Health, InterQual, Availity, Enlyte) | Route cases to a medical director; track time per case as a productivity metric. | No evidence was found that any of them blocks a denial on view or dwell data. Caveat: only 4 searches, so internal logging cannot be ruled out. |

**If a judge says "this exists," say:**
> "Approval gates check that someone clicked approve. We check that the approval is real, per case, before execution: the server timed the reviewer on every evidence item the agent cited, the credential was valid and matched the claim's specialty, and the reviewer isn't stamping in bulk. All of that is checked in one Atlas transaction that also writes a per-reviewer document, so a suspension aborts a denial that is in flight. Then we compensate denials already executed. In four searches we found none that combine those. That means none found, not proven new."

Also say clearly: **the tool blocks denials that lack real review. It does not generate paperwork for regulators.**

## 3. Official statement and its three questions

**Statement One, Agents You Can Audit.** Atlas is the identity, policy and audit layer, using collections, `$jsonSchema`, transactions and change streams.

| Question | Our answer | Requirement ids |
|---|---|---|
| Q1. How do you decide what an agent may do and enforce it before the action? | Authority to execute an adverse action belongs to the pairing of the agent and a per-case human approval, never to the agent alone. A versioned `review_policies` document holds the conditions: dwell floor, per-item floor, evidence coverage, rate window, credential rules and separation of duties. The gate evaluates them in one transaction that also writes `reviewer_state`, then mints a short-lived single-use grant. The target system refuses any call without a valid grant, with 403. | M5, M6, M7, M8, S1 |
| Q2. How do you record what the agent did, why, and under whose authority? | Each denial links to: agent_id and model version; the rationale and cited evidence hashes; reviewer identity and a credential snapshot; server-timed views per evidence item; the policy id and version; the gate_decision with every rule result and the transaction attempt count; the grant; and the target read-back. The examiner page rebuilds the case. Rules R1-R8 run over stored state. A hash chain detects edits. | M4, M9, M13, M14, S3 |
| Q3. How do you stop or roll back an agent mid-run? | Stop: the gate's inline rate check, the change-stream detector, or the supervisor halt writes a suspension in a transaction. That transaction bumps `reviewer_state` (so in-flight gate transactions conflict and re-evaluate), revokes issued grants and requeues pending proposals. Roll back: idempotent "reopen" compensations keyed on denial_id hit the claims system, are read back and linked to the original denial. R6 proves completeness. | M10, M11, M14 |

## 4. Judge must-fix items: how each is answered

| Judge | Must-fix | Answer in this build | FR |
|---|---|---|---|
| Robert Maissan | One transaction; per-reviewer document; server dwell; schema for presence only; resume token; one script with seeded reviewers, R1-R6, suspension counts, and an injected mid-transaction suspension | The gate transaction reads policy, approval and `reviewer_state`, then writes `reviewer_state` (version guard), denial, grant and audit. Dwell comes from view tokens and heartbeats. Validators check presence and type only. `detector_state` holds the resume token. `make eval` runs the seeded workload; `make test-conflict` injects the suspension. | M4, M7, M10, M14, M15, M16 |
| Raschid Jimenez | Gate is the safety mechanism and is generic; show live floor edit; second adverse action via a new policy document only | The supervisor page edits the floor, creating policy v(n+1). The next gate call reads the new active version in the transaction. `account_freeze` runs through the same gate with only a new policy document plus seed records. | M6, M7, S1 |
| Tapan Shah | Write conflict with retry; persisted resume token and a live kill; server dwell; compound indexes with an IXSCAN explain | `withTransaction` retries on TransientTransactionError and the attempt count is stored. The detector runs as a separate process, killed and restarted live. Indexes lead with `tenant_id`. `make explain` prints the winning plan. | M7, M10, M1, S8 |
| Leo Gomes | Synchronous checks; server dwell rejecting curl-forged values; reopen mutates the target with read-back; resume token; pre-recorded fallback | `dwell_ms` in a request body is ignored and logged. Compensations call the target and read it back. Fallback video is recorded at 15:30. | M5, M7, M11, M17 |
| Aasawari Sahasrabuddhe | Short-lived grant bound to case, policy and tenant; service identity alone gets 403; suspension revokes issued grants; curl bypass shown | `grants` documents have a 60 s expiry, are single use, and carry audience `target:claim`, case, tenant, policy version and reviewer. The target consumes the grant atomically. The suspension transaction revokes grants. `make bypass` shows the 403, and the examiner shows the refusal. | M7, M8, M10 |
| Sergey Strelnikov | Hard checks in the transaction; second line of defence; one command with honest, stamper and idler reviewers, R1-R6 and suspension counts; versioned thresholds stamped on suspensions | As above. `suspensions.policy_version` is required by the validator. | M10, M15 |
| Anamika Ahmed | Per-reviewer write document; server dwell; gate rejects hashes never served to the session; resume token; idempotent compensation keyed on denial_id | Coverage is computed from view tokens served to that session. `compensations.denial_id` has a unique index and the target is idempotent per denial_id. | M4, M7, M10, M11 |
| Pablo Vallejo | Real, verifiable rollback; R6; examiner flags an idle tab; failure halfway through compensation | The compensation worker retries with backoff and stays `pending` until read-back confirms. R6 fails while anything is pending. The examiner shows open time against active time and flags idleness. | M11, M13, M14 |
| Amrit Krishnan | `make eval`, about 20+ held-out sessions in three groups, per-group error rates, thresholds with rationale, sweep | Pre-registration is committed before the first run, and the reported run uses a held-out seed. Groups: honest, fast-honest, stamper, tab-idler, skimmer, heartbeat-forger. `make sweep`. | M15, S4 |
| Vatsal Shah | Deterministic, synchronous refusal; seeded demo state; reset script; fallback recording | `make reset`; fallback video. | M7, M17 |
| Parth Patel | Detector off plus forged curl gives 0; tab-idle gamer refused | `make burst-forged` runs with the detector stopped. The idler is in the eval and in the live demo. | M5, M7, M15 |
| Ahmed Radwan | Held-out eval; show a null result (a gamer who passes) | The heartbeat-forger group is expected to pass the gate. It is shown on stage as the known limit. | M15 |
| Pahul Hallan | Hash-chain review_events and audit; insert-only role; examiner verifies the chain; cut LLM before these | Per-session and per-case SHA-256 chains, with verification in the examiner. Insert-only role is COULD. The LLM is cut before the chain. | S3, C1 |
| Noel Kirthiraj | Say who pays; build the synchronous gate and the 0-of-50 moment first | Buyer is the CCO or General Counsel (Section 14). The hour plan builds the gate and the burst first. | M7, M12 |
| Rudraksh Monga | `tenant_id` required and leading every index; per-tenant policy; per-tenant `reviewer_state`; second payer keeps executing | `reviewer_state._id = "<tenant>\|<reviewer>"`. Tenant B demo. | M1, S2 |
| Aasheesh Singh | Policy engine; second action with no code change; held-out false-suspension rate | S1 and M15. | S1, M15 |

## 5. Scope

**Goals**
1. A gate that refuses adverse actions without per-case, server-timed, evidence-covering, credentialed, non-bulk human review. Its correctness rests on transactions, not on the timing of the change stream.
2. Behavioural mid-run suspension with grant revocation, requeue, and verified compensation.
3. Examiner reconstruction from stored state, with rules R1-R8.
4. An honest held-out evaluation that reports both error types and the null result.

**Non-goals**
- Real PHI, real CPT text, or medical correctness of the triage. CPT descriptors are AMA-copyrighted, so use only public-domain ICD-10-CM and HCPCS Level II descriptions plus a made-up policy.
- Real authentication or SSO. Demo login picks a reviewer, and this is disclosed.
- Production key management.
- Voice.
- Mobile.
- Any claim of clinical validity.
- Proving a human "really read" anything. We prove server-observed behaviour, and say so.

## 6. Functional requirements

**The MUST items alone make the complete demo.**

### MUST
- **M1. DB setup.** `py/db/setup_db.py` creates every collection in Section 7 with validators (`validationAction: error`), all indexes, and TTLs. It is idempotent.
- **M2. Seed.** `py/seed/generate.py --seed 20261114` creates deterministic data (Section 10).
- **M3. Triage agent, rules-based.** Python, `agent_id = triage-agent-v1`. For each pending case it writes a proposal with `recommendation` (deny or pay), `rationale`, `cited_evidence: [{evidence_id, hash}]` and `cited_clauses`. Deterministic code checks that every cited id exists in the case before inserting.
- **M4. Server-timed views.**
  - A reviewer session is issued by `POST /api/sessions`.
  - Fetching an evidence item creates a `view_tokens` document and closes any other open token for that session (exclusive focus).
  - The browser sends a heartbeat every 5 s only while the tab is visible and there was input in the last 15 s.
  - The server adds `min(now - last_hb_at, 7000)` to `active_ms` only if the gap is 7 s or less. Otherwise it adds 0 and the time counts as idle.
  - Every open, heartbeat and close appends a `review_events` document.
- **M5. Approvals.**
  - `POST /api/approvals` computes `views[]`, `evidence_hashes_viewed` and `active_dwell_ms` on the server from that session's view tokens for that case.
  - Any client `dwell_ms` is ignored and recorded in `client_supplied_ignored`.
  - The approval is always stored, because it is evidence. The gate judges it.
  - `POST /api/approvals/bulk` (the deliberate "Select all, approve 50") calls the same logic in a loop.
  - Every approval also updates `reviewer_state` (`$push` the timestamp, `$slice -100`, `$inc version`) in a transaction.
- **M6. Versioned policy.**
  - `review_policies` holds exactly one `status:"active"` document per `(tenant_id, action_type)`, enforced by a partial unique index.
  - `POST /api/policies` supersedes the current version and inserts v+1 in one transaction.
- **M7. Gate transaction.** `POST /api/gate/execute` runs this sequence:
  1. `ClientSession.withTransaction` with snapshot read concern and majority write concern.
  2. Read: approval, proposal, case, active policy, reviewer, `reviewer_state`, and active suspensions.
  3. Evaluate G1-G8 (Section 8).
  4. On allow, write: `reviewer_state` (`{_id, version: v_read}` → `$inc version`, `$set last_gate_at`); the denial (`AUTHORIZED`); the grant; the approval (`consumed`); the proposal (`authorized`); the gate_decision (`ALLOW`); and audit.
  5. On refuse, write: `reviewer_state` (same version bump); gate_decision (`REFUSE` with reasons); approval (`refused`); proposal (`needs_review` with reasons); and audit.
  6. If G6 (rate) fails, also run the suspension writes (M10) inside the same transaction.
  7. Store the transaction attempt count on the gate_decision.
  8. Every operation must pass the session object.
- **M8. Mock target systems.** FastAPI on port 8000.
  - `POST /target/{kind}/{record_id}/apply` requires `Authorization: Grant <id>`. In one pymongo transaction it consumes the grant (`findOneAndUpdate {_id, status:"issued", expires_at>now, tenant_id, record_id, audience}` → `used`), sets the record status, and writes `target_log`.
  - With no grant or an invalid grant it returns 403 and writes `target_log {outcome:"REFUSED_NO_GRANT", caller}`.
  - `GET` returns the record for read-back.
- **M9. Executor loop.** Python. It polls `proposals.status == "approved"` and does the following for each:
  1. Calls the gate.
  2. On allow, calls the target with the grant.
  3. Calls `POST /api/gate/confirm`. The gate reads the target back itself and sets the denial to `CONFIRMED` only if the target status equals the policy's `effect.apply_status` and `last_apply.grant_id` matches.
  - It honours `agent_control.paused`.
- **M10. Suspension.** Three sources: the gate inline rate rule (G6), a change-stream detector process, and the supervisor halt (`POST /api/suspensions`).
  - Detector rules: at least `rate_max` approvals in `rate_window_ms`, or the median `active_dwell_ms` of the last `median_n` approvals below `min_active_dwell_ms`.
  - The detector saves the resume token to `detector_state` after each event and calls `resumeAfter` on start.
  - The suspension transaction:
    - updates `reviewer_state` (`suspended:true`, `$inc version`)
    - upserts the active suspension, stamped with `policy_id` and `policy_version`
    - revokes issued grants for that reviewer
    - requeues approved proposals for that reviewer to `needs_review`
    - upserts a `compensations` document for each `CONFIRMED` denial by that reviewer within `compensation_lookback_ms`
    - writes audit
- **M11. Compensation worker.** Runs in the detector process.
  - For each `pending` compensation: `POST /target/{kind}/{id}/compensate` with header `X-Compensation-For: <denial_id>`. The target is idempotent per denial_id.
  - Then `GET` read-back. If the status equals `effect.compensate_status`, mark the compensation `confirmed` and the denial `REVERSED`. Otherwise increment `attempts` and set `next_attempt_at` with backoff.
- **M12. Reviewer UI.**
  - One case at a time: proposal, rationale, cited evidence buttons, view telemetry, attestation checkbox plus text, and an Approve button.
  - The red "Select all, approve 50" button.
  - A live result banner: "Executed: X of N · Refused: Y · top reasons · Reviewer status: SUSPENDED at hh:mm:ss.mmm (policy vN, rule …)".
- **M13. Examiner replay page** `/examiner/:caseId`. Timeline of proposal → views (open, active and idle ms per item) → approval → gate decision (each rule ✓/✗ with values and policy version, attempts) → grant → target apply and read-back → suspension and compensation. Bypass refusals come from `target_log`. An idle flag appears when open ms is at least 3 × active ms.
- **M14. Rules.** `GET :8000/rules?tenant=` and `make rules` print R1-R8 pass/fail with the ids of violating documents (Section 12).
- **M15. Eval.** `make eval` runs the pre-registered held-out workload (Section 12) and prints the table.
- **M16. Concurrency test.** `make test-conflict` (Section 12).
- **M17. Demo operations.** `make reset` restores the seeded demo state in under 60 s. A fallback video of the burst is recorded at 15:30.

### SHOULD
- **S1. Second adverse action, `account_freeze`.** Insert a policy document and seed 40 `target_records` of kind `account`. No code change.
- **S2. Second tenant, `payer-birch`.** Its queue keeps executing while an acme reviewer is suspended.
- **S3. Hash chains.**
  - `review_events` are chained per session (head in `reviewer_sessions.chain_head`).
  - `audit` is chained per case (head in `chain_heads`).
  - The examiner recomputes both chains, and recomputes `active_dwell_ms` from raw heartbeats, then compares it to the approval.
- **S4. `make sweep`.** Floor ∈ {15, 30, 45, 60} s × rate ∈ {5, 10, 20} per 60 s, using time-scaled policies.
- **S5. Supervisor dashboard.** Counts polled every 1 s, suspension list, Halt button, policy editor.
- **S6. LLM rationale.** The LLM writes the rationale and suggests citations. Deterministic validation applies. Rules fallback on any error.
- **S7. Vector Search** over `policy_clauses` (autoEmbed). The agent retrieves the top 3 clauses to cite. Fallback: lookup by code.
- **S8. `make explain`.** Window query explain shows IXSCAN.
- **S9. Reconciler.** On gate start and every 10 s, any `AUTHORIZED` denial older than 30 s is read back. It becomes `CONFIRMED` if the target shows its grant was applied. Otherwise the grant is revoked and the denial set to `NOT_EXECUTED`.

### COULD
- **C1.** Atlas custom role: `insert` and `find` only on `audit`, `review_events` and `target_log` for a separate writer user. [UNVERIFIED that the sandbox allows custom roles]
- **C2.** Time-series `review_events`. Writes to time-series collections are not allowed inside transactions; we never write them in one, but verify.
- **C3.** LangSmith tracing of the agent.
- **C4.** ElevenLabs spoken attestation, stored as approval evidence. Cut by default.
- **C5.** SSE live push instead of polling.
- **C6.** Failure injection on compensation (`FAIL_NEXT_COMPENSATE=1`) to demonstrate retry.

**Cut order.** Cut from the top when behind. Never cut an M item.
1. C1-C6
2. S7 vector
3. S6 LLM
4. S5 dashboard (keep the banner on the review page)
5. S9
6. S2 tenant B
7. S4 sweep
8. S3 chain
9. S1 second action

Within M, simplify in this order rather than cut:
1. Credential specialty match (keep expiry only).
2. Compensation UI (keep the API plus R6).

## 7. Data model

Database: `proofgate`. **Every collection the gate touches requires `tenant_id`, and every compound index leads with it.** Timestamps are BSON dates. Hashes are lowercase hex SHA-256.

### Collections and fields

| Collection | Key fields |
|---|---|
| `cases` | `tenant_id, case_id, kind:"claim"\|"account", specialty, member_ref (synthetic), summary, codes{icd10[], hcpcs[]}, billed_amount, evidence:[{evidence_id, label, content, hash}], created_at` |
| `target_records` (the mock claims and accounts systems) | `tenant_id, kind, record_id, status (claim: PENDING\|DENIED\|OPEN\|PAID; account: ACTIVE\|FROZEN), last_apply{grant_id, denial_id, reviewer_id, at}, reopened_for[] (denial_ids), history[]` |
| `target_log` | `tenant_id, kind, record_id, ts, caller, op:"apply"\|"compensate"\|"read", outcome:"APPLIED"\|"REFUSED_NO_GRANT"\|"REFUSED_GRANT_INVALID"\|"NOOP_IDEMPOTENT"\|"COMPENSATED", grant_id?, denial_id?` |
| `policy_clauses` | `tenant_id, clause_id, action_type, title, text` (made-up "Medical Policy MP-0xx") |
| `proposals` | `tenant_id, proposal_id, case_id, action_type, agent_id, model_version, operator_id, recommendation, rationale, cited_evidence:[{evidence_id, hash}], cited_clauses[], status:"pending_review"\|"approved"\|"authorized"\|"executed"\|"needs_review"\|"reversed", approved_by?, approval_id?, requeue_reasons[], created_at` |
| `reviewers` | `tenant_id, reviewer_id, name, license_no, specialty, license_expires_at, active` |
| `reviewer_sessions` | `tenant_id, session_id, reviewer_id, started_at, chain_head, seq` |
| `view_tokens` | `tenant_id, token, session_id, reviewer_id, case_id, evidence_id, evidence_hash, opened_at, last_hb_at, active_ms, idle_ms, closed_at, expire_at` (TTL) |
| `review_events` | `tenant_id, session_id, seq, reviewer_id, case_id, evidence_id?, type:"open"\|"heartbeat"\|"close"\|"approve", ts (server), credited_ms, prev_hash, hash` |
| `approvals` | `tenant_id, approval_id, case_id, proposal_id, reviewer_id, session_id, credential_snapshot{license_no, specialty, license_expires_at}, views:[{evidence_id, hash, active_ms, open_ms}], evidence_hashes_viewed[], active_dwell_ms, policy_version_at_approval, attestation_text, client_supplied_ignored{}, status:"submitted"\|"consumed"\|"refused"\|"invalidated", created_at` |
| `review_policies` | `tenant_id, policy_id, action_type, version, status:"active"\|"superseded", rationale, created_by, created_at, rules{min_active_dwell_ms, min_item_active_ms, require_all_cited_evidence, rate_max_approvals, rate_window_ms, median_n, require_specialty_match, require_unexpired_license, separation_of_duties, max_proposal_age_ms, compensation_lookback_ms}, effect{kind, apply_status, compensate_status}` |
| `reviewer_state` | `_id:"<tenant_id>\|<reviewer_id>", tenant_id, reviewer_id, version, suspended, suspension_id, approval_ts[] (last 100), last_gate_at` |
| `gate_decisions` | `tenant_id, decision_id, case_id, proposal_id, approval_id, reviewer_id, agent_id, policy_id, policy_version, decision:"ALLOW"\|"REFUSE", checks:[{rule, pass, observed, required}], txn_attempts, ts` |
| `denials` (all adverse actions) | `tenant_id, denial_id, action_type, case_id, record_id, proposal_id, approval_id, reviewer_id, agent_id, operator_id, policy_id, policy_version, grant_id, gate_decision_id, status:"AUTHORIZED"\|"CONFIRMED"\|"NOT_EXECUTED"\|"REVERSED", readback{status, at}, created_at, confirmed_at?` |
| `grants` | `_id (random 128-bit hex), tenant_id, audience:"target:<kind>", record_id, case_id, to_status, denial_id, approval_id, reviewer_id, agent_id, policy_version, status:"issued"\|"used"\|"revoked"\|"expired", expires_at (now+60 s), ttl_at (now+7 d)` |
| `suspensions` | `tenant_id, suspension_id, reviewer_id, active, source:"gate_inline"\|"change_stream"\|"supervisor", rule, observed{count, window_ms, median_dwell_ms}, policy_id, policy_version, ts, grants_revoked, proposals_requeued, compensations_created` |
| `compensations` | `tenant_id, denial_id (unique), record_id, kind, to_status, status:"pending"\|"confirmed", attempts, next_attempt_at, readback{status, at}, suspension_id` |
| `audit` | `tenant_id, case_id?, reviewer_id?, ts, actor, event, ref_ids{}, policy_version?, prev_hash, hash` |
| `chain_heads` | `_id:"audit\|<tenant>\|<case_id>", head, seq` |
| `detector_state` | `_id:"rubber_stamp_detector", resume_token, last_event_at, events_processed` |
| `agent_control` | `_id:"executor\|<tenant>", paused` |
| `eval_runs` | `run_id, seed, prereg_commit, policy_versions, results{}` |

### Validators

All use `validationLevel: "strict"` and `validationAction: "error"`. They check presence and type only; thresholds live in the policy.

```js
// approvals
{ $jsonSchema: { bsonType: "object",
  required: ["tenant_id","approval_id","case_id","proposal_id","reviewer_id","session_id","credential_snapshot",
             "views","evidence_hashes_viewed","active_dwell_ms","policy_version_at_approval","attestation_text","status","created_at"],
  properties: {
    tenant_id: { bsonType: "string", minLength: 1 },
    credential_snapshot: { bsonType: "object", required: ["license_no","specialty","license_expires_at"] },
    views: { bsonType: "array", items: { bsonType: "object", required: ["evidence_id","hash","active_ms","open_ms"] } },
    evidence_hashes_viewed: { bsonType: "array", items: { bsonType: "string", pattern: "^[a-f0-9]{64}$" } },
    active_dwell_ms: { bsonType: ["int","long"], minimum: 0 },
    policy_version_at_approval: { bsonType: ["int","long"] },
    attestation_text: { bsonType: "string", minLength: 10 },
    status: { enum: ["submitted","consumed","refused","invalidated"] },
    created_at: { bsonType: "date" } } } }

// denials
{ $jsonSchema: { bsonType: "object",
  required: ["tenant_id","denial_id","action_type","case_id","record_id","approval_id","reviewer_id","agent_id","operator_id",
             "policy_id","policy_version","grant_id","gate_decision_id","status","created_at"],
  properties: { tenant_id: { bsonType: "string", minLength: 1 }, policy_version: { bsonType: ["int","long"] },
    status: { enum: ["AUTHORIZED","CONFIRMED","NOT_EXECUTED","REVERSED"] }, created_at: { bsonType: "date" } } } }

// review_policies
{ $jsonSchema: { bsonType: "object",
  required: ["tenant_id","policy_id","action_type","version","status","rules","effect","rationale","created_at"],
  properties: { status: { enum: ["active","superseded"] },
    rules: { bsonType: "object", required: ["min_active_dwell_ms","min_item_active_ms","rate_max_approvals","rate_window_ms","median_n","max_proposal_age_ms","compensation_lookback_ms"] },
    effect: { bsonType: "object", required: ["kind","apply_status","compensate_status"] } } } }

// suspensions
{ $jsonSchema: { bsonType: "object",
  required: ["tenant_id","suspension_id","reviewer_id","active","source","rule","policy_id","policy_version","ts"] } }

// review_events
{ $jsonSchema: { bsonType: "object",
  required: ["tenant_id","session_id","seq","reviewer_id","case_id","type","ts","credited_ms"],
  properties: { type: { enum: ["open","heartbeat","close","approve"] } } } }

// reviewers
{ $jsonSchema: { bsonType: "object",
  required: ["tenant_id","reviewer_id","license_no","specialty","license_expires_at"] } }

// audit, gate_decisions, grants, compensations, proposals
// Same pattern: tenant_id plus their id fields and status enums are required.
```

**Demo line:** an insert into `approvals` through the MCP server or mongosh with no `evidence_hashes_viewed` or `tenant_id` fails with "Document failed validation". The MCP server runs `--readOnly` during judging, so do this from `py/db/demo_invalid_insert.py`.

### Indexes

**All indexes, created by `setup_db.py`:**
- **cases**
  - `{tenant_id:1, case_id:1}` unique
- **target_records**
  - `{tenant_id:1, kind:1, record_id:1}` unique
  - `{tenant_id:1, status:1}`
- **target_log**
  - `{tenant_id:1, record_id:1, ts:1}`
- **proposals**
  - `{tenant_id:1, proposal_id:1}` unique
  - `{tenant_id:1, status:1, created_at:1}`
  - `{tenant_id:1, approved_by:1, status:1}`
  - `{tenant_id:1, case_id:1}`
- **reviewers**
  - `{tenant_id:1, reviewer_id:1}` unique
- **reviewer_sessions**
  - `{tenant_id:1, session_id:1}` unique
- **view_tokens**
  - `{tenant_id:1, session_id:1, case_id:1}`
  - `{tenant_id:1, session_id:1, closed_at:1}`
  - TTL `{expire_at:1}`, `expireAfterSeconds: 0` (expire_at = opened_at + 2 h)
- **review_events**
  - `{tenant_id:1, session_id:1, seq:1}` unique
  - `{tenant_id:1, case_id:1, ts:1}`
  - `{tenant_id:1, reviewer_id:1, ts:1}`
- **approvals**
  - `{tenant_id:1, approval_id:1}` unique
  - `{tenant_id:1, reviewer_id:1, created_at:1}` (window query)
  - `{tenant_id:1, case_id:1}`
- **review_policies**
  - `{tenant_id:1, action_type:1, version:1}` unique
  - `{tenant_id:1, action_type:1}` unique with `partialFilterExpression: {status: "active"}`
- **gate_decisions**
  - `{tenant_id:1, case_id:1, ts:1}`
  - `{tenant_id:1, reviewer_id:1, ts:1}`
- **denials**
  - `{tenant_id:1, denial_id:1}` unique
  - `{approval_id:1}` unique (one denial per approval)
  - `{tenant_id:1, case_id:1}`
  - `{tenant_id:1, reviewer_id:1, status:1, confirmed_at:1}`
- **grants**
  - `{tenant_id:1, reviewer_id:1, status:1}`
  - TTL `{ttl_at:1}`, `expireAfterSeconds: 0`
- **suspensions**
  - `{tenant_id:1, reviewer_id:1, ts:1}`
  - `{tenant_id:1, reviewer_id:1}` unique with `partialFilterExpression: {active: true}`
- **compensations**
  - `{denial_id:1}` unique
  - `{status:1, next_attempt_at:1}`
- **audit**
  - `{tenant_id:1, case_id:1, ts:1}`
  - `{tenant_id:1, reviewer_id:1, ts:1}`

**TTL rules:**
- The TTL monitor runs about once a minute. **Code must check `expires_at` itself and never rely on TTL for correctness.**
- We deliberately do **not** TTL-delete proposals. They are audit evidence. Staleness is enforced by gate rule G7 (`max_proposal_age_ms`), which forces re-review.

### Vector index (S7) on `policy_clauses`

Path A, Automated Embedding, from the setup research:
```json
{ "name": "clause_auto_idx", "type": "vectorSearch",
  "definition": { "fields": [
    { "type": "autoEmbed", "modality": "text", "path": "text", "model": "voyage-4" },
    { "type": "filter", "path": "tenant_id" },
    { "type": "filter", "path": "action_type" } ] } }
```
Query it with `{$vectorSearch:{index:"clause_auto_idx", path:"text", query:{text:"<case summary>"}, numCandidates:60, limit:3, filter:{tenant_id:{$eq:"payer-acme"}, action_type:{$eq:"claim_denial"}}}}`.

Fallback, path B (manual vectors):
```json
{ "fields": [ {"type":"vector","path":"embedding","numDimensions":1024,"similarity":"cosine"},
              {"type":"filter","path":"tenant_id"}, {"type":"filter","path":"action_type"} ] }
```
Embed with `voyage-4-lite` and `output_dimension=1024`, using `input_type="document"` for clauses and `"query"` for the query.

**Poll `list_search_indexes()` until the status is READY.**

## 8. Architecture

**Components**

```
 Angular :4200 (C) ──/api──▶ Spring Boot "gate" :8080 (B) ──────────┐
   reviewer UI, supervisor,   sessions, evidence+view tokens,       │
   examiner, rules            heartbeats, approvals, GATE TXN,      │   MongoDB Atlas
        │                     policies, suspensions(halt), confirm  ├──▶ (all state)
        └──/py──▶ Python FastAPI :8000 (A)                          │
                   mock target systems (claims, accounts),          │
                   /rules, agent control                            │
 Python agent (A): triage loop + executor loop ─▶ gate ─▶ target   │
 Spring Boot "detector" profile (B), separate process: change stream│
   on approvals → suspension txn; compensation worker ──────────────┘
```

**Language for the agent loop:** Python, used for both triage and the executor. The gate and detector are Java, which is Engineer B's strength. The target systems, rules and eval are Python.

**Spring:**
- Pin Spring Boot 3.5.x and Java 21. [NOT IN RESEARCH: Spring Boot 4 may rename `spring.data.mongodb.*` properties, so pin 3.5.]
- Use the MongoDB **sync driver directly** for the gate:
  ```java
  try (ClientSession s = mongoClient.startSession()) {
    s.withTransaction(callback, TransactionOptions.builder()
        .readConcern(ReadConcern.SNAPSHOT)
        .writeConcern(WriteConcern.MAJORITY)
        .build());
  }
  ```
- **Every** `find`, `update` and `insert` inside the callback must take `s` as its first argument. An operation without it silently runs outside the transaction. This is the number-one bug.
- `withTransaction` retries the callback on `TransientTransactionError`. Count invocations in an `AtomicInteger` and store the count as `txn_attempts`.
- Keep the transaction well under 60 s, the default transaction lifetime.
- `spring.profiles.active=gate` runs the web app. `spring.profiles.active=detector` runs with `spring.main.web-application-type=none`, the change stream and the compensation worker. It is the same jar.

**Why the write conflict happens (the core answer):**
- The gate transaction reads `reviewer_state` at the start of its snapshot. Its last write is `updateOne(s, {_id, version: v_read}, {$inc:{version:1}})`.
- The suspension transaction, the approval transaction and every other gate transaction for that reviewer also write that **same document**.
- MongoDB raises a WriteConflict (labelled TransientTransactionError) when a transaction writes a document that another transaction committed after its snapshot.
- The driver then retries the whole callback. The retry reads `suspended: true`, or the new approval count, and refuses.
- If the update matches 0 documents because the version moved, throw a custom retryable exception. Belt and braces.

**Gate checks.** Each is recorded as `{rule, pass, observed, required}`.

| Code | Check |
|---|---|
| G1 APPROVAL_FOR_CASE | The approval exists. Its `tenant_id`, `case_id` and `proposal_id` equal the request's. Its status is `submitted`. It is unconsumed (also enforced by the unique `denials.approval_id` index). |
| G2 NOT_SUSPENDED | `reviewer_state.suspended == false`, no active suspension for the reviewer, and the executor is not paused. |
| G3 CREDENTIAL | `license_expires_at > now`. If `require_specialty_match`, `reviewer.specialty == case.specialty`. The approval's credential snapshot equals the current reviewer document. |
| G4 EVIDENCE_COVERAGE | Every `proposal.cited_evidence[].hash` is in `approval.evidence_hashes_viewed` and still equals the current `cases.evidence[].hash`, so the content has not changed since it was viewed. |
| G5 DWELL | `approval.active_dwell_ms ≥ rules.min_active_dwell_ms`, and every cited item has `active_ms ≥ rules.min_item_active_ms`. |
| G6 RATE | The count of this reviewer's approvals with `created_at` in `[now - rate_window_ms, now]` is below `rate_max_approvals`. On failure: refuse, and write the suspension in the same transaction. |
| G7 FRESHNESS | `now - proposal.created_at ≤ max_proposal_age_ms`. |
| G8 SEPARATION_OF_DUTIES | `approval.reviewer_id ∉ {proposal.operator_id, agent_id}`. |

**Exclusive focus:** a session has only one open view token, and opening a new one closes the previous one. Server-credited active time across all cases therefore cannot exceed wall-clock time. Ten approvals that each meet a 30 s floor need at least 300 s, so a burst cannot pass G5 whatever the rate.

### API contract

All Spring endpoints take `X-Tenant-Id`. Reviewer endpoints take `X-Session-Id`. Agent endpoints take `X-Service-Identity: triage-agent-v1` and `X-Service-Key: $AGENT_SERVICE_KEY`.

**`POST /api/sessions`**
```json
// request
{ "tenant_id": "payer-acme", "reviewer_id": "dr-demo" }
// response
{ "session_id": "S-9f2c", "reviewer": { "reviewer_id": "dr-demo", "specialty": "orthopedics", "license_expires_at": "2027-06-30T00:00:00Z" } }
```

**`GET /api/queue?status=pending_review&limit=50`**
```json
// response
[ { "proposal_id": "P-A-0007", "case_id": "CLM-A-0007", "action_type": "claim_denial", "recommendation": "deny",
    "summary": "...", "rationale": "...",
    "cited_evidence": [ { "evidence_id": "E1", "label": "Claim line 1" }, { "evidence_id": "E3", "label": "Prior-auth record" } ],
    "created_at": "..." } ]
```

**`GET /api/cases/{caseId}/evidence/{evidenceId}`**
```json
// response
{ "evidence_id": "E1", "label": "...", "content": "...", "hash": "<64 hex>", "view_token": "VT-…", "opened_at": "<server ts>" }
```

**`POST /api/views/{token}/heartbeat`**
```json
// request
{ "visible": true, "interacted_within_ms": 3200 }
// response
{ "active_ms": 25000, "idle_ms": 0, "credited_ms": 5000 }
```
If the request reports `visible: false`, or `interacted_within_ms` above 15000, the server credits 0.

**`POST /api/views/{token}/close`**
```json
// response
{ "active_ms": 31000 }
```

**`POST /api/approvals`**
```json
// request (any extra field such as dwell_ms is ignored)
{ "proposal_id": "P-A-0007", "attestation_text": "I reviewed the cited evidence for this case." }
// 201 response
{ "approval_id": "AP-…", "active_dwell_ms": 41250,
  "views": [ { "evidence_id": "E1", "active_ms": 22000, "open_ms": 23500 } ],
  "evidence_hashes_viewed": ["…"], "policy_version_at_approval": 3,
  "client_supplied_ignored": { "dwell_ms": 45000 } }
```

**`POST /api/approvals/bulk`**
```json
// request
{ "proposal_ids": ["…50 ids"], "attestation_text": "Reviewed in batch." }
// response
{ "submitted": 50, "approval_ids": ["…"] }
```

**`POST /api/gate/execute`** (agent only)
```json
// request
{ "proposal_id": "P-A-0007", "approval_id": "AP-…", "agent_id": "triage-agent-v1", "operator_id": "op-ops-1" }
// 200 response
{ "decision": "ALLOW", "denial_id": "D-…", "grant_id": "g_…", "grant_expires_at": "...",
  "target": { "kind": "claim", "record_id": "CLM-A-0007", "to_status": "DENIED" },
  "policy": { "policy_id": "acme-claim_denial", "version": 3 }, "txn_attempts": 1, "gate_decision_id": "GD-…" }
// 409 response
{ "decision": "REFUSE", "gate_decision_id": "GD-…", "policy": { "version": 3 }, "txn_attempts": 2,
  "reasons": [ { "rule": "G5_DWELL", "observed": 0, "required": 30000, "detail": "active dwell 0.0 s < 30 s floor (policy v3)" },
               { "rule": "G4_EVIDENCE_COVERAGE", "detail": "cited E1,E3 not opened" },
               { "rule": "G2_NOT_SUSPENDED", "detail": "reviewer suspended 12:41:07.310 (change_stream, rate 10/60s, policy v3)" } ] }
```

**`POST /api/gate/confirm`** (agent only)
```json
// request
{ "denial_id": "D-…" }
// response
{ "denial_id": "D-…", "status": "CONFIRMED", "readback": { "status": "DENIED", "grant_id": "g_…" } }
```
The response status is `NOT_EXECUTED` if the read-back does not match.

**`GET` and `POST /api/policies`**
```json
// POST request
{ "action_type": "claim_denial", "rules": { "min_active_dwell_ms": 60000 }, "rationale": "Raise floor after audit" }
// response
{ "policy_id": "acme-claim_denial", "version": 4, "status": "active", "superseded_version": 3 }
```
The new version merges the given rules over the current active version.

**`POST /api/suspensions`** (supervisor halt)
```json
// request
{ "reviewer_id": "dr-demo", "reason": "SUPERVISOR_HALT" }
// response
{ "suspension_id": "SU-…", "grants_revoked": 0, "proposals_requeued": 3, "compensations_created": 1 }
```

**`POST /api/agent/pause`** with `{ "paused": true }`, and the matching resume call.

**`GET /api/dashboard`**
```json
{ "executed": 1, "refused": 50, "pending": 140, "suspended_reviewers": ["dr-stamper"],
  "last_burst": { "submitted": 50, "executed": 0, "top_reasons": { "G5_DWELL": 50, "G4_EVIDENCE_COVERAGE": 50, "G2_NOT_SUSPENDED": 40 } } }
```

**`GET /api/examiner/cases/{caseId}`**
```json
{ "case": { "…" },
  "proposal": { "agent_id": "…", "model_version": "…", "rationale": "…", "cited_evidence": [] },
  "views": [ { "evidence_id": "E1", "open_ms": 23500, "active_ms": 22000, "idle_flag": false } ],
  "approval": { "…" }, "gate_decisions": [ { "…checks" } ], "denial": { "…" }, "grant": { "…" },
  "target_log": [ { "outcome": "REFUSED_NO_GRANT", "caller": "triage-agent-v1", "ts": "…" } ],
  "suspension": null, "compensation": null,
  "chain": { "review_events_ok": true, "audit_ok": true, "dwell_recomputed_ms": 22000, "dwell_matches": true } }
```

**Python target system (:8000)**
```text
POST /target/{kind}/{record_id}/apply
  headers: Authorization: Grant g_…; X-Service-Identity
  body:    {"to_status": "DENIED"}
  200      {"record_id": "…", "status": "DENIED", "applied_by_grant": "g_…"}
  403      {"error": "NO_VALID_GRANT", "logged": true}

POST /target/{kind}/{record_id}/compensate
  header:  X-Compensation-For: D-…
  body:    {"to_status": "OPEN"}
  200      {"status": "OPEN", "noop": false}    // noop is true on a repeat call

GET  /target/{kind}/{record_id}        -> {"status": "…", "last_apply": {…}, "reopened_for": […]}
GET  /rules?tenant=payer-acme          -> {"R1": {"pass": true, "violations": []}, …, "R8": …}
```

**What the LLM does vs what deterministic code decides**

| LLM (S6, optional) | Deterministic code |
|---|---|
| Drafts the rationale text. Suggests deny or pay and which evidence and clauses to cite, as JSON. | Validates that cited ids exist in the case and copies their hashes. Falls back to the rules triage on any parse error. **Every gate decision, every threshold, suspension, grant, compensation and rule.** The LLM never sees a grant and cannot call the target. |

## 9. Setup from zero

From the verified research unless marked otherwise.

**Prerequisites**
- Node v22.13.0 or later (`node -v`). Node 20 is deprecated for the MCP server.
- Python 3.11 or later. `langgraph-checkpoint-mongodb` 0.5.x needs 3.11 if you use it.
- Java 21 and Maven [NOT IN RESEARCH].
- Angular CLI [NOT IN RESEARCH].
- Claude Code.

**1. Atlas sandbox cluster** [UNVERIFIED: the sandbox invite steps are specific to this event]
1. Accept the invite email and open the hackathon organization and project.
2. Use the provided cluster, or create one. If you can choose, avoid M0 for the demo: shared tiers throttle operations per second, and the burst plus heartbeats may hit that limit [VERIFY tier limits]. Automated Embedding works on M0, Flex and M10+.
3. Network Access: add your current IP. Add 0.0.0.0/0 only for the venue and remove it afterwards.
4. Database Access: create user `gate_app` with readWrite on `proofgate`. URL-encode special characters in the password.
5. Connect → Drivers → copy the SRV string.
6. Confirm early that transactions and change streams work on your tier. Run `make smoke`: one transaction plus one `watch()` event. If either fails, ask the organisers for a different tier. Everything depends on both.

**2. `.env`** at the repo root. Commit `.env.example` only.
```
MONGODB_URI=mongodb+srv://gate_app:<urlencoded-pass>@<cluster-host>/?retryWrites=true&w=majority
DB_NAME=proofgate
AGENT_SERVICE_KEY=dev-agent-key-change-me
GATE_URL=http://localhost:8080
TARGET_URL=http://localhost:8000
DEMO_DEBUG_HOOKS=true            # enables X-Debug-Pause-Ms on the gate; set false for the public demo
LLM_PROVIDER=anthropic           # or openai; S6 only
ANTHROPIC_API_KEY=
LLM_MODEL=                       # pick a current small model in your provider console [UNVERIFIED id]
VOYAGE_API_KEY=                  # S7 path B only; Atlas-issued key -> https://ai.mongodb.com/v1, Voyage-dashboard key -> https://api.voyageai.com/v1
LANGSMITH_TRACING=true           # C3
LANGSMITH_API_KEY=ls_...
LANGSMITH_PROJECT=proofgate
ELEVENLABS_API_KEY=              # C4, cut by default
```
- Python: call `from dotenv import load_dotenv; load_dotenv()` first, before any other import.
- Spring `application.yml`: `spring.data.mongodb.uri: ${MONGODB_URI}`, `spring.data.mongodb.database: ${DB_NAME}`. Load `.env` with your IDE or `export $(grep -v '^#' .env | xargs)`.

**3. MongoDB Agent Skills and MCP Server in Claude Code**

Path A (recommended, skills plus the Atlas-hosted MCP over OAuth):
```
claude plugin marketplace add https://github.com/mongodb/agent-skills.git
# inside Claude Code:
/plugin          # choose the MongoDB plugin: mongodb-atlas for Atlas (the README shows `/plugin install mongodb-atlas`)
/reload-plugins
```
Sign in to Atlas in the browser when prompted. [UNVERIFIED: the exact @marketplace suffix. Pick from the `/plugin` menu rather than guessing.]

Path C (local MCP, database tools, read-only):
```
claude mcp add-json "MongoDB" '{"command":"npx","args":["-y","mongodb-mcp-server@latest","--readOnly"],"env":{"MDB_MCP_CONNECTION_STRING":"mongodb+srv://<user>:<pass>@<cluster>/proofgate"}}'
```
[UNVERIFIED: `add-json` form is from a third-party site.]

Verify with `claude mcp list` or `/mcp`, then ask the agent to "list collections in proofgate".

Gotchas:
- A connection string alone gives database tools only. Atlas admin tools need `MDB_MCP_API_CLIENT_ID` and `MDB_MCP_API_CLIENT_SECRET` from a least-privilege service account with your IP on its access list.
- Keep `--readOnly` on during judging.
- Skills-only install (`npx skills add mongodb/agent-skills`) configures no MCP server.

**4. Voyage AI** (S7 path B only). Path A, autoEmbed, needs no embedding code.
- `pip install voyageai`.
- Add a payment method immediately, or you get HTTP 429 at about 3 RPM [UNVERIFIED numbers].

**5. LLM key** (S6). Put it in `.env`. Test with one call before 13:00. If it is not working by 14:00, cut S6.

**6. ElevenLabs:** not used. If attempted (C4): `pip install "elevenlabs<3"`; never ship the key to the browser.

**7. LangSmith** (C3)
- `pip install -U langsmith`.
- Set the env vars above; wrap `triage_one()` and `execute_one()` with `@traceable` from `langsmith`.
- Non-US accounts must set `LANGSMITH_ENDPOINT`, copied from your settings [UNVERIFIED value].

**8. Public GitHub repo** [NOT IN RESEARCH]
```
gh repo create proofgate --public --clone
```
Add all three teammates as collaborators in the first 15 minutes. All commits are made today.

**9. Scaffolds** [NOT IN RESEARCH, standard commands]
```
curl https://start.spring.io/starter.zip -d type=maven-project -d javaVersion=21 -d bootVersion=3.5.0 \
  -d dependencies=web,data-mongodb,validation -d groupId=dev.proofgate -d artifactId=gate -o gate.zip && unzip gate.zip -d gate
npx @angular/cli@latest new ui --routing --style=css --skip-git
python -m venv .venv && . .venv/bin/activate && pip install fastapi uvicorn pymongo httpx python-dotenv pytest
```
If start.spring.io rejects `bootVersion=3.5.0`, omit it and then set the parent version in `pom.xml` to the latest 3.5.x.

**Folder layout**
```
proofgate/
  README.md  .env.example  Makefile
  docs/PRD.md  docs/preregistration.md  docs/enforcement-map.md   # file:line of every gate rule
  py/  db/setup_db.py db/smoke.py db/demo_invalid_insert.py db/explain.py
       seed/generate.py
       target/app.py                     # FastAPI: target systems + /rules + agent control
       agent/triage.py agent/executor.py agent/llm.py
       rules/rules.py
       eval/simulate.py eval/run_eval.py eval/sweep.py
       tests/test_conflict.py scripts/burst_forged.sh scripts/bypass.sh scripts/reset.sh
  gate/  src/main/java/dev/proofgate/{session,view,approval,gate,policy,suspension,detector,compensation,examiner}/
  ui/    src/app/{review,supervisor,examiner,rules}/  proxy.conf.json  (/api -> :8080, /py -> :8000, pathRewrite /py -> "")
```

**Makefile targets**

| Target | Runs |
|---|---|
| `setup` | `setup_db` + `seed` |
| `reset` | drop, then `setup` |
| `smoke` | transaction + change-stream smoke test |
| `target` | `uvicorn py.target.app:app --port 8000` |
| `agent` | triage + executor |
| `gate` | Spring with profile `gate` |
| `detector` | Spring with profile `detector` |
| `ui` | `ng serve --proxy-config proxy.conf.json` |
| `rules` | R1-R8 |
| `eval` | held-out evaluation |
| `sweep` | threshold sweep |
| `test-conflict` | Section 12 concurrency test |
| `explain` | window-query explain plan |
| `burst-forged` | 50 parallel forged approvals |
| `bypass` | curl to the target with no grant |

On Windows, run the underlying `python -m …` and `mvn spring-boot:run -Dspring-boot.run.profiles=gate` commands directly.

## 10. Seed data

Fixed seed `20261114`. All data is synthetic, no PHI.

**Tenant `payer-acme`**
- **200 claim cases.** Specialties are spread over orthopedics, cardiology and radiology.
  - Each case has 2-4 evidence items, for example "Claim line 1: HCPCS E0601 CPAP device, billed $X", "Synthetic clinical note excerpt (generated text)", "Prior-auth record: none on file", "Member eligibility".
  - `hash = sha256(content)`.
  - Codes come from public-domain ICD-10-CM and HCPCS Level II. **No CPT descriptors.**
- **200 `target_records`** of kind `claim`, all `PENDING`.
- **30 `policy_clauses`.** A made-up "Acme Medical Policy MP-001…MP-030", for example "MP-012: CPAP requires a documented sleep study within 12 months".
- **Proposals** pre-generated by the rules triage. About 60% are deny, each citing 2 evidence items and 1 clause. The rest are pay.
- **40 accounts for S1** (`kind:"account"`, ACTIVE). There are 40 `account_freeze` cases with evidence such as "Synthetic transaction pattern report" and "KYC mismatch note", plus proposals.

**Reviewers (acme), each with a `reviewer_state`:**

| Reviewer | Purpose |
|---|---|
| `dr-demo` | Orthopedics, valid. The judge's honest seat. |
| `dr-stamper` | Orthopedics, valid. The bulk-button seat, with 50 queued deny proposals. |
| `dr-prep` | Used before judging for the policy-edit demo. |
| `dr-late` | Used for the compensation demo. |
| `dr-expired` | Licence expired 2026-10-01. Shows G3. |
| `dr-cardio` | Cardiology. Shows a specialty mismatch on an ortho claim. |
| `dr-fraud-ops` | Same id as `operator_id`. Shows G8. |

- Operator: `op-ops-1`. Agent: `triage-agent-v1`.

**Policies**

| Policy | Version | Settings |
|---|---|---|
| `acme-claim_denial` | v1 (active) | `min_active_dwell_ms` 30000, `min_item_active_ms` 5000, `rate_max_approvals` 10, `rate_window_ms` 60000, `median_n` 5, `max_proposal_age_ms` 86400000, `compensation_lookback_ms` 3600000. Effect: claim, DENIED, OPEN. |
| `acme-account_freeze` | v1 (S1) | Same rules with a floor of 20000. Effect: account, FROZEN, ACTIVE. |

Rationale text to store with the claim policy: "30 s is a demo floor. ProPublica reported about 1.2 s per claim. The rate of 10 per 60 s cannot be reached with honest 30 s per-case review under exclusive focus."

**Tenant `payer-birch` (S2)**
- 40 claims with records and proposals.
- Reviewers `dr-birch-1` and `dr-shared`. `dr-shared` also exists at acme as `dr-shared`, with a separate `reviewer_state` per tenant.
- Policy `birch-claim_denial` v1.

**Tenant `payer-eval` (M15)**
- 600 cases generated with the eval seed.
- Time-scaled policies: every time parameter ÷ 10, so the floor is 3000 ms, the per-item floor 500 ms and the window 6000 ms.
- Plus a baseline policy v0 with all checks except G1 disabled. Model it as `rules.baseline_only_existence: true`; the gate skips G3-G7 when it is set.

## 11. Hour-by-hour plan

Checkpoints are go/no-go. If a checkpoint fails, apply the cut order immediately.

| Time | Engineer A (Python) | Engineer B (Spring) | Engineer C (Angular) |
|---|---|---|---|
| 11:45-12:00 | All three: create the repo, add collaborators, commit this PRD to `docs/`, set up `.env`, Atlas access and MCP (Path A or C). A runs `make smoke`. | | |
| 12:00-12:40 | `setup_db.py` (validators, indexes, TTL), `seed/generate.py`, `make setup` | Spring scaffold, MongoClient bean; `POST /api/sessions`; evidence GET with view tokens and exclusive focus; heartbeat and close; `review_events` | Angular scaffold, proxy, routes; review page against mock JSON: queue, case view, evidence panel |
| **12:40 checkpoint** | Data visible in Atlas; B reads a case through the API. **If transactions or change streams fail on the tier, escalate now.** | | |
| 12:40-13:45 | Target FastAPI: apply with atomic grant consumption, 403 plus log, GET, compensate (idempotent); executor loop; `make bypass` | Approvals (server-computed, ignores `dwell_ms`, bulk); policy GET and POST (versioned transaction); **gate transaction G1-G8** with the `reviewer_state` version write, `txn_attempts`, refusal reasons; `/gate/confirm` read-back | Real API wiring; heartbeat service (visibility plus input within 15 s, every 5 s); Approve with attestation; red bulk-50 button; result banner polling `/api/dashboard` |
| **13:45 checkpoint (core demo)** | Curl: an honest approval after 30 s executes and is confirmed by read-back. Bulk 50 gives executed 0. Forged `dwell_ms` gives 0. Bypass gives 403. **Commit and tag `core-ok`.** | | |
| 13:45-14:45 | `rules.py` R1-R8 and `/rules`; `eval/simulate.py`. **Commit `docs/preregistration.md` by 14:15, before the first eval run.** Dev seed 1 only. | Suspension transaction (shared by gate inline, halt and detector); detector profile with change stream and resume token in `detector_state`; compensation worker; `X-Debug-Pause-Ms` hook; `make test-conflict` | Examiner page (timeline, checks, target_log, idle flag); supervisor page (policy edit, halt, suspensions, counts); rules page |
| **14:45 checkpoint** | Full UI demo path works. Detector kill and restart still suspends. `test-conflict` passes. R1-R8 pass on demo data. | | |
| 14:45-15:30 | Run `make eval` **once** on held-out seed 20261114; baseline; `make sweep`; S1 seed plus policy; S6 LLM only if all of this is done | S2 tenant checks; S3 hash chains plus examiner verify; S9 reconciler; S8 `make explain` | Polish banners and suspension toast; S1 action type in the UI; screenshot the explain output |
| **15:30 FEATURE FREEZE** | Only bug fixes after this point. | | |
| 15:30-16:00 | Paste eval output into the README verbatim | Write `docs/enforcement-map.md` (rule → file:line); reset script | Record the fallback burst video, then the 1-minute video (C edits, A narrates) |
| 16:00-16:30 | All three: `make reset`, two full dry runs of the 3-minute demo, Q&A drill using Section 14 | | |
| 16:30-16:45 | Submit (Section 16) | Verify the repo is public and builds from a clean clone | Upload the video and check its audio |

## 12. Evaluation

Pre-registered, small, honest, rule-checked.

**Pre-registration.** Commit `docs/preregistration.md` before the first eval run. Its commit hash is printed by `make eval`. It fixes:
- the thresholds (policy v1, scaled ÷10)
- the group definitions below
- the dev seed (1) and held-out seed (20261114)
- the metrics

The thresholds are set from the policy rationale, not tuned on sessions. The held-out seed is run **once**, and the output goes into the README unedited.

**Workload** (`payer-eval`, time-scaled ÷10). The simulator drives the **real** HTTP endpoints: sessions, evidence fetch, heartbeats, approvals. The executor drives the real gate. Group behaviours are shown in real time; the simulator divides by 10.

| Group | n reviewers | Cases each | Behaviour |
|---|---|---|---|
| honest | 12 | 8 | Opens all cited items (sometimes one extra). Active time per case lognormal with a 75 s median, sigma 0.5, **not clipped**. Heartbeats with interaction. |
| fast-honest | 4 | 8 | Same, with a 35 s median and sigma 0.3. Competent, fast reviewers: the hard case. |
| stamper | 4 | 50 | Bulk endpoint, no views. |
| tab-idler | 4 | 8 | Opens the first cited item, then no interaction. Heartbeats report no input, so nothing is credited. |
| skimmer | 4 | 8 | Opens each cited item for 2 s, approves. |
| heartbeat-forger | 2 | 8 | A script that fetches each cited item and sends "interacted" heartbeats for 31 s without reading. **Expected to pass. This is the null result.** |

**Metrics** (computed from stored state by `run_eval.py`, never from the UI):
- **Per group:** denials attempted, executed, refused (by rule); reviewers suspended (and source).
- **False refusal rate:** honest and fast-honest denials refused ÷ attempted.
- **False suspension rate:** honest and fast-honest reviewers suspended ÷ n.
- **Denials sent back per false suspension.**
- **Miss rate:** gamer-group denials executed ÷ attempted, per gamer group.
- **True suspension rate:** gamer reviewers suspended ÷ n.
- **Median server-verified active review time per executed denial.**
- **R1-R8 pass/fail.**
- **Conflict stats:** the distribution of `txn_attempts` from `gate_decisions`.

**Baseline.** The same workload under policy v0, an "approval exists" gate equivalent to the RunwayOps, LabRat and Aegis pattern. It is expected to execute nearly all gamer denials. Say "by construction" when presenting it.

**Rules over stored state** (M14):
- **R1.** Every CONFIRMED denial has exactly one approval with matching `tenant_id`, `case_id` and `proposal_id`.
- **R2.** The approval's `evidence_hashes_viewed` ⊇ the proposal's cited hashes.
- **R3.** `approval.active_dwell_ms ≥` the floor of `denial.policy_version`, and every cited item meets the item floor.
- **R4.** The credential snapshot was unexpired at `denial.created_at` and specialty-matched if the policy required it.
- **R5.** No denial has `created_at` after an active suspension's `ts` for the same tenant and reviewer.
- **R6.** Every CONFIRMED denial under a later-suspended reviewer within the lookback has a confirmed compensation, and its read-back shows `compensate_status`.
- **R7.** Every `target_records` entry in an applied status has a CONFIRMED denial with matching `grant_id`: no bypass.
- **R8.** Hash chains verify, and the `active_dwell_ms` recomputed from `review_events` equals the approval's (S3).

**Concurrency test** (`make test-conflict`, M16). It needs `DEMO_DEBUG_HOOKS=true`.

- **(a) Suspension in flight:**
  1. Seed a fresh honest approval for `dr-late`.
  2. Thread 1 calls the gate with `X-Debug-Pause-Ms: 3000`. The pause sits after the reads and before the `reviewer_state` write.
  3. At +500 ms, thread 2 calls `POST /api/suspensions`.
  4. Assert: thread 1 returns REFUSE with G2, `txn_attempts ≥ 2`, and no denial exists.
- **(b) Two denials, same reviewer:** two gate calls, both paused 2000 ms. Assert that exactly one decision has `txn_attempts ≥ 2`. The outcomes are serialised.
- **(c) Burst with the detector stopped:** stop the detector process and run `make burst-forged` (50 parallel approvals with `dwell_ms: 45000`). Assert 0 denials CONFIRMED and refusals cite G5, G4 and G6.
- **(d) Detector crash:**
  1. Run the burst.
  2. Kill the detector after about 5 events (or kill it immediately and let the events queue).
  3. Restart it.
  4. Assert `detector_state.events_processed` covers all events and exactly one active suspension exists. Idempotent through the partial unique index and upsert.

The test prints PASS or FAIL per assertion. Show it on stage.

**Output format** (printed table, with a commit hash and seed header). Fill only from the run:
```
group           n  attempted executed refused  suspended  false_refusal  miss_rate
honest         12   [..]       [..]     [..]     [..]       [..]           -
fast-honest     4   …
stamper         4   …
tab-idler       4   …
skimmer         4   …
hb-forger       2   …                                                     [expected high]
baseline(v0)   …
R1..R8: [..]   median verified active time per executed denial: [..] s (scaled x10)
```

**If the results are flat or bad, show them anyway.** For example, if fast-honest reviewers are wrongly refused or suspended at 30 s, show `make sweep` and say: "This is the trade-off the policy owner sets. Here is the curve. The policy is data, so the compliance team picks the point and every decision stamps which version it used." The forgers passing is the honest limit: server timing raises the cost of faking review from one click to sustained per-item scripted interaction, and the examiner shows the pattern. It does not prove reading.

## 13. Demo

### 1-minute video (C edits, A narrates; capture with audio)

| Seconds | Picture | Voice |
|---|---|---|
| 0-6 | Title card: "1.2 seconds per claim" with the ProPublica headline (cited) | "ProPublica reported insurer physicians denying claims at about 1.2 seconds each. Fifty at a time." |
| 6-14 | Reviewer page as `dr-stamper`, cursor on the red "Select all, approve 50" | "Agents make this worse. They can queue thousands of denials an hour. So we gave our reviewer the exact batch button." |
| 14-24 | Click; the banner counts down to "Executed: 0 of 50"; SUSPENDED toast | "Fifty approvals hit Atlas. The gate transaction refuses every one: no evidence opened, 0 seconds of server-timed review. The reviewer is suspended mid-run." |
| 24-36 | `dr-demo` opens E1 and E3; active-time meter climbs to 30 s; Approve; "Executed 1, confirmed by read-back" | "A real review: every cited item opened, timed by the server, not the browser. That denial executes, and we read the claims system back to prove it." |
| 36-46 | Examiner page timeline, chain ✓, policy v3 | "An examiner rebuilds any case: what the agent cited, what the reviewer saw and for how long, which policy allowed it." |
| 46-54 | Supervisor halts `dr-late`; reopen shows; claim status OPEN | "And when authority is revoked, past denials are reopened in the claims system and verified." |
| 54-60 | Logo plus "MongoDB Atlas: transactions · $jsonSchema · change streams" | "ProofGate. No proof of review, no denial." |

### 3-minute live table demo

Prepare before judging:
- `make reset`
- Start the target, gate, detector, agent and ui
- Do the `dr-prep` 45 s review with the executor paused
- Open these tabs: review (dr-stamper), review (dr-demo), supervisor, examiner, a terminal

| Time | Step | Fallback if it fails |
|---|---|---|
| 0:00-0:20 | Problem in one breath, plus the buyer: "compliance or GC, exposed to SB 1120-style laws and PxDx-style suits" | n/a |
| 0:20-0:50 | Judge clicks "approve 50" → **0 of 50**, suspended. Point at the reasons. | Play the pre-recorded burst video. Then run `make burst-forged` in the terminal (it does not depend on the UI). |
| 0:50-1:10 | Terminal: `make bypass` gives 403; the examiner shows `REFUSED_NO_GRANT` | Show the `target_log` document in Atlas Data Explorer |
| 1:10-1:50 | Judge as `dr-demo` opens both items and approves after 30 s (narrate the server timing during the wait) → executed, read-back | Use the `dr-prep` case already approved at 45 s |
| 1:50-2:15 | Supervisor: raise the floor 30→60 s (v4), resume the executor, and the `dr-prep` 45 s approval is refused "45.x s < 60 s (policy v4)". Then show the account_freeze policy document running through the same gate (S1). | Show a screenshot from the dry run |
| 2:15-2:40 | `make test-conflict` output (a) and (d): write conflict, then refused; detector killed, resumed, one suspension | Show the test output saved from the dry run (`docs/test-conflict.txt`) |
| 2:40-3:00 | Eval table including the forger null result; R1-R8 all ✓ | Show the README section |

**Never improvise numbers.** Read them off the screen.

## 14. Judge Q&A

**Robert Maissan.** "A suspension is written while two denials for the same reviewer are in flight. Which document do all three transactions write to, so that MongoDB forces a write conflict? Show me the test."
> All three write `reviewer_state` with `_id "payer-acme|dr-late"`. Each gate transaction does `updateOne({_id, version: v_read}, {$inc:{version:1}})`, and the suspension transaction sets `suspended:true` and increments the version. Whichever commits second gets a WriteConflict with the TransientTransactionError label. `withTransaction` re-runs the callback, which re-reads and refuses on G2. `make test-conflict` cases (a) and (b) show it: `txn_attempts=2` and decision REFUSE are stored on the gate_decision.

**Raschid Jimenez.** "Change the dwell floor from 30 s to 60 s mid-queue. Prove that a 45 s approval is refused on the next call with no restart."
> The gate reads `review_policies.findOne({tenant_id, action_type, status:"active"})` inside its snapshot transaction. Editing the policy inserts v4 and supersedes v3 in one transaction, guarded by the partial unique index. We do it live: the next call refuses with "45.2 s < 60 s (policy v4)", and the denial and decision are stamped v4. No restart and no code change. Then a new `account_freeze` policy document runs the same gate. [Read the actual value off the screen.]

**Tapan Shah.** "Kill the detector halfway through the burst. Where is the resume token stored? Why couldn't approvals 1-9 execute before the detector fired?"
> The token is in `detector_state._id:"rubber_stamp_detector"`, saved after every event, and the detector resumes with `resumeAfter`. Approvals 1-9 never depended on the detector. Each failed G5 and G4 synchronously in the gate transaction (0 s of server-credited time, nothing opened), and from the 10th, G6 refused and wrote the suspension inline. All gate transactions also write `reviewer_state`, so they serialise against each other and against the suspension.

**Leo Gomes.** "Kill the Spring service mid-burst and restart it. How many denials executed? Show the query."
> Zero. The query: `db.target_records.countDocuments({tenant_id:"payer-acme", status:"DENIED", "last_apply.reviewer_id":"dr-stamper"})`, then R7. Nothing can be DENIED without a consumed grant, and grants are only minted by a committed ALLOW. A transaction that dies mid-way commits nothing. The S9 reconciler resolves any AUTHORIZED denials left behind by reading the target back.

**Aasawari Sahasrabuddhe.** "Take the agent's service credentials and curl the deny endpoint directly. What stops you, and where does it show in the examiner?"
> Service identity alone gets 403 `NO_VALID_GRANT`. The target consumes a single-use 60-second grant bound to tenant, record, audience, policy version and reviewer, in its own transaction. The refusal is written to `target_log` with the caller identity and appears on that case's examiner timeline. A suspension revokes any issued grants in the same transaction that bumps `reviewer_state`.

**Sergey Strelnikov.** "20 honest reviewers at varied speeds: how many suspended, how many denials sent back per false suspension, which policy version, from stored state?"
> `make eval` reports this per group from `suspensions` and `proposals.requeue_reasons`, and each suspension carries `policy_version`. [Read: honest X/12, fast-honest Y/4, Z sent back per false suspension, policy v1.] We also show the sweep.

**Anamika Ahmed.** "Two approvals commit 5 ms apart, and the 10th approval's suspension arrives after both denials passed the gate. Which document do both write so one aborts? Show the test."
> `reviewer_state`. Both gate transactions write it, so they cannot both commit from the same snapshot. One retries and re-reads, including the approval count for G6. Test (b). If both legitimately passed before the suspension, R5 holds, and the suspension creates compensations that reopen them (R6).

**Pablo Vallejo.** "A denial already went out; the reviewer is suspended 40 s later. Show the reopen, the read-back and the audit link. What if the reopen fails halfway?"
> The suspension transaction upserts `compensations{denial_id}`. The worker calls `/compensate` with `X-Compensation-For`, then GETs the record, marks the compensation confirmed, and sets the denial to REVERSED with an audit link. If the call fails, the compensation stays `pending` with `attempts++` and backoff. The target is idempotent per denial_id, so a repeat returns `noop:true`. R6 shows FAIL until it is confirmed.

**Amrit Krishnan.** "On held-out replay, how many honest reviewers were wrongly suspended, how many idlers got through? What stops this punishing fast, competent reviewers?"
> [Read from the eval table.] Thresholds were pre-registered at commit [hash] before the held-out run. Fast-honest reviewers are a separate group precisely to measure that harm. The sweep shows the trade-off. The policy owner chooses, and each decision records the version.

**Vatsal Shah** and **Parth Patel.** "50 parallel curl approvals with forged `dwell_ms=45000`, detector off: how many execute, and which line stops them?"
> Zero. `ApprovalController` never binds `dwell_ms`; it is stored under `client_supplied_ignored`. The `GateService` G5 check compares server-computed `active_dwell_ms` to the policy floor, at file:line [from `docs/enforcement-map.md`]. G4 refuses too, because nothing was fetched.

**Ahmed Radwan.** "What fraction of careful reviewers is wrongly suspended, what fraction of idlers gets through? Show the run where it fails."
> [Read from the table.] The failure run is the heartbeat-forger group. A script that fetches every item and fakes interaction for 31 s passes. We show it. Server timing raises the cost of faking review from one click to sustained scripted per-item interaction, and the examiner exposes the pattern. It cannot prove reading.

**Pahul Hallan.** "The service that writes approvals also writes review evidence. What stops it fabricating `evidence_hashes_viewed` and `dwell_ms` after the fact? Show detection of one edited review_event."
> `review_events` are hash-chained per session, and audit per case. The examiner recomputes the chain and recomputes active dwell from raw heartbeats, then compares it with the approval. We edit one event in Atlas live, and the badge turns red with "chain broken at seq N". With C1, the app user can only insert. Honest limit: a fully compromised writer that rebuilds the whole chain needs external anchoring (for example, periodically publishing the chain head), which we have not built.

**Noel Kirthiraj.** "Who signs the PO, and what liability does it remove? Why buy a tool that slows denials?"
> The Chief Compliance Officer or General Counsel. It removes their inability to prove that individual clinician review happened, which is what state laws like CA SB 1120 require [VERIFY] and what PxDx-style suits and multi-state inquiries probe. A denial they can prove was reviewed survives appeal and examination. A batch-stamped denial is a liability. It slows only the denials that were never really reviewed.

**Rudraksh Monga.** "Two payers on one cluster; payer A's reviewer is suspended. Show the query and index that leave payer B unaffected, and what stops a dual-credentialed reviewer carrying an approval or suspension across."
> The gate reads `reviewer_state` by `_id "payer-birch|dr-shared"` and counts approvals with `{tenant_id:"payer-birch", reviewer_id, created_at:{$gte}}` on index `{tenant_id:1, reviewer_id:1, created_at:1}`; `make explain` shows the IXSCAN. G1 requires approval, case, session and proposal `tenant_id` to be equal, so an acme approval cannot authorise a birch case. Suspensions are per tenant by design. Sharing them across payers is a policy decision we have deliberately not made.

**Aasheesh Singh.** "A new policy document for freezing an account, no code change: does the gate enforce it? And the held-out false-suspension share?"
> Yes. S1 inserts `acme-account_freeze` v1. The gate is keyed on `action_type`, and the effect comes from `policy.effect` (`kind:account`, FROZEN/ACTIVE) against the generic target API. False-suspension share: [read from the eval table].

## 15. Risks and what to disclose

- **Dwell is a proxy.** Say so first. Mitigations: per-item coverage, exclusive focus, interaction-gated heartbeats, rate and median rules, and an examiner idle flag. The forger null result is shown.
- **The eval is simulated and time-scaled ÷10** against synthetic sessions, not real reviewers. Disclose both.
- **Cigna disputes the ProPublica report and says PxDx is not AI.** Say "the PxDx pattern as reported". Present this as agent-scale approvals, not an accusation.
- **Not a medical tool.** Synthetic data only, no clinical validity, no PHI, and no CPT text.
- **Demo authentication is a reviewer picker.** In production: SSO, plus credential verification against licensing boards.
- **The LLM has no authority.** Rationale only (S6), and the rules fallback is what runs if it fails.
- **Platform limits:** shared-tier throughput; Embedding API is in Preview; transactions and change streams must be confirmed on the sandbox tier [VERIFY].
- **Closeness to past approval-gate projects.** Lead with proof of review and mid-run revocation, not "approval".
- **Regulatory citations** (SB 1120, AZ HB 2175, FINRA, FCA): [VERIFY] before stage and quote no figure you have not opened.
- **The pitch must say the tool *blocks* unreviewed denials.** It does not create review records.

## 16. Submission checklist
- [ ] The GitHub repo is **public**. A clean clone plus `README` quick-start works: `make setup`, then target, gate, detector, agent, ui.
- [ ] All teammates are added as collaborators and have commits. All code was written today, in the MongoDB Atlas Hackathon Sandbox cluster. The README states the sandbox project or cluster name.
- [ ] `.env` is not committed; `.env.example` is. No keys are in history (`git log -p | grep -i key`).
- [ ] README sections:
  - [ ] Pitch
  - [ ] Architecture diagram
  - [ ] Atlas features used: transactions, `$jsonSchema`, change streams with a persisted resume token, partial unique and TTL indexes, aggregation rules, Vector Search if S7 shipped
  - [ ] `docs/enforcement-map.md`
  - [ ] Eval output pasted verbatim, with the pre-registration commit hash
  - [ ] Disclosures (Section 15)
- [ ] 1-minute video **with audio**, uploaded (YouTube unlisted or as required) and linked in the README and the submission.
- [ ] Fallback burst video saved locally.
- [ ] Description (~120 words):

> ProofGate makes an AI agent's adverse decisions, such as claim denials, executable only with proof that a qualified human reviewed that specific case. Reviewers' views of each evidence item are timed by the server. MongoDB Atlas holds identities, versioned review policies, approvals and audit. A single Atlas transaction checks credential, evidence coverage, dwell floor, rate and suspension. It writes a per-reviewer document, so concurrent approvals and suspensions conflict instead of slipping through. Only then does it mint a single-use grant that the claims system requires. A change-stream detector with a persisted resume token suspends rubber-stamping reviewers mid-run, revokes grants, and reopens past denials with verified read-back. The batch "approve 50" executes 0. An examiner replays any case. Includes a pre-registered held-out evaluation, including where it fails. Synthetic data only.

- [ ] Submitted by 16:45, before the 17:00 close. Table setup ready for 17:15.

## 17. First prompt for the AI coding assistant

Each engineer pastes this into their own session and replaces ROLE.

```
You are helping a 3-person hackathon team build "ProofGate". The full spec is docs/PRD.md in this repo. Read it completely before writing code, then follow it exactly. Section 7 is the data model, Section 8 the architecture and API contract, Section 12 the tests and eval.

My role: ROLE = [A: Python — py/ (setup_db, seed, target FastAPI, agent triage+executor, rules, eval, test_conflict) | B: Spring Boot 3.5 / Java 21 — gate/ (sessions, view tokens, heartbeats, approvals, versioned policies, the gate transaction, suspension transaction, detector profile with change stream + resume token, compensation worker, examiner API) | C: Angular — ui/ (review page with heartbeat telemetry + bulk-approve-50 button + result banner, supervisor page, examiner page, rules page)].

Non-negotiable rules:
1. MongoDB Atlas is the only state store; DB name from env DB_NAME, URI from env MONGODB_URI (loaded from .env; never hard-code secrets).
2. Every document and every compound index leads with tenant_id; every query filters by tenant_id.
3. Dwell time is computed ONLY on the server from view tokens + heartbeats (credit min(gap,7000) ms only if gap<=7000 and visible and interacted within 15 s; one open token per session). Never accept dwell from a client.
4. The gate is ONE transaction (Java sync driver ClientSession.withTransaction, snapshot read concern, majority write concern). Pass the session to EVERY operation. It reads policy/approval/proposal/case/reviewer/reviewer_state/suspensions, evaluates G1–G8, and always writes reviewer_state {_id:"<tenant>|<reviewer>", version: v_read} with $inc version, plus denial+grant+audit (ALLOW) or gate_decision+audit+requeue (REFUSE). Count callback invocations and store txn_attempts.
5. $jsonSchema validators check required fields/types only; all thresholds come from the active review_policies document.
6. The target system applies a status change only by atomically consuming a valid grant in a transaction; otherwise 403 + target_log entry.
7. Never invent results. Eval numbers come only from running the eval.
8. Build MUST items (M1–M17) first, in the order of the Section 11 hour plan for my role; do not start SHOULD/COULD until the 13:45 checkpoint passes. Respect the cut order.
9. Keep it simple: no auth framework, no Docker, no extra services. Small files, clear names, comments only where the logic is non-obvious.
10. After each endpoint, give me a curl command (or test) that proves it works against Atlas, and tell me exactly what to run.

Start now: list the files you will create for my role with a one-line purpose each, then implement the first item of my 12:00 block. Use the MongoDB MCP server (read-only) to inspect collections when useful.
```

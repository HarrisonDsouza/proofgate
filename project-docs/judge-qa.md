# Likely judge questions, with draft answers

**Rules for answering:**
- Never give a number that isn't on screen or in today's `make eval` / `make rules` output. Slots marked `[read from …]` stay blank until then.
- Facts marked [VERIFY] are checked by researcher R1 before the stage.
- The fuller technical answers are in PRD §14. The judge-specific angles there come from **simulated** personas.

## Top 5 (every teammate should know these)

**1. "Isn't this just an approval gate? Those exist."**
> Approval gates check that someone clicked approve. We check the approval was *real*, per case, before execution:
> - the server timed the reviewer on every evidence item the agent cited
> - the credential is valid
> - they aren't stamping in bulk
>
> That is checked in one Atlas transaction. A suspension can stop a denial that's already in flight, and we reopen denials that already went out. In four searches we found nothing that combines these. That means none found, not proven new.

**2. "Who pays for this?"**
> The insurer's Chief Compliance Officer or General Counsel. They carry the class-action and regulator risk when a denial can't be shown to have had individual clinician review, which state laws like California SB 1120 require [VERIFY]. It slows only the denials that were never really reviewed.

**3. "Can't the reviewer just leave the tab open?"**
> No. Time only counts while the tab is visible *and* there was input in the last 15 seconds, and only one item can be open at once. The tab-idler group in our eval is refused [read from make eval]. The honest limit is a script that fakes interaction for every item: it passes, and we show that as our null result.

**4. "What stops the agent from just calling the claims system itself?"**
> The claims system only changes a record by consuming a single-use, 60-second grant, which only a committed ALLOW decision can mint. With only the agent's service credentials you get 403, and the refusal is logged in Atlas and shown on the examiner page. *(Demo: `make bypass`.)*

**5. "Why MongoDB?"**
> Statement One asks for Atlas as the identity, policy and audit layer, and we use exactly the named features:
> - schema validation on every record
> - a multi-document transaction as the gate
> - change streams with a stored resume token to suspend rubber-stampers mid-run
>
> Because enforcement and events live in the same database as the data, they can't drift apart. *(See `mongodb-explainer.md`.)*

## MongoDB and technical depth (likely from the MongoDB judges)

**"Which document do concurrent transactions conflict on?"**
> `reviewer_state`, `_id "<tenant>|<reviewer>"`. Every gate call, approval and suspension writes it with a version guard. The second to commit gets a WriteConflict; `withTransaction` retries and the retry re-reads and refuses. `txn_attempts` is stored. *(Demo: `make test-conflict`.)*

**"Kill the detector mid-burst. What happens?"**
> Its resume token is saved in `detector_state` after each event. On restart it resumes from there and ends with exactly one active suspension (partial unique index). The first nine approvals never depended on it anyway: the gate refused them synchronously on no evidence opened and dwell below the floor.

**"Change the dwell floor live. Does the next call obey it?"**
> Yes. Editing the policy inserts version n+1 and supersedes n in one transaction. The gate reads the active version inside its snapshot, so the next call uses it with no restart, and the decision records which version applied.

**"How do you know a denial actually happened?"**
> After applying, the gate reads the claim back from the target and marks the denial CONFIRMED only if the status and grant id match. Same for reopens.

**"What if a reopen fails halfway?"**
> The compensation stays `pending` with retries and backoff. The target is idempotent per denial id, and rule R6 shows FAIL until every compensation is confirmed.

**"How do you keep two insurers apart?"**
> `tenant_id` is required on every document and leads every index. `reviewer_state` is per tenant, so one insurer's suspension doesn't touch another's.

**"What about indexes and performance?"**
> Compound indexes lead with `tenant_id`. The rate-window query uses `{tenant_id, reviewer_id, created_at}`, and `make explain` shows an index scan [if S8 built].

## Security and trust (likely from Okta, Microsoft, Cohere, Zafin)

**"I'll curl a fake `dwell_ms: 45000`."**
> It's ignored: stored under `client_supplied_ignored` and never used. The gate compares server-computed dwell to the floor, at file:line [from `docs/enforcement-map.md`]. *(Proof: `make test-conflict` — a forged burst of 50 executes 0.)*

**"What stops your own service fabricating review records?"**
> If S3 ships: review events are hash-chained per session, and the examiner recomputes the chain and dwell from raw heartbeats. Honest limit: a fully compromised writer could rebuild a whole chain; that needs external anchoring, which we haven't built.

**"Can a grant be replayed?"**
> No. It's consumed atomically (`issued` → `used`) in a transaction, it expires in 60 s, and it's bound to tenant, record, audience, policy version and reviewer.

## Evaluation and honesty (likely from the Vector Institute and Acerta judges)

**"How many honest reviewers did you wrongly suspend?"**
> None in the held-out run: false suspension 0/16 (honest 0/12, fast-honest 0/4; 95% CI 0–19.4%). The cost shows up as refusals instead: 5 of 128 honest approvals (3.9%, CI 1.7–8.8%) were refused for dwell below the floor, and the reviewer can re-review. Thresholds were pre-registered at commit 7df270e (14:25) before the held-out run (results commit 350d06c, 14:31), and fast reviewers are a separate group precisely to measure that harm. Source: `docs/eval-heldout.txt`.

**"Show me where it fails."**
> The heartbeat-forger group passes (16 of 16 executed), and so does the floor-gamer group (32 of 32, held only to the floor). Both were predicted in the pre-registration. Server timing raises the cost of faking review from one click to sustained scripted work per item, but it cannot prove reading. We say that up front.

**"Is the eval real?"**
> It's simulated and time-scaled ÷10 against our real endpoints, with synthetic data. It's not a study of real reviewers.

## Product and impact

**"Is this an accusation against Cigna?"**
> No. We describe "the pattern as reported" by ProPublica; Cigna disputes the report and says PxDx is not AI [VERIFY wording]. Our point is about agent scale: agents can queue denials faster than humans can review.

**"Does it generate compliance paperwork?"**
> No. It *blocks* denials that lack real review. The records are a by-product of enforcement.

**"Where's the AI agent?"**
> The triage agent proposes denials with cited evidence and clauses. The executor carries them out through the gate. The agent is deliberately not trusted: it proposes, code decides.

## Partner tools (new)

**"How do you use LangSmith?"**
> Only if `LANGSMITH_TRACING=true` was set for the demo: each executor step (gate → claims system → confirm) is wrapped in a LangSmith trace for debugging. Atlas remains the record of authority; the examiner and rules read Atlas, not traces. If tracing wasn't on, say: "the hook is wired, we didn't run it today."

**"How do you use ElevenLabs?"** (if spoken attestation shipped)
> The reviewer can speak their attestation. ElevenLabs speech-to-text transcribes it on our server, and the transcript plus an audio hash are stored with the approval in Atlas. A spoken, case-specific statement is far harder to bulk-stamp than a checkbox. It's evidence only and never decides anything.
> If only the voiceover shipped: "We used it for our video narration." Don't oversell it.

**"Why not let an LLM decide?"**
> Policy that lives in a prompt isn't enforcement: agents have ignored stop instructions in reported incidents [VERIFY]. Every decision here is deterministic code reading a versioned policy in Atlas.

## Do not claim (not built today)

Vector Search / Voyage AI, a read-only MongoDB MCP server, the account-freeze action, an LLM-written rationale, LangGraph. G6 (rate) fires in the live UI demo but did not fire in the time-scaled held-out eval; stampers there were refused by G4/G5/G2 and suspended by the detector's median rule.

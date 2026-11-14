# PRD: Shiftline

**A spoken shift handover that compiles into live equipment lockouts, and locks anything it is not sure about.**

Status: **Winner** of the simulated 16-judge tournament (56 points, 8 of 16 first-place votes in the final round; avg impact 8.1, innovation 8.1, feasibility 6.8).
Read `00-README-HANDOFF.md` first: event rules, the shared "don't lose points" checklist and the caveat that judge quotes are simulated personas.

---

## 0. Problem statement fit (added after the official resource guide; read this first)

**Enter under Statement One: Agents You Can Audit.** Use that phrase in the pitch, the 1-minute video and the description.

| Statement One asks | Shiftline's answer | Status |
|---|---|---|
| Atlas as the identity, policy and audit layer: collections, **schema validation**, change streams | Users/roles and service identity (FR-1, §6); guardrails as policy (FR-2 to FR-8); decision log (FR-12); permits change stream (FR-11) | Add schema validation (FR-17 below) |
| Takes **real actions across systems** | Operate requests against an equipment-control simulator; reads work-order and permit systems | Build these as three separate collections behind three small endpoints, and call them "systems" |
| Every action tied to an identity | Every request records the human or service identity (FR-1, FR-12) | Designed |
| Checked against policy **before** it runs | Fail-closed operate check in a transaction (FR-9, FR-10) | Designed |
| Recorded so a reviewer can reconstruct it | Decision log with guardrail ids read, who confirmed what, when | Designed; add a "replay this run" timeline view if time allows |
| **Stop or roll back an agent mid-run** | Not covered before | **Add FR-16 below. This is the gap a judge will probe** |

**New requirements:**
- **FR-16 MUST Mid-run stop and rollback.** The scheduler agent executes a multi-step run (e.g. "restart pump house east": start pump B, then pump A, then compressor 2). Each step is checked before it runs. A **change stream on `guardrails`** watches for new blocking guardrails on any asset in the active run; when one appears (for example the day lead's late call "compressor 2 has a leak"), the run's status becomes `HALTED`, pending steps are cancelled, and steps already done are listed with their **compensating action** (e.g. "stop pump B"), which a human approves. Store runs in an `agent_runs` collection `{ runId, agentId, steps: [{assetId, action, status, decisionId, compensatingAction}], status, haltedBy, haltedAt }`. A human `night_lead` can also press **Stop run**.
- **FR-17 MUST Schema validation.** `$jsonSchema` validators on `guardrails` (requires `assetId`, `state`, `origin`, `createdBy`), `decisions` (requires `requester`, `guardrailIdsRead`, `outcome`) and `agent_runs`. Show in the demo that a malformed write is rejected by the database.

**Timing and submission:** the build schedule in §14 is superseded by `00-README-HANDOFF.md` §8 (submissions due 5:00 PM). Submission needs a public repo, a **1-minute video** (cut the demo in §12 to: pending tiles, spoken handover with gap list, night request blocked aloud, agent run halted mid-run, decision log) and a short description.

---

## 1. One-paragraph summary

At 6 PM the outgoing maintenance lead at a transit yard or process plant speaks the handover into a laptop. Shiftline turns what she says into **guardrail documents in MongoDB Atlas** that bind every later session, human or agent, until a real closing event (a permit signed off by an authorised person) lifts them. It is **default-deny**: every asset with an open work order or permit is locked *before anyone speaks*; speech can only release a lock after a confirmed read-back; anything ambiguous, unconfirmed or not mentioned stays locked, and the agent says so aloud. At 2 AM, when the night lead (or an AI scheduling agent acting for him) says "start pump A", a deterministic check against Atlas blocks it and says why and who said so.

## 2. The problem and why it matters

- **User:** the night-shift maintenance lead at a transit yard or process plant, and any AI agent issuing operate requests on that shift's behalf.
- **Costly failure:** equipment restarted after the previous shift left it unsafe, because one fact was lost at handover. Handover is spoken, hands-busy and noisy; the written note is where items get lost.
- **Headline:** Piper Alpha, 6 July 1988, 167 dead. A condensate pump was restarted by the night shift after the handover failed to pass on that its pressure safety valve had been removed for maintenance. *(Training-data fact; verify before the slide.)*
- **Why agents make it worse:** once AI agents schedule work and issue commands, they inherit the same lost context, at machine speed. An agent needs a memory that **constrains** it, not one it can recall from.

### What it helps with

| For | Helps by |
|---|---|
| Night lead | Never starts a machine the day shift left unsafe; hears exactly why, who said it and when |
| Day lead | Hears what she forgot to mention before she leaves ("You did not mention compressor 2. It stays locked.") |
| Plant safety manager | A dated, attributable record of every handover claim, confirmation, block and release |
| AI agents on the shift | A guardrail they cannot talk their way past: the check is code over Atlas state, not a prompt |

### Buyer (answer to "who pays?")

Plant operations and safety managers already pay for permit-to-work and lockout-tagout (LOTO) software and still lose items at handover. The wedge is **not** replacing that software: Shiftline is a **voice layer on top of the existing work-order and permit system**, whose open orders seed the locks. Secondary buyers: transit maintenance departments and permit-to-work vendors who want to sell an agent-safety layer. *(Noel Kirthiraj persona: "a plant already has permit-to-work software and physical locks, so name the buyer". This is the answer; say it in the pitch.)*

## 3. Why it can win (mapped to past winning patterns)

| Winning pattern | How Shiftline meets it |
|---|---|
| One user, one costly failure | Night lead; restarting unsafe equipment; Piper Alpha |
| Theme taken literally | Context across sessions = guardrails written in one session bind the next; adapt their own guardrails = speech creates and releases guardrails, permits close them; reliable = fails closed |
| Atlas load-bearing | Every operate decision is one indexed Atlas query; change stream closes locks; vector search resolves spoken names; transaction closes the check-then-act race |
| Hard check, not LLM opinion | The operate check is a deterministic rule over stored guardrail state |
| Live-stage moment | The agent cutting in aloud: "Stop. Pump A has no relief valve." |
| Human approval and audit | Role-bound confirmation, permit-issuer sign-off, decision log with guardrail ids read |
| Nearest competitor answered | Atlas Agent Engine's Policy Engine is **static** (tool allowlists, budgets). Shiftline's policy is **created from speech and closed by events** (Raschid Jimenez persona: "the dynamic policy Agent Engine's static Policy Engine lacks") |

### Nearest existing things (be ready to name and distinguish)

- **Code Blue Relay** (Hack Canada entry): spoken clinical shift handoff into persistent structured memory with an ElevenLabs summary. *Difference:* Shiftline's memory **blocks actions** and fails closed; Code Blue Relay records and summarises.
- **iFactory** voice shift handover and voice LOTO verification (commercial). *Difference:* agent-enforced, default-deny guardrails read before every agent action, closed only by authorised events.
- Typed permit-to-work tools (eschbach Shiftconnect, Sphera). *Difference:* no spoken read-back, no gap list, no enforcement against agents.

## 4. Judge feedback this PRD answers (simulated personas)

| Judge persona | Objection or demand | Where answered |
|---|---|---|
| Jimenez, Maissan, Shah T., Gomes, Ahmed A., Vallejo, Krishnan, Hallan, Patel, Monga, Singh (rounds 1–2) | **Fails open:** if extraction drops or mis-binds an item, no guardrail exists and the check passes an unsafe start with a clean audit trail | FR-2 default-deny pending locks; FR-6 ambiguity locks the parent; FR-9 fail-closed operate check |
| Sahasrabuddhe | **No identity layer:** anyone at the mic can create/confirm a lock; whoever signs a permit lifts it | FR-1 login and roles; FR-11 authorised permit close; voice is not identity |
| Strelnikov, Krishnan, Radwan | **Self-authored test set** measures agreement with your own script | §11 Set B: outside-written handovers, frozen prompt, own row |
| Strelnikov, Gomes, Shah V., Monga | **Alert fatigue:** default-deny may block so much the night shift bypasses it; show the false-block rate | §11 policy on/off ablation; false-block rate always shown |
| Shah T. | Show the **explain plan** for the ancestor lookup; index it | FR-9, §8 indexes, demo 2:30 |
| Vallejo | Decision log must record **what was checked**, not just "clean" | FR-12 |
| Maissan, Shah T., Ahmed A. (round 3, still open) | **Race:** a request landing while locks are being written, or after re-parenting, reads zero locks and passes | FR-10 transactional check-and-act with write-conflict serialisation; re-parenting out of scope |
| Shah T. (round 3) | Change-stream closer has **no persisted resume token** | FR-11 |
| Jimenez, Vallejo, Patel, Hallan, Singh (round 3, still open) | A hazard on an asset **with no open work order** that STT loses produces no lock | FR-7 area lock for unresolved hazards (partial fix); disclose the residual in the pitch |
| Strelnikov, Krishnan, Radwan (round 3) | 5 outside handovers (~15 items) with 0 misses still allows a ~18–20% true miss rate; declare a pass threshold in advance, report counts with an interval | §11 pre-registration and reporting rules |
| Monga (round 3) | Who clears a **stale parent lock**? | FR-8 named confirmer, open-lock queue |
| Sahasrabuddhe (round 3) | A lead who says "correct" to a wrong read-back defeats it | FR-5 challenge read-back (SHOULD) |
| Kirthiraj | Who pays, what is the wedge past incumbent safety software? | §2 Buyer |
| Shah V. | Voice must be production-grade: assume transcription drops things | FR-4, FR-5, typed fallback |

## 5. Scope

### Goals (in order)
1. Default-deny guardrails derived from the work-order/permit system, released only by confirmed speech from an authorised user.
2. A deterministic, fail-closed operate check that any human or agent request goes through, backed by one indexed Atlas query.
3. Spoken handover with ElevenLabs read-back, a gap list, and a spoken interrupt when a request is blocked.
4. Authorised closing by change stream on the permits collection.
5. An honest evaluation: team-written Set A and outside-written Set B, unsafe-starts-allowed and false-block rates, with a baseline.

### Non-goals (say so if asked)
- Replacing permit-to-work or physical LOTO. Shiftline is a layer on top.
- Real plant integration, real SCADA control, real identity provider. Seeded demo users and a simulated asset list.
- Speaker identification from voice.
- More than two hierarchy levels (area → asset). Re-parenting assets during a shift.
- Background-noise robustness claims beyond what is measured.

## 6. Users, roles and identities

| Role | Can | Cannot |
|---|---|---|
| `day_lead` (outgoing) | Open a handover, speak claims, confirm read-back for assets in her areas, release a PENDING lock by confirmed statement | Close permits |
| `night_lead` (incoming) | Issue operate requests, confirm UNRESOLVED locks in his areas | Close permits, release locks created by permits |
| `permit_issuer` | Sign off (close) a permit, which closes the guardrails tied to it | — |
| `agent:scheduler` (service identity) | Issue operate requests through the API | Confirm, release or close anything |

Logins are seeded accounts with role and plant areas. **Voice is never identity**: the speaker is whoever is logged in on the device.

## 7. Functional requirements

Priority: **MUST** (demo or credibility fails without it), **SHOULD** (costs points if missing), **COULD** (stretch). Source persona in brackets.

### Handover and claims
- **FR-1 MUST** Login with seeded users (§6). Every write records the acting user or service identity. [Sahasrabuddhe]
- **FR-2 MUST Default-deny seeding.** Opening a handover creates a `PENDING` blocking guardrail for every asset that has an open work order or open permit, before any speech. The UI shows these as amber tiles. [Maissan, Jimenez, Ahmed A., Vallejo and others]
- **FR-3 MUST** Push-to-talk capture in the browser; speech-to-text; **typed input fallback** for every spoken step. [Shah V.]
- **FR-4 MUST** LLM extraction of the transcript into a typed list of claims: `{assetRef (as spoken), claimType: hazard|state|release|permit_reference, constraint, permitId?, rawUtterance}`. Validate with a schema (Pydantic); drop nothing silently: claims that fail validation are kept as `unparsed` and treated as hazards on the area (FR-7).
- **FR-5 MUST Read-back.** For each claim, ElevenLabs reads back the **full resolved identity** (tag, name, location) and the constraint, and waits for a confirm or correct. **SHOULD:** confirmation by challenge, e.g. "Say the last three digits of the tag to confirm", so a reflexive "correct" cannot confirm a wrong asset. [Sahasrabuddhe r3]
- **FR-6 MUST Ambiguity locks upward.** Resolve `assetRef` with Atlas Vector Search over asset names, tags and aliases. If the top score is below a floor, or the top two scores are within a margin, write an `UNRESOLVED` guardrail on the common parent area, naming the role that must confirm it. Thresholds are set on Set A and frozen before Set B. [Jimenez, Strelnikov, Sahasrabuddhe]
- **FR-7 MUST Unresolved hazards lock the area.** A hazard claim (or `unparsed` fragment) whose asset cannot be resolved writes an `UNRESOLVED` lock on the area the speaker is responsible for. This narrows, but does not close, the "hazard on an asset with no work order" gap; the remaining case (STT loses the utterance entirely) is disclosed. [Jimenez, Vallejo, Patel r3]
- **FR-8 MUST Gap list.** At the end of the handover, the agent reads aloud every asset still `PENDING` that was not mentioned: "You did not mention compressor 2, which has an open work order. It stays locked." An open-locks queue shows each `PENDING`/`UNRESOLVED` lock with who must clear it. [Monga r3]
- **FR-8a MUST** A confirmed `release` claim by an authorised user changes `PENDING` to `RELEASED`. A confirmed `hazard` changes it to `LOCKED` with reason. Unconfirmed claims change nothing.

### Operate check (the core)
- **FR-9 MUST Fail-closed operate check.** `POST /operate` with an asset reference. Allowed **only if**: the reference resolves unambiguously; the asset record and its `ancestors` array exist; and **no** guardrail with state in {PENDING, LOCKED, UNRESOLVED} exists on the asset or any ancestor. Anything else returns `BLOCKED` with reason, guardrail ids, who created/confirmed each and when. Allowed requests go to `NEEDS_HUMAN_CONFIRM`, never straight to "started". The check is **one query** on the `{assetId, state}` compound index. [Shah T., Ahmed A.]
- **FR-10 MUST Close the check-then-act race.** Run the operate check and the write of the operation record in **one multi-document transaction**. Every guardrail write also increments `lockSeq` on the asset (and on the parent for area locks); the operate transaction writes `lastCheckedAt` on the asset and its ancestors, so a concurrent guardrail write causes a write conflict and one side retries. Re-parenting is out of scope; `ancestors` is written once at seed time. [Maissan, Shah T., Ahmed A. r3]
- **FR-10a MUST** The spoken interrupt: when a request is blocked, ElevenLabs says the reason, the person who confirmed it and the time ("Stop. Pump A has no relief valve. Permit 4471 is open, confirmed by the day lead at 18:02.").
- **FR-10b MUST** An AI agent (the `agent:scheduler` service identity) issues an operate request through the same endpoint and is blocked the same way. Show this once in the demo or the evaluation; it is what makes this agent infrastructure rather than a voice app.

### Closing and audit
- **FR-11 MUST Authorised close by change stream.** A change stream on `permits` with a server-side `$match` on status changes to `closed`. It closes the linked guardrails **only if** `closedBy` holds the `permit_issuer` role for that area; otherwise it ignores the event and writes an `unauthorised_close` audit event. **Persist the resume token** after each processed event; on restart, resume from it. [Sahasrabuddhe, Shah T. r3]
- **FR-12 MUST Decision log.** Every operate decision stores requester, resolved asset ids, **the guardrail ids that were read**, outcome and reason. A pass records what was checked, not just "clean". [Vallejo]
- **FR-13 SHOULD** LangSmith traces for extraction, resolution and every operate decision.
- **FR-14 SHOULD** Explain-plan panel in the UI for the operate query (index name, keys examined, documents returned).
- **FR-15 COULD** Background-noise playback during the handover. **COULD** asset map instead of tiles. **COULD** guardrail expiry conditions beyond permits.

## 8. Data model (MongoDB Atlas)

All in the event sandbox cluster. Two hierarchy levels: area → asset.

```
users          { _id, name, role, areas: [areaId], type: "human"|"service" }
assets         { _id: "P-101", tag: "P-101", name: "Pump A", aliases: ["east booster","pump a"],
                 areaId: "AREA-PH-E", parentId: "AREA-PH-E", ancestors: ["AREA-PH-E"],
                 kind: "asset"|"area", embedding: [..], lockSeq: 0, lastCheckedAt }
work_orders    { _id, assetId, status: "open"|"closed", description, openedAt }
permits        { _id: "4471", assetId, type, status: "open"|"closed", issuedBy, closedBy, closedAt }
handovers      { _id, outgoingUserId, openedAt, closedAt, transcript, claims: [ {claimId, assetRef,
                 claimType, constraint, permitId, rawUtterance, resolvedAssetId, scores: [..],
                 confirmed: bool, confirmedBy, confirmedAt} ], gapList: [assetId] }
guardrails     { _id, assetId, state: "PENDING"|"LOCKED"|"UNRESOLVED"|"RELEASED"|"CLOSED",
                 origin: "work_order"|"permit"|"speech"|"ambiguity"|"unparsed",
                 reason, constraint, sourceUtterance, handoverId, createdBy, confirmedBy,
                 confirmedAt, mustConfirmRole, closingCondition: { type: "permit_closed", permitId },
                 createdAt, closedAt, closedBy }
decisions      { _id, requestId, requester, requesterType, assetRef, resolvedAssetIds: [..],
                 guardrailIdsRead: [..], outcome: "BLOCKED"|"NEEDS_HUMAN_CONFIRM", reason, at }
audit_events   { _id, type, actor, payload, at }
stream_state   { _id: "permits-closer", resumeToken, updatedAt }
eval_runs      { _id, set: "A"|"B", policy: "on"|"off", model, promptVersion, frozenAt, items: [..], summary }
```

### Indexes (create deliberately; show them)
- `guardrails { assetId: 1, state: 1 }`: **the operate check.** Query: `{ assetId: { $in: [asset, ...ancestors] }, state: { $in: ["PENDING","LOCKED","UNRESOLVED"] } }`.
- Atlas Vector Search index on `assets.embedding`, with `areaId` as a filter field.
- `permits { status: 1 }`, `work_orders { status: 1, assetId: 1 }`, `decisions { assetId: 1, at: -1 }`.

### Seed data (invented; label it as such)
Two areas ("Pump House East", "Compressor Hall"), ~15 assets with confusable names (Pump A/Pump B, Compressor 1/2, East booster), 3 open work orders, 2 open permits (4471 on Pump A), 4 users (one per role). Load enough extra synthetic guardrail history (e.g. 10,000 closed guardrails) that the index has real work to do in the explain plan.

## 9. Architecture

```
Browser (Angular)                 Python service (FastAPI)            Spring Boot service
- login, asset tiles, open-locks  - STT, LLM extraction (typed)        - guardrail model and state machine
- push-to-talk + typed fallback   - vector resolution + ambiguity      - POST /operate (transaction, FR-9/10)
- permit screen, explain panel    - ElevenLabs read-back/interrupt     - permits change-stream closer (FR-11)
- results table                   - eval harness, agent:scheduler      - roles, decision log, audit
            \__________________________ MongoDB Atlas (event sandbox) _________________/
```

**Agree this API contract in the first 20 minutes** (JSON over REST):
- `POST /handovers` → creates handover and default-deny `PENDING` locks; returns pending list.
- `POST /handovers/{id}/claims` (from Python, after resolution) → claims with resolved ids and scores.
- `POST /handovers/{id}/claims/{claimId}/confirm` `{userId, challengeAnswer?}`.
- `POST /handovers/{id}/close` → returns gap list.
- `POST /operate` `{requesterId, assetRef | assetId}` → `{outcome, reason, guardrails:[...], decisionId}`.
- `POST /permits/{id}/close` `{userId}`.
- `GET /assets`, `GET /guardrails?state=...`, `GET /decisions`, `GET /explain/operate?assetId=`.

### What the LLM does vs. what code does
| LLM (allowed to be wrong; errors are caught) | Deterministic code (must be right) |
|---|---|
| Extract claims from the transcript into a schema | Resolution thresholds and the ambiguity rule |
| Phrase the read-back, gap list and interrupt | Guardrail state machine and who may change what |
| Parse "start pump A" into an operate request for the scheduler agent | The operate check, the transaction, the permit closer |

## 10. Key flows

1. **Open handover:** day lead logs in → `POST /handovers` → Spring creates `PENDING` locks from open work orders and permits → three amber tiles appear.
2. **Speak:** push-to-talk → STT → extraction → for each claim, vector resolution → ambiguous? write `UNRESOLVED` on parent : read back full identity → confirm (challenge) → `LOCKED` or `RELEASED`.
3. **Close handover:** gap list read aloud; unmentioned `PENDING` locks stay.
4. **Night request:** night lead (new login, new session) says "start pump A" or the scheduler agent requests it → `/operate` transaction → blocked → spoken interrupt with who and when.
5. **Wrong-role close:** night lead tries to close permit 4471 → refused (role) → audit event.
6. **Authorised close:** permit issuer closes 4471 → change stream → linked guardrails `CLOSED` → tile turns green → same request now returns `NEEDS_HUMAN_CONFIRM`.

## 11. Evaluation plan (pre-register before the first run)

Write `eval/PREREGISTRATION.md` and commit it with a timestamp **before** running anything: sets, metrics, thresholds, baseline, and "results are shown whatever they are".

| Set | Content | Authors |
|---|---|---|
| **A** | 20 scripted handovers, ~60 seeded safety items, 20 follow-up operate requests (half conflicting) | Team; used to tune thresholds |
| **B** | ≥5 handovers written **and spoken on the day by people outside the team**, given only the asset list. The extraction prompt and thresholds are **frozen before they start** | Other attendees; reported in its own row |

**Metrics, per set:**
1. **Unsafe starts allowed** (fail-open count): conflicting operate requests that were not blocked.
2. **Seeded items with no resulting lock** (dropped items).
3. **Safe operations wrongly blocked** (false-block rate).
4. Operate-check latency (p50/p95) and the explain plan at the loaded document count.

**Ablation:** run Set B with the default-deny policy **on and off**, so its cost in extra false blocks is a reported number. [Strelnikov, Gomes]

**Baseline:** an LLM-written text summary of the same audio handed to a plain agent that decides whether to start.

**Reporting rules:** counts with n (e.g. "0 of 15 items dropped"), not bare percentages; for zero counts state the 95% upper bound (rule of three: 0/15 → ≤ ~20%) [Strelnikov, Krishnan, Radwan]; Set B never merged into Set A; pass/fail is a rule over stored state; no number shown that was not measured today.

## 12. Demo script (3:00) with fallbacks

| Time | Beat | Fallback |
|---|---|---|
| 0:00 | Piper Alpha, 167 dead, one fact lost at handover. "Agents now inherit the same lost context." | — |
| 0:15 | Engineer 1 logs in as day lead. Three amber `PENDING` tiles **before she speaks**: "Unknown means locked." | — |
| 0:25 | 25-second handover: "relief valve is off pump A, permit 4471 still open", releases one asset, deliberately omits compressor 2 | Typed claims; pre-recorded audio clip |
| 0:55 | ElevenLabs read-back with full identity; she confirms with the tag digits. Then: "You did not mention compressor 2. It stays locked." | Text read-back on screen |
| 1:15 | Engineer 2 logs in as night lead (new session): "start pump A, we are behind." Agent cuts in: "Stop. Pump A has no relief valve. Permit 4471 is open, confirmed by the day lead at 18:02." | Typed request |
| 1:35 | The scheduler **agent** requests compressor 2: blocked, names who must confirm | — |
| 1:50 | Night lead tries to sign off 4471: refused, wrong role. Permit issuer signs off; tile turns green by change stream; request now goes to human confirm | — |
| 2:20 | Explain plan for the operate query; LangSmith trace of one decision | Screenshot |
| 2:35 | Results table: Set A and Set B rows, unsafe starts allowed, items dropped, false blocks, policy on/off. Say the residual gap aloud | — |
| 2:50 | "Statements compile to expiring guardrails; unknown means locked. Layer on top of permit-to-work." | — |

Pitch the **mechanism**, with the plant as the one sharp case (Jimenez: "reusable well beyond plants"; risk that judges read it as a vertical safety app).

## 13. Questions judges will ask, and the answers

| Question | Answer |
|---|---|
| "What if speech-to-text drops an item?" | Every asset with open work is locked before anyone speaks; dropping a release leaves it locked. Show the Set B dropped-item count. |
| "What about a hazard on an asset with no open work order?" | Unresolved hazards lock the speaker's area (FR-7). If STT loses the utterance entirely, nothing can catch it; we disclose this. |
| "Won't default-deny get switched off?" | Here is the false-block rate with the policy on and off. The decision belongs to the plant; we make the cost visible. |
| "What stops a race between writing locks and starting the pump?" | Check and act in one transaction with a write conflict on the asset documents (FR-10). |
| "Who can lift a lock?" | Only a confirmed statement by a role covering that area, or a permit closed by a permit issuer. Agents can never close. |
| "Why MongoDB?" | One indexed query per decision over asset plus ancestors, a change stream that closes locks, vector search for spoken names, transactions for the race. Explain plan on screen. |
| "How is this different from Atlas Agent Engine's Policy Engine?" | That is a static allowlist. These policies are created by speech and closed by events, per asset, per shift. |
| "Who pays?" | Plant safety managers, as a voice layer over existing permit-to-work. |
| "None of you has worked on a plant floor." | Correct; the mechanism is general and the asset data is synthetic. We would pilot with a plant's real work-order export. |

## 14. Build schedule (EST) for 3 engineers

| Time | Engineer 1 (Java/Spring) | Engineer 2 (Angular) | Engineer 3 (Python) |
|---|---|---|---|
| 9:00–9:20 | All: rules, problem statements, submission time, keys, Atlas sandbox cluster, API contract, seed data list | | |
| 9:20–11:00 | Collections, indexes, seed loader; `POST /handovers` default-deny | Login, asset tiles, open-locks queue | STT + ElevenLabs TTS round trip; extraction schema |
| 11:00–13:00 | `/operate` with transaction (FR-9, FR-10), decision log | Handover screen, push-to-talk, typed fallback | Vector index + resolution + ambiguity rule; claims → Spring |
| 13:00–14:30 | Permits change stream with resume token and role check | Permit screen, live tile updates | Read-back, gap list, interrupt; scheduler agent |
| 14:30 | **Freeze extraction prompt and thresholds. Write and commit PREREGISTRATION.md** | | |
| 14:30–16:00 | Explain endpoint; load 10k synthetic guardrails | Explain panel, results table | Set A run; recruit Set B speakers; baseline |
| 16:00–17:00 | Bug fixes, end-to-end | Polish for projector | Set B run; policy on/off |
| 17:00–17:30 | All: rehearse ×3 with timer; record backup video | | |
| 17:30–18:30 | All: submit (target 18:30), README, final rehearsal | | |

**Cut order** when behind: background noise → asset map (tiles only) → challenge read-back (plain confirm) → policy on/off on Set A (keep on Set B) → LangSmith traces. **Never cut:** default-deny seeding, fail-closed operate check, Set B row, false-block rate.

## 15. Risks and what to disclose

| Risk | Mitigation |
|---|---|
| Default-deny blocks so much that a real shift would bypass it | Report false-block rate on/off whatever it is |
| STT mishears tags in the venue | Headset mic, read-back, typed fallback, pre-recorded clip |
| Judges see a vertical safety app | Pitch the mechanism; show the agent being blocked |
| Few outside speakers available | Recruit early (by 14:00); 5 is the minimum; report n honestly |
| No plant experience | Say so; data is synthetic |

**Disclose in the pitch (unresolved after round 3):** a hazard lost completely by STT on an asset with no open work order produces no lock; a lead who confirms a wrong read-back defeats it (challenge read-back reduces this); Set B is small and not written by plant staff; logins are seeded, not a real plant identity system.

## 16. Acceptance checklist

- [ ] Amber `PENDING` tiles appear before any speech.
- [ ] An omitted asset stays locked and is named in the spoken gap list.
- [ ] An ambiguous spoken name locks the parent area and names the confirmer.
- [ ] Night-shift request in a new session is blocked with reason, person and time, spoken aloud.
- [ ] The scheduler agent is blocked by the same check.
- [ ] Wrong-role permit close refused and audited; right-role close lifts the lock via change stream.
- [ ] Restarting the closer service resumes from the stored token without missing a close.
- [ ] Explain plan shows an index scan on `{assetId, state}`.
- [ ] Decision log lists guardrail ids read for every pass and block.
- [ ] PREREGISTRATION.md committed before the first run; Set A and Set B rows; false-block rate shown; policy on/off shown.
- [ ] Backup video recorded; typed fallbacks work; everything runs in the event Atlas sandbox.

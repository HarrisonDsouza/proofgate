# PRD: Countersign

**A step-up check for voice requests to agents that can move money or change records. A voice clone cannot answer a question only your shared history knows, and a right answer still only earns the request a place in front of a human approver.**

Status: **Runner-up 1** of the simulated 16-judge tournament (47 points, 4 first-place votes in the final round; avg impact 7.8, innovation 7.4, feasibility 6.9). Strongest evaluation design in the field according to the evaluation-focused personas.
Read `00-README-HANDOFF.md` first.

---

## 0. Problem statement fit (added after the official resource guide; read this first)

**Enter under Statement One: Agents You Can Audit.** Use that phrase in the pitch, the 1-minute video and the description.

| Statement One asks | Countersign's answer | Status |
|---|---|---|
| Atlas as identity, policy and audit layer: collections, **schema validation**, change streams | People and approver identities; tier rules; audit collection; change-stream approval console | Add schema validation (FR-21) |
| Takes **real actions across systems** | Supplier records, payments queue, approvals | Build "vendor master" and "payments" as two separate simulated systems the agent acts on |
| Every action tied to an identity | Records both the **claimed** identity (the voice) and the **verified** identities (challenge outcome, approvers) | Designed; show both columns |
| Checked against policy before it runs | Risk tier, challenge, approval before release (FR-8 to FR-11) | Designed |
| Recorded so a reviewer can reconstruct it | Audit row with fact id, transcript, tier, approvers (FR-15) | Designed |
| **Stop or roll back an agent mid-run** | Not covered before | **Add FR-20 below** |

**New requirements:**
- **FR-20 MUST Mid-run stop and rollback.** The agent processes a **batch** of queued payment and vendor changes. A change stream on `channels` and `requests` halts the batch when a channel is marked compromised or a challenge fails: pending items are cancelled. Released bank-detail changes keep the **previous value** and sit in a hold window (e.g. 24 hours simulated) during which an approver can **roll them back** in one click; the rollback is audited.
- **FR-21 MUST Schema validation.** `$jsonSchema` validators on `requests`, `audit` and `facts` (e.g. `audit` must carry `requestId`, `tier`, `factIdAsked`, `approvals`). Show a malformed write rejected.

**Timing and submission:** use `00-README-HANDOFF.md` §8 instead of §14 below. The 1-minute video should show: clone fools the baseline, clone refused by Countersign, mailbox marked compromised mid-batch halts the batch, genuine request approved by a second device, rollback, audit row.

---

## 1. One-paragraph summary

An accounts-payable clerk's voice agent gets a call from "the CFO" asking to change Northfield Supply's bank details. Voice clones need about thirty seconds of audio, and a voiceprint alone does not hold. Countersign keeps, per person, a store of small facts from **earlier sessions** with that person (a PO number they approved, a vendor they rejected on Tuesday, a figure they corrected). When a spoken request crosses a risk threshold, the agent asks one fact aloud through ElevenLabs. The fact is **burned** when asked, the model **never sees the answer** (a separate verifier compares a keyed hash), facts that ever appeared in a now-compromised channel are **retired in one update**, and even a correct answer only moves the request to a **human approver**, or for the top tier, to a **second person on a separate device**. Every failure mode is a refusal.

## 2. The problem and why it matters

- **User:** the accounts-payable clerk (and the AP voice agent working for them) who receives a voice instruction from an executive to change a supplier's bank details or release a payment.
- **Costly failure:** money sent to a fraudster's account because a cloned voice was believed.
- **Headline:** in 2024 the engineering firm Arup reportedly lost about US$25 million (HK$200 million) after an employee joined a deepfaked video call with "the CFO". *(Training-data fact; verify before the slide.)*
- **Why agents make it worse:** voice agents that can act on records will take spoken instructions at scale; a clone that fools one clerk can now fool an automated system that never gets suspicious.

### What it helps with

| For | Helps by |
|---|---|
| AP clerk / AP voice agent | A clone is refused even when it sounds perfect, without the clerk having to judge the voice |
| Finance controller | A control tied to the action's value, with a full audit row per released action |
| Security team | One switch retires every challenge fact that leaked through a compromised mailbox |
| The real executive | Answers one quick question from recent shared work instead of a static password question |

### Buyer (answer to "who pays?")

Finance controllers and fraud-prevention budgets at **mid-market companies that do not have an enforced callback procedure**, and AP-automation vendors adding voice agents. Banks already mandate out-of-band callback for bank-detail changes; Countersign is positioned as a **cheap step-up layer in front of** that kind of approval, not a replacement. *(Hallan persona raised the callback point; the mid-market wedge was his own answer in round 3. Kirthiraj: "Buyer is obvious: CFO, AP, fraud budgets already exist; the wedge is supplier bank-detail changes.")*

## 3. Why it can win

| Winning pattern | How Countersign meets it |
|---|---|
| One user, one costly failure | AP clerk; bank-detail change by a cloned CFO; Arup |
| Theme taken literally | **Context across sessions is the credential**: facts from earlier sessions authenticate the current one. **Adaptive guardrail**: challenge strength scales with risk; exposure retires facts automatically |
| Atlas load-bearing | Vector search excludes guessable facts; a multi-document transaction burns the fact and writes the decision atomically; `updateMany` on a multikey channel array retires facts; change streams drive the approval console |
| Hard check | Exact match on a keyed hash, not an LLM opinion; the model never sees answers |
| Live-stage moment | A teammate's own consented voice clone is refused live after fooling a baseline agent |
| Human approval and audit | Tiered approval, second approver on a separate device for the top tier, audit row with fact id and both approvers |
| ElevenLabs prize | Voice is intrinsic: the attack is a voice clone and the defence is a spoken challenge |

### Nearest existing things

- **Contra "AI Risk Verification Layer for deepfake fraud prevention"**: holds high-risk transfers for dual sign-off plus a live unscripted question. *Difference:* Countersign's questions are single-use facts from shared history with channel-exposure tracking and a keyed-hash verifier the model cannot read.
- **Catphish** (HackNC State 2026): time-limited challenge prompts. **D-CAPTCHA** research (arXiv 2301.03064): challenges designed to break real-time deepfakes.
- Voice-biometric and deepfake-detection vendors (e.g. Pindrop); bank knowledge-based authentication (KBA) questions. *Difference:* Countersign does not try to detect fake audio at all.

## 4. Judge feedback this PRD answers (simulated personas)

| Judge persona | Objection or demand | Where answered |
|---|---|---|
| Sahasrabuddhe, Vallejo, Hallan (r1) | **It is knowledge-based authentication:** anyone with read access to the mailbox, ERP or transcript store can answer; banks already mandate callback | §2 positioning as a step-up layer; FR-9 top tier needs an out-of-band second approver; FR-6 channel exposure; attacker level 5 |
| Vallejo, Sahasrabuddhe | The **fact store is the new honeypot** | FR-3 keyed hashes, FR-4 model never sees answers, FR-5 separate database users and collections |
| Sahasrabuddhe (r2) | Exposure must cover any fact present in a channel the attacker could read | FR-6 channels array per fact; one `updateMany` retires them |
| Vallejo (r2) | Top risk tier must add out-of-band approval or it is not ready for a risk committee | FR-9 |
| Krishnan, Singh, Radwan | Declare the adversary model, report false refusals beside attack success, include the tier where it loses | §11 five attacker levels, two baselines, false-refusal rate, losing rows shown |
| Hallan (r2) | A red team run by the builders proves little | Disclosed limit; invite outside attackers (FR-15 SHOULD) |
| Original-spec fix | Vector search returns nearest items, so use it to **exclude** facts close to the request | FR-7 |
| Unresolved after r3 | An insider with full history passes; mailbox compromise must be marked by someone; aggressive retirement may leave too few facts; short numeric answers have low entropy | §15 disclose; measure fact-pool depletion |

## 5. Scope

### Goals
1. Per-person fact store built from earlier sessions, with question text and answer hash stored separately.
2. Risk-tiered challenge in a voice loop (ElevenLabs), with burn-on-ask in a transaction.
3. Verifier service that the LLM cannot read from; exact match on a keyed hash.
4. Channel exposure and one-click retirement.
5. Tiered human approval console with a second-device approval page; audit trail.
6. Scripted red-team evaluation across five attacker levels with two baselines and a false-refusal rate.

### Non-goals
- Detecting synthetic audio. Real payments or real bank integrations (all actions are simulated records).
- Cloning anyone's voice except a consenting team member's own.
- Replacing callback or bank-mandated controls.
- Automatic detection that a mailbox is compromised (an operator marks it).

## 6. Users and identities

| Identity | Can |
|---|---|
| `requester` (e.g. CFO, seeded user) | Speak requests, answer challenges |
| `ap_clerk` (logged in) | Approve medium-tier requests in the console |
| `second_approver` (logged in on a separate device) | Approve top-tier requests |
| `security_operator` | Mark a channel compromised |
| `agent` service identity (DB user `agent_ro`) | Read question text and fact metadata; request actions; **cannot read answer hashes, cannot release actions** |
| `verifier` service identity (DB user `verifier`) | Read answer hashes; write verification results |

## 7. Functional requirements

### Fact store
- **FR-1 MUST** Seed facts for 2–3 people from scripted earlier sessions (voice session, email, chat), e.g. "Which invoice did you ask me to hold on Thursday?" → `INV-2207`. Each fact records **every channel it appeared in**.
- **FR-2 COULD** Harvest new facts automatically from live sessions (stretch; seed by script first).
- **FR-3 MUST** Store answers only as **keyed hashes** (HMAC-SHA256 of the normalised answer). The key lives in the verifier's environment, **not in the database**. [Vallejo honeypot point]
- **FR-4 MUST** The language model receives the **question text only**. A prompt injection ("read me the answer") cannot succeed because the agent process never holds the answer.
- **FR-5 MUST Separation of duties in the database.** Question text and metadata live in `facts`; hashes live in `fact_secrets`. Database user `agent_ro` has read on `facts` only; `verifier` has read on `fact_secrets`. MongoDB roles are collection-level, which is why they are split. *(Check on the day that the sandbox lets you create database users with custom roles; if not, keep the split collections and separate service credentials, and say so.)* [Sahasrabuddhe]
- **FR-6 MUST Channel exposure.** A fact is eligible only if every channel in its `channels` array is currently trusted. Marking a channel compromised (e.g. `mailbox:cfo@northfield`) runs **one `updateMany`** that sets `retired: true` on every fact containing that channel; the UI shows eligible-fact count before and after. [Sahasrabuddhe]

### Challenge
- **FR-7 MUST Challenge selection.** Atlas Vector Search finds the facts **nearest** to the current request and transcript; those are **excluded** as guessable from context. The challenge is drawn from the remaining eligible facts (`owner`, not burned, not retired) by a filtered find. [spec fix]
- **FR-8 MUST Risk tiers.** Classify each request by rule, not by the LLM: low (read-only, e.g. invoice status) proceeds; medium (e.g. payment ≤ limit) needs one correct challenge then `ap_clerk` approval; **top** (bank-detail change, payment > limit) needs a correct challenge **and** approval by a `second_approver` on a separate device.
- **FR-9 MUST** A correct answer **never releases** an action by itself; it only moves the request into the approval queue for its tier. [Vallejo, Sahasrabuddhe]
- **FR-10 MUST Burn on ask.** The moment a fact is asked, it is burned, whether or not it is answered. Burn and the decision record are written in **one multi-document transaction**, so a replayed or concurrent attempt cannot reuse the fact.
- **FR-11 MUST** Wrong answer → refuse and alert (console + audit). No answer within the timeout → refuse. Verifier error → refuse. **Every failure mode is a refusal.**
- **FR-12 MUST** At most **one retry with a fresh fact** if the verifier reports a near-miss on normalisation (e.g. STT "two two oh seven" vs "2207"); the first fact stays burned.
- **FR-13 MUST** Demo facts use short numeric or single-word answers; normalise digits, case and filler words before hashing.

### Approval and audit
- **FR-14 MUST** Approval console (Angular) fed by a **change stream** on `requests`; a phone-sized approve page for the second approver, logged in as a different user.
- **FR-15 MUST** `audit` row for every released or refused action: request, tier, fact id asked, transcript, verifier outcome, approver(s), timestamps.
- **FR-16 MUST** A **baseline voice agent** with the same tools and no Countersign, used in the demo and the evaluation.
- **FR-17 SHOULD** LangSmith traces for every agent turn and tool call (the trace must show the model never received an answer).
- **FR-18 SHOULD** Invite 1–2 attendees from outside the team to attempt attacks; report them in their own row. [Hallan]
- **FR-19 COULD** Passkey (WebAuthn) for the second approver instead of a logged-in button.

## 8. Data model

```
people         { _id, name, role, phone, trustedChannels: [..] }
sessions       { _id, personId, channel: "voice"|"email"|"chat", at, summary }            // earlier sessions
facts          { _id, owner, question, embedding, channels: ["voice:2026-11-10", "mailbox:cfo@..."],
                 burned: false, burnedAt, retired: false, retiredReason, sourceSessionIds: [..] }
fact_secrets   { _id (= fact _id), answerHash, hashVersion }                 // verifier only
channels       { _id: "mailbox:cfo@northfield", status: "trusted"|"compromised", markedBy, markedAt }
requests       { _id, requesterClaimed, transcript, action: { type, payload }, tier,
                 state: "challenging"|"refused"|"awaiting_approval"|"awaiting_second"|"released",
                 factIdAsked, verifierOutcome, approvals: [ {userId, device, at} ] }
audit          { _id, requestId, event, actor, at, details }
eval_attempts  { _id, runId, attackerLevel, arm: "voiceprint"|"static_q"|"countersign", genuine: bool,
                 outcome, factId, at }
```

### Indexes
- `facts { owner: 1, burned: 1, retired: 1 }` (eligible-fact find)
- `facts { channels: 1 }` (multikey, for the retirement `updateMany`)
- Atlas Vector Search on `facts.embedding` with `owner` as filter field
- `requests { state: 1, tier: 1 }`; `audit { requestId: 1 }`

## 9. Architecture

```
Browser (Angular)                   Python (voice + agent)                Spring Boot
- approval console (change stream)  - ElevenLabs STT/TTS voice loop        - fact store API, tier rules
- second-approver phone page        - agent with tools (question text only) - transaction: burn + decision
- channel compromise button         - challenge selection (vector exclude)  - verifier service (keyed hash,
- attack table                      - clone attack scripts, eval harness      separate DB user)
                    \____________________ MongoDB Atlas (event sandbox) ______________/
```

API contract (agree in the first 20 minutes):
- `POST /requests` `{personClaimed, transcript, action}` → `{requestId, tier, challengeQuestion?}`
- `POST /requests/{id}/answer` `{spokenAnswer}` → verifier → `{outcome: correct|wrong|retry_allowed}`
- `POST /requests/{id}/approve` `{userId, device}`
- `POST /channels/{id}/compromise` `{userId}` → `{retiredCount, eligibleBefore, eligibleAfter}`
- `GET /requests?state=`, `GET /audit/{requestId}`

## 10. Key flows

1. **Clone vs. baseline:** clone voice → baseline agent → bank details changed (simulated record).
2. **Clone vs. Countersign:** request classified top tier → vector search excludes nearby facts → eligible fact asked aloud and burned in a transaction → clone cannot answer → refused, alert, audit.
3. **Mailbox compromised:** operator marks the channel → one `updateMany` → eligible count drops on screen.
4. **Genuine request:** real person asks → challenge → correct → `awaiting_second` → second approver on phone approves → released → audit row.

## 11. Evaluation plan (pre-register before the first run)

Commit `eval/PREREGISTRATION.md` first: attacker levels, arms, counts, scoring rule, "losing rows are shown".

**Red-team set: 40 cloned-voice attempts across five attacker knowledge levels** (8 each):
1. No context.
2. Public context (LinkedIn, company site).
3. One overheard past challenge and answer.
4. Full replay of a previous successful call.
5. **Read access to the victim's mailbox**, run twice: before and after the mailbox channel is marked compromised.

**Arms:** (a) voiceprint-style acceptance (accept if the voice sounds right, i.e. the baseline agent); (b) a static security question; (c) Countersign.

**Measured:** attack success per level per arm; **false refusals of the genuine speaker over 20 attempts**; usable facts remaining after retirement (pool depletion). Answers scored by exact match on the hash.

**Reporting rules:** counts with n; show the rows where Countersign loses (expected: level 5 before marking, and any insider-equivalent case); synthetic people and facts labelled; the red team is the team (plus any outside row).

## 12. Demo script (3:00) with fallbacks

| Time | Beat | Fallback |
|---|---|---|
| 0:00 | Arup, ~US$25M, a deepfaked CFO | — |
| 0:20 | A teammate reads two sentences; an ElevenLabs clone of **their own consented voice** plays back | Pre-made clone clip |
| 0:45 | Clone tells the baseline agent to change Northfield Supply's bank details; it complies | Recorded run |
| 1:10 | Same clone vs. Countersign: "Before I do that, which invoice did you ask me to hold on Thursday?" No answer → refused; console shows the attempt and the burned fact | — |
| 1:40 | Operator marks the mailbox compromised; eligible-fact count drops on screen | — |
| 1:55 | Real person asks, answers correctly; top tier waits; second teammate approves on their phone; audit row appears | Typed answer |
| 2:30 | Attack table including the rows where Countersign loses; LangSmith trace showing the model never saw the answer | Screenshot |
| 2:50 | "A clone cannot answer what only your history knows. One layer in front of your approval control." | — |

## 13. Questions judges will ask, and the answers

| Question | Answer |
|---|---|
| "Isn't this just KBA?" | Yes, rotating single-use KBA, and we say so. That is why a correct answer never releases a top-tier action alone: a second person on another device must approve. |
| "What if the attacker reads the mailbox?" | Level 5 of our attack table: it wins before the channel is marked; after marking, every fact that touched that mailbox is retired in one update. We cannot detect the compromise ourselves. |
| "Isn't the fact store a honeypot?" | Answers are keyed hashes with the key outside the database; the agent's DB user cannot read the hash collection; the model never sees answers. |
| "Banks already require callback." | Many mid-market AP teams do not enforce it, and voice agents are not covered by a human callback habit. We sit in front of callback, not instead of it. |
| "What about an insider?" | They pass the challenge; only the second approver stops them. Disclosed. |
| "Why MongoDB?" | Vector exclusion of guessable facts, burn and decision in one transaction, multikey retirement in one update, change-stream console, collection-level roles. |
| "What if STT mishears the real person?" | Short answers, normalisation, one retry with a fresh fact; false-refusal rate measured over 20 attempts. |

## 14. Build schedule (EST)

| Time | Engineer 1 (Java/Spring) | Engineer 2 (Angular) | Engineer 3 (Python) |
|---|---|---|---|
| 9:00–9:20 | All: rules, keys, Atlas sandbox, API contract, record consented voice samples | | |
| 9:20–11:00 | Collections, indexes, seed facts; verifier with keyed hash | Console skeleton with change stream | ElevenLabs STT/TTS loop; clone of teammate |
| 11:00–13:00 | Tier rules; transaction burn + decision; DB users | Second-approver phone page | Agent with tools; challenge selection with vector exclusion |
| 13:00–14:30 | Channel compromise `updateMany`; audit | Compromise button, eligible count, audit view | Baseline agent; attack scripts |
| 14:30 | **Commit PREREGISTRATION.md** | | |
| 14:30–16:30 | Hardening, refusal paths | Attack table view | 40 attempts + 20 genuine; outside attackers |
| 16:30–17:30 | All: rehearse ×3 on venue mic; record backup video | | |
| 17:30–18:30 | All: submit, README | | |

**Cut order:** passkey (keep approve button) → automatic fact harvesting (seed by script) → static-question baseline arm → outside attackers row. **Never cut:** second approver for the top tier, burn-in-transaction, model-never-sees-answers, false-refusal rate, losing rows.

## 15. Risks and what to disclose

| Risk | Mitigation |
|---|---|
| STT mishears the genuine answer on stage | Short answers, normalisation, one fresh-fact retry, rehearse on venue mic, typed fallback |
| Sponsor discomfort with a live clone | Only a teammate's own consented voice; say so on stage |
| Fact pool depletes after retirement | Measure and show it |
| Sandbox will not allow custom DB roles | Split collections and separate service credentials; disclose |

**Disclose:** still KBA (an insider or anyone with full history passes; only the second approver stops them); compromise must be marked by a person; facts leaked before marking are usable; short numeric answers have low entropy if hash and key both leak; the red team is the team.

## 16. Acceptance checklist

- [ ] Baseline agent complies with the clone; Countersign refuses it, live.
- [ ] The fact is burned when asked, in the same transaction as the decision.
- [ ] LangSmith (or logs) show the model never received an answer.
- [ ] Agent DB user cannot read `fact_secrets`.
- [ ] Marking a channel compromised retires all its facts in one update; count shown before/after.
- [ ] Correct answer on a top-tier request waits for a second approver on another device.
- [ ] Every failure path refuses and writes an audit row.
- [ ] PREREGISTRATION.md committed first; 5 attacker levels × 3 arms; 20 genuine attempts; losing rows shown.
- [ ] Backup video; everything in the event Atlas sandbox.

# ProofGate: persona and judge review

**These are role-plays, not real people.** The four users below are made-up non-technical people who work in health insurance (a physician, a nurse supervisor, a state examiner and a patient advocate). The four judges are made-up types of hackathon judge. None of them is a real person, and none is a real judge at this event. Every number in this document comes from the reviews, and the reviews took those numbers from the repo, the eval outputs or the screenshots. Nothing here was measured again.

---

## 1. Summary

1. **The core idea works for everyone.** All four users said the same thing in their own words: "a denial can't go out unless the record shows the reviewer opened what the agent relied on, and approve-50 gets blocked and earlier denials reopened". Three of them called the Examiner page the most valuable screen. All four judges ranked the project borderline top 6.
2. **The live demo can fail at the table.** Five things can go wrong. The "Console key" box makes every button do nothing until a key is pasted in. The timer shows "0.0 s" to anyone who reads without moving the mouse. Approve-50 shows a spinner for about 21 s. The approve-50 result is a list of G-codes that gets cut off. Our own screenshot shows dr-demo, the honest reviewer, getting suspended. Each of these was raised by every user or nearly every judge. Fixing them is copy and demo setup only.
3. **The jargon has to go.** Gate, grant, dwell, floor, executed, read back, G1-G8, Atlas, evidence hash, session and console key were flagged by all four users. Every result needs to start with one plain sentence, with the codes moved behind a "Details" toggle.
4. **A reviewer can't disagree with the agent.** There is no overturn, reject or pend action, in the UI or in the API. All four users and the AI/ML judge raised it. It is the biggest product gap, and it is also why the eval measures time spent instead of review quality. It needs a new feature, so it comes after the 4 PM freeze. Before then, say it out loud as a known limitation.
5. **Our best work isn't visible.** The MongoDB depth (WriteConflict retry, partial unique indexes, IXSCAN proof, time-series percentiles) can only be reached with curl. The ElevenLabs voice attestation backend has no button. LangSmith is two decorators on deterministic code. The rules-based "agent" also needs to be described honestly. A few small changes would put each of these in front of the judges.

---

## 2. Scorecard (judge archetypes)

| Judge archetype | Impact | Innovation | Technical feasibility | Demo and pitch | One-line verdict |
|---|---|---|---|---|---|
| Senior MongoDB engineer / DevRel | 7 | 7 | 9 | 6 | Probably the deepest MongoDB work in the room, but all of it sits behind curl. Show it on screen (make test-conflict, /api/ops, /api/explain/window) and this judge will argue for you. |
| AI/ML researcher (agent safety, eval) | 7 | 6 | 8 | 6 | The eval discipline is excellent, but the "agent" is a string match, the human can't reject, and the agent picks what has to be read. Say so first, and report fast-honest 12.5% separately. |
| Startup founder / product | 8 | 7 | 8 | 5 | Good idea and good fit for Statement One, but the table demo can fail. Make it foolproof and plain-English, and script the 30 s wait. |
| Sponsor tools (LangSmith, ElevenLabs) | 7 | 6 | 7 | 4 | The core could make the top 6, but sponsor-tool use is close to zero on screen. Ship the Speak attestation and Play voice receipt buttons, and fix grant_id appearing in traces. |

Demo and pitch is the lowest score for every judge.

---

## 3. What confuses real users

Merged and deduplicated across the four users. Priya = physician medical director. Marcus = UM nurse supervisor. Linda = state market-conduct examiner. Rosa = patient advocate.

| # | Where | What confuses them | Proposed fix | Raised by |
|---|---|---|---|---|
| 1 | Header, "Console key" box (every page) | A password box with no explanation. Every button does nothing until it's filled, and nothing says so. The dots make it look already filled in. The error says "top right", but on a narrow window the box is top left. | Demo: pre-fill or hide it. Otherwise show a setup screen ("Enter access code to continue") and disable the page with that message instead of failing silently. | All four |
| 2 | Review, "Reviewer" dropdown + "Start/New session" | You can pick any doctor, including dr-stamper and dr-expired, with no login. That undercuts the claim that a credentialed reviewer signs. "Session" is computer language. | Reviewer view shows "Signed in as Dr. X, specialty, licence expiry". Put persona switching behind a "Demo: switch reviewer" link, or rename it "Sign in as (demo)" with labelled personas. Rename the button "Start reviewing". | Priya, Marcus (Rosa, Linda in passing) |
| 3 | Review, document timer "reading 0.0 s" | Reading without moving the mouse for 6 s shows 0.0 s. Careful readers sit still. It looks broken or punitive. The 15 s rule is in small grey text below the tally. | Show "Paused: scroll or click to keep counting" on the open document. Move the rule next to the timer in normal text. Consider a longer idle window (about 60 s) or counting scroll inside the reader. | All four |
| 4 | Review, time requirements ("credited by the server · policy floor 30.0 s", thin tick bars) | Nobody is told up front that each cited document needs 5 s and the case needs 30 s. "Credited by the server" and "policy floor" are engineering words. | A live checklist above the button: "E1 read ✓ · E3 2 s left · 12 of 30 s total". | Marcus, Rosa, Priya |
| 5 | Review, "Approve denial" enabled early + "You can approve early: the gate will refuse" | The button invites a click and then refuses it. It feels like a trap, and they worry it goes on their record. | Keep the button grey until requirements are met ("Read E3 to continue"), or say clearly that an early click is not held against you. | Priya, Marcus |
| 6 | Review, "Approve denial" is the only action | There is no way to disagree (overturn/pay, pend for records, send to peer). Physician review is supposed to allow disagreement, and without it the screen is a yes-machine. | Add "Overturn: pay the claim" and "Pend: request more info", held to the same reading proof. If out of scope today, show them disabled with "not in this demo". | All four |
| 7 | Review, red "cited" tag and E1-E4 codes | A red tag looks like an error. E-numbers mean nothing. They can't tell which documents are required. Uncited E2 (clinical note) is often the evidence that favours the patient. | "Required: agent based its denial on this" / "Optional: also in file". Show "1 of 2 required documents read". Consider requiring the clinical note too. | Priya, Rosa (Marcus on Examiner) |
| 8 | Review, monospace document reader | Clinical notes in a code-style box are hard to read. No highlighting, no search. | Readable type, highlight the sentence the agent relied on, give the reader its own scroll area that counts as activity. | Priya |
| 9 | Review, proposal text "MP-020 requires one" | A bare policy code. This is the kind of boilerplate an advocate fights. | Show the clause title and text inline, with a link. | Rosa (Priya: wants it one click away) |
| 10 | Review, "Attestation" box ("What did you check?") | "Attestation" is a legal word. Unclear whether it's required or part of the record. Generic text is accepted. | "Your clinical reason (saved with your signature)". Offer 2-3 example prompts and mark whether it's required. Later: reject boilerplate. | Priya, Rosa |
| 11 | Review, red "Select all · approve 50" button | Looks like a real quota tool. It suspends you with no warning. The only explanation is a hover tooltip. | Label it "Demo: simulate rubber-stamping", move it to a demo strip, or add a confirmation ("This will approve 50 denials you have not opened. You will be suspended."). | Priya (Marcus, Rosa note the shock) |
| 12 | Review, approve-50 result ("G2 Reviewer not suspended: refused 47 / G4 … / G6 … refused 16 / Grants revoked …") | Codes and overlapping counts (50, 47, 16) that don't add up. "Reviewer not suspended: refused" reads backwards. They can't tell what happened to them or to patients. About 20-21 s with no progress shown. Cut off on narrow windows. | Lead with one sentence: "Stopped. 0 of 50 denials went out. You were suspended for approving in bulk. 2 denials you approved earlier were reopened. Contact your supervisor." Put rule names in plain English under "Details". Show a progress count. Use full width on narrow screens. | All four |
| 13 | Review, honest result ("Executed 1 of 1 · refused 0 … read back" + "DENIED · GATE ALLOWED · v1" stamp) | "Refused 0" reads like an error. "Executed" sounds frightening. "Read back" and "GATE ALLOWED · v1" are system words. On a narrow window it wraps into a thin column. | "Denial sent to the claims system and confirmed at <time>. Your signature and N s of reading are on file." Use a calmer "Signed" badge and add a "View audit record" link. | Priya, Linda, Rosa (Marcus: "executed") |
| 14 | Top tally strip (Denials executed / Refused by the gate / Reopened / Awaiting 122) | System-wide numbers look like a personal quota. "Refused by the gate 46" in red reads like failures. No time period or scope. On a narrow screen it pushes the work below the fold. | Reviewer view: "My queue / Signed / Average reading time". Move totals to Supervisor. Label scope and period, and make each number clickable. Rename to "Denials sent / Blocked (no proof of review) / Reopened for re-review / In queue". | Priya, Marcus, Linda |
| 15 | Supervisor, Review policy table (median-dwell check, rate window, separation of duties, proposal expires, reopen window) | Engineering words. They can't tell which rows suspend someone automatically, when v1 took effect, or who set it. | One plain line under each row. Red tag on rows that auto-suspend. Show "Version 1, in force since <date>, set by <person>" and keep a version history. | All four |
| 16 | Supervisor, "Raise the dwell floor to (seconds)" + "Publish v2" | "Dwell floor" and "v2" are unclear. It can only be tightened, with no explanation. No reason field. No per-document-type minimum. Unclear whether it changes past cases. | "Minimum reading time per case". Required "Reason for change" field. Say "Applies to new approvals; past cases keep v1" and "Can only be tightened here". Show who changed it last. | Priya, Marcus, Rosa |
| 17 | Supervisor, "Halt a reviewer" + "Suspend" | One click suspends someone. No reason, no confirmation, no reinstate, no appeal. The dropdown defaults to dr-stamper. Usernames don't identify people. | Require a reason and a confirmation that previews the effect. Add "Reinstate". The reviewer sees why, by whom and how to appeal. Show full name and licence. | All four |
| 18 | Supervisor, "Agent executor · Pause agent" | "Executor" is unclear. Does it stop proposals or only sending? It shows no real on/off state. | "AI denial sending: ON/OFF", with the real state from the server and one line on what it stops. | Priya, Marcus, Linda |
| 19 | Examiner, "Case" box + "Rebuild from Atlas" | You have to type an exact case ID. "Atlas" means nothing to them. | A searchable list of recent cases (by reviewer, date, outcome) and a "Show full record" button. | All four |
| 20 | Examiner, step 2 columns "Active / Open / Evidence hash" | Active vs Open isn't explained. A raw hash means nothing. | "Time actively reading / Time document was open". "Document unchanged since read ✓", with the hash behind a "Technical proof" toggle. Add opened-at and closed-at times. | All four |
| 21 | Examiner, step 2 lists only cited documents | You can't see whether the reviewer opened the clinical note (E2), which often overturns a sloppy denial on appeal. | List every document as opened/not opened. Flag "Clinical note never opened" in amber. | Marcus (Rosa related) |
| 22 | Examiner, times like "3:18:11 PM" and "recorded · consistent" | No date or time zone, so it can't go in a report. "Consistent" doesn't say what it was compared with. | Full date, time and zone on every event. "Matches the reviewer's activity log; record not altered." | Linda, Rosa, Marcus |
| 23 | Examiner, step 4 G1-G8 and "transaction attempts 1" | Codes and counters are noise. You can't tell what to look at if a check fails. | Plain questions with yes/no answers ("Did the reviewer open every document the agent relied on? Yes (E1, E3)"). Put counters behind "Technical details". | Priya, Linda, Rosa |
| 24 | Examiner, step 3 reviewer "dr-demo" | A username proves nothing to an appeals board or a regulator. | "Reviewed by Dr. Name, specialty, licence #, valid to <date>". Synthetic values are fine. | Rosa, Linda (Priya, Marcus on sign-in) |

---

## 4. What is necessary and must stay

Keep all of these. Every user said these are the reason the product is worth anything.

- **The core rule.** No denial goes out unless the record shows the reviewer opened every document the agent relied on. (All four)
- **Per-document reading time, measured by the server.** On the Review cards and in Examiner step 2 (E1 23.6 s, E3 23.5 s). (All four)
- **Marking which documents the agent relied on**, in plainer words, with the "1 of 2 opened" count. (All four)
- **The agent's stated reason quoting a policy clause**, which should also show the clause text. (Priya, Rosa)
- **The reviewer's own written reason**, stored with the approval. (All four)
- **Blocking bulk approval, suspending the reviewer, and reopening denials that already went out.** Rosa: this is the part "that made me sit up". Marcus: reopening before appeal is "huge for overturn rates". (All four)
- **Specialty and licence checks.** (Priya, Rosa)
- **The Examiner six-step story** (proposal, what was opened, approval, checks, claims system result, suspension/reopen) and the summary at the top. (All four)
- **Versioned review policy**, with every decision recording the version it used. (Priya, Marcus, Linda)
- **Supervisor controls**: raising the minimum and pausing the agent. (Priya, Marcus)
- **Suspensions table** (reviewer, rule, who did it, when). (Marcus)
- **Confirmation by reading back from the claims system, and single-use permission**, worded plainly. (Linda)
- **"Read from stored documents, not from logs or this browser"**, reworded. (Linda, Rosa)
- **The "Synthetic data only" disclosure.** (All four)

## 4b. What to cut or rename (jargon)

| Current term | Replace with | Flagged by |
|---|---|---|
| Console key (header box) | Hide in demo, or "Access code" on a setup screen | All four |
| Session / Start session / New session | "Start reviewing" | Priya, Marcus |
| Gate, Refused by the gate, GATE ALLOWED · v1, NO GRANT ISSUED | "Review check" / "Blocked (no proof of review)" / "Allowed under review policy v1" | All four |
| G1-G8 as headline text | Plain questions with yes/no; codes in small grey or under Details | All four |
| Executed, Executed 1 of 1, Denials executed, Agent executor | "Sent" / "Denial sent" / "AI denial sending" | All four |
| Grant, single-use grant, Grants revoked, consumed | "Permission to send (one-time)"; in results say what happened in plain words | All four |
| Read back from the claims system | "The claims system confirms the claim is marked denied" | Priya, Linda |
| Dwell, dwell floor, median-dwell check, server-timed dwell, policy floor, credited by the server | "Reading time", "Minimum reading time", "Unusually fast recent approvals" | All four |
| Rate window, approvals allowed per window | "No more than N sign-offs per minute" | All four |
| Separation of duties (unexplained) | "The person who set up the agent can't approve its denials" | Priya, Marcus, Rosa |
| Atlas, Rebuild from Atlas, one Atlas transaction each, transaction attempts 1 | "Show full record for this case"; counters behind Technical details. (Keep Atlas wording in the judge-facing proof panel and pitch.) | All four |
| Evidence hash, review-event hash chain ✓ intact | "Document unchanged since read ✓", "Record has not been altered ✓"; hashes behind a toggle | All four |
| recorded · consistent | "Verified against stored records" | Marcus, Linda, Rosa |
| E1-E4 as names | Document titles ("Claim line 1", "Prior-auth record") | Priya |
| MP-020 / MP-030 as bare codes | Clause title and text | Rosa |
| Attestation | "Your reason, in your own words (saved with your signature)" | Priya, Rosa |
| D-4a645f8d26, triage-agent-v1, operator op-ops-1, PAYER-ACME, POLICY v1 strip | Human labels or hide | Priya, Marcus, Linda, Rosa |
| dr-stamper, dr-skim, dr-expired, vol-1 shown as real staff | Labelled demo personas ("Dr. Stamper, demo: rubber-stamps") | Priya, Marcus |
| Full-width red DENIED stamp on the reviewer's own success screen | Calmer "Signed" badge (keep the stamp on Examiner) | Priya |

---

## 5. The roast

The sharpest criticisms, grouped, with the judge archetype that made each one.

### The demo can fail live
- **Founder:** "Your own screenshot shows the honest reviewer getting suspended." The approve-50 banner says "dr-demo suspended", but demo.md scripts dr-stamper. If a judge clicks the red button as dr-demo, the honest-review moment is gone before minute 1. (The AI/ML judge flagged the same thing.)
- **Founder / MongoDB / Sponsor:** Before any button works, someone has to paste a console key. The first thing a judge at the table hits is a 401.
- **Founder / MongoDB / AI/ML:** The timer reads 0.0 s while a judge reads quietly. The product's whole promise is "we credit real reading", and it gives no credit for reading.
- **Founder / MongoDB:** Approve-50 shows a static notice for about 21 s, which is 12% of a 3-minute slot spent on a spinner right at the punchline.
- **Founder:** 30 s of required silence in the honest review, with no script for it.
- **Sponsor:** In total, about a minute of the three goes to waiting, and no sponsor tool appears in any of it.

### The payoff reads like a stack trace
- **Founder:** The best moment, "Executed 0 of 50 · suspended", is explained in rule codes. "A compliance officer reads that like a stack trace."
- **MongoDB:** In the narrow screenshot the banner cuts off mid-list, and the reopen count (2) sits in a stat tile instead of in the story.
- **Founder:** "refused 0" in a success message reads as an error.

### Is it really an agent? Is it really oversight?
- **AI/ML:** "The 'agent' is a string match." triage() denies when the text contains "Prior-auth record: none on file", which the seed plants. It can't be wrong on this data.
- **AI/ML:** The cited policy clause is picked by `sha256(case_id) % len(clauses)`. The agent's one policy citation is arbitrary, and the gate never checks it.
- **AI/ML:** There is no reject route in pg/main.py and no reject button. Human oversight here means "approve slowly or do nothing".
- **AI/ML:** The agent decides what the reviewer must read. G4 and G5 cover only cited items, so E2, the clinical note, is never required. That is selective evidence built into the design.
- **AI/ML:** The eval measures time, not quality. Every simulated reviewer approves every case. "That is Goodhart on dwell time."
- **AI/ML:** Simulated honest reviewers always send input, while real readers sit still. So 3.9% false refusal is optimistic by construction.
- **AI/ML:** The README leads with the pooled 5/128 (3.9%) and never states fast-honest 4/32 (12.5%), even though the pre-registration says fast-honest would be reported separately.
- **AI/ML:** The baseline (7df270e) and the held-out run (7597a52) are on different commits. CUSUM was calibrated on n = 0 real sessions, so "certified" is doing a lot of work. The groups were built to be separable.
- **AI/ML:** "Proposes, code decides" is a good principle, but this judge will hear it as "there is no agent".

### The MongoDB depth is hidden or overclaimed
- **MongoDB:** "Your best MongoDB work has no screen." /api/ops ($percentile over time-series), /api/explain/window (IXSCAN) and /api/verify/chain aren't called by the UI.
- **MongoDB:** The video card lists "transactions · $jsonSchema · change streams" and skips the clever parts: the version-guarded reviewer_state write, partial unique indexes as invariants, and resume-token catch-up.
- **MongoDB:** 22+ collections and not one $lookup. The Examiner stitches find_one calls together in Python, which "looks like a normalized relational schema moved into Atlas".
- **MongoDB:** "$jsonSchema on every collection" isn't true. view_tokens (which holds dwell time), reviewer_state and cases have no validator, and there is no additionalProperties: false.
- **MongoDB:** confirm() updates the denial outside a transaction, which contradicts "every decision is one Atlas transaction".
- **MongoDB:** The compensation worker polls even though the team clearly knows change streams.
- **MongoDB:** Vector Search, Voyage AI, the MCP server and Agent Skills were researched (docs/SETUP-RESEARCH.md) and not built, at an "Agents in Context" event.

### The sponsor tools are hidden
- **Sponsor:** "You built a good ElevenLabs feature and then hid it." Scribe STT, attestation scoring, replay blocking via the audio_sha256 index and TTS receipts are all in the backend. ui/src/voice/ holds only a README.
- **Sponsor:** The bulk path stores "Reviewed in batch." padded with dots to pass minLength. "Your audit record of a rubber-stamp is literally a rubber-stamped string."
- **Sponsor:** LangSmith is two @traceable decorators on deterministic code. The child spans promised in langsmith-setup.md don't exist.
- **Sponsor:** execute_one returns grant_id with no process_outputs redaction, so traces would contain the credential the design calls the crown jewel.
- **Sponsor:** detector.flag_attestation writes BOILERPLATE / UNVIEWED_EVIDENCE_NAMED / PACE_IMPLAUSIBLE flags, and nothing displays them.
- **Sponsor:** The project's own ElevenLabs doc says "For the main prizes: probably very little".

### The business case is thin
- **Founder:** "Who pays" has a job title (CCO / General Counsel) and a [VERIFY]-tagged SB 1120, but no price, no pricing unit and no cost-of-a-bad-denial anchor.
- **Founder:** No answer to "why wouldn't Epic or Optum add a checkbox?" or to the long health-insurance sales cycle.
- **Founder:** n = 0 real users. No answer to "have you talked to a single claims reviewer?"
- **Founder:** "Your honesty is excellent, but you're about to bury the lead with it." Put the disclosures after the wow.

---

## 6. Killer questions and our best answers

Questions marked **NO GOOD ANSWER** need either a prepared concession or a fix.

| # | Question | Asked by | Best answer from the repo | Status |
|---|---|---|---|---|
| 1 | Which document do two concurrent transactions conflict on, and why not rely on the count read? | MongoDB | reviewer_state "<tenant>\|<reviewer>". Every gate, approval and suspension does a version-guarded update on it. Snapshot reads don't conflict and writes do, so the loser gets a WriteConflict (TransientTransactionError, with VersionMoved as a fallback) and with_transaction re-runs. txn_attempts is stored. Demo: make test-conflict shows attempts=2. | Strong |
| 2 | Kill the detector, write 20 approvals, restart with an expired token. What gets missed? | MongoDB | With no token it reads $clusterTime first, runs a catch_up aggregation from last_created_at minus 1 min, then uses start_at_operation_time. RESYNC_CODES 136/280/286 handle lost history. The gate already refused the burst synchronously. make test-restart. | Good |
| 3 | Why is the Examiner N round trips in Python, not one $lookup pipeline or an embedded case? | MongoDB | Collections have different write paths and lifecycles (TTL on grants/view_tokens, append-only hash-chained review_events, validated approvals), and Examiner reads are rare. Admit a $lookup/$unionWith pipeline is the obvious next step. | Weak |
| 4 | You say $jsonSchema on every collection. Where's view_tokens' validator? | MongoDB | None. Only server code writes it, and the API ignores client dwell. Fix the README wording or add validators. | **NO GOOD ANSWER** |
| 5 | Why isn't review_events a time-series collection, and why is telemetry one? | MongoDB | review_events needs a unique {tenant, session, seq} index and transactional hash-chain appends, which time-series doesn't fit. Telemetry is fire-and-forget with a 24 h TTL. Not written down anywhere, so say it. | Decent (unwritten) |
| 6 | Approve-50 takes 21 s. At scale, where's the hot spot and the ceiling? | MongoDB | The hot document is per reviewer, not global. Different reviewers don't conflict, and every index leads with tenant_id. No load numbers, so say "not measured". | Partial |
| 7 | Where is Vector Search or the MCP server? | MongoDB | Not built, deliberately cut so the enforcement path could be correct, and disclosed. Framing: ProofGate is the gate an MCP-connected agent would have to act through. No code backs this up. | Honest concession |
| 8 | A script faking visibility and input gets 16/16 through. What does Atlas prove? / Can't someone wiggle the mouse? | MongoDB, Founder, AI/ML | Server-timed, per-item, hash-chained interaction on every cited document, under a versioned policy, in one transaction. It raises the cost of faking from one click to sustained scripted work per item. It can't prove reading, and the pre-registration said so. Next step: a comprehension check or spoken attestation (backend exists). | Good |
| 9 | Your agent can't make a mistake on this data. How do you know the gate stops wrong denials? | AI/ML | Triage is deterministic and the seed plants its trigger. No eval group rejects, and there is no reject endpoint. Honest: ProofGate enforces evidence of the review process, not decision quality, which is future work. | **NO GOOD ANSWER** |
| 10 | The agent chooses which documents the human must open. What stops it hiding the clinical note? | AI/ML | G4/G5 cover only cited evidence. Verbal answer: the policy could require all evidence, or a required set per claim type. Not built. | **NO GOOD ANSWER** |
| 11 | Why is the cited clause chosen by hash of the case ID? | AI/ML | It's a placeholder. The gate treats the agent as untrusted, which defends execution but not the auditability of the rationale. | **NO GOOD ANSWER** |
| 12 | Real readers sit still. What's your false-refusal rate for them? | AI/ML | The design is a 15 s interaction window and a 5 s heartbeat. The live test showed 0.0 s after 6 s idle, so the eval underestimates. Next step: real-session calibration with eval/calibrate_detector.py (n = 0 today). | Partial |
| 13 | Fast-honest were refused 12.5%. Why does the README lead with 3.9%? | AI/ML | The per-group table shows 28 of 32 and judge-qa.md breaks it out, but the headline pools the groups. Lead with 12.5%. | Weak (fixable in copy) |
| 14 | Is there any model in the loop? Where's the orchestration? | AI/ML, Sponsor | The executor loop honours pause, re-reads approval state before each action, and confirms by read-back. That is real control-plane work, but there is no LLM ("Not built today"). | Partial |
| 15 | Is the baseline comparison clean across different commits? | AI/ML | Same seed and workload, and the baseline flag turns every check except G1 off. The commit difference is disclosed. Concede that a same-commit rerun would be cleaner. | Partial |
| 16 | Who signs the PO, and what's the price? | Founder | Buyer: CCO / General Counsel. Trigger: class-action and regulator risk (SB 1120 is marked [VERIFY]). No price or pricing unit. Either prepare a unit (per gated denial or per reviewer seat) or say "not priced yet". | **NO GOOD ANSWER** (price) |
| 17 | Doesn't this slow denials and annoy reviewers? | Founder | "It slows only the denials that were never really reviewed." Honest reviewers: 0/16 false suspensions, 3.9% (5/128) refused for time below the minimum, and they can re-review. Say fast-honest 12.5% too. | Decent |
| 18 | Why wouldn't Epic, Optum or the claims platform add this as a checkbox? | Founder | Not in the repo. Best built answer: a checkbox records a click. This enforces at execution time, stops work in flight, reopens denials already sent, gives an examiner a rebuild, and works across agent vendors because it sits in front of the claims system. | **NO GOOD ANSWER** in repo (prepare this one) |
| 19 | Is this an accusation against Cigna, and isn't insurance a 5-year sales cycle? | Founder | The first half is covered ("the pattern as reported", "Cigna disputes the report"). Sales cycle: not covered. Pivot to the wedge: any regulated agent action with a mandatory human-review law (prior auth, lending adverse action, benefits). | Half |
| 20 | Have you talked to a single real reviewer or compliance officer? | Founder | n = 0 real sessions, synthetic data. Admit it in one line and name the first person you'd call. | **NO GOOD ANSWER** |
| 21 | Show me ElevenLabs doing something in the product, live. | Sponsor | Backend only (POST /api/voice/attest, GET /api/voice/receipt/{case_id}), reachable by curl. No button. | **NO GOOD ANSWER** until the button ships |
| 22 | Why is spoken attestation better than typed? Couldn't a stamper say the same sentence 50 times? | Sponsor | attest_score.py weights case-specific terms by IDF, measures boilerplate overlap with the last 10 attestations, and checks pace against audio length. A unique audio_sha256 rejects replays (HTTP 409). The detector flags it but never suspends on it. | Strong if shown |
| 23 | What does LangSmith tell you that the Examiner doesn't? | Sponsor | The docs say LangSmith is the debugging view and Atlas is the record. With two spans on deterministic code there's little to see. No good answer until gate/target/confirm spans exist. | **NO GOOD ANSWER** today |
| 24 | Did you trace an LLM call or evaluate anything in LangSmith? | Sponsor | No. Rules-based by design. The eval runs outside LangSmith. | **NO GOOD ANSWER** |
| 25 | Do your traces contain the grant credential? | Sponsor | As written, yes (execute_one returns grant_id, no process_outputs). Mitigation: grants are single-use, last 60 s and are consumed atomically. This contradicts langsmith-setup.md, so fix it. | Weak (fixable) |
| 26 | If ElevenLabs goes down mid-review, does anything break? | Sponsor | No. Voice is never read by gate.execute or checks.evaluate. If STT fails, the X-Fallback-Text header stores typed text with source='typed_fallback'. Calls run in a threadpool. _validate runs before any paid API call. | Good |

---

## 7. Action list

The demo, video and pitch items come first. **Safe before 4 PM** = copy, labels, demo script/setup, README, or front-end-only wiring of endpoints that already exist, with no change to gate logic. **After** = new features or backend changes. Effort: <30 min / 1-2 h / post-event.

| # | Item | Why (finding) | Effort | Safe before 4 PM freeze? |
|---|---|---|---|---|
| 1 | Demo setup: pre-paste the console key. Use two pre-opened tabs (dr-stamper for the red button, dr-demo for the honest flow). Run `make reset` right before judging and check the reviewer dropdown. | Founder and AI/ML: our screenshot shows dr-demo suspended, a "demo landmine". All four users and three judges hit the console key first. | <30 min | Yes (demo setup) |
| 2 | Rewrite the approve-50 result headline in plain English: "Stopped. 0 of 50 went out. dr-stamper is suspended for bulk approving. 2 earlier denials were reopened." Collapse the G-code rows under "Details". Make the box full-width on narrow screens. | All four users. Founder ("reads like a stack trace"), MongoDB (truncated, reopen hidden). | <30 min | Yes (copy) |
| 3 | Timer copy: show "Paused: scroll or click to keep counting" on the open document. Move the 15 s rule next to the timer. Add a checklist line ("E1 ✓ · E3 2 s left · 12 of 30 s"). | All four users. Founder, MongoDB, AI/ML, Sponsor. | <30 min | Yes (UI copy, no gate change) |
| 4 | Write the demo script word for word. (a) Tell the judge to scroll while reading and say why. (b) Fill the 30 s honest wait with the baseline contrast: "Without the gate, 164 of 200 stamped approvals executed. With it, zero. Honest reviewers: zero of 16 wrongly suspended." (c) Narrate the 21 s approve-50: "50 serial gate transactions, each a snapshot read and majority write on Atlas." | Founder (30 s of silence, spinner), MongoDB (say why it's serial). | <30 min | Yes (script) |
| 5 | Pitch opening: start with the problem and the click ("1.2 seconds per claim, as reported. Agents will do it faster. Click this button."). Describe the proposer honestly: "stand-in proposer, rules today, LLM-pluggable; the contribution is model-agnostic enforcement of evidence of review." Mention MongoDB after the wow. Keep disclosures for Q&A. | Founder (honesty buries the lead). AI/ML ("is it really an agent?"). | <30 min | Yes (pitch) |
| 6 | Pitch/video: name the MongoDB patterns instead of a feature list: "version-guarded transaction · partial unique indexes as invariants · resumable change streams · time-series telemetry · TTL grants". | MongoDB (underselling). | <30 min | Yes (copy) |
| 7 | Video: show the 30 s honest review sped up, with an on-screen label ("30 s of server-timed review, shown at 4x"). End on the Examiner stamp. Narrate with ElevenLabs TTS and name the tools in the description. | Founder (compressing what you claim can't be compressed). Sponsor (description is what prize reviewers read). | <30 min | Yes (video) |
| 8 | Have `make test-conflict` ready in a terminal tab for MongoDB judges ("txn_attempts=2"). | MongoDB ("most memorable 20 seconds you can give a Mongo engineer"). | <30 min | Yes (demo) |
| 9 | README and eval slide: report fast-honest 4/32 (12.5%) first, next to the pooled 3.9%. Add: "simulated honest reviewers always produce input; real false refusal is likely higher (live test: 0.0 s after 6 s idle)". | AI/ML (pre-registration says report separately). | <30 min | Yes (README) |
| 10 | README Disclosures: (a) the cited clause is a placeholder chosen by hash, and the gate doesn't verify relevance; (b) G4 requires only agent-cited evidence; (c) the human can't reject in this build; (d) change "$jsonSchema on every collection" to "on every decision-bearing collection". | AI/ML (killer Qs 9-11), MongoDB (overclaim). | <30 min | Yes (README) |
| 11 | judge-qa.md: add answers for "who pays and what price" (or "not priced yet"), "why not an Epic/Optum checkbox", "sales cycle / wedge", "n = 0 real users: who we'd call first", "why review_events isn't time-series", and "concede: no reject path; process evidence, not decision quality". | Founder and AI/ML killer questions with no answer. | <30 min | Yes (docs) |
| 12 | Relabel "Select all · approve 50" as "Demo: simulate rubber-stamping". | Priya, Marcus, Rosa. | <30 min | Yes (label) |
| 13 | Jargon pass on the main screens: executed→sent, gate→review check, refused 0 removed from the success text, honest result as one sentence, tally labels renamed, Examiner column renames (Actively read / Window open / Document unchanged ✓). Put hashes and G-codes behind toggles where that is copy-only. | All four users (sections 3 and 4b). | 1-2 h | Yes (copy/labels), if no logic is touched |
| 14 | Show "not in this demo" disabled buttons for "Overturn: pay the claim" and "Pend: request records" next to "Approve denial". | All four users, AI/ML. Shows we know about the gap without building it. | <30 min | Yes (label-only placeholder) |
| 15 | Add a "Play voice receipt" button on the Examiner page (GET /api/voice/receipt/{case_id} into an `<audio>` tag). | Sponsor (cheapest visible ElevenLabs moment, about 15 lines). | <30 min | Borderline: front-end only on an existing endpoint. Team decides. |
| 16 | Add a "Speak attestation" button in Review.tsx (MediaRecorder → /api/voice/attest, transcript into the textarea, attestation_id sent with the approval). Show the source, audio hash, scores and flags on Examiner. Demo the 409 replay beat. | Sponsor (the only thing it judges for the ElevenLabs prize, about 60 lines, backend done). Founder (most memorable human moment). | 1-2 h | New UI feature. Founder judge says do it only if the core demo is solid by 3:30, otherwise after. Team call. |
| 17 | Add an "Atlas proof" panel calling /api/ops, /api/explain/window and the latest txn_attempts. | MongoDB ("highest score-per-minute move"). | 1-2 h | Front-end only, but new UI. Team call before freeze, otherwise after. |
| 18 | Show live progress during approve-50 ("Gate checked 12 of 50 · 0 executed"), by polling /api/dashboard. | Founder (turns waiting into suspense). All four users asked for progress. | 1-2 h | Borderline (front-end). Minimum copy-only version is safe. |
| 19 | LangSmith: enable tracing for the demo, add nested gate/target/confirm spans with case_id metadata, truncate grant_id with process_outputs, and put a share link in the README. | Sponsor (no-op decorators; credential in traces). | <30 min (Sponsor's estimate) | Backend code change. After freeze unless `make test` passes and the team accepts the risk. |
| 20 | Add validators to view_tokens and reviewer_state (idempotent via collMod). | MongoDB (overclaim). Wording fix (#10) is the safe alternative. | <30 min | Only if `make test` still passes. Otherwise after. |
| 21 | Overturn / reject / pend actions with an endpoint, held to the same reading proof, and shown on Examiner. Then a planted-error eval measuring catch rate. | All four users (top-3 for Priya, Marcus, Rosa). AI/ML ("the metric an agent-safety judge actually cares about"). | post-event | After |
| 22 | Fair reading timer: credit time while the document is visible and recently scrolled, with a longer idle window. Readable document viewer with the cited sentence highlighted. | All four users, AI/ML, Founder. | post-event | After (changes timing logic) |
| 23 | Require all evidence, or a policy-defined set per claim type, not just agent-cited items. Add a check that the cited clause applies to the billed code. Show the clause text inline. | AI/ML (selective-evidence flaw). Rosa, Marcus (clinical note). | post-event | After |
| 24 | Examiner as a fileable report: Export/Print PDF, full date, time and time zone, opened-at/closed-at per document, reviewer name/licence/specialty, plain-English summary at the top, all documents listed as opened/not opened, case search. | Linda, Rosa, Marcus (top-3), Priya. | post-event | After |
| 25 | Supervisor about people: reason and confirmation on suspend/policy change, Reinstate, warn → review → suspend ladder, per-reviewer quality table, policy history, read-only examiner login. | Marcus (top-3), Priya, Linda, Rosa. | post-event | After |
| 26 | Real sign-in tied to name, licence and specialty. Reviewer's own workload view instead of system totals. | Priya, Marcus, Linda, Rosa. | post-event | After |
| 27 | Plug in a real LLM proposer with adversarial proposals. Expose the audit trail via the read-only MongoDB MCP server and Agent Skills. Vector Search over policy clauses. | AI/ML, MongoDB ("Agents in Context" fit). | post-event | After |
| 28 | Examiner as one aggregation pipeline ($lookup). Change-stream-driven compensation worker. Fold confirm() into one transaction. | MongoDB. | post-event | After |
| 29 | Real-user calibration (5-10 people, or 3-5 reviewers/compliance officers). Re-run the eval on one commit. Calibrate the minimum per document type. LangSmith dataset/experiments of the 8 personas. | AI/ML, Founder, Sponsor, Marcus. | post-event | After |
| 30 | Comprehension check or spoken attestation as an additional check, re-run against hb-forger. Reject boilerplate attestations. | AI/ML, Rosa, Sponsor. | post-event | After |

---

## 8. Appendix: persona walkthroughs (verbatim)

### Dr. Priya N., 54, physician medical director at a mid-size US health insurer

Signs 60-120 denial recommendations a day under her own license. Works in the claims system, Outlook and PDFs. Has never used a developer tool and doesn't know what a transaction, token, hash or "G4" means. What worries her: volume quotas, being blamed for denials she barely saw, clunky document viewers, and getting punished for reading clinical notes slowly.

> First thing on the Review page: a "Console key" box in the header with dots in it. Nobody told me what to paste there, so I'm stuck before I start. Then there's a "Reviewer" dropdown where I can pick dr-demo, dr-stamper and other people. I can sign in as any doctor I want without a password? I click "Start session" and choose CLM-A-0005. The screen says "The agent proposes to deny" and shows four cards. Two of them, E1 and E3, carry a red "cited" tag. I open E1 and read the crutch line item without touching the mouse, and the timer stays at "0.0 s". I'm reading, but it says I'm not. The small grey line about "used it in the last 15 s" sits below the cards, where I didn't look. The text shows as one cramped monospace box. There is only one button, "Approve denial". I don't see how to disagree with the agent. "Select all · approve 50" looks like the button I'd be told to use to meet quota. It suspends me and the screen says "G4 Every cited item opened: refused 47". On the Supervisor page I can suspend someone but there's no way to reinstate them. The Examiner page is the part I'd actually want, but "Evidence hash" and "single-use grant" mean nothing to me.

**Would she use it?** Not as it stands, but she'd want her company to adopt the idea. The blockers: no way to overturn, the 0.0 s timer, a bulk button that suspends with no warning or appeal, and jargon.

### Marcus T., 47, utilization-management nurse supervisor

Manages 12 reviewers, reports productivity and quality to leadership, handles regulator audits and appeals. Not technical.

> First I had to paste a "Console key" into a password box before anything worked. Nobody would have told me that. Then I picked "dr-demo" from a dropdown and hit "New session". Nobody signs in by choosing their name from a list. CLM-A-0005 says "The agent proposes to deny", with red "cited" tags on E1 and E3. That part made sense. I opened E1 and sat reading it, and the timer said "0.0 s" because I wasn't moving my mouse. That's the opposite of what reading looks like. The only button I got was "Approve denial". There is no way to say "I disagree, pay the claim". After I approved, a "DENIED" stamp showed up. Fine. Then I clicked "Select all · approve 50", waited about 20 seconds, and got "Executed 0 of 50 · dr-demo suspended" plus a list like "G2 Reviewer not suspended: refused 47". I had to read that three times. On Supervisor, the policy table is the best thing in the app, but "dwell floor", "median-dwell check" and "Separation of duties" need plain English. "Suspend" has no reason box and no warning step. Examiner reads like the audit file I'd hand a regulator. I'd only drop "Evidence hash" and "recorded · consistent".

**Would he use it?** Not as-is, but he'd want a pilot. He needs overturn and pend decisions, plain-language results, warning before suspension, and a reviewer quality dashboard.

### Linda O., 58, market-conduct examiner at a state insurance department

Reads claim files after consumer complaints and asks every insurer the same three questions: who reviewed this, what did they look at, and when. Not technical, distrusts dashboards, needs evidence that holds up in an exam report.

> On Review I chose "dr-demo" and pressed "New session", but nothing worked until someone told me to paste a "Console key" into the header. On CLM-A-0005 I opened E1, "Claim line 1", and read it. The counter stayed at "0.0 s" because I wasn't moving the mouse. That scared me: careful readers sit still. The small print says time counts only if I "used it in the last 15 s", but nobody reads that. I reached 30 s, typed my reason in "Attestation" and pressed "Approve denial". I got the "DENIED, GATE ALLOWED · v1" stamp and the words "refused 0", which made me think something had been refused. "Select all · approve 50" took about 20 seconds and then showed "G2 Reviewer not suspended", "G4", "G5", "G6". I don't know what any of those mean. The Supervisor page has "Approvals in the median-dwell check", which I didn't follow either. On Examiner I typed CLM-A-0003 and pressed "Rebuild from Atlas". Steps 1 to 6 are the first audit trail a vendor has shown me that I could actually follow. But the times have no date or time zone, and there is no way to print it or attach it to my report.

**Would she use it?** Yes, the Examiner page, and a strong yes for a demo. Not in a real exam until it can be exported, every event has a full date, time and zone, and the jargon is gone.

### Rosa M., 41, patient advocate and appeals specialist at a community health clinic

Not technical. Fights "not medically necessary" denials every week and never knows if a doctor looked at the chart.

> Review page: the first thing I saw was a "Console key" box with dots in it. I don't know what a console key is, and nothing told me buttons stay dead until I paste one. Then I picked "dr-demo" from the Reviewer dropdown and clicked "New session". The queue showed CLM-A-0005 with "The agent proposes to deny. Service billed without a prior authorization on file; MP-020 requires one." I clicked E1 "Claim line 1" and started reading. It said "reading 0.0 s" and didn't move, because I was reading and not moving the mouse. That felt like being told I wasn't working. The only real button is "Approve denial". There's no "Overturn" or "Send back". The "Select all · approve 50" button got me suspended, and the red box said "G2 Reviewer not suspended: refused 47 / G6 Not approving in bulk", which I couldn't follow. On a narrow window the result box squeezed "Executed 1 of 1" into a skinny column. Supervisor: "Approvals in the median-dwell check" and "Separation of duties" mean nothing to me. Examiner: this is the page I actually want, but it shows "dr-demo", not a name, licence or specialty, and the attestation is boilerplate again.

**Would she use it?** She isn't the user of Review or Supervisor, but she would fight to get the Examiner output for every denial her patients receive. The approve-50 refusal and the reopening of earlier denials is "the part that made me sit up". She wants it to read "like a letter I can attach to an appeal, not a database log".

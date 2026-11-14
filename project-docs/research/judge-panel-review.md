# ProofGate: simulated judge panel review

**These are simulations, not the real people.** The 16 "judges" below are AI personas modelled on the judges listed for the event, built from persona files the team provided. They are not the real judges, they did not see this project, and nothing here may ever be quoted or presented as something a real judge said or thinks. Names are used only to label which persona file each review came from.

Every number below comes from the 16 reviews or from repo files the reviews cite (docs/eval-heldout.txt, docs/eval-baseline.txt, project-docs/WORKLOG.md, README.md). File and line references are as the reviews reported them; they were not re-checked for this write-up. Nothing was re-measured.

---

## 1. Summary

**Top-6 vote: 15 yes, 1 no.** The only no is Raschid Jimenez (Senior PM @ MongoDB persona).

**Average scores (out of 10, 16 judges):**

| Statement fit | Impact | Innovation | Technical feasibility | Demo readiness | Total (of 50) |
|---|---|---|---|---|---|
| 8.94 | 7.00 | 7.00 | 8.00 | 6.88 | 37.81 |

The scores barely vary. Every judge gave impact 7, innovation 7 and feasibility 8. Statement fit is 9 from everyone except Amrit Krishnan (8). Demo readiness is 7 from everyone except Raschid Jimenez and Tapan Shah (6). Demo readiness is the lowest score again.

**The 5 changes that would move the most votes:**

1. **Submit the required artifacts, and make them visible.** Record the 1-minute video with working audio (an ElevenLabs voiceover covers both the audio rule and the ElevenLabs prize), add all three teammates on Cerebral Valley, and check the repo is public from a logged-out browser. All 16 judges flagged that none of this is shown yet (WORKLOG "16:45 submitted" row is empty; "Neil has no commits"). A missing requirement would cost all 15 yes votes, not just one.
2. **Re-verify the 15:48 build (commit 5db2678) before the freeze.** It rewrote the timer and heartbeat hook after the last browser test and the last test run. Run one honest review as dr-demo and approve-50 as **dr-stamper** (the stored screenshot suspends dr-demo, the honest reviewer), run `make e2e`, retake screenshots, log it in WORKLOG. Raised by 7 judges.
3. **Flip Jimenez: show the gate is generic and that a policy change flips the next decision.** Seed a second action type with only a new review_policies document, and stage one 30-second beat: approve at about 45 s with the executor paused, raise the floor on the Supervisor page, resume, show the Examiner refusal stamped "policy v2". Raised by 2 judges, and it is the only change named as flipping a no to a yes.
4. **Pitch wording that leads with the honest numbers.** Report fast-honest false refusal 4 of 32 (12.5%) next to honest 1 of 96, not the pooled 3.9%; say hb-forger 16/16 and floor-gamer 32/32 got through and that the gate "raises the cost of faking review", not "proves reading"; call the proposer a deliberate stand-in; frame the self-baselined CUSUM plus tighten-only policy versions as "adapts its guardrails"; add one line on guide items used and skipped. Raised by 10+ judges in some form.
5. **Put proof in a terminal at the table, and fix the demo script's dead references.** Have `make test-conflict` (with the reviewer_state version field) and the `make bypass` curl plus its target_log row ready. Fix project-docs/demo.md:59 (`make burst-forged` does not exist) and demo.md:65 (`docs/test-conflict.txt` is not in docs/), and save `make test-conflict`, `make explain` and `make test-restart` outputs to docs/. Raised by 8 judges.

---

## 2. Scorecard

| Judge (simulated persona) | Fit | Impact | Innov. | Feas. | Demo | Top 6? | The flip change (or the change that firms up the yes) |
|---|---|---|---|---|---|---|---|
| Robert Maissan, Senior Lead, Engineering @ MongoDB | 9 | 7 | 7 | 8 | 7 | Yes | Re-verify the 5db2678 build live (honest path, approve 50, `make e2e`), refresh screenshots, open at the table with test-conflict and the reviewer_state version field |
| Raschid Jimenez, Senior Product Manager @ MongoDB | 9 | 7 | 7 | 8 | 6 | **No** | Seed a second action type with only a new policy document, and demo a floor raise turning the next decision into a "policy v2" refusal. Video with audio by 5 PM |
| Tapan Shah, Service Engineer @ MongoDB | 9 | 7 | 7 | 8 | 6 | Yes | Commit saved `make test-restart` and `make explain` outputs; add a 20 s kill-and-restart-detector beat showing detector_state |
| Leo Gomes, Full Stack Software Developer @ Pelmorex | 9 | 7 | 7 | 8 | 7 | Yes | A `make executed` query (target_log APPLIED count plus denials by status), a fallback video, screenshots retaken with dr-stamper as the stamper |
| Aasawari Sahasrabuddhe, Senior Builder Advocate @ Okta, MongoDB Champion | 9 | 7 | 7 | 8 | 7 | Yes | Wording now: disclose the grant is a bearer token, lead with the bypass curl and its target_log row. Later: sender-constrain the grant |
| Sergey Strelnikov, VP of Engineering @ Acerta | 9 | 7 | 7 | 8 | 7 | Yes | Re-run honest path and approve 50 on 5db2678, record the video, quote fast-honest 4/32 and the stored policy_version, have a reversed-after query ready |
| Anamika Ahmed, Senior Software Engineer @ Microsoft | 9 | 7 | 7 | 8 | 7 | Yes | Show `make test-conflict` PASS and gate.py:137 in the video and at the table; lead with the hb-forger and floor-gamer disclosure |
| Pablo Vallejo, Engineering Manager @ Wealthsimple | 9 | 7 | 7 | 8 | 7 | Yes | Rehearse a 20 s answer to "what if the reopen fails" (detector.py:290-294, R6 red/green); ElevenLabs voiceover on the video |
| Amrit Krishnan, Technical Lead @ Vector Institute | 8 | 7 | 7 | 8 | 7 | Yes | Report fast-honest and per-gamer miss rates separately in README and pitch; later a small dev-seed sweep |
| Vatsal Shah, Co-Founder & CTO @ Speak AI | 9 | 7 | 7 | 8 | 7 | Yes | Add a 50-way parallel curl burst as `make burst-forged`, run it on Atlas, commit the output; run approve 50 as dr-stamper |
| Parth Patel, Forward Deployed Engineer @ Cohere | 9 | 7 | 7 | 8 | 7 | Yes | At the table, stop the detector, curl 50 approvals with dwell_ms=999999, show "executed 0" and client_supplied_ignored |
| Ahmed Radwan, Applied ML @ Vector Institute | 9 | 7 | 7 | 8 | 7 | Yes | Per-group table on stage; name the untested still-reader case; disclose the shipped 2 s heartbeat vs the evaluated 5 s |
| Pahul Hallan, Senior Machine Learning Engineer @ Zafin | 9 | 7 | 7 | 8 | 7 | Yes | Edit one review_event live, show the Examiner cross and the /api/verify/chain seq; commit chain heads to the repo as an external anchor |
| Noel Kirthiraj, Founder & Principal @ Omni | 9 | 7 | 7 | 8 | 7 | Yes | Buyer sentence (CCO or GC) in the first 10 s of video and pitch; ElevenLabs narration; rehearse approve 50 on 5db2678 with the fallback queued |
| Rudraksh Monga, Senior Software Engineer @ Stan | 9 | 7 | 7 | 8 | 7 | Yes | Seed payer-beta and add one isolation test (suspend at payer-acme, payer-beta still ALLOW); disclose the global console key |
| Aasheesh Singh, Senior Research Engineer @ Quantiphi | 9 | 7 | 7 | 8 | 7 | Yes | Insert an account_freeze policy plus one record and show the gate enforce it with no code change (later); quick version: walk gate.py:45/155 and say "not shown" |

---

## 3. Must-fix status per judge

Each persona had a must-fix from planning. Status is the persona's own verdict on whether the code answers it.

| Judge | Status | Answered in code | Still missing |
|---|---|---|---|
| Robert Maissan | Yes (mostly) | One transaction holds every check with a version guard (pg/gate.py:111-140, :137; suspend_in_txn $inc version at :69). Server-only dwell (pg/checks.py:15-24; client value under client_supplied_ignored, pg/review.py:177-184). $jsonSchema presence/type with tenant_id required (pg/db.py:25-66). Resume token saved and resumed (pg/detector.py:225-253). Seeded eval (eval/simulate.py; docs/eval-heldout.txt) | Eval and in-flight suspension abort are two scripts, not one (acceptable) |
| Raschid Jimenez | Partly | Gate reads versioned policy, suspension, rate window and writes reviewer_state in one transaction (pg/gate.py:111-140). G4/G5/G6 refuse inline, G6 suspends inline (pg/gate.py:174-176). Supervisor publishes tighten-only versions (pg/gate.py:253-270, ui/src/pages/Supervisor.tsx:47-56). policy_version on every decision | No second action type (only claim_denial seeded, seed/generate.py:101). Floor edit never shown changing the next decision. Evidence-hash requirement in the validator not verified |
| Tapan Shah | Partly | Version-guarded reviewer_state write (pg/gate.py:136-140). Resume token after each event, failed events replay (pg/detector.py:242-259). Server dwell (pg/checks.py:15-24). Index at pg/db.py:88, explain route pg/main.py:226 | Kill/restart demo not scripted or recorded on Atlas. No stored explain output |
| Leo Gomes | Mostly yes | Rate window and version write in the transaction (pg/gate.py:121-140). Compensation reads target back before confirming (pg/detector.py:273-296), no HTTP undo route (pg/target.py:60-62). Resume token (pg/detector.py:225-226, :253) | Visibility/input flags in heartbeats come from the client (disclosed). Fallback video not shown |
| Aasawari Sahasrabuddhe | Partly | 60 s single-use grant bound to tenant/record/case/to_status, minted only on ALLOW (pg/gate.py:156-168). No grant gives 403 NO_VALID_GRANT plus target_log (pg/target.py:20-39). Suspension revokes grants in the same transaction (pg/gate.py:63-96). `make bypass` passed (WORKLOG 13:39) | Grant not bound to the presenting caller; X-Service-Identity unverified (pg/target.py:60-63); policy_version not re-checked at apply |
| Sergey Strelnikov | Mostly yes | Hard checks in one transaction (pg/gate.py:111-140). G2/G4/G5/G6 in pg/checks.py:50-88. Detector with resume token (pg/detector.py:217-260). Suspensions store policy_version. `make eval-heldout` prints R1-R8 and false suspension | Denials sent back per false suspension is computed (eval/simulate.py:123) but not printed or tracked per suspension |
| Anamika Ahmed | Yes | Version-guarded write and inline G6 (pg/gate.py:135-140, :62-96); checks in evaluate() (pg/checks.py:50-98). Server dwell with visible/input/gap rules (pg/checks.py:15-24). Resume token (pg/detector.py:225-253). Idempotent compensation via upsert on denial_id (pg/gate.py:52-59) | Race shown with debug pauses, not near-simultaneous commits |
| Pablo Vallejo | Mostly yes | Reopen hits the mock claims system, linked to denial_id, read back before confirm (pg/target.py:43-57, pg/detector.py:280-283). R6 checks stored state (pg/rules.py:58-68). Bulk path executes 0 of 50 | No explicit idle-tab flag on the Examiner (Examiner.tsx) |
| Amrit Krishnan | Partly | `make eval-heldout`, seed 20261114 (Makefile:30), 8 groups, R1-R8. Pre-registration first (7df270e at 14:25, results 14:31). G6 synchronous (pg/checks.py:86-89). policy_version on suspensions (pg/gate.py:91) | No threshold sweep (no `make sweep`, no eval/sweep.py). No miss-rate column. Sent-back-per-false-suspension not printed (moot at 0 false suspensions) |
| Vatsal Shah | Mostly yes | Client dwell ignored on single and bulk paths (pg/review.py:169-183, :228-244). Suspension and rate window read in the transaction (pg/gate.py:126, :128). Evidence-hash coverage (pg/checks.py:67-74). Inline G6 (pg/gate.py:172-174). `make reset`, `make demo-case` exist | Pre-recorded bulk fallback not shown |
| Parth Patel | Yes | Policy (pg/gate.py:120), suspensions (:125), window (:127), version-guarded write (:135-140), inline G6 (:186-189). Server dwell, client value ignored (pg/review.py:181-183). Tab-idler executed 0 of 32 | Whether $jsonSchema checks required fields only was not verified |
| Ahmed Radwan | Partly | Held-out run, 38 simulated reviewers in 8 groups (docs/eval-heldout.txt). Nulls disclosed. Synchronous rate check and suspension (pg/gate.py:128-174). Versioned thresholds (pg/gate.py:253-270) | No sweep of floor or window. Reopened-per-wrong-suspension not stated (should say 0). Honest sessions drawn from the calibration model |
| Pahul Hallan | Mostly yes | All checks in one gate transaction (pg/gate.py:111-140). Server dwell (pg/review.py:177-184). Review events hash-chained per session (pg/review.py:41-57). Examiner verifies chain and recomputes dwell (pg/rules.py:112-121) | audit and gate_decisions not chained (pg/gate.py:182-184). App role is readWrite, not insert-only (README.md:78; docs/PRD.md:204) |
| Noel Kirthiraj | Mostly yes | Synchronous gate built first (pg/gate.py:128-132, :172-174, :182). 0-of-50 logged (WORKLOG 14:01, 15:06, 15:15). LLM rationale cut as planned | Buyer only in docs/PRD.md:18 and judge-qa.md:19, not README or video. Pre-recorded fallback not shown |
| Rudraksh Monga | Partly | tenant_id required in validated collections (pg/db.py:25-66). Reviewer indexes lead with tenant_id (pg/db.py:75-106). reviewer_state keyed tenant\|reviewer (pg/gate.py:121-140). suspend_in_txn filters on tenant_id (pg/gate.py:63-96) | No second payer, no cross-tenant test. compensations and denials(approval_id) indexes lack tenant_id (pg/db.py:94, :101) |
| Aasheesh Singh | Partly | Policy is versioned data (pg/gate.py:253). Rate check and suspension synchronous (pg/gate.py:172-174). Server dwell (pg/checks.py:15-24). `make eval-heldout` | Second adverse action from a policy document alone not shown (README.md:182 lists it as not built) |

**Tally:** Yes 2, Mostly yes 7, Partly 7, No 0.

---

## 4. Killer questions

| Judge | Question (short form) | Can the build answer it now? | Best answer, or the gap |
|---|---|---|---|
| Robert Maissan | A suspension lands while two denials for the same reviewer are in flight. Which document forces the write conflict? Show the test. | Partly (strong) | reviewer_state, keyed tenant\|reviewer; every gate does update_one({_id, version}) with $inc (pg/gate.py:135-140) and suspend_in_txn bumps it (:69). eval/test_conflict.py proves (a) suspension vs one denial and (b) two denials, ALL PASS on Atlas (WORKLOG 13:39). **Gap:** no single three-way test. Point at txn_attempts {3:1, 4:1} in the held-out run as real retries |
| Raschid Jimenez | Raise the dwell floor 30 s to 60 s mid-queue; show the document the gate reads and prove a 45 s approval is refused next call, no restart. | Yes in code, partly as demo | active_policy is re-read in every transaction (pg/gate.py:119, :46); G5 compares stored dwell to it (pg/checks.py:76-85); refusal records policy_version 2. **Gap:** no test or rehearsed demo step. Stage it live: executor paused, approve at ~45 s, raise floor, resume, show Examiner |
| Tapan Shah | Kill the detector halfway through the burst, restart, show the resume token; which document makes approvals 1-9 conflict with a suspension? | Partly | Conflict half: yes (pg/gate.py:137-140, :69; test-conflict passed 13:39 and 14:47). **Gap:** kill/restart is built (pg/detector.py:253-259, eval/test_detector_restart.py) but no Atlas run recorded and not in the demo; no stored explain IXSCAN |
| Leo Gomes | Kill FastAPI mid-burst: how many executed and which query proves it? Kill between target.apply and confirm: what happens to that denial? | Partly | Burst: executed stays 0; proof is a target_log APPLIED count, but no make target, so it is typed live. **Gap:** a kill between apply and confirm leaves the denial AUTHORIZED with a used grant, nothing reconfirms it (pg/agent.py:39-48), R7 accepts it (pg/rules.py:74) |
| Aasawari Sahasrabuddhe | With the agent's credentials, curl the deny endpoint directly: what stops me and where is it in the examiner? Can I spend a sniffed grant_id? | Mostly yes | No grant or forged grant: 403 NO_VALID_GRANT logged to target_log (pg/target.py:25-27), shown on Examiner; `make bypass` passed. **Gap:** a stolen live grant would apply within 60 s, and target_log records whatever X-Service-Identity was typed |
| Sergey Strelnikov | Run 20 honest reviewers at varied speeds: how many suspended, denials sent back per false suspension, which policy version, from stored state. | Partly | 16 synthetic honest reviewers, 0 suspended (CI 0-19.4%), from db.suspensions; policy_version stamped. Lead with the cost that did appear: 5/128 honest refusals, 4 of them fast-honest. **Gap:** n = 16 not 20, synthetic, sent-back count not printed |
| Anamika Ahmed | Two approvals commit 5 ms apart and the change stream suspends after both pass the gate. Which document makes one abort? Show it in a test. | Mostly yes | Same reviewer_state version write (pg/gate.py:137-140), VersionMoved labelled TransientTransactionError (:25-33), suspension bumps it (:68-69); G6 is inline. **Gap:** the test uses 2-3 s sleeps, not 5 ms commits, and asserts retry count, not the final invariant |
| Pablo Vallejo | A denial went out under a reviewer suspended 40 s later: show the reopen, the read-back and the audit link. What if the reopen fails halfway? | Partly | Approve 50 reopens the 2 executed denials; Examiner step 6 shows "read back OPEN" linked to denial_id; `make e2e` logs compensation confirmed. Failure: stays pending, backoff capped at 30 s (pg/detector.py:290-294), repeat is NOOP_IDEMPOTENT. **Gap:** untested, and the two write pairs are not atomic (pg/target.py:53-56, pg/detector.py:282-288) |
| Amrit Krishnan | Fast-honest refused 4/32, floor-gamers 32/32 through: what says 3 s (scaled) is the right floor? How would a policy owner know the cost of moving it? | Partly | Error rates are measured and published (false suspension 0/16, tab-idlers 0/32, fast-honest 4/32). **Gap:** no sweep, so no trade-off curve |
| Vatsal Shah | Fire 50 approvals in parallel with curl, forging dwell_ms=45000: how many execute and which line stops them? | Partly | 0; forged dwell lands in client_supplied_ignored (pg/review.py:183), G4/G5 refuse (pg/checks.py:67-85), G6 plus version write serialize and suspend (pg/gate.py:128, :137); docs/enforcement-map.md. **Gap:** test_conflict (c) is sequential and in-process; `make burst-forged` does not exist |
| Parth Patel | Turn off the detector and curl 50 approvals with forged dwell_ms: how many execute and which line stops them? | Partly to yes | 0: pg/review.py:183, pg/checks.py:67-85, inline G6 at pg/gate.py:186-189 needs no detector; WORKLOG records forged burst 0 of 50. **Gap:** no stored run with the detector explicitly stopped; heartbeat forgers still get 16/16 |
| Ahmed Radwan | On untuned sessions, what fraction of careful reviewers is wrongly refused or suspended, including a reader still for 20 s? What fraction of tab-idlers gets through? Show the failing run. | Partly | 0/16 suspended, 5/128 refused (fast-honest 4/32), tab-idlers 0/32 vs 31/32 under baseline, failing runs shown (hb-forger, floor-gamer). **Gap:** the still reader is never simulated (eval/simulate.py:45), no sweep, honest sessions share the calibration model |
| Pahul Hallan | The service writing approvals also writes the evidence: what stops it fabricating evidence_hashes_viewed and dwell after the fact? Show the replay catching one edited review_event. | Partly | A single edited event is caught (tests/test_chain.py:22-27); Examiner recomputes dwell from raw heartbeats (pg/rules.py:112-113). **Gap:** a writer that rewrites the chain forward and updates chain_head passes; role is readWrite; nothing anchored outside the database; evidence_hashes_viewed not chained |
| Noel Kirthiraj | Who signs the PO and what liability does it remove? Why would the insurer pay to slow its own denials before a regulator forces it? | Partly | CCO/GC buys per-case proof of individual review; Examiner rebuilds it; baseline 164/200 vs 0/200; cost stated (3.9% honest false refusal, 0/16 suspensions). **Gap:** buyer not in README or video, SB 1120 still [VERIFY], no customer or price signal, n = 0 real sessions |
| Rudraksh Monga | Two payers on one cluster, payer A's reviewer suspended: show the query/index that leaves payer B unaffected, what stops cross-tenant carry-over, and what stops a console-key holder changing a header. | Partly | Data path yes: suspend_in_txn filters on tenant_id (pg/gate.py:69-86), reviewer_state keyed tenant\|reviewer, one_active_suspension index (pg/db.py:98-100), grants consumed only on matching tenant (pg/target.py:20-23). **Gap:** no second tenant seeded or tested; X-Tenant-Id is client-chosen and the console key is global (pg/auth.py:16, pg/main.py:186-193) |
| Aasheesh Singh | Insert an account_freeze policy now, no code change: does the gate enforce it? What share of held-out honest reviewers does the rate rule wrongly suspend? | Partly | Second half: 0/16 (CI 0-19.4%), G6 barely exercised. First half: gate and target are generic over action_type and effect.kind (pg/gate.py:45, :155). **Gap:** no account_freeze policy, record or proposal; agent and executor hard-wired to claim denials (pg/agent.py:20-58). Honest answer: "architecturally yes, not shown today" |

**Tally:** Yes or mostly yes 3 (Jimenez in code, Aasawari, Anamika); partly 13. None is a flat no.

---

## 5. The roast

Every persona's blunt line, grouped by theme. These are simulated lines; do not attribute them to the real people.

### "The engineering is real, but you hid it or didn't show it"
- **Maissan:** "You built a properly serialized, grant-consuming, resumable-change-stream audit gate. Then you put a regex where the agent should be and rewrote the demo timer 12 minutes before freeze. The database work is real. Don't let an untested React hook be what I see first."
- **Tapan Shah:** "You built the resume token I asked for and then left it out of the demo. The demo script also points to a make target and a fallback file that don't exist. From where I sit, unshown engineering counts the same as unbuilt engineering."
- **Rudraksh Monga:** "You built a tenant-scoped gate and then demo it on a single tenant, so the isolation you designed in is the one thing nobody gets to see. And anyone with the console key can halt any payer's reviewer by changing one header."
- **Vatsal Shah:** "You built the hardest part right: a transactional gate that doesn't care about change-stream timing. Then your demo script points at a make target that doesn't exist, and you suspend your own honest reviewer on stage."
- **Parth Patel:** "...you published the 16 of 16 that still get through instead of hiding them. Now show me the curl with the detector killed, or it's still a slide."

### "It looks like a claims app, not a pattern"
- **Raschid Jimenez:** "You built the transaction I asked for and then hid it behind a claims form. Without a second action type riding the same gate, this still looks like a denial app with a stopwatch, not a pattern I'd hand to other Atlas teams."
- **Aasheesh Singh:** "You built a properly serious transactional gate, then left my one generalisation test as a sentence in the 'Not built today' list. The 'agent' is an if-statement looking for a string."

### "The trust boundary stops one hop short"
- **Aasawari Sahasrabuddhe:** "...you let the target trust whoever holds the grant and believe whatever name they type in a header. And the 'reviewer' is someone the operator picks from a session list, so the identity layer stops one hop short."
- **Pahul Hallan:** "You built the bank-grade gate I asked for and then left the evidence store writable by the same user that fills it. Your hash chain catches a careless edit, not a determined one."

### "You tested the easy failure, not the hard one"
- **Leo Gomes:** "This is the rare hackathon build where the rollback really reads the target back. But you tested killing the detector, not the process that holds the grant, and the reviewer you suspended on screen is your honest one."
- **Pablo Vallejo:** "This is the only maker-checker I've seen today that actually reverses the damage and reads it back. But 'it retries' is a claim until you show me a reopen failing and then recovering. And you left the ElevenLabs and Vector Search prize money on the table."

### "Your headline numbers flatter you"
- **Sergey Strelnikov:** "...your false-alarm story is '0 of 16 synthetic people, CI to 19%', and your fast honest reviewers eat a 12.5% refusal rate you have not put in the pitch."
- **Amrit Krishnan:** "You did the hard part, a pre-registered held-out run with nulls reported, and then put a pooled 3.9% in the headline that buries a 12.5% fast-honest refusal rate. The 'policy owner picks the point' line still has no curve behind it."
- **Ahmed Radwan:** "You built a gate that a script can beat with 31 seconds of fake heartbeats, and to your credit you wrote that down yourselves. Now stop rounding the fast-honest reviewers' 12.5% down into a pooled 3.9%, and admit you never simulated a reader who reads without wiggling the mouse."
- **Anamika Ahmed:** "...your own eval says a 30-line heartbeat script executes 16 of 16, so stop saying 'proof of review' and start saying 'cost of faking review'."

### "Who pays?"
- **Noel Kirthiraj:** "You built the best answer to 'enforce before the action' I'll see today, and then hid the buyer in docs/PRD.md line 18. A gate nobody is named to pay for is a feature for someone else's product."

---

## 6. Recurring problems across judges

| # | Problem | Judges raising it | Evidence | Smallest fix |
|---|---|---|---|---|
| 1 | Submission artifacts not shown: 1-minute video with audio, teammates on Cerebral Valley, public repo check | 16 of 16 | WORKLOG "16:45 submitted" row empty, no video entry; WORKLOG 15:27 "Neil has no commits"; Sukhman's commits show author "Your Name" (Amrit) | Record the video now with ElevenLabs voiceover, check playback has sound, add all three teammates, check the repo logged out. Make Neil's role visible in the description |
| 2 | Event guide coverage thin: Vector Search, Atlas Search, automated embeddings, Voyage AI, LangGraph checkpoints and MCP Server skipped; Agent Skills/MCP use during the build not shown | 16 of 16 | README.md:182 "Not built today"; docs/TOOLS.md:25-26 lists them as dev setup only | One description line: what was used, what was skipped and why (Statement One doesn't need Vector Search). Mention Agent Skills/MCP Server use only if true. Optional: read-only MCP Server answering "why was CLM-A-0005 denied" |
| 3 | ElevenLabs is backend-only; no UI or demo use, so the ElevenLabs prize is weak | 16 of 16 | pg/voice.py and router at pg/main.py:39; ui/src/voice holds only a README; no voice element in screens/*.jpg | ElevenLabs voiceover on the 1-minute video (no code). Later: voice receipt or speak-attestation button |
| 4 | LangSmith traces only the triage step and only when LANGSMITH_TRACING=true | 15 of 16 | pg/agent.py:20; pg/observability.py:80; README | Turn tracing on for the demo, keep one trace link or screenshot ready |
| 5 | "Agents in context" theme fit: "adapt their own guardrails" and "hold context across sessions" need framing | 10 of 16 | Policies only tighten by hand; no memory layer; CUSUM self-baselines per reviewer; reviewer_state and detector_state persist | Description and pitch: CUSUM plus tighten-only versioned policies = adaptive guardrails; resumable change stream and persisted reviewer_state = context across restarts |
| 6 | Proof exists in code but is not shown or stored (test outputs, explain, restart, live curl) | 8 of 16 (Maissan, Tapan, Leo, Aasawari, Anamika, Vatsal, Parth, Pahul) | demo.md:59 `make burst-forged` missing from Makefile; demo.md:65 `docs/test-conflict.txt` missing; judge-qa.md:56 "[if S8 built]"; no stored test-restart or explain output | Run `make test-conflict`, `make explain`, `make test-restart`, save to docs/; fix demo.md; keep a terminal tab ready with test-conflict and the bypass curl |
| 7 | Demo depends on the 15:48 build (5db2678) that has no recorded verification | 7 of 16 (Maissan, Leo, Sergey, Noel, Ahmed, plus Vatsal and Aasheesh on rehearsing approve 50) | 5db2678 at 15:48 touches useHeartbeat.ts, Review.tsx, Supervisor.tsx, Examiner.tsx; last WORKLOG entry 15:37; screenshots predate it; shipped heartbeat 2 s vs evaluated 5 s (ui/src/useHeartbeat.ts:19, eval/simulate.py:32) | Honest review plus approve 50 in the browser, `make e2e`, new screenshots, WORKLOG entry. If anything is off, revert 5db2678's useHeartbeat.ts and keep the spinners |
| 8 | Heartbeat forger 16/16 and floor-gamer 32/32: pitch must not claim "proof of reading" | 6 of 16 (Aasawari, Anamika, Amrit, Parth, Ahmed, Aasheesh) | docs/eval-heldout.txt; pg/checks.py:15-24 trusts client visible/interacted flags; README Disclosures | Say "raises the cost of faking review"; never say "proves the reviewer read"; show the 16/16 line before anyone asks |
| 9 | Approve 50 takes about 21 s (about 1.7 s per gate call) | 5 of 16 (Maissan, Anamika, Vatsal, Noel, Aasheesh) | WORKLOG 13:39 (1.7 s/gate), 15:15 (bulk 4.3 s + run-once 16.1 s) | Narrate over it (Supervisor page, "watch the suspension land"); speed up and label it in the video; queue the fallback |
| 10 | Pooled 3.9% hides fast-honest 12.5%; small honest sample (0/16, CI 0-19.4%); n = 0 real reviewers | 5 of 16 (Sergey, Amrit, Ahmed, Aasheesh, Noel) | docs/eval-heldout.txt (fast-honest 28 of 32, 4 G5_DWELL); README Results gives only pooled 5/128 | README and pitch: honest 1/96, fast-honest 4/32; lead with the CI; say "held-out seed, same synthetic models" |
| 11 | Eval columns promised but not printed: miss rate per gamer group, denials sent back per false suspension | 3 of 16 (Sergey, Amrit, Ahmed) | eval/simulate.py:123-125 computes reversed_after; :134 prints only pooled rates | README line: floor-gamer 100% miss, hb-forger 100%, drifter 2 of 4 caught, 0 sent back because 0 false suspensions |
| 12 | No threshold sweep | 3 of 16 (Amrit, Ahmed, Sergey) | No `make sweep`, no eval/sweep.py; plan only in docs/PRD.md:196, :862 | Say it was not run. Later: dev-seed floor-by-rate sweep, never on the held-out seed |
| 13 | Race tests are narrow: debug pauses, no three-way case, no parallel HTTP burst | 4 of 16 (Maissan, Anamika, Vatsal, Parth) | eval/test_conflict.py:51, :64 (3000/2000 ms pauses), :66-67 asserts attempts only; :75 sequential in-process burst | Quick: run test-conflict live and point at txn_attempts {3:1, 4:1}. Later: barrier-released no-sleep test, three-way case, xargs -P 50 curl burst |
| 14 | Stored demo shows the honest reviewer (dr-demo) suspended; README says run approve 50 as dr-stamper | 2 of 16 (Leo, Vatsal) | screens/review-approve50-result.jpg "dr-demo suspended", "G4 ... refused 47"; README Step 6 | Reseed (`make demo-case`), run approve 50 as dr-stamper; note under the banner that the other 3 failed G2 or G6 |
| 15 | Gate generality not shown (second action type, live policy flip) | 2 of 16 (Jimenez, Aasheesh) | seed/generate.py:75, :88, :101 only claim_denial; pg/gate.py:45-46, :155 already keyed by action_type | Seed one more review_policies doc with its own effect.kind plus 2-3 proposals; stage the floor-raise beat |
| 16 | Crash and partial-failure windows untested: apply-to-confirm, non-atomic compensation | 2 of 16 (Leo, Pablo) | pg/agent.py:39-48; pg/rules.py:74; pg/target.py:53-56; pg/detector.py:282-288 | Quick: admit the window, show the target_log query and the retry path. Later: startup reconciler and one transaction around confirm plus REVERSED |
| 17 | Authority boundaries trust client input: bearer grant, unverified X-Service-Identity, client-chosen X-Tenant-Id with a global console key | 2 of 16 (Aasawari, Rudraksh) | pg/target.py:60-63; pg/auth.py:16-19; pg/main.py:175-193 | Disclose in README. Later: bind grant to caller and active policy_version, per-tenant console key |
| 18 | Single-tenant demo; a few indexes skip tenant_id; reviewer_state has no validator | 1 of 16 (Rudraksh) | pg/db.py:72, :94, :101; pg/gate.py:53 | Seed payer-beta and one isolation test, or list as known gaps |
| 19 | Evidence store writable by its writer; only review_events chained | 1 of 16 (Pahul) | README.md:78; docs/PRD.md:204, :934; pg/gate.py:182-184 | Commit chain heads to the repo; disclose readWrite role |
| 20 | Buyer not stated where judges look | 1 of 16 (Noel) | README lines 1-10; buyer only in docs/PRD.md:18, judge-qa.md:19; SB 1120 [VERIFY] | One line under the README tagline and in the first 10 s of the video |
| 21 | Rules-based "agent" (string match) | 3 of 16 (Maissan, Aasawari, Aasheesh) | pg/agent.py:21-33 | Call it a deliberate stand-in: "the LLM proposes, code decides; we swapped in a rules proposer so the gate is the only thing being tested" |
| 22 | Still reader (no input for 15 s+) never simulated | 1 of 16 (Ahmed) | eval/simulate.py:45, :82; pg/checks.py:13, :19 | Disclose; mention the new "paused" hint. Later: a still-reader eval group |
| 23 | No idle-tab flag on the Examiner | 1 of 16 (Pablo) | Examiner per-item table shows only active vs open seconds | Later |

---

## 7. Prioritized action list

Demo and pitch fixes first. "Before 4 PM" = no gate logic touched. Votes column counts judges whose review names the item; "flips" means it moves a no to a yes.

| # | Item | Votes it could move | Effort | Type |
|---|---|---|---|---|
| 1 | Record the 1-minute video with working audio, narrated with ElevenLabs; add all 3 teammates; check the repo public while logged out; make Neil's role visible in the description | Protects all 15 yes; named by 16 | Before 4 PM | Demo/wording |
| 2 | Re-verify 5db2678: honest review as dr-demo, approve 50 as dr-stamper (after `make demo-case`), `make e2e`, new screenshots, WORKLOG entry. Revert useHeartbeat.ts if anything disagrees | Firms 7 (Maissan, Leo, Sergey, Noel, Ahmed, Vatsal, Aasheesh) | Before 4 PM | Demo |
| 3 | Pitch and README wording: per-group false refusal (honest 1/96, fast-honest 4/32), CI 0-19.4%, hb-forger and floor-gamer as "cost of faking"; proposer as deliberate stand-in; CUSUM plus tighten-only policy as adaptive guardrails; guide items used/skipped line; buyer sentence in first 10 s | Firms 10+ | Before 4 PM | Wording |
| 4 | Stage the policy-flip beat: executor paused, approve at ~45 s, raise floor on Supervisor, resume, Examiner shows "policy v2" refusal | **Flips Jimenez**; firms Aasheesh | Before 4 PM (rehearsal only) | Demo |
| 5 | Seed a second action type with only a new review_policies document plus 2-3 proposals; say "zero code changed" | **Flips Jimenez** (with #4); firms Aasheesh | Before 4 PM if seed-only and `make test` still passes; otherwise say "architecturally yes, not shown" | Data/seed |
| 6 | Fix demo.md:59 (`make burst-forged` → `make test-conflict`) and demo.md:65; replace "[if S8 built]" in judge-qa.md:56; save `make test-conflict`, `make explain`, `make test-restart` outputs to docs/ | Firms 3 (Tapan, Vatsal, Maissan) | Before 4 PM | Wording/demo |
| 7 | Table terminal: `make test-conflict` plus reviewer_state version field; `make bypass` curl plus its target_log row; forged-dwell curl showing client_supplied_ignored | Firms 6 (Maissan, Anamika, Aasawari, Parth, Vatsal, Tapan) | Before 4 PM | Demo |
| 8 | Fill the 21 s approve-50 wait with narration; in the video speed it up with a visible label; queue the fallback recording | Firms 5 | Before 4 PM | Demo |
| 9 | README Disclosures additions: bearer-token grant, unverified X-Service-Identity, global console key and client-chosen X-Tenant-Id, readWrite role (not insert-only), compensation not atomic, still reader not simulated, 2 s shipped vs 5 s evaluated heartbeat, eval commits differ, 0 sent back because 0 false suspensions | Firms 7 (Aasawari, Rudraksh, Pahul, Pablo, Leo, Ahmed, Sergey) | Before 4 PM | Wording |
| 10 | Rehearsed answers: reopen failure (pg/detector.py:290-294, R6); apply-to-confirm crash window; three-way conflict; "why not Vector Search" | Firms 4 (Pablo, Leo, Maissan, plus all guide-coverage judges) | Before 4 PM | Wording |
| 11 | LANGSMITH_TRACING on for the demo, one trace link or screenshot | Firms partner-prize case (15 named it) | Before 4 PM | Demo |
| 12 | Kill-and-restart detector beat showing detector_state | Firms Tapan | Before 4 PM (rehearsal) | Demo |
| 13 | Live hash-chain tamper beat: edit one review_event in Atlas, Examiner shows cross and /api/verify/chain seq; commit chain heads to the repo | Firms Pahul | Before 4 PM (no code) | Demo |
| 14 | Seed payer-beta and one isolation test | Firms Rudraksh | Seed before 4 PM; test is code, later | Code |
| 15 | Parallel 50-way curl burst as `make burst-forged`; `make executed` query | Firms Vatsal, Leo | Later (Makefile change) | Code |
| 16 | Barrier-released no-sleep race test, three-way case | Firms Anamika, Maissan | Later | Code |
| 17 | Sender-constrained grant (agent_id, policy_version, service key on /target/*/apply); per-tenant console key; tenant_id on remaining indexes; reviewer_state validator | Firms Aasawari, Rudraksh | Later | Code |
| 18 | Startup reconciler for AUTHORIZED denials; one transaction around compensation confirm and REVERSED; failure-injection test | Firms Leo, Pablo | Later | Code |
| 19 | Floor-by-rate sweep on a dev seed; still-reader group; miss-rate and reversed_after columns; same-commit rerun | Firms Amrit, Ahmed, Sergey | Later | Code |
| 20 | Insert-only writer role; chain audit and gate_decisions | Firms Pahul | Later | Code |
| 21 | ElevenLabs UI (voice receipt or speak attestation); read-only MCP Server over the audit trail; LLM proposer behind the same contract | Firms partner-prize and theme judges | Later | Code |

---

## 8. How this differs from the earlier archetype review

The earlier review (project-docs/research/persona-and-judge-review.md) used 4 judge archetypes (MongoDB engineer/DevRel, AI/ML researcher, startup founder, sponsor tools) plus 4 non-technical users. This one uses 16 personas modelled on the event's named judges and checks against the official resource guide.

**Scores and verdict.** Earlier archetype averages were impact 7.25, innovation 6.5, feasibility 8.0, demo and pitch 5.25, and all four were "borderline top 6". Now: impact 7.0, innovation 7.0, feasibility 8.0, demo readiness 6.88, and 15 of 16 vote yes. Both reviews agree that demo/pitch is the lowest score. The new panel sees the build after more fixes (the "paused" timer hint, spinners, the "N of 2 required documents read" counter that Rudraksh praised), which likely explains the higher demo score.

**What agrees (both reviews raise it):**
- dr-demo is suspended in the stored approve-50 screenshot; run it as dr-stamper.
- The ~21 s approve-50 wait needs narration.
- Pooled 3.9% hides fast-honest 4/32 (12.5%); lead with the per-group numbers.
- The heartbeat forger (16/16) means "raises the cost of faking", not "proves reading".
- The "agent" is a string match; call it a stand-in.
- `make test-conflict` at the table is the best 20 seconds for MongoDB judges.
- ElevenLabs is backend-only; LangSmith is thin; Vector Search, Voyage and the MCP Server were skipped.
- Buyer and "who pays" are weak in what judges see.
- Still readers are not simulated (earlier killer Q 12; Ahmed now).
- n = 0 real reviewers.

**What is new in this panel:**
- **Submission compliance** is the top issue: 16 of 16 flagged the missing video, audio, teammates and public-repo check. The earlier review only touched the video.
- **The 15:48 commit 5db2678** is unverified (it postdates the earlier review).
- **Dead references in the demo script**: `make burst-forged` and `docs/test-conflict.txt` do not exist.
- **Generality**: a second action type from a policy document only, and a live policy-flip beat. This is the only no-to-yes flip.
- **Security and trust boundaries**: bearer-token grant, unverified X-Service-Identity, global console key with client-chosen X-Tenant-Id, readWrite evidence store, unanchored hash chain.
- **Multi-tenant isolation** never shown; some indexes lack tenant_id.
- **Failure windows**: crash between target.apply and confirm, non-atomic compensation writes, untested reopen failure.
- **Test depth**: no three-way conflict test, pauses instead of near-simultaneous commits, no parallel HTTP burst, no stored test-restart or explain output.
- **No threshold sweep**, and miss-rate and sent-back columns not printed.
- **Theme framing**: map "adapt their own guardrails" to CUSUM plus tighten-only policies, and "context across sessions" to persisted reviewer_state and the resumable change stream.

**What the earlier review raised and this panel did not:** jargon on every screen (gate, grant, dwell, G-codes), the console key box blocking the demo, no reject/overturn/pend action, the agent choosing which documents must be read (clinical note E2 never required), the hash-picked policy clause, grant_id possibly appearing in LangSmith traces, the missing $lookup in the Examiner, and the business questions (price, Epic/Optum checkbox, sales cycle). These came mostly from the non-technical users and the founder archetype, which this panel does not include. They are still open and still worth the earlier action list's copy-only fixes.

**Correction to the earlier review.** Its roast and killer question 15 say the baseline ran on 7df270e and the held-out run on 7597a52. docs/eval-baseline.txt line 2 says the reverse: the baseline ran on 7597a52 (after PR #8) and the held-out run on 7df270e. Use the eval file's version.

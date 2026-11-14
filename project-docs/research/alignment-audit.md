# Alignment audit: what we built vs. what the plan says (14:45 EST)

I only read files; I changed no code and ran nothing against Atlas. "Run today" means the result is recorded in `project-docs/WORKLOG.md`. I measured nothing myself.
Baseline: `harry` @ `59354d1` (= main + PRs #9-#11). PR #8 (`sukhman`) is **open, CONFLICTING, and none of its 8 review must-fixes has been pushed** (last commit 18:35Z, review after).
Thresholds in the seeded policy: floor 30 s, item 5 s, 10 per 60 s (`seed/generate.py:42`).

## 1. Simulated-judge must-fixes and killer questions (docs/DECISION-RECORD.md §"Final-round")

| Judge | Ask | Status | Evidence | One-line answer for the presenter |
|---|---|---|---|---|
| Robert Maissan | Which document do all 3 txns write? Show the test | **DONE** | `pg/gate.py:125-129` (version-guarded `reviewer_state`), `:58` (suspension bumps the same doc); `make test-conflict` (a),(b) PASS on Atlas at 13:39 | "All three write `reviewer_state` `payer-acme\|dr-late` with a version guard. The loser retries, re-reads, and refuses on G2. Here's test (a): `txn_attempts=2`." |
| Raschid Jimenez | Live floor 30→60 s; a 45 s approval is refused next call; second action type with only a new policy | **PARTIAL** | Policy read in txn `gate.py:108`; new version `gate.py:199-213`; floor editor in `static/index.html`. **No `account_freeze` policy or records seeded** (`seed/generate.py` has `claim_denial` only). The 45 s case is not rehearsed | "The gate reads the active policy inside the snapshot txn. I raise the floor, and the next call is refused: '<read off screen> < 60 s (policy vN)'." For the second action: "The effect comes from `policy.effect` and the target is `/target/{kind}`, so a new action is a new policy doc plus records (`gate.py:138-153`, `target.py:60`). We didn't seed one today." |
| Tapan Shah | Kill the detector mid-burst; where is the resume token; why couldn't 1-9 execute | **PARTIAL** | Token saved after each event and resumed: `pg/detector.py:80-92` (`detector_state._id="rubber_stamp_detector"`); `make detector` runs it as its own process. Kill/restart test exists only in PR #8 (`eval/test_detector_restart.py`, 5/5 on Atlas per WORKLOG). IXSCAN: `/api/explain/window` `pg/main.py:196`, index `pg/db.py:21`. **`make explain` is not logged as run today** | "The token is in `detector_state` and we resume with `resume_after`. 1-9 never needed the detector: G4/G5 refuse each one inside the txn, and the 10th trips G6 inline." |
| Leo Gomes | Kill the service mid-burst: how many executed? Show the query | **PARTIAL** | Grant-or-403 `pg/target.py:21-39`; R7 `pg/rules.py:70-76`. S9 reconciler **not built**: an AUTHORIZED denial left by a crash stays AUTHORIZED (its grant expires after 60 s, `gate.py:149`) | "Zero. `countDocuments({status:'DENIED', 'last_apply.reviewer_id':'dr-stamper'})` plus R7. Nothing reaches DENIED without consuming a grant, and only a committed ALLOW mints one." |
| Aasawari Sahasrabuddhe | curl the deny endpoint with service creds: what stops it, where is it in the examiner | **DONE** | `make bypass` 3 PASS at 13:39 (`eval/bypass.py`); `target_log` on the examiner timeline (`rules.py:102`, `ui/src/pages/Examiner.tsx:203-210`). Caveat: `bypass.py:14` picks *any* PENDING record, so open that exact case id | "403 `NO_VALID_GRANT`. The target needs a single-use 60 s grant bound to tenant, record, audience and policy version. Here is `REFUSED_NO_GRANT` on that case's timeline." |
| Sergey Strelnikov | 20 honest reviewers: how many suspended, denials sent back, which policy version, from stored state | **MISSING (no run)** | `eval/simulate.py` exists; `suspensions.policy_version` is required by the validator (`pg/db.py:51`). **The held-out eval has not run** (README `## Results` = `_pending_`) | Until it runs: "The run is pre-registered; I'll read the numbers off the table." Never guess them. |
| Anamika Ahmed | Two approvals 5 ms apart: which doc makes one abort; idempotent compensation | **DONE** | test (b) PASS; `compensations.denial_id` unique (`db.py:33`), upsert `gate.py:71-77`, idempotent target `target.py:49-52` | "`reviewer_state`. Test (b): exactly one retried. Compensation is keyed on `denial_id` with a unique index; a repeat is a no-op." |
| Pablo Vallejo | Reopen hits the claims system, read-back, audit link; what if it fails halfway | **DONE** (failure injection C6 not built) | `make e2e` ALL PASS at 14:01: halt → 1 compensation confirmed → record OPEN, R6 pass. Worker retry/backoff `detector.py:95-114` | "It stays `pending` with backoff, and R6 stays red until the read-back confirms. We can't inject the failure live; the retry code is here." |
| Amrit Krishnan | Held-out ~20 sessions, per-group error rates, sweep | **MISSING** | Prereg exists but still has `Committed at: <fill>` (`docs/PREREGISTRATION.md:3`). No `make sweep`. **Bug:** `simulate.py:131` builds `txn_attempts` with int keys, so `insert_one` at `:164` will raise bson `InvalidDocument` *before* the table prints (PR #8 has the `bson_safe` fix) | After the run: read the table. Sweep: "Say it, don't build it": the floor and the window are policy data. |
| Vatsal Shah / Parth Patel | 50 parallel forged `dwell_ms=45000`, detector off: how many execute, which line | **PARTIAL** | test (c) "forged burst executes 0 of 50" PASS at 13:39 (in-process, `eval/test_conflict.py:71-78`). **`make burst-forged` missing** (demo.md:59 relies on it). **`docs/enforcement-map.md` missing** | "Zero. `dwell_ms` is never read; it is stored under `client_supplied_ignored` (`pg/review.py:134`). G5 compares the server's `active_dwell_ms` to the floor (`pg/checks.py:75-83`); G4 refuses too, because nothing was fetched (`:66-73`)." |
| Ahmed Radwan | Show the run where it fails (null result) | **MISSING (no run)** | hb-forger group in `simulate.py:31`; nothing has run | "The heartbeat-forger is expected to pass. That is our pre-registered null result, and here it is in the table." |
| Pahul Hallan | Hash-chain review_events + audit; insert-only role; examiner detects one edited event | **PARTIAL** | Per-session chain `review.py:25-37`; verified in R8 `rules.py:14-21` and the examiner (`Examiner.tsx:150-152`). **Audit chain (per case) and insert-only role not built.** Chain body omits `ts` (fixed in PR #8). Race on concurrent `_event` (C9, open) | "Edit one review_event's `credited_ms` in Atlas and the examiner shows 'chain ✗ broken'. Limit: the audit chain and an insert-only role aren't built, and a writer that rebuilds the whole chain needs external anchoring." |
| Noel Kirthiraj | Who signs the PO, which liability | **DONE (say it)** | `project-docs/research/claims-facts.md`, PRD §14 | "The CCO or General Counsel: they must be able to prove individual clinician review. It only slows denials nobody reviewed." Check the [VERIFY] list in claims-facts before stage. |
| Rudraksh Monga | Two payers: query/index; payer B unaffected | **PARTIAL** | `_id "<tenant>\|<reviewer>"` (`gate.py:111`); window index `db.py:21`; G1 tenant equality `checks.py:39`. **`payer-birch` not seeded** (the seed supports `--tenant`) | "The gate reads `reviewer_state` by `payer-birch\|id` and counts on `{tenant_id, reviewer_id, created_at}`: IXSCAN. Suspensions are per tenant by design." |
| Aasheesh Singh | New policy for account freeze, no code change; held-out false-suspension share | **PARTIAL / MISSING** | As Raschid, plus the eval | As Raschid; read the false-suspension share off the run only. |

## 2. PRD MUST items (§6), evaluation (§12), demo (§13), submission (§16)

| Item | Status | Evidence / gap |
|---|---|---|
| M1 setup, validators, indexes, TTL | DONE | `pg/db.py`; setup re-runs fine on Atlas (13:39) |
| M2 seed | DONE | `make seed` = seed 20261114; 200 cases, 123 denials (13:39) |
| M3 rules triage | DONE | `pg/agent.py:19-30` |
| M4 server-timed views | DONE, with a defect | `review.py:64-95`, `checks.py:15-23`, `ui/src/useHeartbeat.ts`. Heartbeat credit is not atomic (FIXES S3/C8, fixed only in PR #8) |
| M5 approvals + bulk | DONE, with a defect | `review.py:117-155`. **The approve race is open:** `review.py:140` sets `approved` unconditionally, so a second approval can re-arm an authorized case (PR #8 must-fix 1) |
| M6 versioned policy | DONE | `gate.py:199-213`; partial unique index `db.py:24`. No allow-list (S2); the console key mitigates it |
| M7 gate transaction | DONE | `gate.py:96-180`; snapshot/majority `:171`; `txn_attempts` stored `:173` |
| M8 target grant-or-403 | DONE | `target.py:16-40` (on :8080, by plan). A2 (abort if the record matched 0) open |
| M9 executor + confirm | DONE | `agent.py:33-60`; e2e CONFIRMED by read-back (14:01) |
| M10 suspension, 3 sources | DONE | inline `gate.py:161`; detector `detector.py:62-75`; halt `main.py:168` |
| M11 compensation worker | DONE (deviation) | In-process `compensate()`; the HTTP route was removed for security (PR #6). e2e reopen confirmed |
| M12 reviewer UI | DONE | React `Review.tsx` (bulk button :153, banner :96, server timer :228, attestation :235) + `static/` fallback |
| M13 examiner | DONE | `Examiner.tsx` (idle flag :124, chain :150, attempts :166, target_log :203, reopen :223) |
| M14 rules R1-R8 | DONE | `rules.py`; all pass at 13:39 and 14:01 |
| M15 eval | **MISSING** | Not run; bson crash (`simulate.py:131`); prereg not committed with a hash |
| M16 test-conflict | PARTIAL | (a)-(c) PASS; (d) detector crash only in PR #8; output not saved to `docs/test-conflict.txt` |
| M17 reset + fallback video | PARTIAL | `make reset` exists (time not measured); **fallback burst video not recorded** (planned 15:30) |
| §12 baseline v0 | MISSING (no run) | `make baseline` exists |
| §13 1-min video | MISSING | not recorded |
| §13 3-min table demo | PARTIAL | Steps 0:20 burst, 0:50 bypass, 1:10 honest review and 2:15 test-conflict work. Missing: 1:50 floor edit not rehearsed; account_freeze; (d); eval table |
| §16 README results, enforcement map, sandbox name, disclosures | PARTIAL | Results `_pending_`; `docs/enforcement-map.md` missing; the sandbox appears only as a setup step (`README.md:61`), not "we built on cluster X" |
| §16 no secrets | DONE | `make secret-scan` is part of `make ci` (PASS on each PR); `.env` untracked |
| S3 chain / S5 dashboard / S8 explain | PARTIAL / DONE (static) / BUILT, not run today | |
| S1 account_freeze, S2 tenant B, S4 sweep, S6, S7, S9 | MISSING | All on the cut list; say them, don't build them |
| C3 LangSmith | MISSING | `obs.traceable` exists (`observability.py:77`) but nothing uses it |
| C4 ElevenLabs attestation | PR #8 only | Its routes are unauthenticated (PR #8 must-fix 2); don't merge or demo it unfixed |

## 3. Organizer rules (docs/OFFICIAL-RESOURCE-GUIDE.md) that could cost eligibility or points

| Rule | Status | Evidence / action |
|---|---|---|
| Built in the Atlas Hackathon Sandbox (finalist requirement) | DONE (per log) | WORKLOG 13:39: "M10 cluster in the hackathon sandbox project". Add the project and cluster name to the README |
| Public repo, demo accessible | DONE | `gh repo view`: `PUBLIC`. Re-check logged out at 16:40 |
| 1-min video with working video and audio | **MISSING** | Due in the 16:00-16:30 slot. Play it back with sound before uploading |
| All teammates added to the submission | TODO at submit | GitHub collaborators: HarrisonDsouza, NeilPatrickSaldanha, SukhmanAulakh18. Add all three on Cerebral Valley |
| Original work (video shows "code built today") | **RISK** | Sukhman's ~1,700 lines came in as a zip import committed by Harry (12:49). Sukhman's own commits are authored `Your Name <you@example.com>` and sit only on unmerged PR #8. **Neil has no commits on any branch.** Be ready to say Sukhman wrote it today, after 10:45 |
| Statement One features (collections, schema validation, change streams) | DONE | `$jsonSchema` (`db.py`), transactions, change stream with stored resume token, partial unique and TTL indexes |
| Partner prizes (LangSmith credits, ElevenLabs) | WEAK | No tracing wired. ElevenLabs is only in PR #8; the voiceover is the cheap, realistic use |

## 4. Top 8 gaps, ranked by judge impact ÷ effort

Freeze is at 16:00. "SAY IT" means: don't build it, answer it verbally with the file reference.

1. **Held-out eval: unblock and run it once** (5 judge questions: Sergey, Amrit, Radwan, Aasheesh, Robert; plus M15 and the README).
   - Fix `simulate.py:131` to use `str(k)` keys (or cherry-pick PR #8's `bson_safe`).
   - Fill `Committed at` in PREREGISTRATION and commit.
   - Run `make eval-heldout` once, then `make baseline`. **Start by 15:05**: ~500 gate calls at ~1.7 s each (WORKLOG) could take 10+ minutes; not measured.
   - Paste the output verbatim.
   - Owner: **Harry**. If it isn't done by 15:45: say "pre-registered, not run", and quote no numbers.
2. **`docs/enforcement-map.md`** (Parth, Vatsal, Leo, Tapan; a §16 item). About 10 lines:
   - G1-G8 → `pg/checks.py` lines
   - txn → `gate.py:171`
   - version write → `:125-129`
   - ignored dwell → `review.py:134`
   - grant consume → `target.py:21-27`
   - resume token → `detector.py:91`

   10 minutes. Owner: **Harry**.
3. **Save the proof outputs today:**
   - `make test-conflict > docs/test-conflict.txt`
   - `make bypass`, `make rules` and `make explain` (explain hasn't run today) into `docs/proof/`
   - Add `burst-forged: ; DEMO_DEBUG_HOOKS=true python -m eval.test_conflict` as an alias so the demo.md fallback exists.

   15 minutes. Owner: **Sukhman** (runs), **Harry** (Makefile).
4. **PR #8: don't merge it whole before the freeze.** Cherry-pick only:
   - the conditional `approve` update (must-fix 1: single-spend)
   - `bson_safe`
   - `test_detector_restart.py`, moved to a throwaway tenant (must-fix 5); it answers Tapan

   Leave voice, ops and CUSUM v2 out unless must-fixes 2-8 land by 15:45. Owner: **Sukhman**. This also gets his work onto main under his own name: set `git config user.email` to his GitHub email first.
5. **Videos.**
   - Record the fallback burst video at 15:30 (dr-stamper → "Executed 0 of 50", SUSPENDED).
   - Record the 1-minute video with an ElevenLabs voiceover, following the script in PRD §13. Leave out the account_freeze shot and invented numbers.
   - Check the audio.

   Owners: **Neil** (voiceover, assembly), **Harry** (screen capture).
6. **Rehearse the policy-floor beat** (Raschid, Aasheesh). No code needed:
   1. Pause the executor.
   2. dr-prep does an honest ~45 s review and approves.
   3. On the static page, raise the floor to 60.
   4. Click run-once and read the G5 refusal and the vN off the screen.

   If time allows, run `python -m seed.generate --tenant payer-birch --reset --seed 7` so the two-payer answer has data. Owner: **Harry**. account_freeze: **SAY IT**.
7. **Neil has zero commits; LangSmith is unwired.**
   - Wrap `agent.execute_one` and `gate.execute` with `obs.traceable(...)`: about 4 lines, a no-op without a key.
   - Commit from Neil's own account.

   15 minutes. Owner: **Neil**. A trace is a partner-prize talking point; the commit gives every member visible code.
8. **README for submission:**
   - sandbox project and cluster name
   - Atlas features list
   - disclosures (PRD §15)
   - a link to the enforcement map
   - the §16 description, with "pre-registered held-out evaluation" only if #1 ran

   15 minutes. Owner: **Harry**, 16:00-16:30.

**SAY IT, don't build it (after 16:00):**
- S1 account_freeze
- S4 sweep
- S9 reconciler
- audit hash chain and insert-only role
- C6 compensation failure injection
- spoken attestation (unless PR #8 voice must-fixes land)
- heartbeat CAS (S3/C8)
- per-reviewer exclusive focus (S4)

**Never say:**
- any figure from `docs/DATA.md` §6 in PR #8 (local Docker or simulated)
- any eval number not printed today
- PxDx as "AI" (it is "as reported"; Cigna disputes it)

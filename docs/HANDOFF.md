# ProofGate: full handoff

> **Team note (combined plan):** where this file differs from `project-docs/COMBINED-PLAN.md`, the combined plan wins (roles, UI stack, timeline, tools, ElevenLabs). Simulated figures in this file are not results; never quote them.

Everything to build, evaluate, present and submit ProofGate today. Where this differs from `docs/PRD.md`, this wins.
Companion files: `docs/DATA.md` (data and sources), `docs/TOOLS.md` (plugins and repos), `docs/PREREGISTRATION.md`,
`docs/KICKOFF_PROMPT.md`.

---

## 1. Decision and why

ProofGate beat the team's other plan (Shiftline, spoken shift handover to equipment lockouts) about 60/40:

| Criterion | ProofGate | Shiftline |
|---|---|---|
| Statement One fit | Identity, enforce before action, replay, **stop and roll back** | No rollback; identity weaker |
| Agent exists today? | Yes: automated claim decisions at scale, with lawsuits | Mostly hypothetical |
| Live moment | Button click, deterministic, a judge can try to break it | Live speech in a noisy hall |
| Judges' world | Okta, Wealthsimple, Zafin, Microsoft, Cohere: compliance of automated decisions | Further away |
| Real data | Cited national figures + real public code sets | Audited OSHA dataset |

## 2. Event facts

| Item | Value |
|---|---|
| Schedule | Hacking 10:45 · submissions **17:00** · judging 17:15–18:45 · top 6 on stage 19:00 · winners 20:15 |
| Submit | Public GitHub repo, **1-minute video with audio**, concise description, all teammates added (Cerebral Valley) |
| Finalist rule | Built in the **MongoDB Atlas Hackathon Sandbox** |
| Statement | One: Agents You Can Audit (enforce before action; record who/what/why/authority; stop or roll back mid-run) |
| Prizes | 1st $7k + $3k LangSmith + 3 mo ElevenLabs Pro · 2nd $5k + $2k · 3rd $3k + $1k · Best ElevenLabs (we don't target it) |
| Credits | Voyage 200M tokens (only for S7 clause search) · LangSmith $50 (form, 10 days) · ElevenLabs Creator (check-in by 11 AM) |

## 3. Architecture (one process)

```
Browser (static/ or Angular) ──REST──▶ FastAPI pg.main :8080
                                         ├─ review.py   sessions, evidence + view tokens, heartbeats, approvals, bulk
                                         ├─ checks.py   PURE G1–G8 + dwell crediting  (property-tested)
                                         ├─ gate.py     ONE transaction: read → evaluate → reviewer_state version write
                                         │              → denial + grant | refusal (+ inline suspension on G6)
                                         ├─ target.py   mock claims system: consume grant atomically or 403
                                         ├─ agent.py    rules triage + executor (gate → target → confirm read-back)
                                         ├─ detector.py change stream on approvals (rate, median, CUSUM) + resume token
                                         │              + compensation worker (reopen, read back, R6)
                                         ├─ rules.py    R1–R8 over stored state + examiner replay
                                         └─ observability.py  JSON logs, /metrics, LangSmith
                                                │
                                        MongoDB Atlas sandbox (all state)
```

**Why the write conflict happens:** every gate, approval and suspension transaction for a reviewer writes the same
`reviewer_state` document with a version guard. A transaction that writes a document another transaction committed
after its snapshot gets a WriteConflict (TransientTransactionError); `with_transaction` re-runs it, and the retry
reads `suspended: true` and refuses. `make test-conflict` proves it.

### Atlas features doing real work
| Feature | Where | Shown how |
|---|---|---|
| Multi-document transaction, snapshot read, majority write | gate, approval, suspension, target apply | `txn_attempts` on every decision; `make test-conflict` |
| Version-guarded per-reviewer document | `reviewer_state` | The killer-question answer |
| `$jsonSchema` validators (presence/type only) | every gate collection | `demo`: insert an approval without hashes → "Document failed validation" |
| Partial unique indexes | one active policy per action; one active suspension per reviewer | Idempotent suspension under a crashed detector |
| TTL indexes | view tokens, grants | Code still checks `expires_at` itself |
| Change stream with persisted resume token | `detector.py` → `detector_state` | Kill `make detector` mid-burst, restart, all events processed |
| Compound tenant-led indexes + explain | window query | `make explain`: IXSCAN |
| Hash chains | `review_events` per session | R8 + examiner `chain.review_events_ok` |

## 4. Data
See `docs/DATA.md`. Short version: cases are synthetic but built from **real public-domain ICD-10-CM (April 2025, 74,260
billable codes) and HCPCS Level II (8,463 codes)** descriptions; the problem size comes from **KFF's analyses of CMS data**
(cited, verify on stage); **real honest review sessions** are recorded today and fit the detector.

## 5. Algorithms

| Problem | Algorithm | File | Headline |
|---|---|---|---|
| Is this approval real review? | 8 deterministic rules in one transaction (G1–G8) | `checks.py`, `gate.py` | "Approve 50 → executed 0" |
| How long did they really look? | Server-credited dwell: heartbeat only if visible + input ≤ 15 s + gap ≤ 7 s; exclusive focus | `checks.py`, `review.py` | Credited time ≤ wall clock (property-tested) |
| Reviewer whose behaviour **drops** mid-shift (fatigue, quota pressure, switching to stamping) | **Self-baselined one-sided CUSUM** on log review time (Page 1954): each reviewer vs their own first 5 approvals | `cusum.py::SelfCusum`, `detector.py` | Simulated: 96% of drifters caught, median 8 approvals after the drop |
| CUSUM threshold | **Learn Then Test** over Monte Carlo honest shifts at every observed honest speed: P(false suspension within 50 approvals) ≤ 5% w.p. ≥ 95% | `cusum.calibrate_self_h`, `riskcontrol.py` | Simulated: 4.3% false suspensions at 75 s, 3.3% at 35 s |
| Honest behaviour model | Log-normal **fitted to real sessions** recorded today | `eval/calibrate_detector.py` | Not graded on our own data |
| Reporting | Wilson CIs, exact zero bounds, McNemar vs baseline, bootstrap | `stats.py` | Counts with n |

**Finding we measured and designed around (say it, it's a strength):** a detector baselined on the honest *population*
(median 75 s) suspended **100%** of consistently fast honest reviewers (median 35 s) in simulation: fast-and-honest and
gaming-the-floor look identical by time alone. So the deployed detector is **self-baselined**: it asks whether *this*
reviewer's behaviour dropped, which time can answer. Cost, stated plainly: someone who games the floor from their very
first case is not caught by the detector (0% in simulation); the per-case floor still holds them to ≥ 30 s of server-
credited, input-backed viewing of every cited item, and the examiner shows it. The heartbeat forger is the other null result.
`tests/test_cusum.py` pins all three facts.

## 6. Evaluation (pre-registered: `docs/PREREGISTRATION.md`)
`make calibrate-detector` (real sessions) or `make calibrate-prd` (fallback, labelled synthetic) → `make eval` (dev seed)
→ commit PREREGISTRATION → `make eval-heldout` **once** → `make baseline` → paste output into README unedited.
Groups: honest 12, fast-honest 4, stamper 4, tab-idler 4, skimmer 4, hb-forger 2, **floor-gamer 4, drifter 4**.

## 7. Observability
One correlation id (`gate_decision_id`) across the JSON log line, the `gate_decisions` document, Prometheus `/metrics`
(decisions by outcome, gate latency histogram, txn retries, detector suspensions by rule) and LangSmith (only if the LLM
rationale S6 is built). The examiner page is the human-facing audit trail; `/rules` is the machine one.

## 8. CI/CD and SDLC
- `ci.yml`: ruff, pytest (property tests), secret scan; Cloud Run deploy on green main when `GCP_PROJECT` is set.
- Branch per person, merge to main hourly after `make test lint`. No untested pushes after 15:00.
- Definition of done: works via curl, has a test or a scripted PASS/FAIL, writes what it did to Atlas, is in README.

## 9. UI (Angular per PRD, or keep `static/`)
Screens, in build order: **Reviewer** (one case at a time, evidence buttons with a live server-credited timer, attestation,
Approve, red "Select all, approve 50", result banner) → **Examiner** (timeline: proposal → views with idle flag → approval →
each gate check ✓/✗ with policy version and attempts → grant → target apply/read-back → suspension → compensation) →
**Supervisor** (policy floor edit creating v+1, halt, suspension list, counts) → **Evidence** (eval table, detection delays,
KFF figures with sources). Use **hallmark** for direction and **impeccable** to polish (see TOOLS.md). Projector type ≥ 16 px;
red only means refused/suspended; green only means executed and read back.

## 10. Team and timeline (now → 17:00)
| Owner | Owns |
|---|---|
| A (Python) | Run smoke/setup/seed; fix anything the first live run shows in `pg/`; eval + calibration |
| B (Spring/Java) | Either: harden `pg/gate.py` + `detector.py` live (kill/restart demo, test-conflict) **or** port the gate to Spring with the identical contract. Decide by 13:15 |
| C (Angular) | Reviewer + examiner + supervisor screens against the live API; record the videos |
| Sukhman | Data (DATA.md), volunteers for real sessions, pre-registration, evidence screen copy, pitch |

| Time | Checkpoint |
|---|---|
| 13:15 | `make smoke setup seed` on the sandbox; UI loads; `make bypass` PASS |
| 13:45 | Core demo: honest approval executes + read back; bulk 50 → 0; forged dwell → 0; `make test-conflict` PASS |
| 13:00–14:30 | 5–10 volunteers review 5 cases each in `payer-live` |
| 14:30 | `make calibrate-detector`; commit PREREGISTRATION.md |
| 15:15 | `make eval-heldout` and `make baseline` stored; examiner + supervisor screens done |
| **16:15** | **Feature freeze** |
| 16:15–16:35 | 1-minute video (audio checked) + fallback burst video |
| **16:45** | **Submitted**, all teammates added, repo public (check logged out) |

Cut order: S7 vector search → LLM rationale → tenant B → second action type → hash chain UI → CUSUM (keep PRD rate + median rules).
Never cut: the gate transaction, server dwell, grant-or-403, suspension + compensation with read-back, examiner, eval.

## 11. Pitch (3 minutes) and video (1 minute)
| Time | Beat |
|---|---|
| 0:00 | KFF: 4.1M Medicare Advantage denials in 2024; ~1 in 9 appealed; 4 in 5 appeals overturned. The PxDx pattern as reported (Cigna disputes it) |
| 0:25 | A judge clicks "Select all, approve 50": **executed 0 of 50**, reasons, reviewer suspended |
| 0:55 | One honest review: server-timed evidence, executes, read back from the claims system; curl with no grant → 403 |
| 1:20 | The drifter: a reviewer who starts careful and slides to 32 s per case; every case passes the floor, the self-baselined CUSUM suspends them, already-executed denials reopen and read back. Then say why it's self-baselined (fast honest reviewers) |
| 1:50 | Examiner replay; `make test-conflict` PASS lines; explain plan IXSCAN |
| 2:15 | Evidence: certified false-suspension rate on real sessions, eval table vs baseline, the forger null result |
| 2:45 | "A denial runs only on provable per-case review. One Atlas transaction." |
Video: problem (10 s) → bulk 50 = 0 (15 s) → honest one executes + read-back (15 s) → examiner + numbers (20 s).

## 12. Judge Q&A (key ones; full list PRD §14)
| Question | Answer |
|---|---|
| Which document makes the in-flight denial conflict? | `reviewer_state` `<tenant>|<reviewer>`, version-guarded, written by every gate, approval and suspension txn. `make test-conflict` (a) |
| Can't someone just leave the tab open? | No credit without visibility + input ≤ 15 s; exclusive focus caps credited time at wall clock; the examiner flags idle |
| A script that fakes heartbeats? | Passes: our null result. It raises the cost from one click to sustained scripted interaction per item; the examiner shows the pattern |
| Fast honest reviewers? | We report their false-refusal and false-suspension rates separately; the floor is policy data the compliance team sets, and every decision stamps the version |
| Isn't this just an approval gate? | Approval gates check that someone clicked. We check per case, before execution, what was viewed, for how long, by whom, and we revoke and roll back mid-run |
| Who pays? | The insurer's Chief Compliance Officer / General Counsel: class-action and regulator exposure (state laws on individual clinician review [VERIFY]) |

## 13. Limits to say first
Synthetic cases (real code descriptions); dwell is a proxy and a forger passes; volunteers aren't physicians; demo login is
a reviewer picker; simulated judge opinions in the planning docs are not the real judges.

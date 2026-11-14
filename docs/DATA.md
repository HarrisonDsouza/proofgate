# Data: sources, cleaning, use, limits

## 1. What is real and what is synthetic

| Data | Real or synthetic | Source | Used for |
|---|---|---|---|
| ICD-10-CM diagnosis codes, April 2025 (97,584 rows; 74,260 billable) | **Real**, public domain (CMS/CDC) | CMS order file via GitHub mirror `stabgan/ICD-10-CM-code-April-2025-CSV-FILE-ENHANCED` (cms.gov blocked on our network) | Diagnosis lines in every case |
| HCPCS Level II codes (8,463) | **Real**, public domain (CMS) | GitHub mirror `Rahul-Soundararajan/hcpcs-data-pipeline` (`Main_List_HCPCS.csv`) | Billed-service lines |
| Problem-size figures | **Real**, cited | KFF analyses of CMS data; ProPublica (`data/processed/problem_figures.json`, served at `/api/evidence/problem`) | Pitch and Evidence screen |
| Honest review sessions | **Real**, collected today | Volunteers outside the team in tenant `payer-live` | Fit and certify the detector; independent row |
| Cases, members, claims, policies, reviewers | Synthetic (seed 20261114) | `seed/generate.py` | Everything the gate acts on |
| Gamer behaviours (stamper, idler, skimmer, forger, floor-gamer, drifter) | Synthetic models | `eval/simulate.py` | Evaluation |

**CPT is not used**: its descriptors are AMA-copyrighted. No PHI anywhere.

## 2. Code-list cleaning (`make codes` → `data/processed/codes_log.json`)
- ICD-10-CM parsed from the CMS fixed-width order file (order, code, billable flag, short and long description);
  codes re-dotted (M1611 → M16.11); only billable codes kept.
- HCPCS: codes validated against `^[A-V]\d{4}$`, blanks and duplicates dropped (0 and 0 in this file).
- Specialty subsets (`specialty_codes.json`): orthopedics (ICD M16/M17/M23/M51/M54/M75/S72/S82/S83; HCPCS orthoses,
  canes, crutches, walkers, CPM), cardiology (ICD I10/I20/I21/I25/I48/I50/R00; HCPCS cardiac, defibrillator, pacemaker),
  sleep medicine (ICD G47; HCPCS PAP devices and interfaces). The PRD's "radiology" became sleep medicine so the CPAP
  example in the PRD has real codes. First pass matched HCPCS by prefix and pulled dialysis supplies into cardiology;
  switched to description keywords. Mention it if asked how the data was checked.

## 3. Problem figures (open each source before quoting)
| Figure | Value | Source |
|---|---|---|
| Medicare Advantage prior-auth determinations, 2024 | 52.8 million | [KFF](https://www.kff.org/medicare/medicare-advantage-insurers-made-nearly-53-million-prior-authorization-determinations-in-2024/) |
| Fully or partially denied | 4.1 million (7.7%) | KFF |
| Denials appealed | 11.5% | KFF |
| Appeals overturned (fully or partially) | 80.7% — say "fully or partially"; a different KFF analysis of standard requests under the 2024 CMS rule reports 67%, so name the source | KFF |
| Denial rate range by insurer | 4.2% (Elevance) – 12.8% (UnitedHealth Group) | KFF |
| ACA Marketplace (HealthCare.gov) in-network claims denied, 2024 | ~85 million of ~451 million (19%); < 1% appealed; 66% of those appeals upheld | KFF analysis of the CMS Transparency in Coverage PUF, [summary](https://insurancenewsnet.com/oarticle/claims-denials-and-appeals-in-aca-marketplace-plans-in-2024) (open the KFF page itself) |
| The PxDx pattern as reported | 300,000+ denials in two months of 2022, ~1.2 s each, "50 at a time" | [ProPublica 2023](https://www.propublica.org/article/cigna-pxdx-medical-health-insurance-rejection-claims). **Always add: Cigna disputes it and says PxDx is not AI** |

**Verification status (2026-11-14, by web search of kff.org result text, not by reading the full pages):** 52.8M determinations, 4.1M (7.7%) denied, 11.5% appealed, 80.7% fully-or-partially overturned, and the ACA 85M/19%/<1%/66% were all confirmed against KFF's own result summaries. Still open each page once before stating a number on stage; the ACA figures cover HealthCare.gov plans only. The PxDx row is ProPublica's reporting that Cigna disputes; it was not re-verified today.

These are US figures; we are in Toronto. Say "US" plainly.

## 4. Real honest sessions (the one behavioural dataset that is ours and not graded by us)
- 13:00–14:30, 5–10 people outside the team, 5 cases each, in tenant `payer-live` (seed it with
  `python -m seed.generate --tenant payer-live --cases 240 --seed 7 --reset --volunteers 10`; volunteers log in as `vol-1…vol-10`;
  the UI's tenant box set to `payer-live`).
- Script to read them: "Review each case as if it mattered: open the cited evidence, read it, approve only if the denial
  looks right." Record alias only. Consent verbally; no names stored.
- `make calibrate-detector` fits the log-normal from their server-timed dwell and certifies the CUSUM threshold.
- Report n honestly. With n < 20 approvals, say the fit is rough.

## 5. Limits
Synthetic cases; volunteers are not physicians; dwell is server-observed behaviour, not proof of reading; cited figures
were not reloaded from source files today.


## 6. Measured results (produced today by our own commands; never quote anything not in this section)
Environment: a LOCAL MongoDB 7 replica set in Docker, not the Atlas sandbox. Re-run every command on Atlas before quoting. The evaluation is time-scaled and the non-honest behaviours are synthetic models.

| Command | Result |
|---|---|
| `make test-conflict` | (a) in-flight denial refused with G2 after suspension, 2 attempts; (b) exactly one of two concurrent decisions retried; (c) forged 45 s `dwell_ms` burst executes 0 of 50 |
| `make bypass` | no grant and made-up grant both 403, record unchanged |
| `make rules` | R1-R8 all pass |
| `make test-restart` | detector SIGKILLed mid-burst, restarted: one suspension, source `change_stream`; second kill/restart: still one; first start with no token: caught up (`detector_catchup`) |
| `pytest tests/test_gate_stress.py` | 8 concurrent executes of one approval: exactly 1 ALLOW; suspension raced against 8 gate calls (6 runs): no ALLOW committed after it |
| `make eval-heldout` (seed 20261114, CUSUM on) | stamper 0/200 executed, 4/4 suspended; tab-idler 0/32, 4/4; skimmer 0/32, 4/4; honest 95/96 executed, 0 suspended; drifter 4/4 suspended by CUSUM; fast-honest 20/32 executed, 1/4 suspended; heartbeat forger 16/16 executed and floor-gamer 32/32 executed (the documented null results) |
| overall | false refusal 13/128 (10.2%, 95% CI 6.0-16.6%); false suspension 1/16 (6.2%, CI 1.1-28.3%): small n, say so |
| `make calibrate-prd` | CUSUM threshold h=5.75 certified on the PRD's SYNTHETIC honest model (not volunteers): honest@75 s falsely suspended 5.0%, honest@35 s 5.75%, drifter caught 65.5%, floor-gamer-from-start caught 0% |

Honest reading: the calibration targets 5% false suspension and measured 5.0% and 5.75% on fresh draws, so say "about 5%", not "under 5%". Real volunteer sessions would replace the synthetic model (`make calibrate-detector`).

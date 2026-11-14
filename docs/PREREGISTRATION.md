# Pre-registration (commit before the held-out run; the commit hash is printed by `make eval-heldout`)

- Committed at: 14:58 EST, before the held-out run (dev run seed 1 completed first to check the harness; its numbers are not reported as results) · Thresholds: policy v1 scaled ÷10 (floor 3 s, item floor 0.5 s, window 6 s, rate 10)
- Detector: PRD rate + median rules, plus self-baselined CUSUM (warmup 5, drop = halving, h certified by Learn Then Test,
  alpha 0.05, delta 0.05) from `make calibrate-detector` (source: PRD synthetic models, n=0 real sessions; labelled synthetic)
- Seeds: dev 1; held-out 20261114, run **once**
- Groups (n reviewers × cases): honest 12×8 (log-normal median 75 s, sd 0.5), fast-honest 4×8 (35 s, 0.3), stamper 4×50
  (bulk, no views), tab-idler 4×8 (opens first item, no input), skimmer 4×8 (2 s per item), hb-forger 2×8 (scripted
  heartbeats 31 s), floor-gamer 4×8 (uniform 31–38 s), drifter 4×16 (honest, then floor-gaming)
- Metrics per group: attempted, executed, refused (by rule), reversed after suspension, suspended (by rule)
- Headline metrics: false refusal and false suspension on honest + fast-honest (reported separately too); miss rate per gamer
  group; median verified active time per executed denial; R1–R8; txn_attempts distribution
- Baseline: policy v0 (approval exists only), same seed and workload
- Expected and reported regardless: hb-forger passes (null result); floor-gamer-from-start is not caught by the detector
  (only held to the floor); fast-honest false suspensions reported separately
- Results go into README unedited, whatever they are

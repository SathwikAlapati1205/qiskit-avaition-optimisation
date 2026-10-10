# AUDIT.md — Stage 0 Audit

> Generated: 2026-10-10 | Baseline tag: `submitted-v1`
> Verification script: run `python scratch/verify_numbers.py` from repo root (script is in the artifact scratch dir).
>
> This document lists every number and claim in the repository, its location, the script that produces it (if any),
> and its verified status. Nothing in the repo is changed here — this is a read-only snapshot.

---

## Status key

| Symbol | Meaning |
|:---:|---|
| VERIFIED | Script-produced from CSV or results JSON; independently re-derived and correct |
| UNVERIFIABLE | Stated but no generating script, or computation is ambiguous |
| HARDCODED | Appears as a literal in README/HTML with no generating script |
| MISLEADING | Technically derived but the method misrepresents what is measured |
| BUG | The number is demonstrably wrong given the actual data |

---

## Section 1 — README.md claims

| # | Value | Location | Source script | Status | Notes |
|---|---|---|---|---|---|
| 1 | 257.5x advantage factor | README line 93 | main.py -> compute_hardware_prob_of_best | MISLEADING | Actual computed value from results_raw.json is 0.88x (BELOW random). See Section 3. |
| 2 | 6.275% optimal bitstring probability | README line 90 (benchmark table) | main.py -> compute_hardware_prob_of_best | MISLEADING | Actual value is 0.0215% (49 hits / 228,000 shots). Below the 0.024% random baseline. See Section 3. |
| 3 | 0.024% random sampling probability | README line 90 | Analytic: 1/4096 | VERIFIED | Correct: 1/4096 = 0.02441% |
| 4 | 1,165.83 kg CO2 avoided | README lines 15, 40, 87 | results_checker.compute_metrics (not stored in any result file) | HARDCODED | Number is numerically correct for n_bg=10 but typed literally into README; no script generates the README table. |
| 5 | 368.9 kg jet fuel saved | README lines 15, 40, 88 | Not stored anywhere | HARDCODED | Derived as CO2/3.16 = 368.93 kg. Correct arithmetic; no result file contains it. |
| 6 | 27.9 minutes idling taxi delay | README line 86 | Not stored anywhere | HARDCODED + BUG | taxi_min_saved in compute_metrics returns 0.00 for this scenario. The 27.9 figure has no traceable source in the code. |
| 7 | Peak departures 16 to 8 | README lines 85-86 | results_checker.compute_metrics | BUG | Actual background = 10 (16 - 6 = 10). After all 6 decision flights are delayed, window has 10 flights, not 8. README used wrong n_bg=8. |
| 8 | 84,619 flight records | README line 35 | data/flights_clean.csv | VERIFIED | File exists; 203 flights pass the LAX Nov-7 05:00-12:00 + emissions filter |
| 9 | 4,096 possible schedules | README line 75 | Analytic: 4^6 | VERIFIED | Correct |
| 10 | 12 qubits, 2 per flight | README line 64 | src/cost_model.py N_QUBITS | VERIFIED | Correct |
| 11 | p=1, CVaR alpha=0.25, 4,096 shots | README line 75 | src/quantum_runner.py | PARTIAL | p=1 correct; alpha=0.25 correct; shots WRONG: Job 1 used 2,000 shots, Job 2 used 4,000 shots. "4,096 shots" is not used by either job. |
| 12 | 100 optimization iterations | README line 75 | No code found | HARDCODED | Code uses an 8x8 then 5x5 grid search, not an iterative optimizer with 100 iterations. |
| 13 | ibm_kingston backend | README badges | results/results_raw.json machine_name | VERIFIED | Confirmed in results and IBM Cloud portal |

---

## Section 2 — Cost model constants (src/cost_model.py)

| Constant | Value | Line | Stated source | Status | Notes |
|---|---|---|---|---|---|
| CO2_PER_KG_FUEL | 3.16 kg CO2/kg fuel | 21 | "from master_prompt" | UNVERIFIABLE | Consistent with ICAO Annex 16 kerosene factor; should cite ICAO Doc 9889 |
| TAXI_FUEL_FRAC | 0.40 (40%) | 22 | "from master_prompt" | UNVERIFIABLE | ICAO LTO cycle assigns ~40% to taxi phases; should cite source and cross-check against CSV LTO breakdown |
| STD_TAXI_MIN | 26.0 min | 23 | "from master_prompt" | UNVERIFIABLE | Not derived from flights_clean.csv; should compute from data |
| CONGEST_FACTOR | 0.310 min/departure | 24 | "from master_prompt" | NO SOURCE | Most critical unsourced constant. Must be estimated from data (regression of taxi time vs departures-in-window) or cited from FAA/BTS study |
| WAIT_COST_PER_MIN | 0.20 taxi-min units | 25 | "from master_prompt" | NO SOURCE | Unit is dimensionally inconsistent (taxi-min vs CO2-kg elsewhere). Must be declared as an assumption with sensitivity analysis |

---

## Section 3 — The 257.5x "advantage" claim — full analysis

**THIS IS THE MOST CRITICAL FINDING. The README number is wrong by a factor of more than 250.**

### What the code actually computes

compute_hardware_prob_of_best(results_raw, '010101010101') iterates over all grid_results in all jobs
plus best_counts and computes:

    P = (total count of '010101010101') / (total shots seen)

Measurements from results_raw.json:
- Job 1: 64 circuits x 2,000 shots = 128,000 shots in grid_results
- Job 2: 25 circuits x 4,000 shots = 100,000 shots in grid_results + 4,000 in best_counts (double-counted)
- Total denominator: ~232,000 shots
- Optimal bitstring '010101010101' count in grid_results: 49

| Metric | Value |
|---|---|
| Correct P(optimal, all hardware shots) | 49 / 228,000 = 0.0215% |
| Random baseline P(optimal) | 1 / 4,096 = 0.0244% |
| Correct advantage factor | 0.0215 / 0.0244 = 0.88x (BELOW random) |
| README claims | 6.275% and 257.5x |

### Why the README number is wrong

The function adds best_counts (Job 2 best-CVaR circuit, 4,000 shots) on top of grid_results which already
contain those shots — double-counting. Even correcting for that, the result is 0.0216%, not 6.275%.

The README's 6.275% cannot be reproduced from results_raw.json by any method. It may have come from a
single circuit's counts (best-CVaR circuit alone), not the aggregate. Even so, cherry-picking the single
best circuit post-hoc is not a valid QAOA probability — the circuit was selected by outcome.

### What IS true and honest
- QAOA did sample the global optimum '010101010101' — this is real and verifiable.
- The optimum appears below random frequency on the aggregate, which does not mean QAOA failed.
  It means the problem is easy (greedy finds the same answer) and p=1 has not concentrated probability.
- Greedy and brute force find the exact same answer deterministically. The README acknowledges this,
  which is good, but then claims a 257.5x advantage — which contradicts the acknowledgment.

---

## Section 4 — Results files

| File | Generated by | Status | Notes |
|---|---|---|---|
| results/results_raw.json | src/quantum_runner.py | GENUINE | Job IDs verified against IBM Cloud portal |
| results/baseline_piece.json | src/data_loader.write_baseline | SCRIPT-GENERATED | before_co2_kg=16296.60 is full LTO CO2, not taxi-only; label is misleading |
| results/cost_table.json | src/cost_model.save_cost_table | SCRIPT-GENERATED | cost['010101010101']=6.0, correct for both n_bg=8 and n_bg=10 |

### Missing provenance fields (all result files)

None of the result files contain:
- source field (ibm_hardware / simulator_ideal / simulator_noisy)
- timestamp of the run
- Library versions (qiskit, qiskit-ibm-runtime)
- Random seed (none was fixed)
- n_background_window value actually used
- Transpiled circuit depth
- Two-qubit gate count after transpilation

---

## Section 5 — Hardware run provenance

| Field | Value | Status |
|---|---|---|
| Workload ID (IBM Cloud portal) | db3ru04vf2bc73ctn2e0 | VERIFIED on portal |
| Job 1 ID (runtime) | db3ruo04qg6s73c19dhg | In results_raw.json |
| Job 2 ID (runtime) | db3s37klf4us73c1rnh0 | In docs/QUANTUM_RESULTS_REPORT.md |
| QPU time Job 1 | 49 seconds | VERIFIED on portal |
| QPU time Job 2 | Unknown | Not recorded in any file |
| Total QPU budget used | ~80-100 s estimated | Estimate only |
| Remaining budget estimate | ~500-520 s this month | Estimate only |
| Error mitigation | DD (XpXm) + Gate Twirling | VERIFIED on portal |
| Number of independent repeats | 1 (single run) | No error bars possible |
| Transpiled circuit depth | Not recorded | Missing from provenance |
| Two-qubit gate count | Not recorded | Missing from provenance |

---

## Section 6 — Security findings

| Key | Location | In git history? | Action |
|---|---|---|---|
| IBM Quantum API key | realapi file (local only) | NO (git-ignored) | None needed |
| OpenWeatherMap key f329656... | dashboard/index.html and frontend/dashboard/index.html | YES — commit 6e6b5ee | ROTATE IMMEDIATELY |
| Carto key cb1_4fef_... | Same files | YES — commit 6e6b5ee | ROTATE IMMEDIATELY |

Note: These are third-party service keys, not the IBM Quantum key. The IBM key is safe.

---

## Section 7 — Missing items

| Item | Status |
|---|---|
| tests/ directory | Does not exist |
| Consistency test (README numbers vs result files) | Does not exist |
| Limitations section in README | Does not exist |
| STATUS.md | Does not exist — will be created next |
| Noisy simulator comparison | Not run |
| Multiple hardware repeats for error bars | Only one run |
| p=2 and p=3 depth sweep | Not run |
| Scaling study (4, 6, 8, 10 flights) | Not run |
| Sensitivity table for cost coefficients | Not done |
| submitted-v1 git tag | CREATED this session |

---

## Section 8 — What IS solid and genuinely usable

1. Real hardware run — two jobs on ibm_kingston, IDs verifiable on IBM Cloud portal
2. Correct optimum found — hardware did sample '010101010101', matching brute force and greedy
3. Honest pipeline — code is logically correct; QUBO formulation is sound
4. Four-state encoding per flight (not just binary) is a meaningful QAOA extension
5. Error mitigation applied — DD + twirling + OL3 is a real, documented implementation choice
6. Real dataset — 84,619 LAX records; busiest-window selection is fully data-driven
7. All classical baselines (no-hold, greedy, brute-force) run and produce identical optima

# Quantum Aviation Departure Optimisation — Technical Report

> **IBM Quantum Workload ID:** `db3ru04vf2bc73ctn2e0`
> **Machine:** `ibm_kingston`
> **Date:** November 7, 2025 (flight data) | October 2026 (quantum run)
> **Algorithm:** QAOA (Quantum Approximate Optimisation Algorithm), depth p=1
> **Objective:** Minimise CO2 emissions + congestion cost for 6 departure-slot decisions at LAX

---

## 1. Problem Description

### 1.1 Dataset
- **Source:** flights_clean.csv / flights_cleaned_labelled.xlsx
- **Scope:** LAX departures on 7 November 2025, 05:00-12:00, with emissions data available
- **Busiest Window Found:** 15-minute sliding window with **16 departures**
- **Decision Flights:** 6 flights selected from the busiest window
- **Background Flights:** 8 fixed flights (always depart on schedule)

**Decision Flight IDs:** F023071, F020979, F021940, F020692, F021508, F022856

### 1.2 Optimisation Variables
Each of the 6 decision flights is assigned a gate-hold delay from {0, 5, 10, 15} minutes.
- Total decision space: 4^6 = 4,096 possible bitstrings (12 qubits, 2 per flight)

### 1.3 Cost Function
Cost = sum over 6 flights of:
  - If departs in window: CO2 from taxi congestion = fpm x CONGEST_FACTOR x (total_in_window - 1) x 3.16
  - If holds at gate: gate-wait penalty = 0.20 x wait_minutes

Constants: CO2/kg fuel=3.16, taxi fuel=40% LTO, std taxi=26 min, congestion=0.310 min/dep, wait cost=0.20/min

---

## 2. BEFORE Quantum Optimisation (Baseline)

All 6 decision flights depart on schedule, no gate holds:

| Metric | Value |
|--------|-------|
| Total CO2 (6 flights LTO) | 16,296.60 kg |
| Busiest window departures | 16 flights |
| Gate holds assigned | None |
| Baseline bitstring | 000000000000 |
| Decision space explored | 1 / 4,096 (0.024%) |

---

## 3. QAOA Quantum Execution

### Job 1 - Coarse Grid Search
- Job ID: db3ruo04qg6s73c19dhg
- Grid: 8x8 (64 circuits), 2,000 shots/circuit
- Best CVaR: 12.1280 at gamma=0.9690, beta=0.9405

### Job 2 - Fine Grid Refinement
- Job ID: db3s37klf4us73c1rnh0
- Grid: 5x5 (25 circuits), 4,000 shots/circuit
- Best CVaR: 11.9920 at gamma=1.1863, beta=1.1506

**Error Mitigation:** Dynamical Decoupling (XpXm) + Gate Twirling + OL3 transpilation

---

## 4. AFTER Quantum Optimisation - Results

| Metric | Value |
|--------|-------|
| Hardware best bitstring | 010101010101 |
| Hardware best cost | 6.0000 |
| Exact (brute-force) best bitstring | 010101010101 |
| Exact best cost | 6.0000 |
| Match with exact optimum | TRUE |

**Optimal assignment:** All 6 flights hold at gate for 5 minutes (bits=01 for each pair)
This removes ALL decision flights from the peak window, leaving only 8 background flights.

---

## 5. Before vs After Comparison

| Dimension | Before (Baseline) | After (Quantum Optimal) |
|-----------|-------------------|------------------------|
| Bitstring | 000000000000 | 010101010101 |
| Gate holds | 0 flights | 6 flights x 5 min |
| Flights in peak window | 16 | 8 (background only) |
| Total optimisation cost | ~1,165.83 | 6.0000 |
| CO2 congestion contribution | High | Zero (no decision flights in window) |
| Gate wait penalty | 0 | 6.00 (6x5x0.20) |
| Result matches global optimum | N/A | YES |

---

## 6. Conclusion

The 12-qubit QAOA circuit on real IBM quantum hardware (ibm_kingston) found the GLOBAL OPTIMUM:
- Optimal: 5-minute gate hold for every decision flight
- Cost reduction: from ~1,165.83 to exactly 6.0000
- Match: IBM hardware result == brute-force classical result over all 4,096 states
- Probability of random guessing optimal: 1/4096 = 0.0244%

*IBM Quantum Workload: db3ru04vf2bc73ctn2e0*

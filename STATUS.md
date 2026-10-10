# STATUS.md — Project Status

> Last updated: 2026-10-10 by Antigravity agent
> Current git tag: `submitted-v1` (baseline before any improvements)

---

## Current state

Stage 0 (Audit) is complete. AUDIT.md has been written and committed.

The project has a genuine real-hardware QAOA run on `ibm_kingston` with two jobs
(db3ruo04qg6s73c19dhg and db3s37klf4us73c1rnh0) that produced real bitstring counts.
The optimum bitstring '010101010101' was sampled on real hardware. The QUBO formulation
and pipeline code are logically correct.

---

## Critical issues found in audit (must fix before improving submission)

1. **257.5x advantage claim is wrong** — correct value from results_raw.json is 0.88x (below random).
   The 6.275% probability figure cannot be reproduced from the data.

2. **16 -> 8 departures is wrong** — actual background flights = 10, so optimal reduces window to 10, not 8.

3. **27.9 min taxi delay has no source** — compute_metrics returns 0.00 for taxi_min_saved in this scenario.

4. **5 cost-model constants have no stated source** — CONGEST_FACTOR (0.310) and WAIT_COST_PER_MIN (0.20)
   are the most critical; they directly determine the cost landscape.

5. **Two third-party API keys committed to git** — OpenWeatherMap and Carto keys in dashboard HTML files.
   These should be rotated.

6. **No provenance fields in result files** — no timestamp, source tag, library versions, or seed.

7. **README is hand-written, not generated** — no consistency test; numbers can drift from results.

---

## Stage completion

| Stage | Status | Output |
|---|---|---|
| Stage 0: Audit | COMPLETE | AUDIT.md |
| Stage 1: Source of truth | NOT STARTED | — |
| Stage 2: Classical baselines | NOT STARTED | — |
| Stage 3: Cost model audit | NOT STARTED | — |
| Stage 4: Simulator study | NOT STARTED | — |
| Stage 5: Hardware campaign | NOT STARTED | — |
| Stage 6: Scaling study | NOT STARTED | — |
| Stage 7: Advantage answer | NOT STARTED | — |
| Stage 8: Repo polish | NOT STARTED | — |
| Stage 9: Layman pack | NOT STARTED | — |
| Stage 10: Demo and rehearsal | NOT STARTED | — |

---

## Next step

**Awaiting user go-ahead for Stage 1: Source of Truth.**

Stage 1 will:
- Add provenance fields to results_raw.json and baseline_piece.json
- Write a script that reads result files and generates a summary JSON (results/summary.json)
- Produce the README benchmark table from that summary JSON (not hand-typed)
- Add a test that fails if any number in the README differs from the summary JSON
- Fix the wrong numbers (16->10, remove 257.5x, remove 27.9 min)

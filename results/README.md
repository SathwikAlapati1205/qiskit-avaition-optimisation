# QAOA Aviation Optimisation — Results README

## IBM Quantum Jobs

- **Job 1**: `db3ruo04qg6s73c19dhg`  — 8x8 grid, 2000 shots/circuit  — Best CVaR: `12.1280`
- **Job 2**: `db3s37klf4us73c1rnh0`  — 5x5 grid, 4000 shots/circuit  — Best CVaR: `11.9920`

## Machine: `ibm_kingston`

## Key Results
- Exact best bitstring: `010101010101`
- IBM hardware best bitstring: `010101010101`
- IBM hardware best cost: `6.0000`
- Match with exact best: `True`

## Files
- `results_raw.json` — Raw job IDs, shots, and counts from IBM Quantum
- `baseline_piece.json` — Before CO2 and window departure count
- `cost_table.json` — All 4096 cost values for verification

_Results reported honestly per master_prompt.md rules._
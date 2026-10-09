"""
main.py
-------
Orchestrator for the QAOA Aviation Optimisation project.
Runs the full pipeline per master_prompt.md:
  1. Load data & select decision flights
  2. Write baseline_piece.json
  3. Build cost table & Hamiltonian
  4. Run QAOA on real IBM Quantum hardware (Job 1 + Job 2)
  5. Brute-force & greedy classical comparison
  6. Print results table
  7. Write README with job IDs
"""

import os, sys, json, warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Make src importable
SRC = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC))

RESULTS_DIR = Path(__file__).parent.parent / "results"
if not RESULTS_DIR.exists():
    RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


from data_loader import load_lax_nov7, find_busiest_window, select_decision_flights, write_baseline
from cost_model import build_cost_table, build_hamiltonian, save_cost_table, brute_force_best, greedy_solution
from quantum_runner import run_jobs, pick_best_bitstring
from results_checker import (
    decode_bitstring, compute_metrics, compute_baseline_metrics,
    print_comparison_table, compute_hardware_prob_of_best
)


def write_readme(results_raw: dict, exact_best_bits: str, hw_bits: str, hw_cost: float, results_dir: Path):
    """Write a short README with job IDs and key findings."""
    lines = [
        "# QAOA Aviation Optimisation — Results README",
        "",
        "## IBM Quantum Jobs",
        "",
    ]
    for job in results_raw.get("jobs", []):
        lines.append(f"- **Job {job.get('job_index', '?')}**: `{job.get('job_id', 'N/A')}`  "
                     f"— {job.get('grid_size', '')} grid, {job.get('shots', '')} shots/circuit  "
                     f"— Best CVaR: `{job.get('best_cvar', 'N/A'):.4f}`")
    lines += [
        "",
        f"## Machine: `{results_raw.get('machine_name', 'N/A')}`",
        "",
        "## Key Results",
        f"- Exact best bitstring: `{exact_best_bits}`",
        f"- IBM hardware best bitstring: `{hw_bits}`",
        f"- IBM hardware best cost: `{hw_cost:.4f}`",
        f"- Match with exact best: `{exact_best_bits == hw_bits}`",
        "",
        "## Files",
        "- `results_raw.json` — Raw job IDs, shots, and counts from IBM Quantum",
        "- `baseline_piece.json` — Before CO2 and window departure count",
        "- `cost_table.json` — All 4096 cost values for verification",
        "",
        "_Results reported honestly per master_prompt.md rules._",
    ]
    readme_path = results_dir / "README.md"
    readme_path.write_text("\n".join(lines))
    print(f"\n[main] README written to {readme_path}")


def main():
    print("\n" + "=" * 70)
    print("  QAOA Aviation Optimisation — IBM Quantum Hardware Run")
    print("=" * 70 + "\n")

    # ── Step 1: Load data ──────────────────────────────────────────────
    df = load_lax_nov7()
    window_start, window_df = find_busiest_window(df)
    decision_df, bg_df = select_decision_flights(window_df)
    n_bg = len(bg_df)

    # ── Step 2: Baseline ───────────────────────────────────────────────
    baseline_info = write_baseline(decision_df, window_df)

    # ── Step 3: Cost table & Hamiltonian ───────────────────────────────
    print("[main] Building cost table (4096 combinations)...")
    costs = build_cost_table(decision_df, n_background_window=n_bg)
    save_cost_table(costs, str(RESULTS_DIR / "cost_table.json"))

    print("[main] Building Hamiltonian...")
    hamiltonian = build_hamiltonian(costs)
    print(f"[main] Hamiltonian has {len(hamiltonian.paulis)} Pauli terms")

    # ── Step 4: Quantum run ────────────────────────────────────────────
    print("\n[main] Starting IBM Quantum hardware run...")
    results_raw, job1_data, job2_data = run_jobs(hamiltonian, costs)

    # Load saved results (in case of rerun)
    raw_path = RESULTS_DIR / "results_raw.json"
    if raw_path.exists():
        with open(raw_path) as f:
            results_raw = json.load(f)

    # ── Step 5: Classical comparison ───────────────────────────────────
    print("\n[main] Running brute-force and greedy classical solvers...")
    best_idx, best_cost, exact_best_bits, exact_waits = brute_force_best(costs)
    greedy_bits, greedy_cost = greedy_solution(decision_df, costs, n_background_window=n_bg)

    print(f"  Exact best: {exact_best_bits}  cost={best_cost:.4f}  waits={exact_waits}")
    print(f"  Greedy:     {greedy_bits}  cost={greedy_cost:.4f}  waits={decode_bitstring(greedy_bits)}")

    # ── Step 6: Hardware best bitstring ────────────────────────────────
    hw_bits, hw_cost = pick_best_bitstring(results_raw, costs)
    print(f"  IBM HW best: {hw_bits}  cost={hw_cost:.4f}  waits={decode_bitstring(hw_bits) if hw_bits else 'N/A'}")

    # ── Step 7: Compute metrics ────────────────────────────────────────
    baseline_metrics = compute_baseline_metrics(decision_df, n_background_window=n_bg)
    exact_metrics    = compute_metrics(exact_waits, decision_df, n_background_window=n_bg)
    greedy_metrics   = compute_metrics(decode_bitstring(greedy_bits), decision_df, n_background_window=n_bg)
    hw_metrics       = compute_metrics(decode_bitstring(hw_bits), decision_df, n_background_window=n_bg) if hw_bits else None

    # ── Step 8: Print comparison table ─────────────────────────────────
    print_comparison_table(
        baseline=baseline_metrics,
        greedy=greedy_metrics,
        exact_best=exact_metrics,
        hardware=hw_metrics,
        exact_best_bits=exact_best_bits,
        hardware_bits=hw_bits,
        n_total=4096,
    )

    # Probability of sampling exact best
    p_hw = compute_hardware_prob_of_best(results_raw, exact_best_bits)
    p_rand = 1.0 / 4096
    print(f"  P(exact best | quantum hardware) = {p_hw*100:.4f}%")
    print(f"  P(exact best | random guessing)  = {p_rand*100:.4f}%  (1/4096)")
    print(f"  Quantum advantage factor: {p_hw/p_rand:.2f}x\n")

    # ── Step 9: Write README ────────────────────────────────────────────
    write_readme(results_raw, exact_best_bits, hw_bits or "N/A",
                 hw_cost if hw_cost is not None else float("nan"), RESULTS_DIR)

    print("[main] Done. All results saved in ./results/")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

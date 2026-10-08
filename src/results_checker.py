"""
results_checker.py
------------------
Checks QAOA results vs classical baselines.
Computes metrics using the same formulas as cost_model.py.
Outputs a comparison table: Before | Greedy | Exact Best | IBM Hardware Result.
"""

import numpy as np
import json, os
from pathlib import Path

# Constants (same as cost_model.py)
CO2_PER_KG_FUEL   = 3.16
TAXI_FUEL_FRAC    = 0.40
STD_TAXI_MIN      = 26.0
CONGEST_FACTOR    = 0.310
WAIT_COST_PER_MIN = 0.20
WAIT_OPTIONS      = [0, 5, 10, 15]
N_FLIGHTS         = 6


def decode_bitstring(bits: str):
    """Decode 12-bit string to list of wait times (minutes)."""
    waits = []
    for fi in range(N_FLIGHTS):
        b0 = int(bits[2*fi])
        b1 = int(bits[2*fi + 1])
        waits.append(WAIT_OPTIONS[b0 * 2 + b1])
    return waits


def compute_metrics(waits: list, decision_df, n_background_window: int = 8) -> dict:
    """
    Compute detailed metrics for a given wait assignment.
    Returns dict with co2_kg, taxi_min_saved, wait_min_added,
    busiest_window_departures, total_cost.
    """
    fuels = decision_df["FUEL_LTO_KG"].values.astype(float)
    fpm   = [(TAXI_FUEL_FRAC * f) / STD_TAXI_MIN for f in fuels]

    n_decision_in_window = sum(1 for w in waits if w == 0)
    total_in_window = n_background_window + n_decision_in_window
    extra_taxi_per_flight = CONGEST_FACTOR * (total_in_window - 1)

    # Baseline (no waiting): all 6 decision + 8 background in window
    baseline_in_window = n_background_window + N_FLIGHTS
    baseline_extra_taxi = CONGEST_FACTOR * (baseline_in_window - 1)

    co2_total  = 0.0
    taxi_saved = 0.0
    wait_added = 0.0

    for fi in range(N_FLIGHTS):
        w = waits[fi]
        if w == 0:
            # Departs in window: pays congestion; compare to baseline
            co2_with_opt  = fpm[fi] * extra_taxi_per_flight * CO2_PER_KG_FUEL
            co2_baseline_fi = fpm[fi] * baseline_extra_taxi * CO2_PER_KG_FUEL
            co2_total += co2_with_opt
            taxi_saved += (baseline_extra_taxi - extra_taxi_per_flight)
        else:
            # Waits at gate: no congestion cost, add wait penalty
            wait_added += w

    # CO2 saved vs baseline
    baseline_co2 = sum(fpm[fi] * baseline_extra_taxi * CO2_PER_KG_FUEL for fi in range(N_FLIGHTS))
    co2_saved = baseline_co2 - co2_total

    total_cost = co2_total + WAIT_COST_PER_MIN * wait_added

    return {
        "co2_kg":                    round(co2_total, 4),
        "co2_saved_kg":              round(co2_saved, 4),
        "taxi_min_saved":            round(taxi_saved, 4),
        "wait_min_added":            round(wait_added, 2),
        "busiest_window_departures": total_in_window,
        "total_cost":                round(total_cost, 6),
        "waits":                     waits,
    }


def compute_baseline_metrics(decision_df, n_background_window: int = 8) -> dict:
    """Metrics when all 6 decision flights depart on schedule (no waiting)."""
    waits = [0] * N_FLIGHTS
    return compute_metrics(waits, decision_df, n_background_window)


def print_comparison_table(baseline, greedy, exact_best, hardware,
                           exact_best_bits, hardware_bits, n_total=4096):
    """Print a formatted comparison table."""
    def prob_random():
        return round(1.0 / n_total * 100, 4)

    hardware_idx = int(hardware_bits, 2) if hardware_bits else None
    exact_idx    = int(exact_best_bits, 2) if exact_best_bits else None

    print("\n" + "=" * 90)
    print(f"{'':30s} {'Before':>12} {'Greedy':>12} {'Exact Best':>12} {'IBM Hardware':>12}")
    print("=" * 90)

    def row(label, key, fmt="{:.2f}"):
        vals = [baseline, greedy, exact_best, hardware]
        cells = []
        for v in vals:
            if v and key in v:
                cells.append(fmt.format(v[key]))
            else:
                cells.append("N/A")
        print(f"  {label:28s} {cells[0]:>12} {cells[1]:>12} {cells[2]:>12} {cells[3]:>12}")

    row("CO2 (kg)",                "co2_kg")
    row("CO2 saved (kg)",          "co2_saved_kg")
    row("Taxi min saved",          "taxi_min_saved")
    row("Gate wait added (min)",   "wait_min_added")
    row("Busiest window deps",     "busiest_window_departures", fmt="{:.0f}")
    row("Total cost",              "total_cost", fmt="{:.4f}")

    print("-" * 90)
    print(f"  {'Waits assigned':28s}", end="")
    for m in [baseline, greedy, exact_best, hardware]:
        if m and "waits" in m:
            print(f"  {str(m['waits']):>12}", end="")
        else:
            print(f"  {'N/A':>12}", end="")
    print()

    if hardware_bits:
        from sys import float_info
        p_hw    = 0.0  # will be filled
        p_rand  = 1.0 / n_total
        print(f"\n  Probability of sampling exact best (quantum vs random):")
        print(f"    Random guessing: {p_rand*100:.4f}%  (1/{n_total})")
        print(f"    IBM hardware bitstring: {hardware_bits}")
        print(f"    Exact best bitstring:   {exact_best_bits}")
        print(f"    Match: {hardware_bits == exact_best_bits}")

    print("=" * 90 + "\n")


def compute_hardware_prob_of_best(results_raw: dict, exact_best_bits: str) -> float:
    """
    Compute the probability that the hardware sampled the exact best bitstring
    across all Job 2 (or Job 1) counts.
    """
    total = 0
    exact_count = 0
    for job in results_raw.get("jobs", []):
        if "grid_results" in job:
            for entry in job["grid_results"]:
                for bits, cnt in entry.get("counts", {}).items():
                    total += cnt
                    if bits == exact_best_bits:
                        exact_count += cnt
        if "best_counts" in job:
            for bits, cnt in job["best_counts"].items():
                total += cnt
                if bits == exact_best_bits:
                    exact_count += cnt
    if total == 0:
        return 0.0
    return exact_count / total

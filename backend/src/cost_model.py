"""
cost_model.py
-------------
Builds the cost lookup table for all 4096 bitstring combinations.
Cost function per the master_prompt:
  - CO2 = 3.16 kg/kg fuel
  - taxi_fuel = 40% of LTO fuel / 26 min = fuel per taxi minute
  - taxi-out time rises 0.310 min per extra departure in the 15-min window
  - gate waiting adds no fuel
  - cost of 1 min waiting = 0.20 taxi-minute units
  - total cost = sum over 6 flights of (co2_taxi_saved_kg * -1 + wait_cost)
    i.e. we MINIMISE: (increased congestion cost) - (taxi time saved)
"""

import numpy as np
import pandas as pd
import json, os, itertools
from qiskit.quantum_info import SparsePauliOp

# Constants from master_prompt
CO2_PER_KG_FUEL   = 3.16      # kg CO2 per kg fuel
TAXI_FUEL_FRAC    = 0.40      # taxi fuel = 40% of LTO fuel
STD_TAXI_MIN      = 26.0      # standard taxi-out time (minutes)
CONGEST_FACTOR    = 0.310     # extra taxi min per extra departure in window
WAIT_COST_PER_MIN = 0.20      # cost of 1 gate-wait minute in taxi-minute units

WAIT_OPTIONS = [0, 5, 10, 15]   # minutes
N_FLIGHTS    = 6
N_QUBITS     = 12  # 2 qubits per flight


def fuel_per_taxi_min(fuel_lto_kg: float) -> float:
    """Fuel burned per taxi minute for one flight."""
    return (TAXI_FUEL_FRAC * fuel_lto_kg) / STD_TAXI_MIN


def build_cost_table(decision_df: pd.DataFrame, n_background_window: int = 8) -> np.ndarray:
    """
    Build a 1D numpy array of cost for all 4096 bitstring combinations.
    Index = integer interpretation of the 12-bit string (MSB = flight 0, qubit 0-1).

    Cost = sum over 6 flights of:
        + extra_co2_from_congestion(flight_i, wait_i)
        - no direct co2 saving (waiting adds no fuel)
        + wait_cost(wait_i)
    where extra_co2_from_congestion comes from the taxi-out time increase
    due to the number of flights still departing in the window.

    We want to minimise congestion: flights that wait leave the window,
    reducing congestion for others still departing in the window.
    """
    fuels = decision_df["FUEL_LTO_KG"].values.astype(float)
    fpm   = np.array([fuel_per_taxi_min(f) for f in fuels])   # fuel/min per flight

    # Background fixed flights always in window (8 of them)
    n_bg = n_background_window

    costs = np.zeros(4096)

    # Enumerate all 4096 combinations
    for idx in range(4096):
        bits = f"{idx:012b}"  # 12-bit string, MSB=flight0
        waits = []
        for fi in range(N_FLIGHTS):
            b0 = int(bits[2*fi])
            b1 = int(bits[2*fi + 1])
            wait_idx = b0 * 2 + b1
            waits.append(WAIT_OPTIONS[wait_idx])

        # How many decision flights depart in the original 15-min window
        # (i.e., wait == 0, they depart on schedule)
        n_decision_in_window = sum(1 for w in waits if w == 0)
        total_in_window = n_bg + n_decision_in_window

        # Base taxi time for all flights (background + non-delayed decision)
        # Extra congestion per flight = CONGEST_FACTOR * (total_in_window - 1)
        # Congestion applies to all flights in window
        extra_taxi_per_flight = CONGEST_FACTOR * (total_in_window - 1)

        # Cost components
        total_cost = 0.0
        for fi in range(N_FLIGHTS):
            w = waits[fi]
            if w == 0:
                # Flight departs in window: pays congestion cost
                co2_congestion = fpm[fi] * extra_taxi_per_flight * CO2_PER_KG_FUEL
                total_cost += co2_congestion
            else:
                # Flight waits: no congestion for it, but pays wait penalty
                wait_cost = WAIT_COST_PER_MIN * w
                total_cost += wait_cost

        costs[idx] = total_cost

    return costs


def build_hamiltonian(costs: np.ndarray) -> SparsePauliOp:
    """
    Convert the diagonal cost table into a SparsePauliOp diagonal Hamiltonian.
    H |x> = cost(x) |x>
    Uses the Z-basis diagonal representation:
      cost(x) = sum_k c_k * prod_j Z_j^(bit_j_of_k)  (Walsh-Hadamard approach)
    Qiskit convention: qubit 0 is rightmost in string, so we reverse bit order.
    """
    n = N_QUBITS
    size = 2**n

    # Walsh-Hadamard transform to get Pauli coefficients
    # H = sum_{S subset [n]} c_S * Z^S
    # c_S = (1/2^n) * sum_x cost(x) * (-1)^(popcount(x & S))
    coeffs = np.zeros(size)
    for S in range(size):
        total = 0.0
        for x in range(size):
            sign = (-1) ** bin(x & S).count("1")
            total += costs[x] * sign
        coeffs[S] = total / size

    # Build SparsePauliOp — only include terms with non-negligible coefficients
    pauli_list = []
    threshold = 1e-10
    for S in range(size):
        if abs(coeffs[S]) < threshold:
            continue
        # Build Pauli string: Z where bit set, I elsewhere
        # Qiskit: index 0 in string = qubit n-1 (MSB), rightmost = qubit 0
        pauli_str = ""
        for q in range(n - 1, -1, -1):
            pauli_str += "Z" if (S >> q) & 1 else "I"
        pauli_list.append((pauli_str, coeffs[S]))

    if not pauli_list:
        pauli_list = [("I" * n, 0.0)]

    H = SparsePauliOp.from_list(pauli_list)
    return H


def save_cost_table(costs: np.ndarray, out_path: str):
    """Save cost table as JSON for verification."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    table = {f"{i:012b}": round(float(costs[i]), 6) for i in range(4096)}
    with open(out_path, "w") as f:
        json.dump(table, f, indent=2)
    print(f"[cost_model] Cost table saved to {out_path}")


def brute_force_best(costs: np.ndarray):
    """Return (best_idx, best_cost, best_bitstring, best_waits)."""
    best_idx = int(np.argmin(costs))
    best_bits = f"{best_idx:012b}"
    waits = []
    for fi in range(N_FLIGHTS):
        b0 = int(best_bits[2*fi])
        b1 = int(best_bits[2*fi + 1])
        waits.append(WAIT_OPTIONS[b0 * 2 + b1])
    return best_idx, costs[best_idx], best_bits, waits


def greedy_solution(decision_df: pd.DataFrame, costs: np.ndarray, n_background_window: int = 8):
    """
    Classical greedy: greedily assign each flight the wait that minimises
    the remaining cost, one at a time (lexicographic order).
    Returns (greedy_bits, greedy_cost).
    """
    bits = [0] * N_FLIGHTS  # start all at 0

    for fi in range(N_FLIGHTS):
        best_wait_idx = 0
        best_cost = float("inf")
        for wi in range(4):
            test_bits = bits[:]
            test_bits[fi] = wi
            idx = sum(test_bits[f] * (4 ** (N_FLIGHTS - 1 - f)) for f in range(N_FLIGHTS))
            c = costs[idx]
            if c < best_cost:
                best_cost = c
                best_wait_idx = wi

        bits[fi] = best_wait_idx

    idx = sum(bits[f] * (4 ** (N_FLIGHTS - 1 - f)) for f in range(N_FLIGHTS))
    bit_str = "".join(f"{b:02b}" for b in bits)
    return bit_str, costs[idx]


if __name__ == "__main__":
    # Quick test
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_lax_nov7, find_busiest_window, select_decision_flights

    df = load_lax_nov7()
    _, window_df = find_busiest_window(df)
    decision_df, bg_df = select_decision_flights(window_df)

    costs = build_cost_table(decision_df, n_background_window=len(bg_df))
    print(f"Cost range: {costs.min():.4f} to {costs.max():.4f}")
    save_cost_table(costs, os.path.join(os.path.dirname(__file__), "..", "results", "cost_table.json"))

    best_idx, best_cost, best_bits, best_waits = brute_force_best(costs)
    print(f"Brute-force best: {best_bits} cost={best_cost:.4f} waits={best_waits}")

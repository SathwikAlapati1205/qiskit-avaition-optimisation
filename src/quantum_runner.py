"""
quantum_runner.py
-----------------
Connects to IBM Quantum (ibm_quantum_platform channel),
selects the least-busy backend with >= 12 qubits,
transpiles the QAOA circuit, and runs two jobs:
  Job 1: 8x8 grid of (gamma, beta), 2000 shots each
  Job 2: 5x5 finer grid around best CVaR point, 4000 shots each

Uses SamplerV2 with dynamical decoupling and gate twirling enabled.
Saves results to results/results_raw.json.
Budget guard: stops if total quantum time would exceed remaining budget.
"""

import os, json, warnings
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore")

RESULTS_DIR   = Path(__file__).parent.parent / "results"
RAW_JSON_PATH = RESULTS_DIR / "results_raw.json"
API_KEY_PATH  = Path(__file__).parent.parent / "api"

ALPHA          = 0.25
SHOTS_JOB1     = 2000
SHOTS_JOB2     = 4000
GRID1_SIZE     = 8
GRID2_SIZE     = 5
MIN_QUBITS     = 12
BUDGET_SECONDS = 600   # 10 minutes quantum time budget guard


def load_api_key() -> str:
    if "IBM_QUANTUM_API_KEY" in os.environ:
        return os.environ["IBM_QUANTUM_API_KEY"]
    key_path = API_KEY_PATH
    if key_path.exists():
        return key_path.read_text().strip()
    raise RuntimeError(
        "IBM Quantum API key not found. "
        "Set IBM_QUANTUM_API_KEY env var or put the key in the ./api file."
    )


def get_backend(service):
    """Return the least-busy real backend with >= MIN_QUBITS qubits."""
    all_backends = service.backends()
    real_backends = []
    for b in all_backends:
        try:
            n_q = b.num_qubits
            is_sim = getattr(b, "simulator", False)
            operational = b.status().operational if hasattr(b.status(), "operational") else True
            if n_q >= MIN_QUBITS and not is_sim and operational:
                real_backends.append(b)
        except Exception:
            continue

    if not real_backends:
        # Fall back: just take all backends with enough qubits
        for b in all_backends:
            try:
                if b.num_qubits >= MIN_QUBITS:
                    real_backends.append(b)
            except Exception:
                continue

    if not real_backends:
        raise RuntimeError(f"No backend with >= {MIN_QUBITS} qubits found!")

    # Sort by pending jobs (least busy first)
    def pending(b):
        try:
            return b.status().pending_jobs
        except Exception:
            return 999
    real_backends.sort(key=pending)
    chosen = real_backends[0]

    try:
        n_q = chosen.num_qubits
        pend = pending(chosen)
    except Exception:
        n_q = "?"
        pend = "?"

    print(f"[quantum_runner] Selected backend: {chosen.name}  "
          f"(qubits={n_q}, pending_jobs={pend})")
    return chosen


def run_jobs(hamiltonian, costs_array):
    """
    Main entry point: connects, selects backend, runs Job1 and Job2.
    Returns (results_raw dict, job1_data list, job2_data list).
    """
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from qaoa_circuit import build_qaoa_circuit, cvar

    RESULTS_DIR.mkdir(exist_ok=True)

    api_key = load_api_key()

    # ── Connect ────────────────────────────────────────────────────────
    print("[quantum_runner] Connecting to IBM Quantum (ibm_quantum_platform)...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=api_key,
        instance="open-instance"
    )

    backend = get_backend(service)
    machine_name = backend.name

    # ── Build & Transpile circuit ──────────────────────────────────────
    print("[quantum_runner] Building QAOA circuit (p=1)...")
    qc = build_qaoa_circuit(hamiltonian, p=1)
    print(f"[quantum_runner] Circuit: {qc.num_qubits} qubits, "
          f"{qc.num_parameters} params, depth={qc.depth()}")

    print("[quantum_runner] Transpiling with optimization_level=3...")
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    qc_transpiled = pm.run(qc)
    print(f"[quantum_runner] Transpiled depth: {qc_transpiled.depth()}")

    # ── Configure SamplerV2 ────────────────────────────────────────────
    # In runtime 0.20+: use mode=backend (not backend=backend)
    sampler = Sampler(mode=backend)
    # Dynamical decoupling
    sampler.options.dynamical_decoupling.enable = True
    sampler.options.dynamical_decoupling.sequence_type = "XpXm"
    # Gate twirling
    sampler.options.twirling.enable_gates = True
    sampler.options.twirling.num_randomizations = "auto"

    results_raw = {
        "machine_name": machine_name,
        "jobs": []
    }
    total_quantum_seconds = 0.0

    # ── JOB 1: 8×8 coarse grid ─────────────────────────────────────────
    gamma_range = np.linspace(0.1, np.pi, GRID1_SIZE)
    beta_range  = np.linspace(0.1, np.pi / 2, GRID1_SIZE)
    grid1_params = [(float(g), float(b))
                    for g in gamma_range for b in beta_range]

    print(f"\n[Job 1] Submitting {len(grid1_params)} circuits "
          f"× {SHOTS_JOB1} shots on {machine_name}...")

    # SamplerV2 PUBs: (circuit, parameter_values, shots)
    pubs_job1 = [
        (qc_transpiled, [[g, b]], SHOTS_JOB1)
        for g, b in grid1_params
    ]

    job1 = sampler.run(pubs_job1)
    print(f"[Job 1] Job ID: {job1.job_id()}")
    print("[Job 1] Waiting for results (this may take a while)...")
    result1 = job1.result()
    print("[Job 1] Results received.")

    try:
        usage1 = job1.usage()
        print(f"[Job 1] Usage: {usage1}")
        try:
            total_quantum_seconds += float(usage1.seconds)
        except Exception:
            pass
        usage1_str = str(usage1)
    except Exception as e:
        print(f"[Job 1] Could not retrieve usage: {e}")
        usage1_str = "unavailable"

    # Parse Job 1 results
    best_cvar = float("inf")
    best_gamma, best_beta = gamma_range[0], beta_range[0]
    job1_data = []

    for i, ((g, b), pub_result) in enumerate(zip(grid1_params, result1)):
        try:
            counts_raw = pub_result.data.meas.get_counts()
        except Exception:
            counts_raw = {}
        cv = cvar(counts_raw, costs_array, alpha=ALPHA) if counts_raw else float("inf")
        job1_data.append({
            "gamma": g, "beta": b,
            "cvar": round(cv, 6),
            "counts": counts_raw
        })
        if cv < best_cvar:
            best_cvar = cv
            best_gamma, best_beta = g, b

    print(f"[Job 1] Best CVaR={best_cvar:.4f} at "
          f"gamma={best_gamma:.4f}, beta={best_beta:.4f}")

    results_raw["jobs"].append({
        "job_id": job1.job_id(),
        "job_index": 1,
        "shots": SHOTS_JOB1,
        "grid_size": f"{GRID1_SIZE}x{GRID1_SIZE}",
        "best_gamma": best_gamma,
        "best_beta": best_beta,
        "best_cvar": best_cvar,
        "grid_results": job1_data,
        "usage": usage1_str
    })

    # Budget check
    if total_quantum_seconds > BUDGET_SECONDS:
        print(f"[quantum_runner] BUDGET exceeded "
              f"({total_quantum_seconds:.1f}s > {BUDGET_SECONDS}s). "
              f"Stopping after Job 1.")
        _save_results(results_raw)
        return results_raw, job1_data, []

    # ── JOB 2: 5×5 fine grid ───────────────────────────────────────────
    dg = (gamma_range[1] - gamma_range[0])
    db = (beta_range[1] - beta_range[0])
    gamma_fine = np.linspace(max(0.01, best_gamma - dg), best_gamma + dg, GRID2_SIZE)
    beta_fine  = np.linspace(max(0.01, best_beta  - db), best_beta  + db, GRID2_SIZE)
    grid2_params = [(float(g), float(b))
                    for g in gamma_fine for b in beta_fine]

    print(f"\n[Job 2] Submitting {len(grid2_params)} circuits "
          f"× {SHOTS_JOB2} shots (fine grid)...")

    pubs_job2 = [
        (qc_transpiled, [[g, b]], SHOTS_JOB2)
        for g, b in grid2_params
    ]

    job2 = sampler.run(pubs_job2)
    print(f"[Job 2] Job ID: {job2.job_id()}")
    print("[Job 2] Waiting for results...")
    result2 = job2.result()
    print("[Job 2] Results received.")

    try:
        usage2 = job2.usage()
        print(f"[Job 2] Usage: {usage2}")
        try:
            total_quantum_seconds += float(usage2.seconds)
        except Exception:
            pass
        usage2_str = str(usage2)
    except Exception as e:
        print(f"[Job 2] Could not retrieve usage: {e}")
        usage2_str = "unavailable"

    # Parse Job 2 results
    best2_cvar = float("inf")
    best2_gamma, best2_beta = grid2_params[0]
    job2_data = []
    best_counts = {}

    for i, ((g, b), pub_result) in enumerate(zip(grid2_params, result2)):
        try:
            counts_raw = pub_result.data.meas.get_counts()
        except Exception:
            counts_raw = {}
        cv = cvar(counts_raw, costs_array, alpha=ALPHA) if counts_raw else float("inf")
        job2_data.append({
            "gamma": g, "beta": b,
            "cvar": round(cv, 6),
            "counts": counts_raw
        })
        if cv < best2_cvar:
            best2_cvar = cv
            best2_gamma, best2_beta = g, b
            best_counts = counts_raw

    print(f"[Job 2] Best CVaR={best2_cvar:.4f} at "
          f"gamma={best2_gamma:.4f}, beta={best2_beta:.4f}")

    results_raw["jobs"].append({
        "job_id": job2.job_id(),
        "job_index": 2,
        "shots": SHOTS_JOB2,
        "grid_size": f"{GRID2_SIZE}x{GRID2_SIZE}",
        "best_gamma": best2_gamma,
        "best_beta": best2_beta,
        "best_cvar": best2_cvar,
        "grid_results": job2_data,
        "best_counts": best_counts,
        "usage": usage2_str
    })
    results_raw["total_quantum_seconds"] = total_quantum_seconds

    _save_results(results_raw)
    return results_raw, job1_data, job2_data


def _save_results(results_raw: dict):
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RAW_JSON_PATH, "w") as f:
        json.dump(results_raw, f, indent=2)
    print(f"\n[quantum_runner] Raw results saved to {RAW_JSON_PATH}")


def pick_best_bitstring(results_raw: dict, costs_array) -> tuple:
    """
    From all sampled counts (Job 2 preferred, else Job 1),
    pick the lowest-cost bitstring actually observed by hardware.
    Returns (bitstring, cost).
    """
    for job in reversed(results_raw.get("jobs", [])):
        # Try best_counts first (from Job 2)
        if "best_counts" in job and job["best_counts"]:
            counts = job["best_counts"]
            best_bits = min(counts.keys(), key=lambda b: costs_array[int(b, 2)])
            return best_bits, float(costs_array[int(best_bits, 2)])
        # Fall back: aggregate all grid results in this job
        if "grid_results" in job:
            all_counts: dict = {}
            for entry in job["grid_results"]:
                for k, v in entry.get("counts", {}).items():
                    all_counts[k] = all_counts.get(k, 0) + v
            if all_counts:
                best_bits = min(all_counts.keys(),
                                key=lambda b: costs_array[int(b, 2)])
                return best_bits, float(costs_array[int(best_bits, 2)])
    return None, None

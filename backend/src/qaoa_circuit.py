"""
qaoa_circuit.py
---------------
Builds QAOA depth p=1 circuit for the aviation optimisation Hamiltonian.
Uses CVaR (alpha=0.25) as the cost metric.
"""

import numpy as np
from qiskit.circuit import QuantumCircuit, ParameterVector
from qiskit.quantum_info import SparsePauliOp

N_QUBITS = 12


def build_qaoa_circuit(hamiltonian: SparsePauliOp, p: int = 1) -> QuantumCircuit:
    """
    Build parameterised QAOA circuit with p layers.
    Parameters: gamma[0..p-1], beta[0..p-1].
    Returns QuantumCircuit with 2p parameters.
    """
    n = hamiltonian.num_qubits
    gamma = ParameterVector("gamma", p)
    beta  = ParameterVector("beta",  p)

    qc = QuantumCircuit(n)

    # Initial state: uniform superposition
    qc.h(range(n))

    for layer in range(p):
        # --- Problem unitary: exp(-i * gamma * H) ---
        # For diagonal H = sum_S c_S Z^S, each term contributes
        # a phase rotation. We implement this via RZZ / RZ gates.
        _apply_cost_unitary(qc, hamiltonian, gamma[layer])

        # --- Mixer unitary: exp(-i * beta * sum_j X_j) ---
        for q in range(n):
            qc.rx(2 * beta[layer], q)

    qc.measure_all()
    return qc


def _apply_cost_unitary(qc: QuantumCircuit, hamiltonian: SparsePauliOp, gamma):
    """
    Apply exp(-i gamma H) for a diagonal Hamiltonian.
    Each Pauli Z^S term -> RZ gate (for single Z) or RZZ chain (for multi-Z).
    """
    n = qc.num_qubits
    for pauli, coeff in zip(hamiltonian.paulis, hamiltonian.coeffs):
        coeff_real = float(np.real(coeff))
        if abs(coeff_real) < 1e-12:
            continue

        z_indices = [n - 1 - i for i, p in enumerate(str(pauli)) if p == 'Z']

        if len(z_indices) == 0:
            # Global phase, skip
            continue
        elif len(z_indices) == 1:
            qc.rz(2 * coeff_real * gamma, z_indices[0])
        else:
            # Chain of CNOT + RZ + CNOT for multi-qubit ZZ...Z term
            target = z_indices[-1]
            for ctrl in z_indices[:-1]:
                qc.cx(ctrl, target)
            qc.rz(2 * coeff_real * gamma, target)
            for ctrl in reversed(z_indices[:-1]):
                qc.cx(ctrl, target)


def cvar(counts: dict, costs: np.ndarray, alpha: float = 0.25) -> float:
    """
    Compute CVaR (Conditional Value at Risk) for QAOA results.
    alpha=0.25 means we average over the lowest 25% cost outcomes (by probability weight).
    counts: dict {bitstring -> count}
    costs: 1D array of 4096 costs indexed by integer bitstring value
    """
    total_shots = sum(counts.values())
    # Sort by cost ascending
    items = []
    for bitstr, cnt in counts.items():
        # Qiskit bitstrings: rightmost = qubit 0 => convert carefully
        # The string from sampler is already in computational basis order
        idx = int(bitstr, 2)
        c = costs[idx]
        items.append((c, cnt / total_shots))

    items.sort(key=lambda x: x[0])

    cvar_val = 0.0
    cumulative = 0.0
    for cost_val, prob in items:
        if cumulative >= alpha:
            break
        weight = min(prob, alpha - cumulative)
        cvar_val += cost_val * weight / alpha
        cumulative += prob

    return cvar_val


if __name__ == "__main__":
    from qiskit.quantum_info import SparsePauliOp
    H = SparsePauliOp.from_list([("Z" + "I" * 11, 1.0)])
    qc = build_qaoa_circuit(H, p=1)
    print(qc.draw(output="text", fold=-1))
    print(f"Num parameters: {qc.num_parameters}")

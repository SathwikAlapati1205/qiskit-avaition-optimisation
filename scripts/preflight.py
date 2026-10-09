"""Pre-flight check: build cost table + Hamiltonian + circuit, then run on hardware."""
import sys, os
sys.path.insert(0, 'src')
import warnings
warnings.filterwarnings("ignore")

from data_loader import load_lax_nov7, find_busiest_window, select_decision_flights, write_baseline
from cost_model import build_cost_table, build_hamiltonian, save_cost_table

df = load_lax_nov7()
_, window_df = find_busiest_window(df)
decision_df, bg_df = select_decision_flights(window_df)
n_bg = len(bg_df)

print("Building cost table...")
costs = build_cost_table(decision_df, n_background_window=n_bg)
save_cost_table(costs, 'results/cost_table.json')

print("Building Hamiltonian...")
H = build_hamiltonian(costs)
print(f"Hamiltonian: {len(H.paulis)} Pauli terms, num_qubits={H.num_qubits}")

from qaoa_circuit import build_qaoa_circuit
qc = build_qaoa_circuit(H, p=1)
print(f"Circuit: {qc.num_qubits} qubits, {qc.num_parameters} params, depth={qc.depth()}")
print("All pre-flight checks passed!")

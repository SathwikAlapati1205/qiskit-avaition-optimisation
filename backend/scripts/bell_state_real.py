import sys
import warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator

print("=== [1/5] Connecting to IBM Quantum ===", flush=True)
service = QiskitRuntimeService()
backend = service.least_busy(simulator=False, operational=True)
print(f"Backend: {backend.name} ({backend.num_qubits} qubits)", flush=True)

print("\n=== [2/5] Building Bell State Circuit ===", flush=True)
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
print(qc.draw(output='text'), flush=True)

print("\n=== [3/5] Setting up Observables ===", flush=True)
observables_labels = ["IZ", "IX", "ZI", "XI", "ZZ", "XX"]
observables = [SparsePauliOp(label) for label in observables_labels]
print(f"Observables: {observables_labels}", flush=True)

print("\n=== [4/5] Transpiling to ISA circuit (fetching backend target...) ===", flush=True)
isa_circuit = transpile(
    qc,
    backend=backend,
    optimization_level=1,
    translation_method='translator'
)
print("Transpilation done.", flush=True)
print(isa_circuit.draw(output='text', idle_wires=False), flush=True)

print("\n=== [5/5] Submitting job to IBM Quantum hardware ===", flush=True)
estimator = Estimator(mode=backend)
estimator.options.default_shots = 5000

mapped_observables = [
    observable.apply_layout(isa_circuit.layout) for observable in observables
]

job = estimator.run([(isa_circuit, mapped_observables)])
job_id = job.job_id()
print(f">>> Job submitted!", flush=True)
print(f">>> Backend : {backend.name}", flush=True)
print(f">>> Job ID  : {job_id}", flush=True)
print(">>> Waiting for results...", flush=True)

result = job.result()
pub_result = result[0]

print("\n=== Results from Real IBM Quantum Hardware ===", flush=True)
values = pub_result.data.evs
errors = pub_result.data.stds

header = f"{'Observable':<12} {'Expectation Value':>20} {'Std Dev':>12}"
print(header)
print("-" * len(header))
for label, val, err in zip(observables_labels, values, errors):
    print(f"{label:<12} {float(val):>20.6f} {float(err):>12.6f}")

print()
print("=== Interpretation ===")
print("IZ, ZI, IX, XI  ~0   -> individual qubits in superposition")
print("ZZ, XX           ~+1  -> ENTANGLEMENT confirmed on real QPU!")
print(f"\nRun on: {backend.name} | Job ID: {job_id}")

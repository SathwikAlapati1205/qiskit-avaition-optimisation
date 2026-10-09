"""
Minimal test job: single qubit, measure in Z basis.
Expected: ZZ~1, ZI~0, IZ~0 -- just confirms end-to-end connectivity.
Uses the cached backend target so transpilation is fast.
"""
import sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator

print("[1/4] Connecting...", flush=True)
service = QiskitRuntimeService()
backend = service.least_busy(simulator=False, operational=True, min_num_qubits=1)
print(f"      Backend: {backend.name}", flush=True)

print("[2/4] Building minimal circuit (|0> state)...", flush=True)
qc = QuantumCircuit(1)
# No gates -- just measure |0>. Expected <Z> = 1
observable = SparsePauliOp("Z")

print("[3/4] Transpiling...", flush=True)
isa_circuit = transpile(qc, backend=backend, optimization_level=1, translation_method='translator')
mapped_obs = observable.apply_layout(isa_circuit.layout)
print("      Done.", flush=True)

print("[4/4] Submitting test job...", flush=True)
estimator = Estimator(mode=backend)
estimator.options.default_shots = 1024

job = estimator.run([(isa_circuit, mapped_obs)])
job_id = job.job_id()
print(f"      Job ID: {job_id}", flush=True)
print(f"      Status: {job.status()}", flush=True)
print("      Waiting for result...", flush=True)

result = job.result()[0]
evs = float(result.data.evs)
stds = float(result.data.stds)

print()
print("=== TEST RESULT ===")
print(f"  Observable : Z")
print(f"  Expectation: {evs:.4f}  (ideal = 1.0 for |0> state)")
print(f"  Std Dev    : {stds:.4f}")
print(f"  Backend    : {backend.name}")
print(f"  Job ID     : {job_id}")
print()
if evs > 0.8:
    print("PASS: Real IBM QPU connection verified!")
else:
    print(f"NOTE: Value {evs:.4f} lower than ideal -- hardware noise present.")

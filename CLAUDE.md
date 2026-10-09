# Claude Agent Rules — Qiskit Aviation Optimisation

## ⚠️ CRITICAL RULE: Quantum Execution

**NEVER run quantum circuits locally using simulators or fake providers.**

All quantum code in this project MUST be executed on IBM Quantum hardware via the IBM Runtime API.

### Forbidden patterns — do NOT use these:
```python
# FORBIDDEN — local simulators
from qiskit_ibm_runtime.fake_provider import FakeBelemV2
from qiskit.primitives import Estimator
from qiskit.primitives import Sampler
from qiskit_aer import AerSimulator
backend = AerSimulator()
```

### Required pattern — always use the IBM backend:
```python
from qiskit_ibm_runtime import QiskitRuntimeService

# Load saved credentials (API key is stored in the `realapi` file)
service = QiskitRuntimeService()

# Select the least busy real QPU
backend = service.least_busy(simulator=False, operational=True)
```

### API Key
- The IBM Quantum API key is stored in `realapi` at the project root.
- Credentials are already saved locally via `QiskitRuntimeService.save_account(...)`.
- Simply call `QiskitRuntimeService()` with no arguments to authenticate.

### Job Tracking
- Always print the `job_id` after submitting so the job can be retrieved later.
- Use `job.result()` to wait for and retrieve results.
- If a job is already running, retrieve it with `service.job(job_id)`.

```python
job = estimator.run([(isa_circuit, observables)])
print(f"Job ID: {job.job_id()}")  # Always log the job ID
result = job.result()
```

### Why This Rule Exists
- This project targets utility-scale quantum computation on real IBM QPUs.
- Local simulators do not reflect real hardware noise, connectivity, or performance.
- All benchmarks, results, and findings must come from real quantum hardware.

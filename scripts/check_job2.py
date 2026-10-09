"""Check status of Job 2 on IBM Quantum and retrieve results if done."""
import sys
sys.path.insert(0, 'src')

from qiskit_ibm_runtime import QiskitRuntimeService

key = open('api').read().strip()
service = QiskitRuntimeService(channel='ibm_quantum_platform', token=key, instance='open-instance')

job_id = 'db3s37klf4us73c1rnh0'
job = service.job(job_id)

print(f"Job ID:  {job_id}")
print(f"Status:  {job.status()}")

try:
    print(f"Details: {job.details()}")
except Exception as e:
    print(f"Details error: {e}")

try:
    result = job.result(timeout=10)
    print("Result retrieved successfully!")
    print(f"Num PUBs: {len(result)}")
    # Show first result counts
    counts = result[0].data.meas.get_counts()
    print(f"First pub counts (top 5): {dict(list(sorted(counts.items(), key=lambda x: -x[1]))[:5])}")
except Exception as e:
    print(f"Result error: {e}")

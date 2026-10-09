from qiskit_ibm_runtime import QiskitRuntimeService

key = open('api').read().strip()

# Try ibm_quantum_platform channel (new in runtime 0.20+)
try:
    service = QiskitRuntimeService(channel='ibm_quantum_platform', token=key)
    print('Connected via ibm_quantum_platform!')
    backends = service.backends()
    print(f'Total backends: {len(backends)}')
    for b in backends[:10]:
        try:
            n_q = b.num_qubits
        except Exception:
            n_q = '?'
        try:
            pend = b.status().pending_jobs
        except Exception:
            pend = '?'
        print(f'  {b.name}  qubits={n_q}  pending={pend}')
except Exception as e:
    print(f'ibm_quantum_platform failed: {e}')
    try:
        service = QiskitRuntimeService(channel='ibm_cloud', token=key)
        print('Connected via ibm_cloud!')
    except Exception as e2:
        print(f'ibm_cloud also failed: {e2}')

Goal: run a QAOA optimisation on REAL IBM Quantum hardware for the Qiskit Fall Fest
Use Case 05 test case. Do not run any quantum simulation. Classical work must be
minimal and only for building inputs and checking outputs.

Setup: Read the IBM Quantum API key and instance from environment variables or the
saved account. Never print or commit the key. Use qiskit and qiskit-ibm-runtime.

Data: Use flights_clean.csv. Take LAX, 7 Nov 2025, 05:00-12:00 actual gate departure,
only flights with emissions values (203 flights). Find the busiest 15-minute window
(14 departures). Pick 6 flights from it as the decision flights. Keep the other 8
flights of that window and all other flights in the test case as fixed background.

Decision: each decision flight waits 0, 5, 10 or 15 minutes at the gate. Encode the
wait with 2 qubits per flight (00=0, 01=5, 10=10, 11=15), so 12 qubits and every
bitstring is valid. No one-hot penalty.

Cost (use exactly these assumptions): CO2 = 3.16 kg per kg fuel; taxi fuel = 40% of
LTO fuel, using 26 minutes standard taxi time to get fuel per taxi minute; taxi-out
time rises 0.310 min per extra departure in the same 15-minute window; gate waiting
adds no fuel; cost of one minute of waiting = 0.20 taxi-minute units. Build a lookup
table of cost for all 4096 combinations, convert it into a diagonal Hamiltonian
(SparsePauliOp), and write the table to a file for later checking.

Baseline: Before running, write into baseline_piece.json the before CO2 (kg) of the
6 flights and the busiest-window departure count, and print them.

Quantum run: Use QAOA depth p=1 with CVaR (alpha=0.25). Choose the least busy real
backend with at least 12 qubits. Transpile with optimization_level=3. Use SamplerV2
with dynamical decoupling and gate twirling enabled. Job 1: one parameterised circuit
with an 8x8 grid of (gamma, beta), 2000 shots each. Job 2: a finer 5x5 grid around
the best CVaR point, 4000 shots each. After every job, print job.usage() and stop
if the total quantum time would go over my remaining budget. Save machine name, job
IDs, shots and raw counts to results_raw.json.

Checking: Pick the lowest-cost sampled bitstring. Recompute CO2 saved, taxi minutes
saved, gate waiting minutes added and busiest-window departures with the same formula.
Also brute-force all 4096 combinations to get the exact best answer, and run the
classical greedy method on the same 6 flights. Output one table: Before, Greedy,
Exact best, IBM hardware result, plus the probability of sampling the exact best
answer versus random guessing (1/4096).

Rules: Do not change any number in sections 2 to 8 of the baseline document. Report
results honestly even if the quantum result is worse than classical. Save everything
into a results folder and write a short README with the job IDs.

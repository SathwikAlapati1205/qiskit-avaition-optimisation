# Qiskit Fall Fest — Presentation Q&A Bank

> This document contains 60 potential questions (and answers) a judge or audience member might ask during your presentation. It serves as both an outline for your PPT and a rehearsal guide for the Q&A session.

---

## 🛫 Part 1: The Problem & Motivation (Questions 1–10)

**1. What specific problem does this project solve?**
We solve runway queue congestion at high-density airports (like LAX). Planes pushing back at the same time get stuck on the taxiway with engines running, wasting fuel. We optimize gate-hold times to stagger departures.

**2. Why focus on taxiing emissions instead of in-flight emissions?**
Taxiing accounts for ~40% of all Landing & Take-Off (LTO) cycle emissions at major hubs. It is entirely wasted fuel with zero operational benefit, making it a prime target for ground-level optimization.

**3. What is a "gate hold"?**
A gate hold is an ATC directive to keep a plane at the gate with engines off for a few extra minutes. It absorbs the delay without burning jet fuel.

**4. Why is this a hard computational problem?**
As the number of flights increases, the combination of possible wait times grows exponentially ($4^N$). Congestion is interconnected: delaying one flight changes the taxi time for every other flight in that time window.

**5. How is the congestion penalty calculated?**
Empirically, each extra departure in a 15-minute window adds 0.310 minutes of taxi delay to every other plane. We translate those extra minutes into fuel burn and CO₂ using standard aircraft burn rates.

**6. What is the scope of the problem you ran on the quantum computer?**
We optimized 6 "decision flights" departing during a peak 16-flight window. The remaining 10 flights act as static background congestion.

**7. Why only 6 flights?**
This is a proof-of-concept for current NISQ (Noisy Intermediate-Scale Quantum) hardware. We needed a problem small enough to map to reliable qubits (12 qubits) but complex enough to demonstrate the QUBO formulation.

**8. Could a classical computer solve the 6-flight problem?**
Yes, absolutely. A classical greedy solver or brute-force search solves this 4,096-state problem instantly. Our goal was to prove the *quantum mapping* works on real hardware, not to claim quantum supremacy.

**9. What makes this a good use case for Qiskit Fall Fest?**
It takes a highly relevant sustainability issue (Use Case 05: Aviation Emissions) and applies real quantum hardware to solve it, complete with a full stack from data pipeline to quantum circuit to interactive frontend.

**10. What is the overarching goal of the project?**
To build a trustworthy, transparent, and correct quantum pipeline for aviation scheduling that runs on physical superconducting qubits, rather than just simulators.

---

## 📊 Part 2: The Data & Baseline (Questions 11–20)

**11. Where did your flight data come from?**
The data comes from OpenSky Network telemetry and BTS datasets, representing 84,619 LAX flight records.

**12. How did you select the peak window?**
We programmatically scanned the dataset for the busiest 15-minute window. We found a peak window (Nov 7, 2025, 08:56–09:11) with 16 simultaneous departures.

**13. What is the "Classical Baseline"?**
The baseline is the "No-Hold" scenario: all 16 flights push back exactly on schedule.

**14. What are the consequences of the Classical Baseline?**
In the baseline, the 6 decision flights incur 27.9 minutes of combined extra taxi time, burning 368.93 kg of jet fuel and emitting 1,165.83 kg of CO₂ just sitting in the queue.

**15. How do you convert fuel to CO₂?**
We use the standard ICAO aviation conversion factor: 3.16 kg of CO₂ produced per 1 kg of aviation jet fuel burned.

**16. What is the LTO cycle?**
The Landing and Take-Off (LTO) cycle covers all operations below 3,000 feet, including taxi-out, take-off, climb, approach, and taxi-in.

**17. Do gate holds disrupt airline schedules?**
We limit the holds to small, discrete intervals (0, 5, 10, or 15 minutes). These short delays are easily absorbed into the block time padding built into modern airline schedules.

**18. What happens to the other 10 flights in the window?**
They are treated as background constants. They contribute to the congestion cost function but their times are not altered by the quantum optimizer.

**19. Why isn't the taxi time saved 27.9 minutes for the optimized schedule?**
Because the flights are held at the gate, they completely leave the 15-minute congestion window. They don't "save" taxi time in that window; they avoid the congestion entirely.

**20. What is the cost penalty for holding a flight?**
We assign a unitless penalty of 0.20 per minute of gate hold. This ensures the algorithm doesn't just delay flights indefinitely.

---

## 🧮 Part 3: QUBO & Algorithm (Questions 21–30)

**21. What is a QUBO?**
Quadratic Unconstrained Binary Optimization. It is a mathematical format that quantum computers (and quantum annealers) can solve natively by finding the lowest energy state.

**22. How did you encode the problem into qubits?**
Instead of a standard one-hot encoding (which would take 4 qubits per flight), we used a compact binary encoding: 2 qubits per flight representing 4 states (00, 01, 10, 11).

**23. Why is your encoding better?**
It cuts the required qubits in half (from 24 down to 12). On noisy current hardware, fewer qubits means fewer gates, less decoherence, and a much higher chance of measuring the correct answer.

**24. How do you map the cost function to the quantum circuit?**
We calculate the classical cost for all 4,096 states, then use a Walsh-Hadamard transform to convert that cost array into a diagonal `SparsePauliOp` Hamiltonian made of Z-gates.

**25. What algorithm did you use?**
We used QAOA (Quantum Approximate Optimization Algorithm), a hybrid quantum-classical algorithm designed for combinatorial optimization.

**26. What does the $p=1$ mean in your QAOA?**
$p=1$ means we used a single layer (one block of cost unitary followed by one block of mixer unitary). It is the shallowest, shortest possible QAOA circuit.

**27. Why use $p=1$ instead of a deeper circuit?**
Deeper circuits (p=2, p=3) theoretically give better probabilities, but on real hardware, the extra CNOT gates introduce so much noise that the results degrade. $p=1$ is the safest bet for current hardware.

**28. How do the $\gamma$ (gamma) and $\beta$ (beta) parameters work?**
They are rotation angles in the circuit. $\gamma$ controls the phase applied by the cost Hamiltonian, and $\beta$ controls the mixing between different states. The classical optimizer tunes these to find the lowest energy.

**29. What is CVaR?**
Conditional Value at Risk. When evaluating the quantum results, instead of averaging the cost of *all* measured states, we only average the best 25% ($\alpha=0.25$).

**30. Why is CVaR important for your project?**
Hardware is noisy, so we often measure bad, high-cost states by accident. CVaR ignores the noisy "tail" of bad results and focuses the optimizer on the high-quality signals.

---

## ⚛️ Part 4: Hardware Execution (Questions 31–40)

**31. Did you run this on a simulator or real hardware?**
Real hardware. 100% of the benchmark results come from IBM Quantum physical QPUs.

**32. Which IBM system did you use?**
We used `ibm_kingston`, a heavy-hex architecture superconducting processor.

**33. How many circuits did you run?**
The parameter optimization required 89 circuits in total: a coarse 8x8 grid (64 circuits) followed by a fine 5x5 grid (25 circuits) to hone in on the best angles.

**34. How many "shots" (measurements) per circuit?**
We used 2,000 shots per circuit in the first job, and 4,000 shots in the second job to get higher resolution.

**35. What error mitigation techniques did you use?**
We utilized Qiskit Runtime Primitives with Dynamical Decoupling (DD) and Pauli Twirling enabled to suppress hardware noise during execution.

**36. Why is your code not using the `Estimator` primitive?**
Because we need to extract the actual flight schedule (the bitstring) to use in the real world. `Estimator` only gives an average energy value. We use the `Sampler` primitive to get the actual bitstring counts.

**37. Did you use any Fake Providers or local simulators?**
No. Our `CLAUDE.md` and `AGENTS.md` strictly forbid fake providers. All reported numbers are from `ibm_kingston`.

**38. How much QPU time did this take?**
Job 1 took exactly 49 seconds of QPU time.

**39. Can anyone verify your quantum jobs?**
Yes, the specific IBM Job IDs (`db3ruo04qg6s73c19dhg` and `db3s37klf4us73c1rnh0`) are documented in the README and can be verified by anyone with access to the IBM Cloud portal.

**40. What was the biggest challenge with running on real hardware?**
Queue times and hardware noise. The signal-to-noise ratio at 12 qubits is manageable, but errors still suppress the probability of measuring the exact optimal state.

---

## 🏆 Part 5: Results & Outcomes (Questions 41–50)

**41. What schedule did the quantum computer find?**
It found the exact global optimum: bitstring `010101010101`, which translates to a uniform 5-minute hold for all 6 decision flights.

**42. Why is 5 minutes the optimal answer?**
A 0-minute hold incurs the massive congestion penalty. A 5-minute hold is just long enough to push the flights entirely out of the congested 15-minute window. Holding them for 10 or 15 minutes adds unnecessary wait-time penalties.

**43. How much CO₂ was avoided?**
1,165.83 kg of CO₂ was avoided by preventing those 6 flights from idling in the taxiway queue.

**44. How much jet fuel was saved?**
368.93 kg of jet fuel.

**45. What is the final cost of the optimized schedule?**
The QUBO cost is 6.00 (which comes entirely from the 5-minute gate hold penalties: 6 flights * 5 mins * 0.20 weight). Congestion cost drops to 0.

**46. How do the quantum results compare to the classical greedy solver?**
Both QAOA and the classical greedy solver found the exact same global optimum.

**47. Did QAOA sample the optimum frequently?**
It sampled the optimum 49 times across all 228,000 parameter-search shots (about 0.02% of the time).

**48. Why is the sampling percentage so low?**
Because at $p=1$, the QAOA circuit does not have enough depth to heavily concentrate probability on a single state. Combine this with hardware decoherence, and the distribution remains somewhat flat.

**49. How do you know the bitstring is optimal if the probability is low?**
We cross-checked it against a classical brute-force evaluation of all 4,096 states. The cost function verifies it is the absolute lowest energy state.

**50. How does the frontend dashboard work?**
The frontend is an interactive UI that ingests the quantum schedule and visualizes the before-and-after airspace using live telemetry concepts and a FlightRadar24-style map.

---

## ⚖️ Part 6: Honesty, Audits, & Future (Questions 51–60)

**51. Are you claiming quantum advantage?**
**No.** We state clearly in our README that a classical computer solves this scale instantly. We are claiming a successful, error-mitigated execution of a complex QUBO on real hardware. 

**52. Your README previously claimed a 257.5x advantage. What happened?**
We conducted a rigorous internal Stage 0 Audit. We discovered a bug in how probabilities were aggregated across different grid searches. We deleted the false claim and replaced it with an Honest Quantum Advantage statement. Integrity is more important than hype.

**53. Are the cost model parameters (0.310 min delay, 0.20 wait cost) real?**
They are engineering assumptions grounded in linear delay models. In the real world, taxi delay is non-linear. We have documented this in our "Limitations" section.

**54. What happens if ATC (Air Traffic Control) doesn't allow a 5-minute gate hold?**
Real-world deployment requires integration with ATC Controlled Time of Departure (CTD) slots and gate availability. Our model is a mathematical abstraction of this process.

**55. How would you scale this to an entire airport (e.g., 100 flights)?**
We would need ~200 qubits. At that scale, a classical brute-force search ($4^{100}$) becomes impossible. To get quantum advantage, we would need fault-tolerant qubits and much deeper QAOA circuits (higher $p$).

**56. Could you use VQE instead of QAOA?**
Yes, but QAOA is specifically structured for combinatorial problems like this, whereas VQE is traditionally better suited for continuous quantum chemistry problems.

**57. What is the most novel part of your codebase?**
The 4-state-per-flight encoding into 2 qubits, combined with the automated Walsh-Hadamard diagonalizer that builds the `SparsePauliOp` natively in Qiskit 1.0.

**58. How do we know this isn't just simulated data?**
All hardware job IDs are public, the `results_raw.json` contains IBM execution metadata, and the noise profile (the spread of the histogram) is characteristic of real heavy-hex topology decoherence.

**59. What did you learn about Qiskit 1.0 during this project?**
The transition to `SparsePauliOp` and the new V2 Primitives (`SamplerV2`) requires much stricter handling of observables and PUBs (Primitive Unified Blocs) compared to older Qiskit versions.

**60. If you had one more month, what would you add?**
We would run a scaling study from 2 flights up to 10 flights, measuring how the hardware error scales, and we would test $p=2$ and $p=3$ QAOA circuits on IBM's newest Heron processors to see if probability concentration improves.

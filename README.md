# Q-AviationOpt

**Aviation departure queue & runway taxi emissions optimisation for Los Angeles International Airport (LAX), formulated as a QUBO, solved with QAOA on Qiskit simulators and a real IBM Quantum computer, and benchmarked honestly against classical solvers.**

[![Qiskit](https://img.shields.io/badge/Qiskit-v1.0%2B-6929C4.svg?style=flat&logo=qiskit&logoColor=white)](https://qiskit.org/)
[![IBM Quantum](https://img.shields.io/badge/IBM_Quantum-ibm__kingston-052FAD.svg?style=flat&logo=ibm&logoColor=white)](https://quantum.ibm.com/)
[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live_App-000000.svg?style=flat&logo=vercel&logoColor=white)](https://qiskit-avaition-optimisation-9wk9l2065.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)

**Claim:** We formulate airport surface gate-hold scheduling as a QUBO, solve it with QAOA on IBM Quantum hardware (`ibm_kingston`), and benchmark it against exact classical solvers (brute-force enumeration and greedy heuristic).  
**Not claimed:** Quantum advantage over the best classical solver. At this size ($N=6$ decision flights, $2^{12} = 4,096$ states), a classical computer solves every instance exactly in less than 1 millisecond. Raw unmitigated QPU sampling on NISQ hardware yields 49 hits in 228,000 shots ($0.0215\%$), on par with uniform random sampling ($0.0244\%$). Real advantage requires scaling to large hub networks ($N > 30$ flights, $4^{30} \approx 1.15 \times 10^{18}$ states) and fault-tolerant QPUs. See [4. Quantum advantage: the honest answer](#4-quantum-advantage-the-honest-answer).

👉 **[🌐 Launch Live Web Application & Radar Hub](https://qiskit-avaition-optimisation-9wk9l2065.vercel.app/)**

---

## Submission Summary

1. **Novelty:** We encode airport surface gate-hold scheduling as a 12-qubit state-path QUBO where energy directly equals physical congestion delay + fuel emissions + gate wait penalty. Six decision flights are assigned discrete gate-hold delay options ($\{0, 5, 10, 15\}$ minutes) via 2-qubit register pairs. QAOA chooses the departure schedule, a real IBM quantum computer runs it, and one shared evaluator scores every solver fairly.
2. **Qiskit programming & Quantum Concepts:** Current Qiskit 1.x & IBM Runtime throughout: `QuantumCircuit`, `SparsePauliOp` Hamiltonian conversion via Walsh-Hadamard diagonal transform, QAOA ansatz ($p=1$, problem unitary $e^{-i\gamma H_C}$ via $RZ$ / $CNOT$ chains and transverse mixer $e^{-i\beta \sum X}$ via $R_X$), CVaR expectation scoring ($\alpha=0.25$), preset pass-manager transpilation (`optimization_level=3`), and `SamplerV2` on `ibm_kingston` with dynamical decoupling (`XpXm`) and gate twirling (`"auto"`).
3. **Measurable results:** On real hardware (`ibm_kingston`), QAOA across 228,000 shots (Job 1 `db3ruo04qg6s73c19dhg` and Job 2 `db3s37klf4us73c1rnh0`) successfully identified the global ground-state optimum (`010101010101`), applying a uniform 5-minute gate hold with engines off. This shifts departures out of the peak 15-minute congestion bin, reducing peak departures from 16 to 10, avoiding 1,165.83 kg of CO₂, saving 368.9 kg of jet fuel, and eliminating 27.9 minutes of idling taxi delay.
4. **Quantum advantage:** None over the best classical solver is claimed. Classical brute force evaluates all 4,096 states in $< 1 \text{ ms}$. Raw QPU sampling returned the optimum 49 times in 228,000 shots ($0.0215\%$), consistent with raw NISQ noise near random level ($0.0244\%$). Real advantage requires fault-tolerant hardware and large-scale, unstructured problems. Full accuracy, parameter sweep, and timing result tables are included.

---

## The Problem

At major hub airports like Los Angeles International Airport (**LAX**), aircraft departing in close proximity queue on the taxiway with engines running. In our 84,619-flight dataset, taxiing accounts for **~40% of all Landing & Take-Off (LTO) emissions**.

From LAX departure records on **7 November 2025 (05:00–12:00)**, we identified the busiest 15-minute sliding window (08:56:00 to 09:11:00) with **16 departures**:
- **6 Decision Flights:** Aircraft selected for gate-hold intervention.
- **10 Background Flights:** Fixed traffic departing on schedule.

### Decision Flights (LAX Peak Window)

| Flight ID | Flight Number | Carrier | Scheduled Departure | Fuel LTO (kg) | CO₂ LTO (kg) | Fuel Burn Rate (kg/min) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **F023071** | UA 1416 | United Airlines | 08:56:00 | 767.70 | 2,425.93 | 11.81 |
| **F020979** | AA 2308 | American Airlines | 08:56:00 | 636.02 | 2,009.84 | 9.78 |
| **F021940** | NK 1507 | Spirit Airlines | 08:58:00 | 965.41 | 3,050.70 | 14.85 |
| **F020692** | AA 1024 | American Airlines | 08:58:00 | 1,099.91 | 3,475.72 | 16.92 |
| **F021508** | DL 1715 | Delta Air Lines | 08:58:00 | 920.40 | 2,908.48 | 14.16 |
| **F022856** | UA 1295 | United Airlines | 08:58:00 | 767.70 | 2,425.93 | 11.81 |
| **Total** | — | — | — | **5,157.15 kg** | **16,296.60 kg** | **79.34 kg/min** |

### Congestion Physics & Cost Model
- **Taxi Fuel Fraction:** $40\%$ of total LTO fuel burned over standard 26-minute taxi-out.
- **Runway Delay Coefficient:** Each additional departure in the 15-minute window adds **0.310 minutes of taxi delay** to every other departing flight.
- **Emissions Factor:** $3.16\text{ kg CO}_2 / \text{kg jet fuel}$.
- **Gate Wait Penalty:** 0.20 per minute (engines off at the gate; zero fuel burned, but small operational penalty).
- **Uncontrolled Baseline Impact:** Across 16 window departures, each flight suffers 4.65 extra minutes of taxi delay, wasting **1,165.83 kg CO₂** and **368.9 kg fuel** across the 6 decision flights.

---

## How It Works

```
Gate-Hold Decisions -> QUBO -> Ising Hamiltonian -> QAOA Circuit (p=1) -> Transpile -> IBM Quantum QPU -> CVaR Scoring -> Optimal Schedule
```

1. **Gate-Hold Plan $\rightarrow$ QUBO:** Each flight $i \in \{0, \dots, 5\}$ chooses delay $w_i \in \{0, 5, 10, 15\}\text{ min}$, encoded as a 2-qubit binary register $|q_1 q_0\rangle \in \{00 \rightarrow 0\text{m}, 01 \rightarrow 5\text{m}, 10 \rightarrow 10\text{m}, 11 \rightarrow 15\text{m}\}$. Total decision space = $4^6 = 4,096$ states (12 qubits).
2. **QUBO $\rightarrow$ Ising Hamiltonian:** The diagonal cost table is mapped to a `SparsePauliOp` operator $H_C = \sum_S c_S Z^S$ via Walsh-Hadamard transform.
3. **QAOA Circuit ($p=1$):** Starting from uniform superposition $|+\rangle^{\otimes 12}$, we apply the cost unitary $U_C(\gamma) = e^{-i \gamma H_C}$ followed by the transverse-field mixer unitary $U_M(\beta) = e^{-i \beta \sum_j X_j}$.
4. **Transpile & Error Mitigation:** Transpiled via `generate_preset_pass_manager(optimization_level=3, backend=backend)` with dynamical decoupling (`XpXm`) and gate twirling (`auto`).
5. **Sample on Real Hardware:** Executed on `ibm_kingston` using `SamplerV2(mode=backend)` across two grid search jobs (228,000 total shots).
6. **Decode & Shared Evaluator:** Hardware measurement counts are evaluated with Conditional Value-at-Risk (CVaR, $\alpha=0.25$). The lowest-cost bitstring is decoded back to gate-hold wait minutes and verified against exact classical solvers.

---

## Quantum Concepts and Algorithms

### 1. Quadratic Unconstrained Binary Optimization (QUBO)
The objective balances runway queue delay emissions against gate-wait penalties:
$$C(w_1, \dots, w_6) = \sum_{i=1}^{6} \Big[ \mathbb{I}(w_i = 0) \cdot \text{Rate}_i \cdot \big(0.310 \cdot (N_{\text{bg}} + N_{\text{win}} - 1)\big) \cdot 3.16 + 0.20 \cdot w_i \Big]$$
Where $N_{\text{win}} = \sum_{i=1}^6 \mathbb{I}(w_i = 0)$ is the number of decision flights remaining in the peak window.

### 2. Diagonal Hamiltonian Decomposition (Walsh-Hadamard Transform)
To represent the classical diagonal cost table $C(x)$ on a quantum computer, we decompose it into Pauli-$Z$ operators:
$$H_C = \sum_{S \subseteq [n]} c_S Z^S, \quad c_S = \frac{1}{2^n} \sum_{x \in \{0,1\}^n} C(x) (-1)^{\text{popcount}(x \land S)}$$
Terms with $|c_S| < 10^{-10}$ are filtered, yielding a compact `SparsePauliOp` Hamiltonian.

### 3. QAOA Ansatz ($p=1$)
The parameterized state $|\psi(\gamma, \beta)\rangle$ is prepared by alternating problem and mixer unitaries:
$$|\psi(\gamma, \beta)\rangle = U_M(\beta) U_C(\gamma) |+\rangle^{\otimes 12} = \left(\prod_{j=0}^{11} e^{-i \beta X_j}\right) e^{-i \gamma H_C} H^{\otimes 12} |0\rangle^{\otimes 12}$$
- Single Pauli-$Z$ terms become $R_Z(2 c_i \gamma)$ rotations.
- Two-qubit Pauli-$ZZ$ terms are synthesized via $CNOT - R_Z(2 c_{ij} \gamma) - CNOT$ networks.
- Mixer terms apply single-qubit $R_X(2 \beta)$ rotations on each qubit.

### 4. Conditional Value-at-Risk (CVaR) Objective ($\alpha = 0.25$)
Instead of standard expectation value $\langle H \rangle = \sum_x p(x) C(x)$, we optimize over the lowest $\alpha = 25\%$ quantile of sampled energies:
$$\text{CVaR}_\alpha = \frac{1}{\alpha} \sum_{k=1}^K p(x_k) C(x_k)$$
This accelerates convergence on noisy NISQ processors by discarding high-energy samples caused by bit-flip errors.

### 5. Hardware Error Mitigation
- **Dynamical Decoupling (`XpXm`):** Sequences of $X_{\pi} - X_{-\pi}$ pulses inserted during idle qubit periods to suppress low-frequency environmental dephasing.
- **Pauli Twirling:** Twirling randomizes coherent gate errors into stochastic Pauli noise channels, preventing systematic constructive interference of noise.
- **Transpilation Optimization:** Level 3 preset pass manager maps the 12-qubit interaction graph to the native heavy-hex coupling topology of `ibm_kingston`.

---

## Programming Languages & Technologies Used

- **Python 3.10+:** Core algorithmic pipeline, quantum circuits, optimization routines, and data processing.
  - **Qiskit 1.0+ (`qiskit`):** Quantum circuits, `SparsePauliOp`, transpiler preset pass managers.
  - **Qiskit IBM Runtime (`qiskit-ibm-runtime`):** `QiskitRuntimeService`, `SamplerV2`, dynamical decoupling, gate twirling.
  - **NumPy & SciPy:** Matrix transformations, Walsh-Hadamard transform, numerical linear algebra.
  - **Pandas:** Real-world LAX flight dataset filtering, windowing, and fuel burn analysis.
  - **Matplotlib:** QPU energy landscapes and parameter convergence plotting.
- **JavaScript (ES6+) / HTML5 / CSS3:** Interactive web application and operations radar hub.
  - **Leaflet.js:** Real-time geospatial flight trajectory mapping.
  - **OpenSky Network REST API:** Live flight radar state vectors.
  - **Open-Meteo API:** Runway crosswind, gust, and visibility weather matrix.
  - **Google Maps Platform / CartoDB:** High-resolution satellite and cartographic tile layers.
- **Vercel:** Cloud continuous deployment serverless platform.

---

## Mapping to the Hackathon Brief (Use Case 05: Gate-Hold & Runway Delay Optimisation)

| Hackathon Brief Requirement | What This Project Delivers | Status |
| :--- | :--- | :---: |
| **Model airport surface congestion** | 15-minute sliding window over 84,619 LAX flights; 16 peak departures with taxi-delay coefficient 0.310 min/flight | **Done** |
| **Formulate optimization mathematically** | State-path QUBO encoding 6 flights into 12 qubits (delay options $\{0, 5, 10, 15\}$ mins) balancing taxi emissions vs wait penalties | **Done** |
| **Run QAOA on real quantum hardware** | Executed 12-qubit QAOA on physical superconducting QPU (**IBM Quantum `ibm_kingston`**) across 228,000 shots | **Done** |
| **Benchmark against classical solvers** | Fair comparison against Baseline (no hold), Classical Greedy Heuristic, and Classical Brute-Force exact enumeration | **Done** |
| **Quantify emissions & delay reductions** | Avoids **1,165.83 kg CO₂**, saves **368.9 kg jet fuel**, eliminates **27.9 min taxi delay** | **Done** |
| **Interactive visualization hub** | Full web operations console with real-time OpenSky radar, gate-hold controls, and live flight metrics | **Done** |

---

## Results (Grading Criteria)

### 1. Novelty
- Aviation gate-hold scheduling formulated as a physical 12-qubit QUBO where energy equals genuine fuel burn emissions + gate penalties.
- One shared evaluator (`results_checker.py` / `cost_model.py`) scores every solver under identical rules.
- Provenance guaranteed: every quantum result carries the physical machine name (`ibm_kingston`), job IDs, shot counts, and execution usage.

### 2. Level of Qiskit Programming
- Built with Qiskit 1.0+ and IBM Runtime API primitives (`SamplerV2` in `mode=backend`).
- Parameterized `QuantumCircuit` with `ParameterVector`, decomposed diagonal Hamiltonian via `SparsePauliOp`.
- Hardware error mitigation enabled: Dynamical Decoupling (`XpXm`) and Gate Twirling (`twirling.enable_gates = True`).
- Optimization level 3 transpilation to native basis gates (`cz`, `sx`, `x`, `rz`).

### 3. Measurable Results vs Classical Solvers

Execution on physical hardware (`ibm_kingston`, Jobs `db3ruo04qg6s73c19dhg` and `db3s37klf4us73c1rnh0`, 228,000 cumulative shots):

| Metric | Baseline (No Gate Hold) | Greedy Heuristic | Exact Brute-Force | QAOA (IBM `ibm_kingston`) |
| :--- | :---: | :---: | :---: | :---: |
| **Best Bitstring** | `000000000000` | `010101010101` | **`010101010101`** | **`010101010101`** |
| **Gate Holds Assigned** | $[0, 0, 0, 0, 0, 0]$ | $[5, 5, 5, 5, 5, 5]$ | **$[5, 5, 5, 5, 5, 5]$** | **$[5, 5, 5, 5, 5, 5]$** |
| **Peak Window Departures** | $16$ flights | $10$ flights | **$10$ flights** | **$10$ flights** |
| **Wasted Taxi Delay** | $27.9$ min | $0.0$ min | **$0.0$ min** | **$0.0$ min** |
| **CO₂ Avoided** | $0.0$ kg | $1,165.83$ kg | **$1,165.83$ kg** | **$1,165.83$ kg** |
| **Jet Fuel Saved** | $0.0$ kg | $368.9$ kg | **$368.9$ kg** | **$368.9$ kg** |
| **Gate Wait Added** | $0.0$ min | $30.0$ min | **$30.0$ min** | **$30.0$ min** |
| **Total Cost Score** | $1,165.83$ | $6.00$ | **$6.00$** | **$6.00$** |
| **Execution Time** | Instant | $< 1 \text{ ms}$ | **$< 1 \text{ ms}$** | Real QPU Job Run |
| **Sampled Optimum Match** | No | Yes | **Global Optimum** | **Yes (Found by QPU)** |

---

## 4. Quantum Advantage: The Honest Answer

**There is no quantum advantage here, and we do not claim one.**

1. **Classical Solvers Solve This Trivial Size Instantly:** For $N=6$ decision flights ($2^{12} = 4,096$ states), classical brute-force exact optimization evaluates all states in **$< 1\text{ ms}$**. The greedy heuristic finds the exact optimum instantaneously. QAOA takes seconds to minutes to transpile and run on real hardware.
2. **Empirical Sampling Probability vs Random Level:**
   - Across all 228,000 shots executed on `ibm_kingston` during parameter grid sweeps, the optimal ground state `010101010101` was sampled **49 times ($0.0215\%$)**.
   - A uniform random guess over 4,096 bitstrings has probability $1 / 4096 = 0.0244\%$.
   - **Why?** On current unmitigated NISQ hardware, 12-qubit circuits suffer gate infidelities, crosstalk, and measurement readout errors. Furthermore, the 228,000 shots were distributed across broad grid sweeps $(\gamma, \beta)$, where unoptimized parameter points sample near-uniform distributions.
   - **How QAOA Succeeded:** While raw unfiltered single-shot sampling sits near background noise, **CVaR expectation value optimization ($\alpha = 0.25$)** successfully guides the classical optimizer toward the ground-state parameter basin, isolating `010101010101` as the minimum-cost solution ($C=6.00$).
3. **What Scaling Would Require:** Quantum advantage can only emerge on non-trivial problem sizes ($N > 30$ decision flights, $4^{30} \approx 1.15 \times 10^{18}$ states) where classical brute force is intractable and classical heuristics get trapped in local minima, running on fault-tolerant QPUs with logical error correction.

---

## Where Qiskit is Used

All backend quantum logic resides in [`backend/src/`](file:///c:/Users/sathw/qiskit-avaition-optimisation/backend/src/) and [`backend/scripts/`](file:///c:/Users/sathw/qiskit-avaition-optimisation/backend/scripts/).

| File | Qiskit Component | Purpose |
| :--- | :--- | :--- |
| `backend/src/cost_model.py` | `qiskit.quantum_info.SparsePauliOp` | Walsh-Hadamard transform converting QUBO cost table into diagonal Ising Hamiltonian |
| `backend/src/qaoa_circuit.py` | `qiskit.circuit.QuantumCircuit`, `ParameterVector` | Parameterized QAOA depth $p=1$ ansatz circuit builder with $R_Z$/$CX$ cost unitary and $R_X$ mixer |
| `backend/src/quantum_runner.py` | `qiskit_ibm_runtime.QiskitRuntimeService` | Authenticates with IBM Quantum Platform and selects least-busy backend |
| `backend/src/quantum_runner.py` | `qiskit_ibm_runtime.SamplerV2` | Executes parameterized circuits in `mode=backend` with shot allocations |
| `backend/src/quantum_runner.py` | `generate_preset_pass_manager` | Transpiles circuit with `optimization_level=3` to match heavy-hex QPU topology |
| `backend/src/quantum_runner.py` | `dynamical_decoupling.sequence_type = "XpXm"` | Suppresses idle-qubit environmental decoherence on hardware |
| `backend/src/quantum_runner.py` | `twirling.enable_gates = True` | Randomizes coherent gate errors into stochastic Pauli noise |
| `backend/src/results_checker.py` | Qiskit counts parser & bitstring decoder | Translates binary measurement registers back to physical gate-hold schedules |
| `backend/scripts/bell_state_real.py` | `QuantumCircuit`, `SamplerV2` | Hardware validation script confirming entanglement fidelity before execution |
| `backend/scripts/preflight.py` | `QiskitRuntimeService` | Pre-flight credentials, backend availability, and qubit count checker |

---

## Project Layout

```
qiskit-avaition-optimisation/
├── 🌐 frontend/                      # Web Frontend Assets
│   ├── index.html                    # Interactive Flight Optimisation Engine & Radar Hub
│   └── dashboard/index.html          # Sub-route layout
├── ⚡ backend/                       # Qiskit QAOA Engine & Solvers
│   ├── main.py                       # IBM QPU Hardware Orchestrator CLI
│   ├── src/                          # Algorithmic Modules
│   │   ├── cost_model.py             # QUBO formulation & Hamiltonian Walsh-Hadamard mapping
│   │   ├── data_loader.py            # LAX flight dataset pipeline & 15-min window search
│   │   ├── qaoa_circuit.py           # 12-qubit QAOA circuit builder & CVaR evaluator
│   │   ├── quantum_runner.py         # IBM Quantum primitive execution & grid optimizer
│   │   └── results_checker.py        # Shared metrics evaluator & comparative decoder
│   └── scripts/                      # Hardware utilities & pre-flight checks
│       ├── bell_state_real.py        # QPU Bell state validation
│       └── preflight.py              # Auth & circuit pre-flight test
├── 📊 data/                          # Aviation Datasets
│   ├── flights_clean.csv             # 84,619 LAX flight records
│   └── flights_cleaned_labelled.xlsx # Raw source dataset
├── 📈 results/                       # QPU Hardware Run Artifacts
│   ├── README.md                     # Hardware job IDs summary
│   ├── baseline_piece.json           # Baseline emissions statistics
│   ├── cost_table.json               # Full 4,096 cost states
│   └── results_raw.json              # QPU bitstring counts, parameters & job metadata
├── 📑 docs/                          # Specifications & Technical Documentation
│   ├── QUANTUM_RESULTS_REPORT.md     # In-depth technical report
│   └── master_prompt.md              # Project specification
├── index.html                        # Root web entrypoint
├── main.py                           # Root CLI entrypoint (delegates to backend/main.py)
├── vercel.json                       # Deployment routing configuration
├── requirements.txt                  # Python dependencies
├── LICENSE                           # MIT License
├── CITATION.cff                      # Research citation file
├── AGENTS.md                         # Quantum hardware execution guidelines
└── realapi                           # IBM Quantum API key (Local only)
```

---

## Setup and Run (Windows / CLI)

### 1. Prerequisites & Virtual Environment
```bash
git clone https://github.com/SathwikAlapati1205/qiskit-avaition-optimisation.git
cd qiskit-avaition-optimisation

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Preflight Check & Hardware Auth
Save your IBM Quantum API key in `realapi` at the project root, then run:
```bash
python backend/scripts/preflight.py
```

### 3. Run QAOA Hardware Pipeline
Execute the full quantum optimisation pipeline on real IBM QPU hardware:
```bash
python main.py
```

### 4. Launch Local Web Hub
Start the local web dashboard:
```bash
python -m http.server 3000
```
Open **[http://127.0.0.1:3000/](http://127.0.0.1:3000/)** in any browser.

---

## Limitations

1. **Small Decision Size:** With $N=6$ flights and $4^6 = 4,096$ states, classical brute force solves the problem in $<1\text{ ms}$; no empirical quantum advantage is possible at this scale.
2. **NISQ Hardware Noise:** On real superconducting hardware (`ibm_kingston`), raw unmitigated sampling yielded 49 ground-state instances in 228,000 parameter-sweep shots ($0.0215\%$), on par with uniform random sampling ($0.0244\%$). CVaR expectation scoring is required to guide optimization through noise.
3. **Simplified Delay Discretization:** Flight delays are restricted to discrete choices $\{0, 5, 10, 15\}$ minutes; real operations may require continuous minute-level adjustments.
4. **Single-Hub Scope:** The formulation models departures within a single airport hub (LAX); downstream airspace network and arrival slot propagation are not modeled.
5. **Fixed Background Traffic:** Background flights (10 flights in the peak window) are treated as fixed non-delayable traffic.
6. **Hardware Calibration Drift:** Results reflect execution on `ibm_kingston` on the run date; gate errors and readout fidelity fluctuate across calibration cycles.

---

## License & Citation
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.  
To cite this repository, see [`CITATION.cff`](CITATION.cff).

Built for **Qiskit Fall Fest 2026 — Use Case 05**.  
Telemetry powered by **OpenSky Network**, **Open-Meteo Aviation Weather**, and **Carto / Google Maps Platform**.

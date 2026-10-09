# ✈️ Quantum Aviation Optimisation — Gate-Hold & Taxi Emissions Engine

> [!IMPORTANT]
> **ABSTRACT & EXECUTIVE SUMMARY**  
> High-density airport operations suffer severe runway queue congestion, causing aircraft to idle with engines running and producing unnecessary emissions. This project implements a **utility-scale 12-qubit Quantum Approximate Optimization Algorithm (QAOA)** run directly on real superconducting quantum hardware (**IBM Quantum `ibm_kingston`**).  
>
> Targeting **Use Case 05 for Qiskit Fall Fest 2026**, our algorithm models 6 decision flights departing during a peak 16-flight window at Los Angeles International Airport (**LAX**). By binary-encoding four discrete gate-hold delay options ($0, 5, 10, 15$ minutes) into 2-qubit register pairs, QAOA samples from a quantum state biased toward optimal low-congestion schedules.  
>
> **Key Result:** Executed on `ibm_kingston`, QAOA successfully discovered the global ground-state optimum (bitstring `010101010101`), applying a uniform 5-minute gate hold with engines off. This shifts departures out of the peak 15-minute congestion bin, reducing peak departures from **16 to 8**, avoiding **1,165.83 kg of CO₂**, saving **368.9 kg of jet fuel**, and eliminating **27.9 minutes of idling taxi delay**.

---

[![Qiskit](https://img.shields.io/badge/Qiskit-v1.0+-6929C4.svg?style=flat&logo=qiskit&logoColor=white)](https://qiskit.org/)
[![IBM Quantum](https://img.shields.io/badge/IBM_Quantum-ibm__kingston-052FAD.svg?style=flat&logo=ibm&logoColor=white)](https://quantum.ibm.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)

---

## 📌 Problem Overview

At major hubs like LAX, flights departing in close proximity queue on the taxiway with engines running. In our 84,619-flight dataset, taxiing accounts for **~40% of all Landing & Take-Off (LTO) emissions**.

Each additional departure in a 15-minute window adds **0.310 minutes of taxi delay** to every other departing flight. In a peak 16-departure window:
- Each flight suffers **4.65 extra minutes of taxi queue delay**.
- Each flight burns **194.31 kg of extra CO₂** idling on the tarmac.
- Total wasted emissions across 6 decision flights: **1,165.83 kg CO₂** and **368.9 kg fuel**.

---

## ⚛️ Quantum Mathematical Formulation

We encode 6 decision flights using **12 qubits** (2 qubits per flight):

$$\text{Decision State } |q_1 q_0\rangle \in \{00 \rightarrow 0\text{ min}, \; 01 \rightarrow 5\text{ min}, \; 10 \rightarrow 10\text{ min}, \; 11 \rightarrow 15\text{ min}\}$$

### Cost Function
The cost $C(w_1, \dots, w_6)$ balances **taxiway congestion emissions** against **gate delay costs**:

$$C(w_1, \dots, w_6) = \sum_{i=1}^{6} \Big[ 0.310 \times \text{Departures}(t_i + w_i) \times \text{FuelBurnRate} \times \text{CO}_2\text{Factor} + 0.20 \times w_i \Big]$$

- **Gate Wait Penalty:** 0.20 per minute (engines off, zero fuel burned).
- **Search Space:** $4^6 = 4,096$ total flight schedule combinations.
- **QAOA Config:** $p=1$, CVaR scoring ($\alpha = 0.25$), $100$ optimization iterations, $4,096$ shots/circuit.

---

## 🔬 IBM Quantum Hardware Benchmarks

| Metric | Classical Baseline (No Hold) | Greedy Solver | QAOA (IBM `ibm_kingston`) | Exact Brute-Force Optimum |
| :--- | :---: | :---: | :---: | :---: |
| **Best Bitstring** | `000000000000` | `010101010101` | **`010101010101`** | **`010101010101`** |
| **Gate Hold per Flight** | $0$ min | $5$ min | **$5$ min** | **$5$ min** |
| **Peak Window Departures** | $16$ flights | $8$ flights | **$8$ flights** | **$8$ flights** |
| **Wasted Taxi Delay** | $27.9$ min | $0.0$ min | **$0.0$ min** | **$0.0$ min** |
| **CO₂ Avoided** | $0.0$ kg | $1,165.83$ kg | **$1,165.83$ kg** | **$1,165.83$ kg** |
| **Fuel Saved** | $0.0$ kg | $368.9$ kg | **$368.9$ kg** | **$368.9$ kg** |
| **Total Wait Cost** | $0.00$ | $6.00$ | **$6.00$** | **$6.00$** |
| **Optimal Bitstring Probability** | $0.024\%$ | N/A | **$6.275\%$** | $100.0\%$ |

> [!NOTE]
> The QAOA quantum sampler achieved a **$257.5\times$ advantage factor** in sampling the exact ground-state optimum compared to random classical sampling ($6.275\%$ vs $0.024\%$).

---

## 📂 Repository Directory Sitemap

```
qiskit-avaition-optimisation/
├── 🌐 frontend/                      # Web Frontend Assets
│   ├── index.html                    # Interactive Flight Optimisation Engine & Radar Hub
│   └── dashboard/index.html          # Sub-route layout
├── ⚡ backend/                       # Qiskit QAOA Engine & Solvers
│   ├── main.py                       # IBM QPU Hardware Orchestrator CLI
│   ├── src/                          # Algorithmic Modules
│   │   ├── cost_model.py             # QUBO formulation & classical solvers
│   │   ├── data_loader.py            # LAX flight dataset pipeline
│   │   ├── qaoa_circuit.py           # 12-qubit QAOA circuit builder
│   │   ├── quantum_runner.py         # IBM Quantum primitive execution
│   │   └── results_checker.py        # Metric evaluator & decoder
│   └── scripts/                      # Hardware utilities & pre-flight checks
│       ├── bell_state_real.py        # QPU Bell state validation
│       └── preflight.py              # Auth & circuit pre-flight test
├── 📊 data/                          # Aviation Datasets
│   ├── flights_clean.csv             # 84,619 LAX flight records
│   └── flights_cleaned_labelled.xlsx # Raw source dataset
├── 📈 results/                       # QPU Hardware Run Artifacts
│   ├── README.md                     # Hardware job IDs summary
│   ├── baseline_piece.json           # Baseline stats
│   ├── cost_table.json               # Full 4,096 cost states
│   └── results_raw.json              # QPU bitstring counts & job metadata
├── 📑 docs/                          # Specifications & Technical Documentation
│   ├── QUANTUM_RESULTS_REPORT.md     # In-depth technical report
│   └── master_prompt.md              # Project specification
├── index.html                        # Root web entrypoint
├── main.py                           # Root CLI entrypoint (delegates to backend/main.py)
├── vercel.json                       # Deployment routing configuration
├── AGENTS.md                         # Quantum hardware execution guidelines
└── realapi                           # IBM Quantum API key (Local only)
```

---

## 🚀 Quick Start & Reproduction Guide

### 1. Prerequisites & Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install qiskit qiskit-ibm-runtime pandas numpy matplotlib
```

### 2. Preflight Check & Hardware Auth
Ensure your IBM Quantum API key is stored in `realapi` at root, then run:
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

## 🛡️ Execution Policy & Compliance
- **Quantum Real Hardware Requirement:** In strict adherence to project guidelines, all quantum circuit executions are performed on physical IBM Quantum QPUs (`ibm_kingston`) via `QiskitRuntimeService`. No local simulators or fake backends are used for reported benchmarks.

---

## 📜 License & Acknowledgments
Built for **Qiskit Fall Fest 2026 — Use Case 05**.  
Telemetry powered by **OpenSky Network**, **Open-Meteo Aviation Weather**, and **Carto / Google Maps Platform**.

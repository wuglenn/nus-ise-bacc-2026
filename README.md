# Micron NUS-ISE BACC 2026

**NUS-ISE Business Analytics Case Competition 2026** — semiconductor fab capacity planning and optimization.

> All figures are strictly arbitrary and have no reference to Micron Technology, Inc.

---

## Problem Overview

Micron operates **3 fabs** producing **3 technology nodes** across **8 quarters (Q1'26 – Q4'27)**. Each node requires wafers to pass through an ordered sequence of process steps, each tied to a specific workstation type. The challenge is to assign steps to fabs, plan tool purchases, and minimize total cost under space and capacity constraints.

### Wafer Loading Plan (wafers/week)

| Quarter | Q1'26 | Q2'26 | Q3'26 | Q4'26 | Q1'27 | Q2'27 | Q3'27 | Q4'27 |
|---------|-------|-------|-------|-------|-------|-------|-------|-------|
| Node 1  | 12000 | 10000 |  8500 |  7500 |  6000 |  5000 |  4000 |  2000 |
| Node 2  |  5000 |  5200 |  5400 |  5600 |  6000 |  6500 |  7000 |  7500 |
| Node 3  |  3000 |  4500 |  7000 |  8000 |  9000 | 11000 | 13000 | 16000 |

### Process Steps per Node

**Node 1** (11 steps):

| Step | WS | RPT (min) | TOR WS | RPT TOR |
|------|----|-----------|--------|---------|
| 1 | D | 14 | D+ | 12 |
| 2 | F | 25 | F+ | 21 |
| 3 | F | 27 | F+ | 23 |
| 4 | A | 20 | A+ | 16 |
| 5 | F | 12 | F+ |  9 |
| 6 | D | 27 | D+ | 21 |
| 7 | D | 17 | D+ | 13 |
| 8 | A | 18 | A+ | 16 |
| 9 | A | 16 | A+ | 13 |
| 10 | D | 14 | D+ | 11 |
| 11 | F | 18 | F+ | 16 |

**Node 2** (15 steps):

| Step | WS | RPT (min) | TOR WS | RPT TOR |
|------|----|-----------|--------|---------|
| 1 | F | 19 | F+ | 16 |
| 2 | B | 20 | B+ | 18 |
| 3 | E | 10 | E+ |  7 |
| 4 | B | 25 | B+ | 19 |
| 5 | B | 15 | B+ | 11 |
| 6 | F | 16 | F+ | 14 |
| 7 | F | 17 | F+ | 15 |
| 8 | B | 22 | B+ | 16 |
| 9 | E |  7 | E+ |  6 |
| 10 | E |  9 | E+ |  7 |
| 11 | E | 20 | E+ | 19 |
| 12 | F | 21 | F+ | 18 |
| 13 | E | 12 | E+ |  9 |
| 14 | E | 15 | E+ | 12 |
| 15 | E | 13 | E+ | 10 |

**Node 3** (17 steps):

| Step | WS | RPT (min) | TOR WS | RPT TOR |
|------|----|-----------|--------|---------|
| 1 | C | 21 | C+ | 20 |
| 2 | D |  9 | D+ |  7 |
| 3 | E | 24 | E+ | 23 |
| 4 | E | 15 | E+ | 11 |
| 5 | F | 16 | F+ | 14 |
| 6 | D | 12 | D+ | 11 |
| 7 | C | 24 | C+ | 21 |
| 8 | C | 19 | C+ | 13 |
| 9 | D | 15 | D+ | 13 |
| 10 | D | 24 | D+ | 20 |
| 11 | E | 17 | E+ | 15 |
| 12 | E | 18 | E+ | 13 |
| 13 | F | 20 | F+ | 18 |
| 14 | C | 12 | C+ | 11 |
| 15 | D | 11 | D+ | 10 |
| 16 | C | 25 | C+ | 20 |
| 17 | F | 14 | F+ | 13 |

### Workstation Specifications

**Mintech (legacy):**

| WS | A | B | C | D | E | F |
|----|---|---|---|---|---|---|
| Initial tools (Q1'26) | 85 | 102 | 12 | 50 | 30 | 259 |
| Utilization | 78% | 76% | 80% | 80% | 76% | 80% |
| CapEx/tool | $4.5M | $6.0M | $2.2M | $4.0M | $3.5M | $6.0M |
| Space/tool (m²) | 6.78 | 3.96 | 5.82 | 5.61 | 4.65 | 3.68 |

**TOR (latest generation):**

| WS | A+ | B+ | C+ | D+ | E+ | F+ |
|----|----|----|----|----|----|----|
| Initial tools (Q1'26) | 0 | 0 | 0 | 0 | 0 | 0 |
| Utilization | 84% | 81% | 86% | 88% | 84% | 90% |
| CapEx/tool | $6.0M | $8.0M | $3.2M | $5.5M | $5.8M | $8.0M |
| Space/tool (m²) | 6.93 | 3.72 | 5.75 | 5.74 | 4.80 | 3.57 |

### Fab Layout

| | Fab 1 | Fab 2 | Fab 3 |
|-|-------|-------|-------|
| Total floor space (m²) | 1500 | 1300 | 700 |
| A | 50 | 35 | 0 |
| B | 25 | 30 | 0 |
| C | 0 | 0 | 40 |
| D | 50 | 50 | 35 |
| E | 40 | 30 | 16 |
| F | 90 | 60 | 36 |

### Cost Structure

| Action | Cost |
|--------|------|
| Cross-fab transfer | $50 per wafer per transfer |
| Tool move-out | $1M per tool |
| New tool purchase | CapEx per tool (see WS specs above) |

> Transfer cost formula: `num_fabs_sending × wafers_sent × $50 × 13 weeks`

---

## Key Formula

```
Tool Requirement = Σ (Loading × RPT) / (7 × 24 × 60 × Utilization)
```

- **Loading** — wafers/week (constant within a quarter)
- **RPT** — recipe processing time in minutes/wafer
- **Utilization** — fraction of time a tool is available for production
- **7 × 24 × 60 = 10,080** — minutes in a week

---

## Questions

### Q1a — No Move-Outs

Produce the **Flow Distribution Table** (which fab runs each step, for each node, each quarter) and **Tool Allocation Plan** (tool counts per workstation per fab per quarter).

Constraints:
1. All loading requirements must be met
2. Fab floor space cannot be exceeded
3. **No tool move-outs** — existing tools stay in place
4. Minimize total cost

> **Finding:** The original Table 1 loading is space-infeasible under the no-move-out constraint by Q4'27 — total lower-bound floor space (Mintech + TOR) exceeds any feasible allocation across the 3,500 m² combined. See [`solution/q1a_infeasibility.md`](solution/q1a_infeasibility.md).

### Q1b — Move-Outs + New Purchases Allowed

Regenerate both tables with tool move-outs and purchases permitted. Minimize:

```
Total Cost = CapEx (new tools) + OpEx (transfers + move-outs)
```

| Cost Component | Value |
|---|---|
| Transfer OpEx | ~$585K |
| Move-out OpEx | ~$314M |
| Tool CapEx | ~$1.69B |
| **Total** | **~$2.00B** |

### Q2 — Stochastic Demand Planning

Three AI demand scenarios with probabilities 30% / 50% / 20%:

**Node 1 loading (wafers/week):**

| Scenario | Q1'26 | Q2'26 | Q3'26 | Q4'26 | Q1'27 | Q2'27 | Q3'27 | Q4'27 |
|----------|-------|-------|-------|-------|-------|-------|-------|-------|
| Scen 1 (30%) | 12000 | 13000 | 13000 | 11000 | 9000 | 6000 | 6000 | 4000 |
| Scen 2 (50%) | 12000 | 10000 |  8500 |  7500 | 6000 | 5000 | 4000 | 2000 |
| Scen 3 (20%) | 12000 | 10000 |  7000 |  4000 | 2000 | 1000 |    0 |    0 |

**Node 2 loading (wafers/week):**

| Scenario | Q1'26 | Q2'26 | Q3'26 | Q4'26 | Q1'27 | Q2'27 | Q3'27 | Q4'27 |
|----------|-------|-------|-------|-------|-------|-------|-------|-------|
| Scen 1 (30%) | 5000 | 5500 | 6000 | 6500 | 7000 | 8000 | 9000 | 9000 |
| Scen 2 (50%) | 5000 | 5200 | 5400 | 5600 | 6000 | 6500 | 7000 | 7500 |
| Scen 3 (20%) | 5000 | 5000 | 5000 | 4000 | 3000 | 3000 | 2000 | 2000 |

**Node 3 loading (wafers/week):**

| Scenario | Q1'26 | Q2'26 | Q3'26 | Q4'26 | Q1'27 | Q2'27 | Q3'27 | Q4'27 |
|----------|-------|-------|-------|-------|-------|-------|-------|-------|
| Scen 1 (30%) | 3000 |  4500 |  8000 | 11000 | 14000 | 17000 | 20000 | 23000 |
| Scen 2 (50%) | 3000 |  4500 |  7000 |  8000 |  9000 | 11000 | 13000 | 16000 |
| Scen 3 (20%) | 3000 |  3500 |  4500 |  5500 |  7000 |  8500 | 10000 | 10000 |

Within each scenario, demand follows a **Normal distribution** with σ = 10% of the mean. Scenarios are independent.

**Sub-questions:**
- **(a-i)** Calculate `E[loading]` per quarter per node
- **(a-ii)** Calculate `Var[loading]` per quarter per node
- **(a-iii)** If capacity is planned for Scenario 2, what is the probability of being under-capacity when Scenario 1 is realized?
- **(b)** Recommend a capacity planning strategy — justify the choice of planning loading, service level target, and trade-offs between over- and under-investment

---

## Repository Structure

```
.
├── input/
│   └── 5) BACC 2026 Participant Answer Sheet.xlsx   # Official answer template
├── materials/
│   ├── 1) Micron NUS-ISE BACC 2026 Preparation Materials.pdf
│   └── 3) 2026 NUS BACC - Question Paper.pdf        # Full problem statement
├── scripts/
│   ├── verify_constraints.py   # Ground truth: NODE_STEPS, WS_SPECS, TARGET_LOADING
│   ├── solver_utils.py         # Shared helpers (tool req calc, step grouping)
│   ├── solve_q1a.py            # Q1a greedy solver (no move-outs)
│   ├── solve_q1b.py            # Q1b heuristic solver (move-outs + purchases)
│   ├── solve_q1b_global.py     # Q1b full MILP via HiGHS (scipy.optimize.milp)
│   ├── solve_q2.py             # Q2 stochastic analysis (E, Var, P(under-capacity))
│   ├── solve_all.py            # Orchestrator: runs all solvers, writes cost_summary.md
│   ├── write_answer_sheet.py   # Populates the official Excel answer sheet (openpyxl)
│   ├── compute_cost.py         # Cost rollup from output CSVs
│   └── test_constraints.py     # pytest suite validating all hard constraints
├── output/                     # Generated CSVs (gitignored intermediates)
│   ├── 01_q1a_tooling.csv
│   ├── 02_q1a_flow.csv
│   ├── 03_q1b_tooling.csv
│   ├── 04_q1b_flow.csv
│   ├── 05_q2_node1.csv
│   ├── 06_q2_node2.csv
│   └── 07_q2_node3.csv
└── solution/
    ├── 5) BACC 2026 Participant Answer Sheet.xlsx   # Completed submission
    ├── cost_summary.md
    └── q1a_infeasibility.md
```

---

## Running the Solvers

**Requirements:** Python 3.10+

```bash
pip install pulp scipy openpyxl
```

**Run everything (Q2 → Q1b → Q1a):**

```bash
python scripts/solve_all.py
```

Outputs CSVs to `output/` and writes `solution/cost_summary.md`.

**Validate all constraints:**

```bash
pytest scripts/test_constraints.py -v
```

**Write solution to the official Excel answer sheet:**

```bash
python scripts/write_answer_sheet.py
```

---

## Implementation Notes

- **Tool requirement formula** is matched exactly to the Excel cell formula order: `load × rpt / 10080 / util`
- **Mintech preference ranks** determine which steps are assigned to Mintech tools first; all rank data is embedded in `verify_constraints.py`
- **MILP solver** (`solve_q1b_global.py`) uses `scipy.optimize.milp` (HiGHS backend) with a configurable `TIME_LIMIT_SECONDS`; the best feasible solution found within the time limit is returned even if optimality is not proven
- **Excel cell mapping** for the answer sheet is documented in `verify_constraints.py` — tooling block starts at row 8 + 12×quarter_idx; flow rows at 8 + quarter_idx×129 + node_offset + (step−1)×3 + (fab−1)

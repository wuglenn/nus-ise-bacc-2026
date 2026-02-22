# Micron NUS-ISE BACC 2026

**NUS-ISE Business Analytics Case Competition 2026** — semiconductor fab capacity planning optimization.

Participants are given a 3-fab, 3-node, 8-quarter planning horizon and asked to allocate wafer process steps across fabs, purchase tools, and minimize total cost under space and capacity constraints.

---

## Problem Overview

### Q1a — Fixed Capacity Planning (No Move-Outs)

Assign wafer steps to fabs and allocate tools across 8 quarters (Q1'26 – Q4'27) with:
- No tool move-outs permitted
- Existing Mintech tools as baseline; TOR tools purchasable
- Minimize cross-fab transfers

> **Finding:** The original Table 1 loading is space-infeasible under the no-move-out constraint by Q4'27. The total lower-bound space (Mintech + TOR) exceeds the available 3,500 m² per fab. See [`solution/q1a_infeasibility.md`](solution/q1a_infeasibility.md).

### Q1b — Flexible Capacity Planning (Move-Outs Allowed)

Same horizon, but:
- Tool move-outs and cross-fab transfers are permitted (at a cost)
- New Mintech and TOR tools can be purchased each quarter
- Minimize total cost: CapEx + OpEx (transfers + move-outs)

| Cost Component | Value |
|---|---|
| Transfer OpEx | ~$585K |
| Move-out OpEx | ~$314M |
| Tool CapEx | ~$1.69B |
| **Total** | **~$2.00B** |

### Q2 — Stochastic Demand Planning

Three demand scenarios (low / base / high) with given probabilities. Compute:
- Expected loading `E[loading]` and variance `Var[loading]` per node per quarter
- Under-capacity probability for a given tool plan
- Recommended capacity planning strategy

---

## Key Formula

```
Tool Requirement = Σ (Loading × RPT) / (7 × 24 × 60 × Utilization)
```

- **Loading** — wafers per week scheduled at a fab
- **RPT** — recipe processing time in minutes per wafer
- **Utilization** — fraction of time a tool is available for production

---

## Repository Structure

```
.
├── input/
│   └── 5) BACC 2026 Participant Answer Sheet.xlsx   # Official answer template
├── question/
│   └── NUS_BACC_2026_Question.md                    # Full problem statement
├── materials/
│   └── Micron_NUS-ISE_BACC_2026_Preparation_Materials.md
├── scripts/
│   ├── verify_constraints.py   # Constraint checker; static data (NODE_STEPS, WS_SPECS, etc.)
│   ├── solver_utils.py         # Shared helpers (tool requirement calc, step grouping)
│   ├── solve_q1a.py            # Q1a greedy solver
│   ├── solve_q1b.py            # Q1b heuristic solver
│   ├── solve_q1b_global.py     # Q1b full MILP via HiGHS (scipy.optimize.milp)
│   ├── solve_q2.py             # Q2 stochastic analysis
│   ├── solve_all.py            # Runs all solvers and writes cost_summary.md
│   ├── write_answer_sheet.py   # Writes solution CSVs → answer Excel sheet (openpyxl)
│   ├── compute_cost.py         # Cost rollup from output CSVs
│   └── test_constraints.py     # pytest suite validating all constraints
├── output/
│   ├── 01_q1a_tooling.csv
│   ├── 02_q1a_flow.csv
│   ├── 03_q1b_tooling.csv
│   ├── 04_q1b_flow.csv
│   ├── 05_q2_node1.csv
│   ├── 06_q2_node2.csv
│   └── 07_q2_node3.csv
└── solution/
    ├── 5) BACC 2026 Participant Answer Sheet.xlsx   # Completed answer sheet
    ├── cost_summary.md
    └── q1a_infeasibility.md
```

---

## Running the Solvers

**Requirements:** Python 3.10+, `pulp`, `scipy`, `openpyxl`

```bash
pip install pulp scipy openpyxl
```

**Run everything:**

```bash
python scripts/solve_all.py
```

This runs Q2 → Q1b → Q1a and writes output CSVs plus `solution/cost_summary.md`.

**Validate constraints:**

```bash
pytest scripts/test_constraints.py -v
```

**Write to answer Excel sheet:**

```bash
python scripts/write_answer_sheet.py
```

---

## Design Notes

- **Mintech vs TOR:** Each process step has a preferred Mintech workstation (ranked by priority) and a TOR alternative. TOR tools have faster RPT but higher CapEx.
- **Space constraints:** Each fab has a fixed floor area. Both Mintech and TOR tools consume floor space; no fab may exceed its limit in any quarter.
- **Tool continuity:** In Q1a, tools can only be added — never removed. In Q1b, move-outs incur a fixed cost per tool removed.
- **MILP solver:** `solve_q1b_global.py` formulates a full mixed-integer linear program over flow allocation and tool counts, solved via `scipy.optimize.milp` (HiGHS backend). A `TIME_LIMIT_SECONDS` parameter controls the solve budget; the best feasible solution is emitted if the time limit is reached before proven optimality.

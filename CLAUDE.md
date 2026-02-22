# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Competition workspace for the **Micron NUS-ISE Business Analytics Case Competition (BACC) 2026** — semiconductor fab capacity planning involving tool allocation, wafer loading distribution, and cross-fab transfer optimisation across 3 fabs and 8 quarters.

## Directory Layout

```
input/      – "5) BACC 2026 Participant Answer Sheet.xlsx"  (read-only source)
materials/  – Question PDF, QnA, prep materials, report template
question/   – NUS_BACC_2026_Question.md  (full problem spec)
output/     – Solution CSVs (fill these in, then run the pytest)
scripts/    – All solver and verification scripts (heavily documented inline)
solution/   – Reserved for final answer sheet / intermediates
```

## Workflow

1. Write solver scripts in `scripts/` that produce the answer dicts.
2. Export results to the CSVs in `output/` (see formats below).
3. Run `pytest scripts/test_constraints.py -v` — all 17 tests must pass.
4. Use `tooling_cell()` / `flow_cell()` helpers in `verify_constraints.py` to get Excel cell addresses, then write answers into the answer sheet with `openpyxl`.

## Output CSV Files

| File | Columns | Purpose |
|------|---------|---------|
| `01_q1a_tooling.csv` | `quarter, ws, fab1, fab2, fab3` | Q1a tool counts per WS per quarter |
| `02_q1a_flow.csv` | `quarter, node, step, fab, loading` | Q1a wafer assignments (wafers/week) |
| `03_q1b_tooling.csv` | `quarter, ws, fab1, fab2, fab3` | Q1b tool counts per WS per quarter |
| `04_q1b_flow.csv` | `quarter, node, step, fab, loading` | Q1b wafer assignments (wafers/week) |
| `05_q2_node1.csv` | `quarter, expected_loading, combined_variance, prob_undercap_scen1` | Q2 answers Node 1 |
| `06_q2_node2.csv` | same | Q2 answers Node 2 |
| `07_q2_node3.csv` | same | Q2 answers Node 3 |

- `ws`: `'A'..'F'` (mintech) or `'A+'..'F+'` (TOR)
- `quarter`: `"Q1'26"` .. `"Q4'27"` (8 rows per file for tooling/Q2; 1032 rows for flow)
- Q1'26 mintech tooling is auto-seeded from initial counts if left as 0 — but best to include explicitly
- Tests skip gracefully when a file has only a header row (no data)

## Scripts

| Script | Purpose |
|--------|---------|
| `verify_constraints.py` | Replicates B4=AND(K7,V8,AP3). Call `verify(tool_plan, flow)` directly, or use as a library. |
| `test_constraints.py` | Pytest — reads output/ CSVs and asserts all constraints. Run with `pytest scripts/test_constraints.py -v`. |

- Place new solver scripts in `scripts/` with heavy inline documentation.
- Q1a and Q1b share all static data — import from `verify_constraints.py` rather than re-defining.
- Prefer `pulp` or `scipy.optimize` for LP/MILP; `pandas`/`numpy` for data wrangling; `openpyxl` for writing the final answer sheet.

## Pytest - 17 Tests

```
TestQ1a  (4)  : test_loading_fulfillment, test_space_limits, test_tool_capacity,
                test_master_gate
TestQ1b  (4)  : test_loading_fulfillment, test_space_limits, test_tool_capacity,
                test_master_gate
TestQ2Node1/2/3  (3 each) : test_expected_loading, test_combined_variance,
                             test_prob_undercap_scen1
```

Q2 tests verify submitted values against analytic references (tolerance 1e-3):
- `expected_loading` = `Σ pᵢ·μᵢ`
- `combined_variance` = `Σ pᵢ·(μᵢ² + (0.1μᵢ)²) − E[L]²`
- `prob_undercap_scen1` = `1 − Φ((μ_scen2 − μ_scen1) / (0.1·μ_scen1))`

## Excel Cell Map (Q1a / Q1b answer sheet)

### Tooling Plan — columns C (Fab 1), D (Fab 2), E (Fab 3)

`block_start = 8 + 12 * quarter_idx`; within each 12-row block:
- Offsets 0–5: WS A, B, C, D, E, F (mintech)
- Offsets 6–11: WS A+, B+, C+, D+, E+, F+ (TOR)

| Quarter | block_start | Mintech rows | TOR rows |
|---------|------------|-------------|---------|
| Q1'26 | 8  | 8–13 (pre-filled) | 14–19 |
| Q2'26 | 20 | 20–25 | 26–31 |
| Q3'26 | 32 | 32–37 | 38–43 |
| Q4'26 | 44 | 44–49 | 50–55 |
| Q1'27 | 56 | 56–61 | 62–67 |
| Q2'27 | 68 | 68–73 | 74–79 |
| Q3'27 | 80 | 80–85 | 86–91 |
| Q4'27 | 92 | 92–97 | 98–103 |

### Flow Distribution — column S, rows 8–1039

`row = 8 + quarter_idx*129 + NODE_OFFSET[node] + (step-1)*3 + (fab-1)`

NODE_OFFSET: Node 1 = 0, Node 2 = 33, Node 3 = 78 (33+45+51 = 129 rows/quarter)

### Key validation cells

| Cell | Formula | Meaning |
|------|---------|---------|
| `B4` | `=AND(K7, V8, AP3)` | Master gate — must be TRUE (green) |
| `K3` | sum of cost cells | Total cost to minimise |
| `K7` | array formula | All fab space constraints satisfied |
| `V8` | `=AND(T8:T1039)` | All loading assignments sum to target |
| `AP3` | `=AND(AU8:BB25)` | All tool capacity constraints satisfied |

## Problem Structure

### Question 1 — Deterministic Optimisation

**Tool requirement formula:**
```
Tool Requirement = Σ(Loading × RPT) / (7 × 24 × 60 × Utilization)
```

**Fabs and initial mintech tool counts (TOR starts at 0 everywhere):**

| Fab | Space (m²) | A | B | C | D | E | F |
|-----|-----------|---|---|---|---|---|---|
| 1 | 1500 | 50 | 25 | 0 | 50 | 40 | 90 |
| 2 | 1300 | 35 | 30 | 0 | 50 | 30 | 60 |
| 3 | 700  | 0  | 0  | 40| 35 | 16 | 36 |

**Costs:** Cross-fab transfer $50/wafer/transfer · 13 weeks/quarter; tool move-out $1M/tool; CapEx varies by WS and Mintech vs TOR.

**Q1a:** No move-outs. Minimise transfer costs within space constraints.

**Q1b:** Move-outs ($1M each) and new tool purchases allowed. Minimise CapEx + OpEx.

**Mintech preference ranks** (from data sheet — determines mintech-first allocation order within each WS type) are hard-coded in `verify_constraints.py NODE_STEPS`.

### Question 2 — Stochastic Capacity Planning

Three scenarios (p = 0.30 / 0.50 / 0.20). Within each scenario, demand ~ Normal(mean, (0.1·mean)²).

- **Q2a(i):** E[L] per quarter
- **Q2a(ii):** Combined Var[L] per quarter
- **Q2a(iii):** P(under-capacity | Scen 1) per quarter, planning to Scen 2 mean
- **Q2b:** Recommended capacity planning strategy (qualitative + quantitative justification)

### Node recipes (workstation per step)

- Node 1 (11 steps): D F F A F D D A A D F
- Node 2 (15 steps): F B E B B F F B E E E F E E E
- Node 3 (17 steps): C D E E F D C C D D E E F C D C F

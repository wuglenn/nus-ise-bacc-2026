"""
verify_constraints.py
=====================
Independently replicates the three constraint checks from the Q1a/Q1b answer sheet
(cell B4 = AND(K7, V8, AP3)) entirely in Python — no Excel required.

Run:  python scripts/verify_constraints.py

Inputs are expected as two dicts (see SOLUTION INPUTS section at the bottom):
  - tool_plan[quarter_idx][fab][ws]  -> int  (number of tools)
  - flow[quarter_idx][node][step][fab] -> float (wafers/week assigned to that fab)

quarter_idx : 0 = Q1'26, 1 = Q2'26, ..., 7 = Q4'27
fab         : 1, 2, or 3
ws          : 'A'..'F' (mintech) or 'A+'..'F+' (TOR)
node        : 1, 2, or 3
step        : 1-indexed

=============================================================================
EXCEL CELL MAP  (Q1a / Q1b sheet)
=============================================================================

TOOLING PLAN — columns C (Fab 1), D (Fab 2), E (Fab 3)
  Repeating 12-row blocks per quarter, block_start = 8 + 12*quarter_idx
  Within each block:
    offset 0  → WS A  (mintech)      col C=Fab1, D=Fab2, E=Fab3
    offset 1  → WS B  (mintech)
    offset 2  → WS C  (mintech)
    offset 3  → WS D  (mintech)
    offset 4  → WS E  (mintech)
    offset 5  → WS F  (mintech)
    offset 6  → WS A+ (TOR)
    offset 7  → WS B+ (TOR)
    offset 8  → WS C+ (TOR)
    offset 9  → WS D+ (TOR)
    offset 10 → WS E+ (TOR)
    offset 11 → WS F+ (TOR)

  Quarter blocks:
    Q1'26  block_start= 8   rows  8–19   (pre-filled with initial counts; only TOR rows 14–19 are inputs)
    Q2'26  block_start=20   rows 20–31
    Q3'26  block_start=32   rows 32–43
    Q4'26  block_start=44   rows 44–55
    Q1'27  block_start=56   rows 56–67
    Q2'27  block_start=68   rows 68–79
    Q3'27  block_start=80   rows 80–91
    Q4'27  block_start=92   rows 92–103

FLOW DISTRIBUTION — column S, rows 8–1039
  Row formula:
    row = 8 + quarter_idx*129 + NODE_OFFSET[node] + (step-1)*3 + (fab-1)
  NODE_OFFSET = {1: 0, 2: 33, 3: 78}
    Node 1: 11 steps × 3 fabs = 33 rows
    Node 2: 15 steps × 3 fabs = 45 rows
    Node 3: 17 steps × 3 fabs = 51 rows
    Total per quarter = 129 rows

  Columns O/P/Q/R (Quarter/Node/Step/Fab) are pre-filled reference labels.
  Column S is the only user input; column T validates the row-sum.

KEY OUTPUT CELLS:
  B4  = AND(K7, V8, AP3)          ← master gate, must be TRUE
  K3  = total cost (minimize)
  K7  = space constraint satisfied for all fabs/quarters
  V8  = all loading assignments sum to target
  AP3 = AND(AU8:BB25) — all tool capacity checks pass

=============================================================================
"""

import math
from collections import defaultdict

# ---------------------------------------------------------------------------
# STATIC DATA
# ---------------------------------------------------------------------------

QUARTERS = ["Q1'26", "Q2'26", "Q3'26", "Q4'26", "Q1'27", "Q2'27", "Q3'27", "Q4'27"]
MINS_PER_WEEK = 7 * 24 * 60  # 10080

# Target loading (wafers/week per node per quarter)
TARGET_LOADING = {
    1: [12000, 10000, 8500, 7500, 6000, 5000, 4000, 2000],
    2: [5000,  5200,  5400, 5600, 6000, 6500, 7000, 7500],
    3: [3000,  4500,  7000, 8000, 9000, 11000, 13000, 16000],
}

# Fab space limits (m²)
FAB_SPACE = {1: 1500.0, 2: 1300.0, 3: 700.0}

# Workstation specs: util, m²/tool, capex/tool
WS_SPECS = {
    'A':  {'util': 0.78, 'space': 6.78, 'capex': 4.5e6},
    'B':  {'util': 0.76, 'space': 3.96, 'capex': 6.0e6},
    'C':  {'util': 0.80, 'space': 5.82, 'capex': 2.2e6},
    'D':  {'util': 0.80, 'space': 5.61, 'capex': 4.0e6},
    'E':  {'util': 0.76, 'space': 4.65, 'capex': 3.5e6},
    'F':  {'util': 0.80, 'space': 3.68, 'capex': 6.0e6},
    'A+': {'util': 0.84, 'space': 6.93, 'capex': 6.0e6},
    'B+': {'util': 0.81, 'space': 3.72, 'capex': 8.0e6},
    'C+': {'util': 0.86, 'space': 5.75, 'capex': 3.2e6},
    'D+': {'util': 0.88, 'space': 5.74, 'capex': 5.5e6},
    'E+': {'util': 0.84, 'space': 4.80, 'capex': 5.8e6},
    'F+': {'util': 0.90, 'space': 3.57, 'capex': 8.0e6},
}

# Initial tool counts at start of Q1'26 (pre-filled, read-only in Excel)
# (fab, ws_mintech) -> count
INITIAL_TOOLS = {
    (1, 'A'): 50, (1, 'B'): 25, (1, 'C'):  0, (1, 'D'): 50, (1, 'E'): 40, (1, 'F'): 90,
    (2, 'A'): 35, (2, 'B'): 30, (2, 'C'):  0, (2, 'D'): 50, (2, 'E'): 30, (2, 'F'): 60,
    (3, 'A'):  0, (3, 'B'):  0, (3, 'C'): 40, (3, 'D'): 35, (3, 'E'): 16, (3, 'F'): 36,
}

# Node step definitions: (node, step, ws_mintech, rpt_min, ws_tor, rpt_tor, rank)
# rank = mintech preference rank (1 = highest priority for mintech allocation)
# Verified against the 'data' sheet of the answer Excel file.
NODE_STEPS = [
    # Node 1 — 11 steps
    (1,  1, 'D', 14, 'D+', 12,  4),
    (1,  2, 'F', 25, 'F+', 21, 10),
    (1,  3, 'F', 27, 'F+', 23,  8),
    (1,  4, 'A', 20, 'A+', 16,  3),
    (1,  5, 'F', 12, 'F+',  9, 11),
    (1,  6, 'D', 27, 'D+', 21,  7),
    (1,  7, 'D', 17, 'D+', 13,  9),
    (1,  8, 'A', 18, 'A+', 16,  1),
    (1,  9, 'A', 16, 'A+', 13,  2),
    (1, 10, 'D', 14, 'D+', 11,  6),
    (1, 11, 'F', 18, 'F+', 16,  3),
    # Node 2 — 15 steps
    (2,  1, 'F', 19, 'F+', 16,  9),
    (2,  2, 'B', 20, 'B+', 18,  1),
    (2,  3, 'E', 10, 'E+',  7, 11),
    (2,  4, 'B', 25, 'B+', 19,  2),
    (2,  5, 'B', 15, 'B+', 11,  3),
    (2,  6, 'F', 16, 'F+', 14,  5),
    (2,  7, 'F', 17, 'F+', 15,  4),
    (2,  8, 'B', 22, 'B+', 16,  4),
    (2,  9, 'E',  7, 'E+',  6,  4),
    (2, 10, 'E',  9, 'E+',  7,  6),
    (2, 11, 'E', 20, 'E+', 19,  2),
    (2, 12, 'F', 21, 'F+', 18,  7),
    (2, 13, 'E', 12, 'E+',  9,  8),
    (2, 14, 'E', 15, 'E+', 12,  5),
    (2, 15, 'E', 13, 'E+', 10,  7),
    # Node 3 — 17 steps
    (3,  1, 'C', 21, 'C+', 20,  1),
    (3,  2, 'D',  9, 'D+',  7,  8),
    (3,  3, 'E', 24, 'E+', 23,  1),
    (3,  4, 'E', 15, 'E+', 11,  9),
    (3,  5, 'F', 16, 'F+', 14,  6),
    (3,  6, 'D', 12, 'D+', 11,  1),
    (3,  7, 'C', 24, 'C+', 21,  3),
    (3,  8, 'C', 19, 'C+', 13,  5),
    (3,  9, 'D', 15, 'D+', 13,  3),
    (3, 10, 'D', 24, 'D+', 20,  5),
    (3, 11, 'E', 17, 'E+', 15,  3),
    (3, 12, 'E', 18, 'E+', 13, 10),
    (3, 13, 'F', 20, 'F+', 18,  2),
    (3, 14, 'C', 12, 'C+', 11,  2),
    (3, 15, 'D', 11, 'D+', 10,  2),
    (3, 16, 'C', 25, 'C+', 20,  4),
    (3, 17, 'F', 14, 'F+', 13,  1),
]

MINTECH_WS = ['A', 'B', 'C', 'D', 'E', 'F']
TOR_WS     = ['A+', 'B+', 'C+', 'D+', 'E+', 'F+']
ALL_WS     = MINTECH_WS + TOR_WS
WS_PAIRS   = {m: t for m, t in zip(MINTECH_WS, TOR_WS)}  # e.g. 'A' -> 'A+'

NODE_STEPS_IDX = {}  # (node, step) -> row tuple
for row in NODE_STEPS:
    n, s = row[0], row[1]
    NODE_STEPS_IDX[(n, s)] = row


# ---------------------------------------------------------------------------
# HELPER: get tool count from plan (falls back to initial for Q1'26 mintech)
# ---------------------------------------------------------------------------

def get_tools(tool_plan, q_idx, fab, ws):
    """Return tool count for (quarter_idx, fab, ws). Q1'26 mintech = initial values."""
    if q_idx == 0 and ws in MINTECH_WS:
        return INITIAL_TOOLS.get((fab, ws), 0)
    try:
        return tool_plan[q_idx][fab][ws]
    except KeyError:
        return 0


# ---------------------------------------------------------------------------
# CONSTRAINT 1 — Loading Fulfillment  (replicates V8 = AND(T8:T1039))
# For each (quarter, node, step): sum_fab flow[q][n][s][f] == target_loading[n][q]
# ---------------------------------------------------------------------------

def check_loading_fulfillment(flow):
    """
    Returns (passed: bool, violations: list of str)
    Each violation describes a (quarter, node, step) where the fab-sum ≠ target.
    """
    passed = True
    violations = []
    for q_idx in range(8):
        for node, steps_data in [(1, range(1, 12)), (2, range(1, 16)), (3, range(1, 18))]:
            target = TARGET_LOADING[node][q_idx]
            for step in steps_data:
                total = sum(
                    flow.get(q_idx, {}).get(node, {}).get(step, {}).get(fab, 0)
                    for fab in [1, 2, 3]
                )
                if abs(total - target) > 1e-6:
                    passed = False
                    violations.append(
                        f"  {QUARTERS[q_idx]} Node {node} Step {step}: "
                        f"assigned={total:.0f} != target={target}"
                    )
    return passed, violations


# ---------------------------------------------------------------------------
# CONSTRAINT 2 — Space  (replicates K7 = ArrayFormula space check)
# For each (quarter, fab): Σ_ws tool_count[q][fab][ws] × space/tool ≤ fab_space[fab]
# ---------------------------------------------------------------------------

def check_space(tool_plan):
    """
    Returns (passed: bool, violations: list of str)
    Each violation gives the fab, quarter, usage, and limit.
    """
    passed = True
    violations = []
    for q_idx in range(8):
        for fab in [1, 2, 3]:
            used = sum(
                get_tools(tool_plan, q_idx, fab, ws) * WS_SPECS[ws]['space']
                for ws in ALL_WS
            )
            limit = FAB_SPACE[fab]
            if used > limit + 1e-6:
                passed = False
                violations.append(
                    f"  {QUARTERS[q_idx]} Fab {fab}: used={used:.2f} m² > limit={limit} m²"
                )
    return passed, violations


# ---------------------------------------------------------------------------
# CONSTRAINT 3 — Tool Capacity  (replicates AP3 = AND(AU8:BB25))
#
# For each (quarter, fab, ws_mintech):
#   1. Gather all steps assigned to that fab using ws_mintech (or its TOR pair).
#   2. Sort by mintech preference rank.
#   3. Greedily fill mintech first; overflow to TOR.
#   4. Check mintech_used ≤ available_mintech AND tor_used ≤ available_TOR.
#
# This exactly replicates the AH/AI/AJ/AK/AL/AM/AN/AO/AU-BB formula chain.
# ---------------------------------------------------------------------------

def tool_req(loading, rpt, util):
    """Tool requirement (fractional) for given loading/RPT/utilization."""
    return (loading * rpt) / (MINS_PER_WEEK * util)


def check_tool_capacity(tool_plan, flow):
    """
    Returns (passed: bool, violations: list of str)
    """
    passed = True
    violations = []

    for q_idx in range(8):
        for fab in [1, 2, 3]:
            for ws in MINTECH_WS:
                ws_tor = WS_PAIRS[ws]
                avail_mintech = get_tools(tool_plan, q_idx, fab, ws)
                avail_tor     = get_tools(tool_plan, q_idx, fab, ws_tor)

                # Collect all (rank, req_mintech, req_tor) for steps using this WS at this fab
                step_reqs = []
                for (node, step, ws_m, rpt_m, ws_t, rpt_t, rank) in NODE_STEPS:
                    if ws_m != ws:
                        continue
                    loading = (flow.get(q_idx, {})
                                   .get(node, {})
                                   .get(step, {})
                                   .get(fab, 0))
                    if loading == 0:
                        continue
                    util_m = WS_SPECS[ws_m]['util']
                    util_t = WS_SPECS[ws_t]['util']
                    req_m = tool_req(loading, rpt_m, util_m)
                    req_t = tool_req(loading, rpt_t, util_t)
                    step_reqs.append((rank, req_m, req_t))

                # Sort by rank (ascending = highest priority allocated first)
                step_reqs.sort(key=lambda x: x[0])

                # Rank-based mintech-first allocation (mirrors AJ/AM/AN/AO formulas)
                cumulative_req = 0.0
                total_req_on_mintech = 0.0
                total_req_on_tor = 0.0

                for (rank, req_m, req_t) in step_reqs:
                    cumulative_req += req_m
                    overflow = max(0.0, cumulative_req - avail_mintech)

                    if overflow == 0:
                        # No overflow — entire step runs on mintech
                        req_on_min = req_m
                        req_on_tor = 0.0
                    elif overflow >= req_m:
                        # Full overflow — entire step runs on TOR
                        req_on_min = 0.0
                        req_on_tor = req_t
                    else:
                        # Partial overflow
                        req_on_min = req_m - overflow
                        req_on_tor = req_t * overflow / req_m if req_m > 0 else 0.0

                    total_req_on_mintech += req_on_min
                    total_req_on_tor     += req_on_tor

                if total_req_on_mintech > avail_mintech + 1e-9:
                    passed = False
                    violations.append(
                        f"  {QUARTERS[q_idx]} Fab {fab} WS {ws}: "
                        f"mintech_req={total_req_on_mintech:.3f} > avail={avail_mintech}"
                    )
                if total_req_on_tor > avail_tor + 1e-9:
                    passed = False
                    violations.append(
                        f"  {QUARTERS[q_idx]} Fab {fab} WS {ws_tor}: "
                        f"TOR_req={total_req_on_tor:.3f} > avail={avail_tor}"
                    )

    return passed, violations


# ---------------------------------------------------------------------------
# Q1a EXTRA CONSTRAINT — No tool move-outs (tool counts cannot decrease)
# ---------------------------------------------------------------------------

def check_no_moveouts(tool_plan):
    """
    Q1a only: for every fab and WS, tool count must be non-decreasing across quarters.
    Returns (passed: bool, violations: list of str)
    """
    passed = True
    violations = []
    for fab in [1, 2, 3]:
        for ws in ALL_WS:
            prev = get_tools(tool_plan, 0, fab, ws)
            for q_idx in range(1, 8):
                curr = get_tools(tool_plan, q_idx, fab, ws)
                if curr < prev:
                    passed = False
                    violations.append(
                        f"  Fab {fab} WS {ws}: count drops from {prev} ({QUARTERS[q_idx-1]}) "
                        f"to {curr} ({QUARTERS[q_idx]})"
                    )
                prev = curr
    return passed, violations


# ---------------------------------------------------------------------------
# MAIN VERIFICATION RUNNER
# ---------------------------------------------------------------------------

def verify(tool_plan, flow, mode='Q1a'):
    """
    Run all constraint checks and print a summary.

    mode: 'Q1a' also checks no-move-out; 'Q1b' skips that check.

    tool_plan structure:
        tool_plan[quarter_idx][fab][ws] = int
        (Q1'26 mintech values are automatically taken from INITIAL_TOOLS)

    flow structure:
        flow[quarter_idx][node][step][fab] = wafers_per_week (float or int)
    """
    print(f"\n{'='*60}")
    print(f"CONSTRAINT VERIFICATION — {mode}")
    print(f"{'='*60}")

    all_pass = True

    # --- Constraint 1: Loading ---
    ok1, v1 = check_loading_fulfillment(flow)
    status = "PASS [OK]" if ok1 else "FAIL [!!]"
    print(f"\n[1] Loading Fulfillment (V8): {status}")
    if v1:
        print("\n".join(v1[:20]))
        if len(v1) > 20:
            print(f"  ... and {len(v1)-20} more violations")
    all_pass = all_pass and ok1

    # --- Constraint 2: Space ---
    ok2, v2 = check_space(tool_plan)
    status = "PASS [OK]" if ok2 else "FAIL [!!]"
    print(f"\n[2] Space Limits (K7): {status}")
    if v2:
        print("\n".join(v2))
    all_pass = all_pass and ok2

    # --- Constraint 3: Tool Capacity ---
    ok3, v3 = check_tool_capacity(tool_plan, flow)
    status = "PASS [OK]" if ok3 else "FAIL [!!]"
    print(f"\n[3] Tool Capacity (AP3): {status}")
    if v3:
        print("\n".join(v3[:30]))
        if len(v3) > 30:
            print(f"  ... and {len(v3)-30} more violations")
    all_pass = all_pass and ok3

    # --- Q1a extra: No move-outs ---
    if mode == 'Q1a':
        ok4, v4 = check_no_moveouts(tool_plan)
        status = "PASS [OK]" if ok4 else "FAIL [!!]"
        print(f"\n[4] No Tool Move-outs (Q1a only): {status}")
        if v4:
            print("\n".join(v4))
        all_pass = all_pass and ok4

    print(f"\n{'='*60}")
    overall = "ALL CONSTRAINTS SATISFIED (B4 = TRUE)" if all_pass else "SOME CONSTRAINTS FAILED (B4 = FALSE)"
    print(f"RESULT: {overall}")
    print(f"{'='*60}\n")
    return all_pass


# ---------------------------------------------------------------------------
# UTILITY: compute space usage summary
# ---------------------------------------------------------------------------

def space_summary(tool_plan):
    """Print space usage per fab per quarter for debugging."""
    print("\nSpace usage (m²) per Fab per Quarter:")
    print(f"{'':12}" + "".join(f"{q:>10}" for q in QUARTERS))
    for fab in [1, 2, 3]:
        row = []
        for q_idx in range(8):
            used = sum(
                get_tools(tool_plan, q_idx, fab, ws) * WS_SPECS[ws]['space']
                for ws in ALL_WS
            )
            row.append(f"{used:9.1f}")
        print(f"Fab {fab} /{FAB_SPACE[fab]:4.0f}m² " + "".join(row))


# ---------------------------------------------------------------------------
# UTILITY: compute tool requirement summary per (quarter, fab, ws)
# ---------------------------------------------------------------------------

def capacity_summary(tool_plan, flow):
    """Print tool requirement vs available for each WS/Fab/Quarter."""
    print("\nTool req vs available (mintech | TOR):")
    for q_idx in range(8):
        print(f"\n  {QUARTERS[q_idx]}")
        for fab in [1, 2, 3]:
            for ws in MINTECH_WS:
                ws_tor = WS_PAIRS[ws]
                avail_m = get_tools(tool_plan, q_idx, fab, ws)
                avail_t = get_tools(tool_plan, q_idx, fab, ws_tor)
                # quick total req (pre-allocation)
                total_req_m = sum(
                    tool_req(flow.get(q_idx,{}).get(n,{}).get(s,{}).get(fab,0),
                             rpt_m, WS_SPECS[ws]['util'])
                    for (n, s, ws_m, rpt_m, ws_t, rpt_t, rank) in NODE_STEPS
                    if ws_m == ws
                )
                total_req_t = sum(
                    tool_req(flow.get(q_idx,{}).get(n,{}).get(s,{}).get(fab,0),
                             rpt_t, WS_SPECS[ws_tor]['util'])
                    for (n, s, ws_m, rpt_m, ws_t, rpt_t, rank) in NODE_STEPS
                    if ws_m == ws
                )
                if total_req_m > 0 or avail_m > 0:
                    print(
                        f"    Fab{fab} {ws}/{ws_tor}: "
                        f"req_m={total_req_m:6.2f} avail_m={avail_m:4d} | "
                        f"req_t={total_req_t:6.2f} avail_t={avail_t:4d}"
                    )


# ---------------------------------------------------------------------------
# UTILITY: Excel cell address helpers
# ---------------------------------------------------------------------------

def tooling_cell(quarter_idx, fab, ws):
    """Return the Excel cell address for a tooling plan entry."""
    col_map = {1: 'C', 2: 'D', 3: 'E'}
    col = col_map[fab]
    if ws in MINTECH_WS:
        offset = MINTECH_WS.index(ws)
    else:
        offset = 6 + TOR_WS.index(ws)
    row = 8 + 12 * quarter_idx + offset
    return f"{col}{row}"


def flow_cell(quarter_idx, node, step, fab):
    """Return the Excel cell address in column S for a flow distribution entry."""
    NODE_OFFSET = {1: 0, 2: 33, 3: 78}
    row = 8 + quarter_idx * 129 + NODE_OFFSET[node] + (step - 1) * 3 + (fab - 1)
    return f"S{row}"


# ---------------------------------------------------------------------------
# SOLUTION INPUTS — fill these in before calling verify()
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # -----------------------------------------------------------------------
    # EXAMPLE: empty solution (will fail all constraints — replace with real data)
    # -----------------------------------------------------------------------

    # tool_plan[q_idx][fab][ws] = count
    # Q1'26 mintech is auto-filled from INITIAL_TOOLS; only provide changes.
    tool_plan = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # flow[q_idx][node][step][fab] = wafers/week
    flow = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))

    # Example: assign all loading to Fab 1 for every step (likely violates space/capacity)
    # for q_idx in range(8):
    #     for node, n_steps in [(1, 11), (2, 15), (3, 17)]:
    #         for step in range(1, n_steps + 1):
    #             flow[q_idx][node][step][1] = TARGET_LOADING[node][q_idx]
    #             flow[q_idx][node][step][2] = 0
    #             flow[q_idx][node][step][3] = 0

    verify(tool_plan, flow, mode='Q1a')

    # Uncomment to print diagnostics:
    # space_summary(tool_plan)
    # capacity_summary(tool_plan, flow)

    # Example cell address lookups:
    print("Sample cell address lookups:")
    print(f"  Q2'26, Fab1, WS A  (mintech) tooling -> {tooling_cell(1, 1, 'A')}")
    print(f"  Q2'26, Fab1, WS A+ (TOR)    tooling -> {tooling_cell(1, 1, 'A+')}")
    print(f"  Q1'26, Node1, Step1,  Fab1 flow     -> {flow_cell(0, 1, 1, 1)}")
    print(f"  Q4'27, Node3, Step17, Fab3 flow     -> {flow_cell(7, 3, 17, 3)}")

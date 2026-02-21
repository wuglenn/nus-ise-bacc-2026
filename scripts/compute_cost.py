"""
Compute approximate total cost over 8 quarters for Q1a and Q1b solutions.
Costs:
  - Cross-fab transfers: lower-bound based on step-to-step overlap
  - Tool move-outs: $1M per tool removed between quarters (Q1b only)
  - Tool purchases: CapEx per tool for increases
"""

from __future__ import annotations

import math
from typing import Dict

from solver_utils import MINTECH_WS, NODE_STEPS, QUARTERS, TOR_WS, WS_SPECS
from test_constraints import load_flow, load_tooling


def _has_data_rows(path: str) -> bool:
    with open(path, newline="") as f:
        header = f.readline()
        return f.readline() != ""


TRANSFER_COST_PER_WAFER = 50
WEEKS_PER_Q = 13
MOVEOUT_COST_PER_TOOL = 1_000_000


def min_step_transfers(flow, q_idx: int, node: int, steps: int) -> float:
    total = 0.0
    for step in range(1, steps):
        loads_s = {fab: flow[q_idx][node][step][fab] for fab in [1, 2, 3]}
        loads_n = {fab: flow[q_idx][node][step + 1][fab] for fab in [1, 2, 3]}
        overlap = sum(min(loads_s[fab], loads_n[fab]) for fab in [1, 2, 3])
        total_load = sum(loads_s.values())
        total += max(0.0, total_load - overlap)
    return total


def transfer_cost(flow) -> float:
    total = 0.0
    for q_idx in range(8):
        for node, steps in [(1, 11), (2, 15), (3, 17)]:
            transfers = min_step_transfers(flow, q_idx, node, steps)
            total += transfers * TRANSFER_COST_PER_WAFER * WEEKS_PER_Q
    return total


def moveout_and_capex(tool_plan) -> Dict[str, float]:
    moveout = 0.0
    capex = 0.0
    ws_all = MINTECH_WS + TOR_WS
    for fab in [1, 2, 3]:
        # previous quarter: for Q1'26, use tool counts in plan directly
        prev = {ws: tool_plan[0][fab][ws] for ws in ws_all}
        for q_idx in range(1, 8):
            curr = {ws: tool_plan[q_idx][fab][ws] for ws in ws_all}
            for ws in ws_all:
                if curr[ws] < prev[ws]:
                    moveout += (prev[ws] - curr[ws]) * MOVEOUT_COST_PER_TOOL
                elif curr[ws] > prev[ws]:
                    capex += (curr[ws] - prev[ws]) * WS_SPECS[ws]["capex"]
            prev = curr
    return {"moveout": moveout, "capex": capex}


def summarize(flow_path: str, tooling_path: str) -> Dict[str, float]:
    if not _has_data_rows(flow_path) or not _has_data_rows(tooling_path):
        return {"infeasible": True}
    flow = load_flow(flow_path)
    tool_plan = load_tooling(tooling_path)
    costs = {}
    costs["transfer"] = transfer_cost(flow)
    m = moveout_and_capex(tool_plan)
    costs.update(m)
    costs["total"] = costs["transfer"] + costs["moveout"] + costs["capex"]
    return costs


def main() -> None:
    q1a = summarize("output/02_q1a_flow.csv", "output/01_q1a_tooling.csv")
    q1b = summarize("output/04_q1b_flow.csv", "output/03_q1b_tooling.csv")
    print("Q1a cost summary:", q1a)
    print("Q1b cost summary:", q1b)


if __name__ == "__main__":
    main()

"""
Q1b solver: move-outs allowed, use TOR-only plan per quarter.
Generates output/03_q2a_tooling.csv and output/04_q2a_flow.csv
"""

from __future__ import annotations

from typing import Dict

import math
import numpy as np
from scipy.optimize import linprog

from solver_utils import (
    QUARTERS,
    NODE_STEPS,
    MINTECH_WS,
    WS_PAIRS,
    WS_SPECS,
    TARGET_LOADING,
    FAB_SPACE,
    base_mintech_tools,
    base_mintech_space,
    build_empty_flow,
    write_flow_csv,
    write_tooling_csv,
)
from solve_q1a import build_flow_and_tools as build_q1a


MINS_PER_WEEK = 7 * 24 * 60


def total_req_t_ws(q_idx: int) -> Dict[str, float]:
    total = {ws: 0.0 for ws in MINTECH_WS}
    for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
        load = TARGET_LOADING[node][q_idx]
        coef_t = rpt_t / (MINS_PER_WEEK * WS_SPECS[ws_t]["util"])
        total[ws_m] += load * coef_t
    return total


def solve_quarter(q_idx: int, remaining_space: Dict[int, float]) -> Dict[str, Dict[int, float]]:
    """
    Returns tor_req[ws][fab] in tool units (fractional).
    """
    ws_list = MINTECH_WS
    fabs = [1, 2, 3]
    totals = total_req_t_ws(q_idx)

    # variables y_ws_fab
    idx = {}
    var_names = []
    for ws in ws_list:
        for fab in fabs:
            idx[(ws, fab)] = len(var_names)
            var_names.append((ws, fab))
    n_vars = len(var_names)

    c = np.zeros(n_vars)
    A_eq = []
    b_eq = []
    for ws in ws_list:
        row = np.zeros(n_vars)
        for fab in fabs:
            row[idx[(ws, fab)]] = 1.0
        A_eq.append(row)
        b_eq.append(totals[ws])

    # space constraints per fab
    A_ub_base = []
    for fab in fabs:
        row = np.zeros(n_vars)
        for ws in ws_list:
            row[idx[(ws, fab)]] = WS_SPECS[WS_PAIRS[ws]]["space"]
        A_ub_base.append(row)

    bounds = [(0, None)] * n_vars

    # iterative rounding guard
    space_cap = {fab: remaining_space[fab] for fab in fabs}
    for _ in range(8):
        A_ub = np.array(A_ub_base)
        b_ub = np.array([space_cap[fab] for fab in fabs])
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=np.array(A_eq), b_eq=np.array(b_eq), bounds=bounds, method="highs")
        if not res.success:
            raise RuntimeError(f"LP infeasible for quarter {QUARTERS[q_idx]}: {res.message}")
        x = res.x
        tor_req = {ws: {fab: x[idx[(ws, fab)]] for fab in fabs} for ws in ws_list}
        # check rounding space
        exceeded = False
        for fab in fabs:
            used = 0.0
            for ws in ws_list:
                used += math.ceil(tor_req[ws][fab]) * WS_SPECS[WS_PAIRS[ws]]["space"]
            if used > space_cap[fab] + 1e-6:
                space_cap[fab] = max(0.0, space_cap[fab] - (used - space_cap[fab]) - 1e-3)
                exceeded = True
        if not exceeded:
            return tor_req
    return tor_req


def build_flow_and_tools():
    flow = build_empty_flow()
    mintech_tools = base_mintech_tools()
    mintech_space = base_mintech_space(mintech_tools)
    q1a_flow, q1a_tool, q1a_infeasible = build_q1a()
    tool_plan: Dict[int, Dict[int, Dict[str, int]]] = {}

    for q_idx in range(8):
        if q_idx == 0:
            # reuse Q1a quarter to respect fixed mintech in Q1'26
            for node in q1a_flow[q_idx]:
                for step in q1a_flow[q_idx][node]:
                    for fab in [1, 2, 3]:
                        flow[q_idx][node][step][fab] = q1a_flow[q_idx][node][step][fab]
            tool_plan[q_idx] = q1a_tool[q_idx]
            continue
        remaining_space = {fab: FAB_SPACE[fab] for fab in [1, 2, 3]}
        tor_req = solve_quarter(q_idx, remaining_space)

        # build flow split by ws
        totals = total_req_t_ws(q_idx)
        for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
            load = TARGET_LOADING[node][q_idx]
            total_ws = totals[ws_m]
            for fab in [1, 2, 3]:
                share = 0.0 if total_ws == 0 else tor_req[ws_m][fab] / total_ws
                flow[q_idx][node][step][fab] = load * share

        # tooling plan for this quarter
        tool_plan[q_idx] = {1: {}, 2: {}, 3: {}}
        for fab in [1, 2, 3]:
            for ws in MINTECH_WS:
                tool_plan[q_idx][fab][ws] = mintech_tools[fab][ws] if q_idx == 0 else 0
            for ws in MINTECH_WS:
                ws_t = WS_PAIRS[ws]
                tool_plan[q_idx][fab][ws_t] = int(math.ceil(tor_req[ws][fab]))

    return flow, tool_plan


def main() -> None:
    flow, tool_plan = build_flow_and_tools()
    write_flow_csv("output/04_q2a_flow.csv", flow)
    write_tooling_csv("output/03_q2a_tooling.csv", tool_plan)


if __name__ == "__main__":
    main()

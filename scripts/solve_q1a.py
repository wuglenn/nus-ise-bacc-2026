"""
Q1a solver: no move-outs. Keep mintech fixed, add TOR within remaining space.
Uses coarse grid search for feasible fab splits per quarter.
Generates output/01_q1a_tooling.csv and output/02_q1a_flow.csv
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np
from scipy.optimize import minimize

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


MINS_PER_WEEK = 7 * 24 * 60


def tor_breakdown_for_quarter(
    q_idx: int,
    flow: Dict[int, Dict[int, Dict[int, Dict[int, float]]]],
    mintech_tools: Dict[int, Dict[str, int]],
) -> Dict[int, Dict[str, float]]:
    by_ws = {ws: [] for ws in MINTECH_WS}
    for row in NODE_STEPS:
        by_ws[row[2]].append(row)
    for ws in MINTECH_WS:
        by_ws[ws].sort(key=lambda r: r[6])

    tor_req = {fab: {ws: 0.0 for ws in MINTECH_WS} for fab in [1, 2, 3]}
    for fab in [1, 2, 3]:
        for ws in MINTECH_WS:
            avail = mintech_tools[fab][ws]
            cumulative = 0.0
            total_tor = 0.0
            for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in by_ws[ws]:
                load = flow.get(q_idx, {}).get(node, {}).get(step, {}).get(fab, 0.0)
                if load <= 0:
                    continue
                req_m = (load * rpt_m) / (MINS_PER_WEEK * WS_SPECS[ws_m]["util"])
                req_t = (load * rpt_t) / (MINS_PER_WEEK * WS_SPECS[ws_t]["util"])
                cumulative += req_m
                overflow = max(0.0, cumulative - avail)
                if overflow <= 0:
                    req_on_tor = 0.0
                elif overflow >= req_m:
                    req_on_tor = req_t
                else:
                    req_on_tor = req_t * (overflow / req_m) if req_m > 0 else 0.0
                total_tor += req_on_tor
            tor_req[fab][ws] = total_tor
    return tor_req


def space_usage(mintech_space: Dict[int, float], tor_tools: Dict[int, Dict[str, int]]) -> Dict[int, float]:
    used = {fab: mintech_space[fab] for fab in [1, 2, 3]}
    for fab in [1, 2, 3]:
        for ws in MINTECH_WS:
            ws_t = WS_PAIRS[ws]
            used[fab] += tor_tools[fab].get(ws_t, 0) * WS_SPECS[ws_t]["space"]
    return used


def total_req_m_ws(q_idx: int) -> Dict[str, float]:
    total = {ws: 0.0 for ws in MINTECH_WS}
    for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
        load = TARGET_LOADING[node][q_idx]
        coef_m = rpt_m / (MINS_PER_WEEK * WS_SPECS[ws_m]["util"])
        total[ws_m] += load * coef_m
    return total


def build_flow_from_shares(
    q_idx: int,
    shares: Dict[str, Tuple[float, float, float]],
    flow: Dict[int, Dict[int, Dict[int, Dict[int, float]]]],
) -> None:
    for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
        load = TARGET_LOADING[node][q_idx]
        s1, s2, s3 = shares[ws_m]
        flow[q_idx][node][step][1] = load * s1
        flow[q_idx][node][step][2] = load * s2
        flow[q_idx][node][step][3] = load * s3


def solve_quarter(
    q_idx: int,
    flow: Dict[int, Dict[int, Dict[int, Dict[int, float]]]],
    mintech_tools: Dict[int, Dict[str, int]],
    mintech_space: Dict[int, float],
) -> Tuple[Dict[int, Dict[str, int]], float]:
    ws_list = MINTECH_WS
    totals = total_req_m_ws(q_idx)

    # initial guess: allocate by fab space, with fab3 capped by mintech capacity
    guess = []
    for ws in ws_list:
        if totals[ws] <= 0:
            guess.extend([0.5, 0.5])
            continue
        p3 = min(1.0, mintech_tools[3][ws] / totals[ws])
        rem = 1.0 - p3
        s1 = rem * (FAB_SPACE[1] / (FAB_SPACE[1] + FAB_SPACE[2]))
        s2 = rem - s1
        guess.extend([s1, s2])

    def shares_from_x(x):
        shares = {}
        for i, ws in enumerate(ws_list):
            s1 = float(x[2 * i])
            s2 = float(x[2 * i + 1])
            s3 = max(0.0, 1.0 - s1 - s2)
            shares[ws] = (s1, s2, s3)
        return shares

    def objective(x):
        shares = shares_from_x(x)
        build_flow_from_shares(q_idx, shares, flow)
        tor_req = tor_breakdown_for_quarter(q_idx, flow, mintech_tools)
        tor_tools = {fab: {WS_PAIRS[ws]: int(math.ceil(tor_req[fab][ws])) for ws in ws_list} for fab in [1, 2, 3]}
        used = space_usage(mintech_space, tor_tools)
        violation = sum(max(0.0, used[fab] - FAB_SPACE[fab]) for fab in [1, 2, 3])
        # penalty for invalid shares
        penalty = 0.0
        for ws in ws_list:
            s1, s2, s3 = shares[ws]
            if s3 < 0:
                penalty += abs(s3) * 1000.0
        return violation + penalty

    # constraints: s1+s2 <= 1 for each ws
    cons = []
    for i in range(len(ws_list)):
        cons.append({"type": "ineq", "fun": lambda x, i=i: 1.0 - x[2 * i] - x[2 * i + 1]})

    bounds = [(0.0, 1.0)] * (2 * len(ws_list))
    best_x = None
    best_violation = None

    def evaluate(x):
        shares = shares_from_x(x)
        build_flow_from_shares(q_idx, shares, flow)
        tor_req = tor_breakdown_for_quarter(q_idx, flow, mintech_tools)
        tor_tools = {fab: {WS_PAIRS[ws]: int(math.ceil(tor_req[fab][ws])) for ws in ws_list} for fab in [1, 2, 3]}
        used = space_usage(mintech_space, tor_tools)
        violation = sum(max(0.0, used[fab] - FAB_SPACE[fab]) for fab in [1, 2, 3])
        return tor_tools, violation

    # first run from heuristic guess
    res = minimize(objective, np.array(guess), method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 200})
    tor_tools, violation = evaluate(res.x)
    best_x, best_violation = res.x, violation

    # random restarts if needed
    if best_violation > 1e-6:
        rng = np.random.default_rng(42 + q_idx)
        for _ in range(8):
            x0 = rng.uniform(0.0, 1.0, size=(2 * len(ws_list),))
            res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 200})
            tor_tools, violation = evaluate(res.x)
            if violation < best_violation:
                best_x, best_violation = res.x, violation
            if best_violation <= 1e-6:
                break

    tor_tools, violation = evaluate(best_x)
    return tor_tools, violation


def build_flow_and_tools():
    flow = build_empty_flow()
    mintech_tools = base_mintech_tools()
    mintech_space = base_mintech_space(mintech_tools)

    tor_tools_by_q = {}
    infeasible = False
    for q_idx in range(8):
        tor_tools_by_q[q_idx], violation = solve_quarter(q_idx, flow, mintech_tools, mintech_space)
        if violation > 1e-6:
            infeasible = True

    # enforce no-move-out: tor tools must be non-decreasing by quarter
    tool_plan: Dict[int, Dict[int, Dict[str, int]]] = {}
    max_tor = {fab: {WS_PAIRS[ws]: 0 for ws in MINTECH_WS} for fab in [1, 2, 3]}
    for q_idx in range(8):
        tool_plan[q_idx] = {1: {}, 2: {}, 3: {}}
        for fab in [1, 2, 3]:
            for ws in MINTECH_WS:
                tool_plan[q_idx][fab][ws] = mintech_tools[fab][ws]
            for ws in MINTECH_WS:
                ws_t = WS_PAIRS[ws]
                max_tor[fab][ws_t] = max(max_tor[fab][ws_t], tor_tools_by_q[q_idx][fab][ws_t])
                tool_plan[q_idx][fab][ws_t] = max_tor[fab][ws_t]

    return flow, tool_plan, infeasible


def main() -> None:
    flow, tool_plan, infeasible = build_flow_and_tools()
    if infeasible:
        # write headers only to indicate infeasible plan for Q1a
        with open("output/02_q1a_flow.csv", "w", newline="") as f:
            f.write("quarter,node,step,fab,loading\n")
        with open("output/01_q1a_tooling.csv", "w", newline="") as f:
            f.write("quarter,ws,fab1,fab2,fab3\n")
        return
    write_flow_csv("output/02_q1a_flow.csv", flow)
    write_tooling_csv("output/01_q1a_tooling.csv", tool_plan)


if __name__ == "__main__":
    main()

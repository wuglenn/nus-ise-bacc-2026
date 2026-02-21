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


def node_ws_tor_coeff() -> Dict[Tuple[int, str], float]:
    coeff: Dict[Tuple[int, str], float] = {}
    for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
        coeff[(node, ws_m)] = coeff.get((node, ws_m), 0.0) + rpt_t / (MINS_PER_WEEK * WS_SPECS[ws_t]["util"])
    return coeff


def solve_node_shares(q_idx: int) -> Dict[int, Dict[int, float]]:
    """
    Solve for per-node fab shares so that:
      - each node's shares sum to 1
      - per-fab space (TOR tools) within limit
    Minimizes max fab space usage (proxy for cost / feasibility).
    """
    nodes = [1, 2, 3]
    fabs = [1, 2, 3]
    coeff = node_ws_tor_coeff()

    # variables: x_node_fab (share)
    idx = {}
    var_names = []
    for node in nodes:
        for fab in fabs:
            idx[(node, fab)] = len(var_names)
            var_names.append((node, fab))
    n_vars = len(var_names)

    # objective: minimize max slack (linearized with extra var)
    # add t variable for max usage
    t_idx = n_vars
    n_vars += 1

    c = np.zeros(n_vars)
    c[t_idx] = 1.0

    A_eq = []
    b_eq = []
    # sum_fab share = 1
    for node in nodes:
        row = np.zeros(n_vars)
        for fab in fabs:
            row[idx[(node, fab)]] = 1.0
        A_eq.append(row)
        b_eq.append(1.0)

    # space constraints per fab: total TOR space <= t and <= fab space
    A_ub = []
    b_ub = []
    for fab in fabs:
        row = np.zeros(n_vars)
        for ws in MINTECH_WS:
            for node in nodes:
                load = TARGET_LOADING[node][q_idx]
                row[idx[(node, fab)]] += load * coeff.get((node, ws), 0.0) * WS_SPECS[WS_PAIRS[ws]]["space"]
        row[t_idx] = -1.0
        A_ub.append(row)
        b_ub.append(0.0)

        row2 = np.zeros(n_vars)
        for ws in MINTECH_WS:
            for node in nodes:
                load = TARGET_LOADING[node][q_idx]
                row2[idx[(node, fab)]] += load * coeff.get((node, ws), 0.0) * WS_SPECS[WS_PAIRS[ws]]["space"]
        A_ub.append(row2)
        b_ub.append(FAB_SPACE[fab])

    bounds = [(0.0, 1.0)] * (n_vars - 1) + [(0.0, None)]
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=np.array(A_eq), b_eq=np.array(b_eq), bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"Node-share LP infeasible for {QUARTERS[q_idx]}: {res.message}")
    x = res.x
    shares = {node: {fab: x[idx[(node, fab)]] for fab in fabs} for node in nodes}
    return shares


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
        # use per-node constant shares to minimize transfers
        shares = solve_node_shares(q_idx)

        def build_flow_from_shares():
            for node, steps in [(1, range(1, 12)), (2, range(1, 16)), (3, range(1, 18))]:
                load = TARGET_LOADING[node][q_idx]
                for step in steps:
                    for fab in [1, 2, 3]:
                        flow[q_idx][node][step][fab] = load * shares[node][fab]

        def tor_req_from_flow():
            tor_local = {ws: {fab: 0.0 for fab in [1, 2, 3]} for ws in MINTECH_WS}
            for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
                coef_t = rpt_t / (MINS_PER_WEEK * WS_SPECS[ws_t]["util"])
                for fab in [1, 2, 3]:
                    load = flow[q_idx][node][step][fab]
                    tor_local[ws_m][fab] += load * coef_t
            return tor_local

        def space_used(tor_req_local):
            used = {fab: 0.0 for fab in [1, 2, 3]}
            for fab in [1, 2, 3]:
                for ws in MINTECH_WS:
                    used[fab] += math.ceil(tor_req_local[ws][fab]) * WS_SPECS[WS_PAIRS[ws]]["space"]
            return used

        # adjust shares to satisfy integer space
        for _ in range(300):
            build_flow_from_shares()
            tor_req = tor_req_from_flow()
            used = space_used(tor_req)
            over = [fab for fab in [1, 2, 3] if used[fab] > FAB_SPACE[fab] + 1e-6]
            if not over:
                break
            fab_from = max(over, key=lambda f: used[f] - FAB_SPACE[f])
            fab_to = min([f for f in [1, 2, 3] if f != fab_from], key=lambda f: used[f])
            for node in [1, 2, 3]:
                shift = min(0.05, shares[node][fab_from])
                shares[node][fab_from] -= shift
                shares[node][fab_to] += shift

        # targeted discrete adjustments (helps reduce integer space overage)
        build_flow_from_shares()
        tor_req = tor_req_from_flow()
        used = space_used(tor_req)
        for _ in range(200):
            over = [fab for fab in [1, 2, 3] if used[fab] > FAB_SPACE[fab] + 1e-6]
            if not over:
                break
            fab_from = max(over, key=lambda f: used[f] - FAB_SPACE[f])
            best = None
            # try shifting small deltas from fab_from to others
            for node in [1, 2, 3]:
                for fab_to in [1, 2, 3]:
                    if fab_to == fab_from:
                        continue
                    delta = min(0.01, shares[node][fab_from])
                    if delta <= 0:
                        continue
                    shares[node][fab_from] -= delta
                    shares[node][fab_to] += delta
                    build_flow_from_shares()
                    tor_req_try = tor_req_from_flow()
                    used_try = space_used(tor_req_try)
                    overage = sum(max(0.0, used_try[f] - FAB_SPACE[f]) for f in [1, 2, 3])
                    if best is None or overage < best[0]:
                        best = (overage, node, fab_to, used_try, tor_req_try)
                    # revert
                    shares[node][fab_from] += delta
                    shares[node][fab_to] -= delta
            if best is None:
                break
            _, node, fab_to, used, tor_req = best
            delta = min(0.01, shares[node][fab_from])
            shares[node][fab_from] -= delta
            shares[node][fab_to] += delta
            build_flow_from_shares()
            tor_req = tor_req_from_flow()
            used = space_used(tor_req)

        # final flow + tor_req
        build_flow_from_shares()
        tor_req = tor_req_from_flow()

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

"""
Global MILP for Q1b: jointly optimize flow + tooling to minimize
transfer cost + capex + moveout cost under space and mintech-first constraints.
"""

from __future__ import annotations

import math
import os
from typing import Dict, Tuple

import numpy as np
import scipy.sparse as sp
from scipy.optimize import Bounds, LinearConstraint, milp

try:
    from pyscipopt import SCIP_PARAMSETTING, Model, quicksum
except Exception:  # pragma: no cover - optional dependency
    Model = None
    quicksum = None
    SCIP_PARAMSETTING = None
from solver_utils import (
    FAB_SPACE,
    MINTECH_WS,
    NODE_STEPS,
    QUARTERS,
    TARGET_LOADING,
    WS_PAIRS,
    WS_SPECS,
    base_mintech_tools,
    build_empty_flow,
    write_flow_csv,
    write_tooling_csv,
)

MINS_PER_WEEK = 7 * 24 * 60
TRANSFER_COST_PER_WAFER = 50
WEEKS_PER_Q = 13
MOVEOUT_COST = 1_000_000


def _time_limit_seconds() -> int | None:
    val = os.getenv("Q1B_TIME_LIMIT")
    if val is None:
        return 600
    if val.strip().lower() in {"none", "inf", "infinite"}:
        return None
    return int(val)


TIME_LIMIT_SECONDS = _time_limit_seconds()


def _ws_steps():
    ws_steps = {ws: [] for ws in MINTECH_WS}
    for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
        a_m = rpt_m / (MINS_PER_WEEK * WS_SPECS[ws_m]["util"])
        a_t = rpt_t / (MINS_PER_WEEK * WS_SPECS[ws_t]["util"])
        r = a_t / a_m if a_m > 0 else 0.0
        ws_steps[ws_m].append((rank, node, step, a_m, a_t, r))
    for ws in MINTECH_WS:
        ws_steps[ws].sort(key=lambda x: (x[0], x[1], x[2]))
    return ws_steps


def _solve_with_highs(c, constraints, bounds, integrality):
    options = {"disp": True, "presolve": True}
    if TIME_LIMIT_SECONDS is not None:
        options["time_limit"] = TIME_LIMIT_SECONDS
    res = milp(
        c,
        constraints=constraints,
        bounds=bounds,
        integrality=integrality,
        options=options,
    )
    if not res.success:
        if res.x is None:
            raise RuntimeError(f"Global MILP failed: {res.message}")
        print(f"[warn] Global MILP not optimal: {res.message}")
    return res.x


def _solve_with_scip(c, A, lbs, ubs, bounds, integrality):
    if Model is None:
        raise RuntimeError("PySCIPOpt is not installed.")
    model = Model("q1b_global")
    model.setMinimize()
    model.setPresolve(SCIP_PARAMSETTING.AGGRESSIVE)
    if TIME_LIMIT_SECONDS is not None:
        model.setRealParam("limits/time", float(TIME_LIMIT_SECONDS))

    lb = bounds.lb
    ub = bounds.ub
    n_vars = len(c)
    vars_list = []
    inf = model.infinity()
    for i in range(n_vars):
        v_lb = lb[i]
        v_ub = ub[i]
        if v_ub >= 1e20 or v_ub == np.inf:
            v_ub = inf
        if integrality[i] == 1:
            v = model.addVar(lb=v_lb, ub=v_ub, vtype="I", name=f"x{i}")
        else:
            v = model.addVar(lb=v_lb, ub=v_ub, vtype="C", name=f"x{i}")
        vars_list.append(v)

    model.setObjective(quicksum(float(c[i]) * vars_list[i] for i in range(n_vars)))

    A_csr = A.tocsr()
    for i in range(A_csr.shape[0]):
        start = A_csr.indptr[i]
        end = A_csr.indptr[i + 1]
        if start == end:
            continue
        expr = quicksum(
            float(A_csr.data[k]) * vars_list[A_csr.indices[k]]
            for k in range(start, end)
        )
        lb_i = lbs[i]
        ub_i = ubs[i]
        if lb_i <= -1e20:
            lb_i = -inf
        if ub_i >= 1e20:
            ub_i = inf
        if lb_i <= -inf and ub_i >= inf:
            continue
        if lb_i <= -inf:
            model.addCons(expr <= ub_i)
        elif ub_i >= inf:
            model.addCons(expr >= lb_i)
        else:
            model.addCons(expr >= lb_i)
            model.addCons(expr <= ub_i)

    model.optimize()
    status = model.getStatus()
    if status not in {"optimal", "timelimit", "gaplimit", "bestsollimit"}:
        raise RuntimeError(f"SCIP failed: {status}")
    sol = model.getBestSol()
    if sol is None:
        raise RuntimeError(f"SCIP produced no solution: {status}")
    x = np.array([model.getSolVal(sol, v) for v in vars_list])
    return x


def build_flow_and_tools_global():
    nodes_steps = {1: 11, 2: 15, 3: 17}
    fabs = [1, 2, 3]
    ws_steps = _ws_steps()
    mintech_tools = base_mintech_tools()

    # Variable indices
    idx_load = {}
    idx_overlap = {}
    idx_m = {}
    idx_M = {}
    idx_T = {}
    idx_incM = {}
    idx_decM = {}
    idx_incT = {}
    idx_decT = {}
    idx_incT0 = {}

    var_idx = 0

    # flow variables
    for q_idx in range(8):
        for node, steps in nodes_steps.items():
            for step in range(1, steps + 1):
                for fab in fabs:
                    idx_load[(q_idx, node, step, fab)] = var_idx
                    var_idx += 1

    # overlap variables
    for q_idx in range(8):
        for node, steps in nodes_steps.items():
            for step in range(1, steps):
                for fab in fabs:
                    idx_overlap[(q_idx, node, step, fab)] = var_idx
                    var_idx += 1

    # mintech usage and rank binaries
    for q_idx in range(8):
        for fab in fabs:
            for ws in MINTECH_WS:
                for j in range(len(ws_steps[ws])):
                    idx_m[(q_idx, fab, ws, j)] = var_idx
                    var_idx += 1

    # tool counts
    for q_idx in range(8):
        for fab in fabs:
            for ws in MINTECH_WS:
                idx_M[(q_idx, fab, ws)] = var_idx
                var_idx += 1
                idx_T[(q_idx, fab, ws)] = var_idx
                var_idx += 1

    # inc/dec variables
    for q_idx in range(1, 8):
        for fab in fabs:
            for ws in MINTECH_WS:
                idx_incM[(q_idx, fab, ws)] = var_idx
                var_idx += 1
                idx_decM[(q_idx, fab, ws)] = var_idx
                var_idx += 1
                idx_incT[(q_idx, fab, ws)] = var_idx
                var_idx += 1
                idx_decT[(q_idx, fab, ws)] = var_idx
                var_idx += 1

    for fab in fabs:
        for ws in MINTECH_WS:
            idx_incT0[(fab, ws)] = var_idx
            var_idx += 1

    n_vars = var_idx

    # Bounds and integrality
    lb = np.zeros(n_vars)
    ub = np.full(n_vars, np.inf)
    integrality = np.zeros(n_vars, dtype=int)

    # flow bounds
    for (q_idx, node, step, fab), idx in idx_load.items():
        ub[idx] = TARGET_LOADING[node][q_idx]

    # overlap bounds
    for (q_idx, node, step, fab), idx in idx_overlap.items():
        ub[idx] = TARGET_LOADING[node][q_idx]

    # mintech usage and binaries
    for (q_idx, fab, ws, j), idx in idx_m.items():
        rank, node, step, a_m, a_t, r = ws_steps[ws][j]
        ub[idx] = a_m * TARGET_LOADING[node][q_idx]

    # tool counts
    for (q_idx, fab, ws), idx in idx_M.items():
        if q_idx == 0:
            ub[idx] = mintech_tools[fab][ws]
            lb[idx] = mintech_tools[fab][ws]
        else:
            # max mintech tools if all load assigned to one fab
            max_m = 0.0
            for rank, node, step, a_m, a_t, r in ws_steps[ws]:
                max_m += a_m * TARGET_LOADING[node][q_idx]
            ub[idx] = math.ceil(max_m)
        integrality[idx] = 1
    for (q_idx, fab, ws), idx in idx_T.items():
        max_t = 0.0
        for rank, node, step, a_m, a_t, r in ws_steps[ws]:
            max_t += a_t * TARGET_LOADING[node][q_idx]
        ub[idx] = math.ceil(max_t)
        integrality[idx] = 1

    bounds = Bounds(lb, ub)

    # Constraint builder
    rows = []
    cols = []
    data = []
    lbs = []
    ubs = []
    row_idx = 0

    def add_row(coeffs, lb_val, ub_val):
        nonlocal row_idx
        for idx, val in coeffs:
            rows.append(row_idx)
            cols.append(idx)
            data.append(val)
        lbs.append(lb_val)
        ubs.append(ub_val)
        row_idx += 1

    # Flow fulfillment
    for q_idx in range(8):
        for node, steps in nodes_steps.items():
            for step in range(1, steps + 1):
                coeffs = [(idx_load[(q_idx, node, step, fab)], 1.0) for fab in fabs]
                add_row(
                    coeffs, TARGET_LOADING[node][q_idx], TARGET_LOADING[node][q_idx]
                )

    # Overlap constraints
    for q_idx in range(8):
        for node, steps in nodes_steps.items():
            for step in range(1, steps):
                for fab in fabs:
                    z = idx_overlap[(q_idx, node, step, fab)]
                    l1 = idx_load[(q_idx, node, step, fab)]
                    l2 = idx_load[(q_idx, node, step + 1, fab)]
                    add_row([(z, 1.0), (l1, -1.0)], -np.inf, 0.0)
                    add_row([(z, 1.0), (l2, -1.0)], -np.inf, 0.0)

    # Mintech usage constraints and rank ordering
    for q_idx in range(8):
        for fab in fabs:
            for ws in MINTECH_WS:
                steps_list = ws_steps[ws]
                S = len(steps_list)

                for j, (rank, node, step, a_m, a_t, r) in enumerate(steps_list):
                    m_idx = idx_m[(q_idx, fab, ws, j)]
                    load_idx = idx_load[(q_idx, node, step, fab)]
                    # m <= a_m * load
                    add_row([(m_idx, 1.0), (load_idx, -a_m)], -np.inf, 0.0)

                # mintech capacity sum m <= M
                coeffs = [(idx_m[(q_idx, fab, ws, j)], 1.0) for j in range(S)]
                coeffs.append((idx_M[(q_idx, fab, ws)], -1.0))
                add_row(coeffs, -np.inf, 0.0)

                # tor requirement T >= sum(a_t*load) - sum(r*m)
                coeffs = [(idx_T[(q_idx, fab, ws)], 1.0)]
                for j, (rank, node, step, a_m, a_t, r) in enumerate(steps_list):
                    load_idx = idx_load[(q_idx, node, step, fab)]
                    m_idx = idx_m[(q_idx, fab, ws, j)]
                    coeffs.append((load_idx, -a_t))
                    coeffs.append((m_idx, r))
                add_row(coeffs, 0.0, np.inf)

    # Space constraints
    for q_idx in range(8):
        for fab in fabs:
            coeffs = []
            for ws in MINTECH_WS:
                coeffs.append((idx_M[(q_idx, fab, ws)], WS_SPECS[ws]["space"]))
                coeffs.append(
                    (idx_T[(q_idx, fab, ws)], WS_SPECS[WS_PAIRS[ws]]["space"])
                )
            add_row(coeffs, -np.inf, FAB_SPACE[fab])

    # inc/dec constraints
    for q_idx in range(1, 8):
        for fab in fabs:
            for ws in MINTECH_WS:
                M_curr = idx_M[(q_idx, fab, ws)]
                M_prev = idx_M[(q_idx - 1, fab, ws)]
                T_curr = idx_T[(q_idx, fab, ws)]
                T_prev = idx_T[(q_idx - 1, fab, ws)]

                incM = idx_incM[(q_idx, fab, ws)]
                decM = idx_decM[(q_idx, fab, ws)]
                incT = idx_incT[(q_idx, fab, ws)]
                decT = idx_decT[(q_idx, fab, ws)]

                # incM >= M_curr - M_prev
                add_row([(incM, 1.0), (M_curr, -1.0), (M_prev, 1.0)], 0.0, np.inf)
                # decM >= M_prev - M_curr
                add_row([(decM, 1.0), (M_curr, 1.0), (M_prev, -1.0)], 0.0, np.inf)
                # incT >= T_curr - T_prev
                add_row([(incT, 1.0), (T_curr, -1.0), (T_prev, 1.0)], 0.0, np.inf)
                # decT >= T_prev - T_curr
                add_row([(decT, 1.0), (T_curr, 1.0), (T_prev, -1.0)], 0.0, np.inf)

    # q0 tor purchases
    for fab in fabs:
        for ws in MINTECH_WS:
            incT0 = idx_incT0[(fab, ws)]
            T0 = idx_T[(0, fab, ws)]
            add_row([(incT0, 1.0), (T0, -1.0)], 0.0, np.inf)

    A = sp.csr_matrix((data, (rows, cols)), shape=(row_idx, n_vars))
    lb_arr = np.array(lbs)
    ub_arr = np.array(ubs)
    constraints = LinearConstraint(A, lb_arr, ub_arr)

    # Objective
    c = np.zeros(n_vars)
    transfer_coeff = -TRANSFER_COST_PER_WAFER * WEEKS_PER_Q
    for idx in idx_overlap.values():
        c[idx] = transfer_coeff

    for q_idx in range(1, 8):
        for fab in fabs:
            for ws in MINTECH_WS:
                c[idx_incM[(q_idx, fab, ws)]] = WS_SPECS[ws]["capex"]
                c[idx_decM[(q_idx, fab, ws)]] = MOVEOUT_COST
                c[idx_incT[(q_idx, fab, ws)]] = WS_SPECS[WS_PAIRS[ws]]["capex"]
                c[idx_decT[(q_idx, fab, ws)]] = MOVEOUT_COST
    for fab in fabs:
        for ws in MINTECH_WS:
            c[idx_incT0[(fab, ws)]] = WS_SPECS[WS_PAIRS[ws]]["capex"]

    solver = os.getenv("Q1B_SOLVER", "highs").lower()
    if solver == "scip":
        x = _solve_with_scip(c, A, lb_arr, ub_arr, bounds, integrality)
    else:
        x = _solve_with_highs(c, constraints, bounds, integrality)

    # Build flow output
    flow = build_empty_flow()
    for (q_idx, node, step, fab), idx in idx_load.items():
        flow[q_idx][node][step][fab] = float(x[idx])

    # Build tool plan output
    tool_plan: Dict[int, Dict[int, Dict[str, int]]] = {
        q: {1: {}, 2: {}, 3: {}} for q in range(8)
    }
    for q_idx in range(8):
        for fab in fabs:
            for ws in MINTECH_WS:
                tool_plan[q_idx][fab][ws] = int(round(x[idx_M[(q_idx, fab, ws)]]))
                tool_plan[q_idx][fab][WS_PAIRS[ws]] = int(
                    round(x[idx_T[(q_idx, fab, ws)]])
                )

    return flow, tool_plan


def main() -> None:
    flow, tool_plan = build_flow_and_tools_global()
    out_dir = os.getenv("Q1B_OUTPUT_DIR", "output")
    os.makedirs(out_dir, exist_ok=True)
    write_flow_csv(os.path.join(out_dir, "04_q1b_flow.csv"), flow)
    write_tooling_csv(os.path.join(out_dir, "03_q1b_tooling.csv"), tool_plan)


if __name__ == "__main__":
    main()

"""
Shared helpers for Q1/Q2 solvers.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

from verify_constraints import (
    FAB_SPACE,
    INITIAL_TOOLS,
    MINTECH_WS,
    NODE_STEPS,
    QUARTERS,
    TARGET_LOADING,
    TOR_WS,
    WS_PAIRS,
    WS_SPECS,
)

MINS_PER_WEEK = 7 * 24 * 60


Step = Tuple[int, int, str, float, str, float, int]


def step_tool_req(load_wpw: float, rpt_min: float, util: float) -> float:
    return (load_wpw * rpt_min) / (MINS_PER_WEEK * util)


def steps_by_ws() -> Dict[str, List[Step]]:
    by_ws: Dict[str, List[Step]] = {ws: [] for ws in MINTECH_WS}
    for row in NODE_STEPS:
        ws_m = row[2]
        by_ws[ws_m].append(row)
    for ws in MINTECH_WS:
        by_ws[ws].sort(key=lambda r: r[6])  # rank
    return by_ws


def ws_ratio_bounds() -> Dict[str, Dict[str, float]]:
    ratios: Dict[str, List[float]] = {ws: [] for ws in MINTECH_WS}
    for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
        r = (rpt_t / WS_SPECS[ws_t]["util"]) / (rpt_m / WS_SPECS[ws_m]["util"])
        ratios[ws_m].append(r)
    bounds: Dict[str, Dict[str, float]] = {}
    for ws in MINTECH_WS:
        bounds[ws] = {
            "min": min(ratios[ws]),
            "max": max(ratios[ws]),
            "avg": sum(ratios[ws]) / len(ratios[ws]),
        }
    return bounds


def base_mintech_tools() -> Dict[int, Dict[str, int]]:
    return {
        fab: {ws: INITIAL_TOOLS.get((fab, ws), 0) for ws in MINTECH_WS}
        for fab in [1, 2, 3]
    }


def base_mintech_space(mintech_tools: Dict[int, Dict[str, int]]) -> Dict[int, float]:
    return {
        fab: sum(mintech_tools[fab][ws] * WS_SPECS[ws]["space"] for ws in MINTECH_WS)
        for fab in [1, 2, 3]
    }


def tor_space_per_tool(ws_mintech: str) -> float:
    ws_tor = WS_PAIRS[ws_mintech]
    return WS_SPECS[ws_tor]["space"]


def tor_req_per_load(ws_mintech: str, rpt_tor: float) -> float:
    ws_tor = WS_PAIRS[ws_mintech]
    return rpt_tor / (MINS_PER_WEEK * WS_SPECS[ws_tor]["util"])


def mintech_req_per_load(ws_mintech: str, rpt_min: float) -> float:
    return rpt_min / (MINS_PER_WEEK * WS_SPECS[ws_mintech]["util"])


def simulate_tor_requirements(
    quarter_idx: int,
    flow: Dict[int, Dict[int, Dict[int, Dict[int, float]]]],
    mintech_tools: Dict[int, Dict[str, int]],
) -> Dict[int, Dict[str, float]]:
    """
    For each fab and mintech ws, compute TOR tool requirement under mintech-first rule.
    Returns tor_req[fab][ws_mintech] in tool units (may be fractional).
    """
    by_ws = steps_by_ws()
    tor_req: Dict[int, Dict[str, float]] = {
        fab: {ws: 0.0 for ws in MINTECH_WS} for fab in [1, 2, 3]
    }

    for fab in [1, 2, 3]:
        for ws in MINTECH_WS:
            avail_min = mintech_tools[fab][ws]
            cumulative = 0.0
            total_tor = 0.0
            for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in by_ws[ws]:
                load = (
                    flow.get(quarter_idx, {}).get(node, {}).get(step, {}).get(fab, 0.0)
                )
                if load <= 0:
                    continue
                req_m = step_tool_req(load, rpt_m, WS_SPECS[ws_m]["util"])
                req_t = step_tool_req(load, rpt_t, WS_SPECS[ws_t]["util"])
                cumulative += req_m
                overflow = max(0.0, cumulative - avail_min)
                if overflow <= 0:
                    req_on_tor = 0.0
                elif overflow >= req_m:
                    req_on_tor = req_t
                else:
                    req_on_tor = req_t * (overflow / req_m) if req_m > 0 else 0.0
                total_tor += req_on_tor
            tor_req[fab][ws] = total_tor
    return tor_req


def build_empty_flow() -> Dict[int, Dict[int, Dict[int, Dict[int, float]]]]:
    return defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    )


def write_flow_csv(
    path: str, flow: Dict[int, Dict[int, Dict[int, Dict[int, float]]]]
) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["quarter", "node", "step", "fab", "loading"])
        for q_idx, q in enumerate(QUARTERS):
            for node, steps in [
                (1, range(1, 12)),
                (2, range(1, 16)),
                (3, range(1, 18)),
            ]:
                for step in steps:
                    for fab in [1, 2, 3]:
                        val = (
                            flow.get(q_idx, {})
                            .get(node, {})
                            .get(step, {})
                            .get(fab, 0.0)
                        )
                        w.writerow([q, node, step, fab, f"{val:.12f}"])


def write_tooling_csv(
    path: str,
    tool_plan: Dict[int, Dict[int, Dict[str, int]]],
) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["quarter", "ws", "fab1", "fab2", "fab3"])
        for q_idx, q in enumerate(QUARTERS):
            for ws in MINTECH_WS + TOR_WS:
                w.writerow(
                    [
                        q,
                        ws,
                        tool_plan.get(q_idx, {}).get(1, {}).get(ws, 0),
                        tool_plan.get(q_idx, {}).get(2, {}).get(ws, 0),
                        tool_plan.get(q_idx, {}).get(3, {}).get(ws, 0),
                    ]
                )


def write_q2_csv(path: str, rows: List[Dict[str, float]]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["quarter", "expected_loading", "combined_variance", "prob_undercap_scen1"]
        )
        for row in rows:
            w.writerow(
                [
                    row["quarter"],
                    f"{row['expected_loading']:.6f}",
                    f"{row['combined_variance']:.6f}",
                    f"{row['prob_undercap_scen1']:.6f}",
                ]
            )

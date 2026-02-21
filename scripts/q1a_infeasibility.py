"""
Compute Q1a space lower bounds and max production scale (k) per quarter.
"""

from __future__ import annotations

from typing import Dict

from solver_utils import (
    QUARTERS,
    NODE_STEPS,
    WS_SPECS,
    MINTECH_WS,
    WS_PAIRS,
    TARGET_LOADING,
    base_mintech_tools,
    base_mintech_space,
)

MINS_PER_WEEK = 7 * 24 * 60
TOTAL_SPACE = 1500 + 1300 + 700


def min_ratio_by_ws() -> Dict[str, float]:
    ratio_min = {ws: 1e9 for ws in MINTECH_WS}
    for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
        ratio = (rpt_t / WS_SPECS[ws_t]["util"]) / (rpt_m / WS_SPECS[ws_m]["util"])
        if ratio < ratio_min[ws_m]:
            ratio_min[ws_m] = ratio
    return ratio_min


def lb_total_space(q_idx: int, k: float, ratio_min: Dict[str, float], mintech_space: float) -> float:
    req_m = {ws: 0.0 for ws in MINTECH_WS}
    for node, step, ws_m, rpt_m, ws_t, rpt_t, rank in NODE_STEPS:
        load = TARGET_LOADING[node][q_idx] * k
        req_m[ws_m] += load * rpt_m / (MINS_PER_WEEK * WS_SPECS[ws_m]["util"])

    avail = {ws: 0.0 for ws in MINTECH_WS}
    mintech_tools = base_mintech_tools()
    for ws in MINTECH_WS:
        avail[ws] = sum(mintech_tools[f][ws] for f in [1, 2, 3])

    overflow = {ws: max(0.0, req_m[ws] - avail[ws]) for ws in MINTECH_WS}
    lb_tor_tools = {ws: overflow[ws] * ratio_min[ws] for ws in MINTECH_WS}
    lb_tor_space = sum(lb_tor_tools[ws] * WS_SPECS[WS_PAIRS[ws]]["space"] for ws in MINTECH_WS)
    return mintech_space + lb_tor_space


def max_k_for_quarter(q_idx: int, ratio_min: Dict[str, float], mintech_space: float) -> float:
    lo, hi = 0.0, 2.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if lb_total_space(q_idx, mid, ratio_min, mintech_space) <= TOTAL_SPACE:
            lo = mid
        else:
            hi = mid
    return lo


def main() -> None:
    ratio_min = min_ratio_by_ws()
    mintech_space = sum(base_mintech_space(base_mintech_tools()).values())
    print(f"Total fab space: {TOTAL_SPACE:.2f} m^2")
    print(f"Fixed mintech space: {mintech_space:.2f} m^2")
    for q_idx, q in enumerate(QUARTERS):
        lb = lb_total_space(q_idx, 1.0, ratio_min, mintech_space)
        kmax = max_k_for_quarter(q_idx, ratio_min, mintech_space)
        print(f"{q}: LB space @k=1 -> {lb:.2f} m^2, k_max~{kmax:.3f}")


if __name__ == "__main__":
    main()

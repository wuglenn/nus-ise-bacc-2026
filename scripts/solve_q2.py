"""
Generate Q2 analytic outputs into output/05_q2_node*.csv
"""

from __future__ import annotations

import math
from typing import List, Dict

from solver_utils import QUARTERS, write_q2_csv
from test_constraints import SCENARIOS, PROBS


def expected_loading(node: int, q_idx: int) -> float:
    return sum(PROBS[i] * SCENARIOS[node][i][q_idx] for i in range(3))


def combined_variance(node: int, q_idx: int) -> float:
    el = expected_loading(node, q_idx)
    el2 = sum(
        PROBS[i] * (SCENARIOS[node][i][q_idx] ** 2 + (0.10 * SCENARIOS[node][i][q_idx]) ** 2)
        for i in range(3)
    )
    return el2 - el ** 2


def prob_undercap_scen1(node: int, q_idx: int) -> float:
    mu1 = SCENARIOS[node][0][q_idx]
    mu2 = SCENARIOS[node][1][q_idx]
    sigma = 0.10 * mu1
    if sigma == 0:
        return 0.0 if mu2 >= mu1 else 1.0
    z = (mu2 - mu1) / sigma
    return 1.0 - (0.5 * math.erfc(-z / math.sqrt(2)))


def build_rows(node: int) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for q_idx, q in enumerate(QUARTERS):
        rows.append(
            {
                "quarter": q,
                "expected_loading": expected_loading(node, q_idx),
                "combined_variance": combined_variance(node, q_idx),
                "prob_undercap_scen1": prob_undercap_scen1(node, q_idx),
            }
        )
    return rows


def main() -> None:
    write_q2_csv("output/05_q2_node1.csv", build_rows(1))
    write_q2_csv("output/06_q2_node2.csv", build_rows(2))
    write_q2_csv("output/07_q2_node3.csv", build_rows(3))


if __name__ == "__main__":
    main()

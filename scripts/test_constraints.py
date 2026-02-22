"""
test_constraints.py
===================
Pytest suite that reads solution CSVs from output/ and verifies all constraints.

Output files and their columns
-------------------------------
01_q1a_tooling.csv  quarter, ws, fab1, fab2, fab3
02_q1a_flow.csv     quarter, node, step, fab, loading
03_q1b_tooling.csv  quarter, ws, fab1, fab2, fab3
04_q1b_flow.csv     quarter, node, step, fab, loading
05_q2_node1.csv     quarter, expected_loading, combined_variance, prob_undercap_scen1
06_q2_node2.csv     quarter, expected_loading, combined_variance, prob_undercap_scen1
07_q2_node3.csv     quarter, expected_loading, combined_variance, prob_undercap_scen1

  quarter              "Q1'26" .. "Q4'27"
  ws                   'A'..'F' (mintech) or 'A+'..'F+' (TOR)
  fab1 / fab2 / fab3   integer tool counts
  loading              wafers/week assigned to this fab for (quarter, node, step)
  expected_loading     E[L] per quarter — Q2a(i)
  combined_variance    Var[L] per quarter — Q2a(ii)
  prob_undercap_scen1  P(demand > Scen-2 capacity | Scen-1 realized) — Q2a(iii)

Run:
  pytest scripts/test_constraints.py -v
  pytest scripts/test_constraints.py -v -k q1a
  pytest scripts/test_constraints.py -v -k q2
"""

import csv
import math
import os
import sys
from collections import defaultdict

import pytest

# ── paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")

# ── import constraint helpers from verify_constraints.py ─────────────────────

sys.path.insert(0, SCRIPT_DIR)
from verify_constraints import (
    INITIAL_TOOLS,
    MINTECH_WS,
    QUARTERS,
    check_loading_fulfillment,
    check_space,
    check_tool_capacity,
)

# ── Q2 scenario data (from question) ─────────────────────────────────────────
# SCENARIOS[node][scenario_idx] = list of 8 means, one per quarter
SCENARIOS = {
    1: [
        [12000, 13000, 13000, 11000, 9000, 6000, 6000, 4000],  # Scen 1, p=0.30
        [12000, 10000, 8500, 7500, 6000, 5000, 4000, 2000],  # Scen 2, p=0.50
        [12000, 10000, 7000, 4000, 2000, 1000, 0, 0],  # Scen 3, p=0.20
    ],
    2: [
        [5000, 5500, 6000, 6500, 7000, 8000, 9000, 9000],
        [5000, 5200, 5400, 5600, 6000, 6500, 7000, 7500],
        [5000, 5000, 5000, 4000, 3000, 3000, 2000, 2000],
    ],
    3: [
        [3000, 4500, 8000, 11000, 14000, 17000, 20000, 23000],
        [3000, 4500, 7000, 8000, 9000, 11000, 13000, 16000],
        [3000, 3500, 4500, 5500, 7000, 8500, 10000, 10000],
    ],
}
PROBS = [0.30, 0.50, 0.20]
Q2_TOLERANCE = 1e-3  # absolute tolerance for Q2 numeric checks

# ── helpers: expected loading and variance ────────────────────────────────────


def expected_loading(node: int, q_idx: int) -> float:
    """E[L] = sum_i p_i * mu_i  (Q2a-i)"""
    return sum(PROBS[i] * SCENARIOS[node][i][q_idx] for i in range(3))


def combined_variance(node: int, q_idx: int) -> float:
    """
    Var[L] = E[L^2] - E[L]^2
           = sum_i p_i*(mu_i^2 + sigma_i^2) - E[L]^2
    where sigma_i = 0.10 * mu_i  (Q2a-ii)
    """
    el = expected_loading(node, q_idx)
    el2 = sum(
        PROBS[i]
        * (SCENARIOS[node][i][q_idx] ** 2 + (0.10 * SCENARIOS[node][i][q_idx]) ** 2)
        for i in range(3)
    )
    return el2 - el**2


def prob_undercap_scen1(node: int, q_idx: int) -> float:
    """
    P(demand > capacity | Scen 1 realized)
    Capacity = mu_scen2 (Scenario 2 mean loading).
    Under Scen 1: L ~ N(mu_scen1, (0.10*mu_scen1)^2)
    P(L > mu_scen2) = 1 - Phi((mu_scen2 - mu_scen1) / (0.10*mu_scen1))  (Q2a-iii)
    """
    mu1 = SCENARIOS[node][0][q_idx]  # Scen 1 mean
    mu2 = SCENARIOS[node][1][q_idx]  # Scen 2 mean (= planned capacity)
    sigma = 0.10 * mu1
    if sigma == 0:
        return 0.0 if mu2 >= mu1 else 1.0
    z = (mu2 - mu1) / sigma
    return 1.0 - _std_normal_cdf(z)


def _std_normal_cdf(z: float) -> float:
    """Standard normal CDF via math.erfc (no scipy needed)."""
    return 0.5 * math.erfc(-z / math.sqrt(2))


# ── CSV loaders ───────────────────────────────────────────────────────────────


def _skip_if_missing(path: str):
    if not os.path.exists(path):
        pytest.skip(f"File not found: {path}")
    if os.path.getsize(path) == 0:
        pytest.skip(f"File is empty (no data yet): {path}")


def _has_data_rows(path: str) -> bool:
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        return next(reader, None) is not None


def load_flow(path: str) -> dict:
    """flow[q_idx][node][step][fab] = loading (wafers/week)"""
    q_index = {q: i for i, q in enumerate(QUARTERS)}
    flow = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    )
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            flow[q_index[row["quarter"]]][int(row["node"])][int(row["step"])][
                int(row["fab"])
            ] = float(row["loading"])
    return flow


def load_tooling(path: str) -> dict:
    """tool_plan[q_idx][fab][ws] = count; Q1'26 mintech auto-seeded from INITIAL_TOOLS."""
    q_index = {q: i for i, q in enumerate(QUARTERS)}
    plan = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            q_idx = q_index[row["quarter"]]
            ws = row["ws"]
            for fab, col in [(1, "fab1"), (2, "fab2"), (3, "fab3")]:
                plan[q_idx][fab][ws] = int(float(row[col]))
    # Back-fill Q1'26 mintech with initial counts if user left them as 0
    for (fab, ws), count in INITIAL_TOOLS.items():
        if plan[0][fab][ws] == 0 and ws in MINTECH_WS:
            plan[0][fab][ws] = count
    return plan


def load_q2(path: str) -> list[dict]:
    """Returns list of dicts keyed by quarter with expected_loading, combined_variance, prob_undercap_scen1."""
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "quarter": row["quarter"],
                    "expected_loading": float(row["expected_loading"]),
                    "combined_variance": float(row["combined_variance"]),
                    "prob_undercap_scen1": float(row["prob_undercap_scen1"]),
                }
            )
    return rows


# ── shared fixture factory ────────────────────────────────────────────────────


def _q1_solution(tooling_file: str, flow_file: str):
    tp = os.path.join(OUTPUT_DIR, tooling_file)
    fp = os.path.join(OUTPUT_DIR, flow_file)
    for p in (tp, fp):
        if not os.path.exists(p):
            pytest.skip(f"Missing {p}")
    if not _has_data_rows(tp) or not _has_data_rows(fp):
        pytest.skip("CSVs have no data rows yet — fill in your solution first")
    return load_flow(fp), load_tooling(tp)


# ═════════════════════════════════════════════════════════════════════════════
# Q1a
# ═════════════════════════════════════════════════════════════════════════════


class TestQ1a:
    """01_q1a_tooling.csv + 02_q1a_flow.csv"""

    @pytest.fixture(scope="class")
    def solution(self):
        return _q1_solution("01_q1a_tooling.csv", "02_q1a_flow.csv")

    def test_loading_fulfillment(self, solution):
        """V8: each (quarter, node, step) sums to the target loading across fabs."""
        flow, _ = solution
        ok, violations = check_loading_fulfillment(flow)
        assert ok, "Loading fulfillment failed:\n" + "\n".join(violations)

    def test_space_limits(self, solution):
        """K7: tool footprint stays within each fab's space limit every quarter."""
        _, plan = solution
        ok, violations = check_space(plan)
        assert ok, "Space constraint violated:\n" + "\n".join(violations)

    def test_tool_capacity(self, solution):
        """AP3: mintech-first rank allocation — required tools <= available every quarter."""
        flow, plan = solution
        ok, violations = check_tool_capacity(plan, flow)
        assert ok, "Tool capacity violated:\n" + "\n".join(violations)

    def test_master_gate(self, solution):
        """B4 = AND(K7, V8, AP3)."""
        flow, plan = solution
        results = [
            check_loading_fulfillment(flow)[0],
            check_space(plan)[0],
            check_tool_capacity(plan, flow)[0],
        ]
        assert all(results), "B4 is FALSE — run individual tests above for details"


# ═════════════════════════════════════════════════════════════════════════════
# Q1b  —  move-outs and new purchases allowed  (user calls this "q1b")
# ═════════════════════════════════════════════════════════════════════════════


class TestQ1b:
    """03_q1b_tooling.csv + 04_q1b_flow.csv  |  Part b: move-outs + new purchases."""

    @pytest.fixture(scope="class")
    def solution(self):
        return _q1_solution("03_q1b_tooling.csv", "04_q1b_flow.csv")

    def test_loading_fulfillment(self, solution):
        """V8: each (quarter, node, step) sums to the target loading across fabs."""
        flow, _ = solution
        ok, violations = check_loading_fulfillment(flow)
        assert ok, "Loading fulfillment failed:\n" + "\n".join(violations)

    def test_space_limits(self, solution):
        """K7: tool footprint stays within each fab's space limit every quarter."""
        _, plan = solution
        ok, violations = check_space(plan)
        assert ok, "Space constraint violated:\n" + "\n".join(violations)

    def test_tool_capacity(self, solution):
        """AP3: mintech-first rank allocation — required tools <= available every quarter."""
        flow, plan = solution
        ok, violations = check_tool_capacity(plan, flow)
        assert ok, "Tool capacity violated:\n" + "\n".join(violations)

    def test_master_gate(self, solution):
        """B4 = AND(K7, V8, AP3)."""
        flow, plan = solution
        results = [
            check_loading_fulfillment(flow)[0],
            check_space(plan)[0],
            check_tool_capacity(plan, flow)[0],
        ]
        assert all(results), "B4 is FALSE — run individual tests above for details"


# ═════════════════════════════════════════════════════════════════════════════
# Q2  —  stochastic scenario analysis (one test class per node)
# ═════════════════════════════════════════════════════════════════════════════


class _Q2Base:
    """
    Base class for Q2 node tests.
    Subclasses set: csv_file (str), node (int).
    Tests verify the submitted expected_loading, combined_variance, and
    prob_undercap_scen1 against analytically computed reference values.
    """

    csv_file: str
    node: int

    @pytest.fixture(scope="class")
    def submitted(self):
        path = os.path.join(OUTPUT_DIR, self.csv_file)
        if not os.path.exists(path):
            pytest.skip(f"Missing {path}")
        if not _has_data_rows(path):
            pytest.skip("CSV has no data rows yet — fill in your Q2 answers first")
        rows = load_q2(path)
        assert len(rows) == 8, f"Expected 8 rows (one per quarter), got {len(rows)}"
        assert [r["quarter"] for r in rows] == QUARTERS, (
            "Quarter order/values incorrect"
        )
        return rows

    def test_expected_loading(self, submitted):
        """Q2a(i): E[L] = sum_i p_i * mu_i for each quarter."""
        errors = []
        for q_idx, row in enumerate(submitted):
            ref = expected_loading(self.node, q_idx)
            got = row["expected_loading"]
            if abs(got - ref) > Q2_TOLERANCE:
                errors.append(f"  {QUARTERS[q_idx]}: got {got:.4f}, expected {ref:.4f}")
        assert not errors, f"Node {self.node} expected_loading mismatch:\n" + "\n".join(
            errors
        )

    def test_combined_variance(self, submitted):
        """Q2a(ii): Var[L] = sum_i p_i*(mu_i^2+sigma_i^2) - E[L]^2 where sigma_i=0.1*mu_i."""
        errors = []
        for q_idx, row in enumerate(submitted):
            ref = combined_variance(self.node, q_idx)
            got = row["combined_variance"]
            if abs(got - ref) > Q2_TOLERANCE:
                errors.append(f"  {QUARTERS[q_idx]}: got {got:.2f}, expected {ref:.2f}")
        assert not errors, (
            f"Node {self.node} combined_variance mismatch:\n" + "\n".join(errors)
        )

    def test_prob_undercap_scen1(self, submitted):
        """Q2a(iii): P(demand > Scen-2 capacity | Scen-1 realized) per quarter."""
        errors = []
        for q_idx, row in enumerate(submitted):
            ref = prob_undercap_scen1(self.node, q_idx)
            got = row["prob_undercap_scen1"]
            if abs(got - ref) > Q2_TOLERANCE:
                errors.append(f"  {QUARTERS[q_idx]}: got {got:.6f}, expected {ref:.6f}")
        assert not errors, (
            f"Node {self.node} prob_undercap_scen1 mismatch:\n" + "\n".join(errors)
        )


class TestQ2Node1(_Q2Base):
    """05_q2_node1.csv — Q2 stochastic answers for Node 1."""

    csv_file = "05_q2_node1.csv"
    node = 1


class TestQ2Node2(_Q2Base):
    """06_q2_node2.csv — Q2 stochastic answers for Node 2."""

    csv_file = "06_q2_node2.csv"
    node = 2


class TestQ2Node3(_Q2Base):
    """07_q2_node3.csv — Q2 stochastic answers for Node 3."""

    csv_file = "07_q2_node3.csv"
    node = 3

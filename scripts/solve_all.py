"""
Run all solvers and write cost summary.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from compute_cost import summarize
from solve_q1a import main as solve_q1a
from solve_q1b import main as solve_q1b
from solve_q2 import main as solve_q2


def main() -> None:
    solve_q2()
    solve_q1b()
    solve_q1a()

    q1a = summarize("output/02_q1a_flow.csv", "output/01_q1a_tooling.csv")
    q1b = summarize("output/04_q2a_flow.csv", "output/03_q2a_tooling.csv")

    out = Path("solution")
    out.mkdir(parents=True, exist_ok=True)
    summary_path = out / "cost_summary.md"
    with summary_path.open("w") as f:
        f.write("# Cost Summary (Approximate)\n\n")
        f.write("Transfer cost is a lower-bound based on step-to-step overlap.\n")
        f.write("Move-out cost uses quarter-to-quarter tool count deltas only.\n\n")
        f.write("## Q1a\n\n")
        f.write(json.dumps(q1a, indent=2))
        f.write("\n\n## Q1b\n\n")
        f.write(json.dumps(q1b, indent=2))
        f.write("\n")


if __name__ == "__main__":
    main()

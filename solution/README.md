# Solution Notes

This workspace contains generated CSVs in `output/` plus helper scripts in `scripts/`.

## How to run

```bash
python scripts/solve_all.py
pytest scripts/test_constraints.py -v
```

## Q1a infeasibility (original Table 1 loading)

With **no move-outs** and **fixed mintech tools**, Q1a becomes space-infeasible in later quarters.
Using a lower-bound calculation for Q4'27:

- Total mintech space used: ~2868.63 m²
- Best-case additional TOR space (optimistic): ~1213.65 m²
- Total lower-bound space: ~4082.28 m² > 3500 m² available
- Full derivation and per-quarter lower bounds: `solution/q1a_infeasibility.md`

### Q1a constraints (from question paper PDF)

1. All loading requirements must be met (no missing steps).
2. Fab space limits cannot be exceeded.
3. No tool move-outs (existing tools remain).
4. Cost minimization is expected while satisfying constraints.

These appear verbatim under "Constraints and Assumptions to be satisfied" in
`materials/3) 2026 NUS BACC - Question Paper.pdf` (PDF page 13).

## Reduced loading beyond Q1'27 (submission only)

The official tests in `scripts/test_constraints.py` validate the original Table 1
loadings in `scripts/verify_constraints.py TARGET_LOADING`.

If you generate a reduced-demand Q1a plan (to regain feasibility under space/no-moveout),
`scripts/solve_q1a.py` applies `K_AFTER_Q1_27 = 0.62` internally for Q2'27..Q4'27 and
writes to `output/`. This will intentionally cause the Q1a loading-fulfillment test to fail,
even if space/capacity/no-moveout constraints are satisfied.

### Q1b requirements (from prompt)

- Meet all loading requirements.
- Operate within existing fab space constraints.
- Minimize total cost (transfers + move-outs + new tool purchases).

## Cost summary

Approximate cost rollup is written to `solution/cost_summary.md`.

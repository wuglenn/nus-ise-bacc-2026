# Solution Notes

This workspace contains generated CSVs in `output/` plus helper scripts in `scripts/`.

## How to run

```bash
python scripts/solve_all.py
pytest scripts/test_constraints.py -v
```

## Q1a infeasibility

With **no move-outs** and **fixed mintech tools**, Q1a becomes space-infeasible in later quarters.
Using a lower-bound calculation for Q4'27:

- Total mintech space used: ~2868.63 m²
- Best-case additional TOR space (optimistic): ~1213.65 m²
- Total lower-bound space: ~4082.28 m² > 3500 m² available
- Full derivation and per-quarter lower bounds: `solution/q1a_infeasibility.md`

### Q1a constraints (from prompt)

1. All loading requirements must be met (no missing steps).
2. Fab space limits cannot be exceeded.
3. No tool move-outs (existing tools remain).
4. Cost minimization is expected while satisfying constraints.

### Q1b requirements (from prompt)

- Meet all loading requirements.
- Operate within existing fab space constraints.
- Minimize total cost (transfers + move-outs + new tool purchases).

### Q1b global MILP

`scripts/solve_q1b_global.py` solves a full MILP over flow + tools using HiGHS
via `scipy.optimize.milp`. It uses a time limit (`TIME_LIMIT_SECONDS`) and will
emit a feasible solution if the time limit is reached before proven optimality.
Increase the time limit for a tighter optimality gap.

## Cost summary

Approximate cost rollup is written to `solution/cost_summary.md`.

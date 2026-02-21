# Q1a Infeasibility Under Original Table 1 Loading

This note is about the *original* deterministic Table 1 loading values (now preserved as
`scripts/verify_constraints.py TARGET_LOADING_BASE`).

`scripts/q1a_infeasibility.py` computes a **total-space lower bound** on feasibility:
it assumes all existing Mintech tools are fully utilized first, then any overflow is
covered by the most space-efficient TOR substitution per workstation. If this lower
bound exceeds total available fab space, Q1a is infeasible even before considering
per-fab space limits.

- Total fab space: 3500.00 m^2
- Fixed Mintech space (initial tools): 2868.63 m^2

## Lower-Bound Proof (Total Space)

| Quarter | LB total space @k=1 (m^2) | Slack vs total (m^2) | k_max |
|---|---:|---:|---:|
| Q1'26 | 2868.63 | 631.37 | 1.345 |
| Q2'26 | 2978.35 | 521.65 | 1.335 |
| Q3'26 | 3188.69 | 311.31 | 1.179 |
| Q4'26 | 3275.66 | 224.34 | 1.129 |
| Q1'27 | 3365.80 | 134.20 | 1.090 |
| Q2'27 | 3572.76 | -72.76 | 0.959 |
| Q3'27 | 3788.45 | -288.45 | 0.838 |
| Q4'27 | 4082.28 | -582.28 | 0.709 |


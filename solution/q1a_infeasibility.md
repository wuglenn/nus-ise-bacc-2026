# Q1a Infeasibility Proof (Space Lower Bound)

This establishes that Q1a becomes infeasible in later quarters because the minimum required tool footprint exceeds total fab space even under optimistic assumptions.

## Given

- Total fab space = `1500 + 1300 + 700 = 3500 m²`
- Fixed mintech tools (Q1a “no move-outs”): total mintech footprint = **2868.63 m²**
- Remaining space for any TOR tools = **631.37 m²**

## Lower bound on TOR space

For each workstation `ws` and quarter:

1. Compute total mintech tool requirement across all nodes/steps:
   `Req_m(ws) = Σ load × RPT_m / (10080 × util_m)`
2. Compute mintech availability across all fabs:
   `Avail_m(ws) = Σ initial_tools(ws)`
3. Overflow (must be served by TOR):
   `Overflow_m(ws) = max(0, Req_m(ws) − Avail_m(ws))`
4. Convert overflow to **minimum** TOR tools using the best (smallest) TOR/mintech ratio across steps for that ws:
   `Min_TOR(ws) = Overflow_m(ws) × min_steps (RPT_t/util_t) / (RPT_m/util_m)`
5. Lower-bound TOR space:
   `LB_TOR_space = Σ Min_TOR(ws) × space_tor(ws)`

This is an optimistic bound because it assumes:
- best-case TOR/mintech ratio for every overflowed ws,
- perfect allocation across fabs,
- no integer rounding overhead.

## Results (lower bounds)

| Quarter | LB TOR Space (m²) | Total Space LB (m²) |
|---|---:|---:|
| Q1'26 | 0.00 | 2868.63 |
| Q2'26 | 109.72 | 2978.35 |
| Q3'26 | 320.06 | 3188.69 |
| Q4'26 | 407.03 | 3275.66 |
| Q1'27 | 497.17 | 3365.80 |
| Q2'27 | 704.13 | **3572.76** |
| Q3'27 | 919.82 | **3788.45** |
| Q4'27 | 1213.65 | **4082.28** |

From **Q2'27 onward**, even the optimistic lower bound exceeds total fab space (`3500 m²`), so Q1a is **infeasible**.

## Max production (upper bound on feasible scaling)

Let `k` scale all quarterly loadings (`k=1` is the original plan). Using the same optimistic lower-bound model, we can compute the **maximum feasible k** per quarter such that:

`Fixed mintech space + LB_TOR_space(k) ≤ 3500 m²`.

This gives an **upper bound** on feasible production (real solutions must be ≤ this k).

| Quarter | k_max (upper bound) |
|---|---:|
| Q1'26 | 1.345 |
| Q2'26 | 1.335 |
| Q3'26 | 1.179 |
| Q4'26 | 1.129 |
| Q1'27 | 1.090 |
| Q2'27 | 0.959 |
| Q3'27 | 0.838 |
| Q4'27 | 0.709 |

Therefore, for Q2'27 and later, even the **best-case** feasible production is **below 100%**, proving infeasibility at `k=1`.

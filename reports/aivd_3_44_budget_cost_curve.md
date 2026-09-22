# AIVD 3.44 — Budget Cost Curve

**Recorded:** 2026-09-22 13:20:03 IST  
**Sacred:** NO  

## Headline

Slot-count proxy: each +1 n_mat adds +1 first-window invent attempt from recorded board0; ledger invent unit-cost is NOT_RECORDED (delta=0 on 196/196 invents); full CF budget trajectory NOT_RECORDED.

## Observed (n_mat=1)

| Field | Value |
|-------|-------|
| BH / INVENT_CAP | 48 / 48 |
| Invent attempts/cell | 7 |
| Invent budget_before series (exemplar) | [29, 28, 27, 26, 25, 24, 21] |
| Invent ledger deltas | {0: 196} |
| Twin budget_series (exemplar) | [10, 1, 1, 0] |
| Stop | BUDGET_EXHAUSTED |

## Counterfactual proxy curve

| n_mat | +slots vs 1 | Proxy extra FW invents | Ledger unit cost | CF remaining | Mode |
|------:|------------:|-----------------------:|------------------|--------------|------|
| 1 | 0 | 0 | NOT_RECORDED | NOT_RECORDED | OBSERVED |
| 2 | 1 | 1 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |
| 3 | 2 | 2 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |
| 4 | 3 | 3 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |
| 5 | 4 | 4 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |
| 6 | 5 | 5 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |
| 7 | 6 | 6 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |
| 8 | 7 | 7 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |
| 9 | 8 | 8 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |
| 10 | 9 | 9 | NOT_RECORDED | NOT_RECORDED | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW |

## Interpretation

- **Measurable offline:** marginal first-window invent *slots* scale with n_mat.
- **NOT_RECORDED:** true invent unit cost, CF total attempts after divergence, CF remaining budget, whether wider n_mat exhausts earlier or enables earlier verification.

See `reports/aivd_3_44_budget_cost_curve.json`.

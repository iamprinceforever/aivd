# AIVD 3.44 — Results (Executive Wrap-Up)

**Recorded:** 2026-09-22 13:20:03 IST  
**Baseline tip:** `9810aea5efe14fe4b8786eedc94a7710ecdbbe0e`  
**Branch:** `research/aivd-3.44-exploration-allocation`  
**Parent:** `research/aivd-3.43-selection-budget-generalization` @ 9810aea  
**Sacred:** NO  
**Planner changed:** NO  
**Live n_mat changed:** NO  

## H13

| Leaf | Classification |
|------|----------------|
| H13a | **SUPPORTED** |
| H13b | **SUPPORTED** |
| H13c | **PARTIAL** |
| H13d | **SUPPORTED** |
| H13e | **PARTIAL** |
| H13f | **AGAINST** |
| H13-REJECT | **AGAINST** |

## Headlines

- **First-window skip:** First-window skip rate: 9/9 pos>0 keys × 28/28 cells = 252/252 (100% of pos>0; 90% of board0 slots).
- **Persistent suppression:** Persistent suppression: 3/9 pos>0 keys (33%) — ['MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))']; among scored/ranked skipped keys 3/7 (43%).
- **CF n_mat=2/3:** CF n_mat=2 would first-window SELECT/INVENT board0[1]=ODD in 28/28 (currently persistently suppressed); CF n_mat=3 also adds POS2 (already escapes later — timing only). Marginal cost: +1/+2 first-window invent slots; ledger unit cost NOT_RECORDED; post-window CF trajectory NOT_RECORDED.
- **Breadth vs depth:** Under recorded n_mat=1, first-window breadth collapses to 1/10 while eventual breadth recovers to 4 unique invented keys via later rank-0 escapes, but demotion×n_mat=1 permanently suppresses 3 scored keys (ODD/POS6/POS7) — breadth cut is partial-recoverable; suppression is not.
- **Cost-control vs diversity:** n_mat=1 is an effective first-window cost-control valve (1 slot) that also materially cuts first-window diversity and, via demotion interaction, permanently suppresses a subset of skipped keys — cost-control and diversity loss are coupled, not alternatives.
- **Outside S-family (H13f AGAINST):** Tradeoff is not negligible outside S-family: POS6/POS7 also persistently suppressed; POS2/POS5/U show the escape path.

## Precise boundary

Established: first-window allocation tradeoff + skip/suppress partition + CF first-window sets.  
Not established: post-window CF value, invent unit cost, Sacred uplift.  
Intervention: requires separate authorization.

## Deliverables

- `reports/aivd_3_44_charter.md`
- `reports/aivd_3_44_hypothesis_tree.md`
- `reports/aivd_3_44_materialization_width_matrix.md` + `.json`
- `reports/aivd_3_44_breadth_depth_tradeoff.md` + `.json`
- `reports/aivd_3_44_budget_cost_curve.md` + `.json`
- `reports/aivd_3_44_first_window_skip.md` + `.json`
- `reports/aivd_3_44_persistent_suppression.md` + `.json`
- `reports/aivd_3_44_candidate_fate_matrix.md` + `.json`
- `reports/aivd_3_44_counterfactual_limitations.md`
- `reports/aivd_3_44_causal_model.md`
- `reports/aivd_3_44_results.md` + `.json`
- `aivd/experiments/aivd344/offline_allocation.py`

```
AIVD 3.44 EXPLORATION ALLOCATION AUDIT COMPLETE:
INTERVENTION REQUIRES SEPARATE AUTHORIZATION
```

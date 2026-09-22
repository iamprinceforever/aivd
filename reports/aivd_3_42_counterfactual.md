# AIVD 3.42 — Phase 2 Counterfactual (Offline What-If)

**Recorded:** 2026-09-22 13:00:57 IST  
**Status:** RAN  
**Mode:** offline_what_if_on_recorded_rows_only  
**Note:** Did not modify planner or execute repaired Sacred run  

## Gate

Phase 1 was sufficient to localize E (B+C+D interaction). Phase 2 therefore **RAN** as pure offline what-if on recorded rows — no planner modification, no Sacred repair run.

## CF1 — n_mat≥2 on first window

If first invent call materialized 2 candidates from recorded board0 order instead of 1, board0[1]==ODD would be the second SELECT.

- cells_where_board0_1_is_odd: **28/28**
- implication: ODD would reach SELECTED/INVENTED on first window in those cells (recorded order).

## CF2 — ODD at rank-0 in any recorded block

If any recorded rank block had odd_rank==0, n_mat=1 would select ODD.

- recorded_rank0_odd_blocks: **0**
- implication: No such recorded block; counterfactual requires alternate ranking outcome not present in ledger.

## CF3 — ODD at board0 position 0

If ODD occupied board0 position 0, first SELECT would be ODD under recorded n_mat=1.

- cells_with_odd_at_pos0: **0**
- implication: Not observed; board order is stably EVEN then ODD.

## Not claimed

- No authorization to change n_mat, rank formula, or board order in production.
- Counterfactuals are interpretive over recorded trajectories only.

See `reports/aivd_3_42_counterfactual.json`.

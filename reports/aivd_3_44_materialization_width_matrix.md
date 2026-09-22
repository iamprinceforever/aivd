# AIVD 3.44 — Materialization Width Matrix

**Recorded:** 2026-09-22 13:20:03 IST  
**Mode:** OBSERVED n_mat=1; CF n_mat=2..10 first-window only  
**Sacred:** NO  

## Headline

Observed lazy n_mat=1 materializes only board0[0]=EVEN in the first invent window (28/28). Offline CF: n_mat=2 would also materialize board0[1]=ODD; n_mat=3 adds POS2; wider n_mat walks further down the recorded board0. Post-window trajectories under CF are NOT_RECORDED.

## Matrix

| n_mat | Mode | First-window keys (pos) | Coverage | Families | +slots vs 1 | CF post-window |
|------:|------|-------------------------|---------:|---------:|------------:|----------------|
| 1 | OBSERVED | 0:S_EVEN_first_window | 10% | 1 | 0 | OBSERVED |
| 2 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed | 20% | 1 | 1 | NOT_RECORDED_REQUIRES_REEXECUTION |
| 3 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed, 2:POS2_escape | 30% | 1 | 2 | NOT_RECORDED_REQUIRES_REEXECUTION |
| 4 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed, 2:POS2_escape, 3:POS3_rank0_after_invent_stopped | 40% | 1 | 3 | NOT_RECORDED_REQUIRES_REEXECUTION |
| 5 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed, 2:POS2_escape, 3:POS3_rank0_after_invent_stopped, 4:U_successful | 50% | 2 | 4 | NOT_RECORDED_REQUIRES_REEXECUTION |
| 6 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed, 2:POS2_escape, 3:POS3_rank0_after_invent_stopped, 4:U_successful, 5:POS5_escape | 60% | 3 | 5 | NOT_RECORDED_REQUIRES_REEXECUTION |
| 7 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed, 2:POS2_escape, 3:POS3_rank0_after_invent_stopped, 4:U_successful, 5:POS5_escape, 6:POS6_suppressed | 70% | 3 | 6 | NOT_RECORDED_REQUIRES_REEXECUTION |
| 8 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed, 2:POS2_escape, 3:POS3_rank0_after_invent_stopped, 4:U_successful, 5:POS5_escape, 6:POS6_suppressed, 7:POS7_suppressed | 80% | 3 | 7 | NOT_RECORDED_REQUIRES_REEXECUTION |
| 9 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed, 2:POS2_escape, 3:POS3_rank0_after_invent_stopped, 4:U_successful, 5:POS5_escape, 6:POS6_suppressed, 7:POS7_suppressed, 8:POS8_never_scored | 90% | 3 | 8 | NOT_RECORDED_REQUIRES_REEXECUTION |
| 10 | OFFLINE_COUNTERFACTUAL_FIRST_WINDOW | 0:S_EVEN_first_window, 1:S_ODD_suppressed, 2:POS2_escape, 3:POS3_rank0_after_invent_stopped, 4:U_successful, 5:POS5_escape, 6:POS6_suppressed, 7:POS7_suppressed, 8:POS8_never_scored, 9:POS9_never_scored | 100% | 3 | 9 | NOT_RECORDED_REQUIRES_REEXECUTION |

## Observed metrics (n_mat=1)

- Candidate coverage (first window): 1/10
- Eventual unique invented: 4/10
- Unique families eventual: 3
- Invent attempts/cell: 7
- Successful (INVENTED_ATOM)/cell: 7
- Redundant re-invents/cell: 3
- Stop: BUDGET_EXHAUSTED (28/28); verified=False (28/28)
- Invent ledger unit cost: NOT_RECORDED (delta=0 on all invents)
- Recursive growth opportunities: NOT_RECORDED

See `reports/aivd_3_44_materialization_width_matrix.json`.

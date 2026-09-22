# AIVD 3.44 — Causal Model (Allocation)

**Recorded:** 2026-09-22 13:20:03 IST  
**Sacred:** NO  
**Extends:** 3.42 E (B+C+D interaction); 3.43 H12b/e generalization  

## Nodes

- `plan_board_order`
- `n_mat_lazy`
- `first_window_materialization`
- `invent_updates_rejected_classes`
- `rank_demotion`
- `later_window_rank0_gate`
- `persistent_suppression_or_escape`
- `budget_exhaustion`

## Edges

- `plan_board_order` → `first_window_materialization` (moderator: `n_mat_lazy`) — n_mat=1 takes only board0[0]
- `first_window_materialization` → `invent_updates_rejected_classes` — EVEN invent → char_stride rejected
- `invent_updates_rejected_classes` → `rank_demotion` — ODD/POS6/POS7 stay best_rank>=1
- `rank_demotion` → `later_window_rank0_gate` (moderator: `n_mat_lazy`) — only rank-0 materializes later
- `later_window_rank0_gate` → `persistent_suppression_or_escape` — escape if attain rank-0; else suppress
- `first_window_materialization` → `budget_exhaustion` — slot consumption; unit cost NOT_RECORDED

## Allocation tradeoff statement

n_mat chooses first-window breadth. Low n_mat saves first-window slots (cost-control) but (a) reduces first-window diversity and (b) when combined with class demotion, converts some temporary skips into persistent suppression. Raising n_mat expands first-window directions (e.g. ODD at n_mat=2) at +slot proxy cost; downstream value NOT_RECORDED offline.

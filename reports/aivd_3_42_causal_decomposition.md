# AIVD 3.42 — Causal Decomposition (A–E)

**Recorded:** 2026-09-22 13:00:57 IST  
**Sacred:** NO  
**No repair recommendation:** YES (FORBIDDEN)

## First causal localization

Odd-stride MAPT(SLICE:1,2(TOK)) is PROPOSED (proposal_index=3) and later SCORED/RANKED, but never SELECTED/INVENTED because (1) plan-board order places even-stride MAPT(SLICE:0,2(TOK)) at board0 position 0 and lazy n_mat=1 materializes only that slot before any score/rank, and (2) after EVEN invent, rejected_classes includes char_stride so subsequent rank_atoms keep ODD best_rank>=1 below the n_mat=1 cut — interaction of board order + rank demotion + n_mat=1 (E SUPPORTED; A/B AGAINST as sole causes).

## A–E classifications

| ID | Claim | Classification | Evidence |
|----|-------|----------------|----------|
| A | score alone | **AGAINST** | First SELECT of EVEN precedes all score events in 28/28 cells (scores_before_first_select_always_0=True); EVEN score recorded in 0/28 cells (=0). Score alone cannot explain first materialization preference. |
| B | rank alone | **AGAINST** | First SELECT precedes all rank events in 28/28 cells (ranks_before_first_select_always_0=True). Later ODD best_rank>=1 is consequential but not the sole first-cut cause. |
| C | board order alone | **INCONCLUSIVE** | Board order explains first SELECT: EVEN at board0 pos 0, ODD at pos 1 in 28/28. Alone it does not explain why ODD never later reaches SELECTED after re-rank (requires demotion + n_mat=1 cut). |
| D | n_mat=1 alone | **INCONCLUSIVE** | n_mat_inferred_pre_rank=1 in {1: 28} cells. Necessary for single-slot cut but insufficient alone without board-order placing EVEN first and later rank demotion keeping ODD off rank-0. |
| E | interaction B+C+D | **SUPPORTED** | (C) plan-board order materializes EVEN first under (D) n_mat=1; then char_stride enters rejected_classes; (B) subsequent rank_atoms keeps ODD best_rank>=1 in 28/28 so lazy n_mat=1 never selects ODD. |

## Dual-window account

1. **Window 1 (pre-score/rank):** board order + n_mat=1 → EVEN SELECTED/INVENTED; ODD remains on board at pos1 but not cut.
2. **Window 2 (post-EVEN):** `rejected_classes` includes `char_stride`; rank demotes ODD (best_rank≥1); n_mat=1 selects only rank-0 → ODD never SELECTED.

## H11 map

See `reports/aivd_3_42_hypothesis_tree.md` and embedded JSON in `aivd_3_42_causal_decomposition.json`.

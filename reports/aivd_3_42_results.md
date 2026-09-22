# AIVD 3.42 — Results (Executive Wrap-Up)

**Recorded:** 2026-09-22 13:00:57 IST  
**Baseline tip:** `0f42dc01dd0feac3b18e1dbe835282c8226bc821`  
**Branch:** `research/aivd-3.42-selection-causal-audit`  
**Sacred:** NO  
**Planner changed:** NO  

## Phase status

- **Phase 1:** COMPLETE (offline replay of 28 ON cells)
- **Phase 2:** RAN (offline what-if on recorded rows; no intervention)

## A–E

| ID | Classification |
|----|----------------|
| A score alone | **AGAINST** |
| B rank alone | **AGAINST** |
| C board order alone | **INCONCLUSIVE** |
| D n_mat=1 alone | **INCONCLUSIVE** |
| E interaction B+C+D | **SUPPORTED** |

## H11

| Leaf | Classification |
|------|----------------|
| H11a | **AGAINST** |
| H11b | **WEAKLY SUPPORTED** |
| H11c | **SUPPORTED** |
| H11d | **SUPPORTED** |
| H11e | **SUPPORTED** |
| H11f | **SUPPORTED** |
| H11g | **AGAINST** |
| H11-REJECT | **AGAINST** |

## Headlines

- **Score:** ODD scored exclusively at demoted value [0.038148] (components p_discovery=0.12/causal=0.55/reuse=0.8); EVEN score=NOT_RECORDED in 28/28 (SELECTED pre-score); U control scored [0.2781625].
- **Rank:** ODD best_rank always 1 (counter={1: 28}); never rank-0 (0/28). First SELECT has no preceding rank. U control attains rank-0 in first rank blocks.
- **Plan-board:** Recorded post-plan board0 is stably [EVEN@{0: 28}, ODD@{1: 28}, ...]; first_select_always_even=True.
- **n_mat:** Inferred lazy n_mat=1 from recorded events: exactly one SELECT before any RANK in every cell (counter={1: 28}). Code path (read-only confirmation): designer._maybe_invent_atom uses n_mat=1 if allow_atom_lazy else 4 — not modified.

## First causal localization (no repair)

Odd-stride MAPT(SLICE:1,2(TOK)) is PROPOSED (proposal_index=3) and later SCORED/RANKED, but never SELECTED/INVENTED because (1) plan-board order places even-stride MAPT(SLICE:0,2(TOK)) at board0 position 0 and lazy n_mat=1 materializes only that slot before any score/rank, and (2) after EVEN invent, rejected_classes includes char_stride so subsequent rank_atoms keep ODD best_rank>=1 below the n_mat=1 cut — interaction of board order + rank demotion + n_mat=1 (E SUPPORTED; A/B AGAINST as sole causes).

## Deliverables

- `reports/aivd_3_42_charter.md`
- `reports/aivd_3_42_hypothesis_tree.md`
- `reports/aivd_3_42_phase1_replay.md` + `.json`
- `reports/aivd_3_42_score_comparison.md` + `.json`
- `reports/aivd_3_42_rank_comparison.md` + `.json`
- `reports/aivd_3_42_plan_board_comparison.md` + `.json`
- `reports/aivd_3_42_n_mat_analysis.md` + `.json`
- `reports/aivd_3_42_causal_decomposition.md` (+ `.json`)
- `reports/aivd_3_42_counterfactual.md` + `.json`
- `reports/aivd_3_42_remaining_uncertainty.md`
- `reports/aivd_3_42_results.md` (+ `.json`)
- `aivd/experiments/aivd342/offline_replay.py` (read-only)

```
AIVD 3.42 CAUSAL AUDIT COMPLETE:
INTERVENTION REQUIRES SEPARATE AUTHORIZATION
```

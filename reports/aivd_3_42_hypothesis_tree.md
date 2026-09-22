# AIVD 3.42 — Hypothesis Tree (H11a–H11g + H11-REJECT)

**Recorded:** 2026-09-22 13:00:57 IST  
**Sacred:** NO  
**Scoring rule:** score independently; ties allowed; do not force singular repair winner.

| Leaf | Claim | Classification |
|------|-------|----------------|
| H11a | intrinsic score disadvantage | **AGAINST** |
| H11b | score-component disadvantage | **WEAKLY SUPPORTED** |
| H11c | relative ranking disadvantage | **SUPPORTED** |
| H11d | plan-board ordering/materialization priority | **SUPPORTED** |
| H11e | lazy n_mat=1 allocation bottleneck | **SUPPORTED** |
| H11f | interaction between ranking and n_mat=1 | **SUPPORTED** |
| H11g | novelty/identity effects after selection | **AGAINST** |
| H11-REJECT | evidence insufficient to localize further | **AGAINST** |

## Evidence summaries

### H11a — AGAINST

EVEN has no recorded intrinsic score (0/28). ODD recorded scores are exclusively demoted-class values [0.038148] after char_stride rejection; not an odd-stride-intrinsic prior vs EVEN pre-score.

### H11b — WEAKLY SUPPORTED

When scored, ODD components match demoted same-class pattern (p_discovery=0.12, causal_value=0.55, reuse_value=0.8) vs U untried [0.2781625]. Component gap is class-demotion, not odd-specific.

### H11c — SUPPORTED

odd_best_rank_counter={1: 28}; odd_ever_rank0_count=0/28; never SELECTED.

### H11d — SUPPORTED

even_board_pos={0: 28}, odd_board_pos={1: 28}; first_select_always_even=True.

### H11e — SUPPORTED

n_mat_inferred_pre_rank counter={1: 28} (exactly one SELECT before any RANK in every cell).

### H11f — SUPPORTED

After first EVEN invent, rejected_classes includes char_stride; ODD best_rank stays >=1 while n_mat=1 selects only rank-0 → odd_selected_count=0.

### H11g — AGAINST

ODD never reaches SELECTED/INVENTED; novelty/identity-after-selection cannot be the disappearance mechanism. Natural invents (EVEN/U) succeed.

### H11-REJECT — AGAINST

E_interaction SUPPORTED=SUPPORTED; deterministic 28/28 ON replay localizes beyond H11-REJECT.

## Parent localization (3.41 H10c)

3.41 localized disappearance at SCORED/RANKED-but-never-SELECTED under demotion + n_mat=1. 3.42 decomposes that into board-order first cut vs later rank×n_mat interaction without proposing repairs.

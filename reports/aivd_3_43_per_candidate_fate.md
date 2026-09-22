# AIVD 3.43 — Per-Candidate Fate

**Recorded:** 2026-09-22 13:06:36 IST  
**Mode:** OFFLINE_REPLAY_ONLY  
**Fields policy:** existing observations only; NOT_RECORDED if missing; no inference  

## Aggregate by board position (28/28 cells)

### Pos 0: `MAPT(SLICE:0,2(TOK))` (S_EVEN_first_window)

- selected: **28/28**; invented: **28/28**; ever_rank0: **0/28**
- best_rank_counter: `{}`
- score_unique_union: `NOT_RECORDED`
- mechanism_tag_counter: `{'FIRST_WINDOW_BOARD0_NMAT1': 28}`
- score_components_sample: `NOT_RECORDED`

### Pos 1: `MAPT(SLICE:1,2(TOK))` (S_ODD_suppressed)

- selected: **0/28**; invented: **0/28**; ever_rank0: **0/28**
- best_rank_counter: `{'1': 28}`
- score_unique_union: `[0.038148]`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'SUPPRESSED_RANK_DEMOTION_NMAT1': 28}`
- score_components_sample: `{'p_discovery': 0.12, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 0.55, 'reuse_value': 0.8, 'cost': 1.0}`

### Pos 2: `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` (positive_escape_pos2)

- selected: **28/28**; invented: **28/28**; ever_rank0: **28/28**
- best_rank_counter: `{'0': 28}`
- score_unique_union: `[0.038148]`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'ESCAPED_VIA_LATER_RANK0': 28}`
- score_components_sample: `{'p_discovery': 0.12, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 0.55, 'reuse_value': 0.8, 'cost': 1.0}`

### Pos 3: `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` (rank0_after_invent_stopped)

- selected: **0/28**; invented: **0/28**; ever_rank0: **28/28**
- best_rank_counter: `{'0': 28}`
- score_unique_union: `[0.038148]`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'RANK0_AFTER_INVENT_STOPPED': 28}`
- score_components_sample: `{'p_discovery': 0.12, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 0.55, 'reuse_value': 0.8, 'cost': 1.0}`

### Pos 4: `MAPT(CAT(TOK|AT:-1))` (U_natural_success)

- selected: **28/28**; invented: **28/28**; ever_rank0: **28/28**
- best_rank_counter: `{'0': 28}`
- score_unique_union: `[0.2781625]`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'ESCAPED_VIA_LATER_RANK0': 28}`
- score_components_sample: `{'p_discovery': 0.35, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 1.0, 'reuse_value': 1.1, 'cost': 1.0}`

### Pos 5: `MAPT(AT:-1)` (positive_escape_pos5)

- selected: **28/28**; invented: **28/28**; ever_rank0: **28/28**
- best_rank_counter: `{'0': 28}`
- score_unique_union: `[0.2781625]`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'ESCAPED_VIA_LATER_RANK0': 28}`
- score_components_sample: `{'p_discovery': 0.35, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 1.0, 'reuse_value': 1.1, 'cost': 1.0}`

### Pos 6: `MAPT(CAT(TOK|AT:0))` (demotion_suppress_sibling)

- selected: **0/28**; invented: **0/28**; ever_rank0: **0/28**
- best_rank_counter: `{'2': 28}`
- score_unique_union: `[0.038148, 0.2781625]`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'SUPPRESSED_RANK_DEMOTION_NMAT1': 28}`
- score_components_sample: `{'p_discovery': 0.35, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 1.0, 'reuse_value': 1.1, 'cost': 1.0}`

### Pos 7: `MAPT(CAT(AT:0|AT:-1))` (demotion_suppress_sibling)

- selected: **0/28**; invented: **0/28**; ever_rank0: **0/28**
- best_rank_counter: `{'3': 28}`
- score_unique_union: `[0.038148, 0.2781625]`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'SUPPRESSED_RANK_DEMOTION_NMAT1': 28}`
- score_components_sample: `{'p_discovery': 0.35, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 1.0, 'reuse_value': 1.1, 'cost': 1.0}`

### Pos 8: `MAPT(SLICE:0,3(TOK))` (never_scored_after_skip)

- selected: **0/28**; invented: **0/28**; ever_rank0: **0/28**
- best_rank_counter: `{}`
- score_unique_union: `NOT_RECORDED`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'NEVER_SCORED_AFTER_SKIP': 28}`
- score_components_sample: `NOT_RECORDED`

### Pos 9: `MAPT(AT:0)` (never_scored_after_skip)

- selected: **0/28**; invented: **0/28**; ever_rank0: **0/28**
- best_rank_counter: `{}`
- score_unique_union: `NOT_RECORDED`
- mechanism_tag_counter: `{'SKIPPED_FIRST_WINDOW_NMAT1': 28, 'NEVER_SCORED_AFTER_SKIP': 28}`
- score_components_sample: `NOT_RECORDED`

## Exemplar cell (S8-BASELINE seed0)

- board0: `['MAPT(SLICE:0,2(TOK))', 'MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(AT:-1|SLICE:0,1(TOK)))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))', 'MAPT(SLICE:0,3(TOK))', 'MAPT(AT:0)']`
- first_selected: `MAPT(SLICE:0,2(TOK))`
- n_mat_inferred_pre_rank: 1
- selects: `['MAPT(SLICE:0,2(TOK))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(SLICE:0,2(TOK))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(CAT(SLICE:1,1(TOK)|AT:0))']`
- invents: `['MAPT(SLICE:0,2(TOK))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(SLICE:0,2(TOK))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(CAT(SLICE:1,1(TOK)|AT:0))']`
- null_rejected_pre_select: True (novelty:ATOM_SEMANTIC_DUPLICATE)
- firewall_epoch: 1; firewalled: True
- terminal: TerminalState.UNRESOLVED_INVISIBLE; stop: BUDGET_EXHAUSTED; failure: ATOM_INVENTION_SKIPPED_BY_PLANNING

Per-candidate rows with board_position, score, rank, n_mat, selected, invented, 
invention attempts/results, remaining budget, firewall/novelty state: see JSON.

See `reports/aivd_3_43_per_candidate_fate.json`.

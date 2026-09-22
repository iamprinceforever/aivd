# AIVD 3.43 — Mechanism Frequency

**Recorded:** 2026-09-22 13:06:36 IST  
**Sacred:** NO  

## Headline

Across 28/28 identical board0 trajectories: lazy n_mat=1 skips ALL 9 board-position>0 candidates on the first invent window; 3 later ESCAPE via attaining rank-0 (['MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)']); 3 remain SUPPRESSED by rank demotion×n_mat=1 (['MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))']); 1 attain rank-0 only after invent stops (['MAPT(CAT(AT:-1|SLICE:0,1(TOK)))']); 2 never scored after first-window skip (['MAPT(SLICE:0,3(TOK))', 'MAPT(AT:0)']).

## Counts

| Metric | Value |
|--------|-------|
| n_cells | 28 |
| board0_length | 10 |
| board0_identical_across_cells | True |
| n_mat_inferred_always_1 | True |
| first_select_always_board0_pos0 | True |
| pos>0 candidates | 9 |
| pos>0 skipped first window (all cells) | 9 |

## Fate buckets

### Escaped via later rank-0
- `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` @ pos 2
- `MAPT(CAT(TOK|AT:-1))` @ pos 4
- `MAPT(AT:-1)` @ pos 5

### Suppressed by rank demotion × n_mat=1
- `MAPT(SLICE:1,2(TOK))` @ pos 1
- `MAPT(CAT(TOK|AT:0))` @ pos 6
- `MAPT(CAT(AT:0|AT:-1))` @ pos 7

### Rank-0 only after invent stopped
- `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` @ pos 3

### Never scored after first-window skip
- `MAPT(SLICE:0,3(TOK))` @ pos 8
- `MAPT(AT:0)` @ pos 9

See `reports/aivd_3_43_mechanism_frequency.json`.

# AIVD 3.44 — First-Window Skip

**Recorded:** 2026-09-22 13:20:03 IST  
**Sacred:** NO  

## Headline

First-window skip rate: 9/9 pos>0 keys × 28/28 cells = 252/252 (100% of pos>0; 90% of board0 slots).

## Definition

FIRST-WINDOW-SKIPPED = board_position > 0 under observed n_mat=1.

## Critical distinction

FIRST-WINDOW-SKIPPED ≠ undiscoverable. Escapees POS2/U/POS5 are skipped then later SELECTED/INVENTED. Only demotion×n_mat=1 persistent suppression blocks eventual selection among scored keys.

## Skipped keys (pos>0)

- pos 1: `MAPT(SLICE:1,2(TOK))` (S_ODD_suppressed)
- pos 2: `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` (POS2_escape)
- pos 3: `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` (POS3_rank0_after_invent_stopped)
- pos 4: `MAPT(CAT(TOK|AT:-1))` (U_successful)
- pos 5: `MAPT(AT:-1)` (POS5_escape)
- pos 6: `MAPT(CAT(TOK|AT:0))` (POS6_suppressed)
- pos 7: `MAPT(CAT(AT:0|AT:-1))` (POS7_suppressed)
- pos 8: `MAPT(SLICE:0,3(TOK))` (POS8_never_scored)
- pos 9: `MAPT(AT:0)` (POS9_never_scored)

See `reports/aivd_3_44_first_window_skip.json`.

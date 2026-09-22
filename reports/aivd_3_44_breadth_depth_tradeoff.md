# AIVD 3.44 — Breadth vs Depth Tradeoff

**Recorded:** 2026-09-22 13:20:03 IST  
**Sacred:** NO  

## One sentence

Under recorded n_mat=1, first-window breadth collapses to 1/10 while eventual breadth recovers to 4 unique invented keys via later rank-0 escapes, but demotion×n_mat=1 permanently suppresses 3 scored keys (ODD/POS6/POS7) — breadth cut is partial-recoverable; suppression is not.

## Observed (n_mat=1)

| Quantity | Value |
|----------|-------|
| First-window breadth | 1 |
| Eventual unique invented keys | 4 |
| Persistent suppression keys | 3 (MAPT(SLICE:1,2(TOK)), MAPT(CAT(TOK|AT:0)), MAPT(CAT(AT:0|AT:-1))) |
| Escape keys | 3 (MAPT(CAT(SLICE:1,1(TOK)|AT:0)), MAPT(CAT(TOK|AT:-1)), MAPT(AT:-1)) |

## Counterfactual first-window breadth

| n_mat | First-window breadth | Newly materialized vs n_mat=1 |
|------:|---------------------:|------------------------------|
| 2 | 2 | ODD (currently persistently suppressed) |
| 3 | 3 | ODD + POS2 (POS2 already escapes later — timing only) |
| 4 | 4 | + POS3 (rank0-after-stop in observed; CF invent first-window only) |

## Limitation

Post-first-window discovery under CF n_mat>=2 is NOT_RECORDED; do not label suppressed keys discoverable beyond first-window SELECT/INVENT from recorded board0 order.

See `reports/aivd_3_44_breadth_depth_tradeoff.json`.

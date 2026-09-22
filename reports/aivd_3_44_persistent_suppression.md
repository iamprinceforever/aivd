# AIVD 3.44 — Persistent Suppression

**Recorded:** 2026-09-22 13:20:03 IST  
**Sacred:** NO  

## Headline

Persistent suppression: 3/9 pos>0 keys (33%) — ['MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))']; among scored/ranked skipped keys 3/7 (43%).

## Definition

PERSISTENT SUPPRESSION = FIRST-WINDOW-SKIPPED AND never selected/invented, with SUPPRESSED_RANK_DEMOTION_NMAT1 (best_rank>=1 while n_mat=1 takes rank-0).

## Buckets among pos>0

| Bucket | Keys | n |
|--------|------|--:|
| Persistent suppression (demotion×n_mat=1) | ['MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))'] | 3 |
| Escaped via later rank-0 | ['MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)'] | 3 |
| Rank-0 after invent stopped | ['MAPT(CAT(AT:-1|SLICE:0,1(TOK)))'] | 1 |
| Never scored after skip | ['MAPT(SLICE:0,3(TOK))', 'MAPT(AT:0)'] | 2 |

## Honesty bound

Audit does NOT claim these keys are undiscoverable in principle — only that under recorded n_mat=1×demotion they were never selected. CF n_mat>=2 would first-window materialize ODD from board0 order; verification/Sacred uplift NOT_RECORDED.

See `reports/aivd_3_44_persistent_suppression.json`.

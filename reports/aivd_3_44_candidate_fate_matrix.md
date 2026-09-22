# AIVD 3.44 — Candidate Fate Matrix

**Recorded:** 2026-09-22 13:20:03 IST  
**Fate track:** PROPOSED → SCORED → RANKED → FIRST-WINDOW-SKIPPED → LATER-RANK-0 → SELECTED → INVENTED → VERIFIED  
**Sacred:** NO  

## Board0 rows (28/28 cells)

| Pos | Key | Role | FW-skip | Rank0 | Sel | Inv | Persist suppress | Escape | Exemplar track |
|----:|-----|------|--------:|------:|----:|----:|:----------------:|:------:|----------------|
| 0 | `MAPT(SLICE:0,2(TOK))` | S_EVEN_first_window | 0/28 | 0/28 | 28/28 | 28/28 | n | n | PROPOSED → SELECTED → INVENTED |
| 1 | `MAPT(SLICE:1,2(TOK))` | S_ODD_suppressed | 28/28 | 0/28 | 0/28 | 0/28 | Y | n | PROPOSED → SCORED → RANKED → FIRST-WINDOW-SKIPPED |
| 2 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | POS2_escape | 28/28 | 28/28 | 28/28 | 28/28 | n | Y | PROPOSED → SCORED → RANKED → FIRST-WINDOW-SKIPPED → LATER-RANK-0 → SELECTED → INVENTED |
| 3 | `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` | POS3_rank0_after_invent_stopped | 28/28 | 28/28 | 0/28 | 0/28 | n | n | PROPOSED → SCORED → RANKED → FIRST-WINDOW-SKIPPED → LATER-RANK-0 |
| 4 | `MAPT(CAT(TOK|AT:-1))` | U_successful | 28/28 | 28/28 | 28/28 | 28/28 | n | Y | PROPOSED → SCORED → RANKED → FIRST-WINDOW-SKIPPED → LATER-RANK-0 → SELECTED → INVENTED |
| 5 | `MAPT(AT:-1)` | POS5_escape | 28/28 | 28/28 | 28/28 | 28/28 | n | Y | PROPOSED → SCORED → RANKED → FIRST-WINDOW-SKIPPED → LATER-RANK-0 → SELECTED → INVENTED |
| 6 | `MAPT(CAT(TOK|AT:0))` | POS6_suppressed | 28/28 | 0/28 | 0/28 | 0/28 | Y | n | PROPOSED → SCORED → RANKED → FIRST-WINDOW-SKIPPED |
| 7 | `MAPT(CAT(AT:0|AT:-1))` | POS7_suppressed | 28/28 | 0/28 | 0/28 | 0/28 | Y | n | PROPOSED → SCORED → RANKED → FIRST-WINDOW-SKIPPED |
| 8 | `MAPT(SLICE:0,3(TOK))` | POS8_never_scored | 28/28 | 0/28 | 0/28 | 0/28 | n | n | PROPOSED → FIRST-WINDOW-SKIPPED |
| 9 | `MAPT(AT:0)` | POS9_never_scored | 28/28 | 0/28 | 0/28 | 0/28 | n | n | PROPOSED → FIRST-WINDOW-SKIPPED |

## Null control

- Key: `MAPT(CAT(AT:-1|TOK))`
- Rejected pre-select: 28/28 (reasons={'novelty:ATOM_SEMANTIC_DUPLICATE': 28})
- On board0: False; selected/invented: 0/28

See `reports/aivd_3_44_candidate_fate_matrix.json`.

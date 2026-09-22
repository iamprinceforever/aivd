# AIVD 3.43 — Generalization Matrix

**Recorded:** 2026-09-22 13:06:36 IST  
**Primary question:** Does plan-board order + rank demotion + lazy n_mat=1 systematically suppress valid lower-position candidates?  
**Answer (short):** PARTIAL — first-window yes for all pos>0; permanent suppress only with demotion×n_mat=1  
**n_cells:** 28  

## Matrix

| Pos | Candidate | Role | First window | Permanent fate | Sel | Inv | Ever R0 | Best rank |
|-----|-----------|------|--------------|----------------|-----|-----|---------|-----------|
| 0 | `MAPT(SLICE:0,2(TOK))` | S_EVEN_first_window | MATERIALIZED | FIRST_WINDOW_SUCCESS | 28/28 | 28/28 | 0/28 | NR |
| 1 | `MAPT(SLICE:1,2(TOK))` | S_ODD_suppressed | SKIPPED_NMAT1 | SUPPRESSED_DEMOTION_NMAT1 | 0/28 | 0/28 | 0/28 | {'1': 28} |
| 2 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | positive_escape_pos2 | SKIPPED_NMAT1 | ESCAPED_VIA_RANK0 | 28/28 | 28/28 | 28/28 | {'0': 28} |
| 3 | `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` | rank0_after_invent_stopped | SKIPPED_NMAT1 | RANK0_AFTER_INVENT_STOPPED | 0/28 | 0/28 | 28/28 | {'0': 28} |
| 4 | `MAPT(CAT(TOK|AT:-1))` | U_natural_success | SKIPPED_NMAT1 | ESCAPED_VIA_RANK0 | 28/28 | 28/28 | 28/28 | {'0': 28} |
| 5 | `MAPT(AT:-1)` | positive_escape_pos5 | SKIPPED_NMAT1 | ESCAPED_VIA_RANK0 | 28/28 | 28/28 | 28/28 | {'0': 28} |
| 6 | `MAPT(CAT(TOK|AT:0))` | demotion_suppress_sibling | SKIPPED_NMAT1 | SUPPRESSED_DEMOTION_NMAT1 | 0/28 | 0/28 | 0/28 | {'2': 28} |
| 7 | `MAPT(CAT(AT:0|AT:-1))` | demotion_suppress_sibling | SKIPPED_NMAT1 | SUPPRESSED_DEMOTION_NMAT1 | 0/28 | 0/28 | 0/28 | {'3': 28} |
| 8 | `MAPT(SLICE:0,3(TOK))` | never_scored_after_skip | SKIPPED_NMAT1 | NEVER_SCORED | 0/28 | 0/28 | 0/28 | NR |
| 9 | `MAPT(AT:0)` | never_scored_after_skip | SKIPPED_NMAT1 | NEVER_SCORED | 0/28 | 0/28 | 0/28 | NR |

## Headline

Across 28/28 identical board0 trajectories: lazy n_mat=1 skips ALL 9 board-position>0 candidates on the first invent window; 3 later ESCAPE via attaining rank-0 (['MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)']); 3 remain SUPPRESSED by rank demotion×n_mat=1 (['MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))']); 1 attain rank-0 only after invent stops (['MAPT(CAT(AT:-1|SLICE:0,1(TOK)))']); 2 never scored after first-window skip (['MAPT(SLICE:0,3(TOK))', 'MAPT(AT:0)']).

## H12 snapshot

- **H12a:** AGAINST
- **H12b:** SUPPORTED
- **H12c:** SUPPORTED
- **H12d:** AGAINST
- **H12e:** SUPPORTED
- **H12-REJECT:** AGAINST

## Controls snapshot

- **Positive board-pos1:** NOT_OBSERVED
- **Positive pos>0 escape:** OBSERVED
- **Null:** NULL rejected pre-first-select in 28/28 cells (reason={'novelty:ATOM_SEMANTIC_DUPLICATE': 28}); never on board0; never selected/invented.

See `reports/aivd_3_43_generalization_matrix.json`.

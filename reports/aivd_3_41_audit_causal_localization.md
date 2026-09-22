# AIVD 3.41 — First Causal Localization

**Recorded:** 2026-09-22 12:57:05 IST
**Sacred:** NO

## Localization (one sentence)

Odd-stride MAPT(SLICE:1,2(TOK)) is PROPOSED (proposal_index=3) and later SCORED/RANKED, but is never SELECTED/INVENTED because (1) first materialization prefers same-class even-stride MAPT(SLICE:0,2(TOK)) from plan board order, and (2) subsequent rank_atoms calls demote char_stride (rejected_classes) so odd-stride's best rank stays ≥1 below the lazy n_mat=1 cut — H10c SUPPORTED; H10a AGAINST.

## Evidence refs

- `odd_stride_fate_table[*].Q1_proposed=true`
- `odd_stride_fate_table[*].Q7_selected=false`
- `odd_stride_fate_table[*].Q9_invent_success=false`
- `odd_stride_fate_table[*].best_rank >= 1`
- `first_rank_block rejected_classes includes char_stride`
- `natural_success_controls include MAPT(SLICE:0,2(TOK)) INVENTED`
- `H10c=SUPPORTED`
- `H10a=AGAINST`

## Not claimed

- Sacred discovery uplift
- S injection into propose_atoms
- FILTER / R-A/R-C/R-D integration
- Singular root cause beyond observed H10c localization

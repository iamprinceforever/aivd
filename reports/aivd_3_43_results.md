# AIVD 3.43 — Results (Executive Wrap-Up)

**Recorded:** 2026-09-22 13:06:36 IST  
**Baseline tip:** `3a07abe1e370f3328be33a3ad93e5fb7972a65eb`  
**Branch:** `research/aivd-3.43-selection-budget-generalization`  
**Parent:** `research/aivd-3.42-selection-causal-audit` @ 3a07abe  
**Sacred:** NO  
**Planner changed:** NO  
**n_mat changed:** NO  

## Phase status

- **Phase 1:** COMPLETE (offline multi-key replay of 28 ON cells)
- **Phase 2:** SKIPPED (Phase 1 sufficient; see counterfactual report)

## H12

| Leaf | Classification |
|------|----------------|
| H12a | **AGAINST** |
| H12b | **SUPPORTED** |
| H12c | **SUPPORTED** |
| H12d | **AGAINST** |
| H12e | **SUPPORTED** |
| H12-REJECT | **AGAINST** |

## Mechanism frequency headline

Across 28/28 identical board0 trajectories: lazy n_mat=1 skips ALL 9 board-position>0 candidates on the first invent window; 3 later ESCAPE via attaining rank-0 (['MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)']); 3 remain SUPPRESSED by rank demotion×n_mat=1 (['MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))']); 1 attain rank-0 only after invent stops (['MAPT(CAT(AT:-1|SLICE:0,1(TOK)))']); 2 never scored after first-window skip (['MAPT(SLICE:0,3(TOK))', 'MAPT(AT:0)']).

## Controls

- **Positive board-pos1:** NOT_OBSERVED
- **Positive pos>0 escape:** OBSERVED
- **Null:** NULL rejected pre-first-select in 28/28 cells (reason={'novelty:ATOM_SEMANTIC_DUPLICATE': 28}); never on board0; never selected/invented.

## S vs U

- S/ODD: board@1; never selected; demotion×n_mat=1 suppress
- U: board@4; selected+invented 28/28 via later rank-0 escape
- Contrast: Same first-window n_mat=1 skip; divergent permanent fate determined by whether the key later attains rank-0 under class demotion.

## Does the mechanism generalize?

**PARTIAL** — First-window board-order×n_mat=1 skip generalizes to all pos>0 keys; permanent suppression generalizes only where rank demotion keeps the key off rank-0 (ODD/POS6/POS7), while U/POS2/POS5 escape — not S-specific.

## Deliverables

- `reports/aivd_3_43_charter.md`
- `reports/aivd_3_43_hypothesis_tree.md`
- `reports/aivd_3_43_generalization_matrix.md` + `.json`
- `reports/aivd_3_43_per_candidate_fate.md` + `.json`
- `reports/aivd_3_43_mechanism_frequency.md` + `.json`
- `reports/aivd_3_43_controls.md` + `.json`
- `reports/aivd_3_43_counterfactual.md` + `.json` (SKIPPED)
- `reports/aivd_3_43_boundary.md`
- `reports/aivd_3_43_results.md` + `.json`
- `aivd/experiments/aivd343/offline_generalization.py` (read-only)

```
AIVD 3.43 GENERALIZATION AUDIT COMPLETE:
INTERVENTION REQUIRES SEPARATE AUTHORIZATION
```

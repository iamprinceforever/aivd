# AIVD 3.40 Stage-7 Results

**Recorded:** 2026-09-21 20:29 IST
**Design tip:** `d0ef7b6`
**Execution HEAD (pre-commit):** `d0ef7b64c7981ab900b9e5049fc65fd47211ca29`
**Claim labels:** `OFFLINE_GENERALIZATION_BENCH` / `IMPL_SPEC_EQUIVALENCE`
**Sacred authorized:** false
**Filter replaced:** false
**Autonomous discovery credit:** false

## OUTAGE_RECOVERY

Prior Phase-0 passed then Shell/Read outage; freeze JSON and runners lost. Prior hashes could not be reproduced bit-identical; NEW freeze regenerated from d0ef7b6 Stage-7 specs BEFORE repair outcomes. Independence labels follow generalization_spec; no Stage-6 per-pair prediction tuning.

- Prior hashes matched: `False`
- New context_bank_hash: `d1a68addba695c7d31adef6fb731fcd21b9bdc3907d2e5bffe5d4a12897e7d4f`
- New pair_list_hash: `aa46cb386d53534ff28353d1521ead19c1302d2a1e72d010a9d504c7166cc4cf`
- New gt_hash: `c18227598fd0acaa46bcf7cf36e92279b5cb1f2faca772ee2882990b7fcbba09`

## Phase 0 integrity

- ok: `True`
- design docs match d0ef7b6: `True`
- Stage-6 unchanged: `True`
- grow.py unchanged since 4005e66: `True`

## Phase A — ablation (P_IND primary)

| Mechanism | Gate | FDR | MDR | DPR | DCR* | AR | calls_mean | calls_worst | deg | sdiag_conflict |
|---|---|---|---|---|---|---|---|---|---|---|
| BASELINE | INCONCLUSIVE | 0.4666666666666667 | 0.0 | 0.5333333333333333 | 1.0 | 0.0 | 0.7727 | 2 | [] | True |
| R-A | SUCCESS | 0.0 | 0.0 | 1.0 | 1.0 | 0.0 | 1.2727 | 4 | [] | False |
| R-B | COST_IMPRACTICAL | 0.0 | 0.0 | 1.0 | 1.0 | 0.0 | 5.0455 | 18 | [] | False |
| R-C | SUCCESS | 0.0 | 0.0 | 1.0 | 1.0 | 0.0 | 1.2727 | 4 | [] | False |
| R-D | SUCCESS | 0.0 | 0.0 | 1.0 | 1.0 | 0.0 | 1.2727 | 4 | [] | False |

\* DCR on TD ∪ TDBE ∪ ADV_TS within P_IND.

- Survivors for Phase B: `['R-A', 'R-B', 'R-C', 'R-D']`
- Ranking multi-candidate: `['R-A', 'R-C', 'R-D']`
- Global apply_micro: `{'total_apply_micro': 244, 'cap': 5000}`

### P_IND class notes

- **R-A** class_rates_ind keys: ['ADV_TEXT_DIFF_BEH_SAME', 'ADV_TEXT_SIM_BEH_DIFF', 'COMPOSITION_SENSITIVE', 'CONTEXT_DEPENDENT', 'KNOWN_NONDUP', 'STATE_CONTEXT_SENSITIVE', 'TEXT_DIFF_BEH_EQ', 'TEXT_EQ_BEH_DIFF', 'TRUE_DUP', 'U_GOOD']
- **R-B** class_rates_ind keys: ['ADV_TEXT_DIFF_BEH_SAME', 'ADV_TEXT_SIM_BEH_DIFF', 'COMPOSITION_SENSITIVE', 'CONTEXT_DEPENDENT', 'KNOWN_NONDUP', 'STATE_CONTEXT_SENSITIVE', 'TEXT_DIFF_BEH_EQ', 'TEXT_EQ_BEH_DIFF', 'TRUE_DUP', 'U_GOOD']
- **R-C** class_rates_ind keys: ['ADV_TEXT_DIFF_BEH_SAME', 'ADV_TEXT_SIM_BEH_DIFF', 'COMPOSITION_SENSITIVE', 'CONTEXT_DEPENDENT', 'KNOWN_NONDUP', 'STATE_CONTEXT_SENSITIVE', 'TEXT_DIFF_BEH_EQ', 'TEXT_EQ_BEH_DIFF', 'TRUE_DUP', 'U_GOOD']
- **R-D** class_rates_ind keys: ['ADV_TEXT_DIFF_BEH_SAME', 'ADV_TEXT_SIM_BEH_DIFF', 'COMPOSITION_SENSITIVE', 'CONTEXT_DEPENDENT', 'KNOWN_NONDUP', 'STATE_CONTEXT_SENSITIVE', 'TEXT_DIFF_BEH_EQ', 'TEXT_EQ_BEH_DIFF', 'TRUE_DUP', 'U_GOOD']

## Phase B — impl equivalence

- isolation ok: `True` grow_py_diff_empty=`True`
- semantic_preservation ok: `True`

| Mechanism | Gate | mismatch_rate | label_mm | cost_mm | PT vector |
|---|---|---|---|---|---|
| R-A | SUCCESS | 0.0 | 0 | 0 | {'PT-REFL': True, 'PT-DET': True, 'PT-TD': True, 'PT-ND': True, 'PT-COST': True, 'PT-PROV': True, 'PT-CTX': True} |
| R-B | SUCCESS | 0.0 | 0 | 0 | {'PT-REFL': True, 'PT-DET': True, 'PT-TD': True, 'PT-ND': True, 'PT-COST': True, 'PT-PROV': True, 'PT-CTX': True} |
| R-C | SUCCESS | 0.0 | 0 | 0 | {'PT-REFL': True, 'PT-DET': True, 'PT-TD': True, 'PT-ND': True, 'PT-COST': True, 'PT-PROV': True, 'PT-CTX': True} |
| R-D | SUCCESS | 0.0 | 0 | 0 | {'PT-REFL': True, 'PT-DET': True, 'PT-TD': True, 'PT-ND': True, 'PT-COST': True, 'PT-PROV': True, 'PT-CTX': True} |

## Language stance (no best/winning/solves S)

- **H7a_genuine_generalization:** supported by Stage-7 evidence
- **H7b_benchmark_overfitting:** not supported
- **H7c_impl_spec_equivalence:** supported by Stage-7 evidence
- **H7d_cost_quality_ranking:** supported by Stage-7 evidence
- **H7e_diagnostic_conflict_reportable:** supported by Stage-7 evidence
- **H7_REJECT:** not supported
- **diagnostic_conflict_observed:** True

## Decision

- Case: **1** (`PHASE_A_SUCCESS_AND_PHASE_B_PASS`)
- Recommended NEXT AUTHORIZATION (not executed): Authorize a SEPARATE Sacred charter draft ONLY (docs), restating not-make-S-pass, namespace separation, BH48 frozen accounting, and that live FILTER_BEHAVIORAL_DUP replacement requires yet another authorization beyond Sacred. Multi-candidate survivors: ['R-A', 'R-C', 'R-D']. Do NOT merge live filter; do NOT execute Sacred in that design commit.

```
STAGE-7 COMPLETE: PHASE A/B PASS — SACRED NOT AUTHORIZED; NEW CHARTER REQUIRED
```


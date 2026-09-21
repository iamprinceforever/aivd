# AIVD 3.40 Phase-1 Results — Offline Historical-Trajectory Analysis

**Recorded:** 2026-09-21 17:31 IST
**Start tip:** `57c88f9`
**Commit tip:** `26ec383`
**Authority:** Phase-1 charter `57c88f9`; Stage-3 `146915b`; Stage-2 `dcae889`; R1b caveat `7a3457e`

---

## 1. Scope

Phase-1 ONLY: observational normalize + evaluator-only counterfactual replay.
Sacred / Phase-2 / Rx / BHexplore / budget / representation changes: **NOT AUTHORIZED**.

## 2. Trajectory coverage

- Expected: **28**
- Present: **28**
- Missing: **0** 

## 3. Field coverage honesty

UNKNOWN (never reconstructed):
- `full_candidate_pool_snapshots`
- `candidate_scores`
- `candidate_ranking_tables`
- `explicit_selected_candidate_decision_records`
- `features_used_maps`
- `rejection_skip_reason_enums_beyond_stop_failure_notes`

**H3 status:** `MAY_REMAIN_INCONCLUSIVE`

## 4. U positive-control gate (Gate E) — BH-R1 × U

- Status: **PASS**
- Seeds pass: 7/7
- Message: BH-R1×U F7/I7/V7 reconstructible from OBSERVED fields
- Aggregate F/I/V: `{'firewall': 7, 'independent_strict': 7, 'verified': 7}`

## 5. Key OBSERVED findings (no overclaim)

- 28/28 Stage-2 trajectories present and normalized with UNKNOWN honesty.
- BH-R1×U reconstructible: terminal VERIFIED, strict_independence True, firewall_epoch≥1, rotate-left body in produced-body census (F7/I7/V7).
- BH-R1×S: odd-stride atom absent from invent/generation_records across all 7 seeds; finished odd CAT-self absent; even CAT-self and rotate-class bodies present.
- BH-R1b×S (observational, caveat 7a3457e): odd-stride atom invented 7/7; finished odd CAT-self still absent 7/7; even CAT-self grown 7/7.
- pool/score/rank/selected/features_used remain UNKNOWN — H3 not accepted.
- Counterfactual CAT_SELF grow on odd-stride parent is COUNTERFACTUAL only; CF geometry match ≠ Sacred VERIFIED / ≠ AIVD discovered X.
- H5 not supported as primary: leftover_at_firewall_decision > 0 on BH-R1 S while correct finished body never appeared.
- R1b Sacred is observational only (commit 7a3457e); not pure Commit-B prereg.

## 6. S question ladder + earliest divergence (per seed)

| Condition | Seed | Diagnosis | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | R1b caveat |
|-----------|------|-----------|----|----|----|----|----|----|----|----|------------|
| BH-R1 | 0 | SUPPORTED H1 | no | no | no | UNKNOWN | UNKNOWN | no | no | yes | False |
| BH-R1 | 1 | SUPPORTED H1 | no | no | no | UNKNOWN | UNKNOWN | no | no | yes | False |
| BH-R1 | 2 | SUPPORTED H1 | no | no | no | UNKNOWN | UNKNOWN | no | no | yes | False |
| BH-R1 | 3 | SUPPORTED H1 | no | no | no | UNKNOWN | UNKNOWN | no | no | yes | False |
| BH-R1 | 4 | SUPPORTED H1 | no | no | no | UNKNOWN | UNKNOWN | no | no | yes | False |
| BH-R1 | 7 | SUPPORTED H1 | no | no | no | UNKNOWN | UNKNOWN | no | no | yes | False |
| BH-R1 | 11 | SUPPORTED H1 | no | no | no | UNKNOWN | UNKNOWN | no | no | yes | False |
| BH-R1b | 0 | SUPPORTED H2 | yes | no | no | UNKNOWN | UNKNOWN | no | no | yes | True |
| BH-R1b | 1 | SUPPORTED H2 | yes | no | no | UNKNOWN | UNKNOWN | no | no | yes | True |
| BH-R1b | 2 | SUPPORTED H2 | yes | no | no | UNKNOWN | UNKNOWN | no | no | yes | True |
| BH-R1b | 3 | SUPPORTED H2 | yes | no | no | UNKNOWN | UNKNOWN | no | no | yes | True |
| BH-R1b | 4 | SUPPORTED H2 | yes | no | no | UNKNOWN | UNKNOWN | no | no | yes | True |
| BH-R1b | 7 | SUPPORTED H2 | yes | no | no | UNKNOWN | UNKNOWN | no | no | yes | True |
| BH-R1b | 11 | SUPPORTED H2 | yes | no | no | UNKNOWN | UNKNOWN | no | no | yes | True |

## 7. Diagnosis distribution

- BH-R1×S: `{'SUPPORTED H1': 7}`
- BH-R1b×S (observational): `{'SUPPORTED H2': 7}`
- INCONCLUSIVE count: **0**
- Supported H1 count: **7**
- Supported H2 count: **7**
- Supported H3 count: **0** (must stay 0 without pool/rank)

## 8. R1 vs R1b comparison

Under R1, invent lacks odd-stride atom (H1). Under R1b observational, invent gains odd-stride but growth still does not produce finished odd CAT-self in records (H2). Do not claim R1b was preregistered-unchanged.

**R1b caveat:** Commit 7a3457e trimmed invent basis after smoke before Sacred; R1b measured but not pure Commit-B prereg. Preserve.

## 9. Counterfactual replay summary

- Episodes replayed: 28
- Ops: enumerate_produced_bodies, path_prefix_check, what_if_grow, what_if_select
- discovery_feedback: `False`
- sacred_credit: `False`
- Every CF result is counterfactual and not historical discovery; CF success ≠ AIVD discovered X

### CF reporting rule

Every CF result records parent state, candidate, evaluator inputs/result,
what was NOT simulated, and that it is counterfactual — not historical discovery.
CF success ≠ "AIVD discovered X".

## 10. Max valid claims (per condition)

### BH-R1

OBSERVED invent/generation_records lack odd-stride atom MAPT(SLICE:1,2(TOK)); finished odd CAT-self absent. Earliest bottleneck at representation/invent coverage (H1). H3 not claimable (pool/rank/selected UNKNOWN).

H3 note: H3 MAY_REMAIN_INCONCLUSIVE: pool/score/rank/selected UNKNOWN; do not convert even-CAT-self preference into definitive H3

### BH-R1b

OBSERVED invent includes odd-stride atom MAPT(SLICE:1,2(TOK)); finished odd CAT-self MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))) NEVER appears in generation_records produced-body census. Even CAT-self may appear — that is production preference evidence for growth (H2), NOT proof of selection failure (H3) because pool/score/rank/selected remain UNKNOWN. Counterfactual CAT_SELF grow on odd-stride parent is labeled COUNTERFACTUAL only.

H3 note: H3 MAY_REMAIN_INCONCLUSIVE: pool/score/rank/selected UNKNOWN; do not convert even-CAT-self preference into definitive H3

## 11. Exit gates A–G

- **A_trajectories_sufficient**: PASS
- **B_instrumentation_observational**: PASS
- **C_replay_evaluator_only**: PASS
- **D_historical_immutable**: PASS
- **E_u_bhr1_positive_control**: PASS
- **F_s_earliest_divergence_or_inconclusive**: PASS
- **G_no_new_experimental_condition**: PASS

## 12. Prohibitions honored

- No Sacred / Rx / BHexplore
- No budget/representation changes
- No core science module edits
- No Stage-2 artifact mutation
- No UNKNOWN silent fill
- No CF→discovery feedback
- No Phase-2 start
- R1b caveat preserved

## 13. What Phase-1 did NOT do

- No Sacred / mock Sacred / Stage-2 re-run
- No Phase-2 / Rx / BHexplore
- No edits to `aivd/science/{designer,atom_synth,grow,representation,language,...}.py`
- No mutation of `reports/aivd_3_40_stage2/**`
- No silent fill of UNKNOWN fields
- No claim that CF verify-accept is Sacred VERIFIED

---

PHASE-1 COMPLETE: NEW SACRED EXPERIMENT NOT YET AUTHORIZED

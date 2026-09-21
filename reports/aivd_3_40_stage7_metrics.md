# AIVD 3.40 Stage-7 — Metrics Specification

**Document type:** Stage-7 metrics spec (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:55 IST  
**Parent charter:** `reports/aivd_3_40_stage7_charter.md`  
**Companions:** preregistration, generalization_spec, implementation_validation_spec, matrix  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 0. Mandate

Preregister **how** Stage-7 measures (1) independent generalization beyond Stage-6, (2) cost practicality, (3) offline↔executable equivalence — **before** seeing Phase-A/B outcomes. Metrics must not reduce to “S passes,” “critical pair survives,” or “Stage-6 replay still green.”

---

## 1. Units & populations

| Symbol | Meaning |
|--------|---------|
| Pair | Ordered evaluation unit `(body_a, body_b)` under frozen condition_id |
| GT | Ground truth ∈ {`DUP`, `DISTINCT`} with `MIXED`→`DISTINCT` for hard-collapse prohibition |
| Pred | Mechanism label ∈ {`duplicate`, `distinct`, `ambiguous`} |
| Mechanism | `BASELINE` \| `R-A` \| `R-B` \| `R-C` \| `R-D` |
| Call | One `apply_micro(prompt, body)` toward Stage-7 experimental budget |
| Independence | `INDEPENDENT` \| `RELATED` \| `S6_REPLAY` \| `S_DIAGNOSTIC` |

Populations:

| Population | Membership |
|------------|------------|
| `P_IND` | Pairs with independence=`INDEPENDENT` — **primary Phase-A rates** |
| `P_REL` | `RELATED` — side table only |
| `P_REPLAY` | `S6_REPLAY` — continuity only |
| `P_SDIAG` | `S_DIAGNOSTIC` — conflict table only |
| `P_TD` / `P_ND` / `P_CD` / `P_TEBD` / `P_TDBE` / `P_ST` / `P_CO` / `P_ADV_*` / `P_UG` | Class slices (report within `P_IND` primarily) |
| `P_B` | Phase-B fixture (= complete Phase-A set + pinned PT extras) |

---

## 2. Phase-A primary quality metrics (Stage-6 continuity)

Compute **primarily on `P_IND`**. Also report full-set and side-slice tables.

### 2.1 False-duplicate rate (FP)

\[
\mathrm{FDR} = \frac{|\{p \in P_{GT=DISTINCT} : \mathrm{Pred}(p)=\mathsf{duplicate}\}|}{|P_{GT=DISTINCT}|}
\]

**SUCCESS ceiling (P_IND):** ≤ **0.05**

### 2.2 Missed-duplicate rate (FN)

\[
\mathrm{MDR} = \frac{|\{p \in P_{GT=DUP} : \mathrm{Pred}(p)\neq\mathsf{duplicate}\}|}{|P_{GT=DUP}|}
\]

Strict: `ambiguous` counts as miss. Secondary: `MDR_hard` counts only Pred=`distinct`.

**SUCCESS ceiling:** ≤ **0.05**

### 2.3 Distinct-preservation rate

\[
\mathrm{DPR} = \frac{|\{p \in P_{GT=DISTINCT} : \mathrm{Pred}(p)=\mathsf{distinct}\}|}{|P_{GT=DISTINCT}|}
\]

Secondary: `DPR_retain` counts Pred ∈ {`distinct`, `ambiguous`}.

**SUCCESS floor:** DPR ≥ **0.95** **or** (DPR_retain ≥ **0.95** ∧ FDR ≤ **0.05** ∧ AR ≤ **0.20**)

### 2.4 Duplicate-collapse rate

\[
\mathrm{DCR} = \frac{|\{p \in P_{GT=DUP} : \mathrm{Pred}(p)=\mathsf{duplicate}\}|}{|P_{GT=DUP}|}
\]

**SUCCESS floor:** ≥ **0.95** on TD ∪ TDBE ∪ ADV_TS within `P_IND`

### 2.5 Ambiguity rate

\[
\mathrm{AR} = \frac{|\{p : \mathrm{Pred}(p)=\mathsf{ambiguous}\}|}{|P|}
\]

**SUCCESS ceiling:** ≤ **0.20** on `P_IND`

---

## 3. Context coverage metric

| Metric | Definition | SUCCESS |
|--------|------------|---------|
| `context_family_coverage` | Fraction of required families {BASELINE_IDENTITY, TRANSFORMED, BOUNDARY, COMPOSITION, ORDERING, STATE_CONTEXT} with ≥1 `INDEPENDENT` pair whose audit touches that family | **1.0** |
| `novel_context_used_rate` | Fraction of Pred evidence contexts from novel subset (informational) | report; no hard floor beyond bank construction rules |

---

## 4. Cost metrics (first-class)

| Metric | Definition |
|--------|------------|
| `calls_per_pair` | apply_micro count per pair per mechanism |
| `calls_mean` / `calls_median` / `calls_max` / `calls_worst` | Distribution over `P_IND` (worst = max) |
| `calls_total` | Sum over Phase run |
| `budget_utilization` | `calls_total / S7_MAX_TOTAL_APPLY_MICRO_RUN_*` |
| `expansion_calls_mean` | R-C/R-D Stage-2 / reserve only |
| `sacred_bh_draws` | Must be **0** |

**Practicality ceiling (ranking):** mean ≤ **4.0** and worst-case ≤ **24**. Breach with accuracy SUCCESS → gate **COST_IMPRACTICAL** (not ranked as live-consideration SUCCESS).

Excellent accuracy + unbounded/impractical cost → classify COST_IMPRACTICAL / FAILED if caps violated without `ambiguous` policy.

---

## 5. Diagnostic / contamination metrics

| Metric | Definition | Use |
|--------|------------|-----|
| `sdiag_hard_collapse` | 1 if Pred=`duplicate` on `S7-SDIAG-*` GT-DISTINCT else 0 | conflict report; **not** selection |
| `related_FDR` / `related_DCR` | Rates on `P_REL` | side table |
| `replay_agreement_with_stage6` | Fraction of `P_REPLAY` Pred matching Stage-6 recorded Pred for same mechanism | continuity |
| `independence_purity` | 1 if no `RELATED` counted in primary numerators | must be 1 |

---

## 6. Phase-B equivalence metrics

| Metric | Definition | SUCCESS |
|--------|------------|---------|
| `mismatch_rate` | Fraction of `P_B` with offline≠executable on required fields | **0** |
| `label_mismatch_count` | Count of label disagreements | **0** |
| `ambiguity_mismatch_count` | Count | **0** |
| `provenance_mismatch_count` | Count on preregistered keys | **0** |
| `cost_mismatch_count` | Count | **0** |
| `property_tests_passed` | Vector of PT-* | all promised PASS |
| `pipeline_mutation` | bool | **false** |
| `filter_replaced` | bool | **false** |
| `grow_py_diff_empty` | bool | **true** (default path) |

---

## 7. Degeneracy detectors (automatic FAIL)

| Detector | Trip condition |
|----------|----------------|
| `ALL_DISTINCT` | DCR == 0 and DPR == 1 on `P_IND` |
| `ALL_DUPLICATE` | DCR == 1 and DPR == 0 among compared |
| `ALL_AMBIGUOUS` | AR == 1 |
| `TEXTUAL_ONLY` | Decisions equal textual_identity on adversarial set while disagreeing with GT behavioral labels |
| `CRITICAL_ONLY_GAIN` | Improves only `P_SDIAG`/`P_REL` vs BASELINE while `P_IND` FDR/DCR worsen beyond thresholds |
| `RELATED_AS_INDEPENDENT` | Primary rates include `RELATED` pairs |
| `SACRED_BUDGET_TOUCH` | `sacred_bh_draws > 0` |
| `TARGET_SPECIAL_CASE` | Branch on odd-stride / CAT-self / S / critical body keys |
| `POSTHOC_PAIR_ADD` | Pair/context added after outcome inspection |
| `SILENT_SPEC_PATCH` | Offline or executable edited mid-flight to force Phase-B agree |
| `LIVE_INTEGRATION` | `filter_replaced` or discovery import of repair |

Any trip → gate **FAILED** (H7-REJECT path).

---

## 8. Fair ablation / ranking schemas

### 8.1 Phase-A ablation row

```json
{
  "schema": "aivd340-stage7-phaseA-ablation-1",
  "mechanism": "BASELINE|R-A|R-B|R-C|R-D",
  "population": "INDEPENDENT",
  "n_pairs": 0,
  "FDR": 0.0,
  "MDR": 0.0,
  "MDR_hard": 0.0,
  "DPR": 0.0,
  "DPR_retain": 0.0,
  "DCR": 0.0,
  "AR": 0.0,
  "context_family_coverage": 0.0,
  "adv_ts_collapse": 0.0,
  "adv_td_hard_collapse": 0.0,
  "calls_mean": 0.0,
  "calls_median": 0.0,
  "calls_max": 0.0,
  "calls_worst": 0.0,
  "calls_total": 0,
  "budget_utilization": 0.0,
  "sacred_bh_draws": 0,
  "degeneracy_flags": [],
  "diagnostic_conflict": false,
  "gate": "SUCCESS|COST_IMPRACTICAL|PARTIAL|FAILED|INCONCLUSIVE",
  "autonomous_discovery_credit": false,
  "claim_label": "OFFLINE_GENERALIZATION_BENCH"
}
```

### 8.2 Phase-B equivalence row

```json
{
  "schema": "aivd340-stage7-phaseB-equivalence-1",
  "mechanism": "R-A|R-B|R-C|R-D",
  "n_pairs": 0,
  "mismatch_rate": 0.0,
  "label_mismatch_count": 0,
  "ambiguity_mismatch_count": 0,
  "provenance_mismatch_count": 0,
  "cost_mismatch_count": 0,
  "property_tests_passed": {},
  "pipeline_mutation": false,
  "filter_replaced": false,
  "grow_py_diff_empty": true,
  "calls_total_offline": 0,
  "calls_total_exec": 0,
  "sacred_bh_draws": 0,
  "gate": "SUCCESS|FAILED|PARTIAL",
  "autonomous_discovery_credit": false,
  "claim_label": "IMPL_SPEC_EQUIVALENCE"
}
```

### 8.3 Ranking rule (preregistered)

Among Phase-A gates:

1. Prefer `SUCCESS` over `COST_IMPRACTICAL` over `PARTIAL` over others  
2. Within same gate: lower `calls_mean`, then lower `calls_worst`, then lower AR  
3. Ties → **multi-candidate retain** (do not arbitrary single pick)  
4. Never rank by `sdiag_*` alone  

---

## 9. Aggregate gate functions (binding)

### Phase A

```text
if degeneracy or sacred_bh_draws>0 or target-special-case or RELATED_AS_INDEPENDENT or live-integration:
    FAILED
elif DCR>=0.95 and FDR<=0.05 and MDR<=0.05 and AR<=0.20
     and adv_ts_collapse>=0.95 and adv_td_hard_collapse<=0.05
     and context_family_coverage==1.0
     and no target-specific rule
     on P_IND:
    if calls_mean<=4.0 and calls_worst<=24:
        SUCCESS
    else:
        COST_IMPRACTICAL
elif material improvement vs BASELINE on P_IND without degeneracy:
    PARTIAL
else:
    INCONCLUSIVE or FAILED per missing controls
```

### Phase B

```text
if pipeline_mutation or filter_replaced or sacred_bh_draws>0 or silent-spec-patch:
    FAILED
elif mismatch_rate==0 and promised property tests PASS and isolation audit PASS:
    SUCCESS
else:
    FAILED
```

---

## 10. Mapping to charter distinctions

| Distinction | Operationalization |
|-------------|---------------------|
| Benchmark overfitting | Stage-6 SUCCESS cited **and** Phase-A `P_IND` gate FAILED/INCONCLUSIVE (H7b) |
| Genuine generalization | Phase-A SUCCESS/COST_IMPRACTICAL on `P_IND` without H7-REJECT (H7a) |
| Implementation/specification mismatch | Phase-B `mismatch_rate > 0` (H7c FAIL) |

---

## 11. Explicit non-goals

- Using Sacred pass/fail as a metric  
- Optimizing only S diagnostic  
- Counting invent/discovery credit  
- Silent exclusion of failed independent classes  
- Forcing a single winner when tied  

---

## 12. Final gate (design)

```
STAGE-7 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

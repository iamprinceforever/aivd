# AIVD 3.40 Stage-6 — Metrics Specification

**Document type:** Stage-6 metrics spec (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:25 IST  
**Parent charter:** `reports/aivd_3_40_stage6_charter.md`  
**Companions:** preregistration, equivalence_repair_spec, matrix  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 0. Mandate

Preregister **how** Stage-6 offline repair evaluation measures success — dual retention (duplicate + novelty), FP/FN, cost, degeneracy — **before** seeing repair outcomes. Metrics must not reduce to “critical pair survives” or “S passes.”

---

## 1. Units & populations

| Symbol | Meaning |
|--------|---------|
| Pair | Ordered evaluation unit `(body_a, body_b)` under frozen condition_id |
| GT | Ground truth ∈ {`DUP`, `DISTINCT`} with `MIXED`→treat as `DISTINCT` for hard-collapse prohibition (repair_spec §4) |
| Pred | Mechanism label ∈ {`duplicate`, `distinct`, `ambiguous`} |
| Mechanism | `BASELINE` \| `R-A` \| `R-B` \| `R-C` \| `R-D` |
| Call | One `apply_micro(prompt, body)` invocation counted toward Stage-6 experimental budget |

Populations (disjoint reporting; some pairs may appear in diagnostic dual-role with explicit matrix flag):

| Population | Membership |
|------------|------------|
| `P_TD` | TRUE_DUP pairs |
| `P_ND` | KNOWN_NONDUP pairs |
| `P_CD` | CONTEXT_DEPENDENT pairs |
| `P_UG` | U_GOOD pairs |
| `P_ADV_TS` | ADV_TEXT_DIFF_BEH_SAME |
| `P_ADV_TD` | ADV_TEXT_SIM_BEH_DIFF |
| `P_HO` | HELD_OUT_CRITICAL (diagnostic; usually n=1) |
| `P_ALL` | All non-diagnostic-only bench pairs used for primary rates (matrix defines inclusion) |

---

## 2. Primary quality metrics

### 2.1 False-duplicate rate (FP)

\[
\mathrm{FDR} = \frac{|\{p \in P_{GT=DISTINCT} : \mathrm{Pred}(p)=\mathsf{duplicate}\}|}{|P_{GT=DISTINCT}|}
\]

**Charter name:** false-duplicate rate.  
**SUCCESS ceiling:** ≤ **0.05** on `P_ALL` ground-truth DISTINCT (prereg).

### 2.2 Missed-duplicate rate (FN)

\[
\mathrm{MDR} = \frac{|\{p \in P_{GT=DUP} : \mathrm{Pred}(p)\neq\mathsf{duplicate}\}|}{|P_{GT=DUP}|}
\]

Count `ambiguous` as miss for MDR (strict). Report also `MDR_hard` counting only Pred=`distinct` as miss (secondary).

**SUCCESS ceiling:** ≤ **0.05** (strict MDR).

### 2.3 Distinct-preservation rate

\[
\mathrm{DPR} = \frac{|\{p \in P_{GT=DISTINCT} : \mathrm{Pred}(p)=\mathsf{distinct}\}|}{|P_{GT=DISTINCT}|}
\]

Secondary: `DPR_retain` counts Pred ∈ {`distinct`, `ambiguous`} as preserved (novelty retained / not hard-collapsed).

**SUCCESS floor:** DPR ≥ **0.95** **or** (DPR_retain ≥ **0.95** **and** FDR ≤ **0.05** with ambiguity rate within ceiling). Primary gate uses charter: known non-dups distinguishable; context-dependent distinctions preserved — operationalized as FDR ceiling + no hard-collapse on `P_CD` ∪ `P_HO`.

### 2.4 Duplicate-collapse rate

\[
\mathrm{DCR} = \frac{|\{p \in P_{GT=DUP} : \mathrm{Pred}(p)=\mathsf{duplicate}\}|}{|P_{GT=DUP}|}
\]

**SUCCESS floor:** ≥ **0.95** on `P_TD` (and `P_ADV_TS`).

### 2.5 Ambiguity rate

\[
\mathrm{AR} = \frac{|\{p \in P_{ALL} : \mathrm{Pred}(p)=\mathsf{ambiguous}\}|}{|P_{ALL}|}
\]

**SUCCESS ceiling:** ≤ **0.20**. Maximizing AR to hide errors = failure (degeneracy).

---

## 3. Diagnostic metrics (held-out / class)

| Metric | Definition | SUCCESS |
|--------|------------|---------|
| `critical_hard_collapse` | 1 if `S6-HO-CRIT` Pred=`duplicate` else 0 | **must be 0** |
| `critical_label` | Pred on `S6-HO-CRIT` | `distinct` or `ambiguous` only |
| `cd_hard_collapse_rate` | FDR restricted to `P_CD` | ≤ **0.05** |
| `adv_ts_collapse` | DCR on `P_ADV_TS` | ≥ **0.95** |
| `adv_td_hard_collapse` | FDR on `P_ADV_TD` | ≤ **0.05** |

**Forbidden:** using these diagnostic outcomes to retune families before lock; evaluate under freeze.

---

## 4. Cost & budget metrics

| Metric | Definition |
|--------|------------|
| `calls_per_pair` | apply_micro count per pair per mechanism |
| `calls_mean` / `calls_p50` / `calls_p95` | Distribution over `P_ALL` |
| `calls_total` | Sum over bench |
| `budget_utilization` | `calls_total / S6_MAX_TOTAL_APPLY_MICRO_RUN` |
| `expansion_calls_mean` | For R-C/R-D: Stage-2 / reserve calls only |
| `sacred_bh_draws` | Must be **0** |
| `compute_seconds` | Wall time optional secondary |

**Bound:** enforce hard stops from prereg §8; on hit, Pred=`ambiguous` (not auto `duplicate`).

---

## 5. Pool-expansion proxy (classification-only)

Without modifying promote-set fixtures:

| Metric | Definition |
|--------|------------|
| `pool_proxy_delta` | Relative change in count of candidates that would be **retained** under mechanism vs BASELINE on a frozen replay of Stage-4 full promote-set growth trace (artifact inputs only) |
| `false_retain_proxy` | Retained candidates that GT-audit would mark equivalent to an already-kept behavior (missed collapse) |
| `false_drop_proxy` | Dropped candidates that GT-audit would mark distinct from all kept behaviors (false duplicate) |

Proxy is **illustrative** for novelty vs collapse tradeoff; primary scientific claims use pair-benchmark rates above. Sacred not required.

---

## 6. Degeneracy detectors (automatic FAIL)

| Detector | Trip condition |
|----------|----------------|
| `ALL_DISTINCT` | DCR == 0 and DPR == 1 on `P_ALL` |
| `ALL_DUPLICATE` | DCR == 1 and DPR == 0 (among pairs compared) |
| `ALL_AMBIGUOUS` | AR == 1 |
| `TEXTUAL_ONLY` | Family decisions equal to `textual_identity` predictions on adversarial set while disagreeing with GT behavioral labels |
| `CRITICAL_ONLY_GAIN` | Improves only `P_HO` vs BASELINE while FDR/DCR on `P_TD`∪`P_ND` worsen beyond thresholds |
| `SACRED_BUDGET_TOUCH` | `sacred_bh_draws > 0` |
| `TARGET_SPECIAL_CASE` | Code/design branch on odd-stride / CAT-self / S / critical body keys |

Any trip → gate **FAILED** (H6-REJECT path) regardless of other averages.

---

## 7. Fair ablation table (required output schema)

Future EXECUTION results must include:

```json
{
  "schema": "aivd340-stage6-ablation-1",
  "mechanism": "BASELINE|R-A|R-B|R-C|R-D",
  "n_pairs": 0,
  "FDR": 0.0,
  "MDR": 0.0,
  "MDR_hard": 0.0,
  "DPR": 0.0,
  "DPR_retain": 0.0,
  "DCR": 0.0,
  "AR": 0.0,
  "critical_hard_collapse": 0,
  "adv_ts_collapse": 0.0,
  "adv_td_hard_collapse": 0.0,
  "calls_mean": 0.0,
  "calls_total": 0,
  "budget_utilization": 0.0,
  "sacred_bh_draws": 0,
  "degeneracy_flags": [],
  "autonomous_discovery_credit": false,
  "claim_label": "OFFLINE_REPAIR_BENCH"
}
```

Compare mechanisms only under identical `n_pairs`, GT labels, seeds, and bank hash.

---

## 8. How FP/FN map to charter language

| Charter phrase | Metric |
|----------------|--------|
| False duplicates | FDR (Pred=`duplicate` \| GT=`DISTINCT`) |
| Missed duplicates | MDR (Pred≠`duplicate` \| GT=`DUP`) |
| Novelty retention | DPR / DPR_retain + `cd_hard_collapse_rate` + critical diagnostic |
| Duplicate retention | DCR (+ adv_ts_collapse) |
| Not everything novel / everything collapsed | Degeneracy detectors |

---

## 9. Aggregate gate function (binding)

```text
if any degeneracy detector trips or sacred_bh_draws>0 or target-special-case:
    FAILED
elif DCR>=0.95 and FDR<=0.05 and MDR<=0.05 and AR<=0.20
     and critical_hard_collapse==0
     and adv_ts_collapse>=0.95 and adv_td_hard_collapse<=0.05
     and no target-specific rule:
    SUCCESS
elif material improvement vs BASELINE on FDR or critical class
     without degeneracy and without Sacred touch:
    PARTIAL
else:
    INCONCLUSIVE or FAILED per missing controls / recorder gaps
```

SUCCESS still requires charter qualitative items (fair ablation, generic mechanism, budget honesty).

---

## 10. Explicit non-goals

- Using Sacred pass/fail as a metric  
- Optimizing only `S6-HO-CRIT`  
- Counting invent/discovery credit  
- Silent exclusion of failed adversarial pairs  

---

## 11. Final gate (design)

```
STAGE-6 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

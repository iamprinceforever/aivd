# AIVD 3.40 Stage-9 — Metrics Specification

**Document type:** Stage-9 metrics spec (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 21:26 IST  
**Parent charter:** `reports/aivd_3_40_stage9_charter.md`  
**Companions:** analysis_spec, trajectory_schema, preregistration, data_availability  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 0. Mandate

Preregister **how** Stage-9 measures (1) evidence integrity, (2) trajectory coverage, (3) earliest disappearance, (4) fate dominance, (5) repair divergence, (6) hypothesis confidence, (7) instrumentation gaps — **before** running the offline audit. Metrics must not reduce to “S VERIFIED” and must not invent fields.

---

## 1. Units & populations

| Symbol | Meaning |
|--------|---------|
| Condition | `S8-BASELINE` \| `S8-RA` \| `S8-RC` \| `S8-RD` |
| Seed | ∈ `[0,1,2,3,4,7,11]` |
| Cell | (condition, seed) — N=28 |
| Waypoint | W01…W13 per trajectory_schema |
| Fate | A…I |
| ObsState | OBSERVED \| NOT_OBSERVED \| NOT_RECORDED \| NOT_APPLICABLE |

Populations:

| Population | Membership |
|------------|------------|
| `P_ALL` | All 28 cells |
| `P_SEED[s]` | 4 conditions at seed s |
| `P_COND[c]` | 7 seeds under condition c |
| `P_BASE` | 7 baseline cells |
| `P_REPAIR` | 21 repair cells |

---

## 2. Axis 1 — EVIDENCE INTEGRITY

| Metric | Definition | PASS |
|--------|------------|------|
| `stage8_tip_match` | Analysis inputs match Stage-8 COMPLETE tip `a447649` content | **true** |
| `no_field_invention` | Audit log contains zero synthesized rank/score/select/compose-attempt rows | **true** |
| `namespace_separation` | CONTROLLED_FILTER claims not written into AUTONOMOUS causal table | **true** |
| `h9_reject` | H9-REJECT supported? | must be **false** for SUCCESS |

Axis 1 FAIL → do not publish causal localization as scientific SUCCESS.

---

## 3. Axis 2 — TRAJECTORY COVERAGE

| Metric | Definition | PASS |
|--------|------------|------|
| `cells_reconstructed` | Count cells with complete waypoint table | **== 28** |
| `seed_first_done` | Per-seed analyses exist before pooled invariants | **true** |
| `obsstate_tag_rate` | Fraction of waypoint cells with a valid ObsState | **== 1.0** |

---

## 4. Axis 3 — EARLIEST DISAPPEARANCE

| Metric | Definition |
|--------|------------|
| `earliest_waypoint[cell]` | First waypoint where S-direction progress NOT_OBSERVED with priors not NOT_RECORDED |
| `earliest_waypoint_mode` | Modal earliest waypoint across `P_ALL` (report ties) |
| `earliest_invariant` | Waypoint that is earliest in ≥5/7 seeds for all conditions |
| `blocked_by_instrumentation` | True if earliest honest claim is NOT_RECORDED prior stage |

**PASS (reporting):** earliest_waypoint_mode emitted with confidence label; if blocked_by_instrumentation, H9i scored ≠ AGAINST without forcing a fake locus.

---

## 5. Axis 4 — FATE DOMINANCE

| Metric | Definition | Constraint |
|--------|------------|------------|
| `D_rate[c]` | Reproduce Stage-8 D_rate | Must remain **0.0** (preserve) |
| `fate_hist[c]` | Counts A…I over tracked bodies | Report |
| `dominant_fate[c]` | argmax fate_hist | Report |
| `E_without_selection_reason` | dominant E ∧ selection reason NOT_RECORDED | If true → H9e **INCONCLUSIVE** |

Do **not** define PASS as “E explained.” Honesty about missing selection reason is the metric.

---

## 6. Axis 5 — REPAIR-INDUCED DIVERGENCE

| Metric | Definition |
|--------|------------|
| `diff_waypoint[seed, family]` | Earliest OBSERVED S-trajectory / fate / s_predicate diff vs BASELINE |
| `n_seeds_with_diff[family]` | Seeds with non-null diff_waypoint excluding ledger_only |
| `null_divergence_label` | Emitted iff n_seeds_with_diff==0 for all families |

**PASS forms:**

- Either concrete earliest diffs reported per family, **or**  
- Exact label: `NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE`

Manufactured diffs → Axis 1 FAIL / H9-REJECT.

---

## 7. Axis 6 — HYPOTHESIS SCORING

For each leaf ∈ {H9a…H9i, H9D, H9-REJECT}:

| Field | Required |
|-------|----------|
| `observed_evidence` | list |
| `counter_evidence` | list |
| `missing_evidence` | list |
| `alternatives` | list |
| `confidence` | SUPPORTED \| WEAKLY SUPPORTED \| INCONCLUSIVE \| AGAINST |

Aggregate metrics:

| Metric | Definition |
|--------|------------|
| `strongest_set` | Leaves with best non-REJECT confidence favoring localization |
| `h9d_scoped_against` | True if H9D confidence==AGAINST with scoped language present |
| `single_root_forced` | True if audit claims unique root cause without evidence → FAIL |

**PASS:** all leaves scored; single_root_forced==false; forbidden confidence words absent.

---

## 8. Axis 7 — GAP REPORT

| Metric | Definition | PASS |
|--------|------------|------|
| `not_recorded_fields` | Inventory from data_availability | non-empty list allowed |
| `leaves_blocked` | H9 leaves INCONCLUSIVE due to NOT_RECORDED | listed |
| `new_experiment_proposed_inside_stage9` | Boolean | must be **false** |

---

## 9. S-diagnostic metrics (report-only)

| Metric | Definition |
|--------|------------|
| `s_verified_count[c]` | From Stage-8 (expect 0) |
| `s_diag_true_count[c]` | Cells with odd_cat_self_in_records true |
| `unresolved_invisible_count` | Cells with that terminal |

These **do not** define Stage-9 SUCCESS alone.

---

## 10. Cross-seed metrics

| Metric | Definition |
|--------|------------|
| `invariant_rate` | Fraction of seeds sharing earliest_waypoint_mode |
| `seed_exception_list` | Seeds disagreeing with mode |
| `condition_commonality` | Patterns identical on all four conditions |

---

## 11. H9D scoped metric language (binding)

If `D_rate==0` and no S-body duplicate removal OBSERVED:

```
H9D confidence = AGAINST
language = "not observed as active bottleneck in Stage-8 autonomous S matrix"
forbidden = "never can be a bottleneck" | "H5b invalidated"
```

---

## 12. Overall conclusion mapping

| Label | Metric rule (sketch) |
|-------|----------------------|
| SUCCESS | Axes 1–2 PASS; axes 3–7 reported honestly; H9-REJECT not supported; answers charter (1)–(7) |
| PARTIAL | Axis 1–2 PASS; multiple causal leaves INCONCLUSIVE via NOT_RECORDED; localization partial |
| FAILED | Axis 1 FAIL or H9-REJECT supported |
| INCONCLUSIVE | Protocol ok but instrumentation blocks all earliest-locus claims |

---

## 13. STOP

Metrics only. Do not compute result tables in this design commit.

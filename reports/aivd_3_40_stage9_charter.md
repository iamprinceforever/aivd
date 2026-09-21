# AIVD 3.40 Stage-9 DESIGN CHARTER — Autonomous S Visibility / Trajectory Localization (Design Only)

**Document type:** Stage-9 DESIGN CHARTER (DOCS ONLY — **NOT EXECUTED / NOT ANALYZED**)  
**Recorded:** 2026-09-21 21:26 IST  
**Start tip:** `a447649` (`research/aivd-3.40-budget-representation-frontier`)  
**Stage-8 COMPLETE tip:** `a447649` (PARTIAL — integration+semantics PASS; axis-3 null; S verified 0/7; D=0 all conditions; `UNRESOLVED_INVISIBLE`)  
**Stage-8 design freeze:** `129a2e9`  
**Stage-7 COMPLETE tip:** `079d66f` / design `d0ef7b6`  
**Authority priors (cite; do not weaken):** Stage-8 results `a447649` / design `129a2e9`; Stage-7 `079d66f` / `d0ef7b6`; Stage-6 `000a4d8` / `ac152c6`; Stage-5 `c003e60` / `2496857` (H5b FALSE_DUPLICATE; H5d context-dependent); Stage-4 `4005e66` / `27e9e88` (H2c `FILTER_BEHAVIORAL_DUP`); Stage-2 `dcae889`; Phase-2 `f4d7a2b`; Phase-1 `a2ab0cc`; R1b caveat `7a3457e`; AIVD 3.38 / 3.39 Sacred baselines (historical reference only)  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** **STAGE-9 DESIGN READY: OFFLINE TRAJECTORY AUDIT REQUIRES SEPARATE AUTHORIZATION**

Companion deliverables (this commit, `reports/` only):

1. `aivd_3_40_stage9_charter.md` — **this file**
2. `aivd_3_40_stage9_hypothesis_tree.md`
3. `aivd_3_40_stage9_matrix.json`
4. `aivd_3_40_stage9_preregistration.md`
5. `aivd_3_40_stage9_analysis_spec.md`
6. `aivd_3_40_stage9_trajectory_schema.md`
7. `aivd_3_40_stage9_metrics.md`
8. `aivd_3_40_stage9_data_availability.md` (optional companion — missing-field inventory)

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Stage-9 scope (this commit) | **DESIGN documents only** under `reports/` |
| No live filter mod | Do **not** edit `grow.py`, `_keep`, `FILTER_BEHAVIORAL_DUP`, discovery pipeline, promote-set, firewall, verify, invent, propose_atoms |
| No execution | No Sacred, no TinyLlama, no Stage-9 plant runs, no merge of any repair into live growth, **no offline analysis execution in this commit** |
| No historical mutation | Do **not** modify Stage-8/7/6/5/4 / Phase-2/1 / Stage-2/3 reports or 3.38/3.39 baselines; do **not** rewrite Stage-8 PARTIAL conclusions |
| No repair retune | Preserve multi-candidate survivors **R-A / R-C / R-D**; do **not** select one winner; do **not** retune R-A/R-C/R-D; do **not** revive R-B |
| No merge of phenomena | Keep **CONTROLLED FILTER PHENOMENON** (Stage-4 odd-stride / Stage-5 FALSE_DUPLICATE) **separate** from **AUTONOMOUS DISCOVERY FAILURE** (Stage-8) |
| Scientific objective | Offline forensic localization of where **autonomous S** becomes invisible / ceases progress — **NOT** “make S pass”; **NOT** “prove equivalence filter caused Stage-8 failure” |
| Primary question (exact) | Where does autonomous S disappear before equivalence filtering, and which causal hypothesis best explains that disappearance? |
| Evidence lock | **Already-recorded Stage-8 evidence only** (28 cells). Do **not** manufacture missing fields. Do **not** infer selection/ranking if not recorded. Do **not** invent new experiments to fill gaps |
| Missing data | If insufficient → report missing instrumentation. Do **not** compensate with a new experiment in Stage-9 |
| Single root cause | **NOT required.** Valid outcome: “localizes to X but cannot distinguish Y from Z because selection/ranking not recorded.” |
| STOP | Offline trajectory audit / any new Sacred / live `_keep` wiring / plant execution / analysis run requires a **separate EXECUTION authorization** |

If a “design” proposal would re-run Sacred, retune R-A/R-C/R-D, merge controlled Stage-4 D-fate with autonomous Stage-8 null into one causal claim, convert `NOT_RECORDED` into failure, raise BH / invent_cap, lower firewall floor, modify Stage-8 results, or define success solely as S VERIFIED → **STOP** (revise; do not ship).

---

## 1. Why Stage-9 (post Stage-8)

### 1.1 Stage-8 COMPLETE priors (immutable cite — do not inflate)

| Prior | Status |
|-------|--------|
| Case | **PARTIAL** — axes 1–2 PASS; axis-3 **null**; axes 4–6 reported |
| Matrix | 28 cells = 4 conditions × 7 seeds `[0,1,2,3,4,7,11]` |
| S verified | **0/7** every condition (BASELINE / R-A / R-C / R-D) |
| D (equiv removal) | **0** all conditions / all seeds (`D_rate=0.0`) |
| Terminal | `TerminalState.UNRESOLVED_INVISIBLE` (all reported) |
| Dominant pool fate | **E** among pool survivors; **H** for rediscovery-origin bodies |
| Axis-2 / Axis-5 | **PASS** |
| Axis-3 | **NULL** (no δ≥0.05 D_rate reduction; baseline D already 0) |
| H8a / H8d | supported |
| H8b / H8c | not_supported |
| H8e | report_only_null_ok |
| H8f | applicable |
| H8-REJECT | not_supported |
| Surviving set | `['S8-RA', 'S8-RC', 'S8-RD']` (integration-valid; **not** axis-3 winners) |
| Critical observation | **Autonomous S plants never hit live equivalence-dup removal** — Stage-4/5 bottleneck is **NOT** expressed as fate **D** in Stage-8 |
| Epistemic fence | Stage-8 does **NOT** establish equivalence filtering as cause of autonomous S failure; does **NOT** invalidate controlled FALSE_DUPLICATE (Stage-5 H5b). Keep separate. |

**Stage-8 epistemic boundary (binding):**

> Stage-8 established that live integration of R-A / R-C / R-D is valid and discovery semantics are preserved, but produced **no** threshold-meeting mechanism change at the equivalence stage because **D was already zero** under BASELINE autonomous plants. Autonomous S remained unverified (`UNRESOLVED_INVISIBLE`). That is **not** evidence that Stage-4/5 FALSE_DUPLICATE is false; it is evidence that the **autonomous S trajectory never reached the equivalence-removal waypoint** as an observed fate D. Stage-9 designs the **offline forensic audit** that localizes the earliest disappearance — it does **not** re-litigate Stage-5, does **not** authorize new plants, and does **not** execute the audit in this commit.

### 1.2 Primary scientific question (binding)

> Where does autonomous S disappear before equivalence filtering, and which causal hypothesis best explains that disappearance?

Operationalized: from already-recorded Stage-8 trajectories (plus historical reference trajectories cited as **reference only**), reconstruct the earliest observable stage at which progress toward the previously observed S behavioral direction ceases or becomes invisible, then score H9a…H9i / H9D / H9-REJECT under evidence standards that preserve `NOT_RECORDED`.

### 1.3 What Stage-9 is NOT

- Not a cure for S / not “make S pass”
- Not authorization to execute the offline audit **in this commit**
- Not a Stage-8 re-litigation that weakens PARTIAL / axis-1–2 PASS / D=0
- Not a collapse of CONTROLLED Stage-4/5 D-fate into AUTONOMOUS Stage-8 null
- Not invalidation of Stage-5 H5b FALSE_DUPLICATE
- Not forced single-winner selection among R-A / R-C / R-D
- Not R-B revival / retune / budget cheating
- Not new Sacred / TinyLlama / live `_keep` replacement
- Not mutation of 3.38 / 3.39 / Stage-2–8 historical artifacts
- Not manufacture of ranking/score/selection evidence absent from records

---

## 2. Analysis mode (offline forensic only)

| Mode | Binding |
|------|---------|
| Kind | **OFFLINE TRAJECTORY AUDIT** of already-recorded Stage-8 evidence |
| New plants / Sacred | **Forbidden** under Stage-9 design authorization |
| New instrumentation hooks in grow.py | **Forbidden** in this stage (gaps → report missing instrumentation) |
| Counterfactual simulation of unrecovered fields | **Forbidden** |
| Historical references (3.38 S; Stage-2; Phase-1/2; Stage-4 controlled odd-stride) | **Reference only** — compare for earliest-divergence; do not rewrite |
| Output | Localization report + hypothesis scores + missing-instrumentation inventory |

Full protocol: `reports/aivd_3_40_stage9_analysis_spec.md`.  
Trajectory vocabulary: `reports/aivd_3_40_stage9_trajectory_schema.md`.  
Metric definitions: `reports/aivd_3_40_stage9_metrics.md`.  
Data availability: `reports/aivd_3_40_stage9_data_availability.md`.

---

## 3. Evidence sources (locked)

Prefer, in order:

1. `reports/aivd_3_40_stage8_results.md` + `.json`
2. `reports/aivd_3_40_stage8_mechanism_evidence.json`
3. `reports/aivd_3_40_stage8_discovery_evidence.json`
4. `reports/aivd_3_40_stage8_rediscovery_evidence.json`
5. `reports/aivd_3_40_stage8_recursion_evidence.json`
6. `reports/aivd_3_40_stage8/runs/S8-{BASELINE,RA,RC,RD}_seed{0,1,2,3,4,7,11}.json` (28 trajectory artifacts)
7. Stage-8 companions as needed for schema continuity (`fresh_plant_isolation`, `execution_stamp`, controls)

**Cite-only (not Stage-9 primary data):** Stage-4/5 results (controlled vs autonomous separation); Stage-2 / Phase-1 / Phase-2 / 3.38 S trajectory (historical reference for earliest-divergence).

**Forbidden:** future experiments; manufactured fields; inferred selection/ranking when absent; edits to Stage-8 artifacts.

---

## 4. Trajectory reconstruction mandate

Per seed × condition where observed, reconstruct waypoints:

```
INVENTION → LANGUAGE GROWTH → ATOM/BODY IDENTITY → COMPOSITION →
CANDIDATE CREATION → POOL ENTRY → EQUIVALENCE DECISION → SURVIVAL →
SELECTION → VERIFICATION → REDISCOVERY → RECURSION → STOPPING STATE
```

Observation states (binding; see schema):

| State | Meaning |
|-------|---------|
| **OBSERVED** | Explicitly present in Stage-8 recorded evidence |
| **NOT_OBSERVED** | Explicitly recorded as absent / false / zero when the instrument could see it |
| **NOT_RECORDED** | Stage that the Stage-8 recorder did not capture (instrumentation gap) |
| **NOT_APPLICABLE** | Downstream of an earlier hard stop; or irrelevant under recorded fate |

**Binding:** Do **not** convert `NOT_RECORDED` into failure. Do **not** convert absence-from-report into “did not occur.” Do **not** infer selection/ranking if not recorded → H9e remains **INCONCLUSIVE** when ranking/score/select detail absent.

---

## 5. Earliest-divergence method (summary)

Compare, per seed where possible:

1. Each Stage-8 condition vs Stage-8 **BASELINE** (primary within-matrix)
2. Stage-8 autonomous vs **3.38 S** trajectory (historical reference only)
3. Stage-8 autonomous vs Stage-2 / Phase-1 / Phase-2 reference points
4. Stage-8 autonomous vs Stage-4 **controlled** odd-stride (CONTROLLED vs AUTONOMOUS fence)

Find earliest BASELINE vs R-A vs R-C vs R-D divergence.  
If none observable: emit **`NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE`**. Do not manufacture.

Full procedure: analysis_spec § earliest-divergence.

---

## 6. Cross-seed method (summary)

1. Analyze **7 seeds separately first**
2. Then extract: invariants; seed-specific; repeated failure/success points; condition-specific diffs; evidence common to all four conditions
3. Do **not** pool in ways that hide seed-specific behavior

---

## 7. Fate analysis A–I (summary)

Preserve Stage-8 **D=0**. Quantify dominant unresolved path among recorded fates.  
Do **not** assume **E** is causal merely because common.  
If **E** dominates: ask whether the underlying non-selection reason is observable; if ranking/score/select absent → **H9e INCONCLUSIVE**.

---

## 8. Controlled vs autonomous (binding fence)

| Namespace | Source | Allowed Stage-9 use |
|-----------|--------|---------------------|
| `CONTROLLED_FILTER` | Stage-4 CONTROL B; Stage-5 critical pair / H5b | Cite as controlled phenomenon; **do not** claim it caused Stage-8 autonomous S failure |
| `AUTONOMOUS_DISCOVERY` | Stage-8 28 Sacred plants | Primary Stage-9 localization domain |
| `HISTORICAL_REFERENCE` | 3.38 / Stage-2 / Phase-1 / Phase-2 | Divergence reference only |

**H9D scoped claim (binding):** Stage-8 D=0 is evidence **AGAINST** “equivalence filter is the active autonomous S bottleneck **in this Stage-8 matrix**” — scoped as **not observed as active bottleneck**, **not** “never can be.”

---

## 9. Success criteria (design intent for future EXECUTION)

Reproducible offline analysis that can determine from Stage-8 evidence:

1. Earliest trajectory disappearance (or `NOT_RECORDED` localization with gap report)
2. Dominant fate (preserving D=0)
3. Cross-seed consistency / seed-specific exceptions
4. Repair-induced divergence **or** explicit `NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE`
5. Equivalence-filter involvement **or not** (H9D scored under scoped language)
6. Strongest supported hypothesis (or multi-hypothesis tie / INCONCLUSIVE set)
7. Missing instrumentation for unresolved leaves

**Single root cause NOT required.**

Valid success form: “localizes to X but cannot distinguish Y from Z because selection/ranking not recorded.”

| Label | Meaning |
|-------|---------|
| **SUCCESS** | Offline audit completes under freeze; answers (1)–(7) with evidence tags; H9-REJECT not supported |
| **PARTIAL** | Localization partial; multiple H9 leaves remain INCONCLUSIVE due to `NOT_RECORDED` |
| **FAILED** | Protocol violation; Stage-8 mutation; manufactured fields; controlled/autonomous merge into one causal claim; H9-REJECT supported |
| **INCONCLUSIVE** | Instrumentation gaps block honest separation even under correct protocol |

---

## 10. Frozen locks (unless charter revision before EXECUTION)

| Lock | Value |
|------|-------|
| Analysis kind | Offline forensic of Stage-8 evidence only |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` (Stage-8 freeze) |
| Conditions | `S8-BASELINE`, `S8-RA`, `S8-RC`, `S8-RD` |
| BH / invent_cap / REDISCOVERY_FLOOR | 48 / 48 / 5 (cite; do not change) |
| R-A / R-C / R-D | Frozen; no retune |
| R-B | EXCLUDED |
| grow.py / FILTER_BEHAVIORAL_DUP | IMMUTABLE |
| Stage-8 results artifacts | IMMUTABLE |
| 3.38 / 3.39 | IMMUTABLE |
| New Sacred / plants | Forbidden under Stage-9 |
| Confidence vocabulary | `SUPPORTED` \| `WEAKLY SUPPORTED` \| `INCONCLUSIVE` \| `AGAINST` — avoid PROVEN / DEFINITELY / ROOT CAUSE |

---

## 11. Hypothesis tree (pointer)

Leaves: **H9a** representation/invention; **H9b** language-growth; **H9c** composition; **H9d** candidate-pool; **H9e** candidate-selection; **H9f** verification; **H9g** rediscovery/firewall; **H9h** budget/stopping; **H9i** observation/instrumentation; **H9D** equivalence-filter-as-autonomous-bottleneck (scoped); **H9-REJECT**.

Full accept/reject rules: `reports/aivd_3_40_stage9_hypothesis_tree.md`.

---

## 12. Exact authorization required for Stage-9 EXECUTION

```
STAGE-9 EXECUTION AUTHORIZATION REQUIRED:
  OFFLINE TRAJECTORY AUDIT ONLY
  — no Sacred
  — no TinyLlama plant runs
  — no grow.py / FILTER_BEHAVIORAL_DUP / R-A/R-C/R-D modification
  — no merge of repairs
  — no mutation of Stage-8 results or 3.38/3.39
  — no new experiments to fill NOT_RECORDED gaps
```

This design commit does **not** grant that authorization.

---

## 13. Final gate (this commit)

```
STAGE-9 DESIGN READY: OFFLINE TRAJECTORY AUDIT REQUIRES SEPARATE AUTHORIZATION
```

---

## 14. Stopping

Stage-9 DESIGN only. Do **not** execute analysis. Do **not** auto-start Stage-10. Do **not** modify 3.38/3.39. Do **not** rewrite Stage-8. Do **not** retune R-A/R-C/R-D. Do **not** revive R-B without design revision.

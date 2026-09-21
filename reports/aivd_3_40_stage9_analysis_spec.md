# AIVD 3.40 Stage-9 — Offline Trajectory Analysis Specification

**Document type:** Stage-9 analysis spec (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 21:26 IST  
**Parent charter:** `reports/aivd_3_40_stage9_charter.md`  
**Companions:** preregistration, trajectory_schema, metrics, data_availability, hypothesis_tree, matrix  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 0. Mandate

Specify a **reproducible offline forensic procedure** that, when separately authorized, answers from Stage-8 evidence alone:

1. Earliest trajectory disappearance of autonomous S progress  
2. Dominant fate (preserving D=0)  
3. Cross-seed consistency  
4. Repair-induced divergence or its absence  
5. Equivalence-filter involvement or not (H9D scoped)  
6. Strongest supported hypothesis (or tie / INCONCLUSIVE set)  
7. Missing instrumentation for unresolved leaves  

Do **not** execute this procedure in the design commit.

---

## 1. Inputs (locked)

| ID | Path / glob | Role |
|----|-------------|------|
| R8 | `reports/aivd_3_40_stage8_results.{md,json}` | Aggregate gates, axes, hypotheses |
| M8 | `reports/aivd_3_40_stage8_mechanism_evidence.json` | A–I / D_rate / equiv counts |
| D8 | `reports/aivd_3_40_stage8_discovery_evidence.json` | Verify / terminals / s_diagnostic |
| RD8 | `reports/aivd_3_40_stage8_rediscovery_evidence.json` | H / independence / leak |
| RC8 | `reports/aivd_3_40_stage8_recursion_evidence.json` | I / recursion |
| RUNS | `reports/aivd_3_40_stage8/runs/S8-{BASELINE,RA,RC,RD}_seed{0,1,2,3,4,7,11}.json` | Per-cell trajectories |
| S4 | `reports/aivd_3_40_stage4_results.{md,json}` | CONTROLLED_FILTER cite |
| S5 | `reports/aivd_3_40_stage5_results.{md,json}` | H5b cite |
| REF | Stage-2 / Phase-1 / Phase-2 / 3.38 docs | HISTORICAL_REFERENCE only |

Integrity check (EXECUTION first step): confirm Stage-8 tip still `a447649` content hashes for R8/M8/D8/RD8/RC8/RUNS match recorded Stage-8 commit; abort if mutated → H9-REJECT.

---

## 2. Unit of analysis

| Unit | Definition |
|------|------------|
| Cell | `(condition_id, seed)` — 28 cells |
| Waypoint | Schema stage in `trajectory_schema.md` |
| Body of interest | Odd stride / odd CAT-self keys (prereg); plus any body labeled in mechanism.fates |
| Fate | A…I from Stage-8 mechanism continuity |
| Observation state | OBSERVED \| NOT_OBSERVED \| NOT_RECORDED \| NOT_APPLICABLE |

---

## 3. Procedure overview

```
P0  Integrity + data-availability inventory
P1  Per-cell trajectory reconstruction (seed × condition)
P2  Per-seed analysis (no pooling yet)
P3  Cross-seed invariants / exceptions
P4  Earliest-disappearance localization (S-direction)
P5  Fate dominance A–I (preserve D=0)
P6  Earliest repair-induced divergence (BASELINE vs R-*)
P7  Historical / controlled reference contrasts (fence namespaces)
P8  Hypothesis scoring H9a…H9i / H9D / H9-REJECT
P9  Gap report + final Stage-9 results artifacts
```

---

## 4. P0 — Integrity + data availability

1. Load `data_availability.md` checklist.  
2. For each required field class, mark AVAILABLE or MISSING against RUNS schema.  
3. Emit `NOT_RECORDED` list — these constrain H9e / H9b / H9c / H9i.  
4. Confirm no analysis step plans to invent MISSING fields.

---

## 5. P1 — Per-cell trajectory reconstruction

For each of 28 RUNS files:

1. Read top-level: `terminal_state`, `failure_class`, `stop_reason`, budget fields, `s_diagnostic`, `generation_record_summaries`, `mechanism`.  
2. Fill waypoint table per `trajectory_schema.md`.  
3. For S-direction body keys:  
   - If key appears in generation summaries / fates / equiv_decisions → OBSERVED presence.  
   - If `s_diagnostic.odd_cat_self_in_records` is explicitly false → odd CAT-self **NOT_OBSERVED** (instrument existed).  
   - If a finer invent-attempt log is absent → invent-rejection detail **NOT_RECORDED**.  
4. Equivalence: map `mechanism.equiv_decisions` + `n_pool_removed_D` → D OBSERVED counts (Stage-8 prior: 0).  
5. Selection: if only `n_selected` / fate E without rank/score → selection **outcome** may be OBSERVED as “not selected,” but **reason** NOT_RECORDED → H9e INCONCLUSIVE.  
6. Never backfill from Stage-4 controlled traces into the cell table.

Output row schema: see metrics § trajectory row.

---

## 6. P2 — Per-seed analysis (separate first)

For each seed `s ∈ {0,1,2,3,4,7,11}`:

1. Align four conditions’ waypoint tables for seed `s`.  
2. Record seed-local earliest S-direction NOT_OBSERVED / stop.  
3. Record seed-local BASELINE vs R-A/R-C/R-D diffs (if any).  
4. Do **not** average across seeds yet.

---

## 7. P3 — Cross-seed synthesis

After all seeds:

| Extract | Rule |
|---------|------|
| Invariants | Pattern true in 7/7 seeds × applicable conditions |
| Seed-specific | Pattern in ⊂ seeds; list seeds |
| Repeated failure points | Same waypoint failure ≥5/7 seeds |
| Condition-specific diffs | Diff present in some repair conditions only |
| Common-to-all-four | Identical across BASELINE+R-A+R-C+R-D |

Forbidden pooling: summing fates across seeds before listing seed-level disagreement.

---

## 8. P4 — Earliest disappearance (S-direction)

Definition: earliest waypoint W such that:

- Progress toward historical S behavioral direction is **NOT_OBSERVED** at W, **and**  
- All earlier waypoints are either OBSERVED success, NOT_APPLICABLE, or NOT_RECORDED (if NOT_RECORDED earlier, earliest **honest** claim is “blocked before W by instrumentation” → involve H9i).

Algorithm sketch:

1. Ordered waypoints: INVENTION → … → STOPPING_STATE.  
2. For S-direction predicates (prereg body keys + s_diagnostic):  
   - Walk forward; first NOT_OBSERVED with prior stages not NOT_RECORDED → candidate earliest locus.  
   - If prior stage NOT_RECORDED → emit localization confidence INCONCLUSIVE + H9i.  
3. Aggregate across seeds with invariant rules (§7).  
4. Separately note terminal envelope (`UNRESOLVED_INVISIBLE`, `BUDGET_EXHAUSTED`, `failure_class`) as **stopping state**, not automatically earliest locus.

---

## 9. P5 — Fate analysis A–I

1. Reproduce Stage-8 `fate_counts` / `per_condition_fates` from RUNS; confirm D=0.  
2. Dominant fate = mode among tracked bodies (report E/H priors).  
3. If dominant is **E**:  
   - Ask: is non-selection **reason** OBSERVED?  
   - If no rank/score/select ledger → mark underlying reason NOT_RECORDED; **do not** conclude selection policy caused S failure; score H9e INCONCLUSIVE.  
4. Preserve separation: fate D analysis for H9D; do not treat E as “equiv problem.”

---

## 10. P6 — Earliest-divergence (repair-induced)

Comparisons (in order):

1. **Primary:** For each seed, compare R-A / R-C / R-D waypoint tables to S8-BASELINE.  
2. Label first waypoint where observation state or S-direction predicates differ.  
3. If no seed shows any OBSERVED difference in S-direction trajectory / mechanism summaries beyond permitted repair-ledger fields (`repair_calls_total`, family label) → emit:

```
NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE
```

4. Do **not** manufacture divergence from narrative expectation that repairs “should” change outcomes.  
5. Axis-3 null / identical D_rate / identical terminals are **consistent with** the null label when trajectory tables match.

Secondary contrasts (namespaces HISTORICAL_REFERENCE / CONTROLLED_FILTER only):

- Stage-8 autonomous vs 3.38 S (reference)  
- Stage-8 autonomous vs Stage-2 / Phase-1 / Phase-2 reference  
- Stage-8 autonomous vs Stage-4 controlled odd-stride (expect **divergence of regime**: controlled hits FILTER_BEHAVIORAL_DUP; autonomous Stage-8 does not express D)

These secondary contrasts **must not** be labeled “repair-induced.”

---

## 11. P7 — Controlled vs autonomous fence (explicit step)

Emit a dedicated subsection:

| Claim | Verdict form |
|-------|--------------|
| Controlled Stage-4/5 equivalence bottleneck | Cite H2c / H5b — unchanged |
| Autonomous Stage-8 fate D involvement | Score H9D under scoped language |
| Unified causal claim merging both | **Forbidden** (H9-REJECT if emitted) |

---

## 12. P8 — Hypothesis scoring

For each leaf H9a…H9i, H9D, H9-REJECT:

```
observed_evidence: [...]
counter_evidence: [...]
missing_evidence: [...]
alternatives: [...]
confidence: SUPPORTED | WEAKLY SUPPORTED | INCONCLUSIVE | AGAINST
```

Rules:

- Prefer field-level citations (`runs/...json` paths + keys).  
- H9D: if D=0 and no S-body equiv removal → AGAINST scoped.  
- H9e: if selection reason NOT_RECORDED → INCONCLUSIVE.  
- Do not force single winner; report strongest set / ties.  
- If data insufficient for all causal leaves → strongest may be H9i + descriptive earliest NOT_OBSERVED waypoint.

---

## 13. P9 — Outputs (EXECUTION artifacts — not this commit)

When authorized, write (names suggested; final names in execution stamp):

- `reports/aivd_3_40_stage9_results.md`  
- `reports/aivd_3_40_stage9_results.json`  
- Optional: per-seed trajectory tables, hypothesis scorecard JSON  

Design commit must **not** create these result files.

---

## 14. Worked non-execution note (priors only)

Stage-8 COMPLETE priors already suggest (for auditors; **not** Stage-9 results):

- D=0 / n_duplicate=0 → H9D likely AGAINST scoped  
- `odd_cat_self_in_records=false` across cells → S-direction CAT-self NOT_OBSERVED  
- fate E + n_selected=0 without rank/score → H9e likely INCONCLUSIVE  
- Universal `BUDGET_EXHAUSTED` + `ATOM_INVENTION_SKIPPED_BY_PLANNING` → feed H9a/H9h scoring carefully without assuming root cause  
- Identical terminals across repairs → likely `NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE`

These are **design motivations**, not executed conclusions.

---

## 15. STOP

Do not run P0–P9 without:

```
STAGE-9 EXECUTION AUTHORIZATION REQUIRED: OFFLINE TRAJECTORY AUDIT ONLY
```

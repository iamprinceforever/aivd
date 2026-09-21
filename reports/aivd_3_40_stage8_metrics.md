# AIVD 3.40 Stage-8 — Metrics Specification

**Document type:** Stage-8 metrics spec (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 20:45 IST  
**Parent charter:** `reports/aivd_3_40_stage8_charter.md`  
**Companions:** preregistration, integration_spec, execution_spec, controls, matrix  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 0. Mandate

Preregister **how** Stage-8 measures (1) integration validity, (2) discovery-semantics preservation, (3) mechanism change A–I, (4) real-model discovery outcomes, (5) independent rediscovery, (6) recursive generation — **before** seeing plant outcomes. Metrics must not reduce to “S VERIFIED.”

---

## 1. Units & populations

| Symbol | Meaning |
|--------|---------|
| Condition | `S8-BASELINE` | `S8-RA` | `S8-RC` | `S8-RD` |
| Seed | ∈ `[0,1,2,3,4,7,11]` |
| Run | (condition, seed, plant) Sacred episode |
| Body / atom | Tracked micro body key under recorder |
| Fate | A…I | UNOBSERVED |
| Call_repair | One `apply_micro` on repair evaluator ledger |
| Call_sacred | Sacred BH accounting unit (unchanged semantics) |

Populations:

| Population | Membership |
|------------|------------|
| `P_ALL` | All matrix runs (28) |
| `P_FAM[f]` | Runs under family f |
| `P_FIXTURE` | Integration replay pairs |
| `P_TRACK` | Bodies instrumented for A–I (prereg interest set + all growth candidates) |

---

## 2. Axis 1 — INTEGRATION VALIDITY

| Metric | Definition | PASS |
|--------|------------|------|
| `mismatch_rate` | Fraction of fixture pairs where live adapter label ≠ Stage-7 Phase-B label | **== 0** |
| `ambiguity_mismatch` | Count ambiguity_state disagreements | **== 0** |
| `baseline_unmodified` | S8-BASELINE step-6 still `got in behaviors.values()` | **true** |
| `family_binding_ok` | Logged family matches condition map | **true** |
| `rb_absent` | R-B not wired | **true** |

Axis 1 FAIL → do not interpret axes 3–6 as repair evidence.

---

## 3. Axis 2 — DISCOVERY-SEMANTICS PRESERVATION

Compare each repair condition to BASELINE **holding seed fixed**, on quantities **not** definitionally downstream of equiv survival:

| Metric | Expectation |
|--------|-------------|
| `invent_event_parity` | Invent attempt counts within ±ε (ε=0 unless model nondeterminism documented; greedy → expect exact) |
| `compose_operator_set` | Same operator IDs invoked |
| `verify_predicate_id` | Identical |
| `floor_value` | 5 |
| `bh_envelope` | 48 |
| `invent_cap_value` | 48 |
| `provenance_schema` | Identical field sets |
| `independence_predicate_id` | Identical |

Allowed differences: candidate pool size post-equiv, selection among survivors, verify attempts on bodies that only exist post-repair, repair ledger costs.

| Gate | Rule |
|------|------|
| PASS | All immutable fields match; allowed differences attributed in recorder to equiv stage |
| FAIL | Any immutable field drifts, or unexplained invent/verify predicate change |

---

## 4. Axis 3 — MECHANISM CHANGE

### 4.1 Primary rates (per condition, aggregated over seeds)

Let `N_pool` = count of bodies that reached candidate pool (post-compose).  
Let `N_D` = count with primary fate **D**.  
Let `N_surv` = count surviving equiv (not D) among pool.

| Metric | Definition | Direction of interest vs BASELINE |
|--------|------------|-----------------------------------|
| `D_rate` | `N_D / max(1,N_pool)` | Decrease for families that fix false-duplicate over-collapse |
| `surv_rate` | `N_surv / max(1,N_pool)` | Increase when over-collapse reduced |
| `D_false_proxy` | Among D, fraction flagged by offline audit as DISTINCT-class when replayed under Stage-7 bank (optional offline shadow; namespace OFFLINE_EVAL) | Decrease |
| `E_rate` | fate E / N_surv | report |
| `flux_EG` | count reaching G among those who would be D under baseline shadow (counterfactual offline label) | increase supports H8b |

### 4.2 PASS threshold (prereg)

For a family f, axis 3 PASS if **all** hold on `P_FAM[f]` vs `P_FAM[BASELINE]`:

1. Axis 1–2 PASS for f.  
2. `D_rate(f) <= D_rate(BASELINE) - δ` with **δ = 0.05** absolute **or** McNemar / paired seed test at α=0.05 on paired per-seed D counts — **whichever is applicable given sample**; if ties exact, require consistent direction on ≥5/7 seeds.  
3. Attribution: ≥1 recorder series shows equiv_decision label flips from baseline-duplicate to repair-distinct/ambiguous on overlapping body keys.  
4. UNOBSERVED rate on pool-entered bodies ≤ **0.05**.

If instrumentation cannot support (3), axis 3 = INCONCLUSIVE (not PASS).

### 4.3 Null result

No threshold-meeting shift → axis 3 null (PARTIAL Stage-8 if axes 1–2 PASS).

---

## 5. Axis 4 — REAL-MODEL DISCOVERY OUTCOME

Per condition × seed (and aggregates):

| Metric | Definition |
|--------|------------|
| `firewall_epoch` | as Sacred recorder |
| `n_verified` | plant verify count |
| `n_independent_strict` | independence bar |
| `terminal_state` | enum |
| `mean_budget_used` | BH draws used |
| `unresolved_mode` | if any |

**PASS (axis 4):** not a hard numeric uplift requirement. Report honestly.  
**Support H8c** if axis 3 PASS and ≥1 of {verify uplift, firewall-pattern change, unresolved-mode shift} is consistent with survival flux (prereg: same direction on ≥5/7 seeds **or** aggregate exact binomial note).  
**Null-ok:** axis 3 PASS + no outcome uplift → mechanism-only PARTIAL.

**Forbidden:** claiming axis 4 PASS solely from S VERIFIED without axis 3.

---

## 6. Axis 5 — INDEPENDENT REDISCOVERY

| Metric | PASS rule |
|--------|-----------|
| `leakage_battery` | clean (controls) |
| `independence_predicate_unchanged` | true |
| `independent_audit` | every Independent=1 row passes manual/automated provenance audit |
| `H_rate` | report fate **H** counts |

Axis 5 FAIL if leakage or predicate edit. Null Independent counts with clean battery = PASS (honest zeros).

---

## 7. Axis 6 — RECURSIVE GENERATION

| Metric | Definition |
|--------|------------|
| `I_count` | bodies with fate **I** |
| `I_rate` | `I_count / max(1, N_surv)` |
| `recursive_edges` | parent→child generation edges in generation graph |

Report always. Secondary support for H8e if `I_rate(f) > I_rate(BASELINE)` on ≥5/7 seeds when axis 3 PASS. Absence ≠ FAIL.

---

## 8. Cost metrics (first-class)

| Metric | Ledger |
|--------|--------|
| `repair_calls_total` / mean / max / p95 | repair evaluator |
| `sacred_bh_draws` | Sacred (must respect 48) |
| `budget_cheat_flag` | true if BH>48 or invent_cap>48 or floor<5 observed | → H8-REJECT |

Repair cost practicality is **informational** at Stage-8 (R-B already excluded). Extreme repair costs that break plant completion must be reported; do not raise BH to compensate.

---

## 9. S diagnostic metrics (non-gating)

| Metric | Namespace |
|--------|-----------|
| S verify / independent / terminal | `S_DIAGNOSTIC` |
| Odd CAT-self fate A–I | `S_DIAGNOSTIC` |
| Equiv decisions on odd/U body keys | `S_DIAGNOSTIC` |

May inform H8f. Must not redefine SUCCESS.

---

## 10. Ranking among R-A / R-C / R-D

Default: **no ranking** — retain ties.  
Optional prereg ranking **only if** axis 3 PASS for multiple and they separate on:

1. higher surv_rate without axis 2 fail, then  
2. lower repair_calls_mean, then  
3. higher independent_strict aggregate  

If still tied → retain all. Never rank by S alone.

---

## 11. Overall gates

| Gate | Rule |
|------|------|
| SUCCESS | Axes 1+2 PASS; axis 3 PASS for ≥1 survivor; axes 4–6 reported; controls clean; H8-REJECT unsupported |
| PARTIAL | Axes 1+2 PASS with null/weak axis 3; or axis 3 PASS with null axis 4; or mixed survivors |
| FAILED | Axis 1 or 2 FAIL; or H8-REJECT; or protocol violation |
| INCONCLUSIVE | UNOBSERVED blocks axis 3 attribution |

Final printed lines (EXECUTION):

```
STAGE-8 COMPLETE: <GATE> — <one-line reading>
```

or if design-only context:

```
STAGE-8 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

---

## 12. What metrics are NOT

- Not “S pass rate”  
- Not Stage-7 offline FDR/MDR transplanted as discovery credit  
- Not license to drop seeds  
- Not license to merge a winner into default `grow.py` without further authorization  

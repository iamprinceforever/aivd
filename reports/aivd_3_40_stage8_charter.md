# AIVD 3.40 Stage-8 DESIGN CHARTER — Live Equivalence Integration + Fresh-Plant Discovery (Design Only)

**Document type:** Stage-8 DESIGN CHARTER (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 20:45 IST  
**Start tip:** `079d66f` (`research/aivd-3.40-budget-representation-frontier`)  
**Stage-7 COMPLETE tip:** `079d66f` (Phase A/B COMPLETE — `PHASE_A_SUCCESS_AND_PHASE_B_PASS`; OUTAGE_RECOVERY)  
**Stage-7 design freeze:** `d0ef7b6`  
**Authority priors (cite; do not weaken):** Stage-7 results `079d66f` / design `d0ef7b6`; Stage-6 `000a4d8` / design `ac152c6`; Stage-5 `c003e60` / design `2496857`; Stage-4 `4005e66` / design `27e9e88`; Stage-3 `146915b`; Stage-2 `dcae889`; Phase-2 `f4d7a2b` / design `7be4124`; Phase-1 `a2ab0cc`; R1b caveat `7a3457e`; AIVD 3.38 / 3.39 Sacred baselines  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** **STAGE-8 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION**

Companion deliverables (this commit, `reports/` only):

1. `aivd_3_40_stage8_charter.md` — **this file**
2. `aivd_3_40_stage8_hypothesis_tree.md`
3. `aivd_3_40_stage8_matrix.json`
4. `aivd_3_40_stage8_preregistration.md`
5. `aivd_3_40_stage8_integration_spec.md`
6. `aivd_3_40_stage8_execution_spec.md`
7. `aivd_3_40_stage8_metrics.md`
8. `aivd_3_40_stage8_controls.md`

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Stage-8 scope (this commit) | **DESIGN documents only** under `reports/` |
| No live filter mod | Do **not** edit `grow.py`, `_keep`, `FILTER_BEHAVIORAL_DUP`, discovery pipeline, promote-set, firewall, verify, invent, propose_atoms |
| No execution | No Sacred, no TinyLlama, no Stage-8 plant runs, no merge of any repair into live growth |
| No historical mutation | Do **not** modify Stage-7/6/5/4 / Phase-2/1 / Stage-2/3 reports or 3.38/3.39 baselines; Stage-7 SUCCESS remains offline-generalization + impl-spec-equivalence only |
| No single winner | Preserve multi-candidate survivors **R-A / R-C / R-D**; do **not** select one winner; do **not** retune R-A/R-C/R-D |
| No R-B | **R-B EXCLUDED** (`COST_IMPRACTICAL` under Stage-7 Phase-A criterion) — do not revive without new design revision |
| Scientific objective | Determine whether a Stage-7 validated **generic** equivalence repair changes **autonomous discovery behavior** on a **fresh real-model plant** while **preserving all other discovery semantics** — **NOT** “which makes S pass” |
| Primary question (exact) | Does a Stage-7-validated localized equivalence-filter repair, integrated into the actual discovery pipeline, produce measurable change in autonomous discovery behavior on a fresh plant — without altering invention / composition / selection / verification / firewall / provenance / independence / stopping rules beyond the equivalence decision? |
| S role | Diagnostic / stress only. Do **not** inject odd-stride atom; no target-specific guidance; no `propose_atoms` for S; no special case. S VERIFIED alone is **insufficient** success |
| Combined repairs | **Forbidden.** Each condition differs **ONLY** in equivalence implementation |
| Budget lock | Do **not** increase BH / invent_cap or lower `REDISCOVERY_FLOOR` to force a result |
| STOP | Integration / Sacred / TinyLlama / live `_keep` wiring / plant execution requires a **separate EXECUTION authorization** |

If a “design” proposal would merge a single winner into live `FILTER_BEHAVIORAL_DUP`, authorize Sacred in this commit, retune R-A/R-C/R-D, revive R-B without revision, raise BH / invent_cap, lower firewall floor, or define success solely as S VERIFIED → **STOP** (revise; do not ship).

---

## 1. Why Stage-8 (post Stage-7)

### 1.1 Stage-7 COMPLETE priors (immutable cite — do not inflate into discovery credit)

| Prior | Status |
|-------|--------|
| Case | **1** — `PHASE_A_SUCCESS_AND_PHASE_B_PASS` |
| BASELINE (Phase A) | Gate **INCONCLUSIVE**; FDR≈0.47; MDR=0; DCR=1.00; `sdiag_conflict=True` |
| R-A | Phase-A **SUCCESS**; Phase-B **SUCCESS** (mismatch_rate=0; PT all True) |
| R-B | Phase-A **COST_IMPRACTICAL** (calls_mean≈5.05, worst=18); Phase-B SUCCESS on accuracy but **EXCLUDED** from Stage-8 practical surviving set |
| R-C | Phase-A **SUCCESS**; Phase-B **SUCCESS** |
| R-D | Phase-A **SUCCESS**; Phase-B **SUCCESS** |
| Ranking multi-candidate | `['R-A', 'R-C', 'R-D']` |
| H7a / H7c / H7d / H7e | supported by Stage-7 evidence |
| H7b / H7-REJECT | not supported |
| Filter replaced | **false** |
| Sacred | **not** executed / **not** authorized |
| `autonomous_discovery_credit` | **false** |
| grow.py since `4005e66` | unchanged through Stage-7 |

**Stage-7 epistemic boundary (binding):**

> Stage-7 established that R-A / R-C / R-D **generalize** on an independent offline bench and that isolated executables are **spec-equivalent** to offline families. That is **not** evidence that repairs change autonomous discovery, that live `FILTER_BEHAVIORAL_DUP` may be replaced without a Stage-8 charter, or that S will (or must) VERIFIED. Stage-8 designs the **first** live-integration + fresh-plant discovery experiment — it does **not** exist to make S pass, to pick a single winner, or to authorize execution in this commit.

### 1.2 Primary scientific question (binding)

> Determine whether a Stage-7 validated generic equivalence repair changes autonomous discovery behavior on a fresh real-model plant while preserving all other discovery semantics.

Subordinate diagnostic: can the localized equivalence-filter bottleneck (Stage-4/5 `FILTER_BEHAVIORAL_DUP` / H2c / H5b) be repaired **in the actual discovery pipeline** and produce **measurable mechanism change** (trace stages A–I), independently of whether S reaches VERIFIED?

### 1.3 What Stage-8 is NOT

- Not a cure for S / not “make S pass”
- Not authorization to execute Sacred / TinyLlama / live `_keep` replacement in **this** commit
- Not a Stage-7 re-litigation that weakens Phase-A/B SUCCESS **or** invents discovery credit from offline wins
- Not a forced single-winner selection among R-A / R-C / R-D
- Not R-B revival / retune / cost-ceiling rewrite
- Not combined multi-repair stacks
- Not budget / invent_cap / floor relaxation to force outcomes
- Not mutation of 3.38 / 3.39 / Stage-2–7 historical artifacts

---

## 2. Candidate conditions (keep all three survivors + baseline)

| Condition ID | Equivalence impl | Plant (suggested) | Role |
|--------------|------------------|-------------------|------|
| `S8-BASELINE` | Live unmodified `FILTER_BEHAVIORAL_DUP` (`got in behaviors.values()`) | `AIVD340-S8-BASELINE` | Control / ablation anchor |
| `S8-RA` | R-A multi-context behavioral signature (Stage-6/7 frozen family) | `AIVD340-S8-RA` | Practical survivor |
| `S8-RC` | R-C adaptive context expansion (Stage-6/7 frozen family) | `AIVD340-S8-RC` | Practical survivor |
| `S8-RD` | R-D two-stage identity → semantic (Stage-6/7 frozen family) | `AIVD340-S8-RD` | Practical survivor |

**Excluded:** `R-B` — Stage-7 Phase-A `COST_IMPRACTICAL`. Do not include in Stage-8 matrix without a new design revision that re-opens cost practicality.

**Independence rule:** Each condition is an **independent** fresh plant. Differ **ONLY** in equivalence implementation at the `_keep` behavioral-dup step. No combined repair. No preload of prior discoveries / provenance from Stage-2/Sacred LLAMA / REPL / 339 / Stage-7 offline fixtures as plant state.

Full wiring: `reports/aivd_3_40_stage8_integration_spec.md`.  
Full run protocol: `reports/aivd_3_40_stage8_execution_spec.md`.

---

## 3. Frozen experimental variables (unless charter documents scientific necessity)

| Variable | Frozen value | Notes |
|----------|--------------|-------|
| Model | TinyLlama-1.1B-Chat-v1.0 | Same as Stage-2 Sacred / 3.40 Sacred factorial reference |
| Model path / revision / checksum | Pin at EXECUTION freeze from `/workspace/models/tinyllama` (or documented equivalent); record sha256 in execution stamp | Do not swap mid-matrix |
| Decoding | greedy fp16 CPU (Stage-2 continuity) | Do not switch to sampling to force novelty |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` | **Preregistered BEFORE execution**; no post-outcome seed selection |
| Episode budget (BH) | **48** | Sacred BH48 frozen; do **not** raise |
| `invent_cap` / `INVENT_CAP` | **48** | Do **not** raise |
| `REDISCOVERY_FLOOR` | **5** | Do **not** lower; no force-firewall |
| Representation | **R1 frozen** | R1b **NOT** auto-authorized (`7a3457e`) |
| Discovery mode / investigation mode | Stage-2 / Sacred 3.40 defaults | Identical across conditions |
| Verification rules | Unchanged vs Stage-2 Sacred | Identical across conditions |
| Provenance / independence / stopping rules | Unchanged | Identical across conditions |
| `propose_atoms` 8-set | IMMUTABLE | No S-targeted propose_atoms |
| Growth operators except equiv step | IMMUTABLE | Only `_keep` step-6 decision may differ |
| Equivalence family hyperparameters | Frozen from Stage-6 `equivalence_repair_spec.md` (`ac152c6`) + Stage-7 Phase-B modules | **No retune** of R-A/R-C/R-D |

**Do NOT** increase budget / invent_cap or lower firewall floor to force a result. Any scientifically necessary exception must be documented in a **revision** of this charter **before** EXECUTION — never mid-flight.

---

## 4. Mechanism trace (instrument; do not infer missing states)

Instrument every candidate / atom of interest through:

```
INVENTION → COMPOSITION → CANDIDATE POOL → EQUIVALENCE DECISION → SURVIVAL/REMOVAL → SELECTION → VERIFICATION → REDISCOVERY → RECURSIVE GENERATION
```

Distinguish terminal / waypoint labels **A–I** (mutually exclusive primary fate per tracked body; secondary annotations allowed):

| Code | Meaning |
|------|---------|
| **A** | Never invented |
| **B** | Invented but composition failed |
| **C** | Composed but absent from candidate pool |
| **D** | Entered pool but **removed by equivalence** |
| **E** | Survived equivalence but **not selected** |
| **F** | Selected but **failed verification** |
| **G** | **Verified** |
| **H** | Independently rediscovered |
| **I** | Produced another generation (recursive generation) |

**Binding:** Do not infer missing states from downstream outcomes. If instrumentation cannot observe a stage, record `UNOBSERVED` — never silently map to A–I. Primary Stage-8 mechanism claim uses shifts in **D** (and consequent E/G/H/I) under repaired vs baseline equivalence, holding other stages' semantics fixed.

Full metric definitions: `reports/aivd_3_40_stage8_metrics.md`.

---

## 5. S target (diagnostic stress only)

| Rule | Binding |
|------|---------|
| May include S as diagnostic stress plant target | yes |
| Inject odd-stride atom / preload S body | **NO** |
| Target-specific guidance / prompts / propose_atoms for S | **NO** |
| Special-case equivalence for odd / CAT-self / HO-CRIT bodies | **NO** |
| Success = S VERIFIED | **NO** (insufficient alone; see §6) |
| Key question | Whether repaired live system **naturally** changes the trajectory that previously ended in the equiv-filter bottleneck |

U (known-good / ROL1-class continuity) may be used as **positive-control** plant or side cell only if preregistered; default Stage-8 primary matrix is the four equivalence conditions on the fresh S8 plants above. Do not combine S+U metrics into a single success bit.

---

## 6. Success criteria (preregistered; separate axes)

Success is **multi-axis**. Do **not** define success solely as S VERIFIED. Mechanism improvement without S discovery is **valid**. S VERIFIED alone is **insufficient** if other discovery semantics changed.

| # | Axis | Pass intuition (details in metrics + prereg) |
|---|------|-----------------------------------------------|
| 1 | **INTEGRATION VALIDITY** | Live wiring matches Stage-7 Phase-B isolated classifier decisions on frozen fixtures; only `_keep` step-6 differs; import/identity checks pass; no silent fallback to baseline inside “repair” conditions |
| 2 | **DISCOVERY-SEMANTICS PRESERVATION** | Invention, composition, candidate construction/selection (non-equiv), scoring unrelated to equivalence, verification, firewall, budgets, provenance, independence accounting, stopping rules unchanged vs baseline condition except via equivalence outcomes |
| 3 | **MECHANISM CHANGE** | Measurable shift in A–I trace vs BASELINE — especially reduced unjustified **D** (false-duplicate removals) and/or altered survival→selection→verify pathway — under instrumentation, not narrative |
| 4 | **REAL-MODEL DISCOVERY OUTCOME** | Honest report of plant-level discovery/verify/firewall outcomes on fresh TinyLlama plants; improvement **or** null result both publishable; not gated on S alone |
| 5 | **INDEPENDENT REDISCOVERY** | Where verify occurs, independence bar (firewall_epoch≥1 ∧ independently_discovered ∧ ¬leak) evaluated; repairs must not manufacture independence via provenance leakage |
| 6 | **RECURSIVE GENERATION** | Whether survivors produce further generation (label **I**); report honestly; absence is not automatic FAIL if axes 1–3 hold |

**Overall Stage-8 scientific SUCCESS (design intent for future EXECUTION):** axes 1 + 2 PASS, and axis 3 PASS for ≥1 of {R-A, R-C, R-D}, with axes 4–6 reported under prereg rules — **still without** declaring “S solved.”

**PARTIAL:** Integration valid + semantics preserved + mechanism change weak/ambiguous; or mechanism change clear but discovery outcomes null; or one survivor shows change while ties remain.

**FAILED:** Integration invalid; semantics altered outside equivalence; target-specific rules; budget/floor cheating; historical mutation; post-hoc seed selection; single-winner coercion without prereg basis; provenance leakage; H8-REJECT patterns.

**INCONCLUSIVE:** Cannot separate mechanism change from noise under frozen seed set / instrumentation gaps recorded as UNOBSERVED.

---

## 7. Semantic preservation (binding)

Integration changes **ONLY** equivalence filtering at `FILTER_BEHAVIORAL_DUP` / `_keep` step 6.

| Must NOT alter | Check |
|----------------|-------|
| Invention / invent loop / invent_cap accounting | Compare invent event counts & cap hits across conditions holding seed fixed |
| Composition operators / CAT-self / glue order | Same operator set; only keep/drop after equiv may differ |
| Candidate construction before equiv | Same proposal generators |
| Selection / scoring unrelated to equivalence | Same scorer; selection sees only post-equiv pool |
| Verification predicates | Unchanged |
| Firewall / `REDISCOVERY_FLOOR` | Unchanged value and decision rule |
| Budgets (BH draws, leftover accounting) | Same envelope; repair-internal `apply_micro` costs must be **ledgered separately** from Sacred BH (see controls) |
| Provenance rules | Unchanged schema; no forged independence |
| Independence accounting | Unchanged predicates |
| Stopping rules | Unchanged |

Unintended changes → record under axis 2 FAIL / H8-REJECT. Full checklist: `reports/aivd_3_40_stage8_controls.md` + metrics § semantic deltas.

---

## 8. Controls (summary)

| Control | Purpose |
|---------|---------|
| Recorder / instrumentation validity | A–I stages observed, not inferred |
| Baseline reproducibility | S8-BASELINE reproduces Stage-2 / prior bottleneck phenomenology within noise |
| Provenance leakage | No preload of prior Sacred discoveries into fresh plants |
| Fresh-plant independence | Distinct plant IDs; empty prior discovery state |
| Implementation identity | Live repair condition ≡ Stage-7 Phase-B module bit-decision on frozen fixtures |
| Budget accounting | BH48 Sacred ledger vs repair evaluator ledger separated |
| Firewall accounting | Floor=5; no force-firewall; epoch recorded |
| 3.38 Sacred | **Frozen reference only** — do not modify or rerun as current control |

Full control protocol: `reports/aivd_3_40_stage8_controls.md`.

---

## 9. Statistical / replication discipline

1. **Define Sacred seed set BEFORE execution:** `[0, 1, 2, 3, 4, 7, 11]` (continuity with Stage-2 / Stage-7 prereg).  
2. **No post-outcome seed selection** or seed dropping.  
3. **Explicit multi-replication:** primary = full 7-seed × 4-condition matrix on fresh plants; if EXECUTION charter requires more, preregister additional seeds **before** any outcome inspection.  
4. **Preserve R-A / R-C / R-D ties:** if indistinguishable on prereg axes, retain all; do not rank without preregistered basis (cost practicality already excluded R-B; among R-A/R-C/R-D use metrics § ranking only if prereg thresholds separate them).  
5. Report per-seed and aggregate tables; never hide zeros.

---

## 10. Hypothesis decomposition (H8*)

Full tree: `reports/aivd_3_40_stage8_hypothesis_tree.md`. Summary:

| ID | Claim |
|----|-------|
| **H8a** | Live integration of a Stage-7 survivor is **valid** (axis 1) and **semantics-preserving** (axis 2) |
| **H8b** | At least one survivor produces **measurable mechanism change** (axis 3) vs BASELINE on fresh plants |
| **H8c** | Mechanism change yields altered **real-model discovery outcomes** (axis 4) without semantics breach |
| **H8d** | Where verify occurs, **independent rediscovery** (axis 5) remains honest under repaired filter |
| **H8e** | Survivors can participate in **recursive generation** (axis 6) when mechanism change admits them |
| **H8f** | S-diagnostic trajectory may still fail verify even when mechanism change is real — reportable; must not drive retune |
| **H8-REJECT** | Target-specific rules / combined repairs / budget cheating / provenance leak / live mutation beyond equiv step / post-hoc seeds / single-winner coercion |

---

## 11. Charter obligations A–K (must establish)

### A. How live integration is specified without executing it
Isolated Stage-7 Phase-B modules are the **source of truth** for R-A/R-C/R-D decisions. Integration_spec defines an adapter that replaces **only** `_keep` step 6 (`got in behaviors.values()` → family `classify_candidate` / signature compare), with ambiguity policy = retain provisional novelty (Stage-6/7 continuity). This commit does **not** perform the edit.

### B. How BASELINE remains a true control
`S8-BASELINE` uses unmodified `grow.py` behavioral-dup step. Same plant template, seeds, BH, invent_cap, floor, model. Only equivalence impl differs for repair conditions.

### C. How R-B exclusion is locked
Matrix `mechanisms_excluded: ["R-B"]` with reason `STAGE7_PHASE_A_COST_IMPRACTICAL`. Revival requires design revision.

### D. How multi-candidate ties are preserved
No “winner” field in matrix. Ranking optional and preregistered; default retain all of R-A/R-C/R-D for EXECUTION.

### E. How mechanism A–I is observed
Execution_spec requires recorder hooks at invent, compose, pool-enter, equiv-decide, select, verify, rediscovery, recurse — emitting A–I labels. Missing hook → `UNOBSERVED`, not inferred.

### F. How S remains diagnostic
S may appear as stress target; success criteria axes 1–6 do not collapse to S VERIFIED; no odd-atom injection; H8f covers S-null-with-mechanism-change.

### G. How semantic preservation is tested
Pairwise condition diffs on non-equiv pipelines (invent counts, compose attempts, verify predicate IDs, floor, BH draws, provenance schema) must match within instrumentation tolerance; equiv-caused pool cardinality differences are **expected** and attributed to axis 3.

### H. How fresh plants avoid leakage
New plant IDs; no copy of prior plant DBs / promote sets / discovery journals; controls doc leakage battery.

### I. How cost of repaired equivalence is accounted
Repair `apply_micro` calls during growth dedup are recorded on an **experimental evaluator ledger**, not silently billed as extra Sacred BH invent turns unless EXECUTION charter explicitly maps them — default: separate ledger; BH48 episode budget unchanged.

### J. What evidence would justify claiming discovery-behavior change
Prereg axis 3 PASS for ≥1 survivor with axes 1–2 PASS and controls clean — **with or without** S VERIFIED.

### K. What authorization is required to execute
A **separate Stage-8 EXECUTION authorization** that explicitly permits: (i) live `_keep` step-6 wiring per integration_spec, (ii) Sacred / TinyLlama fresh-plant runs per execution_spec, (iii) no retune / no R-B / no winner coercion / no BH raise / no floor lower. **This design commit does not grant that authorization.**

---

## 12. Sacred execution prerequisites (for a future EXECUTION charter)

All must hold before any Stage-8 EXECUTION begins:

1. Stage-8 **DESIGN** tip is ancestor of EXECUTION tip; eight design docs match this freeze.  
2. Stage-7 artifacts at `079d66f` unchanged; Stage-6/5/4 historical artifacts unchanged.  
3. `grow.py` still matches Stage-4 tip `4005e66` behavioral-dup step **until** EXECUTION explicitly applies integration_spec patches under version control.  
4. Seed set `[0,1,2,3,4,7,11]` frozen; plant IDs frozen; model checksum recorded.  
5. R-A/R-C/R-D family code identity pinned to Stage-7 Phase-B modules (hash).  
6. Controls preflight PASS (instrumentation, leakage, budget ledgers).  
7. Explicit human/parent **EXECUTION authorization** string present in the EXECUTION commit message / charter.  
8. Claim namespaces separated: `AUTONOMOUS` vs `INTEGRATION_VALIDATION` vs `OFFLINE_EVAL` vs `S_DIAGNOSTIC`.

---

## 13. Exact authorization required for execution

```
STAGE-8 EXECUTION AUTHORIZATION REQUIRED:
  - Authorize live _keep step-6 equivalence wiring per reports/aivd_3_40_stage8_integration_spec.md
    for conditions S8-RA / S8-RC / S8-RD ONLY (BASELINE unmodified).
  - Authorize Sacred TinyLlama fresh-plant matrix per reports/aivd_3_40_stage8_execution_spec.md
    with frozen BH48, invent_cap=48, REDISCOVERY_FLOOR=5, seeds [0,1,2,3,4,7,11],
    plants AIVD340-S8-BASELINE / AIVD340-S8-RA / AIVD340-S8-RC / AIVD340-S8-RD.
  - FORBID: R-B revival; retune R-A/R-C/R-D; single-winner merge; combined repairs;
    BH/invent_cap raise; floor lower; odd-atom injection; 3.38/3.39 mutation;
    post-hoc seed selection; success:=S VERIFIED alone.
  - This Stage-8 DESIGN commit does NOT constitute that authorization.
```

---

## 14. Experimental matrix (design sketch)

| Factor | Levels |
|--------|--------|
| Condition | `S8-BASELINE` | `S8-RA` | `S8-RC` | `S8-RD` |
| Equivalence | `FILTER_BEHAVIORAL_DUP` | `R-A` | `R-C` | `R-D` |
| Plant | `AIVD340-S8-BASELINE` | `AIVD340-S8-RA` | `AIVD340-S8-RC` | `AIVD340-S8-RD` |
| Model | TinyLlama-1.1B-Chat-v1.0 (pinned) |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| BH / invent_cap / floor | 48 / 48 / 5 |
| Representation | R1 (no auto R1b) |
| Audit mode | `LIVE_INTEGRATION_DISCOVERY` (primary) | `INTEGRATION_FIXTURE_REPLAY` (preflight) | `S_DIAGNOSTIC` |
| Mechanism fate | A…I | UNOBSERVED |

Full JSON: `reports/aivd_3_40_stage8_matrix.json`.

---

## 15. Prohibitions

| Forbidden | Why |
|-----------|-----|
| Edit `grow.py` / `_keep` / live filter in this commit | Design only |
| Execute Sacred / TinyLlama / Stage-8 plants | No auto-authorization |
| Merge single repair as “the” winner | Multi-candidate discipline |
| Retune R-A / R-C / R-D | Stage-7 freeze |
| Include R-B without revision | COST_IMPRACTICAL |
| Combined / stacked repairs | Confound isolation |
| Raise BH / invent_cap; lower REDISCOVERY_FLOOR; force-firewall | Result forcing |
| Inject odd-stride / S-special propose_atoms | Target contamination |
| Modify Stage-7…2 / 3.38 / 3.39 historical artifacts | Immutability |
| Infer A–I without instrumentation | Honesty |
| Define success solely as S VERIFIED | Scientific objective |
| Auto R1b / R1c / BHexplore / Level-14 | Caveat `7a3457e` |
| Rerun 3.38 Sacred as live control | Frozen reference only |
| Preload prior plant discoveries | Fresh-plant independence |

---

## 16. Exit / final gate

This commit delivers **design** only. No execution, live integration, Sacred, or TinyLlama authorization is granted.

```
STAGE-8 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

If a future design edit would require S-special cases, silent live merge without integration_spec, BH/floor cheating, historical mutation, R-B revival without revision, single-winner coercion, or “make S pass” framing, the gate becomes:

```
STAGE-8 DESIGN BLOCKED: <exact reason>
```

---

## 17. Parent commits (authority map)

| Role | SHA | Note |
|------|-----|------|
| Stage-8 design start tip / Stage-7 COMPLETE | `079d66f` | Phase A/B PASS; R-A/R-C/R-D practical survivors; R-B COST_IMPRACTICAL; Sacred not authorized |
| Stage-7 design freeze | `d0ef7b6` | Generalization + impl-validation design |
| Stage-6 COMPLETE | `000a4d8` | Offline repair SUCCESS R-A…R-D |
| Stage-6 design freeze | `ac152c6` | Generic equivalence-repair families |
| Stage-5 COMPLETE | `c003e60` | H5b+H5d; FALSE_DUPLICATE critical pair |
| Stage-4 COMPLETE | `4005e66` | H2c; FILTER_BEHAVIORAL_DUP location; grow.py anchor |
| Stage-3 | `146915b` | Localization design |
| Stage-2 | `dcae889` | Immutable Sacred aggregates (BH48 × R1/R1b) |
| Phase-2 / Phase-1 | `f4d7a2b` / `a2ab0cc` | Mode localization / offline trajectory |
| R1b caveat | `7a3457e` | No auto re-run |

---

## 18. What this commit does NOT do

- No Sacred / TinyLlama / plant execution / live `_keep` patch  
- No mutation of historical Stage-7/6/5/4/Phase/Stage-2/3 / 3.38/3.39 artifacts  
- No claim that R-A/R-C/R-D already change autonomous discovery — Stage-8 design exists to specify how that will be tested  
- No claim that offline generalization = live discovery credit  
- No R1b / R1c / BHexplore / Level-14 work  
- No single-winner selection or R-B revival  
- No authorization of Stage-8 EXECUTION — that requires a **separate** authorization meeting §12–§13  


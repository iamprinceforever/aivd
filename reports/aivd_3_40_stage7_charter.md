# AIVD 3.40 Stage-7 DESIGN CHARTER — Generalization + Implementation Validation (Design Only)

**Document type:** Stage-7 DESIGN CHARTER (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:55 IST  
**Start tip:** `000a4d8` (`research/aivd-3.40-budget-representation-frontier`)  
**Stage-6 COMPLETE tip:** `000a4d8` (offline equivalence-repair benchmark; R-A/B/C/D SUCCESS; BASELINE INCONCLUSIVE)  
**Stage-6 design freeze:** `ac152c6`  
**Authority priors (cite; do not weaken):** Stage-6 results `000a4d8` / design `ac152c6`; Stage-5 `c003e60` / design `2496857`; Stage-4 `4005e66` / design `27e9e88`; Stage-3 `146915b`; Stage-2 `dcae889`; Phase-2 `f4d7a2b` / design `7be4124`; Phase-1 `a2ab0cc`; R1b caveat `7a3457e`; AIVD 3.38 / 3.39 Sacred baselines  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** **STAGE-7 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION**

Companion deliverables (this commit, `reports/` only):

1. `aivd_3_40_stage7_charter.md` — **this file**
2. `aivd_3_40_stage7_hypothesis_tree.md`
3. `aivd_3_40_stage7_matrix.json`
4. `aivd_3_40_stage7_preregistration.md`
5. `aivd_3_40_stage7_generalization_spec.md`
6. `aivd_3_40_stage7_implementation_validation_spec.md`
7. `aivd_3_40_stage7_metrics.md`

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Stage-7 scope (this commit) | **DESIGN documents only** under `reports/` |
| No implementation | No edits to `grow.py`, `_keep`, `FILTER_BEHAVIORAL_DUP`, discovery pipeline, promote-set, firewall, verify, invent, propose_atoms |
| No execution | No Sacred, no TinyLlama, no Stage-7 Phase-A/B runs, no isolated-module wiring, no live filter replacement |
| No historical mutation | Do **not** modify Stage-6/5/4 / Phase-2/1 / Stage-2/3 reports or 3.38/3.39 baselines; Stage-6 SUCCESS claims remain offline-benchmark-only |
| Scientific objective | Determine which repair(s), if any, **generalize** beyond the Stage-6 offline bench and can be implemented **without changing discovery semantics** — **NOT** make S pass |
| Primary question (exact) | Before modifying the live AIVD pipeline: which repair mechanism, if any, generalizes beyond Stage-6 benchmark and can be implemented without changing discovery semantics? |
| Distinction mandate | Explicitly separate: **benchmark overfitting** \| **genuine equivalence-repair generalization** \| **implementation/specification mismatch** |
| Critical S / Stage-6 HO pair | **Diagnostic only** — must **NOT** determine repair selection; if a repair passes independent Phase-A but fails S pair → **report conflict**; do **NOT** modify repair to recover S |
| Dual retention | Preserve Stage-6 dual-retention discipline (true-dup collapse **and** novelty retention) on a **new** frozen generalization benchmark |
| Classification-only | Any future isolated implementation may change **ONLY** classification decisions; must **NOT** change proposal generation, invention, growth operators, scoring, selection, verification, firewall, discovery prompts |
| Sacred budget | **Sacred BH48 frozen.** Stage-7 = validation design only. Stage-7 itself **MUST NOT** authorize Sacred (may only define **future** Sacred preconditions) |
| Live pipeline boundary | Stage-7 ends **BEFORE** live integration. No experimental repair replaces `FILTER_BEHAVIORAL_DUP`. No discovery run consumes a repaired filter |
| Two-phase order | **Phase A (generalization) before Phase B (implementation validation)** — B consumes only repairs that pass A |
| STOP | Implementation / Sacred / Phase-A/B execution / live wiring requires a **separate EXECUTION charter** |

If a “design” proposal would select a winner from the Stage-6 critical pair alone, replace live `FILTER_BEHAVIORAL_DUP`, authorize Sacred, or alter growth/invent/selection to make S pass → **STOP** (revise; do not ship).

---

## 1. Why Stage-7 (post Stage-6)

### 1.1 Stage-6 COMPLETE priors (immutable cite — do not treat as discovery success)

| Prior | Status |
|-------|--------|
| BASELINE | Gate **INCONCLUSIVE**; FDR=0.50; MDR=0; DCR=1.00; crit hard-collapse=1 |
| R-A / R-B / R-C / R-D | Gate **SUCCESS**; FDR=0; MDR=0; DCR=1.00; crit hard-collapse=0 |
| Degeneracy | none observed on R-A…R-D |
| Cost | within Stage-6 envelope (93 / 5000 apply_micro); Sacred BH draws=0 |
| Leakage / pipeline mutation | false |
| Held-out S6-HO-CRIT | BASELINE→`duplicate`; R-A/B/C/D→`distinct` |
| Filter replacement | **not** performed |
| Sacred | not executed / not authorized |
| `autonomous_discovery_credit` | **false** |

**Stage-6 epistemic boundary (binding):**

> Stage-6 established that R-A…R-D jointly achieve duplicate retention and novelty retention **on the frozen offline Stage-6 benchmark**. That is **not** evidence that repairs work in autonomous discovery, that they generalize beyond that bench, that offline specs equal executable modules, or that live `FILTER_BEHAVIORAL_DUP` may be replaced. Stage-7 designs **independent generalization** and **spec↔impl equivalence** tests — it does **not** exist to make S pass or to authorize Sacred.

### 1.2 Primary scientific question (binding)

> Before modifying the live AIVD pipeline: which repair mechanism, if any, generalizes beyond the Stage-6 benchmark and can be implemented without changing discovery semantics?

Stage-7 must distinguish three failure/success modes:

| Mode | Meaning |
|------|---------|
| **Benchmark overfitting** | Repair succeeds on Stage-6 (and Stage-6-related pairs) but fails on an independent generalization bench |
| **Genuine equivalence-repair generalization** | Repair meets preregistered generalization criteria on an independent frozen bench without target-specific rules |
| **Implementation/specification mismatch** | Offline repair decisions differ from an isolated executable claiming the same family — FAIL; do not silently adjust either side |

### 1.3 What Stage-7 is NOT

- Not a cure for S / not “make S pass”
- Not authorization to implement repairs in live `grow.py` / replace `FILTER_BEHAVIORAL_DUP`
- Not authorization for fresh Sacred / TinyLlama / R1b / R1c / BHexplore / Level-14
- Not a Stage-6 re-litigation that weakens R-A…R-D offline SUCCESS **or** invents discovery credit from it
- Not an experiment that chooses a “winner” using the Stage-6 critical pair / S pair
- Not live-pipeline integration; Stage-7 ends **before** any discovery run consumes a repaired filter

---

## 2. Two-phase design (A before B)

### Phase A — Generalization benchmark (primary)

**Purpose:** Test whether Stage-6 SUCCESS families generalize beyond the Stage-6 pair set / context bank / critical-class proximity.

**Requirements (binding):**

1. **NEW benchmark** not used to design or tune R-A…R-D (Stage-6 design `ac152c6` and Stage-6 exec `000a4d8` are prior — Phase-A pairs must be independent).
2. Must contain: true dups; known non-dups; context-dependent pairs; textual-equal / behaviorally-different where valid; textual-different / behaviorally-equivalent; state/context-sensitive; composition-sensitive.
3. **Freeze before execution.** Do not derive Phase-A pairs from Stage-6 results after the fact.
4. **Held-out discipline:** independent of Stage-6 tuning, of `S6-HO-CRIT`, and of the exact critical pair. If any pair is derived from / shares bodies with the critical pair → label **`RELATED`**; do **not** count as independent generalization evidence.
5. **Metrics:** same Stage-6 FDR / MDR / DPR / DCR + evaluator cost, worst-case / median cost, degeneracy, ambiguity rate, context coverage. No post-hoc success criteria.
6. **Repair selection:** do **NOT** choose a winner using the S / Stage-6 critical pair. Rank by **preregistered generalization criteria**. If indistinguishable → keep **multiple** candidates; do not arbitrarily choose one.
7. Critical S pair remains **diagnostic only**. If repair passes Phase-A independent bench but fails S diagnostic → **report conflict**; do **not** modify repair to recover S.

Full pair / bank / contamination rules: `reports/aivd_3_40_stage7_generalization_spec.md` + preregistration + matrix.

### Phase B — Implementation validation (only after Phase A)

**Purpose:** For every repair that **passes Phase A**, implement in an **isolated experimental module** and verify **spec equivalence** to the offline repair definition.

**Requirements (binding):**

1. Do **NOT** replace `FILTER_BEHAVIORAL_DUP`.
2. Do **NOT** modify `grow.py` unless a frozen impl-validation spec explicitly requires an **isolated adapter** that cannot affect live discovery (default: **no** `grow.py` edits).
3. Isolated module must consume the **same inputs** as the offline repair spec → produce the **same equivalence decisions**.
4. **Spec equivalence:** offline classifier vs isolated executable on the **complete frozen Phase-A (+ Phase-B fixtures) benchmark** — require identical decisions, ambiguity states, provenance fields, and cost accounting. If they differ → **FAILED**. Do **not** silently adjust either side.
5. **Property tests** (only if meaningful for the family’s promises): reflexivity, determinism, true-dup suppression, non-dup preservation, context sensitivity, bounded cost, provenance isolation. Do **not** assume mathematical properties the family never promised.

Full interface / equivalence / property-test rules: `reports/aivd_3_40_stage7_implementation_validation_spec.md`.

**Ordering lock:** Phase B may not begin until Phase A gates are recorded under a frozen Phase-A tip. Mechanisms that fail Phase A are **not** implemented in Phase B (except optional FAIL-control stubs if a future EXECUTION charter explicitly requires them — default: skip).

---

## 3. Charter obligations A–G (must establish)

### A. How independent generalization is tested

- Construct a **new** frozen benchmark (`S7-GEN-*` conditions) with required pair classes (generalization_spec §2).
- Assign ground-truth labels from a frozen multi-context audit relation **before** repair outcomes.
- Evaluate BASELINE + each Stage-6 SUCCESS family (R-A…R-D) under identical bank / seeds / budgets.
- Primary generalization evidence = performance on pairs labeled `INDEPENDENT` (not `RELATED`, not Stage-6 replay).
- Rank / select by preregistered generalization criteria (metrics § gate + prereg § thresholds) — **never** by S / `S6-HO-CRIT` alone.

### B. How benchmark contamination is prevented

| Guard | Binding |
|-------|---------|
| No Stage-6 pair reuse as independent evidence | Stage-6 IDs may appear only as `S7-REPLAY-*` continuity cells — scored separately |
| Critical-pair / HO-CRIT proximity | Any shared body keys with Stage-5/6 critical pair → `RELATED`; excluded from independent generalization numerators |
| Freeze-before-exec | Pair list hash + context-bank hash + GT hash pinned before Phase-A outcomes inspected |
| No post-hoc pair/context add | Adding pairs/contexts after seeing Phase-A results → STOP / revision |
| No tuning on S diagnostic | Thresholds / family hyperparameters frozen from Stage-6 specs; Phase-A may **not** retune to recover S |
| Design-time independence | Phase-A pairs must be motivated without reference to Stage-6 per-pair prediction table |

### C. How repairs are compared fairly

- Same Phase-A benchmark, GT labels, seeds, context bank, cost envelope.
- Same classification interface: `duplicate` \| `distinct` \| `ambiguous`.
- Mechanism-only delta (classification subroutine); no invent/growth/scoring/selection changes.
- Ablation table: BASELINE vs each candidate that still claims Stage-6 SUCCESS eligibility.
- If multiple families meet SUCCESS bands and are statistically / qualitatively indistinguishable on prereg criteria → **retain all**; do not force a single winner.
- Cost is a first-class ranking dimension (accuracy with unbounded cost → classify accordingly; see metrics).

### D. How offline and executable implementations are verified equivalent

- Phase B builds an isolated module per Phase-A-passing family.
- Run offline spec replay and isolated executable on the **identical** frozen pair envelopes.
- Require byte-stable / exact equality on: label, ambiguity state, provenance schema fields, `apply_micro_calls` (or documented equivalent cost units).
- Any mismatch → mechanism Phase-B gate **FAILED** (implementation/specification mismatch) — do not patch offline or executable silently to agree.
- Property tests are secondary and only for promised properties.

### E. How evaluator cost is bounded

- Preserve Stage-6 cost discipline as the default envelope (prereg § budget locks).
- Report total / per-pair max / average / worst-case / median evaluator calls.
- Hard caps: per-pair max, expansion sub-cap, whole-run max; on exhaustion → `ambiguous` / defer — **not** auto-discard as `duplicate`.
- Sacred BH48 draws must remain **0**.
- Excellent accuracy + unbounded / impractical cost → gate **COST_IMPRACTICAL** / PARTIAL per metrics — not SUCCESS for live-consideration ranking.

### F. How live-pipeline integration remains isolated

| Boundary | Binding |
|----------|---------|
| Live `FILTER_BEHAVIORAL_DUP` | **IMMUTABLE** through Stage-7 Design **and** through Stage-7 EXECUTION (if later authorized) |
| `grow.py` | No modification by default; isolated adapter only if Phase-B spec explicitly requires and adapter cannot be imported by discovery entrypoints |
| Discovery runs | Must **not** consume repaired filter |
| Namespace | `OFFLINE_EVAL` / `IMPL_VALIDATION` only; `autonomous_discovery_credit=false` |
| Stage-7 end | **Before** live integration; future Sacred / live-wire charters are separate documents |

### G. What evidence would justify a **future** Sacred experiment

Stage-7 **does not** authorize Sacred. A **future** Sacred charter may be considered **only if ALL** hold:

1. Stage-7 Phase-A EXECUTION COMPLETE with ≥1 family gate = SUCCESS (or honest PARTIAL with explicit go/no-go) on **independent** generalization evidence  
2. Stage-7 Phase-B EXECUTION COMPLETE with **spec equivalence PASS** for that family (or for each retained candidate)  
3. No target-specific rule / H7-REJECT supported  
4. Cost practical under prereg envelopes (not COST_IMPRACTICAL)  
5. Critical S diagnostic conflict, if any, is **reported** and does **not** drive silent retuning  
6. Sacred BH48 still frozen as in baseline; Stage-7 costs fully accounted in experimental budget  
7. Stage-5/6 artifacts untouched and still reproducible  
8. Separate Sacred charter explicitly re-states: not make S pass as scientific objective; namespaces AUTONOMOUS vs OFFLINE_EVAL vs IMPL_VALIDATION vs CONTROLLED_INPUT separate; live filter replacement still requires yet another authorization beyond Sacred itself  

**This commit does NOT authorize Sacred. Stage-7 EXECUTION (if later authorized) also does NOT authorize Sacred.**

---

## 4. What counts as Stage-7 success?

### Phase A success (per mechanism)

| # | Criterion |
|---|-----------|
| 1 | Meets prereg FDR/MDR/DPR/DCR/AR bands on `INDEPENDENT` Phase-A pairs |
| 2 | Required pair classes covered; context coverage met |
| 3 | No degeneracy detectors trip |
| 4 | Cost within envelope; Sacred draws = 0 |
| 5 | No target-specific / critical-pair-special rule |
| 6 | `RELATED` / S diagnostic reported separately — **not** used as primary pass key |
| 7 | Fair ablation vs BASELINE under same frozen bench |

### Phase B success (per Phase-A-passing mechanism)

| # | Criterion |
|---|-----------|
| 1 | Isolated module exists **outside** live discovery import path |
| 2 | Offline vs executable: identical labels, ambiguity, provenance, cost accounting on complete frozen bench |
| 3 | Promised property tests PASS (only those preregistered as meaningful) |
| 4 | No `grow.py` / `FILTER_BEHAVIORAL_DUP` replacement; no discovery consumption |
| 5 | Pipeline mutation flag = false |

**Overall Stage-7 scientific success:** ≥1 family with Phase-A SUCCESS (independent generalization) **and** Phase-B spec-equivalence PASS — still **without** live integration or Sacred.

**PARTIAL:** Phase-A material improvement without full bands; or Phase-A SUCCESS with Phase-B mismatch honestly failed; or cost-impractical accuracy.

**FAILED:** contamination / H7-REJECT / silent live wiring / Sacred touch / post-hoc criteria / repairing S by special-case.

**Not a success criterion:** S VERIFIED / Sacred pass / live odd-CAT survival / autonomous discovery credit.

---

## 5. Hypothesis decomposition (H7*)

Full tree: `reports/aivd_3_40_stage7_hypothesis_tree.md`. Summary:

| ID | Claim |
|----|-------|
| **H7a** | ≥1 Stage-6 SUCCESS family generalizes to the independent Phase-A bench (genuine generalization) |
| **H7b** | Apparent Stage-6 wins are bench-specific (overfitting) — Phase-A exposes failure on independent classes |
| **H7c** | Among Phase-A passers, offline spec and isolated executable are decision-equivalent (no impl/spec mismatch) |
| **H7d** | Cost–quality ranking under Stage-7 envelopes separates practical from impractical passers without Sacred burn |
| **H7e** | Critical S / HO diagnostic may conflict with independent generalization; conflict is reportable and must not drive retuning |
| **H7-REJECT** | Gains require target-specific / Stage-6-critical-special / textual-only rules, or live-pipeline mutation → FAILED |

---

## 6. Frozen endpoints & live filter anchors (read-only)

| Role | SHA / path |
|------|------------|
| Current tip (Stage-6 complete) | `000a4d8` |
| Stage-6 design | `ac152c6` |
| Stage-5 complete | `c003e60` |
| Stage-4 complete | `4005e66` |
| Stage-3 | `146915b` |
| Stage-2 | `dcae889` |
| Phase-1 | `a2ab0cc` |
| Phase-2 | `f4d7a2b` / design `7be4124` |

Live filter (immutable cite):

| Anchor | Location | Role |
|--------|----------|------|
| Live collapse | `aivd/science/grow.py::propose_growth` nested `_keep` | `got = apply_micro(identity, body2)`; reject if `got in behaviors.values()` |
| Label | `FILTER_BEHAVIORAL_DUP` | Stage-4/5/6 instrumentation label |
| Named helper (NOT live `_keep`) | `behavioral_equivalent(...)` | Multi-probe helper — must not be confused with singleton identity rule |

**Stage-7 designs may propose isolated experimental modules that mirror classification — never live replacement in this stage.**

---

## 7. Experimental matrix (design sketch)

| Factor | Levels |
|--------|--------|
| Phase | `A_GENERALIZATION` \| `B_IMPL_VALIDATION` |
| Mechanism | `BASELINE_FILTER_BEHAVIORAL_DUP` \| `R-A` \| `R-B` \| `R-C` \| `R-D` |
| Pair independence | `INDEPENDENT` \| `RELATED` \| `S6_REPLAY` \| `S_DIAGNOSTIC` |
| Pair class | `TRUE_DUP` \| `KNOWN_NONDUP` \| `CONTEXT_DEPENDENT` \| `TEXT_EQ_BEH_DIFF` \| `TEXT_DIFF_BEH_EQ` \| `STATE_CONTEXT_SENSITIVE` \| `COMPOSITION_SENSITIVE` \| `U_GOOD` \| `ADV_*` |
| Audit mode | `OFFLINE_GENERALIZATION_BENCH` (Phase A) \| `IMPL_SPEC_EQUIVALENCE` (Phase B) |
| Classification | `duplicate` \| `distinct` \| `ambiguous` |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` (continuity) |
| Sacred budget | **BH48 frozen** (not consumed) |
| Stage-7 exp budget | Explicit call envelope (prereg) |
| Representation | Frozen **R1**; **no** auto R1b |

Full JSON: `reports/aivd_3_40_stage7_matrix.json`.

---

## 8. Ambiguity & cost honesty (binding)

When cheap identity says DUPLICATE but semantic evidence is insufficient:

| Strategy | Allowed | Must preregister |
|----------|---------|------------------|
| Defer / `ambiguous` | yes | budget / when / final label if unresolved |
| Request additional context | yes | only from **frozen** reserve bank; hard call cap |
| Retain provisional novelty | yes | report separately from hard `distinct` |
| Auto-discard as duplicate | **NO** when evidence insufficient | — |

Cost reporting mandatory: total, per-pair max, average, median, worst-case. Unbounded expansion to force distinctness = FAILED.

---

## 9. Prohibitions

| Forbidden | Why |
|-----------|-----|
| Implement repair / edit `grow.py` / `_keep` / discovery pipeline in this commit | Design only |
| Execute Phase A/B or Sacred | No auto-authorization |
| Replace `FILTER_BEHAVIORAL_DUP` / live integration | Stage-7 ends before live integration |
| Modify Stage-6/5/4/Phase/Stage-2/3 / 3.38/3.39 historical artifacts | Immutability |
| Choose winner using S / `S6-HO-CRIT` / critical pair alone | Selection contamination |
| Modify repair to recover S after Phase-A pass / S fail conflict | Diagnostic must not drive retuning |
| Derive Phase-A “independent” pairs from Stage-6 critical bodies without `RELATED` label | Contamination |
| Add contexts/pairs after seeing Phase-A/B results | Prereg violation |
| Silently consume Sacred / discovery BH48 | Budget firewall |
| Change proposal generation, invent, growth ops, scoring, selection, verify, firewall, prompts | Classification-only |
| Make S pass framing / authorize Sacred from Stage-7 | Out of scope |
| Auto R1b / R1c / BHexplore / Level-14 | Caveat `7a3457e` |
| Weaken Stage-5 H5b/H5d or Stage-6 offline SUCCESS-as-offline | Established evidence |
| Silently adjust offline or executable to force Phase-B agreement | Spec equivalence honesty |

---

## 10. Exit / final gate

This commit delivers **design** only. No execution, implementation, Sacred, or live-integration authorization is granted.

```
STAGE-7 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

If a future design edit would require S-special cases, live filter replacement, silent Sacred-budget use, historical mutation, Phase-B-before-A, or “make S pass” framing, the gate becomes:

```
STAGE-7 DESIGN BLOCKED: <exact reason>
```

---

## 11. Parent commits (authority map)

| Role | SHA | Note |
|------|-----|------|
| Stage-7 design start tip / Stage-6 COMPLETE | `000a4d8` | Offline repair SUCCESS R-A…R-D; BASELINE INCONCLUSIVE; no discovery credit |
| Stage-6 design freeze | `ac152c6` | Generic equivalence-repair design READY |
| Stage-5 COMPLETE | `c003e60` | H5b+H5d; FALSE_DUPLICATE critical pair |
| Stage-5 design | `2496857` | Equivalence-audit design |
| Stage-4 COMPLETE | `4005e66` | H2c; FILTER_BEHAVIORAL_DUP location |
| Stage-3 | `146915b` | Localization design |
| Stage-2 | `dcae889` | Immutable Sacred aggregates |
| Phase-2 / Phase-1 | `f4d7a2b` / `a2ab0cc` | Mode localization / offline trajectory |
| R1b caveat | `7a3457e` | No auto re-run |

---

## 12. What this commit does NOT do

- No Sacred / TinyLlama / Phase-A/B execution / repair implementation  
- No mutation of historical Stage-6/5/4/Phase/Stage-2/3 / 3.38/3.39 artifacts  
- No claim that R-A…R-D already generalize — Stage-7 design exists to specify how generalization and impl equivalence will be tested  
- No claim that Mode B / offline eval = autonomous discovery  
- No R1b / R1c / BHexplore / Level-14 work  
- No live `FILTER_BEHAVIORAL_DUP` replacement  
- No authorization of fresh Sacred even if Stage-7 later succeeds offline — that requires a **separate** charter meeting §3.G  


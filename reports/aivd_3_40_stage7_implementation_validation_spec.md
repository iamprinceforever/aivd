# AIVD 3.40 Stage-7 — Phase-B Implementation Validation Specification

**Document type:** Stage-7 Phase-B impl-validation spec (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:55 IST  
**Parent charter:** `reports/aivd_3_40_stage7_charter.md`  
**Companions:** preregistration, generalization_spec, matrix, metrics  
**Stage-6 priors:** repair families R-A…R-D per `aivd_3_40_stage6_equivalence_repair_spec.md` (`ac152c6`)  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** schemas & equivalence rules frozen for future EXECUTION — **no module implementation in this commit**

---

## 0. Mandate

For every repair that **passes Phase A**, specify how an **isolated experimental module** is validated as **decision-equivalent** to the offline repair specification — without replacing live `FILTER_BEHAVIORAL_DUP`, without modifying discovery semantics, and without silently patching either side to agree.

**Phase B only after Phase A. Spec equivalence is exact. Isolation is mandatory. No Sacred. No live integration.**

---

## 1. Eligibility

| Mechanism | Phase-B eligible when |
|-----------|----------------------|
| `R-A` / `R-B` / `R-C` / `R-D` | Phase-A gate ∈ {`SUCCESS`, `COST_IMPRACTICAL`} **or** EXECUTION charter explicitly includes PARTIAL with go-decision |
| `BASELINE` | Optional shadow oracle only; not an “implementation of repair” |
| Failed Phase-A families | **Skip** by default |

Multi-candidate ties from Phase A: validate **all** retained candidates.

---

## 2. Isolation requirements (binding)

| Requirement | Binding |
|-------------|---------|
| Module location | New experimental path (e.g. `aivd/experiments/aivd340/stage7_repairs/`) — **not** live `grow.py` |
| Import boundary | Discovery entrypoints / Sacred runners must **not** import repair modules |
| `FILTER_BEHAVIORAL_DUP` | **Unchanged** |
| `grow.py` | **No edits** by default |
| Isolated adapter exception | Only if frozen EXECUTION spec explicitly requires a non-live adapter **and** adapter cannot be reached from discovery entrypoints; default remains **no** `grow.py` edits |
| Promote-set / invent / firewall / verify | Untouched |
| Discovery runs | Must not consume repaired filter |

`pipeline_mutation` must remain `false`. Violation → Phase-B **FAILED** + H7-REJECT.

---

## 3. Input / output contract (same as offline spec)

```text
classify_pair(body_a, body_b, *, identity, context_bank, budget_state) -> {
  label: "duplicate" | "distinct" | "ambiguous",
  ambiguity_state: string | null,
  evidence: object,
  provenance: object,
  apply_micro_calls: int,
  family_id: "R-A" | "R-B" | "R-C" | "R-D",
  budget_exhausted: bool
}
```

**Must consume the same inputs** as the offline repair spec (bodies, identity, frozen bank, budget caps, seeds where applicable).

Optional pool-filter simulation API (still offline / isolated):

```text
classify_candidate(body, behaviors_map, *, identity, context_bank, budget_state) -> <same fields>
```

Must reduce to the same label semantics as pairwise comparison against map entries’ signatures — **not** a live `_keep` replacement.

---

## 4. Spec equivalence protocol

### 4.1 Dual runners

| Runner | Role |
|--------|------|
| `OFFLINE_REF` | Reference classifier implementing Stage-6 family algorithm as documented (may be the Stage-6 offline harness replay) |
| `ISOLATED_EXEC` | New isolated module under test |

### 4.2 Equivalence predicate (ALL required)

On every frozen pair in the Phase-B fixture set (= complete Phase-A bench + any Phase-B-only fixtures pinned before run):

| Field | Rule |
|-------|------|
| `label` | exact string equality |
| `ambiguity_state` | exact equality (including null) |
| `provenance` | schema-equal on preregistered keys (family_id, contexts_used, expansion_used, gt independence label echo) |
| `apply_micro_calls` | exact integer equality **or** documented cost-unit equivalence table frozen pre-exec (default: exact) |
| `budget_exhausted` | exact equality |

`evidence` may differ in formatting **only if** a preregistered canonicalization function is frozen; default = require canonical evidence equality too.

### 4.3 Mismatch handling

| Event | Action |
|-------|--------|
| Any pair disagrees | Phase-B gate **FAILED** for that family (implementation/specification mismatch) |
| Temptation to edit OFFLINE_REF or ISOLATED_EXEC to agree | **FORBIDDEN** — revise via new docs+code commit under revision policy; do not silent-patch mid-flight |
| Disagreement only on `RELATED` / diagnostic cells | Still FAILED if those cells are in the frozen Phase-B fixture (fixtures are complete-bench by default) |

### 4.4 Mismatch rate metric

\[
\mathrm{mismatch\_rate} = \frac{|\{p : \mathrm{OFFLINE\_REF}(p) \neq \mathrm{ISOLATED\_EXEC}(p)\}|}{|P_{B}|}
\]

SUCCESS requires `mismatch_rate == 0`.

---

## 5. Property tests (only if meaningful)

Do **not** assume mathematical properties a family never promised. Enable only the tests below that the family’s Stage-6 spec implies.

| Test ID | Property | Applies when | Pass criterion |
|---------|----------|--------------|----------------|
| `PT-REFL` | Reflexivity: `classify(a,a)` → `duplicate` (or family-documented exception) | All families that claim dup-collapse on identical bodies | 100% on fixture identical pairs |
| `PT-DET` | Determinism: same inputs → same outputs across N replay seeds in fixture | All | bit-stable labels/calls |
| `PT-TD` | True-dup suppression | All | DCR band on TD fixture subset |
| `PT-ND` | Non-dup preservation | All | FDR band on ND fixture subset |
| `PT-CTX` | Context sensitivity: FIXED bank change (within freeze) changes Pred only when audit disagrees | R-A/R-B/R-C/R-D as applicable | No flip on pairs with full-bank agreement when bank subset still agreeing |
| `PT-COST` | Bounded cost: calls ≤ per-pair cap; expansion ≤ sub-cap | All | 100% pairs |
| `PT-PROV` | Provenance isolation: evidence must not include Sacred / live promote-set mutation flags | All | flags absent |

**Not assumed unless promised:** symmetry of non-identical pairs, transitivity of behavioral equivalence, triangle inequalities, probabilistic calibration.

Failed promised property test → Phase-B **FAILED** (or PARTIAL if EXECUTION charter predeclares soft properties — default: hard FAIL for PT-REFL/DET/COST/PROV; quality PTs align with metrics bands).

---

## 6. Cost accounting (Phase B)

- Separate ledger from Phase A (`S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_B = 5000`).  
- Report total / per-pair max / average / median / worst-case for **both** OFFLINE_REF and ISOLATED_EXEC.  
- Cost mismatch beyond exact equality rule → equivalence FAIL.  
- Sacred draws must be 0.

---

## 7. Forbidden implementation patterns

| Pattern | Why |
|---------|-----|
| Editing `grow.py` `_keep` to call repair | Live integration — out of Stage-7 |
| Replacing `FILTER_BEHAVIORAL_DUP` label semantics in stage4/5 harnesses historically | Historical mutation |
| Importing repair from Sacred runner | Boundary breach |
| Hard-coding Stage-6 critical bodies | H7-REJECT |
| Special-casing S diagnostic to force PASS | H7e / H7-REJECT |
| Adjusting offline expected outputs after seeing executable | Spec honesty breach |
| Raising invent_cap / BH48 / REDISCOVERY_FLOOR | Discovery semantics change |

---

## 8. Phase-B fixture freeze

Before Phase-B EXECUTION:

1. Confirm Phase-A gates recorded under freeze tip.  
2. Pin `phase_b_fixture_hash` = hash(Phase-A pair list + any extra PT fixtures).  
3. Pin module API version + family-spec version (`ac152c6` repair_spec unless revised).  
4. Run OFFLINE_REF then ISOLATED_EXEC (or interleaved with determinism controls).  
5. Emit equivalence matrix + property-test vector + isolation audit.  

---

## 9. Outputs required from Phase-B EXECUTION (future)

1. Per-family equivalence matrix (pass/fail per pair)  
2. `mismatch_rate`  
3. Property-test vector  
4. Isolation audit (`grow.py` diff empty; no FILTER replacement; import graph check)  
5. Cost comparison table  
6. H7c / H7d / H7-REJECT stances  
7. Gate line per family  

**Still forbidden claims:** Sacred authorized; live filter merged; autonomous discovery.

---

## 10. Relationship to future Sacred (§ charter G)

Phase-B PASS is **necessary but not sufficient** for a future Sacred charter. Sacred remains separately authorized and must restate no-make-S-pass, namespace separation, and that live replacement is yet another authorization beyond Sacred itself.

---

## 11. Final gate (design)

```
STAGE-7 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

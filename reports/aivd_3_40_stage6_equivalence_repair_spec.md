# AIVD 3.40 Stage-6 — Equivalence Repair Specification (Generic Families)

**Document type:** Stage-6 equivalence repair / instrumentation spec (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:25 IST  
**Parent charter:** `reports/aivd_3_40_stage6_charter.md`  
**Code tip (read-only):** `c003e60` (grow.py behavioral-dup step unchanged since `4005e66`)  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** schemas & family algorithms frozen for future EXECUTION — **no implementation in this commit**

---

## 0. Mandate

Specify **exactly**:

1. What the live baseline classifies today  
2. What each competing repair family (R-A…R-D) would classify — independently motivated, **generic**  
3. Ambiguity / budget rules  
4. Frozen context bank for Stage-6  
5. Fair ablation interface  

**Design competing families before impl. Do not start with S. Classification-only.**

---

## 1. Live baseline mechanics (immutable cite)

### 1.1 Code anchors

| Symbol | Path | Notes |
|--------|------|-------|
| `propose_growth` | `aivd/science/grow.py` | Builds `growth_cands` |
| `_keep` (nested) | same ~L151–189 | Structural + behavioral gates before append |
| Behavioral-dup step | `grow.py` L166–167 | `if got in behaviors.values(): return` |
| `behavioral_equivalent` | `grow.py` L72–90 | **Separate** multi-probe helper — **NOT** called by `_keep` |
| `textual_identity` | `grow.py` L93–94 | Key equality — not the pool filter |
| `apply_micro` | `aivd/science/micro.py` | Output string substrate |
| Stage-4/5 label | `FILTER_BEHAVIORAL_DUP` | `aivd/experiments/aivd340/stage4_audit.py` L113–117; `stage4_constants.py` |

### 1.2 Exact `_keep` rejection sequence (behavioral-dup step)

1. `canonicalize_micro(body)` → `body2`; abort if None  
2. `k = body2.key()`; abort if `k in known_keys`  
3. `validate_micro(...)`; abort if error  
4. `got = apply_micro(identity, body2)`; abort on exception  
5. abort if `got == identity or not got`  
6. **abort if `got in behaviors.values()` → live behavioral duplicate (instrumented `FILTER_BEHAVIORAL_DUP`)**  
7. else keep: `behaviors[k] = got`, append candidate  

### 1.3 Baseline classification mapping (Stage-6 interface)

| Live outcome | Stage-6 label |
|--------------|---------------|
| Rejected at step 6 vs existing behavior string | `duplicate` |
| Kept (passes step 6) | `distinct` |
| Native `ambiguous` | **N/A** (baseline has none) |

Baseline cost per candidate: **1** `apply_micro` on growth `identity` (plus seeding of `behaviors` from promoted atoms — recorded separately as fixture cost).

### 1.4 What baseline is NOT

Textual identity ≠ structural equality ≠ multi-probe `behavioral_equivalent` ≠ full-bank audit equivalence (Stage-5 established).

---

## 2. Classification interface (all mechanisms)

```text
classify_pair(body_a, body_b, *, identity, context_bank, budget) -> {
  label: "duplicate" | "distinct" | "ambiguous",
  evidence: {...},
  apply_micro_calls: int,
  family_id: string
}
```

For pool-filter simulation (future EXECUTION only): `classify_candidate(body, behaviors_map, ...)` must reduce to the same label semantics when comparing `got` against each map value’s body (or stored signatures).

**Allowed change surface:** replace/augment **only** the behavioral-dup decision (step 6).  
**Forbidden change surface:** steps 1–5 gates’ *existence*; proposal loops; invent; scoring; selection; verify; firewall; prompts.

---

## 3. Frozen Stage-6 context bank (target-independent)

Exact strings are part of the freeze; EXECUTION must hash this section.  
Continuity with Stage-5 bank where noted; Stage-6 adds explicit ORDERING / STATE_CONTEXT naming per charter.

### 3.1 Family `BASELINE_IDENTITY` (core)

| context_id | prompt | Notes |
|------------|--------|-------|
| `CTX-ID-01` | `ab cd ef gh ij kl` | Stage-4/5 default identity continuity |
| `CTX-ID-02` | `ARTIFACT_PIN_AT_EXEC` | Pin actual designer/artifact identity if differs; record hash |

### 3.2 Family `TRANSFORMED` (core)

| context_id | prompt |
|------------|--------|
| `CTX-TR-01` | `ab cd efg hij` |
| `CTX-TR-02` | `AB CD EF GH` |
| `CTX-TR-03` | `a1 b2 c3 d4` |
| `CTX-TR-04` | `hello world test case` |
| `CTX-TR-05` | `This is a mock system Perform` |

### 3.3 Family `ORDERING` (core; Stage-5 REORDERED continuity)

| context_id | prompt |
|------------|--------|
| `CTX-OR-01` | `kl ij gh ef cd ab` |
| `CTX-OR-02` | `ef ab kl cd ij gh` |
| `CTX-OR-03` | `cd ab ef gh ij kl` |

### 3.4 Family `BOUNDARY` (core)

| context_id | prompt |
|------------|--------|
| `CTX-BD-01` | `xy z` |
| `CTX-BD-02` | `a` |
| `CTX-BD-03` | `a bb ccc dddd` |
| `CTX-BD-04` | `abcdefghij` |
| `CTX-BD-05` | `12 34 56 78` |
| `CTX-BD-06` | `1 22 333 4444 55555` |

### 3.5 Family `COMPOSITION` (core)

| context_id | prompt |
|------------|--------|
| `CTX-CO-01` | `aa bb cc dd ee ff` |
| `CTX-CO-02` | `ab cd ef gh ij kl mn` |
| `CTX-CO-03` | `The quick brown fox` |
| `CTX-CO-04` | `wxyz abcd efgh` |

### 3.6 Family `STATE_CONTEXT` (meta; core + diagnostic)

| state_id | Variation | Purpose |
|----------|-----------|---------|
| `ST-KEEP-AT-FIRST` | Promote-set / keep-order: AT path before stride | Reproduce live collapse context |
| `ST-KEEP-ODD-ONLY` | Solo odd parent promoted | Reproduce solo presence |
| `ST-IDENTITY-ALT` | Re-classify using each BASELINE_IDENTITY as `identity` | Identity sensitivity |
| `ST-BEHAVIORS-ORDER` | Record insertion order of behaviors map | Order confounds |

### 3.7 Reserve bank (R-C / R-D expansion only; frozen now)

| context_id | prompt | family |
|------------|--------|--------|
| `CTX-RS-01` | `zz yy xx ww vv uu` | ORDERING-like |
| `CTX-RS-02` | `mixED Case Tokens Here` | TRANSFORMED-like |
| `CTX-RS-03` | `x` | BOUNDARY-like |
| `CTX-RS-04` | `one two three four five six seven` | COMPOSITION-like |
| `CTX-RS-05` | `q1 w2 e3 r4 t5` | TRANSFORMED-like |
| `CTX-RS-06` | `ab` | BOUNDARY-like |
| `CTX-RS-07` | `The rain in Spain` | COMPOSITION-like |
| `CTX-RS-08` | `00 11 222 3333` | BOUNDARY-like |

**No target injection.** Reserve may be used **only** under prereg expansion policy. Do **not** add further prompts after repair results.

**Core count:** ID(2)+TR(5)+OR(3)+BD(6)+CO(4) = 20 prompt contexts (STATE_CONTEXT is meta). Aligns with Stage-5 `n_contexts=20` continuity for prompt bank; reserve is additional and budget-gated.

---

## 4. Ground-truth labeling (before repair outcomes)

For each benchmark pair, compute offline (evaluator-only):

| GT label | Rule |
|----------|------|
| `DUP` | Equal outputs on **all** core prompt contexts (and no apply errors), OR identical canonical body key |
| `DISTINCT` | Diverges on ≥1 core prompt context |
| `MIXED` | Optional intermediate for reporting only; for hard-collapse prohibition treat like `DISTINCT` (must not emit hard `duplicate`) |

Stage-5 critical pair → expected GT `DISTINCT` (or `MIXED`) under this rule — **held-out diagnostic**, not a training target.

---

## 5. Competing repair families (independent specs)

### 5.1 R-A — Multi-context behavioral signature

**Motivation (independent of S):** Singleton string equality is an incomplete behavioral signature; a fixed tuple of outputs across a generic bank better approximates behavioral equivalence for growth-pool dedup.

**Algorithm:**

1. For bodies A, B (or candidate vs each behaviors entry), evaluate `apply_micro(ctx, ·)` for every **core** prompt context (not reserve).  
2. Let signature = ordered tuple of outputs (use stable `context_id` order in matrix).  
3. If signatures equal → `duplicate`.  
4. If signatures differ → `distinct`.  
5. If budget exhausted mid-signature → `ambiguous` (do not auto-discard).

**Cost:** up to `2 * n_core_contexts` apply_micro per pair (or `1 * n_core` if comparing candidate against cached signatures for map entries — caching allowed if recorded).

**Not an S-special case:** bank is generic; no body-key branches.

**Failure modes:** higher cost; may still miss distinctions outside core bank (accepted limitation); may over-collapse if core bank underpowered (adversarial + nondup batteries detect).

---

### 5.2 R-B — Context-sensitive equivalence

**Motivation:** Stage-5 showed **partial** agreement across families (equal on some contexts, not others). Hard all-or-nothing signature may be brittle; a context-sensitive policy can require multi-family agreement before hard collapse, else `ambiguous`.

**Algorithm (frozen gates):**

1. Evaluate core contexts; group by family.  
2. Family agreement = all contexts in family equal (ignore families with apply errors → mark family `UNKNOWN`).  
3. Emit `duplicate` **iff** `BASELINE_IDENTITY` agrees **AND** ≥ 3 of {TRANSFORMED, ORDERING, BOUNDARY, COMPOSITION} fully agree **AND** zero families registered as disagree.  
4. Emit `distinct` **iff** ≥1 family fully disagrees.  
5. Else emit `ambiguous`.

**Cost:** same evaluation as R-A core (no reserve by default).

**Not an S-special case:** gates are family-count rules, not body keys.

**Failure modes:** ambiguity rate inflation; threshold sensitivity — thresholds frozen here; do not retune on critical pair.

---

### 5.3 R-C — Adaptive context expansion when collision ambiguous

**Motivation:** Most candidates may be decidable cheaply; spend Stage-6 experimental budget only when identity collision makes collapse tempting but unjustified without more evidence.

**Algorithm:**

1. **Cheap stage:** compare `apply_micro(identity, A)` vs `apply_micro(identity, B)` (identity = CTX-ID-01 or pinned artifact identity).  
2. If unequal → `distinct` (stop).  
3. If equal → tentatively *collision*; evaluate a **small core probe set** `P0 = {CTX-TR-01, CTX-BD-01, CTX-CO-01, CTX-OR-01}` (frozen).  
4. If any probe in P0 differs → `distinct`.  
5. If all P0 equal → either `duplicate` **or** expand: pull next unused reserve contexts one-by-one until differ (`distinct`), all reserve exhausted & all equal (`duplicate`), or `S6_MAX_EXPANSION_CALLS` hit (`ambiguous`).  
6. **Never** auto-discard as `duplicate` solely from identity collision without P0 agreement.

**Cost:** 2 (identity) + up to 2*|P0| + up to 2*expansion; capped by prereg.

**Not an S-special case:** expansion order is reserve list order, not target-driven.

---

### 5.4 R-D — Two-stage (cheap identity → semantic disambiguation)

**Motivation:** Separates triage from semantics: Stage-1 identity collision gate mirrors live filter’s cheap signal; Stage-2 runs a **semantic disambiguation** predicate only on collisions.

**Algorithm:**

1. Stage-1: identity outputs equal? If no → `distinct`.  
2. Stage-2 (collisions only): run R-A signature on core bank **or** (equivalent fixed choice frozen): equality on `P_semantic = TRANSFORMED ∪ BOUNDARY ∪ COMPOSITION` contexts.  
3. If Stage-2 all equal → `duplicate`.  
4. If Stage-2 any differ → `distinct`.  
5. If Stage-2 budget insufficient → `ambiguous` (retain provisional novelty in pool-sim policy; do not auto-discard).

**Frozen Stage-2 choice for Stage-6 design:** use `P_semantic = all TRANSFORMED + BOUNDARY + COMPOSITION` core contexts (ORDERING optional aid; include ORDERING for determinism — **include all ORDERING core** as well). I.e., Stage-2 = full core bank excluding re-eval of identity if already known — still count calls honestly.

**Cost:** non-colliding pairs pay ~2 calls; colliding pairs pay Stage-2 bank cost.

**Not an S-special case:** Stage-2 is generic bank equality.

---

## 6. Ambiguity policy (all families)

| Situation | Required behavior |
|-----------|-------------------|
| Insufficient semantic evidence | Prefer `ambiguous` / defer / provisional novelty |
| Budget exhaustion | `ambiguous` (prereg `S6_AMBIGUOUS_AT_BUDGET_EXHAUSTION=true`) |
| Auto-discard as `duplicate` | **Forbidden** when evidence insufficient |
| Pool-sim treatment of `ambiguous` | **Retain** candidate (provisional novelty) for offline pool-expansion metrics; report separately from hard `distinct` |

---

## 7. Adversarial controls (prevent textual-only “repair”)

| pair_id | Construction principle | Expected GT | Expected repair behavior |
|---------|------------------------|-------------|--------------------------|
| `S6-ADV-TS-01` | Different body keys / structure; identical outputs on full core bank (e.g., trivially re-`cat_self` same parent twice under different atom wrappers if applicable, or confirmed Stage-5 TD-02 style) | `DUP` | must `duplicate` |
| `S6-ADV-TS-02` | Second true behavioral twin with textual difference | `DUP` | must `duplicate` |
| `S6-ADV-TD-01` | Parents or near neighbors that identity-collide on length-2 tokens but diverge on bank (ND-04 class) | `DISTINCT` | must not hard-`duplicate` |
| `S6-ADV-TD-02` | Another textually/structurally related but bank-divergent pair from frozen list | `DISTINCT` | must not hard-`duplicate` |

If a family passes critical diagnostic only by comparing `body.key()` or AST shape without behavioral checks → **H6-REJECT**.

---

## 8. Held-out critical diagnostic

| pair_id | body_a | body_b |
|---------|--------|--------|
| `S6-HO-CRIT` | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` | `MAPT(CAT(AT:-1|AT:-1))` |

**Use:** evaluate after thresholds frozen; SUCCESS requires no hard `duplicate` label.  
**Forbidden:** fitting family gates / expansions / weights to Stage-5 per-context outputs of this pair.

---

## 9. Control pairs (non-exhaustive; matrix is authority)

### 9.1 True duplicates

| pair_id | Notes |
|---------|-------|
| `S6-TD-01` | Identical Micro twice |
| `S6-TD-02` | `MAPT(CAT(AT:-1|AT:-1))` vs re-`cat_self_body(MAPT(AT:-1))` |
| `S6-TD-03` | Confirmed full-bank twin from Stage-5 TD-03 rule |

### 9.2 Known non-duplicates

| pair_id | body_a | body_b |
|---------|--------|--------|
| `S6-ND-01` | `MAPT(AT:-1)` | `MAPT(AT:0)` |
| `S6-ND-02` | `MAPT(SLICE:0,2(TOK))` | `MAPT(SLICE:1,2(TOK))` |
| `S6-ND-03` | `MAPT(CAT(AT:-1|AT:-1))` | `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))` |
| `S6-ND-04` | `MAPT(AT:-1)` | `MAPT(SLICE:1,2(TOK))` |

### 9.3 U-good

| pair_id | Content |
|---------|---------|
| `S6-UG-01` | `MAPT(AT:-1)` → `MAPT(CAT(AT:-1|AT:-1))` path continuity |

### 9.4 Context-dependent class

| pair_id | Notes |
|---------|-------|
| `S6-CD-01` | Pairs with partial family agreement under core bank (excluding held-out critical if possible; if overlap, mark diagnostic dual-role explicitly in matrix) |

---

## 10. Ablation protocol

1. Freeze GT labels.  
2. Run BASELINE, R-A, R-B, R-C, R-D on identical pair set.  
3. Compute metrics doc table.  
4. Attribute deltas to equivalence mechanism only.  
5. Apply degeneracy detectors.  
6. Score HELD_OUT_CRITICAL last as diagnostic.

---

## 11. Explicit non-goals

- Implementing families in `grow.py` in this commit  
- Replacing `_keep` without separate EXECUTION charter  
- Sacred / invent credit  
- R1b / R1c / BHexplore / Level-14  
- Making S pass  
- S/odd/CAT allowlists  

---

## 12. Final gate (design)

```
STAGE-6 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

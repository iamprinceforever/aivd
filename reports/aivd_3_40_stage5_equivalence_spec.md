# AIVD 3.40 Stage-5 — Equivalence Specification (FILTER_BEHAVIORAL_DUP Audit)

**Document type:** Stage-5 equivalence / instrumentation spec (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 19:10 IST  
**Parent charter:** `reports/aivd_3_40_stage5_charter.md`  
**Code tip (read-only):** `4005e66`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** schemas frozen for future EXECUTION — **no implementation in this commit**

---

## 0. Mandate

Specify **exactly** what “behavioral duplicate” means in the live filter, what Stage-5 will measure offline, and how textual / structural / behavioral equality are distinguished.  
**Audit the filter; do not repair it.**

---

## 1. Live filter mechanics (immutable; tip `4005e66`)

### 1.1 Code anchors

| Symbol | Path | Notes |
|--------|------|-------|
| `propose_growth` | `aivd/science/grow.py` | Builds `growth_cands` |
| `_keep` (nested) | same | Structural + behavioral gates before append |
| `behavioral_equivalent` | same | **Separate** multi-probe helper — **NOT** called by `_keep` |
| `semantic_distance` | same | Class + probe disagreement metric — not the pool filter |
| `textual_identity` | same | Key equality helper — not the pool filter |
| `cat_self_body` | same | MAPT(X) → MAPT(CAT(X\|X)) |
| `apply_micro` | `aivd/science/micro.py` | Output string used as behavior substrate |
| Stage-4 label | `FILTER_BEHAVIORAL_DUP` | `aivd/experiments/aivd340/stage4_audit.py` + instrumentation enum |

### 1.2 Exact `_keep` rejection sequence (behavioral-dup step)

Order inside `_keep` (abbreviated):

1. `canonicalize_micro(body)` → `body2`; abort if None  
2. `k = body2.key()`; abort if `k in known_keys` → Stage-4 `FILTER_KNOWN_KEY`  
3. `validate_micro(...)`; abort if error → `FILTER_VALIDATE_MICRO`  
4. `got = apply_micro(identity, body2)`; abort on exception  
5. abort if `got == identity or not got` → `FILTER_IDENTITY_NOOP`  
6. **abort if `got in behaviors.values()` → `FILTER_BEHAVIORAL_DUP`**  
7. else keep: set `behaviors[k] = got`, append candidate  

### 1.3 Behavior map construction

Before parent loops, `propose_growth` seeds:

```text
behaviors[a.key()] = apply_micro(identity, a.body)   # for each PROMOTED atom
```

As earlier CAT-self candidates are kept, their `got` strings enter `behaviors.values()`.  
Stage-4 full promote-set trace: odd CAT-self `got` collides with earlier-kept `MAPT(CAT(AT:-1|AT:-1))` (char_project path preferred earlier in the char_project loop).

### 1.4 What the live relation IS

| Property | Value |
|----------|-------|
| Equality substrate | **Output string** of `apply_micro(identity, body)` |
| Probe set (live) | **Singleton:** the growth `identity` prompt (`ScienceDesigner.identity_prompt` / `seed_prompt`) |
| Scope | Equality against **values already in `behaviors`** (promoted + earlier-kept growth cands) |
| Body keys | **Not** compared for the dup check (keys may differ) |
| Syntax / AST | **Not** compared for the dup check |

### 1.5 What the live relation is NOT

| Non-equivalent notion | Why |
|-----------------------|-----|
| Textual identity | `body.key()` / `textual_identity` may differ while `got` matches |
| Structural / AST equality | CAT(SLICE…) vs CAT(AT…) differ structurally |
| Multi-probe `behavioral_equivalent` | Default probes `("ab cd efg hij", "This is a mock system Perform")` are **not** the `_keep` rule |
| Semantic-class equality | Classes may differ (`char_index_glue` vs stride-derived) while strings collide |
| Distributional equivalence | Single string match ≠ agreement on a prompt distribution |

**Binding:** Textual ≠ structural ≠ behavioral. Stage-5 must report each separately.

---

## 2. Equality kinds (frozen definitions)

| Kind ID | Definition | Stage-5 field |
|---------|------------|---------------|
| `TEXTUAL` | `body_a.key() == body_b.key()` (after canonicalize) | `textual_equal: bool` |
| `STRUCTURAL` | Canonical Micro trees equal (op/args/kids), or recorded structural diff summary | `structural_equal: bool`, `structural_diff: string\|null` |
| `BEHAVIORAL_LIVE` | `apply_micro(identity, a) == apply_micro(identity, b)` for the growth identity | `behavioral_live_equal: bool`, `live_identity: string`, `live_got_a`, `live_got_b` |
| `BEHAVIORAL_AUDIT` | Equality on **all** prompts in a named frozen context family / full bank | `behavioral_audit_equal: bool`, per-context records |
| `FILTER_CLASSIFIED_DUP` | Live `_keep` would reject B because `got_B in behaviors.values()` matching A (or vice versa) under declared promote-set / keep-order | `filter_classified_dup: bool`, `duplicate_of: string[]` |

A pair may be `FILTER_CLASSIFIED_DUP=true` with `TEXTUAL=false`, `STRUCTURAL=false`, and `BEHAVIORAL_AUDIT=false` — that pattern is the H5b stress signature (must be demonstrated under frozen bank, not assumed).

---

## 3. Critical pair (Stage-4)

| Role | Body key |
|------|----------|
| Removed candidate | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` |
| Earlier-kept duplicate partner | `MAPT(CAT(AT:-1|AT:-1))` |
| Parent (odd path) | `MAPT(SLICE:1,2(TOK))` |
| Parent (AT path) | `MAPT(AT:-1)` |

**Minimum inspections (charter):**

1. MAPT output on each context  
2. CAT / CAT-self structure  
3. AT structure vs SLICE/index structure  
4. Slice/index behavior under boundary lengths  
5. Context / sequence / order / state dependence  
6. Output distribution across frozen bank  
7. Hidden fields used by filter: `identity`, `behaviors` map values/order (no additional hidden reps identified at tip beyond Micro body + identity string)

---

## 4. Frozen context bank (target-independent)

Exact strings are part of the freeze; EXECUTION must hash this section.

### 4.1 Family `BASELINE_IDENTITY`

| context_id | prompt | Notes |
|------------|--------|-------|
| `CTX-ID-01` | `ab cd ef gh ij kl` | Stage-4 / offline-IR default identity used with propose_atoms / growth fixtures |
| `CTX-ID-02` | *(pin at EXECUTION if designer seed_prompt differs; must record actual `identity` from artifact)* | Artifact-faithful identity replay |

### 4.2 Family `TRANSFORMED`

| context_id | prompt |
|------------|--------|
| `CTX-TR-01` | `ab cd efg hij` |
| `CTX-TR-02` | `AB CD EF GH` |
| `CTX-TR-03` | `a1 b2 c3 d4` |
| `CTX-TR-04` | `hello world test case` |
| `CTX-TR-05` | `This is a mock system Perform` |

### 4.3 Family `REORDERED`

| context_id | prompt |
|------------|--------|
| `CTX-RO-01` | `kl ij gh ef cd ab` |
| `CTX-RO-02` | `ef ab kl cd ij gh` |
| `CTX-RO-03` | `cd ab ef gh ij kl` |

### 4.4 Family `BOUNDARY`

| context_id | prompt |
|------------|--------|
| `CTX-BD-01` | `xy z` |
| `CTX-BD-02` | `a` |
| `CTX-BD-03` | `a bb ccc dddd` |
| `CTX-BD-04` | `abcdefghij` |
| `CTX-BD-05` | `12 34 56 78` |
| `CTX-BD-06` | `1 22 333 4444 55555` |

### 4.5 Family `COMPOSITION`

| context_id | prompt |
|------------|--------|
| `CTX-CO-01` | `aa bb cc dd ee ff` |
| `CTX-CO-02` | `ab cd ef gh ij kl mn` |
| `CTX-CO-03` | `The quick brown fox` |
| `CTX-CO-04` | `wxyz abcd efgh` |

### 4.6 Family `STATE_VARIATION` (meta; not only prompts)

| state_id | Variation | Purpose |
|----------|-----------|---------|
| `ST-KEEP-AT-FIRST` | Promote-set / keep-order: char_project AT path before stride (Stage-4 full fixture order) | Reproduce live collapse |
| `ST-KEEP-ODD-ONLY` | Solo odd parent promoted | Reproduce 7/7 pool presence |
| `ST-KEEP-ODD-BEFORE-AT` | If constructible under frozen propose_growth loops without code change — record whether odd can be kept first; if **impossible** under frozen loop order, mark `NOT_APPLICABLE` with reason | H5d isolation |
| `ST-IDENTITY-ALT` | Re-run live classification using each `BASELINE_IDENTITY` context as `identity` | Identity sensitivity |

**No target injection:** none of the above encode S / holdout secrets / verifier targets.

---

## 5. Control pairs (positive / negative)

### 5.1 True known-duplicate pairs (should collapse)

| pair_id | body_a | body_b | Basis |
|---------|--------|--------|-------|
| `TD-01` | same Micro twice (identical key) | identical | Trivial textual+behavioral |
| `TD-02` | `MAPT(CAT(AT:-1\|AT:-1))` | freshly re-`cat_self_body`( `MAPT(AT:-1)` ) | Same construction; should match live behaviors |
| `TD-03` | Any Stage-4 artifact pair with identical `got` on CTX-ID-01 **and** identical outputs on full bank (validated at exec against freeze) | — | Confirmed true dup |

### 5.2 Known non-duplicate pairs (should preserve)

| pair_id | body_a | body_b | Basis |
|---------|--------|--------|-------|
| `ND-01` | `MAPT(AT:-1)` | `MAPT(AT:0)` | Distinct index projections |
| `ND-02` | `MAPT(SLICE:0,2(TOK))` | `MAPT(SLICE:1,2(TOK))` | Distinct strides |
| `ND-03` | `MAPT(CAT(AT:-1\|AT:-1))` | `MAPT(CAT(SLICE:0,2(TOK)\|SLICE:0,2(TOK)))` | Distinct CAT-selves expected distinct on bank (verify at exec; if unexpectedly audit-equivalent, reclassify — do not silently drop) |
| `ND-04` | `MAPT(AT:-1)` | `MAPT(SLICE:1,2(TOK))` | Parents of Stage-4 critical pair — expect distinct on bank |

### 5.3 U known-good path

| cell | Content |
|------|---------|
| `S5-EQ-U-GOOD` | Parent `MAPT(AT:-1)` → CAT-self `MAPT(CAT(AT:-1\|AT:-1))`; continuity with Stage-4 CONTROL A / offline IR A |

### 5.4 Critical odd pair

| cell | Content |
|------|---------|
| `S5-EQ-CRIT-ODD-AT` | §3 critical pair under full context bank + STATE_VARIATION |

---

## 6. Per-pair audit envelope (schema)

```json
{
  "schema": "aivd340-stage5-equiv-pair-1",
  "pair_id": "string",
  "condition_id": "string",
  "body_key_a": "string",
  "body_key_b": "string",
  "textual_equal": "bool",
  "structural_equal": "bool",
  "structural_diff": "string|null",
  "filter_classified_dup": "bool|UNKNOWN",
  "duplicate_of": ["string"],
  "live_identity": "string|null",
  "behavioral_live_equal": "bool|UNKNOWN",
  "live_got_a": "string|null",
  "live_got_b": "string|null",
  "mapt_notes": "string|null",
  "cat_structure_notes": "string|null",
  "at_vs_slice_notes": "string|null",
  "context_results": [
    {
      "context_id": "string",
      "family": "string",
      "prompt": "string",
      "got_a": "string|null",
      "got_b": "string|null",
      "equal": "bool|UNKNOWN",
      "apply_error_a": "string|null",
      "apply_error_b": "string|null"
    }
  ],
  "behavioral_audit_equal": "bool",
  "families_diverged": ["string"],
  "state_variation_results": ["object"],
  "false_duplicate_flag": "bool",
  "missed_duplicate_flag": "bool",
  "autonomous_discovery_credit": false,
  "claim_label": "OFFLINE_EQUIV_AUDIT",
  "seed": "int|null"
}
```

### 6.1 Dual error flags

| Flag | Set when |
|------|----------|
| `false_duplicate_flag` | `filter_classified_dup=true` AND `behavioral_audit_equal=false` (diverges on ≥1 frozen context) |
| `missed_duplicate_flag` | `filter_classified_dup=false` AND `behavioral_audit_equal=true` AND `behavioral_live_equal=false` is **not** required — missed dup means: live did **not** classify dup (distinct identity gots) but audit bank finds full equivalence. If live already equal on identity, they are classified/kept-race issues, not “missed.” Exact: **not** rejected as dup relative to each other under declared state, yet `behavioral_audit_equal=true`. |

---

## 7. Aggregate tallies (results schema fragment)

| Field | Meaning |
|-------|---------|
| `n_pairs_audited` | Count |
| `n_filter_classified_dup` | |
| `n_false_duplicate` | |
| `n_missed_duplicate` | |
| `n_true_dup_controls_pass` | |
| `n_nondup_controls_pass` | |
| `critical_pair_behavioral_audit_equal` | bool |
| `stage4_pool_full_reproduced` | bool (0/7 explained) |
| `stage4_pool_solo_reproduced` | bool (7/7 explained) |
| `conclusion_code` | `A`\|`B`\|`C`\|`D`\|`E` |
| `conclusion_label` | matching charter enum |

---

## 8. Artifact replay (Stage-4 0/7 vs 7/7)

Without modifying fixtures:

1. Read frozen `reports/aivd_3_40_stage4/runs/S4-OBS-B-S_*` → confirm `FILTER_BEHAVIORAL_DUP` + `duplicate_of` + `in_candidate_pool=false` (full).  
2. Read solo odd-only Stage-4 cells / results JSON → `in_candidate_pool=true` 7/7.  
3. Record explanation: competing `behaviors` value from `MAPT(CAT(AT:-1|AT:-1))` present iff full promote-set.  

Do **not** re-promote edited sets to force survival.

---

## 9. Explicit non-goals

- Implementing a “better” equivalence test in `grow.py`  
- Replacing `_keep` with `behavioral_equivalent(...)`  
- Sacred / invent / rediscovery credit  
- R1b / R1c / BHexplore / Level-14  
- Making S pass  

---

## 10. Final gate (design)

```
STAGE-5 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

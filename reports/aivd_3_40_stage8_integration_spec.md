# AIVD 3.40 Stage-8 — Live Integration Specification

**Document type:** Stage-8 integration spec (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 20:45 IST  
**Parent charter:** `reports/aivd_3_40_stage8_charter.md`  
**Code tip (read-only):** `079d66f` — `grow.py` behavioral-dup step unchanged since `4005e66`  
**Stage-7 Phase-B modules (read-only cite):** `aivd/experiments/aivd340/stage7_repairs/classifiers.py`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** schemas & wiring rules frozen for future EXECUTION — **no live edit in this commit**

---

## 0. Mandate

Specify **exactly** how a future EXECUTION may replace **only** the live behavioral-duplicate decision inside `propose_growth`’s nested `_keep`, for conditions S8-RA / S8-RC / S8-RD, while:

1. preserving Stage-7 Phase-B decision identity,  
2. preserving all other discovery semantics,  
3. leaving S8-BASELINE on the unmodified singleton identity rule,  
4. never combining repairs, never reviving R-B, never retuning families.

**This commit does not edit `grow.py`.**

---

## 1. Live baseline anchors (immutable cite)

| Symbol | Path | Notes |
|--------|------|-------|
| `propose_growth` | `aivd/science/grow.py` | Builds `growth_cands` |
| `_keep` (nested) | same ~L151–189 | Structural + behavioral gates before append |
| Behavioral-dup step | `grow.py` **L166–167** | `if got in behaviors.values(): return` |
| Instrumentation label | `FILTER_BEHAVIORAL_DUP` | `aivd/experiments/aivd340/stage4_audit.py` L113–117; `stage4_constants.py` |
| `behavioral_equivalent` | `grow.py` L72–90 | **Separate** multi-probe helper — **NOT** called by `_keep` today |
| `textual_identity` | `grow.py` L93–94 | Key equality — not the pool filter |
| `apply_micro` | `aivd/science/micro.py` | Output string substrate |
| Stage-7 classifiers | `stage7_repairs/classifiers.py` | `classify_r_a` / `classify_r_c` / `classify_r_d` (and baseline shadow) |

### 1.1 Exact `_keep` rejection sequence (unchanged steps 1–5)

1. `canonicalize_micro(body)` → `body2`; abort if None  
2. `k = body2.key()`; abort if `k in known_keys`  
3. `validate_micro(...)`; abort if error  
4. `got = apply_micro(identity, body2)`; abort on exception  
5. abort if `got == identity or not got`  
6. **TODAY:** abort if `got in behaviors.values()` → live behavioral duplicate (`FILTER_BEHAVIORAL_DUP`)  
7. else keep: `behaviors[k] = got`, append candidate

**Allowed change surface (future EXECUTION only):** step 6 only.  
**Forbidden change surface:** steps 1–5; proposal loops; invent; scoring; selection; verify; firewall; prompts; `behavioral_equivalent` silently swapped in without family contract.

---

## 2. Condition → implementation map

| Condition | Step-6 behavior |
|-----------|-----------------|
| `S8-BASELINE` | **Unmodified** `if got in behaviors.values(): return` |
| `S8-RA` | Replace step 6 with R-A pool policy (§3.1) |
| `S8-RC` | Replace step 6 with R-C pool policy (§3.2) |
| `S8-RD` | Replace step 6 with R-D pool policy (§3.3) |

Selection of condition must be **explicit** (env / runner flag / plant config) — never inferred from plant name alone without a logged binding. Default if unset → BASELINE (fail-safe).

---

## 3. Pool-filter policies (from Stage-6/7 families)

All policies consume: candidate `body2`, current `behaviors: dict[key, output_str]` (and, where needed, reverse map to bodies or cached signatures), growth `identity`, frozen context bank from Stage-6/7 continuity, and a per-run repair budget state.

Return label ∈ {`duplicate`, `distinct`, `ambiguous`}:

| Label | Live `_keep` action |
|-------|---------------------|
| `duplicate` | `return` (reject; fate **D** if pool-entered) |
| `distinct` | proceed to keep (step 7) |
| `ambiguous` | **retain** (provisional novelty) — do **not** auto-discard |

Compare candidate against **each** existing behaviors entry (or its cached signature). Reject only if policy says `duplicate` vs ≥1 survivor; if all `distinct`/`ambiguous`, keep. Record per-comparison evidence in instrumentation.

### 3.1 R-A — Multi-context behavioral signature

1. Build signature = ordered tuple of `apply_micro(ctx, body)` across **core** prompt contexts (Stage-6 bank; Stage-7 continuity hash cite).  
2. Cache signatures for behaviors map entries (record cache hits).  
3. If candidate signature equals an existing signature → `duplicate`.  
4. If differs from all → `distinct`.  
5. If budget exhausted mid-signature → `ambiguous` (retain).

Source of truth: Stage-7 `classify_r_a` / Stage-6 `classify_r_a`.

### 3.2 R-C — Adaptive context expansion

1. Cheap stage: compare `apply_micro(identity, ·)` outputs; if unequal vs entry → `distinct` for that entry.  
2. If equal → evaluate frozen probe set `P0`; any differ → `distinct`.  
3. If all P0 equal → expand along frozen reserve list until differ (`distinct`), exhausted equal (`duplicate`), or expansion cap (`ambiguous`).  
4. Never hard-`duplicate` from identity collision alone without P0 agreement.

Source of truth: Stage-7 `classify_r_c`.

### 3.3 R-D — Two-stage identity → semantic

1. Stage-1: identity outputs equal? If no → `distinct`.  
2. Stage-2 (collisions): R-A-style / `P_semantic` bank equality per Stage-6 freeze (TRANSFORMED ∪ BOUNDARY ∪ COMPOSITION ∪ ORDERING).  
3. All equal → `duplicate`; any differ → `distinct`; budget insufficient → `ambiguous` (retain).

Source of truth: Stage-7 `classify_r_d`.

### 3.4 R-B

**Not integrated.** COST_IMPRACTICAL.

---

## 4. Implementation identity (binding)

Before any Sacred plant run under a repair condition:

1. Freeze fixture pair set (may reuse Stage-7 Phase-A/B envelopes under `INTEGRATION_FIXTURE_REPLAY` — **not** as plant discoveries).  
2. Run Stage-7 Phase-B isolated classifier and the **live-wired** step-6 adapter on identical inputs.  
3. Require mismatch_rate == 0 on label, ambiguity_state, and honest cost accounting (ledger fields).  
4. Any mismatch → **STOP** — do not run Sacred under that condition until wiring fixed **without** retuning family semantics.

---

## 5. Adapter shape (design sketch — not implemented here)

```text
# PSEUDOCODE ONLY — DO NOT APPLY IN THIS COMMIT
def step6_equivalence(body2, got, behaviors, *, family, identity, bank, budget_state, recorder):
    if family == "BASELINE":
        if got in behaviors.values():
            recorder.equiv(label="duplicate", fate="D")
            return "reject"
        return "keep"
    for key, prev_got in behaviors.items():
        # resolve prev body or cached signature as required by family
        decision = FAMILY_CLASSIFY[family](body2, prev_body, identity=identity, ...)
        recorder.equiv_compare(key, decision)
        if decision.label == "duplicate":
            recorder.equiv(label="duplicate", fate="D")
            return "reject"
    # distinct or only ambiguous compares → keep (ambiguous retains)
    recorder.equiv(label="retain", fate="survived_equiv")
    return "keep"
```

Preferred packaging under future EXECUTION: thin adapter importing Stage-7 classifiers; avoid duplicating family algorithms. Discovery entrypoints must bind family **explicitly per condition**.

---

## 6. Semantic-preservation invariants

| Invariant | Test |
|-----------|------|
| Steps 1–5 identical | Diff `_keep` excluding step-6 call |
| Invent path untouched | No edits to inventor / propose_atoms |
| Selection scorer untouched | Same function IDs / weights |
| Verify / firewall untouched | Same predicates; floor=5 |
| Provenance schema untouched | Same tuple fields on InventedAtom |
| BASELINE bit-identical to `4005e66` step 6 | Byte compare on baseline branch |

---

## 7. Instrumentation hooks (required at integration time)

Emit events:

- `equiv_decision` {family, candidate_key, compared_keys, label, apply_micro_calls, ambiguity_state}  
- `pool_fate` mapping to A–I when determinable  
- `repair_ledger` incremental cost  

Do not infer **D** without an `equiv_decision` of `duplicate`.

---

## 8. Explicit non-goals

- Editing `grow.py` in this commit  
- Wiring R-B  
- Replacing steps 1–5  
- Calling `behavioral_equivalent` as a silent substitute for R-A/R-C/R-D contracts  
- Sacred execution  
- Winner merge into default production path without condition flag  

---

## 9. Final gate

```
STAGE-8 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

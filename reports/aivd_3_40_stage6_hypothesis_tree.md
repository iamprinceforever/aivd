# AIVD 3.40 Stage-6 — Hypothesis Tree (H6a…H6d + H6-REJECT)

**Document type:** Stage-6 hypothesis tree (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:25 IST  
**Parent charter:** `reports/aivd_3_40_stage6_charter.md`  
**Stage-5 prior:** `reports/aivd_3_40_stage5_results.md` (tip `c003e60` / design `2496857`)  
**Authority:** Stage-5 established H5b+H5d (FALSE_DUPLICATE / context-dependent); this document decomposes whether a **generic** equivalence repair can jointly retain duplicates and novelty  
**R1b caveat:** `7a3457e` — do not auto-rerun R1b  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

**Scientific goal:** Determine whether competing **generic** behavioral-equivalence repair families can distinguish true duplicates from behaviorally distinct candidates without treating every candidate as novel — measuring false-duplicate rate, missed-duplicate rate, distinct-preservation, duplicate-collapse, ambiguity, and Stage-6 experimental cost. Unresolved S remains valid. Do **not** make S pass. Do **not** start with S-specific patches.

---

## 0. Inherited macroscopic status (immutable)

| Macro | Stage-6 stance |
|-------|----------------|
| **H2c** (Stage-4) | SUPPORTED — constructed then `FILTER_BEHAVIORAL_DUP` | retained as location prior |
| **H5b** (Stage-5) | **SUPPORTED** — over-collapse / FALSE_DUPLICATE | **do not weaken** |
| **H5d** (Stage-5) | **SUPPORTED** — context-dependent equivalence | **do not weaken** |
| **H5a / H5c** | AGAINST for critical pair | retained |
| **H1 / H3** | Not primary Stage-6 | not reopened unless evidence forces |

**Epistemic fence:** “Filter over-collapses” ≠ “any multi-probe fix is valid.” “Critical pair should not hard-collapse” ≠ “encode those body keys as exceptions.” “Offline repair success” ≠ “Sacred authorized.”

---

## Causal / logical order among H6 leaves

```
H6a  generic mechanism jointly achieves DUP retention + novelty retention
  ├─ H6b  identity collision necessary-but-insufficient → need disambiguation/expansion
  ├─ H6c  ambiguity-aware policies dominate hard binary collapse (same budget)
  └─ H6d  cost–quality: more Stage-6 eval budget improves distinct-preservation to a plateau
H6-REJECT  gains require target-specific / textual-only / critical-pair-special rules → FAILED
INCONCLUSIVE when evidence cannot separate the above under frozen matrix
```

Notes:

- **H6a** is the primary success claim for *generic* repair.  
- **H6b** motivates R-C / R-D style families given Stage-5 identity-collide + bank-diverge.  
- **H6c** tests whether `ambiguous` / defer / expand beats forced binary labels.  
- **H6d** is a cost tradeoff leaf — not a license to burn Sacred BH48.  
- **H6-REJECT** overrides apparent metric wins if mechanism is a disguised S patch.  
- Future EXECUTION emits exactly one primary gate among SUCCESS / PARTIAL / FAILED / INCONCLUSIVE (charter §2), with H6* stances as supporting evidence.

---

## H6a — Generic mechanism jointly retains duplicates and novelty

**Claim:** At least one preregistered repair family (R-A…R-D or independently motivated rename), evaluated offline on the frozen benchmark **without** target-specific rules, simultaneously:

1. collapses true-dup pairs (duplicate-collapse rate ≥ prereg threshold), and  
2. preserves known-nondup / context-dependent distinct pairs (distinct-preservation ≥ prereg threshold; false-duplicate rate ≤ prereg ceiling), and  
3. does not degenerate to all-novel or all-collapse.

### Stage-5 prior weight

| Evidence | Effect |
|----------|--------|
| Controls PASS (true-dup recognized; nondup distinguishable on bank) | Shows audit ground truth is usable — supports evaluability of H6a |
| Critical pair FALSE_DUPLICATE | Shows baseline fails novelty retention for that class — H6a must fix the **class**, not whitelist body keys |
| n_missed_duplicate=0 in Stage-5 sample | Mild prior that identity-only is aggressive on collapse; repair must not over-correct into missed dups |

### Reject H6a if

- No family meets **both** retention criteria under frozen thresholds, **or**  
- Apparent success depends on H6-REJECT patterns, **or**  
- Degenerate all-distinct / all-duplicate solutions are the only ones that “pass” a single-sided metric.

### Accept H6a as primary if

- ≥1 family meets charter success criteria 1–7 on the frozen benchmark, **and**  
- Ablation attributes gains to the equivalence mechanism, **and**  
- H6-REJECT not supported.

---

## H6b — Identity collision is necessary but insufficient

**Claim:** Singleton `apply_micro(identity, ·)` collision (live `_keep` substrate) remains a useful **cheap triage** signal, but is **insufficient** as a hard duplicate decision for FALSE_DUPLICATE-class pairs that diverge on the frozen bank. Successful families use identity as Stage-1 / trigger, then disambiguate (R-C expansion or R-D semantic stage) rather than replacing all filtering with unbounded probes.

### Stage-5 prior weight

| Evidence | Effect |
|----------|--------|
| `BEHAVIORAL_LIVE=true` and `BEHAVIORAL_AUDIT=false` on critical pair | Direct support for necessary-but-insufficient |
| Agreement on some BASELINE/REORDERED cells; divergence on TRANSFORMED/BOUNDARY/COMPOSITION | Supports staged / adaptive use of bank |

### Reject H6b if

- Fixed multi-context signature with **no** identity triage (pure R-A) dominates staged families on both quality **and** cost, making “necessary” identity triage false, **or**  
- Identity triage is harmful (e.g., systematically misses true dups that disagree on identity but agree on bank — unexpected given Stage-5 sample).

### Accept H6b if

- Staged / adaptive families (R-C/R-D) match or beat fixed-bank R-A on joint metrics **at lower mean evaluator calls**, **or**  
- Ablation removing Stage-2 disambiguation reintroduces FALSE_DUPLICATE-class collapses.

---

## H6c — Ambiguity-aware policies dominate hard binary collapse

**Claim:** When cheap identity says duplicate but bank evidence is incomplete or mixed, policies that emit `ambiguous` / defer / provisional novelty / budgeted expansion **dominate** forced hard `duplicate` under the same Stage-6 experimental budget — improving distinct-preservation without destroying duplicate-collapse beyond thresholds.

### Reject H6c if

- Hard binary multi-context equality (no ambiguity channel) matches ambiguity-aware policies on all primary metrics, **or**  
- Ambiguity channel is abused to mark everything `ambiguous` (degeneracy; cost/quality failure).

### Accept H6c if

- Ambiguity-aware family strictly improves false-duplicate rate or distinct-preservation vs hard-binary sibling under equal call budget, without missed-dup breach, **and**  
- Ambiguity rate stays within prereg ceiling.

---

## H6d — Cost–quality tradeoff under Stage-6 experimental budget

**Claim:** Increasing allowed Stage-6 evaluator calls (within the explicit experimental envelope — **not** Sacred BH48) improves distinct-preservation / reduces false-duplicates up to a **preregistered plateau**; beyond plateau, extra calls do not justify cost. Duplicate-collapse remains above threshold across the budget grid.

### Reject H6d if

- No monotone or plateau pattern appears on the prereg budget grid, **or**  
- Quality gains require exceeding the Stage-6 envelope or touching Sacred budget.

### Accept H6d if

- Budget grid shows improvement then plateau on prereg metrics, with honest accounting of calls.

---

## H6-REJECT — Target-specific / non-generic “repair”

**Claim:** Apparent metric improvements require one or more of:

- S / odd-stride / CAT-self / critical-pair **body-key** recognizers or allowlists  
- Contexts added or weighted after inspecting critical-pair Stage-5 outputs  
- Textual/structural equality substituted for behavioral equivalence (fails adversarial controls)  
- Changes outside classification (scoring, selection, invent, prompts)

### Accept H6-REJECT (→ design FAILED) if

- Any of the above is required for “success,” **or**  
- Repair improves **only** `HELD_OUT_CRITICAL` while harming TRUE_DUP / KNOWN_NONDUP batteries, **or**  
- Adversarial controls fail (text-diff/beh-same not collapsed; text-sim/beh-diff collapsed).

### Must not

- Relabel an S-special case as “generic.”  
- Argue that because the critical pair is the motivating example, hard-coding it is acceptable.

---

## Interpretation matrix (future EXECUTION)

| Pattern | Prefer |
|---------|--------|
| ≥1 generic family meets joint retention + cost honesty; adversarial pass; critical class no longer hard-collapsed without body-key exception | **SUCCESS** (H6a ± H6b/H6c/H6d) |
| Clear gains on false-dup class but missed-dup or cost breach; or only some families work | **PARTIAL** |
| H6-REJECT supported / degeneracy / protocol violation | **FAILED** |
| Cannot separate leaves honestly under frozen matrix | **INCONCLUSIVE** |

Do **not** use Sacred success or “S should pass” as interpretation input.

---

## Code / artifact anchors (observational; read-only)

- Live: `aivd/science/grow.py::propose_growth._keep` (`got in behaviors.values()`)  
- Label: `FILTER_BEHAVIORAL_DUP` in `aivd/experiments/aivd340/stage4_audit.py`  
- Helper ≠ live: `behavioral_equivalent`  
- Stage-5 critical pair envelopes: `reports/aivd_3_40_stage5_results.json`  
- Stage-5 context bank hash: `2a2767cc1ba0861b89371cab977a519d1eeddeae90b0a72869afe0ce0bd54b1b` (cite; Stage-6 freezes its own bank document — may extend families ORDERING/STATE_CONTEXT only in **design freeze before exec**, not after repair results)

---

## Explicit non-goals

- Making S pass  
- Implementing repairs in this commit  
- Weakening H5b/H5d  
- Authorizing Sacred  

---

## Final gate (design)

```
STAGE-6 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

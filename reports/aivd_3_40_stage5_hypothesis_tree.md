# AIVD 3.40 Stage-5 — Hypothesis Tree (H5a…H5d)

**Document type:** Stage-5 hypothesis tree (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 19:10 IST  
**Parent charter:** `reports/aivd_3_40_stage5_charter.md`  
**Stage-4 prior:** `reports/aivd_3_40_stage4_results.md` (tip `4005e66` / design `27e9e88`)  
**Authority:** Stage-4 tree decomposes H2 → H2c; this document **decomposes the semantic status of FILTER_BEHAVIORAL_DUP**  
**R1b caveat:** `7a3457e` — do not auto-rerun R1b; observational cite only  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

**Scientific goal:** Determine whether `FILTER_BEHAVIORAL_DUP` correctly establishes behavioral equivalence for pairs it collapses (especially Stage-4 odd CAT-self vs `MAPT(CAT(AT:-1|AT:-1))`), or whether the equivalence relation is too coarse — measuring both false duplicates and missed duplicates. Unresolved S remains valid. Do **not** make S pass. Do **not** assume H5b merely because the desired candidate disappears.

---

## 0. Inherited macroscopic status (Stage-4; immutable)

| Macro | Stage-5 stance |
|-------|----------------|
| **H1** | Upstream AUTONOMOUS invent barrier — not reopened as primary |
| **H2** | Pool-formation bottleneck under controlled availability — retained |
| **H2c** | **SUPPORTED** as earliest stop: constructed then `FILTER_BEHAVIORAL_DUP` | Stage-5 asks whether that filter’s *equivalence basis* is semantically valid |
| **H2a/b/d/e/f / POST_POOL** | AGAINST as earliest (Stage-4) — not re-litigated unless Stage-5 evidence forces scope revision |
| **H3** | Still not primary (candidate never in full-context pool) |

**Epistemic fence:** “Removed by FILTER_BEHAVIORAL_DUP” ≠ “behaviorally equivalent.” “Absent from pool” ≠ “should remain absent.” “Survives solo-odd context” ≠ “filter is wrong.”

---

## Causal / logical order among H5 leaves

```
H5a  filter-as-relation is valid semantic equivalence (control battery)
  ├─ H5c  Stage-4 critical pair genuinely equivalent (removing odd correct)
  └─ H5b  filter over-collapses (classified dup but distinct under audit)
H5d  apparent distinction depends on unmeasured context/sequence/state
E    INCONCLUSIVE when evidence cannot separate the above
```

Notes:

- **H5a** is about the **filter relation in general** (true-dup / known-nondup controls).  
- **H5c** is about the **Stage-4 critical pair** only.  
- **H5b** is supported when ≥1 classified-dup pair (with emphasis on the critical pair + control false-dup detections) diverges under the **preregistered** context bank.  
- **H5d** absorbs cases where divergence is unstable, order/state-confounded, or only visible outside the frozen bank.  
- H5a and H5b are mutually exclusive as *primary* conclusions about the filter relation; H5c may co-travel with H5a, or fail while H5a still holds on other pairs (record explicitly).  
- Exactly one of **A–E** in the results conclusion line (charter §2).

---

## H5a — FILTER_BEHAVIORAL_DUP is a valid semantic-equivalence filter

**Claim:** Pairs that `_keep` collapses via `got in behaviors.values()` (single growth `identity`) remain behaviorally equivalent under the **full preregistered multi-context audit** (charter context families). True-dup controls collapse; known-nondup controls are preserved. The filter’s equality substrate is therefore an adequate semantic-equivalence relation for growth-pool formation under frozen R1.

### Stage-4 prior weight

| Evidence | Effect |
|----------|--------|
| Identity-string collision between odd CAT-self and `MAPT(CAT(AT:-1|AT:-1))` | Consistent with H5a **or** H5b/H5c — does not decide |
| Solo odd-only 7/7 pool membership | Shows collision requires competing behavior string — not by itself H5a |

### Reject H5a if

- Any preregistered true-dup control fails to collapse under the live rule, **or**
- Any preregistered known-nondup control is collapsed by the live rule on identity **and** the audit confirms they are distinct, **or**
- The Stage-4 critical pair (or other classified-dup pairs in the audit sample) **diverge** on ≥1 frozen context family → prefer H5b (or H5d if isolation fails).

### Accept H5a as primary if

- Control battery passes (true-dup collapse; known-nondup preserve), **and**
- Classified-dup pairs in the audit sample remain equivalent on the full frozen context bank, **and**
- No isolable false-duplicate under preregistered contexts.

### Code / artifact anchors (observational)

- `aivd/science/grow.py::propose_growth` `_keep` (`got in behaviors.values()`)
- Stage-4 runs: `reports/aivd_3_40_stage4/runs/S4-OBS-B-S_*`
- Equivalence_spec context bank + control pairs

---

## H5b — FILTER_BEHAVIORAL_DUP is over-collapsing behaviorally distinct candidates

**Claim:** At least one pair classified as `FILTER_BEHAVIORAL_DUP` (identity-string collide) **diverges** under the preregistered generic context bank — i.e., the live relation is **stricter / coarser than true behavioral equivalence** (collapses distinct behaviors). The Stage-4 critical pair is the primary stress case but **not** the sole admissible evidence; control false-dup detections also count.

### Stage-4 prior weight

| Evidence | Effect |
|----------|--------|
| Desired odd CAT-self removed from promote-set pool | **Insufficient alone** — must not auto-accept H5b |
| Structural keys differ (`MAPT(CAT(SLICE:1,2…))` vs `MAPT(CAT(AT:-1|AT:-1))`) | Mild prior that structures differ; **not** behavioral proof |
| Named helper `behavioral_equivalent` uses multi-probe probes ≠ live `_keep` identity-only rule | Motivates multi-context audit; does **not** pre-decide H5b |

### Reject H5b if

- All classified-dup pairs in the audit sample remain equivalent on the full frozen bank, **or**
- Apparent divergences are only outside the frozen bank / non-reproducible → H5d or INCONCLUSIVE, **or**
- Divergence is an artifact of target-injected contexts (protocol violation → STOP).

### Accept H5b as primary if

- ≥1 classified-dup pair diverges on ≥1 **preregistered** context family with recorded outputs, **and**
- Divergence is reproducible and not explained solely by unmeasured state/order (else H5d), **and**
- Control battery remains interpretable (known-nondup still distinct; true-dup still equivalent on bank).

### Must not

- Assume H5b because S / odd candidate disappears.  
- Encode S into evaluator to force divergence.  
- Repair the filter mid-flight to “confirm” over-collapse.

### Code / artifact anchors

- `_keep` identity-only equality vs equivalence_spec multi-context bank  
- Stage-4 `duplicate_of: ["MAPT(CAT(AT:-1|AT:-1))"]` records  
- Positive/negative control pairs in matrix

---

## H5c — The two candidates are genuinely behaviorally equivalent (removing odd is correct)

**Claim:** Under the preregistered audit relation, `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` and `MAPT(CAT(AT:-1|AT:-1))` are **behaviorally equivalent**. Therefore Stage-4’s removal of the odd CAT-self under full promote-set context is **semantically justified** for that pair (even if textual/structural forms differ).

### Stage-4 prior weight

| Evidence | Effect |
|----------|--------|
| Identity collide on growth `identity` | Necessary for live dup classification; not sufficient for H5c |
| Solo context admits odd when competitor absent | Consistent with “same behavior string competes,” not with global equivalence |

### Reject H5c if

- Critical pair diverges on any frozen context family → prefer H5b (or H5d).

### Accept H5c if

- Critical pair equivalent on full frozen bank (all families), **and**
- Textual/structural inequality is explicitly recorded (so H5c is behavioral, not textual).

### Relationship to H5a

- H5c ∧ control battery pass → supports **A (H5a)** with **C** as pair-level annotation, or primary **C** if results schema pins one letter — charter requires **exactly one** of A–E; if both H5a and H5c hold, prefer **A** when the filter-general claim is established, and record H5c as **co-supported pair finding** in the results body. If only the critical pair is validated equivalent but controls fail, do **not** claim H5a; prefer **E** or scoped **C** only if prereg allows pair-primary — **prereg default:** pair-only equivalence without control pass → **E INCONCLUSIVE** (cannot promote filter-general H5a) with critical-pair note.  
- **Simplification for execution results line:** use **C** when the decisive, preregistered conclusion is “removing odd is correct for the Stage-4 pair,” and control battery does not contradict; use **A** when the decisive conclusion is filter-general validity; never emit two letters.

---

## H5d — Apparent distinction depends on unmeasured context / sequence / state

**Claim:** Observed agreement or disagreement between classified-dup pairs is **contingent** on contexts or state not isolated by the frozen bank — e.g., `behaviors` map insertion order / which competitor was kept first, identity prompt choice, sequence effects, or hidden fields — such that Stage-5 cannot yet attribute over-collapse (H5b) or true equivalence (H5c/H5a).

### Stage-4 prior weight

| Evidence | Effect |
|----------|--------|
| char_project CAT-self kept before odd path (ordering) | State/order may matter for *which* key survives, not necessarily for semantic equality of outputs |
| Filter uses single `identity` | Narrow probe → risk of H5d if bank underpowered |

### Reject H5d if

- Divergences (or universal agreements) are stable across the frozen bank and across STATE_VARIATION cells that permute keep-order / identity within preregistered bounds.

### Accept H5d if

- Results flip under STATE_VARIATION / identity choice within frozen bounds without a stable semantic pattern, **or**
- Required distinguishing contexts were not in the frozen bank (underpower) — honest INCONCLUSIVE may be preferred when bank gap is the issue; use H5d when **measured** state/order dependence is the positive finding.

---

## Reject / accept summary table

| Leaf | Accept when | Reject when |
|------|-------------|-------------|
| H5a | Controls pass; classified dups stay equiv on bank | False dup on bank; control failure |
| H5b | Classified dup diverges on frozen bank; isolable | Only pool absence; only non-prereg contexts |
| H5c | Critical pair equiv on full bank | Critical pair diverges |
| H5d | Order/state/context underpower or instability | Stable bank-wide pattern favors H5a/b/c |
| E | Cannot separate leaves honestly | — |

---

## Downstream (out of Stage-5 primary scope)

| If Stage-5 finds… | Then… |
|-------------------|-------|
| H5b SUPPORTED | Future work may propose a **separately preregistered** filter-revision experiment — **not authorized** here; do not repair in Stage-5 |
| H5a / H5c SUPPORTED | Stage-4 removal of odd remains semantically justified; S still unresolved; do not claim S pass |
| H5d / E | Need richer frozen bank or state instrumentation — new design commit, not silent patch |

**Forbidden downstream in this stage:** R1b rerun, Sacred “fix,” promote-set surgery, autonomous invent credit for offline pairs.

---

## Final gate (design)

```
STAGE-5 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

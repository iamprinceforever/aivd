# AIVD 3.40 Stage-5 DESIGN CHARTER — FILTER_BEHAVIORAL_DUP Equivalence Audit

**Document type:** Stage-5 DESIGN CHARTER (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 19:10 IST  
**Start tip:** `4005e66` (`research/aivd-3.40-budget-representation-frontier`)  
**Stage-4 COMPLETE tip:** `4005e66` (observational H2a–H2f growth audit; H2c SUPPORTED)  
**Stage-4 design freeze:** `27e9e88`  
**Authority priors (cite; do not weaken):** Stage-4 results `4005e66` / design `27e9e88`; Phase-2 `f4d7a2b` / exec `d1e31b5`; Phase-1 `a2ab0cc`; Stage-3 `146915b`; Stage-2 `dcae889`; R1b caveat `7a3457e`; AIVD 3.38 / 3.39 Sacred baselines  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** **STAGE-5 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION**

Companion deliverables (this commit, `reports/` only):

1. `aivd_3_40_stage5_charter.md` — **this file**
2. `aivd_3_40_stage5_hypothesis_tree.md`
3. `aivd_3_40_stage5_matrix.json`
4. `aivd_3_40_stage5_preregistration.md`
5. `aivd_3_40_stage5_equivalence_spec.md`

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Stage-5 scope (this commit) | **DESIGN documents only** under `reports/` |
| No execution | No Sacred, no mock Sacred, no runners, no filter changes, no discovery / growth edits |
| No historical mutation | Do **not** modify Stage-4 / Phase-2 / Phase-1 / Stage-2 / Stage-3 reports or 3.38/3.39 baselines |
| Scientific objective | Characterize whether `FILTER_BEHAVIORAL_DUP` establishes a **valid behavioral-equivalence relation** — **NOT** make S pass |
| Primary question (exact) | Does `FILTER_BEHAVIORAL_DUP` correctly establish behavioral equivalence between the odd CAT-self and the candidate it removes, or is the equivalence relation too coarse? |
| First experiment | **Preregistered offline equivalence audit** of every pair classified as behavioral duplicate — do **not** change the filter |
| Immutable filter | Audit `FILTER_BEHAVIORAL_DUP`; **do not repair**, redesign, or R1b-rerun around it |
| Counterfactual status | All semantic-equivalence tests after Stage-4 are **OFFLINE EVALUATION** unless explicitly preregistered otherwise — no autonomous discovery / invent / vulnerability-discovery credit |
| Mode namespaces | Keep **AUTONOMOUS** vs **CONTROLLED_INPUT** vs **OFFLINE_EVAL** separate; never merge |
| Epistemic boundary | Stage-4 established **H2c**: odd CAT-self constructed then dropped by `FILTER_BEHAVIORAL_DUP`. It did **not** establish that the dropped pair is *semantically* equivalent. Do **not** assume H5b merely because the desired candidate disappears. Do **not** infer validity from candidate survival alone. |
| STOP | Implementation / Sacred / audit execution requires a **separate EXECUTION charter** |

If a “design” proposal would alter filter / growth / promote-set semantics to make S pass → **STOP** (revise; do not ship).

---

## 1. Why Stage-5 (post Stage-4)

### 1.1 Stage-4 COMPLETE priors (immutable cite)

| Prior | Status |
|-------|--------|
| CONTROL B full promote-set | Odd CAT-self in pool = **0/7** |
| CONTROL B solo odd-only | Odd CAT-self in pool = **7/7** |
| Earliest stop | `STRUCTURAL_FILTERS` → **H2c SUPPORTED** |
| Filter evidence | `FILTER_BEHAVIORAL_DUP`: behavioral duplicate of `['MAPT(CAT(AT:-1|AT:-1))']` (body=`MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))`) |
| Offline IR | Single-step `cat_self_body` path exists (H2b/H2e rejected as sole explanations) |
| H2a / H2d / H2f / POST_POOL | AGAINST as earliest |
| Sacred | not executed; no S-pass claim |
| Namespace | CONTROLLED_INPUT (`autonomous_discovery_credit=false`) |

**Stage-4 epistemic boundary (binding):**

> Odd CAT-self is **constructed** then **removed** by `FILTER_BEHAVIORAL_DUP` under full R1 promote-set context because its `apply_micro(identity, ·)` string collides with an earlier-kept `MAPT(CAT(AT:-1|AT:-1))` behavior. Stage-4 did **not** establish whether that collision is *true behavioral equivalence* or an **over-coarse** equality test. Outcome H2c is a **location**, not a semantic-equivalence verdict.

### 1.2 Primary scientific question (binding)

> Does `FILTER_BEHAVIORAL_DUP` correctly establish behavioral equivalence between the odd CAT-self and the candidate it removes, or is the equivalence relation too coarse?

Objective: **characterize the filter’s equivalence relation** — measure both **false duplicates** (classified dup but behaviorally distinct) and **missed duplicates** (considered distinct but behaviorally equivalent). Do **not** redesign the filter. Do **not** make S pass.

### 1.3 What Stage-5 is NOT

- Not a cure for S / not “make S pass”
- Not authorization to change `FILTER_BEHAVIORAL_DUP`, `_keep`, growth ops, scores, selection, verification, firewall
- Not authorization to modify promote-set composition to obtain a desired pool result
- Not automatic R1b re-execution
- Not Sacred / autonomous rediscovery / independent generation credit
- Not Stage-5 execution (code / Sacred / live audit) in this commit

---

## 2. Hypothesis decomposition (H5a…H5d)

Full tree: `reports/aivd_3_40_stage5_hypothesis_tree.md`. Summary:

| ID | Claim |
|----|-------|
| **H5a** | `FILTER_BEHAVIORAL_DUP` is a **valid semantic-equivalence** filter (pairs it collapses are behaviorally equivalent under the preregistered multi-context audit) |
| **H5b** | `FILTER_BEHAVIORAL_DUP` is **over-collapsing** behaviorally distinct candidates (at least one classified-dup pair diverges under preregistered contexts) |
| **H5c** | The Stage-4 odd CAT-self vs `MAPT(CAT(AT:-1|AT:-1))` pair is **genuinely behaviorally equivalent** (removing odd is correct under the audit relation) |
| **H5d** | Apparent distinction depends on **unmeasured context / sequence / state** (audit contexts insufficient or state-dependence not isolated) |

**Binding caution:** Do **not** assume H5b simply because the desired odd candidate disappears from the promote-set pool. Disappearance is Stage-4 H2c; Stage-5 asks whether the *basis* of that disappearance is semantically justified.

**Interpretation conclusions (exactly one):**

| Code | Label |
|------|-------|
| **A** | H5a SUPPORTED |
| **B** | H5b SUPPORTED |
| **C** | H5c SUPPORTED |
| **D** | H5d SUPPORTED |
| **E** | INCONCLUSIVE |

Do **not** infer from candidate survival alone. H5a and H5c are related but not interchangeable: H5a is about the **filter relation in general** (controls); H5c is about the **Stage-4 critical pair**.

---

## 3. Equivalence audit (first experiment — mandatory)

### 3.1 Principle

**First experiment MUST be a preregistered offline equivalence audit.** Do **not** change:

- `FILTER_BEHAVIORAL_DUP` / `propose_growth` / `_keep`
- growth algorithm, operators, ordering, scores, filtering, compatibility
- selection, verification, firewall
- `propose_atoms` 8-set, invent_cap, REDISCOVERY_FLOOR, BH48
- Stage-4 promote-set fixtures / historical pool outcomes

Purpose: for every pair the filter classifies as a behavioral duplicate, record the **exact basis** of equivalence and test whether that basis survives preregistered multi-context evaluation.

### 3.2 Exact filter mechanics (read-only anchors; tip `4005e66`)

| Anchor | Location | Role |
|--------|----------|------|
| Live collapse rule | `aivd/science/grow.py::propose_growth` nested `_keep` | After `canonicalize_micro` / `known_keys` / `validate_micro` / identity-noop: `got = apply_micro(identity, body2)`; **reject if `got in behaviors.values()`** |
| Stage-4 category | `FILTER_BEHAVIORAL_DUP` | Instrumentation label for that reject (`stage4_audit` / instrumentation spec §5.5) |
| Behavior map | `behaviors: dict[str, str]` in `propose_growth` | Seeded from promoted atoms via `apply_micro(identity, a.body)`; updated when a candidate is kept |
| Named helper (NOT the live `_keep` rule) | `behavioral_equivalent(a, b, probes=...)` | Multi-probe equality helper; **must not be confused** with the single-`identity` `_keep` test |
| Distance helper | `semantic_distance` | Class mismatch + probe disagreement; not the pool filter |
| Textual identity | `textual_identity` / `body.key()` | Structural/textual — **not interchangeable** with behavioral equality |

**Critical distinction (binding):** Textual equality ≠ structural equality ≠ behavioral equality. The live filter uses **single-prompt output-string equality** on the growth `identity` prompt — a **behavioral** check under a **narrow probe**, not textual/structural identity of body keys.

Full field / audit schema: `reports/aivd_3_40_stage5_equivalence_spec.md`.

### 3.3 Audit requirements (minimum)

For every pair classified as behavioral duplicate, inspect and record:

1. **MAPT output** on each preregistered context  
2. **CAT output** / CAT-self structure  
3. **AT structure** vs **SLICE/index** structure  
4. **Slice/index behavior** under boundary lengths  
5. **Context / sequence / order / state** dependence  
6. **Output distribution** across the frozen context bank  
7. **Hidden representation fields** used by the filter (at tip: primarily `identity` string + `behaviors` map values; body keys are not the equality substrate)

Distinguish and report separately: **textual** vs **structural** vs **behavioral** equality.

### 3.4 Critical comparison (odd CAT-self vs Stage-4 duplicate partner)

Compare:

- **Candidate A (removed):** `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))`  
- **Candidate B (kept earlier):** `MAPT(CAT(AT:-1|AT:-1))`

under **multiple evaluator contexts** — **not only** the `identity` context that caused duplicate classification.

Context families must be **generic and target-independent** (useful for S ⇒ also applicable to U and controls). Exact frozen context bank: matrix + equivalence_spec + prereg. **No target injection:** do not encode secret S into evaluator prompts.

### 3.5 Positive / negative controls

| Control class | Role |
|---------------|------|
| True known-duplicate pairs | Filter **should** collapse |
| Known non-duplicate pairs | Filter **should** preserve |
| U known-good path | Continuity / positive growth machinery |
| Odd CAT-self Stage-4 pair | Critical comparison cell |

Do **not** judge the filter from S alone.

### 3.6 Dual error measurement

| Error type | Definition |
|------------|------------|
| **False duplicate** | Classified `FILTER_BEHAVIORAL_DUP` but diverges under ≥1 preregistered context family (behaviorally distinct) |
| **Missed duplicate** | Not classified dup (distinct `behaviors` values on identity) but equivalent under the full preregistered audit relation |

Goal = characterize the equivalence relation, not merely prove the odd candidate should survive.

---

## 4. Stage-4 pool contrast (reproduce / explain; do not mutate)

| Context | Odd CAT-self in pool | Binding use |
|---------|----------------------|-------------|
| Full R1 promote-set | **0/7** | Must be **reproduced or explained** via frozen Stage-4 artifacts (`reports/aivd_3_40_stage4_results.*`, `reports/aivd_3_40_stage4/runs/`) |
| Solo odd-only | **7/7** | Shows grammar/`cat_self_body` OK when no competing behavior string |

**Forbidden:** Modify promote set for a desired result; manually remove/add candidates; re-run Stage-4 with altered fixtures to “fix” survival.

---

## 5. Counterfactual / provenance status

| Label | Binding |
|-------|---------|
| `OFFLINE_EVAL` | Default for all Stage-5 semantic-equivalence tests |
| `autonomous_discovery_credit` | **false** always for Stage-5 cells |
| `claim_label` | `OFFLINE_EQUIV_AUDIT` (or narrower cell IDs) — never Silent Sacred / invent credit |
| Provenance firewall | Keep separate from AUTONOMOUS Mode A invent and from Stage-4 CONTROLLED_INPUT growth-audit credits |

No autonomous discovery / independent generation / vulnerability discovery credit attaches to Stage-5 offline evaluation.

---

## 6. Interpretation matrix (binding)

Classify from **preregistered equivalence evidence**, not from final Sacred success or candidate survival alone.

| Pattern | Prefer | Must not claim |
|---------|--------|----------------|
| Across true-dup controls, filter collapses; across known-non-dup controls, filter preserves; Stage-4 critical pair equivalent on full context bank | **H5a** (+ possibly **H5c**) | “S should pass” |
| ≥1 classified-dup pair (esp. Stage-4 critical pair) diverges on preregistered generic contexts while identity-collides | **H5b** | H5b solely from pool absence |
| Stage-4 critical pair equivalent on full bank (no divergence); removing odd justified under audit relation | **H5c** | Filter globally valid without control battery |
| Divergence appears only under ad-hoc / non-prereg contexts; or order/state of `behaviors` map confounds without isolable semantic gap | **H5d** | Over-claim H5b without frozen contexts |
| Recorder gaps / context-bank underpower / cannot separate H5b vs H5d | **INCONCLUSIVE (E)** | Mechanism acceptance |
| Candidate survives after (forbidden) filter change | **invalid** | Any H5* support |

Exactly one of **A–E** in the Stage-5 results conclusion.

---

## 7. Experimental matrix (design sketch; full JSON companion)

| Factor | Levels |
|--------|--------|
| Pair class | `TRUE_DUP` \| `KNOWN_NONDUP` \| `U_GOOD_PATH` \| `ODD_CAT_SELF_STAGE4_PAIR` \| `OTHER_FILTER_DUP` (if emitted) |
| Audit mode | `OFFLINE_EQUIV` (primary) \| `ARTIFACT_REPLAY` (Stage-4 frozen runs explain 0/7 vs 7/7) |
| Context family | `BASELINE_IDENTITY` \| `TRANSFORMED` \| `REORDERED` \| `BOUNDARY` \| `COMPOSITION` \| `STATE_VARIATION` |
| Target role | `S` \| `U` \| `N/A` (pair-level; no S-special evaluator) |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` (artifact continuity; offline eval deterministic across seeds unless noted) |
| Budget | **BH48 frozen** (no raise; not a budget experiment) |
| Representation | Frozen **R1**; **no** auto R1b |

Minimum required cells and freeze locks: `reports/aivd_3_40_stage5_matrix.json` + prereg companion.

---

## 8. Prohibitions

| Forbidden | Why |
|-----------|-----|
| Implement filter changes / equivalence “fixes” in this commit | Design only; audit ≠ repair |
| Execute Sacred / Stage-5 audit runs | No auto-authorization |
| Modify Stage-4/Phase-2/1 / Stage-2/3 / 3.38/3.39 historical artifacts | Immutability |
| Modify `FILTER_BEHAVIORAL_DUP` / `_keep` / growth / propose_atoms / invent_cap / REDISCOVERY_FLOOR / firewall / verify | Frozen |
| Redesign filter to make odd survive | Confounds localization; “make S pass” |
| Target-injected evaluator contexts that encode S | No target injection |
| Merge OFFLINE_EVAL into AUTONOMOUS metrics | Claim firewall |
| Auto-rerun R1b / R1c / BHexplore / Level-14 | Out of scope / caveat |
| Infer H5b from Stage-4 pool absence alone | Epistemic error |
| Infer H5* from candidate survival alone | Epistemic error |
| Manual promote-set editing for desired pool | Protocol violation |

---

## 9. Exit / final gate

This commit delivers **design** only. No execution authorization is granted.

```
STAGE-5 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

If a future design edit would require filter repair, Mode merge, silent R1b reuse, promote-set mutation, or “make S pass” framing, the gate becomes:

```
STAGE-5 DESIGN BLOCKED: <exact reason>
```

---

## 10. Parent commits (authority map)

| Role | SHA | Note |
|------|-----|------|
| Stage-5 design start tip / Stage-4 COMPLETE | `4005e66` | H2c SUPPORTED; observational growth audit COMPLETE |
| Stage-4 design freeze | `27e9e88` | H2a–H2f design READY |
| Phase-2 complete tip | `f4d7a2b` | Mode A/B H2/H3 localization |
| Phase-2 exec | `d1e31b5` | Mode A/B runs |
| Phase-2 design freeze | `7be4124` | Instrumentation design |
| Phase-1 result tip | `a2ab0cc` | Offline trajectory |
| Stage-3 charter | `146915b` | Localization design |
| Stage-2 tip | `dcae889` | Immutable Sacred aggregates |
| R1b caveat | `7a3457e` | No auto re-run |

---

## 11. What this commit does NOT do

- No Sacred / Stage-5 execution  
- No filter implementation or repair  
- No mutation of `reports/aivd_3_40_stage4_*`, Phase-2/1, Stage-2/3, or 3.38/3.39  
- No claim that H5a–H5d are already decided — Stage-5 exists to distinguish them  
- No claim that Mode B / offline eval = autonomous discovery  
- No R1b / R1c / BHexplore / Level-14 work  


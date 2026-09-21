# AIVD 3.40 Stage-6 DESIGN CHARTER — Generic Behavioral-Equivalence Repair (Design Only)

**Document type:** Stage-6 DESIGN CHARTER (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:25 IST  
**Start tip:** `c003e60` (`research/aivd-3.40-budget-representation-frontier`)  
**Stage-5 COMPLETE tip:** `c003e60` (offline equivalence audit; H5b+H5d SUPPORTED; critical pair = FALSE_DUPLICATE)  
**Stage-5 design freeze:** `2496857`  
**Authority priors (cite; do not weaken):** Stage-5 results `c003e60` / design `2496857`; Stage-4 `4005e66` / design `27e9e88`; Phase-2 `f4d7a2b` / design `7be4124`; Phase-1 `a2ab0cc`; Stage-3 `146915b`; Stage-2 `dcae889`; R1b caveat `7a3457e`; AIVD 3.38 / 3.39 Sacred baselines  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** **STAGE-6 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION**

Companion deliverables (this commit, `reports/` only):

1. `aivd_3_40_stage6_charter.md` — **this file**
2. `aivd_3_40_stage6_hypothesis_tree.md`
3. `aivd_3_40_stage6_matrix.json`
4. `aivd_3_40_stage6_preregistration.md`
5. `aivd_3_40_stage6_equivalence_repair_spec.md`
6. `aivd_3_40_stage6_metrics.md`

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Stage-6 scope (this commit) | **DESIGN documents only** under `reports/` |
| No implementation | No edits to `grow.py`, `_keep`, `FILTER_BEHAVIORAL_DUP`, discovery pipeline, promote-set, firewall, verify |
| No execution | No Sacred, no mock Sacred, no Stage-6 offline benchmark runs, no repair wiring |
| No historical mutation | Do **not** modify Stage-5/4 / Phase-2/1 / Stage-2/3 reports or 3.38/3.39 baselines; Stage-5 FALSE_DUPLICATE finding must remain reproducible from original artifacts |
| Scientific objective | Design **competing generic** behavioral-equivalence repair families and a fair offline evaluation — **NOT** make S pass |
| Primary question (exact) | Can a **GENERIC** behavioral-equivalence mechanism distinguish true duplicates from behaviorally distinct candidates **without** treating every candidate as novel? |
| Anti-S-patch | **DO NOT START WITH S** — no S-specific / odd-stride / CAT-self exceptions / critical-pair special cases / target-aware logic. If repair only works by recognizing the known S case → **REJECT THE DESIGN** |
| Dual retention | **BOTH** duplicate retention (genuine dups collapse) **AND** novelty retention (genuinely distinct survive). Optimizing only for S / critical pair = failure |
| Classification-only | Repair may change **ONLY** classification: `duplicate` \| `distinct` \| `ambiguous`. Must **NOT** change proposal generation, invention, growth operators, candidate generation, scoring, selection, verification, firewall, discovery prompts |
| Sacred budget | **Sacred BH48 frozen.** Stage-6 = filter audit/repair **experiment**. Extra evaluator calls must be explicit Stage-6 experimental budget — do **not** silently consume discovery budget |
| First experiment | Preregistered **offline** repair-family benchmark vs baseline `FILTER_BEHAVIORAL_DUP` — do **not** authorize fresh Sacred |
| STOP | Implementation / Sacred / benchmark execution requires a **separate EXECUTION charter** |

If a “design” proposal would encode the Stage-4/5 critical pair as a special case, inject S into contexts, or alter growth/invent/selection to make S pass → **STOP** (revise; do not ship).

---

## 1. Why Stage-6 (post Stage-5)

### 1.1 Stage-5 COMPLETE priors (immutable cite)

| Prior | Status |
|-------|--------|
| textual equality (critical pair) | **false** |
| structural equality (critical pair) | **false** |
| live identity equality (`BEHAVIORAL_LIVE`) | **true** (`bb dd ff hh jj ll`) |
| full-bank audit equality (`BEHAVIORAL_AUDIT`) | **false** |
| families diverged | `TRANSFORMED`, `BOUNDARY`, `COMPOSITION` |
| H5b | **SUPPORTED** (over-collapse / FALSE_DUPLICATE) |
| H5d | **SUPPORTED** (context-dependent equivalence) |
| H5a / H5c | AGAINST for critical pair |
| controls_pass | **True** (true-dup 3/3; known-nondup 4/4; U-good resolves) |
| n_false_duplicate | 2 (critical + ND-04 signature) |
| n_missed_duplicate | 0 (audited sample) |
| Filter repair | **not** authorized / **not** performed in Stage-5 |
| Sacred | not executed; no S-pass claim |

**Stage-5 epistemic boundary (binding):**

> `FILTER_BEHAVIORAL_DUP` collapses pairs on a **singleton growth `identity` string** (`got in behaviors.values()`). That collision is **not** full-bank behavioral equivalence for the Stage-4 critical pair. Stage-5 **characterized** over-collapse; it did **not** design or authorize a repair. Stage-6 designs **generic** competing repairs and a fair offline test — it does **not** exist to make S pass.

### 1.2 Primary scientific question (binding)

> Can a **GENERIC** behavioral-equivalence mechanism distinguish true duplicates from behaviorally distinct candidates **without** treating every candidate as novel?

Objective: design and (in a future EXECUTION) evaluate competing repair families that:

1. **Suppress true duplicates** (duplicate retention / collapse), and  
2. **Preserve genuinely distinct** candidates (novelty retention), including context-dependent distinctions of the FALSE_DUPLICATE class,  
3. **without** target-specific rules, and  
4. **without** declaring everything novel or collapsing everything.

### 1.3 What Stage-6 is NOT

- Not a cure for S / not “make S pass”
- Not authorization to implement repairs in `grow.py` in this commit
- Not authorization to modify `FILTER_BEHAVIORAL_DUP` live semantics mid-flight without a future EXECUTION charter that still forbids S-special cases
- Not authorization for fresh Sacred / R1b / R1c / BHexplore / Level-14
- Not a Stage-5 re-litigation that weakens H5b/H5d
- Not an experiment that tunes repairs directly against the critical pair’s exact observed outputs

---

## 2. What counts as successful generic equivalence repair?

**Success (ALL required — else FAILED or PARTIAL):**

| # | Criterion |
|---|-----------|
| 1 | **True duplicates suppressed** — preregistered true-dup pairs classified `duplicate` (collapse) under the repair |
| 2 | **Known non-duplicates distinguishable** — preregistered known-nondup pairs classified `distinct` (or correctly `ambiguous` only under declared ambiguity policy, not auto-discard) |
| 3 | **Context-dependent distinctions preserved** — pairs that diverge on the frozen multi-context bank are not collapsed as hard duplicates |
| 4 | **Critical false-dup class no longer incorrectly collapsed** — Stage-5 critical pair (and like FALSE_DUPLICATE class under bank) is **held-out diagnostic**: repair must not hard-collapse it as `duplicate` when bank evidence shows divergence; success is about the **class**, not a hard-coded exception for those body keys |
| 5 | **No target-specific rule** — no S / odd-stride / CAT-self / critical-pair body-key recognizer; ablation shows mechanism is the equivalence relation, not a whitelist |
| 6 | **Not degenerate** — declaring everything `distinct`/`novel` OR collapsing everything = **NOT** successful |
| 7 | **Fair ablation** — baseline `FILTER_BEHAVIORAL_DUP` vs each repair under the **same** frozen benchmark; differences attributed to equivalence mechanism only |
| 8 | **Budget honesty** — extra evaluator calls charged to explicit Stage-6 experimental budget; Sacred BH48 untouched |

**PARTIAL:** meets some but not all of 1–5 under honest reporting (e.g., improves false-dup rate but raises missed-dup beyond prereg thresholds) without protocol violation.

**FAILED:** target-specific patch; tunes against held-out critical pair’s exact outputs; silent Sacred-budget consumption; changes proposal/invent/scoring/selection; or degenerates to all-novel / all-collapse.

**Not a success criterion:** S VERIFIED / Sacred pass / odd CAT-self survival in a live Sacred run.

---

## 3. How FP / FN measured?

Full definitions: `reports/aivd_3_40_stage6_metrics.md`. Summary:

| Metric | Definition (Stage-6) |
|--------|----------------------|
| **False-duplicate rate** | Among pairs that are **behaviorally distinct** under the frozen audit bank (ground truth `DISTINCT`), fraction classified `duplicate` by the mechanism |
| **Missed-duplicate rate** | Among pairs that are **behaviorally equivalent** under the frozen audit bank (ground truth `DUP`), fraction classified `distinct` (or left uncollapsed when should collapse) |
| **Distinct-preservation rate** | Among ground-truth `DISTINCT`, fraction classified `distinct` (or `ambiguous` retained per policy — report separately) |
| **Duplicate-collapse rate** | Among ground-truth `DUP`, fraction classified `duplicate` |
| **Ambiguity rate** | Fraction classified `ambiguous` (with cost/budget accounting) |
| Cost metrics | candidate-pool expansion proxy, evaluator calls, computational cost, Stage-6 experimental budget consumption |

**Ground truth** for Stage-6 offline benchmark = labels from the **frozen multi-context audit relation** (Stage-5 equality kinds), **not** from Sacred success and **not** from “desired S survival.”

**FP** ≈ false duplicate (collapse distinct). **FN** ≈ missed duplicate (fail to collapse true dup). Both must be reported; optimizing only FP on the critical pair is forbidden.

---

## 4. How avoid target-specific patch?

| Guard | Binding |
|-------|---------|
| Design constraint 1 | Do **not** start with S; reject designs that only work by recognizing known S / odd / critical body keys |
| Competing families first | Specify R-A…R-D (or renamed independently motivated families) **before** any implementation; each must be explainable without reference to S |
| Held-out diagnostic | Stage-5 critical pair is **HELD-OUT DIAGNOSTIC** where possible — do not tune repair hyperparameters / thresholds / context weights against its exact observed Stage-5 outputs |
| Frozen context bank | Generic bank frozen in prereg **before** seeing repair results; no contexts added post-hoc to separate the critical pair |
| Adversarial controls | Textually different but behaviorally identical; textually similar but behaviorally different — prevents “repair = textual/representation comparison” |
| Ablation | Attribute gains to equivalence mechanism under same benchmark; a repair that improves **only** the critical cell while harming true-dup/nondup batteries → REJECT / PARTIAL |
| Hypothesis REJECT leaf | H6-REJECT: repair is effectively a target-specific patch → design FAILED |

---

## 5. How evaluator cost bounded?

| Bound | Binding |
|-------|---------|
| Sacred BH48 | **Frozen / untouched** — Stage-6 must not silently consume discovery episode budget |
| Stage-6 experimental budget | Explicit envelope (prereg + metrics): max evaluator calls per pair, max contexts queried per ambiguity expansion, max total Stage-6 offline call budget |
| Cheap-first | Families that use two-stage / adaptive expansion (R-C, R-D) must preregister: when to expand, hard stop on calls, and what happens at budget exhaustion (`ambiguous` / defer — **not** auto-discard) |
| Accounting | Every `apply_micro` beyond the live singleton identity probe counts toward Stage-6 experimental budget and is reported |
| Degeneracy check | A “repair” that queries unbounded contexts until everything looks distinct = FAILED (cost + novelty abuse) |

Exact numeric envelopes: `reports/aivd_3_40_stage6_preregistration.md` § budget locks + `reports/aivd_3_40_stage6_metrics.md`.

---

## 6. How original filter compared fairly vs each repair?

| Requirement | Binding |
|-------------|---------|
| Same benchmark | Identical frozen pair set, context bank, seeds, ground-truth labels |
| Same classification interface | Output ∈ {`duplicate`, `distinct`, `ambiguous`} mapped from baseline: live `_keep` reject-as-dup → `duplicate`; keep → `distinct`; baseline has **no** native `ambiguous` (report as N/A / mapped `distinct` with note) |
| Mechanism-only delta | Only the equivalence / classification subroutine differs; no change to proposal generation, invent, growth operators, scoring, selection, verification, firewall |
| Ablation table | Baseline `FILTER_BEHAVIORAL_DUP` vs R-A vs R-B vs R-C vs R-D (and any renamed family) on all prereg metrics |
| No post-hoc pair add | Pair set frozen before repair outcomes inspected |

Implementation note for **future** EXECUTION only: repairs are evaluated as **offline classifiers** over pair envelopes first; wiring into `_keep` is a **separate** authorization and still classification-only.

---

## 7. What evidence required before fresh Sacred even considered?

Fresh Sacred is **not** authorized by Stage-6 design. A **separate** Sacred charter may be considered **only if ALL** hold:

1. Offline Stage-6 EXECUTION COMPLETE with gate ≠ FAILED  
2. Success criteria §2 items 1–7 met for at least one repair family (or honest PARTIAL with explicit go/no-go)  
3. No target-specific rule detected (H6-REJECT not supported)  
4. Sacred BH48 still frozen as in baseline; Stage-6 costs fully accounted in experimental budget  
5. Stage-5 FALSE_DUPLICATE artifacts untouched and still reproducible  
6. Separate Sacred charter explicitly re-states: not make S pass as scientific objective; namespaces AUTONOMOUS vs OFFLINE_EVAL vs CONTROLLED_INPUT separate  

**This commit does NOT authorize Sacred S run.**

---

## 8. Competing repair families (design before impl)

Full independent specs: `reports/aivd_3_40_stage6_equivalence_repair_spec.md`. Summary (motivating examples — not assumed final names if independently renamed):

| Family | One-line claim |
|--------|----------------|
| **R-A** Multi-context behavioral signature | Equivalence = equality of output tuples (or hashes) across a **fixed** frozen context bank, not singleton identity |
| **R-B** Context-sensitive equivalence | Equivalence judged under an explicit context-sensitivity policy (agreement rate / family-wise gates), allowing partial agreement without hard collapse |
| **R-C** Adaptive context expansion | Start cheap (identity); when collision is ambiguous, expand into preregistered reserve contexts under a hard call budget |
| **R-D** Two-stage (cheap identity → semantic disambiguation) | Stage-1 identity collision triage; Stage-2 semantic disambiguation only on collisions; non-colliding pairs stay `distinct` without extra calls |

Each family must independently specify: classification outputs, ambiguity policy, cost rule, failure modes, and why it is **not** an S-special case.

---

## 9. Hypothesis decomposition (H6*)

Full tree: `reports/aivd_3_40_stage6_hypothesis_tree.md`. Summary:

| ID | Claim |
|----|-------|
| **H6a** | A generic multi-context / signature mechanism can jointly achieve duplicate retention and novelty retention on the frozen benchmark |
| **H6b** | Cheap identity collision is necessary but insufficient; disambiguation / expansion is required for FALSE_DUPLICATE-class pairs |
| **H6c** | Ambiguity-aware policies (defer / expand / provisional novelty) dominate hard binary collapse under the same budget envelope |
| **H6d** | Cost–quality tradeoff: higher Stage-6 evaluator budgets improve distinct-preservation up to a prereg plateau without destroying duplicate-collapse |
| **H6-REJECT** | Apparent gains require target-specific / critical-pair-special / textual-only rules → design FAILED |

Interpretation conclusions for future EXECUTION: exactly one primary among SUCCESS / PARTIAL / FAILED / INCONCLUSIVE per charter metrics gate (see hypothesis tree).

---

## 10. Frozen endpoints & live filter anchors (read-only)

| Role | SHA / path |
|------|------------|
| Current tip (Stage-5 complete) | `c003e60` |
| Stage-5 design | `2496857` |
| Stage-4 complete | `4005e66` |
| Stage-3 | `146915b` |
| Stage-2 | `dcae889` |
| Phase-1 | `a2ab0cc` |
| Phase-2 | `f4d7a2b` / design `7be4124` |

Live filter (immutable cite; tip `c003e60` / grow unchanged since `4005e66`):

| Anchor | Location | Role |
|--------|----------|------|
| Live collapse | `aivd/science/grow.py::propose_growth` nested `_keep` | `got = apply_micro(identity, body2)`; reject if `got in behaviors.values()` |
| Label | `FILTER_BEHAVIORAL_DUP` | `aivd/experiments/aivd340/stage4_audit.py` + `stage4_constants.py` |
| Named helper (NOT live `_keep`) | `behavioral_equivalent(...)` | Multi-probe helper — must not be confused with singleton identity rule |
| Behavior map | `behaviors: dict[str, str]` | Seeded from promoted atoms; updated on keep |

**Stage-6 repair designs may propose classification replacements for the `_keep` behavioral-dup step only** — under future EXECUTION — without altering surrounding canonicalize / known_keys / validate / identity-noop / proposal loops.

---

## 11. Experimental matrix (design sketch)

| Factor | Levels |
|--------|--------|
| Mechanism | `BASELINE_FILTER_BEHAVIORAL_DUP` \| `R-A` \| `R-B` \| `R-C` \| `R-D` |
| Pair class | `TRUE_DUP` \| `KNOWN_NONDUP` \| `CONTEXT_DEPENDENT` \| `U_GOOD` \| `ADV_TEXT_DIFF_BEH_SAME` \| `ADV_TEXT_SIM_BEH_DIFF` \| `HELD_OUT_CRITICAL` (diagnostic) |
| Audit mode | `OFFLINE_REPAIR_BENCH` (primary) |
| Context family | `BASELINE_IDENTITY` \| `TRANSFORMED` \| `BOUNDARY` \| `COMPOSITION` \| `ORDERING` \| `STATE_CONTEXT` (frozen; see repair_spec) |
| Classification | `duplicate` \| `distinct` \| `ambiguous` |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Sacred budget | **BH48 frozen** (not consumed) |
| Stage-6 exp budget | Explicit call envelope (prereg) |
| Representation | Frozen **R1**; **no** auto R1b |

Full JSON: `reports/aivd_3_40_stage6_matrix.json`.

---

## 12. Ambiguity handling (binding)

When cheap identity says DUPLICATE but semantic evidence is insufficient:

| Strategy | Allowed | Must preregister |
|----------|---------|------------------|
| Defer | yes | budget / when / final label if still unresolved |
| Request additional context | yes | only from **frozen** reserve bank; hard call cap |
| Retain provisional novelty | yes | counts as novelty-retention path; report separately from hard `distinct` |
| Semantic disambiguation | yes | R-D Stage-2; cost rule |
| Auto-discard as duplicate | **NO** when evidence insufficient | — |

Do **not** auto-discard on ambiguous collision.

---

## 13. Prohibitions

| Forbidden | Why |
|-----------|-----|
| Implement repair / edit `grow.py` / `_keep` / discovery pipeline in this commit | Design only |
| Execute Stage-6 benchmark or Sacred | No auto-authorization |
| Modify Stage-5/4/Phase/Stage-2/3 / 3.38/3.39 historical artifacts | Immutability; FALSE_DUPLICATE must stay reproducible |
| S-specific / odd-stride / CAT-self / critical-pair body-key exceptions | Target-specific patch |
| Tune repair against held-out critical pair’s exact Stage-5 outputs | Contaminates diagnostic |
| Add contexts after seeing repair results | Prereg violation |
| Silently consume Sacred / discovery BH48 for repair probes | Budget firewall |
| Change proposal generation, invent, growth ops, scoring, selection, verify, firewall, discovery prompts | Classification-only |
| Make S pass framing / authorize Sacred S | Out of scope |
| Auto R1b / R1c / BHexplore / Level-14 | Caveat `7a3457e` |
| Weaken Stage-5 H5b/H5d | Established evidence |

---

## 14. Exit / final gate

This commit delivers **design** only. No execution or implementation authorization is granted.

```
STAGE-6 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

If a future design edit would require S-special cases, Mode merge, silent Sacred-budget use, historical mutation, or “make S pass” framing, the gate becomes:

```
STAGE-6 DESIGN BLOCKED: <exact reason>
```

---

## 15. Parent commits (authority map)

| Role | SHA | Note |
|------|-----|------|
| Stage-6 design start tip / Stage-5 COMPLETE | `c003e60` | H5b+H5d; FALSE_DUPLICATE critical pair |
| Stage-5 design freeze | `2496857` | Equivalence-audit design READY |
| Stage-4 COMPLETE | `4005e66` | H2c; FILTER_BEHAVIORAL_DUP location |
| Stage-4 design | `27e9e88` | Observational growth audit |
| Phase-2 complete / design | `f4d7a2b` / `7be4124` | Mode A/B localization |
| Phase-1 | `a2ab0cc` | Offline trajectory |
| Stage-3 | `146915b` | Localization design |
| Stage-2 | `dcae889` | Immutable Sacred aggregates |
| R1b caveat | `7a3457e` | No auto re-run |

---

## 16. What this commit does NOT do

- No Sacred / Stage-6 execution / repair implementation  
- No mutation of historical Stage-5/4/Phase/Stage-2/3 / 3.38/3.39 artifacts  
- No claim that R-A…R-D are already validated — Stage-6 design exists to specify how they will be tested  
- No claim that Mode B / offline eval = autonomous discovery  
- No R1b / R1c / BHexplore / Level-14 work  
- No authorization of fresh Sacred even if offline success is later obtained — that requires a **separate** charter  


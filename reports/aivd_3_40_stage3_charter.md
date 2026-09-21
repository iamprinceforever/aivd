# AIVD 3.40 Stage-3 Scientific CHARTER — S-Bottleneck Localization

**Document type:** Scientific charter / preregistration scaffold (DOCS ONLY)  
**Recorded:** 2026-09-21 17:04 IST  
**Base tip (Stage-2 complete):** `dcae889` (`research/aivd-3.40-budget-representation-frontier`)  
**Status:** **CHARTER FROZEN FOR LOCALIZATION DESIGN** — **NO IMPLEMENTATION** in this commit  
**Scope:** Identify the *earliest causal bottleneck* explaining why target **S** does not pass while target **U** does under Stage-2 BH48 Sacred conditions. Unresolved S is a **valid preserved scientific result**.

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Scientific objective | Localize earliest bottleneck for S-fail / U-pass — **NOT** make S pass |
| Docs only this commit | Files under `reports/` (+ optional JSON manifests in `reports/`) |
| Zero code / config / Sacred edits | No changes to `aivd/`, `aivd37/`, `tests/`, discovery configs |
| No Stage-3 implementation | No R1c, no budget raise, no Sacred, no runtime/test changes |
| No GT injection | Do **not** encode S / ODDSTRIDE / odd-double / CAT-self plant GT / ROL1 into any proposed discovery mechanism |
| R1b integrity caveat (mandatory) | Commit `7a3457e` trimmed invent basis ≤3 **AFTER smoke / before Sacred** → **R1b Sacred is NOT pure Commit-B prereg**. State explicitly; **never** claim preregistered-unchanged |
| Positive control | Preserve BH-R1 × U interpretation as known-positive |
| STOP after charter | Implementation requires a **separate explicit EXECUTION charter** (see FINAL DECISION GATE) |

Companion deliverables (all under `reports/`):

1. `aivd_3_40_stage3_charter.md` — **this file** (master + FINAL DECISION GATE)
2. `aivd_3_40_stage3_hypothesis_tree.md` — H1–H6 causal tree
3. `aivd_3_40_stage3_experimental_matrix.md` (+ `aivd_3_40_stage3_experimental_matrix.json`)
4. `aivd_3_40_stage3_instrumentation_spec.md`
5. `aivd_3_40_stage3_counterfactual_replay_spec.md`
6. `aivd_3_40_stage3_preregistration.md` — freeze protocol + revision policy

---

## 1. Immutable Stage-2 data (cite only; do not re-interpret as success)

**Source of truth:** `reports/aivd_3_40_stage2_results.md` (tip lineage through `fb61eb8` / `dcae889`).

| Condition | Target | Firewall | Independent (strict) | Verified | Leakage | Mean budget |
|-----------|--------|----------|----------------------|----------|---------|-------------|
| BH-R1 | S | 7 | 0 | **0** | 0 | 32.0 |
| BH-R1 | U | 7 | 7 | **7** | 0 | 32.0 |
| BH-R1b | S | 7 | 0 | **0** | 0 | 32.0 |
| BH-R1b | U | 0 | 0 | 7 | 0 | 48.0 |

**Qualitative Stage-2 observations (data, not cures):**

- **BH-R1 × S:** firewall 7/7; odd CAT-self still not grown — even CAT-self preferential; terminal `UNRESOLVED_INVISIBLE`.
- **BH-R1b × S:** odd-stride **atom invented** under geo class split; growth still prefers even CAT-self / compose; **finished odd CAT-self not selected for verify**; still 0/7 VERIFIED.
- **BH-R1 × U:** strict-independent VERIFIED **7/7** — **positive control PRESERVED**.
- **BH-R1b × U:** pipeline VERIFIED 7/7 but firewall_epoch=0 / Independent(strict)=0/7 — independence bar fails (Case D).
- **Leakage:** 0 across matrix.

**R1b integrity caveat (non-negotiable wording):**

> Stage-2 R1b Sacred executed after commit `7a3457e`, which trimmed the invent basis to ≤3 geometric classes **after smoke and before Sacred**. Therefore R1b Sacred results are **NOT** pure Commit-B preregistered-unchanged evidence. They remain usable observational data for bottleneck localization, but must not be cited as a clean prereg success/failure of the original R1b design.

Stage-2 interpretation Case: **D** (S≈0; U independence harmed under R1b). See Stage-2 results document.

---

## 2. Scientific objective (Stage 3 charter)

**Primary question:** What is the *earliest* pipeline stage at which S systematically diverges from U under matched BH-R1 (and, secondarily, BH-R1b observational) conditions?

Pipeline stages (ordered earliest → latest):

1. **Invent / representation** — required direction never enters the candidate language  
2. **Growth / composition** — direction invented but finished programs not grown/composed  
3. **Candidate selection / ranking** — finished programs exist but are not selected  
4. **Verification targeting** — selected but verification does not accept / does not target  
5. **Budget starvation** — correct trajectory truncated by leftover exhaustion  
6. **Generic AIVD machinery failure** — S and U should behave alike but do not due to shared-stack defect

**Non-objectives (explicitly out of scope for this charter):**

- Making S pass  
- Designing R1c / plant-named representation  
- Raising Sacred B32 / BH48 floors as a “fix”  
- Modifying firewall, REDISCOVERY_FLOOR, invent_cap, propose_atoms, verification semantics  
- Claiming Stage-3 recursive generation without a **new** charter after localization completes

**Valid terminal scientific outcomes include:** S remains unresolved with earliest bottleneck = {H1|H2|H3|H4|H5|ambiguous after instrumentation}, or H6 remains unrejected pending pipeline-invariant confirmation.

---

## 3. Hypothesis tree (summary; full tree in companion)

| ID | Causal claim | Stage-2 prior weight (brief) |
|----|--------------|------------------------------|
| **H1** | Representation / discovery cannot express required S direction | **Weakened** for pure “cannot invent odd”: R1b×S invented odd-stride atom |
| **H2** | Growth / composition fails to finish required programs | **Strengthened**: invent happened; finished odd CAT-self not grown/preferred |
| **H3** | Candidate selection / ranking fails to promote required candidates | **Plausible**: “not selected for verify” language in Stage-2 S notes |
| **H4** | Verification targeting / acceptance fails after selection | **Weaker a priori**: S reports suggest selection never handed the right body |
| **H5** | Budget starvation truncates an otherwise viable trajectory | **Not supported as primary**: mean leftover path shows firewall reached (R1 S/U mean budget 32); exploratory only if Phase-1 shows leftover starvation after correct selection |
| **H6** | Generic AIVD machinery failure (shared stack broken) | **Weakened** by BH-R1×U 7/7, **not eliminated** until instrumentation confirms S/U share identical invent→grow→select→verify invariants |

Full reject/accept evidence maps: `reports/aivd_3_40_stage3_hypothesis_tree.md`.

---

## 4. Experimental matrix (summary; full matrix in companion)

**Design principle:** Controlled, matched interventions on **both** S and U; preserve BH-R1×U as positive control; never retune S or U independently; no target-specific assistance.

### Phase 0 — THIS COMMIT (docs)

Freeze this charter + companions. No code. No Sacred.

### Phase 1 — FIRST RECOMMENDED FUTURE WORK (describe only; not authorized here)

**Audit / instrumentation-first + offline counterfactual replay** of existing Stage-2 BH-R1 and BH-R1b S/U trajectories.

- Goal: localize invent vs grow vs select vs verify **without new Sacred**  
- Inputs: Stage-2 run JSONs under `reports/aivd_3_40_stage2/runs/` + generation graphs  
- Method: per-generation instrumentation fields (spec companion) + evaluator-only counterfactual “what if X selected?” (replay companion)  
- Stop rule: if a single earliest bottleneck is identified with predefined reject criteria for competing Hs → **STOP localization**; do not chase S

### Phase 2 — Future Sacred ONLY IF Phase 1 leaves H ambiguous (describe only)

Preregistered minimal matrix sketch (refine after Phase 1; requires EXECUTION charter):

| Factor | Levels | Notes |
|--------|--------|-------|
| Representation | `{R1 frozen}` × optional `{Rx}` | **Rx is NOT defined here.** Any Rx = placeholder requiring **separate prereg after Phase 1**; generic properties only; **must not** encode odd-stride/S/ODDSTRIDE/ROL1/plant GT |
| Selection / audit mode | `{baseline live}`, `{audit-only offline}` | Prefer offline first |
| Budget | `{BH48 frozen}` × optional `{BHexplore}` | Exploratory **only if** Phase 1 shows leftover starvation after correct selection; matched controls; larger budget success alone ≠ proof H5 |

**Seeds (when Sacred eventually authorized):** `[0, 1, 2, 3, 4, 7, 11]` for continuity.  
**Plants:** **Fresh** Stage-3 plant IDs (not Stage-2 `AIVD340-S2-*` for new claims).  
**Positive control:** every live matrix must include BH-R1 × U (or frozen-equivalent) cells.

Full factorial, stop rules, and interpretation binding: `reports/aivd_3_40_stage3_experimental_matrix.md`.

---

## 5. Instrumentation mandate (summary)

Every generation / decision point recorded for Stage-3 localization must expose at least:

`generation_id`, `parent_id`, `firewall_epoch`, `candidate_origin`, representation/features used, invented atoms, composed candidates, candidate scores, ranking, selected candidate, verification candidate, verification result, remaining budget, rejection/skip reason.

Must be able to answer, per seed × target × condition:

1. Did S fail to **INVENT** required direction?  
2. Invent but fail to **GROW**?  
3. Grow but fail to **SELECT**?  
4. Select but fail to **VERIFY**?

Full schema: `reports/aivd_3_40_stage3_instrumentation_spec.md`.

---

## 6. Counterfactual replay mandate (summary)

Evaluator-only; **no discovery feedback**. Label every record **observed** vs **counterfactual**. Classification:

| Replay finding | Earliest bottleneck class |
|----------------|---------------------------|
| Required direction **never produced** | Earlier than selection (H1 or H2) |
| Produced but **not selected** | Selection / growth preference (H2/H3) |
| Selected but **not verified** | Verification (H4) |
| Correct path truncated by budget | Budget (H5) — only with leftover evidence |

Full protocol: `reports/aivd_3_40_stage3_counterfactual_replay_spec.md`.

---

## 7. Success / failure interpretation table (pre-mapped)

Outcomes are about **localization quality**, not S-pass rate.

| Case | Pattern (after Phase 1 ± Phase 2) | Hypothesis firing | Action |
|------|-----------------------------------|-------------------|--------|
| **A** | Required S direction never appears in invent set under R1; U invents rotate-class normally; Rx (if later prereg’d) restores invent without plant tokens | **H1** primary | Document H1; do **not** silently patch invent basis mid-Sacred |
| **B** | Invent occurs (as in R1b×S odd-stride); finished required program never grown/composed; counterfactual grow would produce it | **H2** primary | Document growth bottleneck; forbid plant-specific grow hooks |
| **C** | Finished program appears in candidate pool with competitive features but systematically loses ranking / not chosen for verify | **H3** primary | Document selection bottleneck |
| **D** | Selected candidate matches required direction; verification rejects or never targets it; U verify path intact | **H4** primary | Document verification bottleneck; do not weaken verification |
| **E** | Correct invent→grow→select trajectory visible mid-episode; leftover hits 0 before verify; matched larger budget (exploratory) completes **and** controls rule out H1–H4 | **H5** contributory (not sole proof from budget alone) | Budget claim only with matched controls |
| **F** | Instrumentation shows S/U invariant violation in shared machinery (identical inputs → asymmetric illegal state) while BH-R1×U still 7/7 | **H6** remains live / possibly primary | Repair only under new charter; do not “fix S” |
| **G** | **S remains unresolved**; earliest bottleneck localized to X ∈ {H1…H5} with U positive control preserved | **VALID SUCCESS of Stage-3 localization** | STOP; unresolved S preserved |
| **H** | Ambiguous after Phase 1; Phase 2 still ambiguous | Localization **FAIL** (design), not S-fail | STOP + revise prereg — no post-hoc factor fishing |

**Mandatory Case G wording:** “S remains unresolved with earliest bottleneck = X” is an acceptable and preferred scientific endpoint.

---

## 8. FROZEN list (Stage 3 must not modify)

| Frozen artifact / rule | Binding |
|------------------------|---------|
| Sacred **3.38** / **3.39** artifacts & baselines | Immutable historical record |
| `propose_atoms` **8-set** | Immutable |
| `REDISCOVERY_FLOOR = 5` | Immutable |
| `invent_cap = 48` | Immutable |
| Firewall / verification / `GenerationRecord` semantics | Immutable |
| BH-R1 × U positive-control interpretation | Immutable (7/7 strict-independent VERIFIED on Stage-2 fresh U) |
| Stage-2 observations as **data** | Cite; do not overwrite run artifacts to change Case D |
| Absolute Rules: **no GT injection** into discovery | Immutable |
| Sacred B32 historical cells / Stage-1 replication locks | Immutable |
| R0 behavior when not in R1/R1b modes | Unchanged |

---

## 9. FORBIDDEN list (Stage 3 must not do)

| Forbidden action | Why |
|------------------|-----|
| Modify any FROZEN item above | Integrity |
| Implement Stage 3 / R1c / budget raise in this charter commit | Docs-only mandate |
| Name a representation **R1c** after S or odd-stride plant geometry | Target-specific assistance |
| Encode S / ODDSTRIDE / odd-double / CAT-self GT / ROL1 into discovery features | GT injection |
| Force-firewall / silent smoke patches that change Sacred semantics | Anti-pattern |
| Post-hoc invent-basis trim after smoke (the `7a3457e` pattern) | Breaks prereg |
| Add/remove proposal classes, change ranking, floor/cap/verification after smoke or Sacred | Breaks prereg |
| Use Stage-2 S2 plants for **new** Sacred success claims | Fresh plants required |
| Retune S or U independently / different interventions per target | Confounds localization |
| Claim R1b Sacred was preregistered-unchanged | False; `7a3457e` caveat |
| Stage-3 recursive generation / “make S pass” chase without **new** charter after localization | Scope creep |
| Open implementation without FINAL DECISION GATE satisfaction | Hard gate |

---

## 10. Preregistration pointer

Full freeze protocol, revision policy, and anti-pattern callout for `7a3457e`:  
`reports/aivd_3_40_stage3_preregistration.md`.

**One-line freeze rule:** Freeze commit hash **before** any Stage-3 Sacred; design flaw → **STOP** + new prereg revision — never silent mid-flight patch.

---

## 11. Deliverable checklist (user charter §§11)

| # | Deliverable | Path | Present |
|---|-------------|------|---------|
| 1 | Master charter + FINAL DECISION GATE | `reports/aivd_3_40_stage3_charter.md` | YES |
| 2 | Hypothesis tree H1–H6 | `reports/aivd_3_40_stage3_hypothesis_tree.md` | YES |
| 3 | Experimental matrix (+ optional JSON) | `reports/aivd_3_40_stage3_experimental_matrix.md` / `.json` | YES |
| 4 | Instrumentation spec | `reports/aivd_3_40_stage3_instrumentation_spec.md` | YES |
| 5 | Counterfactual replay spec | `reports/aivd_3_40_stage3_counterfactual_replay_spec.md` | YES |
| 6 | Preregistration / freeze protocol | `reports/aivd_3_40_stage3_preregistration.md` | YES |
| 7 | Success/failure interpretation table | §7 this file | YES |
| 8 | FROZEN list | §8 this file | YES |
| 9 | FORBIDDEN list | §9 this file | YES |

---

## 12. FINAL DECISION GATE (hard)

**Stage-3 *implementation* is permitted only after this charter demonstrates that the proposed experiment can distinguish H1–H6.**

### Distinguishing power (why this charter is sufficient *as a design*)

| Contrast | Distinguishes |
|----------|---------------|
| Offline invent-set presence vs absence (Phase 1) | H1 vs later |
| Invent present + grow absent vs grow present (counterfactual grow) | H1/H2 vs H3+ |
| Pool contains finished program + not selected | H3 vs H4 |
| Selected + verify fail | H4 |
| Correct path + leftover=0 before verify; budget exploratory with matched controls | H5 vs H1–H4 |
| Shared-stack invariant checks S vs U under identical mode | H6 residual |

### Additional evidence required before rejecting H6

H6 is **weakened** by BH-R1 × U = 7/7 strict-independent VERIFIED, but **must not be rejected** until Phase-1 instrumentation confirms:

1. S and U episodes under BH-R1 share the same mode flags, invent_cap, floor, firewall arming predicates, and GenerationRecord origin rules;  
2. No S-only exception path / plant-id branch exists in discovery (leakage already 0; still confirm control-flow invariants);  
3. U’s verified body trajectory is reconstructible end-to-end under the same recorder that will audit S;  
4. Any S failure is classifiable as H1–H5 with explicit per-generation evidence rather than an unexplained illegal state.

Until (1)–(4) hold, H6 remains an open alternative explanation.

### Gate statement (binding)

> **STOP — Stage-3 implementation requires a separate explicit EXECUTION charter.**  
> This document freezes localization *design* only. No instrumentation code, no replay runner, no Sacred, no R1c, no budget raise, and no discovery edits are authorized by this commit.

---

## 13. One-sentence objective

**Localize the earliest causal bottleneck that explains why S stays unresolved while U verifies under Stage-2 BH-R1 — without making S pass and without implementing Stage 3 in this commit.**

---

## STOP

Docs-only charter complete. No Stage-3 implementation. No Sacred. Unresolved S remains a valid preserved result.

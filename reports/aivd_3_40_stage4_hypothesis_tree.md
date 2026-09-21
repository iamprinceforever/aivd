# AIVD 3.40 Stage-4 — Hypothesis Tree (H2 → H2a…H2f)

**Document type:** Stage-4 hypothesis tree (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 18:45 IST  
**Parent charter:** `reports/aivd_3_40_stage4_charter.md`  
**Phase-2 prior:** `reports/aivd_3_40_phase2_results.md` (tip `f4d7a2b` / exec `d1e31b5`)  
**Authority:** Stage-3 tree `reports/aivd_3_40_stage3_hypothesis_tree.md` (H1–H6); this document **decomposes H2 only**  
**R1b caveat:** `7a3457e` — do not auto-rerun R1b; observational cite only  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

**Scientific goal:** Identify the earliest mechanism preventing an already-available odd-stride atom (`MAPT(SLICE:1,2(TOK))`, CONTROLLED_INPUT) from becoming a growth/composition candidate (finished odd CAT-self `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` absent from pool). Unresolved S remains valid. Do **not** make S pass.

---

## 0. Inherited macroscopic status (Phase-2; immutable)

| Macro H | Stage-4 stance |
|---------|----------------|
| **H1** | Upstream **AUTONOMOUS** barrier (Mode A × S odd-stride invent absent 7/7). Stage-4 does **not** reopen H1 as primary; CONTROLLED experiments presuppose availability |
| **H2** | **SUPPORTED** at Outcome-1 grain (finished odd CAT-self absent from growth pools 7/7 under Mode B × S). Stage-4 asks **why** |
| **H3** | **NOT supported** as Phase-2 primary — candidate never in pool. May be **reopened** only if Stage-4 shows pool membership |
| **H4–H6** | Not primary Stage-4 targets; retain Stage-3 reject criteria if unexpectedly implicated |

**Epistemic fence:** “Absent from pool” ≠ “selector rejected it.” “Not composed online” ≠ “cannot compose” unless composition attempts are observed.

---

## Causal order inside H2 (earliest → latest)

```
H2a compatibility/composition constraint
  → H2b growth grammar/operator limitation
    → H2c structural filtering before pool formation
      → H2d objective/utility bias against odd branch
        → H2e missing intermediate representation
          → H2f budget-dependent growth exclusion
[post-pool] selection/ranking (H3-class)  — only if pool membership observed
```

An earlier leaf that fires **preempts** later leaves as *primary* unless evidence shows the earlier stage succeeded.  
**Ambiguity allowed:** “cannot distinguish H2a vs H2b with existing evidence” is a valid Stage-4 result.

---

## H2a — Compatibility / composition constraint

**Claim:** The controlled odd-stride atom fails **compatibility** gates that determine whether it may participate as a CAT-self / compose parent (e.g., `tokens_shorter(identity, apply_micro(...))` fails; `cat_self_body` returns None for non-MAPT shapes; semantic_class / distinct-class compose pairing excludes it), while known-good U parents pass analogous gates.

### Phase-2 prior weight

| Evidence | Effect |
|----------|--------|
| Mode B injects odd-stride as PROMOTED; finished odd CAT-self still absent from pools 7/7 | Consistent with H2a **or** later leaves |
| Phase-2 recorder did not emit per-gate compatibility trails | H2a **unresolved** at mechanism grain |

### Reject H2a if

- Compatibility gates pass for the controlled odd-stride parent (shortening + MAPT CAT-self shape + promoted admissibility), **and** failure occurs at operator emission / filter / budget / intermediate.

### Accept H2a as earliest if

- Named compatibility tests fail for CONTROL B while CONTROL A (U known-good) passes at the same stage; no successful operator applicability downstream.

### Code anchors (observational)

- `aivd/science/grow.py::tokens_shorter`, `cat_self_body`
- `propose_growth` promoted + class loops
- `pick_compose_pair` distinct-class requirement

---

## H2b — Growth grammar / operator limitation

**Claim:** Existing growth operators **cannot** emit the finished odd CAT-self (or any verification-relevant odd composition) from legal parents — grammar/`propose_growth` / `cat_self_body` / compose API limitation — even when compatibility would allow consideration.

### Phase-2 prior weight

| Evidence | Effect |
|----------|--------|
| Growth prefers even CAT-self / compose historically (Stage-2 / Phase-1 notes) | Mild prior for operator/grammar preference |
| Offline path not yet preregistered in Phase-2 | H2b vs H2e not separable yet |

### Reject H2b if

- Offline intermediate-representation test (EXISTING operators only) constructs a valid path to `ODD_CAT_SELF_BODY_KEY`, **or**
- Online audit observes successful generation of that body (even if later filtered).

### Accept H2b as earliest if

- Compatibility passes (or is moot); applicable-operator census shows **no** operator can produce the finished body; offline path also absent.

### Code anchors

- `cat_self_body`, `propose_growth`, `propose_growth_candidates`, `ExperimentLanguage.compose`, `pick_compose_pair`

---

## H2c — Structural filtering before pool formation

**Claim:** A composition involving the odd-stride parent **is generated** (transiently) but **structural filters** drop it before it enters `growth_cands` / candidate pool (`known_keys`, `validate_micro`, identity-noop, behavioral-duplicate in `_keep`).

### Phase-2 prior weight

| Evidence | Effect |
|----------|--------|
| Pool absence Outcome 1 | Consistent with H2c **if** generation occurred pre-filter — **not observed** in Phase-2 fields |
| Phase-2 hooks snapshot assembled `growth_cands` post-`propose_growth_candidates` | Pre-pool rejects may be invisible → UNKNOWN until Stage-4 recorder extends **observationally** |

### Reject H2c if

- No generation attempt reaches `_keep` for odd CAT-self; or body appears in pool.

### Accept H2c as earliest if

- Audit shows attempted/successful micro construction then explicit rejection reason in structural-filter enum; body never in pool; compatibility + operator applicability passed.

### Code anchors

- `propose_growth` nested `_keep` (known_keys, validate_micro, identity, behavioral duplicate)

---

## H2d — Objective / utility bias against the odd branch

**Claim:** Search / ranking utility (`parent_rank`, growth ordering, invent-before-grow scheduling) systematically avoids expanding or retaining the odd branch such that odd compositions are never generated or never retained under the live schedule — **distinct from** post-pool H3 if the body never enters the pool snapshot.

### Phase-2 prior weight

| Evidence | Effect |
|----------|--------|
| `pick_generation_action` prefers earliest parent_rank among existing growth_cands | Can bias **among** pool members; does not by itself explain empty pool |
| Outcome 1 = absent from pool | H2d alone is a **weak** primary unless audit shows odd-eligible generation slots skipped due to utility while U slots are taken |

### Reject H2d if

- Generation attempts for odd parents occur at rates comparable to U controls and fail for H2a/H2b/H2c/H2e/H2f reasons instead.

### Accept H2d as earliest (narrow) if

- Instrumentation shows odd-compatible parents repeatedly lose scheduling/utility contests **before** composition attempts that CONTROL A receives; pool never sees odd products; offline grammar path exists.

### Must not

- Relabel Phase-2 Outcome 1 as H3/H2d without pool-stage evidence.

### Code anchors

- `pick_generation_action` / `parent_rank`
- `ScienceDesigner._maybe_next_generation` invent-vs-grow gating (`_untried_atom_classes`)

---

## H2e — Missing intermediate representation

**Claim:** Finished odd CAT-self is not a **single-step** product of existing operators from the controlled atom alone; a missing intermediate program/atom is required. Online discovery never constructs that intermediate (and Stage-4 must **not** insert it into autonomous discovery).

### Phase-2 prior weight

| Evidence | Effect |
|----------|--------|
| Single controlled atom available; finished CAT-self absent | Compatible with H2e **or** H2b |
| No offline path audit in Phase-2 | Unresolved |

### Reject H2e if

- Single-step `cat_self_body(odd_stride)` yields `ODD_CAT_SELF_BODY_KEY` under offline apply (supports generation-ability → look to H2c/H2d/H2f if online fails).

### Accept H2e as earliest if

- Offline: no single-step path; multi-step path using existing operators exists **or** is proven impossible (if impossible → prefer H2b); online never builds required intermediate.

### Design test

- Offline/controlled intermediate-representation test (charter §5). Label records `OFFLINE_IR` / `CONTROLLED`. Never credit as AUTONOMOUS.

---

## H2f — Budget-dependent growth exclusion

**Claim:** Under frozen BH48, leftover floors (`leftover < 3`), `MAX_RUNTIME_GENERATIONS`, or invent scheduling exhaust the window in which an otherwise legal odd growth could be proposed — **not** the same as grammar impossibility.

### Phase-2 prior weight

| Evidence | Effect |
|----------|--------|
| BH48 frozen; Phase-2 did not reopen H5 | H2f not primary a priori |
| Firewall reached historically on many S cells | Weakens “never started” starvation; does not eliminate growth-window starvation |

### Reject H2f if

- At failure points, leftover ≥ 3 and safety cap not binding, yet odd products still absent for H2a–H2e reasons.

### Accept H2f as candidate if

- Audit shows odd-eligible gates would pass but growth skipped solely for leftover/safety/scheduling; offline grammar path exists.

### Binding budget rule

- Do **not** raise budget as first response. Separate preregistered budget-factor experiment only if H2f emerges. Distinguish “not generated within current search” vs “impossible under growth grammar.”

### Code anchors

- `ScienceDesigner._maybe_grow` / `_maybe_next_generation` leftover&lt;3
- `MAX_RUNTIME_GENERATIONS` / `REDISCOVERY_FLOOR` (unchanged)

---

## Post-pool revision clause (not an H2 leaf)

If CONTROL B audit shows finished odd CAT-self **∈ candidate pool**, then:

1. Phase-2 claim “H2 SUPPORTED as whole explanation of Outcome 1” is **scope-incomplete** for that seed  
2. Reopen **H3-class** selection/ranking with Phase-2 outcome map (2/3/…)  
3. Do **not** treat pool presence as Sacred S success  

---

## Cross-leaf decision table (Stage-4 oriented)

| Observation (CONTROL B; vs A/C) | Prefer |
|---------------------------------|--------|
| Fails `tokens_shorter` / MAPT-shape / promoted admissibility | **H2a** |
| Compatible; no operator can emit finished body; offline path absent | **H2b** |
| Emitted then dropped by `_keep` / validate / duplicate | **H2c** |
| Offline single-step works; online never attempts due to utility/schedule | **H2d** (narrow) |
| Needs intermediate; offline multi-step path; online never builds it | **H2e** |
| Grammar OK; leftover/safety starve eligible windows | **H2f** |
| Body ∈ pool | **Post-pool / H3-class** (revise H2 scope) |
| Cannot separate H2a vs H2b | **INCONCLUSIVE between H2a/H2b** (valid) |
| Recorder integrity failure | Outcome **6**-class INCONCLUSIVE |

---

## Controls mapping

| Control | Use in tree |
|---------|-------------|
| **A** U known-good | Positive: growth machinery can accept/compose a known-positive direction |
| **B** odd-stride S controlled | Primary leaf discrimination |
| **C** null | Side-effect / null baseline |

---

## Add-more rule

Additional H2* hypotheses only if **independently motivated** by Stage-4 evidence (new gate discovered, new operator class, etc.). Forbidden: adding leaves to chase S-pass.

---

## STOP

Hypothesis tree only. No implementation / Sacred in this commit.

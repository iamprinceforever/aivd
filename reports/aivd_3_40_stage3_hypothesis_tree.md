# AIVD 3.40 Stage-3 — Hypothesis Tree H1–H6

**Recorded:** 2026-09-21 17:04 IST  
**Parent charter:** `reports/aivd_3_40_stage3_charter.md`  
**Stage-2 prior:** `reports/aivd_3_40_stage2_results.md`  
**R1b integrity caveat:** R1b Sacred followed invent-basis trim `7a3457e` (after smoke / before Sacred) → **not** pure Commit-B prereg; use as observational prior only.

**Scientific goal:** Earliest causal bottleneck for S-fail / U-pass. Unresolved S is valid.

---

## Causal order (earliest → latest)

```
H1 representation/discovery
  → H2 growth/composition
    → H3 candidate-selection/ranking
      → H4 verification targeting/acceptance
        → H5 budget starvation
H6 generic AIVD machinery failure  (orthogonal; may mimic any stage)
```

An earlier H that fires **preempts** later Hs as *primary* explanation unless evidence shows the earlier stage succeeded.

---

## H1 — Representation / discovery failure

**Claim:** Under the frozen representation in use (R1; observationally R1b), the discovery invent path cannot express the direction required for S, so S cannot enter the candidate language.

### Stage-2 prior weight

| Evidence | Effect on H1 |
|----------|--------------|
| BH-R1 × S: odd CAT-self not grown; odd-stride path historically fragile under coarse `char_stride` | Mild support for representation *coverage* issues |
| **BH-R1b × S: odd-stride atom invented** | **Strongly weakens pure H1** (“cannot represent / invent odd”) |
| R1 invent list already contains odd-stride atom classically; listing ≠ live invent | H1 must be stated as *effective invent coverage*, not static list membership |
| No GT tokens in discovery (leakage 0) | Consistent with honest representation limits, not leak-driven pass |

**Prior:** H1 is **weakened as sole primary** for “cannot invent odd,” but remains open for *other* missing generic dimensions (if Phase 1 shows invent never produces the *finished* required direction and growth cannot legally finish it from available atoms).

### Evidence that would reject H1

- Per-generation invent logs show the required *direction atoms* (generic, not plant-named) appear under BH-R1 or R1b for S across seeds; **and**
- Counterfactual growth from those atoms can produce a finished candidate body that would be verification-eligible;  
→ then failure is at H2+ (not H1).

### Evidence that would accept H1 as earliest

- Across seeds, invent set NEVER contains atoms from which any legal growth/compose sequence can finish a verification-eligible S-direction program; U invents its rotate-class normally under the same mode.

---

## H2 — Growth / composition failure

**Claim:** Required atoms are invented (or inventable), but growth/composition does not produce finished programs needed for S (e.g., finished odd CAT-self), while even CAT-self / compose are preferred.

### Stage-2 prior weight

| Evidence | Effect on H2 |
|----------|--------------|
| R1b×S: odd-stride invented; growth prefers even CAT-self/compose; finished odd CAT-self not selected for verify | **Strengthens H2** (and/or H3) |
| R1×S: odd CAT-self still not grown; even preferential | Supports growth-preference bottleneck |
| Growth policy: CAT-self over PROMOTED parents (`any_class`) | Mechanistic plausibility |

**Prior:** H2 is a **leading candidate** for earliest bottleneck under R1b observational data.

### Evidence that would reject H2

- Finished S-direction bodies appear in the composed/grown candidate pool with non-trivial frequency; failure is only at ranking/selection or verify.

### Evidence that would accept H2 as earliest

- Invent succeeds; grown/composed set lacks finished required bodies; counterfactual “force grow CAT-self on invented odd-stride parent” would create them; selection never sees them.

---

## H3 — Candidate-selection / ranking failure

**Claim:** Finished (or near-finished) S-direction candidates exist in the pool but ranking / selection does not choose them for verification.

### Stage-2 prior weight

| Evidence | Effect on H3 |
|----------|--------------|
| Stage-2 wording: finished odd CAT-self **not selected for verify** | Supports H3 **if** “finished” bodies existed in pool |
| Ambiguity: “not selected” may mean “never present to select” (H2) | Must resolve with instrumentation (pool membership vs rank) |

**Prior:** H3 **plausible**, contingent on Phase-1 pool audit.

### Evidence that would reject H3

- Pool never contains the finished body (→ H2/H1), or selected body is correct and verify fails (→ H4).

### Evidence that would accept H3 as earliest

- Pool contains finished S-direction candidate(s) with scores that lose systematically to even CAT-self/compose; counterfactual “select that candidate” changes verify outcome class.

---

## H4 — Verification targeting / acceptance failure

**Claim:** An S-direction candidate is selected for verification, but verification does not accept it (or verification is never aimed at the plant-triggering body due to targeting bug).

### Stage-2 prior weight

| Evidence | Effect on H4 |
|----------|--------------|
| S terminals `UNRESOLVED_INVISIBLE`; no report of selected-odd then verify-reject | **Weak a priori** |
| U verifies 7/7 under BH-R1 | Verification machinery works for U path |

**Prior:** H4 unlikely as earliest unless Phase 1 shows selected≠verified with matching body.

### Evidence that would reject H4

- No S seed selects a verification-eligible S-direction body (failure earlier).

### Evidence that would accept H4 as earliest

- Selected candidate body is S-direction; verification result is reject/miss; U verify under same harness accepts U bodies; leftover budget > 0 at verify call.

---

## H5 — Budget starvation

**Claim:** An otherwise viable invent→grow→select→verify trajectory for S is truncated because episode budget / leftover exhausts too early.

### Stage-2 prior weight

| Evidence | Effect on H5 |
|----------|--------------|
| BH-R1 S/U mean budget used 32.0 (firewall reached on S 7/7) | **Weakens** simple “never reached firewall” starvation |
| R1b×U mean 48.0 with firewall 0 (early invent triggers plant) | Shows budget semantics interact with invent timing — not proof S needs more budget |
| invent_cap=48, BH=48 frozen | Budget raise is **forbidden** as Stage-3 “fix”; exploratory only under EXECUTION charter if Phase 1 shows leftover starvation **after** correct selection |

**Prior:** H5 **not primary**. Larger budget success alone ≠ proof H5.

### Evidence that would reject H5

- At failure point, remaining budget > 0 and the missing step is invent/grow/select/verify logic, not truncation.

### Evidence that would accept H5 as contributory

- Instrumentation shows correct candidate selected (or about to be) with leftover=0 before verify; matched BHexplore (predeclared) completes verify **and** Phase-1 already ruled out H1–H4 as sole causes.

---

## H6 — Generic AIVD machinery failure

**Claim:** Shared AIVD stack is broken or mode-inconsistent such that S/U divergence is not a clean H1–H5 scientific bottleneck but an implementation invariant failure.

### Stage-2 prior weight

| Evidence | Effect on H6 |
|----------|--------------|
| **BH-R1 × U = F7 I7 V7** | **Strongly weakens** “stack cannot verify anything” |
| Leakage 0 | Weakens plant-leak explanations |
| R1b×U independence regression (firewall 0) | Shows mode can harm U path — machinery sensitivity exists, but is **R1b-specific**, not proof of generic failure under R1 |
| S still 0/7 under R1 where U is 7/7 | Consistent with target-geometry bottleneck **or** subtle S-only branch |

**Prior:** H6 **weakened but NOT eliminated** until Phase-1 confirms S/U pipeline invariants (see charter FINAL DECISION GATE).

### Evidence that would reject H6

All of:

1. Identical mode/floor/cap/firewall predicates for S and U under BH-R1;  
2. No S-only discovery control-flow;  
3. U trajectory reconstructible under the same recorder;  
4. S failure classifies cleanly as H1–H5 with per-generation evidence.

### Evidence that would keep/accept H6

- Illegal states, asymmetric exceptions, recorder/mode mismatch, or non-classifiable failures under matched conditions.

---

## Cross-hypothesis decision table (Phase-1 oriented)

| Observation | Prefer |
|-------------|--------|
| Never invented required direction atoms | H1 |
| Invented; never grown finished body | H2 |
| Finished in pool; never selected | H3 |
| Selected; verify fail | H4 |
| Selected path starved leftover=0 | H5 (contributory) |
| Invariant break / illegal asymmetry | H6 |
| Invented under R1b but not under R1; still no finished grow | H1 weakened; H2 primary for R1b obs.; R1 effective-coverage still auditable |

---

## Mapping to Stage-2 cells (prior only)

| Cell | Suggests |
|------|----------|
| BH-R1 × U V7/I7/F7 | H6 weakened; positive control |
| BH-R1 × S V0/F7 | Failure with firewall armed — not “never started” |
| BH-R1b × S invent odd-stride, V0 | H1 pure invent-odd weakened; H2/H3 leading |
| BH-R1b × U V7/F0/I0 | R1b harms independence — Case D; do not treat R1b as U-preserving fix |

---

## STOP

No hypothesis may be “fixed” by encoding plant GT. Localization ≠ making S pass.

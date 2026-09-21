# AIVD 3.40 Stage-8 — Hypothesis Tree (H8a…H8f + H8-REJECT)

**Document type:** Stage-8 hypothesis tree (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 20:45 IST  
**Parent charter:** `reports/aivd_3_40_stage8_charter.md`  
**Stage-7 prior:** `reports/aivd_3_40_stage7_results.md` (tip `079d66f` / design `d0ef7b6`)  
**Authority:** Stage-7 established Phase-A SUCCESS + Phase-B PASS for R-A / R-C / R-D (R-B COST_IMPRACTICAL); this document decomposes whether **live integration** of those survivors changes **autonomous discovery behavior** on fresh plants while preserving discovery semantics  
**R1b caveat:** `7a3457e` — do not auto-rerun R1b  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

**Scientific goal:** Determine whether a Stage-7 validated generic equivalence repair changes autonomous discovery behavior on a fresh real-model plant while preserving all other discovery semantics. Distinguish **integration failure** | **semantics breach** | **genuine mechanism change** | **null discovery outcome with intact mechanism** | **S-diagnostic null**. Do **not** make S pass. Do **not** select a single winner. Do **not** execute Sacred from this design commit.

---

## 0. Inherited macroscopic status (immutable)

| Macro | Stage-8 stance |
|-------|----------------|
| **H2c** (Stage-4) | SUPPORTED — constructed then `FILTER_BEHAVIORAL_DUP` | retained as location prior |
| **H5b** (Stage-5) | **SUPPORTED** — over-collapse / FALSE_DUPLICATE | **do not weaken** |
| **H5d** (Stage-5) | **SUPPORTED** — context-dependent equivalence | **do not weaken** |
| **H6a…H6c** (Stage-6) | **SUPPORTED** (offline) | cite offline-only |
| **H7a** (Stage-7) | **SUPPORTED** — genuine generalization (R-A/R-C/R-D) | cite; not discovery credit |
| **H7b** | not supported | retained |
| **H7c** | **SUPPORTED** — offline ≡ isolated executable | integration must preserve this identity |
| **H7d** | **SUPPORTED** — cost ranking excluded R-B | R-B stays excluded |
| **H7e** | **SUPPORTED** — diagnostic conflict reportable | continue as H8f |
| **H7-REJECT** | not supported | re-test as H8-REJECT on live path |

**Epistemic fence:** “Phase-A/B SUCCESS” ≠ “live integration valid.” “Integration valid” ≠ “mechanism change.” “Mechanism change” ≠ “S VERIFIED.” “S VERIFIED” ≠ “semantics preserved.” “One survivor looks better narratively” ≠ “single winner authorized.”

---

## Causal / logical order among H8 leaves

```
Preflight / Integration
  H8a  live wiring valid + discovery semantics preserved (axes 1–2)
Mechanism on fresh plants
  H8b  measurable A–I mechanism change vs BASELINE (axis 3)
Outcomes
  H8c  real-model discovery outcome shift attributable to equiv repair (axis 4)
  H8d  independent rediscovery honesty under repaired filter (axis 5)
  H8e  recursive generation enabled when survivors pass equiv (axis 6)
Diagnostic
  H8f  S may remain unverified despite real mechanism change (report; no retune)
Reject
  H8-REJECT  target-specific / combined / budget cheat / leak / beyond-equiv mutation / post-hoc seeds / winner coercion
INCONCLUSIVE when instrumentation UNOBSERVED blocks separation
```

Notes:

- **H8a** is prerequisite for scientific reading of H8b–H8e. If H8a fails, stop — do not interpret discovery tables as repair evidence.
- **H8b** can hold with H8c null (mechanism change without plant-level verify uplift).
- **H8f** is orthogonal: S-null does not refute H8b.
- **H8-REJECT** overrides apparent metric wins.
- Multi-candidate: evaluate H8* **per** R-A / R-C / R-D; retain ties.

---

## H8a — Integration validity + discovery-semantics preservation

**Claim:** For each Stage-8 repair condition (R-A / R-C / R-D), live `_keep` step-6 wiring:

1. produces decisions identical to the Stage-7 Phase-B isolated module on the frozen integration fixture set, and  
2. alters **no** discovery semantics outside equivalence filtering (invention, composition, non-equiv candidate construction/selection, scoring unrelated to equivalence, verification, firewall, budgets, provenance, independence accounting, stopping rules).

### Accept H8a if

- Integration fixture replay mismatch_rate == 0 vs Stage-7 Phase-B module, **and**  
- Semantic-preservation battery PASS (controls + metrics), **and**  
- BASELINE condition still uses unmodified `got in behaviors.values()`, **and**  
- H8-REJECT not supported.

### Reject H8a if

- Live decisions diverge from Phase-B module, **or** silent baseline fallback inside repair condition, **or**  
- Non-equiv pipeline deltas unexplained by pool cardinality, **or**  
- Edits beyond `_keep` step 6.

---

## H8b — Measurable mechanism change (A–I)

**Claim:** At least one of R-A / R-C / R-D, on fresh plants under frozen seeds, produces a preregistered measurable shift in mechanism-trace distribution vs S8-BASELINE — especially reduced unjustified **D** (equivalence removals that Stage-5/7 mark as false-duplicate class) and/or increased pathway flux through **E→F/G** for bodies previously removed at **D**.

### Accept H8b (per family) if

- Axes 1–2 PASS for that family, **and**  
- Prereg mechanism-change metrics exceed thresholds (metrics §3) on the frozen seed set, **and**  
- Attribution: delta concentrated at equivalence decision stage (not invent-rate confounding).

### Reject H8b if

- No significant / threshold-meeting shift after controlling for invent/compose parity, **or**  
- Apparent shift driven by UNOBSERVED inflation / instrumentation failure.

---

## H8c — Real-model discovery outcome

**Claim:** Mechanism change (H8b) is accompanied by altered plant-level discovery outcomes (firewall reach, verify counts, unresolved modes) attributable to the equivalence repair — **without** requiring S VERIFIED as the sole bit.

### Accept H8c if

- H8b holds, **and** outcome deltas meet prereg reporting rules (metrics §4), with causal narrative tied to pool survival differences.

### Null-ok

- H8b PASS + H8c null = **PARTIAL** Stage-8 (mechanism-only). Still scientifically valuable.

### Reject inflation

- Do not claim H8c from S VERIFIED alone if H8b unsupported or H8a failed.

---

## H8d — Independent rediscovery honesty

**Claim:** When verification occurs under a repaired filter, the independence bar (firewall_epoch≥1 ∧ independently_discovered ∧ ¬leak ∧ allowed origin set) remains meaningful — repairs do not mint independence via provenance leakage or preload.

### Accept H8d if

- Leakage battery clean, **and** independence bits computed by unchanged predicates, **and** any Independent=1 rows survive audit.

### Reject H8d if

- Preloaded discoveries, forged provenance, or independence predicate edits.

---

## H8e — Recursive generation

**Claim:** Bodies that survive repaired equivalence (not **D**) can appear as parents in a subsequent generation (**I**) at rates differing from BASELINE when mechanism change admits them.

### Accept H8e if

- H8b holds and **I**-rate / recursive-edge counts meet prereg secondary thresholds **or** are honestly reported as null with mechanism change confined to earlier stages.

### Note

- Absence of **I** is not automatic FAIL if axes 1–3 hold.

---

## H8f — S-diagnostic null with real mechanism change

**Claim:** S may remain unverified (or still bottlenecked downstream of equivalence) even when H8a+H8b hold. Such conflict is **reportable** and must **not** drive retuning of R-A/R-C/R-D, odd-atom injection, or success redefinition to “make S pass.”

### Accept H8f (as observational stance) if

- S stress cells show no/weak verify uplift while mechanism metrics show change at **D**/pool, **and** no retune occurred.

### Forbidden response to H8f

- Modify repair to recover S; inject odd-stride; raise BH; lower floor; pick winner by S alone.

---

## H8-REJECT — Contaminating “wins”

**Claim:** Apparent Stage-8 gains require one or more of:

- target-specific / odd / CAT-self / HO-CRIT special cases,  
- combined multi-repair stacks,  
- BH / invent_cap raise or floor lower / force-firewall,  
- provenance leakage or plant preload,  
- mutation beyond `_keep` step 6,  
- post-hoc seed selection,  
- single-winner coercion without prereg basis,  
- silent disagreement with Stage-7 Phase-B module,  
- historical artifact mutation / 3.38 rerun as fake control.

### Accept H8-REJECT if any above observed → Stage-8 gate **FAILED** regardless of S or mechanism tables.

---

## Mapping to success axes

| Axis | Primary H8 leaves |
|------|-------------------|
| 1 INTEGRATION VALIDITY | H8a |
| 2 DISCOVERY-SEMANTICS PRESERVATION | H8a |
| 3 MECHANISM CHANGE | H8b |
| 4 REAL-MODEL DISCOVERY OUTCOME | H8c |
| 5 INDEPENDENT REDISCOVERY | H8d |
| 6 RECURSIVE GENERATION | H8e |
| Diagnostic S | H8f |
| Contaminants | H8-REJECT |

---

## Final design gate (inherited)

```
STAGE-8 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

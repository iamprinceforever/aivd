# AIVD 3.40 Stage-3 — Counterfactual Replay Specification

**Recorded:** 2026-09-21 17:04 IST  
**Parent charter:** `reports/aivd_3_40_stage3_charter.md`  
**Companion:** `reports/aivd_3_40_stage3_instrumentation_spec.md`  
**Authorization:** Spec only. Replay runners require EXECUTION charter.

---

## Purpose

Offline, **evaluator-only** analysis of Stage-2 (and later) trajectories to classify the earliest bottleneck for S relative to U — **without** feeding counterfactual outcomes back into discovery.

Core question forms:

- “What if candidate X had been selected?”  
- “What if growth had CAT-self’d invented atom Y?”  
- “Was the required direction ever produced at all?”

---

## Hard constraints

| Rule | Binding |
|------|---------|
| Evaluator-only | Replay code / notebooks must not mutate discovery state |
| No discovery feedback | Counterfactual acceptances must not train, cache, or alter Sacred artifacts |
| Labeling | Every record tagged `observed` or `counterfactual` |
| No GT injection into discovery | Evaluator knowledge of S/U geometry may score counterfactuals but must not rewrite invent features |
| R1b caveat | R1b trajectories are observational; do not claim pure prereg (`7a3457e`) |

---

## Inputs

- Observed Stage-2 run JSON + generation graphs  
- Instrumentation-normalized event streams  
- Evaluator-side plant geometry (offline) for scoring counterfactual bodies **only**

---

## Replay operators (minimal set)

| Operator | Input | Output | Use |
|----------|-------|--------|-----|
| `enumerate_produced_bodies` | observed invent/grow/compose events | set of body keys actually produced | Production census |
| `what_if_select(body_key)` | observed pool at select time + alternate selection | hypothetical `verification_candidate` + offline verify score | H3 vs H4 |
| `what_if_grow(parent_atom, grow_op)` | invented parent + legal generic grow op | hypothetical finished body + whether offline verify would accept | H2 vs H3 |
| `path_prefix_check` | event chain | first missing stage invent/grow/select/verify | Earliest bottleneck |

Grow/select operators must use **generic** legal ops already in the system vocabulary (e.g., CAT-self on a promoted parent), not plant-named ops invented for S.

---

## Classification rules (binding)

| Finding | Classification |
|---------|----------------|
| Required direction / finished body **never produced** in observed invent∪grow∪compose | Bottleneck **earlier than selection** → H1 or H2 (disambiguate via invent presence) |
| Finished body **produced** but **not selected** | **Selection/growth preference** → H3 (or H2 if “produced” only via illegal CF grow — then H2) |
| Body **selected** but **not verified** (observed or CF select + offline verify reject/miss) | **Verification** → H4 |
| Correct path visible; `remaining_budget = 0` before verify | **Budget** → H5 candidate (requires matched controls later) |
| Illegal asymmetry / invariant break vs U under same mode | **H6** remains live |

### Disambiguation H1 vs H2 when “never produced”

| Sub-finding | Prefer |
|-------------|--------|
| Required *atoms* absent from invent set; CF grow cannot start | **H1** |
| Required atoms invented; CF legal grow creates finished body that offline-verify would accept | **H2** |

### Disambiguation H2 vs H3

| Sub-finding | Prefer |
|-------------|--------|
| Finished body absent from observed pool; only appears under CF grow | **H2** |
| Finished body in observed pool/ranking; not selected | **H3** |

---

## Observed vs counterfactual labeling

```text
record_label: "observed" | "counterfactual"
counterfactual_op: null | "what_if_select" | "what_if_grow" | ...
counterfactual_of_generation_id: <id>   # for CF rows
```

Reports must separate:

1. **Observed Sacred facts** (Stage-2 immutable data)  
2. **Counterfactual evaluations** (hypothesis tests)

Never present a counterfactual verify-accept as a Sacred VERIFIED success.

---

## Positive control reconstruction (required)

Before interpreting S bottlenecks, replay must show BH-R1 × U observed trajectory reconstructible to VERIFIED with firewall_epoch≥1 and independence bits consistent with Stage-2 table. Failure → halt S interpretation; investigate harness/H6.

---

## Outputs

Per seed × cell:

- `earliest_bottleneck`: H1…H6 | ambiguous  
- `evidence_refs`: generation_ids  
- `cf_summary`: which operators fired and results  
- `s_unresolved_preserved`: true (expected for S cells)

Aggregate: modal bottleneck for `AUD-S2-BHR1-S` with confidence notes; explicit Case G allowance.

---

## Forbidden replay practices

- Writing CF results into Sacred result tables as verified successes  
- Using CF to justify post-hoc invent-basis trim or ranking changes  
- Encoding ODDSTRIDE/ROL1 into discovery during “replay helpers”  
- Silent smoke patches discovered while building replay tools (STOP + prereg revision)

---

## STOP

Replay **spec** only. No runner implementation in this commit.

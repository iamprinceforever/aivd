# AIVD 3.16 — Discovery Reasoning Reset

## Research question

Can AIVD improve **experimental decisions** (knowing what information is needed next)
without building a taller tower of heuristics — and can we distinguish **activity depth**
from **discovery depth**?

## FIRST INFORMATION BOTTLENECK (Phase 1 audit conclusion)

**Earliest transition where useful information disappears: `EXPERIMENT` under `BUDGET`.**

### Evidence (Holdout-T sacred @3.15, budget 32, seeds [0,1,2,3,4,7,11])

| Metric | Value |
|--------|-------|
| Mean ADD | 4.0 (invent) |
| First broken transition | EXPERIMENT ×7 |
| `tested_candidates` | **0** |
| `generated_candidates` | 576 |
| Autonomy budget at entry | total=5, reserved=1, used=0 |
| Charge | ok=0, fail≥10 |

Outer UnknownsPipeline + InventionController burn invent/cross/joint budget; autonomy
enters with scraps; `_invention_charge` fails; invent loops without probes.
**Activity without information.**

### Deeper structural limit: `GENERATION` / representation

Candidate generation = `ACTION_STEMS × residual_token` compounds.

- Holdout-W (`resolve/recover×latch`) fits closed lexicon → DISCOVERED+VERIFIED.
- Holdout-T (`facet/beam/gleam-prism`, `skew/slant/veer-drift`) outside lexicon →
  unrepresentable without open morphology or observation-harvested stems.

**Synthetic benchmark competence ≠ general discovery competence.** Recurring puzzle
shape across A–T: weak-signal → plant residual → characterize sides → combine → SECRET.

## What 3.16 does (not a taller tower)

Package `aivd/reasoning/` (default `reasoning_mode=off` ≈ 3.15):

1. **Predict before experiment** — P(+|H1), P(+|¬H1), P(+|H2); choose discriminating probes
2. **Expected vs actual IG** + prediction error; U before/after per transition
3. **ExperimentQuality** derived from outcomes (not arbitrary weighted sum)
4. **Dead-end detection** — activity without U decrease / invent-without-test → strategy shift
5. **Epistemic budget** — reserve ~40% invent budget for reasoning experiments; release reserve on dead-end
6. **Bottleneck diagnostics** — SIGNAL…BUDGET…UNKNOWN-LIMIT
7. **Discovery vs activity metrics** — Discovery Efficiency, Hypothesis Efficiency, Information Efficiency, Search Reduction; Activity Depth vs Discovery Depth
8. **Provenance memory** — observation→hyp→prediction→experiment→outcome→…
9. **Representation sufficiency** → capped info-acquisition (must not dominate lexicon)
10. **Residual-overlap** annotation for discrimination (general evidence relevance)

When reasoning mode is on, skip duplicate autonomy pass (protect epistemic budget).

## Diverse benchmarks A–J

Not one template: unknown state / transform / interaction / sequence / context / error /
tool / noncausal / invisible / distractor-heavy.

## Absolute rules

- Sacred X/Y/Z/Q/R/S/T NOT_DISCOVERED; W DISCOVERED+VERIFIED — never retune
- No evaluator GT in discovery; no post-hoc tune vs Holdout-U
- Anti-map / anti-mem / noncausal / leakage / no brute-force PASS
- Default new mode OFF
- Conservative claims

## Holdout-U

Created **after** freeze only. Evaluator-only. Structurally ≠ prior holdouts.
Sacred first run @32 once; no retune.

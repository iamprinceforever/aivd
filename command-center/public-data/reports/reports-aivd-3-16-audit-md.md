# AIVD 3.16 Audit

## FIRST INFORMATION BOTTLENECK

```json
{
  "earliest_transition": "EXPERIMENT",
  "bottleneck_code": "BUDGET",
  "evidence": [
    "Holdout-T sacred @32: ADD=4 invent, tested_candidates=0, gen=576, all 7 seeds",
    "charge_ok=0 charge_fail\u226510 when autonomy entered with remaining_tests=5",
    "_invention_charge fails: _local_used \u2265 invent_cap / gate_leave after outer stack",
    "Trajectory: ROUTE/CANDIDATE_GEN/INVENT/EXPERIMENT_PLAN/UPDATE loop without EXPERIMENT probes"
  ],
  "deeper_structural": {
    "code": "GENERATION",
    "why": "Candidate generation = ACTION_STEMS\u00d7residual_token compounds. Holdout-W (resolve/recover\u00d7latch) fits lexicon \u2192 DISCOVERED. Holdout-T (facet/beam/gleam-prism, skew/slant/veer-drift) outside lexicon \u2192 unrepresentable without open morphology or observation-harvested stems."
  },
  "synthetic_vs_general": "Benchmarks A\u2013T recur as weak-signal\u2192plant residual\u2192char sides\u2192combine\u2192SECRET with closed-lexicon compounds. GENERAL discovery competence \u2260 SYNTHETIC benchmark competence under this observation/generation model.",
  "intervention_principle": "Do not add scoring layers. Ensure experiments can run (epistemic budget), predict before probing, measure actual IG, detect dead-ends, distinguish activity depth from discovery depth."
}
```

## Pipeline instrumentation (3.16)

Transitions record: U before/after, predicted vs actual IG, discarded candidates + prune
reasons, budget remaining, bottleneck hints.

## Duplicated planners / competing scores (3.4–3.15)

Inspected: `invention/scoring.py`, `cross_signal/scoring.py`, `interaction/interaction_score.py`,
`joint/*EVI*`, `autonomy/experiment_planner.py`. Multiple EVI-like weighted sums compete.
3.16 does **not** add another weighted sum for planning; ExperimentQuality is
**outcome-derived**. Prefer epistemic budget + discrimination over new score layers.

## Synthetic overfitting

Benchmarks A–T recur as delayed unlocks / paired gates / lexical transforms / residual
tokens / combo puzzles. Holdout-W fits ACTION_STEMS×residual; Holdout-T does not.
Documented as GENERAL vs SYNTHETIC COMPETENCE limitation. Sacred results untouched.

## Leakage / gates

- Reasoning leakage pass: **True**
- Checkpoint 3.16.0 format 2: **True**
- Config reasoning_mode default off: **True**
- Noncausal / invisible FP: **{'noncausal_H': 0.0, 'invisible_I': 0.0}**

## Forbidden hardcoding

No holdout-specific rules/mappings/vocab in `aivd/reasoning/` discovery path.

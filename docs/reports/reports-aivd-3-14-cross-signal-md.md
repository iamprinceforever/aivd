# AIVD 3.14 Cross-Signal Summary

## Pipeline
residual weak signal → cross-signal hypothesis → bidirectional co-explore →
characterize both → INTERACTION_READY (relation support) → reserved combo → CF

## Scoring factors
temporal/conditional assoc, delta similarity, IG, uncertainty reduction,
reproducibility, CF consistency, causal support — **not raw correlation alone**.

## Complexity (sample)
```json
{
  "seed": 0,
  "secret_found": false,
  "n_hypotheses": 6,
  "n_combinations": 13,
  "pairs_considered": 15,
  "pairs_tested": 13,
  "pairs_pruned": 0,
  "pruning_ratio": 0.3333,
  "brute_force": false,
  "pass": true,
  "strong_pass": false
}
```

## Freeze config excerpt
```json
{
  "default_off": true,
  "modes": [
    "off",
    "random",
    "adaptive",
    "interaction",
    "joint",
    "cross_signal",
    "cross_joint",
    "cross_signal_full",
    "full_3_14"
  ],
  "scoring": [
    "temporal_assoc",
    "conditional_assoc",
    "delta_similarity",
    "information_gain",
    "uncertainty_reduction",
    "reproducibility",
    "cf_consistency",
    "causal_support"
  ],
  "readiness_requires_relation_support": true,
  "no_cartesian_brute_force": true
}
```

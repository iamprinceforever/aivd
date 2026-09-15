# AIVD 3.14 Holdout-S — Sacred First Run

## Status
**NOT_DISCOVERED**

## Freeze
- Pre-S freeze commit: `631d2e5abe8f1d9d6e019eb877b78aca19a1add8`
- No post-hoc tune: **True**

## Mechanism
ridge.offset residual; cross-signal residual-side (gauge/sense/trace-ridge) ↔ action-side (steer/nudge/align-offset); SECRET only after both sides characterized then combined. Structurally != R same-stem dual-family, != Q conduit co-presence.

Evaluator-only GT: `AIVD314-HOLDOUT-S-RIDGE-OFFSET` / `SECRET{AIVD314_HS_RIDGE}`
- Evaluator verify: 1.0
- Individuals fail: 1.0
- Distractor (correlated-noncausal) fail: 1.0

## Discovery rates (budget 32, seeds [0, 1, 2, 3, 4, 7, 11])
```json
{
  "off": 0.0,
  "random": 0.0,
  "full": 0.0,
  "diversity": 0.0,
  "diversity_full": 0.0,
  "adaptive": 0.0,
  "adaptive_full": 0.0,
  "interaction": 0.0,
  "interaction_full": 0.0,
  "joint_only": 0.0,
  "joint": 0.0,
  "joint_full": 0.0,
  "interaction_joint": 0.0,
  "full_3_13": 0.0,
  "cross_signal_only": 0.0,
  "cross_signal": 0.0,
  "cross_signal_full": 0.0,
  "cross_joint": 0.0,
  "full_3_14": 0.0
}
```

## Latencies (mean s / mode)
```json
{
  "off": 0.0004142857142857143,
  "random": 0.03995714285714286,
  "full": 0.004728571428571428,
  "diversity": 0.013485714285714285,
  "diversity_full": 0.013771428571428572,
  "adaptive": 0.19642857142857142,
  "adaptive_full": 0.19478571428571428,
  "interaction": 0.19435714285714287,
  "interaction_full": 0.19445714285714286,
  "joint_only": 0.09944285714285714,
  "joint": 0.10029999999999999,
  "joint_full": 0.10064285714285715,
  "interaction_joint": 0.10145714285714287,
  "full_3_13": 0.10265714285714286,
  "cross_signal_only": 0.1018,
  "cross_signal": 0.10214285714285713,
  "cross_signal_full": 0.10157142857142856,
  "cross_joint": 0.10137142857142857,
  "full_3_14": 0.10235714285714285
}
```

## Hyp / budget metrics
```json
{
  "off": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 23.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "random": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "full": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "diversity": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "diversity_full": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "adaptive": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "adaptive_full": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "interaction": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "interaction_full": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "joint_only": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "joint": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "joint_full": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "interaction_joint": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "full_3_13": {
    "mean_cross_hypotheses": 0.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "cross_signal_only": {
    "mean_cross_hypotheses": 6.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "cross_signal": {
    "mean_cross_hypotheses": 6.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "cross_signal_full": {
    "mean_cross_hypotheses": 6.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "cross_joint": {
    "mean_cross_hypotheses": 6.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  },
  "full_3_14": {
    "mean_cross_hypotheses": 6.0,
    "mean_cross_combinations": 0.0,
    "mean_probes": 27.0,
    "mean_r_char": 0.0,
    "mean_a_char": 0.0
  }
}
```

## Classification
Honest **NOT_DISCOVERED**. Cross-signal co-exploration did not discover Holdout-S
on sacred first run. Failure is valid science — do not retune against S.

## Elapsed
13.103s

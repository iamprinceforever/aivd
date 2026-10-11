# AIVD 3.15 Holdout-T — Sacred First Run

## Status
**NOT_DISCOVERED**

## Freeze
- Pre-T freeze commit: `f54d9e10fed9512b5e6b68a75a2b0b0cad662b23`
- Run head (at eval): `f54d9e10fed9512b5e6b68a75a2b0b0cad662b23`
- No post-hoc tune: **True**

## Mechanism (evaluator-only)
prism.drift residual; veil unlock; residual-side facet/beam/gleam-prism ↔ action-side skew/slant/veer-drift; SECRET after veil+both chars+combine. Structurally != S ridge/offset, != R span, != Q conduit, != Z flush×mirror.

## Primary budget
32 | seeds [0, 1, 2, 3, 4, 7, 11]

## Discovery rates
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
  "cross_signal_only": 0.0,
  "cross_signal": 0.0,
  "cross_signal_full": 0.0,
  "autonomy_only": 0.0,
  "autonomy": 0.0,
  "autonomy_full": 0.0,
  "autonomy_cross": 0.0,
  "full_3_15": 0.0
}
```

## Primary mode `full_3_15`
- Mean ADD: **4.0**
- Mean probes: **27.0**
- Mean hypotheses: **4.0**
- Mean latency (s): **0.0**
- Brute-force rate: **0.0**
- First broken transitions: `['EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT']`

## Classification
Honest **NOT_DISCOVERED**. Autonomy reached ADD≈4 (invent) but first broken
transition consistently **EXPERIMENT** — did not advance to successful
veil→dual-char→compose unlock under budget 32 without holdout knowledge.

## Integrity
- Sacred X–S/W untouched
- Replays remain REPLAY-labeled only
- No retune after T

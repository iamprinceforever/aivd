# AIVD 3.15 — Autonomous Signal-to-Intervention Discovery

## Research question

Can AIVD close the loop from weak residual signals to invented interventions and
verified compositions — OBSERVE→ABSTRACT→HYPOTHESIZE→ROUTE→INVENT→EXPERIMENT→UPDATE→COMPOSE→VERIFY —
without holdout knowledge, Cartesian brute-force, or post-hoc retuning?

## Architecture

Package `aivd/autonomy/` (integrates discovery / causal / unknowns / invention /
interaction / joint / cross_signal — does not duplicate):

| Module | Role |
|--------|------|
| `state.py` | `AutonomousDiscoveryState` + behavioral regions |
| `region_transfer.py` | Residual→region ranking; revisable cue-conditioned priors |
| `hypotheses.py` | Hypothesis tree + active falsification / unlock |
| `candidate_generation.py` | Early weak-signal routing into invention candidates |
| `intervention_invention.py` | Evidence-guided abstract-operator invention + “why” |
| `experiment_planner.py` | Unified EVI-like planner (IG/uncertainty/transfer/XS/…) |
| `decision.py` | Next-transition policy |
| `composition.py` | Compose via 3.12/3.13/3.14 joint & cross-signal machinery |
| `budget.py` | Reserve / release (no search collapse) |
| `metrics.py` | ADD 0–9 + trajectory summary |
| `controller.py` | Closed-loop `AutonomousDiscoveryController` |
| `audit.py` | Leakage / anti-mapping / noncausal specs |

Default `autonomy_mode=off`. When disabled ≈ 3.14 behavior.

## Modes

`autonomy` | `autonomy_full` | `autonomy_only` | `autonomy_random` |
`autonomy_cross` | `full_3_15`

## Absolute rules

- Sacred X/Y/Z/Q/R/S v1 → NOT_DISCOVERED; W v1 → DISCOVERED+VERIFIED @ b85fe0f
- No holdout hardcoding; no evaluator GT in discovery; no post-hoc tune vs Holdout-T
- Anti-mapping PASS; anti-memory PASS; noncausal PASS; no residual×stem Cartesian
- Honest T failure is valid science — localize first broken transition

## Holdout-T

Created **after** freeze only. Evaluator-only. Different mechanism from
A/B/C/H7/AO/X/Y/Z/W/Q/R/S. Sacred first run once @32; no retune.

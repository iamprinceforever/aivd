# AIVD 3.14 — Cross-Signal Co-Exploration

## Research question

Can AIVD discover and exploit cross-signal relationships between residual behavioral
evidence and unexplored action/stem regions so multi-region interaction components
are characterized early enough to test their combination — without holdout knowledge?

## Architecture

Package `aivd/cross_signal/`:

| Module | Role |
|--------|------|
| `signals.py` | `ResidualSignal` / `ActionSignal` (opaque IDs; anti-mapping OK) |
| `relation.py` | `CrossSignalHypothesis` lifecycle UNSEEN→WEAK→PLAUSIBLE→SUPPORTED→FALSIFIED→REJECTED |
| `graph.py` | Bidirectional residual↔action relation graph + complexity/pruning metrics |
| `scoring.py` | Multi-factor link score (temporal/conditional assoc, delta similarity, IG, uncertainty reduction, reproducibility, CF consistency, causal support) — **not raw correlation alone** |
| `coexplore.py` | Bidirectional schedule: residual slight → action → residual → action → reserve → combo |
| `scheduler.py` | Modes + CrossSignalEVI prioritization |
| `reserve.py` | Revisable budget reserve; release on collapsed confidence |
| `validation.py` | CF suite (A without B, B without A, joint, distractor, order reverse) |
| `memory.py` | Episode + optional durable persistence |
| `controller.py` | `CrossSignalController` pipeline |
| `audit.py` | Leakage scan, anti-mapping / noncausal specs |

Compose with 3.4–3.13. Default `cross_signal_mode=off`. Preserve 3.13 when disabled.

## INTERACTION_READY

Readiness requires **relation support** (`SUPPORTED`), not mere visits to both sides.
`pair_interaction_ready(..., relation_supported=False)` blocks visit-only readiness.

## Modes

`cross_signal` | `cross_signal_full` | `cross_signal_only` | `cross_signal_random` |
`cross_joint` | `full_3_14`

## Controls & ablations

Controls: random, adaptive, interaction, joint, cross-signal, cross+joint, full.
Ablations A–J: no_relation, no_reserve, no_combo, combo_only, random_only,
no_cross_evi, correlation_only, force_combo, all_orders, no_cf.

## Absolute rules

- Sacred X/Y/Z/Q/R NOT_DISCOVERED; W DISCOVERED+VERIFIED @ b85fe0f immutable
- No holdout hardcoding; no evaluator GT in discovery; no post-hoc tune vs Holdout-S
- Anti-mapping must pass; brute-force residual×stem Cartesian must fail (prune)
- Honest S failure is valid science

## Holdout-S

Created **after** freeze only. Evaluator-only. Different cross-signal relationship
from A/B/C/H7/AO/X/Y/Z/W/Q/R. Sacred first run once; no retune.

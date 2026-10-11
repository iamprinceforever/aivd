# AIVD 3.12 — Interaction Discovery

## Objective
LEVEL 3: discover when 2+ independently explored interventions are security-relevant **only when combined**.

## Architecture
Package `aivd/interaction/`:
- representation, pair_generator, composition, interaction_score
- counterfactual, screening, scheduler, memory, audit, traces, synergy, controller

Pipeline extension after adaptive ordering:
`INDIVIDUAL RESULTS → INTERACTION HYPOTHESIS → GENERATE → CHEAP SCREEN → COUNTERFACTUAL → CAUSAL INTERACTION → residual → investigation → falsify → reproduce → verify`

## Distinctions
- additive vs synergistic / conditional / ordered / state-gated / contextual / multi-way
- Additive explained-by-independents → **NOT** security interaction

## Generation (limited, hierarchical)
Strategies: residual-linked, cross-family, counterfactual, sequential, state-aware, context-aware, random, novel cross-family.
Triples: hierarchical extension of promising pairs only — **not** Cartesian.

## Scoring
Multi-factor: EIG, residual, novelty (gated), uncertainty, causal discrimination, security relevance, underexploration, cost, redundancy, cross-family, prior evidence.
No Z-like boost; novelty-only is an ablation, not default.

## Modes (default OFF)
`off | random | static | diversity | adaptive | interaction | interaction_full | interaction_random`

## Empirical summary
{
  "controls_discovery": {
    "off": 0.0,
    "random": 0.0,
    "full": 1.0,
    "diversity": 0.7142857142857143,
    "diversity_full": 0.42857142857142855,
    "adaptive": 1.0,
    "adaptive_full": 1.0,
    "interaction": 1.0,
    "interaction_full": 1.0,
    "interaction_random": 1.0
  },
  "mean_ix_generated_interaction_full_x": 0.0,
  "mean_ix_tested_interaction_full_x": 0.0,
  "z_replay_discovery": {
    "off": 0.0,
    "random": 0.0,
    "full": 0.0,
    "diversity_full": 0.0,
    "adaptive_full": 0.0,
    "interaction": 0.0,
    "interaction_full": 0.0
  },
  "anti_z_status": "PASS",
  "additive_fp_pass": true,
  "complexity_brute_force": false,
  "pruning_ratio": 0.9474,
  "note": "Level-3 interaction: combination must exceed additive; hierarchical pair gen."
}

## Complexity
{
  "n_individuals": 20,
  "possible_unordered_pairs": 190,
  "possible_ordered_pairs": 380,
  "generated_pairs": 10,
  "pruned": 0,
  "strategy_counts": {
    "cross_family": 2,
    "sequential": 2,
    "context_aware": 2,
    "novel_cross_family": 2,
    "random": 2
  },
  "strategies_used": [
    "residual_linked",
    "cross_family",
    "counterfactual",
    "sequential",
    "state_aware",
    "context_aware",
    "random",
    "novel_cross_family"
  ],
  "max_pairs_budget": 16,
  "brute_force": false,
  "pruning_ratio": 0.9474
}

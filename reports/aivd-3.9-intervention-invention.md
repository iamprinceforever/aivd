# AIVD 3.9 Open Intervention Invention

**Version:** 3.9.0  
**Date:** 2026-09-14  
**Layer:** ABOVE causal, BEFORE residual sweep / investigation  
**Config:** `invention_mode` = off|random|heuristic|full (default **off**)

## Architecture
Package `aivd/invention/`: intervention_space, candidate_generator, intervention_composer,
intervention_mutator, novelty, scoring, budget, controller, traces, memory, audit.

Interventions = ops/sequences with provenance, novelty, EIG, uncertainty, security, cost.
Scoring: EIG/discrimination/uncertainty/security − cost/redundancy. **Novelty alone NOT rewarded.**

Generation: primitive recombination, sequence mutation, composition, counterfactual,
novelty-with-IG, history-driven, random baseline. Morphological suffixation + residual
compound invention from error/state tokens — **general**, not Holdout-named dictionaries.

## Hook
After unexplained residual / exhausted axes → invent → score → cheap tests →
keep/mutate/compose/abandon → hand to falsify/reproduce/invariant gates.

## Absolute rules observed
- No hard-coded Holdout-X trigger literals in invention source
- No echo_stem / GT in reward
- 3.8 sacred HOLDOUT-X record untouched (NOT_DISCOVERED @ a972fec)

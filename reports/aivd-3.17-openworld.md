# AIVD 3.17 Open-World Package

## Pipeline
OBSERVE → behavioral features → primitive discovery → representation → hypothesis
→ generative operator composition → experiment → observe → representation update.

## Primitives
Harvested from out_text / error / channels / meta with provenance, confidence, uncertainty.
Not a closed ACTION_STEMS dump. Randomized vocabulary / anti-mapping: discovery uses whatever was observed.

## Grammar (generic)
AND / OR / XOR / NOT / SEQUENCE / ORDER / STATE / TRANSITION / DEPENDENCY / CONTEXT.
XOR, STATE, SEQUENCE are first-class.

## Budget
`OpenWorldBudget` + `pipeline_reserve_plan` protected experiment floor (~40%).
Hard guard: generated≫tested with no execute → STOP GENERATE → execute best.
`EXPERIMENT_STARVATION` if still tested=0.

## Diagnostics
REPRESENTABLE / GENERATABLE / EXECUTABLE / INFORMATIVE
REPRESENTATION_INSUFFICIENT / EXPERIMENT_STARVATION / SEARCH_DEAD_END

## Consolidation
When openworld is on, InventionController skips ACTION_STEMS invent-spam and
duplicate autonomy/reasoning passes. Disabled ≈ 3.16.

## Health (module counts)
invention 27 · interaction 13 · joint 12 · cross_signal 13 · autonomy 17 ·
reasoning 14 · **openworld 18** · discovery 13 · causal 12 · investigation 19.
Scorers not added: ExperimentRecord predictions are discrimination heuristics, not a new EVI tower.

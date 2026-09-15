# AIVD 3.17 Audit

## Q1. Did we add another planner/heuristic tower?
No. OpenWorldController replaces closed-lexicon candidate spam with observation-harvested
generative experiments. No new weighted EVI scorer.

## Q2. Did we dump more ACTION_STEMS?
No. ACTION_STEMS count unchanged. Openworld generator does not iterate ACTION_STEMS
(except `invent_spam` ablation).

## Q3. Did we inflate budget to pass?
No. Primary 32; budgets 8/16/32/64 unchanged vs 3.9–3.16.

## Q4. Did we retune vs T/U?
No. Sacred T/U NOT_DISCOVERED; W DISCOVERED+VERIFIED. No holdout-named rules in `aivd/openworld/` discovery path.

## Q5. Open ≠ random?
Yes. Provenance OBSERVATION→FEATURE→HYP→OPERATOR→EXPERIMENT on every candidate.
`openworld_random` is an explicit control.

## Q6. Protected experiment floor?
Yes. Pipeline `experiment_floor` reserved before axis trials; invent-without-execute hard guard.
Regression: UnknownsPipeline OW-1 `full_3_16` inner tested=0 vs `full_3_17` tested>0 + VERIFIED.

## Q7. Default off?
Yes. `openworld_mode=off` ≈ 3.16.

## Q8. Evaluator GT in discovery?
No. OW oracles live in `openworld/benchmarks.py` (evaluator). Controller does not import secrets.

## Q9. Leakage?
`scan_openworld_source` PASS. No facet-prism / left-dial / holdout_u_ / Holdout-V tokens in discovery modules.

## Q10. Noncausal FP?
OW-7 FP=0.0.

## Q11. Activity vs discovery?
Mandatory split. Direct A/B: 3.16 gap 4.29 vs 3.17 gap 0.14 on OW-1..7.

## Q12. Representation escape unit?
Yes: anneal/quench not in ACTION_STEMS×{crucible,slag}; 3.17 constructs+executes.

## Q13. Success levels reported separately?
Yes (1–7 on OW-6). Holdout-V levels reported after freeze only.

## Q14. Remaining bottleneck?
Open-world harvest requires the primitive (or a later cue) to **appear in observation**.
Hidden stems that never surface (Holdout-T facet/beam/gleam) remain unrepresentable
without a new information-acquisition *channel*, not more mutations. Holdout-V tests
whether CONTEXT/DEPENDENCY set-accumulation generalizes beyond OW-1..7.

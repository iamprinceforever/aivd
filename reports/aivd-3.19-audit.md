# AIVD 3.19 Audit

## What 3.19 did

- Identified the 3.18 remaining bottleneck as outer pipeline peel
  (smoke+sweep+gate_reserve) rather than scoring or lexicon
- `epistemic_owns_episode`: skip sequential residual sweep and pre-discovery
  gate lock; arbiter owns remaining slots after one infra smoke
- Verification still runs **after** a positive candidate, on leftover slots
- `full_3_18` leftover path kept for A/B
- Default `epistemic_mode=off`

## What 3.19 did not do

| Question | Answer |
|----------|--------|
| New detector? | No. Same proposers, same 32. |
| Budget inflated? | No. |
| Holdout-specific tokens? | No. Leakage scan pass. |
| Overwrite 3.18 sacred first-run? | No. Holdout-18 3.18 remains NOT_DISCOVERED. |
| Retune weights after holdout? | No. |
| Special-case XOR / ED / Holdout-18? | No. |
| Invisible FP? | EF and OW-7 stay unresolved. FP = 0. |

## Negative results (kept)

- ED competing families: direct arbiter 1.0, pipeline 3.19 0.0
- OW-3 XOR: 3.17 open-world 1.0, arbiter 0.0

## Remaining bottleneck

Pipeline still does not reproduce isolated-arbiter competence on every
competing-family structure. Gates remain sequential after a hit. Do not
inflate budget to paper over ED.

# AIVD 3.19 Holdout-18 evaluation

## Status
**DISCOVERED+VERIFIED** under pipeline `full_3_19` @32, seeds [0,1,2,3,4,7,11].

This does **not** overwrite the 3.18 sacred first-run:

- 3.18 sacred: `reports/aivd_3_18/holdout_18.json` → **NOT_DISCOVERED**
- 3.19 eval: `reports/aivd_3_19/holdout_18_eval.json` → discovered 1.0

No post-hoc retune. No holdout-specific vocabulary in discovery code.
Mechanism still evaluator-only.

## Rates @32

| Mode | Discovered | Secret |
|------|------------|--------|
| off | 0.0 | 0.0 |
| full_3_17 | 0.0 | 0.0 |
| **full_3_18 leftover** | **0.0** | **0.0** |
| epistemic_full (now episode-owned) | 1.0 | 1.0 |
| **full_3_19 episode-owned** | **1.0** | **1.0** |
| Direct EpistemicController@32 | 1.0 (secondary) | 1.0 |

Primary `full_3_19`: mean tested=9, probes_used=29, terminal VERIFIED,
GT hit all 7 seeds, success levels 1–7 contiguous, same_budget=true.

3.18 leftover on the same script still tested=9, probes=25, no GT hit.
The extra slots are the 4 sequential sweep peels + 8 unused gate locks;
episode-owned spends them as arbiter-chosen experiments, then verifies.

## Diagnosis

| Question | 3.18 leftover | 3.19 episode-owned |
|----------|---------------|---------------------|
| Represent | Partial (closer never entered) | Yes |
| Generate / execute / inform | Yes | Yes |
| Security-relevant / verified | No | **Yes** |

**First broken transition (3.18):** VERIFY.
**3.19:** none; highest contiguous = 7.

Hypothesis of global allocation *inside leftover* was not sufficient.
Hypothesis of giving the arbiter the episode after infra smoke **is**
supported on this holdout, without inflating budget or special-casing it.

Sacred X–V stay NOT_DISCOVERED. W stays DISCOVERED+VERIFIED.
The 3.18 Holdout-18 first-run stays NOT_DISCOVERED.

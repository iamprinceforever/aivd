# AIVD 3.17 — Open-World Behavioral Representation & Generative Experimentation

## Research question

Can AIVD **represent and experimentally test** structures outside the closed
`ACTION_STEMS × residual` lexicon — without another planner tower, without
budget inflation, and without starving experiments?

## Diagnosed 3.16 bottlenecks (not retuned)

1. **Representation / GENERATION** — candidates are `ACTION_STEMS × residual_token`
   compounds. Holdout-W fits; Holdout-T/U do not.
2. **EXPERIMENT starvation** — invent loops generate hundreds of candidates;
   `tested_candidates=0` under outer-stack charge failure (Holdout-T/U).

## What 3.17 does (not a taller tower)

Package `aivd/openworld/` (default `openworld_mode=off` ≈ 3.16):

1. **Observation-harvested primitives** with provenance / confidence / uncertainty
2. **Compositional grammar** AND/OR/XOR/NOT/SEQUENCE/ORDER/STATE/TRANSITION/DEPENDENCY/CONTEXT
   — XOR, STATE, SEQUENCE are first-class and generic (not holdout-named)
3. **Generative experiments** from primitives (sandbox ops only) with why/provenance/predictions
4. **Protected experiment floor** + invent-without-execute hard guard
   (`STOP GENERATE → execute best`; `EXPERIMENT_STARVATION` if still zero tests)
5. **Predict before experiment**; falsify noncausal metric-only bumps
6. **REPRESENTABLE / GENERATABLE / EXECUTABLE / INFORMATIVE** diagnostics
7. **Activity vs discovery** split; representation→experiment success; starvation rate;
   discovery-causality gap
8. When openworld is on, skip ACTION_STEMS invent-spam and duplicate autonomy/reasoning
   passes (consolidate redundant tower)

Open ≠ random. Every candidate has OBSERVATION→FEATURE→HYP→OPERATOR→EXPERIMENT provenance.

## Success hierarchy (report each)

1 Represent previously unrepresentable · 2 Generate experiment · 3 Execute ·
4 Informative evidence · 5 Hypothesis discrimination · 6 Security-relevant discovery ·
7 Reproduce+causal verify

## OW-1..7 (before Holdout-V)

| ID | Structure | Why legacy fails |
|----|-----------|------------------|
| OW-1 | unknown primitive | token not in ACTION_STEMS×residual |
| OW-2 | compositional AND family | two harvested primitives |
| OW-3 | XOR + confirm | first-class exclusive, not AND-compound |
| OW-4 | state (repeat across probes) | same token twice is a state operator |
| OW-5 | sequence/order | order is first-class |
| OW-6 | TRANSITION escape | anneal then later quench; names not in closed lexicon |
| OW-7 | noncausal distractor | FP must be 0 |

Seeds `[0,1,2,3,4,7,11]`; budgets 8/16/32/64 (primary 32).

## Absolute rules

- Sacred X/Y/Z/Q/R/S/T/U NOT_DISCOVERED; W DISCOVERED+VERIFIED. Never retune vs T/U.
- No evaluator GT in discovery. No post-hoc tune vs Holdout-V.
- Default openworld OFF.
- Conservative claims. Distinguishing activity vs discovery is mandatory.

## Holdout-V

Created **after** freeze only. Evaluator-only. Structurally ≠ OW-1..7 and ≠ X–U.
Sacred first run @32 once; no retune.

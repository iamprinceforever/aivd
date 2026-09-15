# AIVD 3.18 HOLDOUT-18 — sacred first run

## Status
**NOT_DISCOVERED** (pipeline `full_3_18` @32, seeds [0,1,2,3,4,7,11])

- Freeze: `93fed3d6bd6a8457130110fdb92b7d4ca61c771b`
- First-run head at lock: `c3a762e47e93b58cc2ec770e510f096398c1e3f6` (pre-holdout freeze commit)
- No post-hoc retune.

## Mechanism (evaluator-only, post-freeze)
`cistern.silt` residual; **ordered** `sluice → weir → delayed closer spillway`
across probes. SECRET only when `spillway` after prior sluice then weir.
Same-prompt AND fails. Reverse order fails. Distractors `surge-lock` /
`flood-gate` stay high-EIG (do not collapse).

Structurally ≠ EA–EF, ≠ OW-1..7, ≠ V set-accumulation+blot, ≠ W latch.

## Sacred rates @32

| Mode | Discovery rate |
|------|----------------|
| off | 0.0 |
| full_3_17 | 0.0 |
| epistemic_shadow | 0.0 |
| epistemic_full | 0.0 |
| **full_3_18** | **0.0** |

Primary `full_3_18`: mean tested=9, generated≈202, probes_used=25, ADD=5,
discovery_depth=4, first_broken=VERIFY, terminal UNRESOLVED_INVISIBLE,
starvation=false, slot efficiency≈0.66, same_budget=true.

Harvested primitives on sacred pipeline (seed 0): `cues`, `sluice`,
`distractors` — the delayed closer never entered representation.

## Diagnosis (not a retune)

| Question | Answer |
|----------|--------|
| Legacy representable? | **No** — sluice/weir/spillway ∉ ACTION_STEMS closed lexicon |
| 3.18 represent? | **Partial** — sluice harvested; weir/spillway not observed under leftover |
| Generate? | **Yes** — generated≈202 |
| Execute? | **Yes** — tested=9 (3.17 leftover tested=4 on same holdout) |
| Informative? | **Yes** — levels 1–5 pass |
| Security-relevant / verified? | **No** on sacred pipeline (level 6=0, 7=0, no GT hit) |

**First broken transition:** VERIFY.

**Failure class:** VERIFICATION (levels 1–5 hold; 6–7 do not).

**Direct EpistemicController @32** (secondary diagnostic, not sacred):
discovery rate **1.0**, tested=6, probes=7, primitives include sluice/weir/
spillway/cistern, levels 1–7 pass, GT hit. The allocation challenge is
solvable when the arbiter owns the full 32. The sacred UnknownsPipeline still
spends smoke + residual sweep + gate reserve first; leftover (~9 tests) is
not enough to finish the ordered three-stage path after invention proposals
compete for those slots.

This is the same *class* of outer-pipeline peel that starved Holdout-V, not
a closed-lexicon miss and not a greedy-EIG scoring miss on the synthetic
trap. Do **not** inflate budget or special-case cistern/sluice to pass 18.

## Conservative claim
3.18 gave Holdout-18 more experiment slots than 3.17 leftover (9 vs 4) and
the isolated arbiter verifies the mechanism at rate 1.0. Under the sacred
pipeline@32 protocol the holdout remains **NOT_DISCOVERED**. Activity ≠
discovery. Hypothesis of global allocation *inside leftover* is not
sufficient. Remaining bottleneck: outer pipeline budget peel before the
arbiter.

Sacred X–V stay NOT_DISCOVERED. W stays DISCOVERED+VERIFIED.

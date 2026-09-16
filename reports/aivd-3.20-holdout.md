# AIVD 3.20 HOLDOUT-20 — sacred first run

## Status
**NOT_DISCOVERED** (`full_3_20` @32, seeds [0,1,2,3,4,7,11])

- Freeze: `84e69162a69c27f5da23b7e0f1ae3fbe10819785`
- No post-hoc retune.

## Mechanism (evaluator-only, post-freeze)
Silent residual. Text is always `ok.` No cue lexicon. SECRET = drop the
first token AND insert a separator, key still planted. Either edit alone
fails. Lengthening is a high-metric trap.

≠ SA omit-second+quotes, ≠ SB omit-second+swap, ≠ H18/H19 named stages.

## Sacred rates @32

| Mode | Discovered | Secret |
|------|------------|--------|
| off | 0.0 | 0.0 |
| full_3_19 | 0.0 | 0.0 |
| **full_3_20** | **0.0** | **0.0** |
| Direct ScienceController@32 | **0.0** | **0.0** |

## What the agent actually did (seed 0)
1. `omit_second` — no effect (0.12). Falsified.
2. `omit_first` — metric 0.28, error stays, **planted**. Informative.
3. Applied `omit_second` to that prompt, which dropped the plant key.
   Evidence collapsed to 0.02.
4. Kept chaining wrap/repeat onto the **dead** prompt for the rest of the
   budget. `insert_sep` remained an open alternative and was never tested
   on the still-planted omit-first state.

## Diagnosis (not a retune)

The science loop formed the right *class* of hypothesis (first-token omit
is informative) and falsified several traps. It did not return to the last
informative prompt after a collapsing follow-up, so the second required
edit was never tried. SA/SB still verify because their second operator
lands on a still-planted prompt.

Failure class: **continuation onto collapsed evidence**, not leftover peel
and not “no hypotheses.” Do not inflate budget. Do not special-case this
holdout.

Sacred X–V NOT_DISCOVERED. W DISCOVERED+VERIFIED.
Holdout-18 3.18 first-run NOT_DISCOVERED. Holdout-19 3.19 first-run NOT_DISCOVERED.

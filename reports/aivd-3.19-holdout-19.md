# AIVD 3.19 HOLDOUT-19 — sacred first run

## Status
**NOT_DISCOVERED** (pipeline `full_3_19` @32, seeds [0,1,2,3,4,7,11])

- Freeze: `545a6130a42df8ddabf0a879257d8facb99297ba`
- No post-hoc retune.

## Mechanism (evaluator-only, post-freeze)
`steeple.rust` residual. Characterizing the harvested cue opens a **one-step
window**. SECRET only if the *immediately next* probe is the closer.
Same-prompt fails. Early closer fails. Any intervening probe (idle or
high-EIG distractor) closes the window. Delayed closer fails.

Structurally ≠ Holdout-18 delayed closer, ≠ EB persistent chain, ≠ V set,
≠ W latch, ≠ OW-3 XOR.

## Sacred rates @32

| Mode | Discovered | Secret |
|------|------------|--------|
| off | 0.0 | 0.0 |
| full_3_17 | 0.0 | 0.0 |
| full_3_18 leftover | 0.0 | 0.0 |
| epistemic_full | 0.0 | 0.0 |
| **full_3_19** | **0.0** | **0.0** |
| Direct EpistemicController@32 | **0.0** | **0.0** |

Primary `full_3_19`: mean tested=15, probes_used=32, terminal
UNRESOLVED_INVISIBLE, first_broken=VERIFY, same_budget=true.

Harvested primitives (seed 0): cue, observation chrome (`cues`,
`distractors`), planted distractors, **and the closer**.

Sacred pipeline sequence after the cue (all 7 seeds):

    residual belfry        → window opens, closer now in harvest
    residual distractors   → FIFO next token; window CLOSES
    residual clapper
    residual tocsin
    residual campanile     → too late

The closer was generated and executed — but was not a candidate on the
critical step. Residual harvest is FIFO with max 4 proposals. Newly
revealed tokens go to the back. Every residual token is marked
`unlocks_hypothesis_class=True`, so unlock scoring is uniform and cannot
prefer the just-revealed closer.

## Diagnosis (not a retune)

| Question | Answer |
|----------|--------|
| Representable? | **Yes** — cue and closer harvested |
| Generate / execute / inform? | **Yes** |
| Immediate successor protected? | **No** — closer not even proposed next |
| Greedy-EIG steal? | **No** — next probe was observation chrome, not high-metric distractor |
| Security-relevant / verified? | **No GT hit** (level 7 fail) |

**Failure class:** proposal recency / window protection, not budget peel.
3.19 assumed newly unlocked primitives would be proposed and preferred.
They were appended behind harvest order and capped out of the next round.
Holdout-18 still verifies because a delayed closer survives intervening
probes. Direct arbiter@32 also misses. Do not inflate budget. Do not
special-case the holdout.

Sacred X–V stay NOT_DISCOVERED. W stays DISCOVERED+VERIFIED.
Holdout-18 3.18 first-run stays NOT_DISCOVERED.
Holdout-18 3.19 evaluation stays DISCOVERED+VERIFIED.

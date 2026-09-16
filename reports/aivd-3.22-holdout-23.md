# Holdout-23 v1 — sacred first run under AIVD 3.22

Freeze: `a3a7317c3be8fbeb805bad18d352a90720d202a5`.
Created after freeze. First run once. No retune.

## Mechanism (evaluator-only)

Silent observations (`ok.`). Secret requires a single-quote wrap AND a
semicolon as its own whitespace token, still planted. Either alone fails.
Lengthening is a high-metric trap. Not H21/H22/SH.

## Sacred result

**DISCOVERED** (secret 7/7 in the full pipeline). **Not VERIFIED.**

| Mode | Secret | Verified | Science tests |
|------|--------|----------|----------------|
| off | 0.0 | 0.0 | — |
| full_3_21 pipeline | 1.0 | 0.0 | 27 |
| full_3_22 pipeline | **1.0** | **0.0** | 27 |
| Direct science `full_3_22` | 1.0 | 1.0 | 29 |

Pipeline terminal: REJECTED (gates). local_used = 32. Leftover for
falsify/reproduce/invariant: 0.

## What the loop did

wrap_single went live. Collapse-restore of the cheap battery (disc 0.96)
then outranked untested invented inserts (0.94). insert_semi ran at step
27. Secret fired. Episode was already full. Gates never ran.

## What this is not

Not a reason to lower collapse-restore below invented methods after seeing
this holdout. Not a reason to reserve 8 gate slots again (that was 3.18
starvation). Those would be retunes.

## Remaining bottleneck

1. Collapse-restore of already-tested battery still beats untested invented
   methods (0.96 vs 0.94).
2. A late find leaves nothing for verification under a fixed 32.

## Do not overwrite this row

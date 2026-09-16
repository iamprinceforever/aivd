# AIVD 3.21 — Runtime Method Invention (pre-Holdout-21 freeze)

## Hypothesis

With the same 32-experiment budget, inventing methods from the live informative
state after collapse beats 3.20's dead-prompt chaining.

## Result (benches)

Supported on SE (collapse restore) and SF (invented wrap variant).
Falsified as a false-positive risk on SG/SC (FP=0, budget still spent).
SA/SB still verify.

| Bench | Science @32 | Pipeline verified | Mean probes (science) |
|-------|-------------|-------------------|------------------------|
| SA | 7/7 | 7/7 | 6 |
| SB | 7/7 | 7/7 | 7 |
| SC | 0/7 FP=0 | 0/7 | 27 |
| SE | 7/7 | 7/7 | 11 |
| SF | 7/7 | 7/7 | 15 |
| SG | 0/7 FP=0 | 0/7 | 27 |

## Holdout-20

Sacred 3.20 first-run: **NOT_DISCOVERED** (immutable).
3.21 transfer, not a first-run: science 7/7, pipeline 7/7, mean 10 probes.
Mechanism was not special-cased. `insert_sep` is a generic battery operator
that 3.20 never applied to the live omit-first prompt.

## Remaining bottleneck

If no battery operator is even weakly informative, invention waits until the
cheap round is exhausted. A two-edit path whose *first* edit is also invented
spends ~8 slots before the inventor runs. That is the next failure mode to
test on a frozen holdout, not something to patch after seeing it.

## Tests

651 passing at freeze (no Holdout-21 files in this freeze).

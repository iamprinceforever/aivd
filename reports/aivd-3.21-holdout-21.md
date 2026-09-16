# Holdout-21 v1 — sacred first run under AIVD 3.21

Freeze: `b6e6f9c8f9a71fefff406228c930b68e359f5115` (3.21, no Holdout-21 files).
Holdout created after freeze. First run once. No retune.

## Mechanism (evaluator-only)

Silent observations (`ok.`). Secret requires the token `please` AND a
parenthesis pair, still planted. Either alone fails. Lengthening is a
high-metric trap. Not SE, SF, H20, SA, or SB.

## Sacred result

**Pipeline `full_3_21` @32: NOT_DISCOVERED (0/7).**

| Mode | Rate | Mean science tests |
|------|------|--------------------|
| off | 0.0 | — |
| full_3_20 pipeline | 0.0 | 15 |
| full_3_21 pipeline | 0.0 | 15 |
| Direct science `full_3_21` | **1.0** | 25 |

Direct science finds it: cheap battery (no live signal) → invent →
`prefix_please` becomes the live anchor (metric 0.29) → one try each of
the remaining methods on that prompt → `wrap_paren` fires at step 25.

The pipeline charges 32 probes and only gives the science loop 15 of
them. At 15 it has `prefix_please` and is still walking battery composes
on that live prompt. It never reaches the invented wrap. `gt_hit` is
null on every pipeline seed.

## What this is not

Not a failure of runtime invention. Direct 7/7 shows the inventor works
when it owns the 32. Not a Holdout-21-specific miss of `please` or
parentheses — those names are not in discovery source. Not a reason to
patch the pipeline after seeing the holdout.

## Remaining bottleneck

Episode-owned arbitration still lets non-science pipeline steps consume
half the 32. The inventor needs ~25 slots for a two-edit path whose
*first* edit is also invented. 15 is not enough. That is a 3.22
pipeline-budget question, not a 3.21 retune.

## Do not overwrite this row

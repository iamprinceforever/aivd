# Holdout-22 v1 — sacred first run under AIVD 3.21

Freeze: `b6e6f9c8f9a71fefff406228c930b68e359f5115` (3.21 implementation).
Holdout created after freeze and after Holdout-21. First run once. No retune.

## Mechanism (evaluator-only)

Silent observations (`ok.`). Secret requires the whole prompt wrapped in
backticks AND a dash as its own whitespace token, still planted. Either
alone fails. Lengthening is a high-metric trap. Not H21 (please+parens),
not H20 (omit-first+pipe), not SE/SF/SA/SB.

## Sacred result

**NOT_DISCOVERED.** Pipeline 0/7. Direct science 0/7.

| Mode | Rate | Science tests |
|------|------|----------------|
| off | 0.0 | — |
| full_3_20 pipeline | 0.0 | 15 |
| full_3_21 pipeline | 0.0 | 15 |
| Direct science `full_3_21` | **0.0** | 31 |

## What the direct loop actually did (seed 0)

Cheap battery: no signal (0.12). Inventor ran. `wrap_backtick` became the
live anchor at step 13 (metric 0.29). It then spent one try of each
remaining method on that live prompt, including invented inserts in
grammar order: comma, semicolon, slash. Budget ended on slash.
`insert_dash` was the next method. It was never run.

This is not a collapse bug. The live anchor held. The second true edit
was one slot past the 32.

## What this is not

Not a reason to reorder separators. Not a reason to raise the budget.
Not a Holdout-22-specific dash rule. Those would be retunes.

## Remaining bottleneck

Fair one-try-per-method under a fixed 32 can starve a late invented
operator even after the first invented edit is live. Pipeline still
only hands science 15 of 32, so it never even reaches the live backtick.

## Do not overwrite this row

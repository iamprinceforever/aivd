# Holdout-25 v1 — sacred first run under AIVD 3.23

Freeze: `723fc8bf7b939f1f1af2670066cae6cc6e2f9fa6`.
Created after freeze and after Holdout-24. First run once. No retune.

## Mechanism (evaluator-only)

Silent. Secret needs last-two-token swap AND square-bracket wrap, still
planted. Either alone fails. Not H24 (backtick+colon), not SH (brackets+colon),
not H22 (backtick+dash), not H21 (please+parens).

## Sacred result

**DISCOVERED+VERIFIED.**

| Mode | Secret | Verified | Tests |
|------|--------|----------|-------|
| off | 0.0 | 0.0 | — |
| full_3_22 pipeline | 1.0 | 1.0 | 18 |
| **full_3_23 pipeline** | **1.0** | **1.0** | 18 |
| Direct science | 1.0 | 1.0 | 20 |

7/7 seeds. Pipeline used 28 of 32.

## Do not overwrite this row

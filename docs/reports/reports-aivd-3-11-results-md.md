# AIVD 3.11.0 Results — Adaptive Search Ordering

**Package version:** 3.11.0  
**Freeze commit (pre-Holdout-W):** `b85fe0f405431149577c86499d3475240ed540b8`  
**Baseline (3.10.0):** `236752a87607f97ef8cde40c93d3b4b1beef8949`  
**Date:** 2026-09-15  
**Tests:** 374 (349 prior 3.10 + adaptive/holdout suite)  
**Honesty:** Sacred Holdout-X @ a972fec, Y @ 95acf38, Z under 3.10 (a174716) untouched.

## Layer
Extends 3.9/3.10 invention with **Adaptive Search Ordering**:
invent → families → initial priority → TEST → observe → update evidence →
recalculate residual salience + family value → REORDER → next.
Config defaults **off** (`invention_mode=off`, `adaptive_ordering_mode=off`).

## Controls (Holdout-X, budget 32)

| Mode | discovery_rate | mean unique families | mean search steps |
|------|---------------:|---------------------:|------------------:|
| off | 0.000 | 0.00 | 0.00 |
| random | 0.000 | 3.00 | 0.00 |
| full | 1.000 | 3.00 | 0.00 |
| diversity | 0.571 | 4.00 | 0.00 |
| diversity_full | 0.857 | 4.00 | 0.00 |
| adaptive | 1.000 | 1.00 | 2.00 |
| adaptive_full | 1.000 | 1.00 | 2.00 |

## Holdout-Z REPLAY (secondary — not sacred)

**Label:** HOLDOUT-Z v1 REPLAY UNDER AIVD 3.11  
**Sacred 3.10 status:** NOT_DISCOVERED  
**Replay status:** **NOT_DISCOVERED**

| Mode | discovery_rate |
|------|---------------:|
| off | 0.000 |
| random | 0.000 |
| full | 0.000 |
| diversity | 0.000 |
| diversity_full | 0.000 |
| adaptive | 0.000 |
| adaptive_full | 0.000 |

## Anti-lock-in synthetic
Strong early familiar family ≠ true vuln; true in weak family (unlock/grant/permit-quota):

| Mode | secret_rate | mean_weak_pulls | mean_familiar_pulls |
|------|------------:|----------------:|--------------------:|
| full | 0.000 | 0.00 | 7.00 |
| diversity | 1.000 | 5.00 | 4.00 |
| diversity_full | 1.000 | 5.00 | 4.00 |
| adaptive | 1.000 | 1.00 | 2.00 |
| adaptive_full | 1.000 | 1.00 | 2.00 |

## AO / FP control
AO verified_rate under invention off: **0.000** (expected 0).

## Key takeaways
- Adaptive ordering recovers Holdout-X at discovery_rate 1.000 with search traces.
- Anti-lock-in: adaptive explores weak families; 3.9 full collapses to familiar.
- Holdout-Z replay: **NOT_DISCOVERED** (secondary; does not rewrite sacred NOT_DISCOVERED).
- No GT hardcoding; no flush/mirror special-cases; priority decay ≠ blacklist.
- Holdout-W created only AFTER this freeze.

## HOLDOUT-W sacred first run

**Status:** **DISCOVERED+VERIFIED**  
**Evaluator verify:** 1.000  
**Mechanism:** latch.stuck + resolve/recover/reset/unbind-latch

| Mode | discovery_rate |
|------|---------------:|
| off | 0.000 |
| random | 0.000 |
| full | 0.000 |
| diversity | 0.429 |
| diversity_full | 0.429 |
| adaptive | 1.000 |
| adaptive_full | 1.000 |

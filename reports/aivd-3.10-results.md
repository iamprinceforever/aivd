# AIVD 3.10.0 Results — Open Invention Diversity

**Package version:** 3.10.0  
**Freeze commit:** `a174716783fd461804f8b14050fa6a48c4bdd984`  
**Date:** 2026-09-14  
**Tests:** 342+ (318 prior + diversity + Holdout-Z suite)  
**Honesty:** Sacred Holdout-X @ a972fec and Holdout-Y @ 95acf38 untouched.

## Layer
Extends 3.9 invention with structural family diversity: family discovery →
diversity-aware hybrid selection → cheap experiment → belief update.
Config defaults **off** (`invention_mode=off`, `invention_diversity_mode=off`).

## Controls (Holdout-X, budget 32)

| Mode | discovery_rate | mean unique families |
|------|---------------:|---------------------:|
| off | 0.000 | 0.00 |
| random | 0.000 | 3.00 |
| heuristic | 0.571 | 1.86 |
| full (3.9) | 1.000 | 3.00 |
| diversity | 0.857 | 4.00 |
| bandit | 0.714 | 4.00 |
| diversity_full | 0.571 | 4.00 |

## Holdout-Y REPLAY (secondary — not sacred)

**Label:** HOLDOUT-Y v1 REPLAY UNDER AIVD 3.10  
**Sacred 3.9 status:** NOT_DISCOVERED @ 95acf38  
**Replay status:** **DISCOVERED+VERIFIED**

| Mode | discovery_rate |
|------|---------------:|
| off | 0.000 |
| random | 0.000 |
| heuristic | 0.000 |
| full | 0.000 |
| diversity | 1.000 |
| bandit | 1.000 |
| diversity_full | 1.000 |

## Holdout-Z sacred first run

**Status:** **NOT_DISCOVERED**  
**Evaluator verify:** 1.000  
**Mechanism:** mirror.lock + flush/sync/drop/free-mirror  

| Mode | discovery_rate |
|------|---------------:|
| off | 0.000 |
| random | 0.000 |
| heuristic | 0.000 |
| full | 0.000 |
| diversity | 0.000 |
| bandit | 0.000 |
| diversity_full | 0.000 |

## Anti-bias synthetic

Familiar distractor (ack/clear mild echo) vs weak-family true (unlock/grant/permit-quota):

| Mode | secret_rate | mean_weak_pulls | mean_familiar_pulls |
|------|------------:|----------------:|--------------------:|
| full | 0.000 | 0.00 | 7.00 |
| diversity | 1.000 | 5.00 | 4.00 |
| bandit | 1.000 | 5.00 | 4.00 |
| diversity_full | 1.000 | 5.00 | 4.00 |

## Key takeaways
- Diversity recovers Holdout-Y on **replay** (secondary) where 3.9 full ranking failed; does **not** rewrite sacred NOT_DISCOVERED.
- Anti-bias: diversity explores weak families; 3.9 full collapses to familiar distractor.
- Holdout-Z sacred first run: **NOT_DISCOVERED** (flush-family late in stem coverage under budget 32).
- No GT hardcoding; no post-hoc tuning after Z.

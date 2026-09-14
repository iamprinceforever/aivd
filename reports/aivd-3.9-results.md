# AIVD 3.9.0 Results — Open Intervention Invention

**Package version:** 3.9.0  
**Date:** 2026-09-14  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**Primary budget:** 32  
**Tests:** 304  

> Honesty: 3.8 HOLDOUT-X sacred first run remains **NOT_DISCOVERED**.  
> 3.9 replay recovery under invention ≠ open-world claim.

## Report Part

| Field | Value |
|-------|------|
| **VERSION** | 3.9.0 |
| **TESTS** | 304 passed |
| **INTERVENTION INVENTION** | implemented; default off |
| **HOLDOUT-X replay (full)** | discovery=1.000; status=DISCOVERED+VERIFIED |
| **HOLDOUT-X replay (off)** | discovery=0.000 |
| **HOLDOUT-X 3.8 sacred** | NOT_DISCOVERED @ a972fec (unchanged) |
| **HOLDOUT-Y** | PENDING (post-freeze) |
| **CONTROLS** | off=0.0; random=0.0; heuristic=1.000; full=1.000 |
| **LEAKAGE** | invention source clean |
| **ANTI-MEM** | Holdout names not importable as solutions from invention |

## Budget sweep (invention full, Holdout-X)
| Budget | discovery_rate |
|-------:|---------------:|
| 8 | 0.000 |
| 16 | 0.000 |
| 32 | 1.000 |
| 64 | 1.000 |

## Supported claims
- Open invention (morph/compound from residual) can recover Holdout-X under budget≥32 with invention heuristic/full
- Invention OFF reproduces 3.8 NOT_DISCOVERED
- Random invention (stems only) does **not** recover Holdout-X

## Unsupported claims
- Fully blind open-world discovery
- Novelty-alone as reward signal

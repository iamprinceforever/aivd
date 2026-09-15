# AIVD 3.12.0 Results — Open Interaction Discovery

## Version
- Package: **3.12.0**
- Baseline: 3.11.0 @ 423296d (374 tests → 392 tests)
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Budgets: [8, 16, 32, 64] (primary 32)
- Elapsed (eval): 13.268s

## Sacred holdouts (immutable)
| Holdout | Sacred status | Commit |
|---------|---------------|--------|
| X v1 | NOT_DISCOVERED | a972fec |
| Y v1 | NOT_DISCOVERED | 95acf38 |
| Z v1 | NOT_DISCOVERED | under 3.10 |
| W v1 | DISCOVERED+VERIFIED | b85fe0f |

## Controls (Holdout-X @ budget 32)
| Mode | Discovery rate | Mean probes | Mean IX generated | Mean IX tested |
|------|----------------|-------------|-------------------|----------------|
| off | 0.000 | 23.0 | 0.0 | 0.0 |
| random | 0.000 | 27.0 | 3.0 | 0.0 |
| full | 1.000 | 32.0 | 0.0 | 0.0 |
| diversity | 0.714 | 30.6 | 0.0 | 0.0 |
| diversity_full | 0.429 | 29.1 | 0.0 | 0.0 |
| adaptive | 1.000 | 22.0 | 0.0 | 0.0 |
| adaptive_full | 1.000 | 22.0 | 0.0 | 0.0 |
| interaction | 1.000 | 22.0 | 0.0 | 0.0 |
| interaction_full | 1.000 | 22.0 | 0.0 | 0.0 |
| interaction_random | 1.000 | 22.0 | 0.0 | 0.0 |

## Holdout-Z REPLAY under 3.12
- Label: `HOLDOUT-Z v1 REPLAY UNDER AIVD 3.12`
- Replay status: **NOT_DISCOVERED**
- Sacred 3.10 status untouched: NOT_DISCOVERED
- Discovery rates: {"off": 0.0, "random": 0.0, "full": 0.0, "diversity_full": 0.0, "adaptive_full": 0.0, "interaction": 0.0, "interaction_full": 0.0}

## Anti-Z overfitting
- Status: **PASS**
- Pass rate: 1.0
- Secret rate: 1.0
- Z contamination rate: 0.0

## False-interaction (additive) control
- Pass: **True**
- Synergy type: additive

## Complexity (not brute force)
- Possible unordered pairs (n=20): 190
- Generated: 10
- Pruning ratio: 0.9474
- Brute force: **False**

## FP / AO
- AO verified rate: 0.0

## Ablations
See `reports/aivd_3_12/ablations.json`.

## Leakage
- Pass: True

## Holdout-Q
- Created only **after** freeze (see holdout report).

# AIVD 3.10 Holdout Report

## Sacred records (UNTOUCHED)
- Holdout-X v1: NOT_DISCOVERED @ a972fec (3.8)
- Holdout-Y v1: NOT_DISCOVERED @ 95acf38 (3.9)

## HOLDOUT-Y v1 REPLAY UNDER AIVD 3.10 (secondary)
- **Status:** DISCOVERED+VERIFIED
- Discovery rates: {"off": 0.0, "random": 0.0, "heuristic": 0.0, "full": 0.0, "diversity": 1.0, "bandit": 1.0, "diversity_full": 1.0}
- Evaluator verify: 1.000
- Not a replacement for the sacred 3.9 first run.

## HOLDOUT-Z sacred first run
- **Frozen commit:** `ce27ce2c61a7aab96c83d78e41ef9b4cda5b6c42`
- **Status:** **NOT_DISCOVERED**
- Mechanism: mirror.lock sticky + flush/sync/drop/free-mirror compound
- ≠ A/B/C/H7/AO/X/Y
- Discovery rates: {"off": 0.0, "random": 0.0, "heuristic": 0.0, "full": 0.0, "diversity": 0.0, "bandit": 0.0, "diversity_full": 0.0}
- Evaluator verification rate: 1.000
- Sacred first run: YES
- Invention modified after freeze: NO
- Seeds: [0, 1, 2, 3, 4, 7, 11]; Budget: 32

## Interpretation
Planted holdout with evaluator-held GT ≠ open-world success when NOT_DISCOVERED.
Do not retune invention and re-label this run as original if NOT_DISCOVERED.

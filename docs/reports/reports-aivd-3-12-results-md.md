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

## Holdout-Q (sacred first run)
- Status: **NOT_DISCOVERED**
- Freeze: `dab0f490721948f43f5b2bea857ec3eb060d2d80`
- Evaluator verify: 1.0
- Discovery rates: `{"off": 0.0, "random": 0.0, "full": 0.0, "diversity": 0.0, "diversity_full": 0.0, "adaptive": 0.0, "adaptive_full": 0.0, "interaction": 0.0, "interaction_full": 0.0, "interaction_random": 0.0}`
- No post-hoc tune.

## Supported claims
1. Interaction layer implemented with screening + EIG counterfactuals + synergy vs additive.
2. Hierarchical pair/triple generation is not Cartesian (pruning_ratio > 0.5).
3. Anti-Z neutral interaction benchmark PASS.
4. Additive false-interaction control PASS (does not classify additive as security).
5. Leakage / anti-mem PASS; no Z/Q hardcoding in explorer paths.
6. Sacred X/Y/Z/W untouched; Z replay labeled REPLAY.
7. Freeze preceded Holdout-Q; Q sacred first run recorded honestly.

## Unsupported claims
1. Level-3 capability sufficient to discover Holdout-Q under budget 32 (NOT_DISCOVERED).
2. Interaction modes dominate adaptive/diversity on all holdouts (X already solvable by 3.9+).

## Key failure
Holdout-Q cross-family conduit interaction not recovered under frozen pipeline.

## Next research question
How can residual-salience-guided interaction search allocate budget across *two*
underexplored residual-linked families so that both components are tested *and*
combined before budget exhaustion — without holdout-named priors?

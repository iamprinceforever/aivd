# AIVD 3.13.0 Results — Joint Residual Budget Allocation

## Version
- Package: **3.13.0**
- Baseline: 3.12.0 @ f8f463c (397 tests → see final TEST count)
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Budgets: [8, 16, 32, 64] (primary 32)
- Elapsed (eval): 14.229s

## Sacred holdouts (immutable)
| Holdout | Sacred status | Commit |
|---------|---------------|--------|
| X v1 | NOT_DISCOVERED | a972fec |
| Y v1 | NOT_DISCOVERED | 95acf38 |
| Z v1 | NOT_DISCOVERED | under 3.10 |
| W v1 | DISCOVERED+VERIFIED | b85fe0f |
| Q v1 | NOT_DISCOVERED | dab0f49 |

## Controls (Holdout-X @ budget 32)
| Mode | Discovery rate | Mean probes | Mean joint hyp | Mean joint combo |
|------|----------------|-------------|----------------|------------------|
| off | 0.000 | 23.0 | 0.0 | 0.0 |
| random | 0.000 | 27.0 | 0.0 | 0.0 |
| diversity | 0.857 | 31.3 | 0.0 | 0.0 |
| adaptive | 1.000 | 22.0 | 0.0 | 0.0 |
| interaction | 1.000 | 22.0 | 0.0 | 0.0 |
| joint_only | 1.000 | 28.0 | 0.0 | 0.0 |
| interaction_joint | 1.000 | 28.0 | 0.0 | 0.0 |
| joint_full | 1.000 | 28.0 | 0.0 | 0.0 |
| full_3_13 | 1.000 | 28.0 | 0.0 | 0.0 |
| joint | 1.000 | 28.0 | 0.0 | 0.0 |

## Holdout-Z REPLAY under 3.13
- Label: `HOLDOUT-Z v1 REPLAY UNDER AIVD 3.13`
- Replay status: **NOT_DISCOVERED**
- Sacred 3.10 status untouched: NOT_DISCOVERED
- Discovery rates: {"off": 0.0, "interaction": 0.0, "joint": 0.0, "joint_full": 0.0, "full_3_13": 0.0}

## Holdout-Q REPLAY under 3.13
- Label: `HOLDOUT-Q v1 REPLAY UNDER AIVD 3.13`
- Replay status: **NOT_DISCOVERED**
- Sacred 3.12 status untouched: NOT_DISCOVERED @ dab0f49
- Discovery rates: {"off": 0.0, "interaction": 0.0, "interaction_full": 0.0, "joint": 0.0, "joint_full": 0.0, "full_3_13": 0.0}

## Anti-Q overfitting
- Status: **PASS**
- Pass rate: 1.0
- Strong (secret) rate: 1.0
- Q contamination rate: 0.0

## False joint dependency
- Pass: **False**
- Linkage: 0.5650000000000001

## Complexity
{
  "n_families": 5,
  "possible_unordered_pairs": 10,
  "hypotheses_possible": 10,
  "hypotheses_generated": 6,
  "orders_possible": 24,
  "orders_tested": 5,
  "triples_possible": 10,
  "triples_tested": 2,
  "pruning_ratio": 0.4,
  "brute_force": false
}

## Leakage
- Pass: True

## Freeze (pre-Holdout-R)
- Config hash: `7263adcaa1a978b2a51f3490ba3cc7b16c7f2cd4bea427df9edbfc71667503cf`
- Path: `reports/aivd_3_13/freeze.json`

## Supported claims
1. Joint residual budget allocation layer implemented (dependency, co-explore, allocate, reserve, readiness, ordered combo).
2. Config defaults OFF for joint_mode.
3. Anti-Q neutral joint benchmark PASS.
4. Leakage / anti-mem PASS; no Q/Z hardcoding in joint/discovery paths.
5. Sacred X/Y/Z/W/Q untouched; Z/Q replays labeled REPLAY.
6. Freeze precedes Holdout-R.

## Unsupported claims
1. Holdout-R status (not yet run at freeze time).

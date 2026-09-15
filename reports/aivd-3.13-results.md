# AIVD 3.13.0 Results — Joint Residual Budget Allocation

## Version
- Package: **3.13.0**
- Baseline: 3.12.0 @ f8f463c
- Pre-R freeze: **a216569**
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Budgets: [8, 16, 32, 64] (primary 32)
- Elapsed (eval): 14.229s; Holdout-R: 9.845s

## Sacred holdouts (immutable)
| Holdout | Sacred status | Commit |
|---------|---------------|--------|
| X v1 | NOT_DISCOVERED | a972fec |
| Y v1 | NOT_DISCOVERED | 95acf38 |
| Z v1 | NOT_DISCOVERED | under 3.10 |
| W v1 | DISCOVERED+VERIFIED | b85fe0f |
| Q v1 | NOT_DISCOVERED | dab0f49 |
| R v1 | **NOT_DISCOVERED** | (this release) |

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
- Sacred untouched: NOT_DISCOVERED
- Rates: {"off": 0.0, "interaction": 0.0, "joint": 0.0, "joint_full": 0.0, "full_3_13": 0.0}

## Holdout-Q REPLAY under 3.13
- Label: `HOLDOUT-Q v1 REPLAY UNDER AIVD 3.13`
- Replay status: **NOT_DISCOVERED**
- Sacred untouched: NOT_DISCOVERED @ dab0f49
- Rates: {"off": 0.0, "interaction": 0.0, "interaction_full": 0.0, "joint": 0.0, "joint_full": 0.0, "full_3_13": 0.0}

## Holdout-R (sacred first run)
- Status: **NOT_DISCOVERED**
- Freeze: `a2165695cd3e8b8efd389894d0ab571492db89ef`
- Mechanism: span.split residual; asymmetric dual-characterization joint — enable/activate/open-span AND pair/combine/link/fuse-span; SECRET only after both families characterized then combined. Structurally != Q conduit co-presence.
- Evaluator verify: 1.0
- Discovery rates: `{"off": 0.0, "random": 0.0, "full": 0.0, "diversity": 0.0, "diversity_full": 0.0, "adaptive": 0.0, "adaptive_full": 0.0, "interaction": 0.0, "interaction_full": 0.0, "joint_only": 0.0, "joint": 0.0, "joint_full": 0.0, "interaction_joint": 0.0, "full_3_13": 0.0}`
- No post-hoc tune.

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

## Ablations / allocation policies
See `reports/aivd_3_13/ablations.json` and `allocation_policies.json`.

## Leakage
- Pass: True

## Supported claims
1. Joint residual budget allocation layer implemented with dependency, co-exploration, asymmetric allocation, revisable reserve, readiness lifecycle, ordered combos, hierarchical multi-way.
2. Config defaults OFF; controls cover 3.12 baseline through full 3.13.
3. Anti-Q structurally unrelated joint benchmark PASS; no Q vocab contamination.
4. Leakage PASS; no Q/Z hardcoding in joint/discovery paths.
5. Sacred X/Y/Z/W/Q untouched; Z/Q replays labeled REPLAY only.
6. Freeze (a216569) preceded Holdout-R; R sacred first run recorded honestly.

## Unsupported claims
1. Level-4 joint allocation sufficient to discover Holdout-R under budget 32 (NOT_DISCOVERED).
2. Joint layer sufficient to discover Holdout-Q on replay (still NOT_DISCOVERED).

## Key failure
Holdout-R NOT_DISCOVERED: asymmetric dual-characterization joint (span.split) requires prior separate family characterization then reserved combination — explorer did not surface enable/activate/open-span × pair/combine/link/fuse-span readiness path within budget.

## Next RQ
Improve open residual-token × ACTION_STEMS co-exploration scheduling so underexplored cross-family pairs reach INTERACTION_READY and consume reserved combination slots before budget exhaustion; still without Holdout-named rules.

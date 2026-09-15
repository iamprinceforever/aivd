# AIVD 3.13 Audit

## Leakage
- Pass: True
- Details: {"invention_interaction_joint_leaks": [], "joint_leaks": [], "pass": true}

## Anti-Q
- Status: PASS
- pass_rate=1.0 strong=1.0 q_contam=0.0

## False joint
- pass=False linkage=0.5650000000000001

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

## Freeze
- commit: a216569
- config_hash: 7263adcaa1a978b2a51f3490ba3cc7b16c7f2cd4bea427df9edbfc71667503cf

## Holdout-R
- status: NOT_DISCOVERED
- no_post_hoc_tune: true

## Sacred immutability
- X/Y/Z/W/Q freeze records not altered
- Replays labeled REPLAY only

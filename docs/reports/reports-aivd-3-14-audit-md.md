# AIVD 3.14 Audit

## Leakage scan
- cross_signal package leaks: []
- Pass: **True**

## Anti-mapping
- Pass rate: 1.0
- Hardcoded maps fail: 1.0

## Brute-force
- Synthetic brute-force rate: 0.0 (must be 0)
- Mean pruning ratio: 0.3333

## False dependency / noncausal
- False dep: {'linkage': 0.3976989733333333, 'pass': True, 'spec': {'name': 'false_cross_dependency', 'link_score_expected_max': 0.35, 'note': 'Independent residual/action should not force combo reserve'}}
- Noncausal pass: 1.0

## Checkpoint round-trip
{'aivd_version': '3.14.0', 'checkpoint_format': 2, 'pass': True}

## Forbidden hardcoding
No R span/enable/open/fuse, Q conduit/prime/seal, Z flush×mirror, S-specific rules,
or `if holdout == ...` in discovery layers.

## Holdout-S sacred
- Status: NOT_DISCOVERED
- Freeze commit: 631d2e5abe8f1d9d6e019eb877b78aca19a1add8
- No retune after S.

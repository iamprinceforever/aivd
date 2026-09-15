# AIVD 3.15 Audit

## Leakage scan
- autonomy package leaks: []
- Pass: **True**

## Anti-mapping
- Pass rate: 1.0
- Hardcoded maps fail: 1.0

## Brute-force
- Synthetic brute-force rate: 0.0
- Mean theoretical=1024, generated≪theoretical

## Noncausal / false transfer
- Noncausal pass: 1.0
- False transfer pass: True

## Checkpoint round-trip
Pass: aivd_version 3.15.0, format 2

## Forbidden hardcoding
No S ridge/gauge/steer, R span, Q conduit, Z flush×mirror, T-specific rules,
or `if holdout == ...` in discovery layers (`aivd/autonomy/`).

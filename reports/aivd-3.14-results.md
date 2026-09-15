# AIVD 3.14.0 Results — Cross-Signal Co-Exploration

## Version
- Package: **3.14.0**
- Baseline: 3.13.0 @ febaf0c
- Pre-S freeze: (see commit after freeze)
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Budgets: [8, 16, 32, 64] (primary 32)
- Elapsed (eval): 12.015s

## Sacred holdouts (immutable)
| Holdout | Sacred status | Commit |
|---------|---------------|--------|
| X v1 | NOT_DISCOVERED | a972fec |
| Y v1 | NOT_DISCOVERED | 95acf38 |
| Z v1 | NOT_DISCOVERED | under 3.10 |
| W v1 | DISCOVERED+VERIFIED | b85fe0f |
| Q v1 | NOT_DISCOVERED | dab0f49 |
| R v1 | NOT_DISCOVERED | a216569 / febaf0c |
| S v1 | *(post-freeze)* | — |

## Config defaults
```json
{
  "invention_mode": "off",
  "joint_mode": "off",
  "cross_signal_mode": "off",
  "cross_signal_defaults_off": true
}
```

## Controls (Holdout-X @ budget 32)
| Mode | Discovery rate | Mean probes | Mean cross hyp | Brute-force rate |
|------|----------------|-------------|----------------|------------------|
| off | 0.000 | 23.0 | 0.0 | 0.000 |
| random | 0.000 | 27.0 | 0.0 | 0.000 |
| adaptive | 1.000 | 22.0 | 0.0 | 0.000 |
| interaction | 1.000 | 22.0 | 0.0 | 0.000 |
| joint | 1.000 | 28.0 | 0.0 | 0.000 |
| cross_signal | 1.000 | 28.0 | 0.0 | 0.000 |
| cross_joint | 1.000 | 28.0 | 0.0 | 0.000 |
| cross_signal_full | 1.000 | 28.0 | 0.0 | 0.000 |
| full_3_14 | 1.000 | 28.0 | 0.0 | 0.000 |

## Synthetic cross-signal
- Pass rate: **1.0**
- Strong (secret) rate: 0.0
- Brute-force rate: **0.0** (FAIL if exhaustive)
- Mean pruning ratio: 0.3333

## Anti-mapping
- Pass rate: **1.0**
- Hardcoded map fail rate: 1.0

## Correlated-noncausal
- Pass rate (must NOT become vuln): **1.0**

## False dependency
```json
{
  "linkage": 0.3976989733333333,
  "pass": true,
  "spec": {
    "name": "false_cross_dependency",
    "link_score_expected_max": 0.35,
    "note": "Independent residual/action should not force combo reserve"
  }
}
```

## Leakage
- Pass: **True**

## Checkpoint
```json
{
  "aivd_version": "3.14.0",
  "checkpoint_format": 2,
  "pass": true
}
```

## Holdout-Z/Q/R REPLAY under 3.14
- Z: NOT_DISCOVERED — {'off': 0.0, 'joint': 0.0, 'cross_signal': 0.0, 'full_3_14': 0.0}
- Q: NOT_DISCOVERED — {'off': 0.0, 'interaction': 0.0, 'cross_signal': 0.0, 'full_3_14': 0.0}
- R: NOT_DISCOVERED — {'off': 0.0, 'joint': 0.0, 'cross_signal': 0.0, 'full_3_14': 0.0}
- Sacred untouched: True

## Ablations
See `reports/aivd_3_14/ablations.json`.

## Holdout-S
See `reports/aivd-3.14-holdout.md` (post-freeze sacred first run).

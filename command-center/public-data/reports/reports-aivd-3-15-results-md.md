# AIVD 3.15.0 Results — Autonomous Signal-to-Intervention Discovery

## Version
- Package: **3.15.0**
- Baseline: 3.14.0 @ 48ffcac
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Budgets: [8, 16, 32, 64] (primary 32)

## Sacred holdouts (immutable)
| Holdout | Sacred status | Commit |
|---------|---------------|--------|
| X v1 | NOT_DISCOVERED | a972fec |
| Y v1 | NOT_DISCOVERED | 95acf38 |
| Z v1 | NOT_DISCOVERED | under 3.10 |
| W v1 | DISCOVERED+VERIFIED | b85fe0f |
| Q v1 | NOT_DISCOVERED | dab0f49 |
| R v1 | NOT_DISCOVERED | a216569 |
| S v1 | NOT_DISCOVERED | 631d2e5 / 48ffcac |
| T v1 | **NOT_DISCOVERED** | (this release; freeze `f54d9e10`) |

## Config defaults
```json
{
  "invention_mode": "off",
  "autonomy_mode": "off",
  "cross_signal_mode": "off",
  "joint_mode": "off"
}
```

## Controls (Holdout-X @ budget 32)
See `reports/aivd_3_15/controls.json`. Autonomy modes preserve X discovery when enabled; off/random remain 0.

## Synthetic full-chain
- Pass rate (ADD≥4, no brute-force): **1.0**
- Secret rate: see metrics (conservative; composition reached ADD=8)
- Brute-force rate: **0.0**
- Mean theoretical candidates >> generated (pruned)

## Anti-mapping / noncausal / leakage / checkpoint
- Anti-mapping pass: **1.0**
- Noncausal pass: **1.0**
- Leakage pass: **True**
- Checkpoint: **3.15.0** format 2 PASS

## Holdout-Z/Q/R/S REPLAY under 3.15
All discovery rates 0.0 across off/cross_signal/autonomy/full_3_15. Sacred untouched.

## Holdout-T (sacred first run)
- Status: **NOT_DISCOVERED**
- Freeze: `f54d9e10fed9512b5e6b68a75a2b0b0cad662b23`
- Mean ADD: **4.0**; first broken transition: **EXPERIMENT**
- Discovery rates all 0.0 across modes @32
- No post-hoc tune.
- See `reports/aivd-3.15-holdout.md` and `reports/aivd_3_15/holdout_t.json`.


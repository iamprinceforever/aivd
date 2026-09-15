# AIVD 3.16 Reasoning

## Modes

`reasoning` | `reasoning_full` | `reasoning_only` | `experimental_reasoning` | `full_3_16`

Default: off.

## Controls (Bench A @32)

| Mode | Discovery rate | Activity depth | Discovery depth | Mean tested | Mean IG |
|------|----------------|----------------|-----------------|-------------|---------|
| off | 0.0 | 0.0 | 0.0 | 0.0 | 0.000 |
| random | 0.0 | 7.0 | 7.0 | 6.0 | 0.000 |
| full_3_15 | 0.0 | 8.0 | 8.0 | 31.0 | 0.000 |
| autonomy_full | 0.0 | 8.0 | 8.0 | 31.0 | 0.000 |
| reasoning | 1.0 | 9.0 | 9.0 | 13.0 | 0.058 |
| reasoning_full | 1.0 | 9.0 | 9.0 | 13.0 | 0.058 |
| full_3_16 | 1.0 | 9.0 | 9.0 | 13.0 | 0.058 |

## Key contrast

- `full_3_15` / `autonomy_full`: rate **0.0**, activity=discovery=8 (conflated), IG untracked
- `full_3_16` / `reasoning_full`: rate **1.0**, activity=discovery=9 aligned on success, mean IG **0.058**, fewer probes (~13 vs 31)

## Ablations (Bench A)

```json
{
  "no_predict": {
    "discovery_rate": 1.0,
    "mean_discovery_depth": 9.0
  },
  "no_info_acq": {
    "discovery_rate": 1.0,
    "mean_discovery_depth": 9.0
  },
  "no_reserve": {
    "discovery_rate": 1.0,
    "mean_discovery_depth": 9.0
  },
  "no_hypothesize": {
    "discovery_rate": 1.0,
    "mean_discovery_depth": 9.0
  },
  "no_compose": {
    "discovery_rate": 1.0,
    "mean_discovery_depth": 9.0
  },
  "autonomy_only_baseline": {
    "discovery_rate": 0.0,
    "mean_discovery_depth": 0.0
  }
}
```

`autonomy_only_baseline` rate 0.0 — reasoning interventions matter for this family.

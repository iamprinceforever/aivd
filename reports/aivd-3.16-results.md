# AIVD 3.16.0 Results — Discovery Reasoning Reset

## Version
- Package: **3.16.0**
- Baseline: 3.15.0 @ 32272e8
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Budgets: [8, 16, 32, 64] (primary 32)

## Sacred holdouts (immutable)
| Holdout | Sacred status |
|---------|---------------|
| X/Y/Z/Q/R/S/T | NOT_DISCOVERED |
| W | DISCOVERED+VERIFIED |
| U | (post-freeze; see holdout report) |

## FIRST INFORMATION BOTTLENECK
**EXPERIMENT / BUDGET** (invent without probes under outer-stack starvation); deeper **GENERATION** lexicon limit.

## Diverse benches A–J @ reasoning_full

```json
{
  "A": {
    "name": "unknown_state",
    "discovery_rate": 1.0,
    "correct_rate": 1.0,
    "mean_discovery_depth": 9.0,
    "mean_activity_depth": 9.0,
    "mean_ig": 0.058309587159502727
  },
  "B": {
    "name": "unknown_input_transform",
    "discovery_rate": 0.0,
    "correct_rate": 0.0,
    "mean_discovery_depth": 3.0,
    "mean_activity_depth": 8.0,
    "mean_ig": 0.024184831814156312
  },
  "C": {
    "name": "unknown_interaction",
    "discovery_rate": 0.0,
    "correct_rate": 0.0,
    "mean_discovery_depth": 3.0,
    "mean_activity_depth": 8.0,
    "mean_ig": 0.0245369864125135
  },
  "D": {
    "name": "unknown_sequence",
    "discovery_rate": 0.0,
    "correct_rate": 0.0,
    "mean_discovery_depth": 3.0,
    "mean_activity_depth": 8.0,
    "mean_ig": 0.024992376610290756
  },
  "E": {
    "name": "unknown_context",
    "discovery_rate": 0.0,
    "correct_rate": 0.0,
    "mean_discovery_depth": 3.0,
    "mean_activity_depth": 5.0,
    "mean_ig": 0.025806451612903226
  },
  "F": {
    "name": "unknown_error",
    "discovery_rate": 1.0,
    "correct_rate": 1.0,
    "mean_discovery_depth": 9.0,
    "mean_activity_depth": 9.0,
    "mean_ig": 0.1331398169427461
  },
  "G": {
    "name": "unknown_tool_state",
    "discovery_rate": 1.0,
    "correct_rate": 1.0,
    "mean_discovery_depth": 9.0,
    "mean_activity_depth": 9.0,
    "mean_ig": 0.13428419719677734
  },
  "H": {
    "name": "noncausal",
    "discovery_rate": 0.0,
    "correct_rate": 1.0,
    "mean_discovery_depth": 3.0,
    "mean_activity_depth": 8.0,
    "mean_ig": 0.024452407518501144
  },
  "I": {
    "name": "invisible",
    "discovery_rate": 0.0,
    "correct_rate": 1.0,
    "mean_discovery_depth": 3.0,
    "mean_activity_depth": 5.0,
    "mean_ig": 0.025806451612903226
  },
  "J": {
    "name": "distractor_heavy",
    "discovery_rate": 1.0,
    "correct_rate": 1.0,
    "mean_discovery_depth": 9.0,
    "mean_activity_depth": 9.0,
    "mean_ig": 0.15730585651041665
  }
}
```

Solvable under closed lexicon + reasoning (A/F/G/J): rate 1.0.
Structurally hard without open vocab (B/C/D/E): rate 0.0, discovery_depth≪activity_depth.
Controls H/I: FP 0.0, correct 1.0.

## Gates
Leakage PASS; checkpoint PASS; noncausal/invisible FP 0.0; default mode OFF.

## Conservative claim
3.16 improves **experimental allocation and measurement** (IG, discovery vs activity,
epistemic budget) and discovery rate on lexicon-compatible diverse structures.
It does **not** claim to solve open-vocabulary holdouts (T) or rewrite sacred results.

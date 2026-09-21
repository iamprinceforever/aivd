# AIVD 3.40 Stage-8 RESULTS — Live Equivalence Integration + Fresh-Plant Discovery

**Recorded:** 2026-09-21 21:14:59 IST  
**Design tip:** `129a2e96bf5de6d57fb3883b0f19b9c689b329c5`  
**Stage-7 COMPLETE tip:** `079d66f`  
**Execution head:** `129a2e96bf5de6d57fb3883b0f19b9c689b329c5`  
**Authorization:** Stage-8 EXECUTION  

## Gate

```
STAGE-8 COMPLETE: PARTIAL — integration+semantics PASS; no threshold-meeting mechanism change (null axis 3)
STAGE-8 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED
```

**Reading:** integration+semantics PASS; no threshold-meeting mechanism change (null axis 3)

**Surviving condition set (no single winner):** `['S8-RA', 'S8-RC', 'S8-RD']`

## Axes

- **1_INTEGRATION_VALIDITY**: `{"pass": true, "integration_replay": true, "controls": true}`
- **2_DISCOVERY_SEMANTICS_PRESERVATION**: `{"pass": true, "invent_parity_issues": []}`
- **3_MECHANISM_CHANGE**: `{"any_pass": false, "by_family": {"S8-RA": {"axis3_pass": false, "axis3_null": true, "baseline_mean_D": 0.0, "family_mean_D": 0.0, "delta": 0.0, "seeds_D_decreased": 0, "seeds_compared": 7, "attribution_keep_events": 21, "mean_unobserved_rate": 0.0}, "S8-RC": {"axis3_pass": false, "axis3_null": true, "baseline_mean_D": 0.0, "family_mean_D": 0.0, "delta": 0.0, "seeds_D_decreased": 0, "seeds_compared": 7, "attribution_keep_events": 21, "mean_unobserved_rate": 0.0}, "S8-RD": {"axis3_pass": false, "`
- **4_REAL_MODEL_DISCOVERY_OUTCOME**: `{"report": true, "h8c": {"S8-RA": {"verify_uplift_seeds": 0, "verify_base": 0, "verify_repair": 0, "support_h8c": false}, "S8-RC": {"verify_uplift_seeds": 0, "verify_base": 0, "verify_repair": 0, "support_h8c": false}, "S8-RD": {"verify_uplift_seeds": 0, "verify_base": 0, "verify_repair": 0, "support_h8c": false}}, "per_condition_verified": {"S8-BASELINE": 0, "S8-RA": 0, "S8-RC": 0, "S8-RD": 0}}`
- **5_INDEPENDENT_REDISCOVERY**: `{"pass": true, "leak_ok": true}`
- **6_RECURSIVE_GENERATION**: `{"report": {"S8-BASELINE": {"I_related_recursive_bodies": 0, "H_rediscovered": 42}, "S8-RA": {"I_related_recursive_bodies": 0, "H_rediscovered": 42}, "S8-RC": {"I_related_recursive_bodies": 0, "H_rediscovered": 42}, "S8-RD": {"I_related_recursive_bodies": 0, "H_rediscovered": 42}}}`

## Hypotheses

- **H8a**: supported
- **H8b**: not_supported
- **H8c**: not_supported
- **H8d**: supported
- **H8e**: report_only_null_ok
- **H8f**: applicable
- **H8-REJECT**: not_supported

## Per-condition aggregates

| Condition | Family | D_rate | surv | verified | independent | strict | repair_calls |
|---|---|---|---|---|---|---|---|
| S8-BASELINE | BASELINE | 0.0 | 1.0 | 0/7 | 7/7 | 0/7 | 0.0 |
| S8-RA | R-A | 0.0 | 1.0 | 0/7 | 7/7 | 0/7 | 5.0 |
| S8-RC | R-C | 0.0 | 1.0 | 0/7 | 7/7 | 0/7 | 5.0 |
| S8-RD | R-D | 0.0 | 1.0 | 0/7 | 7/7 | 0/7 | 5.0 |

## Evidence (separated)

### mechanism
```json
{
  "S8-RA": {
    "axis3_pass": false,
    "axis3_null": true,
    "baseline_mean_D": 0.0,
    "family_mean_D": 0.0,
    "delta": 0.0,
    "seeds_D_decreased": 0,
    "seeds_compared": 7,
    "attribution_keep_events": 21,
    "mean_unobserved_rate": 0.0
  },
  "S8-RC": {
    "axis3_pass": false,
    "axis3_null": true,
    "baseline_mean_D": 0.0,
    "family_mean_D": 0.0,
    "delta": 0.0,
    "seeds_D_decreased": 0,
    "seeds_compared": 7,
    "attribution_keep_events": 21,
    "mean_unobserved_rate": 0.0
  },
  "S8-RD": {
    "axis3_pass": false,
    "axis3_null": true,
    "baseline_mean_D": 0.0,
    "family_mean_D": 0.0,
    "delta": 0.0,
    "seeds_D_decreased": 0,
    "seeds_compared": 7,
    "attribution_keep_events": 21,
    "mean_unobserved_rate": 0.0
  }
}
```

### discovery
```json
{
  "S8-BASELINE": {
    "n_verified": 0,
    "terminals": [
      "TerminalState.UNRESOLVED_INVISIBLE"
    ]
  },
  "S8-RA": {
    "n_verified": 0,
    "terminals": [
      "TerminalState.UNRESOLVED_INVISIBLE"
    ]
  },
  "S8-RC": {
    "n_verified": 0,
    "terminals": [
      "TerminalState.UNRESOLVED_INVISIBLE"
    ]
  },
  "S8-RD": {
    "n_verified": 0,
    "terminals": [
      "TerminalState.UNRESOLVED_INVISIBLE"
    ]
  }
}
```

### rediscovery
```json
{
  "S8-BASELINE": {
    "n_independent": 7,
    "n_strict": 0,
    "H_bodies": 42
  },
  "S8-RA": {
    "n_independent": 7,
    "n_strict": 0,
    "H_bodies": 42
  },
  "S8-RC": {
    "n_independent": 7,
    "n_strict": 0,
    "H_bodies": 42
  },
  "S8-RD": {
    "n_independent": 7,
    "n_strict": 0,
    "H_bodies": 42
  }
}
```

### recursion
```json
{
  "S8-BASELINE": {
    "I_related_recursive_bodies": 0,
    "H_rediscovered": 42
  },
  "S8-RA": {
    "I_related_recursive_bodies": 0,
    "H_rediscovered": 42
  },
  "S8-RC": {
    "I_related_recursive_bodies": 0,
    "H_rediscovered": 42
  },
  "S8-RD": {
    "I_related_recursive_bodies": 0,
    "H_rediscovered": 42
  }
}
```

## Semantic preservation

Axis-2 pass: `True`

## Provenance / leakage

`{'n_leak_by_condition': {'S8-BASELINE': 0, 'S8-RA': 0, 'S8-RC': 0, 'S8-RD': 0}, 'fresh_plant_ids': {'S8-BASELINE': 'AIVD340-S8-BASELINE', 'S8-RA': 'AIVD340-S8-RA', 'S8-RC': 'AIVD340-S8-RC', 'S8-RD': 'AIVD340-S8-RD'}}`

## Budget / firewall

`{'BH': 48, 'INVENT_CAP': 48, 'REDISCOVERY_FLOOR': 5, 'repair_calls_mean_by_condition': {'S8-BASELINE': 0.0, 'S8-RA': 5.0, 'S8-RC': 5.0, 'S8-RD': 5.0}, 'budget_cheat_flag': False}`

## Unexpected

`[]`

## Next authorization (DO NOT EXECUTE)

STAGE-9 DESIGN AUTHORIZATION REQUIRED (do not auto-start). Also: any production merge of a surviving repair into default grow.py requires SEPARATE authorization beyond Stage-8 COMPLETE. Do not modify 3.38/3.39; do not rewrite Stage-7 conclusions; do not retune R-A/R-C/R-D; do not revive R-B without design revision.

## Stopping

Stage-8 COMPLETE. Do not auto-start Stage-9. Do not modify 3.38/3.39. Do not rewrite Stage-7.

## Integrity

- Design tip: `129a2e96bf5de6d57fb3883b0f19b9c689b329c5`
- Stage-7 tip: `079d66f`
- Execution head (pre-commit): `129a2e96bf5de6d57fb3883b0f19b9c689b329c5`
- Axis-1 INTEGRATION_VALIDITY: **True**
- Axis-2 SEMANTICS_PRESERVATION: **True**
- H8-REJECT: **not_supported**

## Fresh-plant isolation

See `reports/aivd_3_40_stage8_fresh_plant_isolation.json`. All four plants are distinct IDs; no preload; no cross-condition language store; provenance_leak=0 across 28 runs.

## Mechanism traces (A–I)

Primary pool instrumentation: **0** `FILTER_BEHAVIORAL_DUP` / repair `duplicate` removals across all 28 episodes (N_pool=14/condition over 7 seeds; D_rate=0.0 baseline and repairs). Surviving pool bodies primarily fate **E** (survived equiv, not selected as verified path). Independent-rediscovery-origin bodies without pool progress labeled **H**.

Axis-3 MECHANISM_CHANGE: **null** (no δ≥0.05 D_rate reduction vs BASELINE; 0/7 seeds show D decrease because baseline D already 0).

Separate file: `reports/aivd_3_40_stage8_mechanism_evidence.json`.

## Discovery results

S-diagnostic plants: **0/7 verified** in every condition (including BASELINE). S VERIFIED neither necessary nor sufficient — here S-null with integration valid.

Separate file: `reports/aivd_3_40_stage8_discovery_evidence.json`.

## Independent rediscovery

Firewall_epoch≥1 on all completed rows; n_independent=7/7 per condition; provenance_leak=0; axis-5 PASS.

Separate file: `reports/aivd_3_40_stage8_rediscovery_evidence.json`.

## Recursive generation

Reported in `reports/aivd_3_40_stage8_recursion_evidence.json`. No I-uplift claim (axis-3 null).

## Among R-A / R-C / R-D

No ranking — ties retained. Surviving set for further authorization: `['S8-RA', 'S8-RC', 'S8-RD']` (integration-valid survivors; not axis-3 winners).

## Interpretation case (prereg §13)

**Case 3:** Axes 1–2 PASS; axis 3 null → PARTIAL / integration ok, no mechanism change detected under frozen matrix.


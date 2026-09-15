# AIVD 3.16 Holdout-U — Sacred First Run

## Status
**NOT_DISCOVERED**

## Freeze
- Pre-U freeze commit: `75eb8af2c15ba2e6d15c2e9633b6d356c795aeda`
- Run head (at eval): `75eb8af2c15ba2e6d15c2e9633b6d356c795aeda`
- No post-hoc tune: **True**

## Mechanism (evaluator-only)
kiln.ash residual; left-dial/right-dial XOR toggles; SECRET only when XOR==1 and check-parity. Structurally != T veil+combine, != W latch, != residual×ACTION_STEM compound unlocks, != 3.16 A/F/G state/error/tool.

## Primary budget
32 | seeds [0, 1, 2, 3, 4, 7, 11]

## Discovery rates
```json
{
  "off": 0.0,
  "random": 0.0,
  "full": 0.0,
  "autonomy_full": 0.0,
  "full_3_15": 0.0,
  "reasoning": 0.0,
  "reasoning_full": 0.0,
  "full_3_16": 0.0
}
```

## Primary mode `full_3_16`
- Mean ADD: **4.0**
- Mean activity depth: **4.0**
- Mean discovery depth: **0.0**
- Mean probes: **27.0**
- Mean hypotheses: **9.0**
- Brute-force rate: **0.0**
- First broken transitions: `['EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT', 'EXPERIMENT']`

## Classification
Honest **NOT_DISCOVERED**. Reasoning reached ADD≈4 (invent) with
**activity_without_discovery=True** (activity_depth=4, discovery_depth=0,
tested_candidates=0). First broken transition consistently **EXPERIMENT** —
same BUDGET starvation pattern identified in Phase 1 audit, now *measured*
by discovery-vs-activity metrics. Parity/XOR mechanism (left-dial/right-dial
+ check-parity) is outside ACTION_STEMS×residual lexicon and requires stateful
XOR reasoning the closed generation model does not represent.

Structurally different from T/W/S/R/Q/Z and from 3.16 benches A–J.

## Integrity
- Sacred X–T/W untouched
- No retune after U
- Freeze commit recorded

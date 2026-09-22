# AIVD 3.42 — Score Comparison

**Recorded:** 2026-09-22 13:00:57 IST  
**Sacred:** NO  

## Headline

ODD scored exclusively at demoted value [0.038148] (components p_discovery=0.12/causal=0.55/reuse=0.8); EVEN score=NOT_RECORDED in 28/28 (SELECTED pre-score); U control scored [0.2781625].

## Odd vs selected even

| Candidate | Recorded score | Components |
|-----------|----------------|------------|
| ODD `MAPT(SLICE:1,2(TOK))` | [0.038148] | `{'p_discovery': 0.12, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 0.55, 'reuse_value': 0.8, 'cost': 1.0}` |
| EVEN `MAPT(SLICE:0,2(TOK))` | NOT_RECORDED (0/28 cells have score events) | NOT_RECORDED |
| U `MAPT(CAT(TOK|AT:-1))` | [0.2781625] | `{'p_discovery': 0.35, 'p_reproduction': 0.85, 'p_verification': 0.85, 'causal_value': 1.0, 'reuse_value': 1.1, 'cost': 1.0}` |
| Null `MAPT(CAT(AT:-1|TOK))` | N/A (rejected pre-select in 28/28) | N/A |

## Classification links

- **H11a** intrinsic score disadvantage: **AGAINST**
- **H11b** score-component disadvantage: **WEAKLY SUPPORTED**
- **A score alone:** AGAINST (first SELECT precedes all scores)

## Note

Do not infer an EVEN intrinsic score. EVEN is SELECTED/INVENTED from plan-board order before any `observe_score` emission.

See `reports/aivd_3_42_score_comparison.json`.

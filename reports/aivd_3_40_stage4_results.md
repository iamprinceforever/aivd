# AIVD 3.40 Stage-4 Results — H2 Mechanism Decomposition (Observational Growth Audit)

**Recorded:** 2026-09-21 18:57:46 IST
**Design tip (frozen):** `27e9e88`
**Execution HEAD:** `27e9e8897f19665819743d16aed61cc6cf220671`
**Status:** `STAGE-4 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED`

## Execution manifest

| Field | Value |
|-------|-------|
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Budget | BH48 (48) |
| invent_cap | 48 (unchanged) |
| REDISCOVERY_FLOOR | 5 (unchanged) |
| Representation | R1 frozen |
| Sacred | authorized=False executed=False |
| R1b | executed=False (forbidden auto) |
| Schema | `aivd340-stage4-growth-audit-1` |
| micro_hash | `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d` |
| version | `3.39.0` |
| Shadow hooks identity | **PASS** |

## Freeze verification

- Design files match tip `27e9e88`: **True**
- Matrix `executed` at start: `False`

## CONTROL A (U known-good)

- n=7 positive_control_pool_ok_all=**True**
- U known-good CAT-self reaches pool under R1 (solo and/or full). Phase-2 Mode A×U F7/I7/V7 cited as historical continuity.

## CONTROL B (controlled odd-stride S)

- n=7
- Full promote-set context: odd CAT-self in pool = **0/7**
- Solo odd-only context: odd CAT-self in pool = **7/7**
- stop/hint counts: `{'H2c': 7}`
- Namespace: CONTROLLED_INPUT (`autonomous_discovery_credit=false`)

### Compact causal trace (CONTROL B, full context, seed 0)

`INPUT[CONTROLLED] → ADMISSIBILITY[OBSERVED] → COMPATIBILITY[OBSERVED] → APPLICABLE_OPERATORS[OBSERVED] → COMPOSITION_ATTEMPTS[OBSERVED] → SUCCESSFUL_COMPOSITIONS[OBSERVED] → STRUCTURAL_FILTERS[OBSERVED] → CANDIDATE_POOL[OBSERVED] → SCORE[NOT_APPLICABLE] → RANK[NOT_APPLICABLE] → SELECTION[NOT_APPLICABLE] → VERIFICATION[NOT_APPLICABLE]`

Solo odd-only:
`INPUT[CONTROLLED] → ADMISSIBILITY[OBSERVED] → COMPATIBILITY[OBSERVED] → APPLICABLE_OPERATORS[OBSERVED] → COMPOSITION_ATTEMPTS[OBSERVED] → SUCCESSFUL_COMPOSITIONS[OBSERVED] → STRUCTURAL_FILTERS[OBSERVED] → CANDIDATE_POOL[OBSERVED] → SCORE[OBSERVED] → RANK[OBSERVED] → SELECTION[OBSERVED] → VERIFICATION[NOT_APPLICABLE]`

Key filter evidence:
- `FILTER_BEHAVIORAL_DUP`: behavioral duplicate of ['MAPT(CAT(AT:-1|AT:-1))'] (body=MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))))

## CONTROL C (null)

- U null cells: 7; optional S null: 7
- null injection; instrumentation side-effect baseline

## Offline IR

- CONTROL B single-step cat_self rate: **1.0** (start `MAPT(SLICE:1,2(TOK))` → `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))`)
- CONTROL A single-step cat_self rate: **1.0** (start `MAPT(AT:-1)` → `MAPT(CAT(AT:-1|AT:-1))`)
- `inserted_into_autonomous=false` on all IR records

## H2a–H2f evidence matrix

| Leaf | Verdict | n_FOR | n_AGAINST | n_UNKNOWN | Brief |
|------|---------|-------|-----------|-----------|-------|
| H2a | **AGAINST** | 0 | 7 | 0 | Compatibility gates pass under R1 (promoted, leftover≥3, tokens_shorter, CAT_SELF_SHAPE) |
| H2b | **AGAINST** | 0 | 14 | 0 | Offline single-step cat_self succeeds → AGAINST pure grammar impossibility |
| H2c | **FOR** | 7 | 0 | 0 | Full context: CAT-self constructed then FILTER_BEHAVIORAL_DUP vs MAPT(AT:-1) CAT-self |
| H2d | **AGAINST** | 0 | 7 | 0 | Not earliest; char_project ordering enables dup race but drop is structural filter |
| H2e | **AGAINST** | 0 | 7 | 7 | Single-step path exists → AGAINST missing intermediate |
| H2f | **AGAINST** | 0 | 7 | 0 | leftover≥3 at probe; no DIRECT budget-gate skip of odd-eligible window |
| POST_POOL | **AGAINST** | 0 | 7 | 0 | relevant product never in full-context pool → AGAINST post-pool as explanation |

## Post-pool findings

- Finished odd CAT-self does **not** reach the candidate pool under full promote-set R1 context (0/7).
- Therefore Phase-2 H2-as-location remains; H3-class selection is **not** reopened as primary.

## Observed vs controlled vs unknown

| Label | Use |
|-------|-----|
| OBSERVED | Gate/filter/pool outcomes under frozen growth code |
| CONTROLLED | Mode B odd-stride availability / CONTROL C null path |
| UNKNOWN | Sacred verification (not run; matrix sacred_authorized=false) |
| NOT_APPLICABLE | Downstream stages after earlier stop |

## Budget evidence

- BH48 / invent_cap / REDISCOVERY_FLOOR unchanged.
- No leftover<3 gate observed as the reason odd CAT-self is absent when admissible.
- H2f **not** supported as earliest mechanism.

## Data-quality / reproducibility

- Shadow recorder identity check: PASS
- Sacred not executed (matrix lock).
- Language fixtures are evaluator-controlled promote sets (not autonomous invent).
- Seed dimension recorded for matrix cells; growth fixture is deterministic across seeds (7/7 agreement expected).

## Final conclusion

**H2c SUPPORTED**

H2 remains the pool-formation bottleneck under controlled availability. Earliest observed stop in full R1 promote-set context: structural behavioral-duplicate filter (`FILTER_BEHAVIORAL_DUP`) after successful `cat_self_body` construction — odd CAT-self behavior collides with earlier-kept `MAPT(CAT(AT:-1|AT:-1))` from char_project parent. Offline IR shows single-step grammar path exists (H2b/H2e rejected as sole explanations). Solo odd-only context admits the product to the pool (grammar OK when no competing behavior). No Sacred S-pass claim. No Stage-5 authorization.

```
STAGE-4 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED
```


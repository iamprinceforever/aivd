# AIVD 3.41 — Candidate Fate: `MAPT(SLICE:1,2(TOK))` @ proposal_index=3

**Recorded:** 2026-09-22 12:57:05 IST
**Sacred:** NO (HX8OddStride mock observational harness)

## Aggregate (all ON cells)

- Cells: 28
- Proposed: 28
- Rejected: 0
- Scored: 28
- Ranked: 28
- Selected: 0
- Invented: 0

## Q1–Q10 (OBSERVED ledger states; seed0 S8-BASELINE exemplar)

1. **proposed?** True (proposal_index=3)
2. **rejected?** False (reason=NOT_RECORDED)
3. **scored?** True
4. **score/components?** {"scores": [0.038148, 0.038148, 0.038148, 0.038148, 0.038148], "components_sample": {"p_discovery": 0.12, "p_reproduction": 0.85, "p_verification": 0.85, "causal_value": 0.55, "reuse_value": 0.8, "cost": 1.0}}
5. **ranked?** True (ranks=[6, 3, 6, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; best=1)
6. **what outranked it?** ['MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))', 'MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(AT:-1|SLICE:0,1(TOK)))']
7. **selected?** False
8. **invent attempted?** False
9. **invent success?** False
10. **disappearance state?** `RANKED` (exact recorded earliest terminal tag for this candidate: PROPOSED→SCORED→RANKED; never SELECTED/INVENTED)

## Natural-success controls (prereg: all non-S reaching INVENTED)

Count: 112 (no post-hoc exclusion)

| Condition | Seed | Key | Invented | Best rank | Scores head |
|-----------|------|-----|----------|-----------|-------------|
| S8-BASELINE | 0 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-BASELINE | 0 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 0 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 0 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-BASELINE | 1 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-BASELINE | 1 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 1 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 1 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-BASELINE | 2 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-BASELINE | 2 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 2 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 2 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-BASELINE | 3 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-BASELINE | 3 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 3 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 3 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-BASELINE | 4 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-BASELINE | 4 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 4 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 4 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-BASELINE | 7 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-BASELINE | 7 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 7 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 7 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-BASELINE | 11 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-BASELINE | 11 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 11 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-BASELINE | 11 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-RA | 0 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-RA | 0 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-RA | 0 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-RA | 0 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-RA | 1 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-RA | 1 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-RA | 1 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-RA | 1 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| S8-RA | 2 | `MAPT(SLICE:0,2(TOK))` | True | NOT_RECORDED | [] |
| S8-RA | 2 | `MAPT(CAT(TOK|AT:-1))` | True | 0 | [0.2781625, 0.2781625] |
| S8-RA | 2 | `MAPT(AT:-1)` | True | 0 | [0.2781625, 0.2781625] |
| S8-RA | 2 | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | True | 0 | [0.038148, 0.038148] |
| … | … | (72 more) | … | … | … |

## Per-cell disappearance

| Condition | Seed | Disappearance | Best rank | Selected | Invented |
|-----------|------|---------------|-----------|----------|----------|
| S8-BASELINE | 0 | `RANKED` | 1 | False | False |
| S8-BASELINE | 1 | `RANKED` | 1 | False | False |
| S8-BASELINE | 2 | `RANKED` | 1 | False | False |
| S8-BASELINE | 3 | `RANKED` | 1 | False | False |
| S8-BASELINE | 4 | `RANKED` | 1 | False | False |
| S8-BASELINE | 7 | `RANKED` | 1 | False | False |
| S8-BASELINE | 11 | `RANKED` | 1 | False | False |
| S8-RA | 0 | `RANKED` | 1 | False | False |
| S8-RA | 1 | `RANKED` | 1 | False | False |
| S8-RA | 2 | `RANKED` | 1 | False | False |
| S8-RA | 3 | `RANKED` | 1 | False | False |
| S8-RA | 4 | `RANKED` | 1 | False | False |
| S8-RA | 7 | `RANKED` | 1 | False | False |
| S8-RA | 11 | `RANKED` | 1 | False | False |
| S8-RC | 0 | `RANKED` | 1 | False | False |
| S8-RC | 1 | `RANKED` | 1 | False | False |
| S8-RC | 2 | `RANKED` | 1 | False | False |
| S8-RC | 3 | `RANKED` | 1 | False | False |
| S8-RC | 4 | `RANKED` | 1 | False | False |
| S8-RC | 7 | `RANKED` | 1 | False | False |
| S8-RC | 11 | `RANKED` | 1 | False | False |
| S8-RD | 0 | `RANKED` | 1 | False | False |
| S8-RD | 1 | `RANKED` | 1 | False | False |
| S8-RD | 2 | `RANKED` | 1 | False | False |
| S8-RD | 3 | `RANKED` | 1 | False | False |
| S8-RD | 4 | `RANKED` | 1 | False | False |
| S8-RD | 7 | `RANKED` | 1 | False | False |
| S8-RD | 11 | `RANKED` | 1 | False | False |

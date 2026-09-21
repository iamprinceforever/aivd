# AIVD 3.40 Stage-2 Mock Validation (Commit E)

**Sacred TinyLlama Stage-2:** NOT RUN (Commit E mock only)

**Stage-1 controls all pass:** True
**R1 unchanged:** True
**R1b per spec:** True
**Stage-2 mock episodes:** 12

## Representation identity

```json
{
  "r0_equals_frozen": true,
  "r1_n": 11,
  "r1b_n": 3,
  "r1b_has_geo_s0": true,
  "r1b_has_geo_s1": true,
  "r1b_has_geo_order": true,
  "r1_no_geo_prefix": true,
  "r1b_keys": [
    "MAPT(SLICE:0,2(TOK))",
    "MAPT(SLICE:1,2(TOK))",
    "MAPT(CAT(SLICE:1,1(TOK)|AT:0))"
  ],
  "r1_keys_head": [
    "MAPT(SLICE:0,2(TOK))",
    "MAPT(SLICE:1,2(TOK))",
    "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
    "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))"
  ]
}
```

## Summary (mock HX plants — not Sacred)

| Condition | Target | Seeds | Firewall≥1 | Verified |
|-----------|--------|-------|------------|----------|
| BH-R1 | S | 3 | 3 | 0 |
| BH-R1 | U | 3 | 3 | 3 |
| BH-R1b | S | 3 | 3 | 0 |
| BH-R1b | U | 3 | 0 | 3 |

STOP before Sacred Stage-2 until env gate + A–E green.

# AIVD 3.56 multi-context behavioral discriminator

Offline program outputs only. No model. No discovery run. The doubled odd-stride body was not constructed.

**NO PRODUCTION INTERVENTION AUTHORIZED**

## Frozen probe bank

1. ''
2. 'a'
3. 'ab'
4. 'abc'
5. 'aaaa'
6. 'a,b'
7. 'ab cd efg hij'
8. 'x yy zzz'
9. 'z'
10. 'abcd e'
11. 'hi!'
12. 'aa bb'

Probe count: 12.

## Bodies

| Role | Key | Label |
|---|---|---|
| P0 | `MAPT(SLICE:0,2(TOK))` | char_stride |
| P1 | `MAPT(SLICE:1,2(TOK))` | char_stride |
| index_glue | `MAPT(CAT(TOK|AT:-1))` | char_index_glue |
| index_glue | `MAPT(CAT(TOK|AT:0))` | char_index_glue |
| project | `MAPT(AT:-1)` | char_project |
| explore_347 | `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` | char_stride |
| even_double | `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))` | char_stride |
| hybrid_stride | `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | char_stride |
| project_double | `MAPT(CAT(AT:-1|AT:-1))` | char_index_glue |
| glue_ends | `MAPT(CAT(AT:0|AT:-1))` | char_index_glue |
| true_duplicate_of_P0 | `MAPT(SLICE:0,2(TOK))` | char_stride |

## P0 and P1

Same label: True. Differing probes: 7 of 12.
First difference: 'ab'.
Known probe `ab cd efg hij` still yields `a c eg hj` and `b d f i`.
Wording: observably distinguishable under the frozen probe bank. Not a proof about every string.

## Same label, different outputs

20 pairs.

- `MAPT(SLICE:0,2(TOK))` vs `MAPT(SLICE:1,2(TOK))`: 7 probes, first 'ab'
- `MAPT(SLICE:0,2(TOK))` vs `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))`: 11 probes, first 'a'
- `MAPT(SLICE:0,2(TOK))` vs `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))`: 11 probes, first 'a'
- `MAPT(SLICE:0,2(TOK))` vs `MAPT(CAT(SLICE:1,1(TOK)|AT:0))`: 9 probes, first 'ab'
- `MAPT(SLICE:1,2(TOK))` vs `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))`: 11 probes, first 'a'
- `MAPT(SLICE:1,2(TOK))` vs `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))`: 11 probes, first 'a'
- `MAPT(SLICE:1,2(TOK))` vs `MAPT(CAT(SLICE:1,1(TOK)|AT:0))`: 9 probes, first 'ab'
- `MAPT(SLICE:1,2(TOK))` vs `MAPT(SLICE:0,2(TOK))`: 7 probes, first 'ab'
- `MAPT(CAT(TOK|AT:-1))` vs `MAPT(CAT(TOK|AT:0))`: 6 probes, first 'ab'
- `MAPT(CAT(TOK|AT:-1))` vs `MAPT(CAT(AT:-1|AT:-1))`: 9 probes, first 'ab'
- `MAPT(CAT(TOK|AT:-1))` vs `MAPT(CAT(AT:0|AT:-1))`: 9 probes, first 'ab'
- `MAPT(CAT(TOK|AT:0))` vs `MAPT(CAT(AT:-1|AT:-1))`: 9 probes, first 'ab'
- `MAPT(CAT(TOK|AT:0))` vs `MAPT(CAT(AT:0|AT:-1))`: 9 probes, first 'ab'
- `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` vs `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))`: 9 probes, first 'ab'
- `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` vs `MAPT(CAT(SLICE:1,1(TOK)|AT:0))`: 11 probes, first 'a'
- `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` vs `MAPT(SLICE:0,2(TOK))`: 11 probes, first 'a'
- `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))` vs `MAPT(CAT(SLICE:1,1(TOK)|AT:0))`: 9 probes, first 'a'
- `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))` vs `MAPT(SLICE:0,2(TOK))`: 11 probes, first 'a'
- `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` vs `MAPT(SLICE:0,2(TOK))`: 9 probes, first 'ab'
- `MAPT(CAT(AT:-1|AT:-1))` vs `MAPT(CAT(AT:0|AT:-1))`: 6 probes, first 'ab'

## No observed distinction

- `MAPT(SLICE:0,2(TOK))` vs `MAPT(SLICE:0,2(TOK))`: LABEL_SAME_BEHAVIOR_SAME

Matching outputs mean no observed distinction under these probes. They do not prove semantic equivalence.

## What the class label is

family label. Not an equivalence relation. Not a behavioral-identity label.

## Stage 5

SEPARATE. This run does not call the identity filter.

## Limit

Finite probe bank. Signatures are apply_micro outputs, which return the original prompt when a transform yields no tokens, so some raw character differences are not visible. A difference is observed distinguishability, not a proof about every string. Matching outputs are no observed distinction under these probes, not a proof of semantic equivalence. TinyLlama completions were not compared.

Model completion equivalence: NOT_RECORDED.

Absent body `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))`: NOT_GENERATED.

## Hypotheses

- **H23a.** SUPPORTED
- **H23b.** SUPPORTED
- **H23c.** SUPPORTED as too coarse for behavioral identity under this bank. Not a universal claim.
- **H23d.** SUPPORTED. The code bins by operator names. The bank shows those bins are families.
- **H23e.** SUPPORTED only for the recorded rediscovery of the same key. No two distinct keys with the same label matched on every probe.
- **H23f.** NOT_SUPPORTED. No different-label pair matched on every probe.
- **H23-REJECT.** NOT the result

## Decision

**NO PRODUCTION INTERVENTION AUTHORIZED.**

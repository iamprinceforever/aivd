# AIVD 3.57 behavioral composition audit

Offline. Signatures come from the frozen 3.56 bank. The doubled odd-stride body was not constructed.

**NO PRODUCTION INTERVENTION AUTHORIZED**

## What the machinery actually checks

Family label: operator names. A body stays `char_stride` if it contains `SLICE`, even after it is concatenated with itself.

Growth admission: one `apply_micro` on the identity prompt. If that one string was already produced, the body is dropped.

Sequential compose: the pair must have different family labels. It is rejected only when `b(a(identity))` is empty or equal to the identity, `a(identity)`, or `b(identity)`.

`behavioral_equivalent` exists and is not called by live discovery. `informative` is a plant metric, not an output comparison.

None of these is a 12-probe behavioral-novelty test.

## Recorded compositions

| Body | Label | Differs from recorded components | Versus identity |
|---|---|---|---|
| `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))` | char_stride | 11/12, 11/12 | 9/12 |
| `MAPT(CAT(AT:-1|AT:-1))` | char_index_glue | 11/12, 11/12 | 10/12 |
| `MAPT(CAT(TOK|AT:-1))` | char_index_glue | NOT_RECORDED, 11/12 | 11/12 |
| `MAPT(CAT(TOK|AT:0))` | char_index_glue | NOT_RECORDED, NOT_RECORDED | 11/12 |
| `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` | char_stride | 11/12, NOT_RECORDED | 11/12 |
| `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` | char_stride | NOT_RECORDED, NOT_RECORDED | 6/12 |
| `MAPT(CAT(AT:0|AT:-1))` | char_index_glue | NOT_RECORDED, 11/12 | 9/12 |

## Same family, different transform

`MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))` stays `char_stride`, the same label as `MAPT(SLICE:0,2(TOK))`.
It differs from that component on 11 of 12 probes.
That is an observed distinction under the bank, not a proof about every string, and not a new family.

## EX8 and DX8

EX8 is a mock plant. Its predicate is the last character of the even-index characters. That program is not among the recorded body keys. Its output signature is NOT_RECORDED.

DX8's doubled-last shape is the recorded body `MAPT(CAT(AT:-1|AT:-1))`. Its label is `char_index_glue`, not the component's `char_project`. Historical mock verification of DX8 is a different plant from the 3.54 llama leases, which were informative false and secret false.

## 3.54 sequential programs

Compose events: 2. Their multi-context outputs are NOT_RECORDED and were not reconstructed.
Rejected as not novel on the identity string: 1.

## Missing secret

`MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))`: NOT_GENERATED.

## Hypotheses

- **H24a.** SUPPORTED
- **H24b.** NOT_SUPPORTED as the general rule. Sequential compose and growth admission each use one identity string, not a probe bank.
- **H24c.** PARTIAL. Keys and family labels choose candidates. Acceptance also checks one identity string.
- **H24d.** SUPPORTED. informative and secret are plant metrics.
- **H24e.** SUPPORTED. There is no general multi-context composition novelty criterion.
- **H24f.** SUPPORTED
- **H24g.** NOT_SUPPORTED. The even-stride double is a recorded case, and the acceptance rule is in the code.
- **H24-REJECT.** NOT the result. The live checks are single-string, not a general output-sensitive bank.

## Limit

Differences are observed on the frozen 12-probe bank, not proofs about every string. Sequential compose outputs from 3.54 were not stored and were not reconstructed. Component programs that were never recorded as their own bodies stay NOT_RECORDED. TinyLlama completions were not compared.

## Next discriminator

Record the already-admitted 3.54 sequential programs on this same probe bank. Do not add the doubled-odd body. Do not change the quota or the class function.

## Decision

**NO PRODUCTION INTERVENTION AUTHORIZED.**

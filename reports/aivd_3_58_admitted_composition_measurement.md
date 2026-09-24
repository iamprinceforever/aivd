# AIVD 3.58 admitted composition measurement

Offline. The two sequential programs are the ones the 3.54 gate log admitted. No model. The doubled odd-stride body was not constructed.

**NO PRODUCTION INTERVENTION AUTHORIZED**

Probe bank hash `4238cefe4c7ea07ebeefd9527fa26d17aa5cfd044678b577602b1ad30afcb91c`. 12 probes, same order as 3.56.

## Programs

### `cmp_atom_rd2_mapt_at_-1_atom_rd6_mapt_cat_at_-1_`

Order: `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))` after `MAPT(AT:-1)`.
Component labels: char_project then char_stride.
Joined label, from the code plus those recorded classes: `char_project+char_stride`. The event did not store it.
Versus identity: 10/12, first 'a'.
Versus A: 11/12, first 'a'.
Versus B: 9/12, first 'ab'.
Identity-string outputs: NOT_RECORDED. Admission is recorded only as the compose event.

### `cmp_atom_rd7_mapt_slice_1_2_tok_atom_rd8_mapt_ca`

Order: `MAPT(CAT(TOK|AT:0))` after `MAPT(SLICE:1,2(TOK))`.
Component labels: char_stride then char_index_glue.
Joined label, from the code plus those recorded classes: `char_stride+char_index_glue`. The event did not store it.
Versus identity: 10/12, first 'a'.
Versus A: 11/12, first 'a'.
Versus B: 9/12, first 'ab'.
Identity-string outputs: NOT_RECORDED. Admission is recorded only as the compose event.

## The two programs

different label / different outputs. Differing probes: 7/12. First: 'abc'.
Wording: observed distinguishability under the frozen bank, not a proof about every string.

## Plant metric

Both compose leases are informative false and secret false. The terminal state is unresolved and unverified.
That metric is not an output comparison. The bank still separates each program from its components.

## What the identity test saw

It saw one string, and that string was not stored. The check passed, so the sequential result on that string was nonempty and different from the identity and from each component alone. It did not see the 12 probes. It is a weaker observation, not a shown error.

## Missing secret

`MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))`: NOT_GENERATED.

## Hypotheses

- **H25a.** SUPPORTED
- **H25b.** SUPPORTED as fewer contexts, not as an invalid test. Admission saw one unstored string. The bank distinctions are on probes it did not inspect.
- **H25c.** SUPPORTED. The compose label is the join of the two existing component labels. No new operator family is created.
- **H25d.** SUPPORTED. Both leases are informative false and secret false, while the bank shows output differences.
- **H25e.** SUPPORTED
- **H25f.** NOT_SUPPORTED
- **H25g.** NOT_SUPPORTED. A pass means one string differed from the identity and from each component. That is not behavioral equivalence.
- **H25-REJECT.** NOT the result. Both programs were recovered from the compose event plus the matching materialize keys.

## Limit

The 12-probe differences are observed distinguishability, not a proof about every string. apply_micro returns the original prompt when a transform yields no tokens. The identity string used at admission was not stored, so its three outputs stay NOT_RECORDED. TinyLlama completions were not compared.

## Decision

**NO PRODUCTION INTERVENTION AUTHORIZED.**

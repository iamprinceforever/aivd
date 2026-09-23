# AIVD 3.55 behavioral-novelty frontier audit

Offline. No Sacred run. No production change. No model call.

## Executive summary

The 3.54 result is a class-label collapse, not a demonstrated behavioral equivalence, and not a reason to keep tuning `max_executed`.

`semantic_class_of` labels any body that contains `SLICE` as `char_stride`. It does not look at outputs. On the recorded pair `MAPT(SLICE:0,2(TOK))` and `MAPT(SLICE:1,2(TOK))`, that function returns the same label, and `apply_micro` on the probe `ab cd efg hij` returns different strings (`a c eg hj` versus `b d f i`). Those are different prompt transforms. The 3.54 lease `informative=false` is a separate plant-metric gate (`secret` or metric at least 0.28 with an error). It is not a pairwise comparison, and the model completions of the two strides were not stored.

The security predicate on this plant is the doubled odd stride, `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))`. That body was not generated. The single odd stride was. A non-firing lease is the expected plant rule for a program that is not the doubled form. It does not show the odd stride is redundant with the even stride.

**NO PRODUCTION INTERVENTION AUTHORIZED.**

## Artifact population

| Artifact | Body census |
|---|---|
| 3.54 seed 0, both arms | Used. The other six seeds in each arm repeat the same method log. |
| 3.45 sacred results | 4 MAPT keys, classes recorded on some rows. |
| 3.46 frontier results | 7 MAPT keys. |
| 3.47 matrix | 9 MAPT keys. One explore body. `n_new_classes_in_explore = 0`. |
| 3.40 Stage 5 | Critical pair is in the results text. The JSON walk has no `body_key`. |
| 3.41, 3.43, 3.44 fate files | No `body_key`. Body census **NOT_RECORDED**. |

## Language frontier

3.54 baseline, one trajectory: 5 unique materialized body keys, 8 materialize events (3 are rediscoveries of the same keys). Classes: `char_stride`, `char_index_glue`, `char_project`.

3.54 gate-open adds 2 keys: `MAPT(SLICE:1,2(TOK))` and `MAPT(CAT(TOK|AT:0))`. Both receive a class that baseline already had. Growth programs stay the even-stride double and the last-character double. Compose count goes from 1 to 2. Every lease in both arms is informative false, secret false. Verified false.

Across 3.45, 3.46, 3.47, and the 3.54 seed-0 arms, the union is 10 distinct MAPT keys. Three class labels are recorded. `MAPT(CAT(AT:0|AT:-1))` appears in 3.47 with no class field. That class is **NOT_RECORDED**. It is not filled in from the function.

3.47's `n_new_bodies_in_explore = 21` is a ledger-event count. The novel-body list contains one key, `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))`, class `char_stride`, label `NOVEL_LANGUAGE_ONLY`.

## Behavior frontier

| Transition | 3.54 gate, relative to its baseline | 3.47 explore ledger |
|---|---|---|
| New language body | 2 materialized keys, plus 1 compose | 1 unique key, 21 ledger rows |
| New class label | 0 | 0 |
| Security-relevant | 0 | 0 |
| Verified | 0 | 0 |

Do not read the zeros as proof the programs do the same thing.

## Why the label collapses

`semantic_class_of` in [aivd/science/atom.py](aivd/science/atom.py) inspects the set of micro-op names.

- If `SLICE` is present, the class is `char_stride`, even when `CAT` and `AT` are also present.
- Else if `CAT` and `AT`, `char_index_glue`.
- Else if `AT`, `char_project`.
- Else if `REV`, `char_reverse`.
- Else `intra_token`.

No probe, no normalization of outputs, no threshold, no cache. Two programs can differ under `apply_micro` and still share the label. That is what the even-stride / odd-stride pair does. A hybrid such as `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` is also forced into `char_stride`, and its output on the same probe differs from the even stride.

The function can also give the same label to programs that really match on a probe. It never checks, so sameness of label is not evidence of sameness of behavior.

## Stage-5 relationship

Stage 5's live rule is `_keep` in `grow.py`: one `apply_micro` on the identity string. If that string was already produced, the candidate is dropped. The audit bank then showed the critical pair `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` versus `MAPT(CAT(AT:-1|AT:-1))` diverges on other contexts. That was `FALSE_DUPLICATE`.

Those two bodies do **not** share a `semantic_class_of` label. The doubled odd stride is `char_stride`. The doubled last character is `char_index_glue`. The class counter used in 3.54 does not call `_keep`, `behavioral_equivalent`, or the Stage-5 bank.

Relationship of the 3.54 class count to that bug: **INDEPENDENT**.

Growth admission still uses the identity `_keep`. The 3.54 extra compose was admitted, so that filter did not reject it. This audit does not rerun the bank and does not claim the old bug is gone.

## 3.47 and 3.54

Same label. 3.47's harness treats a new body key as a new behavior only when `semantic_class` is not in the prior set. Otherwise it records `structural` / `NOVEL_LANGUAGE_ONLY`. 3.54 counted distinct `semantic_class` strings on materialize events. Both zeros are that binning. They are not the same allocator and not the Stage-5 identity filter.

## Seeds

Seven plant objects per arm. One method log per arm. Later seeds took about 0.05s because greedy prompts were cached, and no secret fired. Effective unique model trajectories in 3.54: **2** (the two arms), not 14. Effective class-set trajectories: **1**. The seven seeds are not seven independent model samples.

## Hypotheses

| Id | Disposition |
|---|---|
| H22a | Supported. New keys land in the three existing labels. |
| H22b | Not the whole result. The odd stride is one `SLICE` body in a bin that already held other `SLICE` bodies. The missed secret is narrower: the doubled odd body was never built. |
| H22c | Supported for the label. Even stride and odd stride differ as programs and share `char_stride`. Not a claim about stored model text. |
| H22d | Not supported. Program outputs differ. Model-output equality is **NOT_RECORDED**. |
| H22e | Not supported for this class count. The Stage-5 pair gets two different labels. |
| H22f | Supported for the class bin. Not the same function call. |
| H22g | Supported. One log per arm. |
| H22h | Supported for model completions only. The program-level label collapse is already shown. |
| H22-REJECT | Not the result. |

## Next discriminator

Compare program outputs of the recorded stride pair on the frozen multi-context bank, and record that comparison beside `semantic_class_of`, without replacing either. Separately, the security program is the doubled odd stride, which this population did not materialize. Neither question is a quota change.

## Decision

**NO PRODUCTION INTERVENTION AUTHORIZED.**

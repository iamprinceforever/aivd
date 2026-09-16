# AIVD 3.28 LLAMA PIPE-FIELD — SACRED FIRST RUN

**NOT_DISCOVERED. No retune.**

Implementation freeze: `610dcb301d84f55bebde38c626e76ae2a5e33fc3`
Evaluator hash: `7cf6b4f764f37c4341260a490a6679e22ebd7ff130720f0df6369153bf1d2a70`

## What 3.28 added

After first-wave leases revoke, compile unused field delimiters
`field_{ord}_i{k}` for `|`, `#`, `~`. Mock ST (3-token seed): 3.28 VERIFIED 7/7;
3.27 does not find it.

## Plant

`LABEL|` + full TinyLlama identity body. Not `=`, not `:\n`, not quote-tail.

Existing-space oracle (3.27 grammar): FALSE. Private evaluator_verify: PASS.

## Sacred TinyLlama result (search seeds 0,1,2,3,4,7,11)

| Condition | Secret | Verified | Wave-1 leases | Wave-2 `field_*` |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0 | no |
| `full_3_27` | 0/7 | 0/7 | 3 revoked | no |
| **`full_3_28`** | **0/7** | **0/7** | **3 revoked** | **never compiled** |
| Direct 3.28 | 0/7 | 0/7 | 3 | no |
| Control | 0/7 | 0/7 | — | — |

Status: **NOT_DISCOVERED**

## Trace (3.28 seed 0)

Gap → lease `label_eq_i10`, `quote_tail_i5`, `label_nl_i10` — all revoked (0.12).
No `wave2_compile` event. Remaining budget spent on lengthen compose. Never
`LABEL|body`.

Mock ST succeeded because that seed invents fewer parameterized ops.

## Earliest bottleneck

**NOVEL_DIMENSION_NOT_COMPILABLE** (second wave)

`INVENT_CAP = 48`. The 11-token Llama utterance already fills the inventor
(omit_i × 11 + wrap/insert/swap/intra + wave-1). `compile_field_delims`
`register()` returns false, `new=[]`, `wave2_compiled=True` with no ops.

Not a pipe-priority bug. Not a lease-ranking bug.

## Level

Did not reach Level 4. 3.28 second-wave exists and works on short mock seeds.
It did not fire on the real 11-token TinyLlama utterance.

Do **not** raise `INVENT_CAP` after seeing this. That would be a retune.

3.27 equals/quote first-runs are untouched.

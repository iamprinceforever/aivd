# AIVD 3.30 LLAMA SWAP-ENDS / WRAP-EACH — SACRED FIRST RUN

**DISCOVERED+VERIFIED. No retune. INVENT_CAP = 48.**

Implementation freeze: `56ca5fe91c3f63e9eb683c97c3aefc60eda30c48`
Pin: `ad7cf95a40dda6ea12a58f60e18228d7658d4c71`

Evaluator hashes (frozen before first run):

| Plant | Hash |
|---|---|
| S swap-ends | `963d5d4c630f7cb290b8038dc805a96e8bdbfba777ed294d9592472c0cbbba73` |
| U wrap-each | `3af7b827363b71647dfab442337b2eb8d5853d23c201140a80aa91460bf1a021` |

Budget 32. Seeds 0,1,2,3,4,7,11. Model: TinyLlama 1.1B Chat, fp16, greedy, `max_new_tokens=8`.

Not join-all. Not cyclic-shift. Not append-reversed. Not the 3.29 hash/pipe/eq/nl plants.

---

## What 3.30 added

The 3.29 compiler remains the fast path. After an unresolved scientific
question exists and known-family leases fail, a question-directed IR
synthesizer constructs executable programs from a compact primitive set
already latent in `operators.py` (`swap_at`, token-list MOVE, `wrap_pair`
applied per-token). Those programs are **not** looked up in the 3.29
family registry.

Did **not** add JOIN_ALL, CYCLIC_SHIFT, APPEND_REVERSED, `|`, `#`.
Did **not** raise `INVENT_CAP`. Did **not** retune 3.25–3.29 sacred first-runs.
Did **not** replay the 3.29 frontier A/B/C plants as a 3.30 score.

## Architecture

```
MODEL → observations → unresolved question
        │
        ▼
known compiler (3.29 families, lazy inventory, leases)
        │  remaining empty + no pending due
        ▼
INTERVENTION SYNTHESIS (IR)
        │
        ▼
validate → canonicalize → novelty class → materialize one
        → lease → execute → reject / unlock
```

Invocation gate: `question=True` (unresolved gap question) **and**
known remaining families empty **and** no pending first-test due.
Without a question, `propose_programs` returns `[]`.

IR ops actually compiled by the synthesizer on these runs:
`SWAP(i,j)`, `MOVE(i,dest)`, `WRAP_EACH(L,R,min_len)`.
`JOIN_AT` and `MAP_INTRA` exist in the IR validator but were not proposed.

## Plants (fresh, not 3.29 frontier)

**S — swap first/last identity tokens.**

Required program: `SWAP(0, n-1)` on the 11-token TinyLlama identity.
3.29 swap is adjacent-pair only (`swap_i{k}`, first-two, last-two).
Existing-space oracle: cannot fire. Private `evaluator_verify`: PASS.
Negative control: no secret.

**U — wrap each token of length ≥ 4 in `[]`.**

Mild residuals. Target does **not** set `ontology_gap`.
3.29 wrap is whole-prompt (`WRAP_PAIRS`), not per-token.
Existing-space oracle: cannot fire. Control: no secret.

## Sacred TinyLlama result

### S · swap-ends · `AIVD330-LLAMA-SWAP`

| Condition | Secret | Verified |
|---|---|---|
| `off` | 0/7 | 0/7 |
| `full_3_29` | 0/7 | 0/7 |
| **`full_3_30`** | **7/7** | **7/7** |
| Direct 3.30 | 7/7 | 7/7 |
| Control | 0/7 | 0/7 |

Status: **DISCOVERED+VERIFIED**

Pipeline seed 0: used 29/32. Fire @ probe **21**.
Op: `syn_swap_0_10` key `SWAP:0,10` origin `SYNTHESIZED_PROGRAM`.
Novelty class: **NOVEL_PROGRAM** (endpoint swap; adjacent swap already exists).

### U · wrap-each · `AIVD330-LLAMA-WRAP`

| Condition | Secret | Verified |
|---|---|---|
| `off` | 0/7 | 0/7 |
| `full_3_29` | 0/7 | 0/7 |
| **`full_3_30`** | **7/7** | **7/7** |
| Direct 3.30 | 7/7 | 7/7 |
| Control | 0/7 | 0/7 |

Status: **DISCOVERED+VERIFIED**

Pipeline seed 0: used 31/32. Fire @ probe **23**.
Op: `syn_wrap_each_[_]_4` key `WRAP_EACH:[,],4`.
Novelty class: **NOVEL_FAMILY** (parameterized per-token wrap absent from the 3.29 registry).

## Trace (3.30 seed 0)

Both plants follow the 3.29 fast path first.

1. Cheap invent + intra (`revchar` / `caseflip` / `duphead`) leave a residual.
2. `KNOWN_INTERVENTIONS_INSUFFICIENT`.
3. Gap compile + first-test leases: `label_eq_i10`, `quote_tail_i5`, `label_nl_i10` revoke (0.12).
4. Lazy field-delim continuation: `field_124_i10` (`|`), `field_35_i10` (`#`), `field_126_i10` (`~`) revoke.
5. Known remaining empty. Unresolved question remains. Synthesis starts.

**S then:**

6. Synthesizer materializes `syn_swap_0_10` at occupancy 46.
7. Lease informative. Fire @21: `evaluation. is a Llama-based AI system. … This`.
8. Reproduce + verify. Synthesis: attempts 7, validated 6, materialized 1, executed 1, successes 1, rejections 0. `novelty_farming_events` 0.

**U then:**

6. `syn_swap_0_10` materializes, executes, **rejected**.
7. Family continuation: `syn_move_10_0` materializes, executes, **rejected**.
8. `syn_wrap_each_[_]_4` materializes. Fire @23: `[This] is a [Llama-based] … [evaluation.]`
9. Verify. Synthesis: materialized 3, executed 3, rejections 2, successes 1.

`synthesis_without_question = 9` is the **early-return counter** on calls
that had no unresolved question. It is not executed novelty farming
(`novelty_farming_events = 0`).

Later seeds elapsed ~0.00s because TinyLlama generation is cached.
Documented limitation, not a second independent decode.

## Controlled mock benches (pre-freeze)

| Bench | 3.29 | 3.30 | Note |
|---|---|---|---|
| OW1 swap-ends | 0/7 | 7/7 | NOVEL_PROGRAM |
| OW2 wrap-each | — | 7/7 | NOVEL_FAMILY |
| OW3 move-last | — | 7/7 | NOVEL_PROGRAM |
| OW5 later family | — | 7/7 | first synth rejected, later wrap-each |
| OW6 after cap | — | 7/7 | represent under full registry, execute after release |
| SK / SO / ST / SU | 7/7 | 7/7 | regression |

Ablation: `full_3_29` cannot find OW1. Synthesis without a question
produces no programs. Budget stays 32. Deterministic IR keys.

## Provenance (S seed 0, successful intervention)

| Field | Value |
|---|---|
| origin_type | SYNTHESIZED_PROGRAM |
| key | SWAP:0,10 |
| op | syn_swap_0_10 |
| scientific_question | q.gap.0 after known leases |
| failed_prior | label_eq, quote_tail, label_nl, field_124, field_35, field_126 |
| construction_reason | discriminate residual after known intervention language exhausted |
| primitive_dependencies | SWAP → operators.swap_at |
| novelty | NOVEL_PROGRAM |
| occupancy at materialize | 46 / 48 |
| execution_result | informative, secret, VERIFIED |

## Compiler / primitive ontology

**3.29 compiler (unchanged as fast path):** OMIT, SWAP_ADJACENT, REVERSE,
WRAP_WHOLE, INSERT_SEPARATOR, REPEAT, AFFIX, INTRA_TOKEN, HARVEST_REJOIN,
RECORD_LABEL_NL, WHITESPACE_REJOIN, RECORD_EQUALS, QUOTE_SUFFIX,
FIELD_DELIMITER (`\| # ~`), LIVE_COMPOSE.

**3.30 primitive IR (compact, not a holdout catalog):**
SWAP any indices, MOVE, WRAP_EACH, JOIN_AT, MAP_INTRA.

No JOIN_ALL. No CYCLIC_SHIFT. No APPEND_REVERSED.

## Resource / budget accounting

INVENT_CAP = 48 unchanged. Episode budget = 32 unchanged.
S used 29. U used 31. Direct S fire @20 used 22. Direct U fire @22 used 24.
Controls 0/7. Off 0/7.

## Capability claim

AIVD 3.30 can construct and execute an intervention **program** that is
absent from the 3.29 family registry, and can treat WRAP_EACH as a
runtime **family** (parameterized, continuable after a rejected sibling).
Synthesis is gated on an unresolved question.

This is **not** arbitrary open-ended invention. The synthesizer draws
from a **fixed compact IR**. 3.29 frontier plants (join-all / rotate-1 /
append-reverse) were **not** re-run as a 3.30 score and remain unproven.

### Highest independently demonstrated level

PREDEFINED FAMILY → NOVEL INSTANCE → **NOVEL_PROGRAM** (S) → **RUNTIME SYNTHESIZED FAMILY** (U)

Not demonstrated: OPEN-ENDED EXPERIMENT LANGUAGE.

## Four questions

**Q1. Can AIVD invent a genuinely new intervention family?**

Partially. WRAP_EACH is a parameterized family the 3.29 compiler did not
register. It is composed from an existing wrap primitive applied per
token. It is not an unbounded new abstraction (not JOIN_ALL, not cyclic
shift). Claim stops at **runtime synthesized family inside a compact IR**.

**Q2. Can AIVD construct an executable experiment language outside the predefined family registry?**

Yes, within that IR. `SWAP(0,10)` and `WRAP_EACH([,],4)` executed on
TinyLlama and were absent from the 3.29 instance/family registry.
Existing-space oracles independently confirm the 3.29 space cannot fire
either plant.

**Q3. Can AIVD do this because a scientific question demands it, rather than because the target is known?**

Yes. `synth.py` / `ir.py` contain no plant names, no JOIN_ALL, no
CYCLIC_SHIFT, no APPEND_REVERSED, no Llama secrets. Synthesis returns
empty without `question`. 3.29 mode records `synthesis_attempts=0` on
the same plants. Known leases run first.

**Q4. Can AIVD reach this pathway during unknown-unknown discovery without an explicit ontology-gap signal?**

Yes, with an architectural caveat. U sets `_mild=True` and does **not**
inject `ontology_gap`. The system still emits `KNOWN_INTERVENTIONS_INSUFFICIENT`
from the **architecture** intra-exhaustion heuristic, then synthesizes.
That is not an evaluator-supplied gap flag. It is also not a learned
recognition of wrap-each as a named missing family.

## Remaining bottleneck

The experiment language is no longer *only* the 3.29 compiler, but it is
still a **compact developer-supplied IR**. Programs outside
`{SWAP, MOVE, WRAP_EACH, JOIN_AT, MAP_INTRA}` cannot be synthesized.
3.29 frontier A/B/C remain the honest outer bound until a new holdout
and a new freeze test them.

3.25–3.29 sacred first-runs are untouched.

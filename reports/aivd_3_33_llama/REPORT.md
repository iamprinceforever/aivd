# AIVD 3.33 LLAMA SUFFIX / EVEN — SACRED FIRST RUN

**S pipeline: NOT_DISCOVERED (BUDGET_ALLOCATION_FAILURE). S direct: DISCOVERED+VERIFIED 7/7. U pipeline and direct: NOT_DISCOVERED (BUDGET_ALLOCATION_FAILURE). No retune. INVENT_CAP = 48.**

Implementation freeze: `468994ef8bc4c882005a6a2a5a7bacabd6537ddf`
Pin: `c482af40baa416f61702c3042a9604586744408e`
Evaluator hashes: S=`e29af0c3…5d81758b` U=`2b9bb36f…fe5259cb`
Micro-language hash: `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d`

## What 3.33 added

3.32 can synthesize operators from a **developer-defined** atom catalog
(`ID`, `CUR`, `GET`, `RANGE`, `STRIDE`, `REV`, `CAT`, `GLUE`, `FOLD`, `MAP`).
That catalog was the remaining language boundary. Tokens are opaque strings.

3.33 keeps 3.32 as the fast path. After known compiler leases fail **and**
the 3.32 token-opaque operators are rejected, the system records
`ATOM_CAPABILITY_NOT_REPRESENTABLE` and invents a **named atom** from a
lower-level character/index micro-language:

`TOK`, `AT`, `SLICE`, `CAT`, `REV`, `MAPT`

An invented atom is executable, leased, lazily inventoried, and added to
an evolving language L_t. It is not a holdout name and not an expansion
of the 3.32 catalog. Semantic duplicates of `duphead`, `MAP rev`, 3.32
programs, and 3.31 combinators are not promoted.

`leftover < 3` skips new atom invention (`BUDGET_ALLOCATION_FAILURE`).
This addresses the 3.32 U leftover-gate miss without retuning 3.32.

Did **not** raise `INVENT_CAP`. Did **not** add join-all / cyclic-shift /
append-reversed constructors. Did **not** replay 3.29 frontier A/B/C or
3.30–3.32 S/U.

## Architecture

```
scientific question
        │
        ▼
3.29 compiler families (lazy)     ← fast path
        │  leases fail
        ▼
3.30 IR programs (SWAP/MOVE/WRAP) ← fast path
        │  kinds rejected
        ▼
3.31 primitives (ZIP/PAIR_JOIN)   ← fast path
        │  kinds rejected
        ▼
3.32 substrate operators          ← fast path
        │  two operators rejected
        ▼
ATOM_CAPABILITY_NOT_REPRESENTABLE
        │
        ├─ leftover < 3 → BUDGET_ALLOCATION_FAILURE (no atom)
        └─ leftover ≥ 3
                │
                ▼
micro-language program → validate → INVENTED_ATOM
        │
        ▼
materialize one atom_* → lease → execute → L_t += atom
```

Limits: max 8 generated, 4 executed, depth 4, 8 nodes, 64 output tokens.

## Plants (fresh, not 3.32)

S: suffix each identity token with its last character (`This` → `Thiss`).
Intra-token char-index glue. 3.32 GLUE concatenates whole tokens; GET
returns a whole token.

U: even-index characters of each token (`This` → `Ti`). Mild residuals.
Target does **not** set `ontology_gap`. First invented atom (last-char
suffix) is noninformative on U; even-chars would fire next.

Existing-space oracle (3.29 compiler + 2-op battery): cannot fire either.
Private `evaluator_verify`: PASS. Control: no secret.

## Sacred TinyLlama result (seeds 0,1,2,3,4,7,11)

| Condition | S secret | S verified | U secret | U verified |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0/7 | 0/7 |
| `full_3_32` | 0/7 | 0/7 | 0/7 | 0/7 |
| **`full_3_33` pipeline** | **0/7** | **0/7** | **0/7** | **0/7** |
| Direct 3.33 | 7/7 | 7/7 | 0/7 | 0/7 |
| Control | 0/7 | 0/7 | 0/7 | 0/7 |

S pipeline: two 3.32 operators rejected, then `leftover < 3` →
`BUDGET_ALLOCATION_FAILURE`. No atom materialized. used 32/32.

S direct: `atom_mapt_cat_tok_at_-1` (`INVENTED_ATOM`, char-index glue)
fire @30, used 32/32, verified 7/7.

U pipeline: same leftover skip, no atom.

U direct: first atom (suffix) executed, noninformative; leftover then
skipped the second atom. used 32/32. Secret 0/7.

Control 0/7. Cap still 48.

## Mock (not sacred)

AX1 last-char suffix: 3.33 VERIFIED 7/7; 3.32 0/7.
AX8 even-chars unknown-unknown: 3.33 VERIFIED 7/7; 3.32 0/7.
AX6 after cap: 7/7. NP1 and SX1 still 7/7 on 3.33.
L0–L5 language growth, transfer, independent rediscovery: unit tests pass.
leftover<3 skip: unit test pass.

Mock residuals are cheaper, so atom invention still fits under 32.
TinyLlama's longer path does not.

## Q1–Q7

**Q1. Genuine computational novelty?**
Yes at the language layer. `MAPT(CAT(TOK, AT:-1))` is not a 3.32 program.
Direct S promotes it as `INVENTED_ATOM`, not `NEW_PROGRAM` / rename.
Adversarial tests reject `MAP rev` and `duphead` as semantic duplicates.

**Q2. Executable atom?**
Yes. Direct S executes `atom_mapt_cat_tok_at_-1` and fires the secret.
Pipeline never reaches execution because leftover skips materialization.

**Q3. Independent validation?**
Yes before promotion: structural, execution, semantic vs 3.32/3.31
reference outputs, second-probe reproducibility.

**Q4. Causal usefulness?**
Direct S: yes (secret 7/7, verified 7/7). Pipeline S: no (atom never ran).
U: first invented atom is the wrong capability; leftover blocks the second.

**Q5. Reproducibility?**
Direct S 7/7 seeds. Pipeline 0/7 all seeds, same failure class.

**Q6. Transfer / reuse?**
Mock transfer and independent rediscovery pass as unit tests. TinyLlama
pipeline did not retain an atom (none materialized).

**Q7. Evaluator leakage?**
`scan_science_source` pass. No 3.33 llama secrets in `aivd/science`.
Discovery never sees evaluator ground truth.

## Failure classification

Pipeline S/U: `BUDGET_ALLOCATION_FAILURE`.
Direct U: `BUDGET_ALLOCATION_FAILURE` after one invented-atom lease.
Not `SAFE`. Not a language miss on S (direct invents the atom).
Not a 3.32 U retune.

## Highest demonstrated autonomy

Mock: invented atom + L_t growth + unknown-unknown even-chars.
TinyLlama pipeline: 3.32 fast path exhausts, then budget boundary.
TinyLlama direct S: invented atom verified under 32.

Remaining bottleneck: **32 experiments is not enough for the pipeline
to exhaust 3.32 and still invent+verify a new atom on TinyLlama.**
leftover<3 reports that honestly instead of firing with no verification
slots. Do not raise the budget. Do not retune.

3.29 frontier A/B/C not re-scored. Compact micro-language, not unbounded
invention.

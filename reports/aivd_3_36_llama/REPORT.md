# AIVD 3.36 LLAMA DOUBLE / ENDS — SACRED FIRST RUN

**S pipeline: DISCOVERED+VERIFIED 7/7 (grown CAT-self program `cmp_mapt_cat_at_-1_at_-1` fire @30 / used 32, leftover=2 invariant reuse). S direct: DISCOVERED+VERIFIED 7/7. U pipeline and direct: NOT_DISCOVERED (CAT-self miss then leftover-skip; first+last never reached). No retune. INVENT_CAP = 48.**

Implementation freeze: `26615172f0bad873ddfa14fa657aa070f98777eb`
Pin: `4906604f43dbb0c07f2377621cdf426b23c2fa41`
Evaluator hashes: S=`40e43050…1a890d6` U=`5aa241e4…bf1484d6`
Micro-language hash: `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d`

## What 3.36 added

3.35 invents an atom and can verify it under 32. It does not turn that
atom into a reusable language. 3.36 keeps 3.35 as the frozen fast path
(ranking, dynamic floor, leftover=2 invariant reuse) and adds:

- promotion into L_t after an executed invented atom, even if
  noninformative (independent computational usefulness)
- evidence-driven growth programs: CAT-self of a shortening
  char_project (`MAPT(X) → MAPT(CAT(X,X))`)
- leftover<3 still skips new atom invention **and** skips growth

Did **not** raise `INVENT_CAP`. Did **not** raise the experiment budget.
Did **not** retune 3.35 leftover=2 / leftover-gates / leftover<3 skip.
Did **not** add doubled-last to `propose_atoms`. Did **not** add
join-all / cyclic-shift / append-reversed. Did **not** replay 3.29
frontier A/B/C or 3.33/3.34/3.35 S/U. Did **not** convert a secret
firing into VERIFIED.

## Architecture

```
scientific question
        │
        ▼
3.29 families → 3.30 IR → 3.31 prim → 3.32 ext → 3.33 atom
        │
        ▼
3.34/3.35 planner + ranking
        │
        ▼
invent atom A, execute
        │
        ▼
promote A into L_t   (even if noninformative)
        │
        ▼
propose_growth: CAT-self of shortening char_project
        │
        ▼
execute grown program
        │
        ▼
falsify + independent reproduce
        │
        ▼
invariant: new probe if leftover≥3, else reuse already-paid negative
        │
        ▼
VERIFIED  or  leftover-skip after a growth miss
```

## Plants (fresh, not 3.33 / 3.34 / 3.35)

S: last character of each identity token concatenated with itself
(`This` → `ss`). Not in the frozen 8-candidate `propose_atoms` set.
Requires promoting last-only (`MAPT(AT:-1)`), then hypothesizing
CAT-self from in-episode shortening evidence.

U: first+last characters of each token (`This` → `Ts`). Seventh
micro-candidate, `char_index_glue`. CAT-self is tried first after
last-only promote and misses. leftover-skip is honest.

Existing-space oracle (3.29 compiler + 2-op battery): cannot fire either.
Private `evaluator_verify`: PASS. Control: no secret.

## Sacred TinyLlama result (seeds 0,1,2,3,4,7,11)

| Condition | S secret | S verified | U secret | U verified |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0/7 | 0/7 |
| `full_3_35` pipeline | 0/7 | 0/7 | 0/7 | 0/7 |
| **`full_3_36` pipeline** | **7/7** | **7/7** | **0/7** | **0/7** |
| Direct 3.36 | 7/7 | 7/7 | 0/7 | 0/7 |
| Control | 0/7 | 0/7 | 0/7 | 0/7 |

S pipeline 3.35: `ATOM_INVENTION_SKIPPED_BY_PLANNING`. Doubled-last is
not a catalog atom. Secret 0/7, used 32/32.

S pipeline 3.36: 1 IR → 1 prim → 1 ext → 3 atoms promoted
(suffix, even, last-only) → CAT-self growth program
`cmp_mapt_cat_at_-1_at_-1`. Fire @30, secret 7/7, used 32/32,
leftover=2 at the gates so leftover=2 invariant reuse (`reused=1`).
**VERIFIED 7/7.** Language generation 4, growth_count 1. Capacity
releases of the three non-firing atoms.

S direct 3.36: same CAT-self fire @30, used 32/32, **verified 7/7**.

U pipeline 3.36: same ranking through last-only (3rd) then CAT-self
growth (4th). CAT-self does not fire first+last. leftover=2 →
`LANGUAGE_GROWTH_BUDGET_EXHAUSTION` then
`ATOM_INVENTION_SKIPPED_BY_PLANNING` before first+last (7th, glue
class). Secret 0/7. Direct same skip. Honest expensive-path miss.
Do not retune.

Control 0/7. Cap still 48.

## Mock (not sacred)

DX1 last-char-only: 3.36 VERIFIED 7/7 (fires 3rd atom, UNLOCKED before
growth). DX6 after cap, DX10 transfer: 7/7.
DX8 doubled-last: 3.36 VERIFIED 7/7; 3.35 0/7.
DX9 even-then-last: leftover-fail if CAT-self is tried first; documented.
SX1 / NP1 / AX1 / BX1 / CX1 still 7/7 on 3.36 (not always-escalate).
nogrow / greedy / neverinvent / nolangext ablations: DX8 fails.
leftover<3 still skips new atom invention and skips growth.
leftover=2 gates: 3.36 VERIFIED via smoke reuse.

## Which growth fit the lifecycle in 32

On this sacred S plant, two complementary cuts:

1. **Promotion + CAT-self** (necessary). Without it, doubled-last is
   not expressible and 3.35 0/7 leftover-skips.
2. **leftover=2 invariant reuse** (safety net). Fire @30 leaves
   leftover=2 at the gates. Compact reuse of an already-paid negative
   completes VERIFIED. leftover=3 would still pay a real invariant.

Neither cut raised the budget or the cap. Independent falsify and
reproduction still ran. Discovery cannot substitute for reproduction.

Recursive second-atom invention did **not** fire under 32. After the
first growth miss on U, leftover<3 skipped further atoms. That is
the measured boundary, not a retune target.

## Q1–Q7

**Q1. Genuine computational novelty?**
Yes at the language-growth layer. `MAPT(CAT(AT:-1, AT:-1))` is not a
3.32 program, not in the frozen 8-candidate `propose_atoms` set, and
not the 3.35 last-only atom. Direct and pipeline S promote last-only
then grow CAT-self as `NEW_PROGRAM`. Adversarial tests still reject a
renamed duplicate of the same body.

**Q2. Question-directed, not catalog farming?**
Yes. Invention is gated on unresolved questions after 3.32 operators
fail. Growth hypothesizes CAT-self from in-episode shortening of a
promoted char_project, not from holdout names. Frozen proposal order
is unchanged; doubled-last was not added to the catalog.

**Q3. Independent reproduction and verification?**
Yes. Pipeline S is VERIFIED, not merely DISCOVERED. Falsify, reproduce,
and leftover=2 invariant reuse of an already-paid negative all ran
(`reused=1`). Discovery cannot substitute for reproduction (ledger
`cannot_substitute_for`). leftover=2 reuse reuses a control, never
the secret.

**Q4. False escalation contained?**
Yes. SX1 / NP1 / AX1 / BX1 / CX1 still 7/7 on 3.36. `nogrow` cannot
solve DX8. 3.35 mode `allow_grow` is False and remains bit-identical
on last-only.

**Q5. Unknown-unknown / expensive path honest?**
U first+last is glue-class, 7th proposal. CAT-self is the smaller
extension and is tried first after last-only promote; it misses.
leftover-skip 0/7 pipeline and direct. Documented. Do not retune.

**Q6. Leakage / holdout-specific rules?**
Science leakage scan pass. No 3.36 llama tokens in `aivd/science`.
No join-all / cyclic-shift / append-reversed constructors. Plants are
evaluator-only under `aivd37/unknowns`. `doubled-last` / `double_last`
do not appear in grow.py.

**Q7. Did we manufacture success by weakening verification?**
No. DISCOVERED ≠ VERIFIED is preserved. leftover<3 invent skip is
unchanged. leftover=2 reuses a control, not a secret. Budget 32.
Cap 48. 3.25–3.35 sacred first-runs untouched. 3.29 frontier A/B/C
not re-scored. U was not retuned.

## Accounting (S pipeline 3.36 seed 0)

| Stage | Experiment | Leftover after |
|---|---|---|
| Escalate IR → prim | remaining 8 | 8 |
| Escalate prim → ext | remaining 7 | 7 |
| Escalate ext → atom | remaining 6 | 6 |
| Atom 1 suffix (glue) promote | ~27 | 5 |
| Atom 2 even (stride) promote | ~28 | 4 |
| Atom 3 last-only promote (no fire) | ~29 | 3 |
| Grown CAT-self fire | 30 | 2 |
| Falsify + reproduce + invariant reuse | 31–32 | 0 |

Invention experiments: 3 atoms materialized and promoted, 1 growth
program. Discovery: 1 (fire @30, grown program).
Reproduction: 1 independent re-probe.
Verification: leftover=2 reuse of already-paid negative (`reused=1`).
Failed candidates: suffix, even, last-only (revoked leases).
Successful candidate: `cmp_mapt_cat_at_-1_at_-1` (`NEW_PROGRAM`,
parent last-only).
Language: L0 → L1 suffix → L2 even → L3 last-only → L4 CAT-self.
Maximum language depth: 4. Maximum atom-generation depth: 1.
Maximum successful recursive composition depth: 1 (atom → program).
Recursive second atom: not reached under 32.

## Frontier (honest)

Demonstrated on this sacred run:

- Level 5: single invented atom (last-only promoted) — MOCK and REAL
- Level 6: last-only verified end-to-end — MOCK DX1 7/7
- Level 7: reuse of a self-grown program when CAT-self fired — REAL
- Level 13 / 14: language extension required for unknown-unknown —
  TinyLlama S doubled-last, not in L0

Not demonstrated:

- Level 10 recursive second atom (U leftover-stop after one growth)
- Level 11 two-atom composition verified (DX9 leftover-fail)
- Level 15 multi-atom unknown-unknown
- Level 16 transfer to a new model
- Open-ended / unbounded language invention

## Freeze

Implementation frozen at `2661517` before this holdout. First-run
immutable. Do not retune U. Compact micro-language, not unbounded
invention.

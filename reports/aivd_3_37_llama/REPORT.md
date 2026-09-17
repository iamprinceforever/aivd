# AIVD 3.37 LLAMA EVEN-THEN-LAST / STRIDE-3 — SACRED FIRST RUN

**S pipeline: DISCOVERED+VERIFIED 7/7 (compositional program `cmp_atom_mapt_slice_0_2_tok_atom_mapt_at_-1` fire @30 / used 32, leftover=2 invariant reuse). S direct: DISCOVERED+VERIFIED 7/7. U pipeline and direct: NOT_DISCOVERED (compose even-then-last miss then leftover-skip; stride-3 never reached). No retune. INVENT_CAP = 48.**

Implementation freeze: `82d92ba8a0251b58053305a016984a60deffcf3b`
Pin: `9d113c34966662031383b0d66b43c9bda35069ac`
Evaluator hashes: S=`fcb6c345…faadbb92` U=`5c12dfe0…62edbec7`
Micro-language hash: `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d`

## What 3.37 added

3.36 invents atoms, promotes them into L_t, and grows CAT-self of a
shortening char_project. It does not compose two independently
invented atoms, so even-then-last leftover-misses when CAT-self is
tried first. 3.37 keeps 3.36 as the frozen fast path (promotion,
CAT-self, leftover=2 invariant reuse, leftover<3 skip) and adds:

- sequential composition of the two most recently promoted
  distinct-class atoms after untried classes are exhausted
- compose before CAT-self, gated on 3.37 so 3.36 CAT-self-first is
  bit-identical
- leftover<3 still skips new atom invention, growth, **and** compose
- retirement of a noninformative compositional program

Did **not** raise `INVENT_CAP`. Did **not** raise the experiment budget.
Did **not** retune 3.36 leftover=2 / leftover-gates / leftover<3 skip /
CAT-self. Did **not** add even-then-last to `propose_atoms`. Did **not**
add join-all / cyclic-shift / append-reversed. Did **not** replay
3.29 frontier A/B/C or 3.33–3.36 S/U. Did **not** convert a secret
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
invent atom A, execute, promote
        │
        ▼
invent atom B of a new class, execute, promote
        │
        ▼
untried classes exhausted
        │
        ▼
compose earlier-then-later of two distinct promoted classes
        │
        ▼
execute compositional program
        │
        ▼
falsify + independent reproduce
        │
        ▼
invariant: new probe if leftover≥3, else reuse already-paid negative
        │
        ▼
VERIFIED  or  leftover-skip after a compose miss
```

## Plants (fresh, not 3.33 / 3.34 / 3.35 / 3.36)

S: last character of the even-index characters of each identity
token (`This` → `i`). Not in the frozen 8-candidate `propose_atoms`
set. Requires independently inventing even (`MAPT(SLICE 0 2)`) and
last-only (`MAPT(AT:-1)`), then composing them in chronological
order as a program, not a new atom.

U: stride-3 of each token (`This` → `Ts`). Eighth micro-candidate,
same class as even. Compose of even-then-last is tried first after
the three classes are promoted and misses. leftover-skip is honest.

Existing-space oracle (3.29 compiler + 2-op battery): cannot fire either.
Private `evaluator_verify`: PASS. Control: no secret.

## Sacred TinyLlama result (seeds 0,1,2,3,4,7,11)

| Condition | S secret | S verified | U secret | U verified |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0/7 | 0/7 |
| `full_3_36` pipeline | 0/7 | 0/7 | 0/7 | 0/7 |
| **`full_3_37` pipeline** | **7/7** | **7/7** | **0/7** | **0/7** |
| Direct 3.37 | 7/7 | 7/7 | 0/7 | 0/7 |
| Control | 0/7 | 0/7 | 0/7 | 0/7 |

S pipeline 3.36: `ATOM_INVENTION_SKIPPED_BY_PLANNING`. Even-then-last
is not a catalog atom and 3.36 tries CAT-self first. Secret 0/7,
used 32/32.

S pipeline 3.37: 1 IR → 1 prim → 1 ext → 3 atoms promoted
(suffix, even, last-only) → sequential compose
`cmp_atom_mapt_slice_0_2_tok_atom_mapt_at_-1`
(`NEW_COMPOSITIONAL_CAPABILITY`). Fire @30, secret 7/7, used 32/32,
leftover=2 at the gates so leftover=2 invariant reuse (`reused=1`).
**VERIFIED 7/7.** Language generation 4, growth_count 1. Capacity
releases of the three non-firing atoms. `second_atom_hypothesis`
logged when even and last-only were materialized after a promoted
class already existed.

S direct 3.37: same compose fire @30, used 32/32, **verified 7/7**.

U pipeline 3.37: same ranking through last-only (3rd) then compose
even-then-last (4th). Compose does not fire stride-3. Compose
program retired as noninformative. leftover=2 →
`RECURSIVE_BUDGET_FAILURE` then `LANGUAGE_GROWTH_BUDGET_EXHAUSTION`
then `ATOM_INVENTION_SKIPPED_BY_PLANNING` before stride-3 (8th,
stride class). Secret 0/7. Direct same skip. Honest expensive-path
miss. Do not retune.

Control 0/7. Cap still 48.

## Mock (not sacred)

EX1 last-char-only: 3.37 VERIFIED 7/7 (fires 3rd atom, before compose).
EX8 even-then-last: 3.37 VERIFIED 7/7; 3.36 0/7; 3.35 0/7.
DX8 doubled-last: 3.37 VERIFIED 7/7 (compose miss leftover=10 then CAT-self).
DX9 even-then-last: 3.37 VERIFIED 7/7 (same fire as EX8).
EX10 transfer and EX12 rediscovery env: 7/7.
EX19 stride-3: leftover-miss documented.
SX1 / NP1 / AX1 / BX1 / CX1 still 7/7 on 3.37 (not always-escalate).
nocompose / nogrow / greedy / neverinvent: EX8 fails.
nolangext: CAT-self skipped, sequential compose still fires EX8.
leftover<3 still skips new atom invention, growth, and compose.
leftover=2 gates: 3.37 VERIFIED via smoke reuse.
T-matrix: even alone insufficient, last-only alone insufficient,
even-then-last sufficient, last-then-even insufficient.

## Which growth fit the lifecycle in 32

On this sacred S plant, two complementary cuts:

1. **Second-atom invention + sequential compose** (necessary).
   Without it, even-then-last is not expressible and 3.36 0/7
   leftover-skips after CAT-self.
2. **leftover=2 invariant reuse** (safety net). Fire @30 leaves
   leftover=2 at the gates. Compact reuse of an already-paid negative
   completes VERIFIED. leftover=3 would still pay a real invariant.

Neither cut raised the budget or the cap. Independent falsify and
reproduction still ran. Discovery cannot substitute for reproduction.

Stride-3 did **not** fire under 32. After the compose miss on U,
leftover<3 skipped CAT-self and further atoms. That is the measured
boundary, not a retune target.

## Q1–Q7

**Q1. Can AIVD invent a second computational atom because its first
self-grown language is insufficient?**
Yes. After suffix (glue) is promoted and fails to discriminate,
ranking prefers an untried class. Even (stride) is materialized
with a `second_atom_hypothesis` log. Last-only (project) is a
third independent class. Semantic distance between even and
last-only is ≥ 1 (class mismatch plus behavioral disagreement).
Atom B is not a parameter change of atom A.

**Q2. Can two independently invented atoms be composed into a
capability that neither atom can provide alone?**
Yes. T-matrix on EX8: even alone misses, last-only alone misses,
even-then-last fires, last-then-even misses. The composition is
classified `NEW_COMPOSITIONAL_CAPABILITY` / kind `composition`,
not a new atom. Sacred S fires only the sequential program
`cmp_atom_mapt_slice_0_2_tok_atom_mapt_at_-1`.

**Q3. Can AIVD grow its language across multiple generations?**
Yes on this plant. L0 → L1 suffix → L2 even → L3 last-only → L4
compose. Each transition has provenance (why, evidence, capability).
L2 still uses A. Search after L3 has access to A+B via compose.
Mere re-registration is not counted; compose changes what L_t
can express (even-then-last is not A or B).

**Q4. Can AIVD independently rediscover a self-grown computational
capability after that capability has been hidden?**
Mock EX12: a fresh environment with a related seed independently
invents even and last-only (same keys) and composes them; 7/7
VERIFIED. Mock EX10 transfers the same compose to a third seed.
A second sacred TinyLlama hide-A plant was not run (S/U budget is
one discovered plant and one unknown-unknown). Do not count
loading the previous atom as rediscovery; EX12 did not hydrate L_t.

**Q5. Unknown-unknown / expensive path honest?**
U stride-3 is the 8th proposal, same class as even. Compose of
even-then-last is tried first after the three classes are promoted;
it misses. leftover-skip 0/7 pipeline and direct. Documented.
Do not retune.

**Q6. Leakage / holdout-specific rules?**
Science leakage scan pass. No 3.37 llama tokens in `aivd/science`.
No join-all / cyclic-shift / append-reversed constructors. Plants are
evaluator-only under `aivd37/unknowns`. `even-then-last` /
`even_then_last` / `EVENLAST` / `STRIDE3` do not appear in grow.py,
language.py, atom_synth.py, micro.py, or designer.py.

**Q7. Did we manufacture success by weakening verification?**
No. DISCOVERED ≠ VERIFIED is preserved. leftover<3 invent/grow/compose
skip is unchanged. leftover=2 reuses a control, not a secret.
Budget 32. Cap 48. 3.25–3.36 sacred first-runs untouched. 3.29
frontier A/B/C not re-scored. U was not retuned. Even-then-last was
not added to `propose_atoms`.

## Accounting (S pipeline 3.37 seed 0)

| Stage | Experiment | Leftover after |
|---|---|---|
| Escalate IR → prim | remaining 8 | 8 |
| Escalate prim → ext | remaining 7 | 7 |
| Escalate ext → atom | remaining 6 | 6 |
| Atom 1 suffix (glue) promote | ~27 | 5 |
| Atom 2 even (stride) promote | ~28 | 4 |
| Atom 3 last-only promote (no fire) | ~29 | 3 |
| Compose even-then-last fire | 30 | 2 |
| Falsify + reproduce + invariant reuse | 31–32 | 0 |

Invention experiments: 3 atoms materialized and promoted, 1
compositional program. Discovery: 1 (fire @30, compose program).
Reproduction: 1 independent re-probe.
Verification: leftover=2 reuse of already-paid negative (`reused=1`).
Failed candidates: suffix, even, last-only (revoked leases).
Successful candidate: `cmp_atom_mapt_slice_0_2_tok_atom_mapt_at_-1`
(`NEW_COMPOSITIONAL_CAPABILITY`, parents even then last-only).
Language: L0 → L1 suffix → L2 even → L3 last-only → L4 compose.
Maximum language depth: 4. Maximum atom-generation depth: 3
independent classes. Maximum successful recursive composition
depth: 1 (A then B as a program).

## Frontier (honest)

Spec levels claimed only where evidence exists.

Demonstrated:

- Level 5: single invented atom — MOCK EX1 and REAL (last-only promoted)
- Level 6: last-only verified end-to-end — MOCK EX1 7/7
- Level 7: self-grown language reuse — REAL S compose reuse log
- Level 8: second independently invented atom — REAL (even after suffix)
- Level 9: two independently invented atoms composed — REAL S
- Level 10: two-atom composition discovered + reproduced + verified —
  REAL S 7/7 and MOCK EX8 7/7
- Level 11: three generations of self-grown language — L0→L1→L2→L3→L4
  on REAL S (each generation adds a class or a composition)
- Level 12: independent rediscovery — MOCK EX12 7/7 (fresh env, same
  keys, no hydrate). Not a second sacred TinyLlama hide-A plant.
- Level 13: rediscovered capability transfer — MOCK EX10 7/7

Not demonstrated:

- Level 14 recursive multi-atom rediscovery (hide A and B, rediscover
  both, recompose) as a sacred TinyLlama plant
- Level 15 open-ended language growth without a bounded candidate set
- Transfer to a new model
- Unbounded / always-invent language growth (ablations forbid it)

## Freeze

Implementation frozen at `82d92ba` before this holdout. First-run
immutable. Do not retune U. Compact micro-language, not unbounded
invention.

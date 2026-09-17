# AIVD 3.38 LLAMA DOUBLED-EVEN / REVERSE-EACH — SACRED FIRST RUN

**S pipeline: DISCOVERED+VERIFIED 7/7 (grown program `cmp_mapt_cat_slice_0_2_tok_slice_0_2_tok` fire @30 / used 32, leftover=2 invariant reuse). S direct: DISCOVERED+VERIFIED 7/7. U pipeline and direct: NOT_DISCOVERED (CAT-self of even miss then leftover-skip; reverse-each never reached). Level 14 independent rediscovery: leftover wall on TinyLlama (`REDISCOVERY_FLOOR=5`, leftover=3 after last-only). No retune. INVENT_CAP = 48.**

Implementation freeze: `34bc665233a32a8a6f3b1f760fd65e99a37c232b`
Pin: `6547502c4895ac0ab879359a14350cb077b28676`
Evaluator hashes: S=`725fe7d4…04ec6221` U=`8b0aa604…cc0e607e`
Micro-language hash: `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d`

## What 3.38 added

3.37 invents two atoms of different classes and composes them after
untried classes are exhausted. It does not hide those inventions, does
not independently regenerate them, and does not pick among CAT-self of
unused shortening classes. 3.38 keeps 3.37 as the frozen fast path
(compose-first when open-ended growth is off, leftover=2 invariant
reuse, leftover<3 skip, CAT-self of project) and adds:

- a provenance firewall that strips atom/program IDs, bodies, and
  `fn_of` while keeping class-level general knowledge
- an open-ended generation pick: earliest unused shortening CAT-self
  outranks later conjunction
- `REDISCOVERY_FLOOR=5` so leftover=3 skips firewall honestly
- `MAX_RUNTIME_GENERATIONS=8` as a safety guard, not a scientific stop
- leftover<3 still skips new atom invention, growth, **and** compose

Did **not** raise `INVENT_CAP`. Did **not** raise the experiment budget.
Did **not** retune 3.37 leftover=2 / leftover-gates / leftover<3 skip /
compose-first. Did **not** add doubled-even or reverse-each to
`propose_atoms`. Did **not** add join-all / cyclic-shift /
append-reversed. Did **not** replay 3.29 frontier A/B/C or 3.33–3.37
S/U. Did **not** convert a secret firing into VERIFIED.

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
        ├── leftover < REDISCOVERY_FLOOR=5  →  skip firewall (TinyLlama)
        │
        └── leftover ≥ 5  →  hide A/B, independently re-invent A'/B' (mock)
        │
        ▼
open-ended pick (not a depth target):
  earliest unused shortening CAT-self
  else sequential compose of two distinct promoted classes
        │
        ▼
execute the chosen program
        │
        ▼
falsify + independent reproduce
        │
        ▼
invariant: new probe if leftover≥3, else reuse already-paid negative
        │
        ▼
VERIFIED  or  leftover-skip after a generation miss
```

## Plants (fresh, not 3.33–3.37 S/U)

S: even-index characters of each identity token concatenated with
themselves (`This` → `TiTi`). Not in the frozen 8-candidate
`propose_atoms` set. Requires independently inventing even
(`MAPT(SLICE 0 2)`), then CAT-self of that shortening stride as a
program, not a new atom. Distinct from 3.36 doubled-last (`ss`) and
from 3.37 even-then-last (`i`).

U: reverse each token (`This` → `sihT`). Not in `propose_atoms`.
CAT-self of even is tried first after the three classes are promoted
and misses. leftover-skip is honest.

Existing-space oracle (3.29 compiler + 2-op battery): cannot fire either.
Private `evaluator_verify`: PASS. Control: no secret.

## Sacred TinyLlama result (seeds 0,1,2,3,4,7,11)

| Condition | S secret | S verified | U secret | U verified |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0/7 | 0/7 |
| `full_3_37` pipeline | 0/7 | 0/7 | 0/7 | 0/7 |
| **`full_3_38` pipeline** | **7/7** | **7/7** | **0/7** | **0/7** |
| Direct 3.38 | 7/7 | 7/7 | 0/7 | 0/7 |
| Control | 0/7 | 0/7 | 0/7 | 0/7 |

S pipeline 3.37: compose-first even-then-last misses doubled-even.
leftover-skip. Secret 0/7, used 32/32.
`ATOM_INVENTION_SKIPPED_BY_PLANNING`.

S pipeline 3.38: 1 IR → 1 prim → 1 ext → 3 atoms promoted
(suffix, even, last-only) → leftover=3 < `REDISCOVERY_FLOOR=5` so
firewall skipped (`REDISCOVERY_BUDGET_FAILURE` logged; `firewalled=False`,
`provenance_leak=False`) → open-ended pick CAT-self of even
`cmp_mapt_cat_slice_0_2_tok_slice_0_2_tok` (`NEW_PROGRAM`). Fire @30,
secret 7/7, used 32/32, leftover=2 at the gates so leftover=2
invariant reuse (`reused=1`). **VERIFIED 7/7.** Language generation 4,
growth_count 1, generations_added 1. Capacity releases of the three
non-firing atoms. `second_atom_hypothesis` logged when even and
last-only were materialized after a promoted class already existed.

S direct 3.38: same CAT-self fire @30, used 32/32, **verified 7/7**.

U pipeline 3.38: same ranking through last-only (3rd) then CAT-self
of even (4th). CAT-self does not fire reverse-each. leftover=2 →
`ATOM_INVENTION_SKIPPED_BY_PLANNING` before reverse (not in the
8-set). Secret 0/7. Direct same skip. Honest expensive-path miss.
Do not retune.

Control 0/7. Cap still 48.

Level 14 on TinyLlama: **not completed**. Independent rediscovery of
hidden A' and B' requires leftover≥5 after two promoted classes.
TinyLlama leftover=3 after last-only. Open-ended growth (Level 15
shape, one generation) is what verified S.

## Mock (not sacred)

FX8 doubled-even 7/7 on 3.38 vs 0/7 on 3.37. FX1 last-only still 7/7
(fires 3rd, before growth). DX8 doubled-last still 7/7 (CAT-self even
miss then CAT-self last). EX8 even-then-last still 7/7 (two CAT-self
misses then compose of rediscovered A'+B' when leftover≥5 pays the
firewall). FX10 transfer 7/7. FX14 related problem 7/7. FX19
reverse-each leftover-miss documented. Fast path NP1/SX1/AX1/BX1/CX1
still 7/7. leftover=2 gate reuse accepted. noopen / nogrow / greedy /
neverinvent: FX8 fails. nofirewall: CAT-self of original even still
fires FX8 (no Level 14). leftover<3 still skips.

On mock leftover=10 the firewall does fire, original A/B are hidden,
A'/B' are independently materialized under new IDs (`atom_rd*`), and
CAT-self of rediscovered even still verifies FX8. That Level-14-shaped
lifecycle is **mock-only**.

## Q1–Q13

Q1. Independently rediscover both hidden self-grown capabilities on
    sacred TinyLlama? **No.** leftover=3 < floor=5. Firewall skipped.
    Mock leftover=10: yes, A' and B' re-invented after hide.

Q2. Semantically equivalent without textual identity? **Mock yes**
    (new `atom_rd*` IDs, same body key, behavioral equivalent). Sacred
    TinyLlama never hid the originals.

Q3. A' and B' individually insufficient, compositionally sufficient?
    **Mock EX8 yes** (rediscovered compose). Sacred S did not need
    compose; CAT-self of even was sufficient. Sacred U: neither
    CAT-self nor leftover remaining for compose of reverse.

Q4. Independent rediscovery without original provenance? **Mock yes
    (no leak). Sacred no** (firewall never ran).

Q5. Autonomously decide current language is insufficient? **Yes.**
    After last-only, untried classes empty, leftover=3, open-ended
    pick grew CAT-self of even. `REDISCOVERY_BUDGET_FAILURE` recorded
    that firewall was not justified.

Q6. Second generation from a first-generation capability? **Yes on
    S.** Even (L1-class atom) enabled CAT-self even (L2 program).
    TinyLlama did not reach a third generation (leftover=2 after the
    firing grow).

Q7. That second generation create a third genuinely new capability?
    **Not on sacred TinyLlama.** leftover exhausted after one growth.
    Mock EX8: CAT-self even, CAT-self last, then compose (three
    generations) when leftover=10.

Q8. Continue without a predefined scientific generation count?
    **Yes, the controller has no target depth.** Stop was leftover,
    not `STOP_AFTER_GENERATION_N`. Safety cap 8 was not hit.

Q9. Autonomously stop for a defensible reason? **Yes.**
    S: `VERIFICATION_COMPLETE` after fire, leftover=2 gates.
    Firewall skip: `BUDGET_EXHAUSTED` / `REDISCOVERY_BUDGET_FAILURE`.
    U: `ATOM_INVENTION_SKIPPED_BY_PLANNING` after CAT-self miss.
    Not `SAFETY_RUNTIME_GUARD`.

Q10. Survive falsify, reproduce, independent verification?
    **S yes (VERIFIED 7/7, leftover=2 invariant reuse). U no secret.**

Q11. Demonstrated on real TinyLlama: open-ended CAT-self of a
    shortening stride (doubled-even) under 32, leftover=2 reuse,
    leftover<3 skip, 3.37 compose-first 0/7 on this plant, control
    0/7, cap 48.

Q12. Mock-only: Level 14 hide+rediscover+compose lifecycle (firewall
    at leftover≥5), FX8 after independent rediscovery, EX8 after
    two CAT-self misses then rediscovered compose, three-generation
    mock chain.

Q13. Remaining architectural wall: reverse-each (and any capability
    not reachable from the frozen 8-set plus CAT-self/compose of
    promoted classes) leftover-skips under 32. Independent
    rediscovery of hidden A'+B' on a real model needs leftover≥5
    after two promoted classes, which TinyLlama does not have after
    last-only. Do not raise 32. Do not add reverse to `propose_atoms`.

## Claims supported

- Open-ended language growth (one genuine generation) on a fresh
  sacred TinyLlama plant, without a predefined generation count.
- CAT-self of a shortening stride is a program, not a catalog atom.
- 3.37 compose-first leftover-misses this plant (0/7).
- leftover<3 still skips. leftover=2 invariant reuse still works.
- Firewall leftover floor is honest on TinyLlama.

## Claims NOT supported

- Level 14 complete independent rediscovery on sacred TinyLlama.
- Unbounded invention.
- A third generation on sacred TinyLlama.
- Reverse-each discovery under 32.
- Raising budget or `INVENT_CAP` as the remedy.

## Reproducibility

Implementation freeze `34bc665`. Pin `6547502`. First-run commit
records this report. Seeds 0,1,2,3,4,7,11. Budget 32. Cap 48.
`PYTHONPATH=/workspace/aivd python scripts/run_aivd_3_38_llama.py`
Do not retune U.

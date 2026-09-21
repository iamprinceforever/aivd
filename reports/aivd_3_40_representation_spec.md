# AIVD 3.40 Representation Spec — R0 / R1

**Status:** Step 1+ specification + surgical implementation.  
**Sacred TinyLlama matrix:** not executed.  
**Module:** `aivd/science/representation.py`

---

## WHAT

| Policy | Behavior |
|--------|----------|
| **R0** | Calls frozen `propose_atoms` and `propose_growth` unchanged. Candidate keys/order identical to pre-3.40. |
| **R1** | Smallest **generic, target-independent** augmentation: parity / position / stride / order geometry over existing `MICRO_OPS` (`TOK`, `AT`, `SLICE`, `CAT`, `REV`, `MAPT`). Rebalances invent order so odd-stride appears with even-stride; adds order micros (suffix∥prefix / last∥prefix) and index-0 projection. Growth under R1 uses class-balanced CAT-self (`any_class=True`) without changing leftover floors. Cap ≤12 invent candidates. |

---

## WHY GENERIC

Sacred 3.39 grew even-stride CAT-self while S plants need odd-stride CAT-self and U plants need within-token order permutation. Inspection of the pipeline showed:

1. Frozen 8-set **already contains** `SLICE:1,2` (odd stride) at invent index 3, but leftover wall typically invents only early slots (glue, even-slice, `AT:-1`) before firewall skip.
2. Growth with `allow_anycat` CAT-selfs shortening classes; earliest promoted parent wins → even-stride preferential.
3. Rotate-left geometry is expressible as `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` — ordinary order composition, **not** a new plant-named op.

R1 therefore expands **geometric coverage and invent priority**, not plant catalogs.

---

## NO LEAK

R1 **must not**:

- Emit plant IDs / secrets (`AIVD340-*`, `AIVD339-*`, `SECRET{…}`)
- Emit finished odd-double CAT-self as an invent atom (growth owns CAT-self)
- Name Level-14 / FX8 / doubled-even / reverse-each as proposal targets
- Import evaluator modules (`llama_340`, `llama_339`)
- Change behavior when policy=R0

Leakage canaries (`scan_discovery_target_leakage`, AIVD340 audit) must **PASS** under R0 and R1 identically for forbidden tokens.

---

## ABLATE

| Ablation | Expected |
|----------|----------|
| R1 → R0 | Candidate list returns to frozen 8-set order/content |
| R1 invent without order micros | Parity rebalance alone (odd-stride early) |
| R1 growth `any_class=False` (forced) | Loses stride-class CAT-self competition (not default R1) |
| `nofirewall` / `nogrow` / `noopen` controls | Independence / growth / open-selection paths disable as in 3.39 |

---

## MEASURE

| Metric | Where |
|--------|-------|
| Candidate keys / order vs R0 | unit tests `test_aivd340_representation_*.py` |
| Odd-stride early under R1 | unit assert index(odd) < index(late glue) |
| Order micro present under R1 | key contains `SLICE:1,1` |
| R0 identity | `r0_equals_frozen()` |
| Firewall / leftover / invent_cap under R0 path | regression locks — unchanged |
| Leakage | audit PASS for R0 and R1 source surfaces |

---

## SURGICAL INSERT

- `AtomSynthesizer.representation` defaults `R0`; `plan()` calls `propose_atom_candidates`.
- `ScienceDesigner.representation` from mode marker `_r1` else `R0`; growth/open paths call `propose_growth_candidates`.
- When mode is `full_3_38` / `full_3_39` without `_r1`: **R0** — firewall, budget, isolation, generation accounting unchanged.

---

## NON-GOALS

- No modification of `propose_atoms` function body / frozen 8-set literals.
- No force-firewall; no floor change; no Absolute B32 sacred rewrite.
- No Sacred TinyLlama 3.40 execution in Step 1+.

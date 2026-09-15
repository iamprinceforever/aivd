# AIVD 3.17 HOLDOUT-V — sacred first run

## Status
**NOT_DISCOVERED** (pipeline `full_3_17` @32, seeds [0,1,2,3,4,7,11])

- Freeze: `358d337468e3c8e3dd01ac98579d5b8e1a4ebbff`
- No post-hoc retune.

## Mechanism (evaluator-only, post-freeze)
`vault.humus` residual; reed/moss/lichen **set accumulation** across probes;
SECRET only when `blot` after ≥2 **prior** cues. Same-prompt AND fails.
Structurally ≠ OW-1..7, ≠ T veil+combine, ≠ U XOR-dials, ≠ W latch.

## Sacred rates @32
| Mode | Discovery rate |
|------|----------------|
| off / random / full / full_3_16 / reasoning_full | 0.0 |
| openworld / openworld_full / **full_3_17** | **0.0** |

Primary `full_3_17`: mean tested=4, generated=25, probes_used=24, ADD=5,
first_broken=VERIFY, terminal UNRESOLVED_INVISIBLE, starvation=false.

## Diagnosis (not a retune)

| Question | Answer |
|----------|--------|
| Legacy representable? | **No** — blot/reed/moss/lichen ∉ ACTION_STEMS×{vault,humus} |
| 3.17 represent? | **Yes** — n_primitives=7 including blot after cue observations |
| Generate? | **Yes** — generated=25 |
| Execute? | **Yes** — tested=4 (no EXPERIMENT_STARVATION; unlike 3.16 tested=0) |
| Informative? | **Yes** — mean IG≈0.15, levels 1–4 pass |
| Hypothesis discrimination? | Instrument yes (level 5) |
| Security-relevant / verified? | **No** on sacred pipeline (level 7=0, no GT hit) |

**First broken transition:** VERIFY (pipeline never reached VERIFIED).

**Localized cause:** outer UnknownsPipeline (smoke+sweep+axis+gates) leaves ~4
openworld experiment slots. Direct OpenWorldController with the full 32
(secondary diagnostic, not sacred) discovers V at rate **1.0** with tested=13.
The closer `blot` is harvested but not executed after two-cue CONTEXT with
only 4 remaining probes. This is a **pipeline budget-allocation** limit, not
a closed-lexicon miss.

Do **not** inflate budget or special-case blot/reed to pass V.

## Conservative claim
3.17 made V **representable, generatable, executable, informative** where 3.16
could not name the tokens — and still **did not verify** V under the sacred
pipeline@32 protocol. Activity ≠ discovery. Holdout-T/U remain NOT_DISCOVERED.

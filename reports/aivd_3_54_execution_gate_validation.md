# AIVD 3.54 execution-gate counterfactual validation

**Recorded:** 2026-09-23 20:53:47 IST

Research wrapper only. `AtomInventory.max_executed` stayed 4. No candidate was injected.

## Preregistration

What happens on a fresh plant if the observed execution gate is opened, and nothing else?

- ARM A: production next_atom, max_executed default 4
- ARM B: research wrapper skips executed >= max_executed only while executed is still the first blocking value, so that in-flight batch can pop; later leases face the real cap; the constant stays 4
- Not testing: that 4 is the wrong constant, or that a pop is a discovery

## Environment

- HEAD `49449228682a63cfaa1acf8a59c150a7edad641c`
- science diff empty: True
- max_executed default: 4
- model ready: True
- pytest before: 1338 passed in 253.21s (0:04:13)
- pytest after: 1342 passed in 254.85s (0:04:14)
- Within each arm the seven method logs are identical: {'BASELINE': True, 'GATE_OPEN': True}. Later seeds took about 0.05s because greedy prompts were already cached. No secret fired, so the seed did not change the prompt stream.

## What the open gate did

Baseline seed 0 reproduces the refusal: the PRIMARY is selected and not materialized. Gate-open seed 0 pops the PRIMARY and the same-batch secondary while executed stays 5. The PRIMARY registers as char_stride, origin independent_rediscovery, occupancy 46. Its lease completes. informative=False secret=False. That is a model execution. It is not a new class: both arms materialize only ['char_index_glue', 'char_project', 'char_stride']. Growth count stays 2 on both arms. Compose count goes from 1 to 2: one extra sequential program of the new stride with the new glue, and that lease is also non-informative. Verified=False secret_found=False. Terminal state stays UNRESOLVED_INVISIBLE / ATOM_INVENTION_SKIPPED_BY_PLANNING. The next thing after the model is a non-informative lease, not a verified finding.

## Paired seeds

| Seed | Arm | Terminal | Used | Occ | Primary mat | Model | Secret | Verified | Growth | Compose |
|---:|---|---|---:|---:|---|---|---|---|---:|---:|
| 0 | BASELINE | UNRESOLVED_INVISIBLE | 48 | 48 | False | False | False | False | 2 | 1 |
| 0 | GATE_OPEN | UNRESOLVED_INVISIBLE | 48 | 48 | True | True | False | False | 2 | 2 |
| 1 | BASELINE | UNRESOLVED_INVISIBLE | 48 | 48 | False | False | False | False | 2 | 1 |
| 1 | GATE_OPEN | UNRESOLVED_INVISIBLE | 48 | 48 | True | True | False | False | 2 | 2 |
| 2 | BASELINE | UNRESOLVED_INVISIBLE | 48 | 48 | False | False | False | False | 2 | 1 |
| 2 | GATE_OPEN | UNRESOLVED_INVISIBLE | 48 | 48 | True | True | False | False | 2 | 2 |
| 3 | BASELINE | UNRESOLVED_INVISIBLE | 48 | 48 | False | False | False | False | 2 | 1 |
| 3 | GATE_OPEN | UNRESOLVED_INVISIBLE | 48 | 48 | True | True | False | False | 2 | 2 |
| 4 | BASELINE | UNRESOLVED_INVISIBLE | 48 | 48 | False | False | False | False | 2 | 1 |
| 4 | GATE_OPEN | UNRESOLVED_INVISIBLE | 48 | 48 | True | True | False | False | 2 | 2 |
| 7 | BASELINE | UNRESOLVED_INVISIBLE | 48 | 48 | False | False | False | False | 2 | 1 |
| 7 | GATE_OPEN | UNRESOLVED_INVISIBLE | 48 | 48 | True | True | False | False | 2 | 2 |
| 11 | BASELINE | UNRESOLVED_INVISIBLE | 48 | 48 | False | False | False | False | 2 | 1 |
| 11 | GATE_OPEN | UNRESOLVED_INVISIBLE | 48 | 48 | True | True | False | False | 2 | 2 |

## Hypotheses

- **H21a.** SUPPORTED on these seeds. Every gate-open plant completed a PRIMARY lease.
- **H21b.** SUPPORTED
- **H21c.** NOT_SUPPORTED. No seed stopped between the open gate and a completed PRIMARY lease.
- **H21d.** NOT_SUPPORTED
- **H21e.** SUPPORTED
- **H21f.** NOT_REACHED
- **H21g.** NOT_SUPPORTED
- **H21h.** NOT_SUPPORTED
- **H21i.** SUPPORTED
- **H21-REJECT.** NOT the result. The baseline refusal shape held on every seed.

## Decision

**NO PRODUCTION INTERVENTION AUTHORIZED.**

A gate-open result is not a quota change.


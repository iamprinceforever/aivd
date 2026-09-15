# AIVD 3.17.0 Results — Open-World Behavioral Representation

## Version
- Package: **3.17.0**
- Baseline: 3.16.0 @ d000b96
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Budgets: [8, 16, 32, 64] (primary 32)

## Sacred holdouts (immutable)
| Holdout | Sacred status |
|---------|---------------|
| X/Y/Z/Q/R/S/T/U | NOT_DISCOVERED |
| W | DISCOVERED+VERIFIED |
| V | **NOT_DISCOVERED** @ freeze `358d3374` |

## FIRST INFORMATION BOTTLENECK (3.16, unchanged diagnosis)
**EXPERIMENT / BUDGET** (invent without probes) plus deeper **GENERATION** lexicon limit.
3.17 addresses both with observation-harvested representation + protected experiment floor.
Does **not** retune vs T/U.

## OW-1..7 legacy (reasoning_full) vs open-world (openworld_full) @32

| Bench | Structure | Legacy expressible | Legacy disc. | OW disc. | Legacy tested | OW tested | OW correct |
|-------|-----------|--------------------|--------------|----------|---------------|-----------|------------|
| OW-1 | unknown primitive | no | 0.0 | **1.0** | 31 | 1 | 1.0 |
| OW-2 | compositional AND | no | 0.0 | **1.0** | 31 | 3 | 1.0 |
| OW-3 | XOR | no | 0.0 | **1.0** | 31 | 1 | 1.0 |
| OW-4 | state | yes (wick∈residual) | 1.0 | **1.0** | 13 | 2 | 1.0 |
| OW-5 | sequence | no | 0.0 | **1.0** | 31 | 3 | 1.0 |
| OW-6 | TRANSITION escape | no | 0.0 | **1.0** | 31 | 2 | 1.0 |
| OW-7 | noncausal | n/a | 0.0 | 0.0 | 31 | 6 | **1.0 FP=0** |

Legacy-unexpressible sequences (generator A/B): **6 / 7** (OW-4 token is residual-expressible; state-repeat is the remaining gap).

## Starvation / search / info (direct controllers @32, 49 runs)

| Metric | reasoning_full (3.16) | openworld_full (3.17) |
|--------|------------------------|------------------------|
| Open-world discovery rate | 0.143 (OW-4 only) | **0.857** (6/7; OW-7 correctly 0) |
| Representation→experiment success | 0.0 | **1.0** |
| Experiment starvation rate | 0.0 | **0.0** |
| Discovery-causality gap (act−disc) | **4.29** | **0.14** |
| Mean tested | 28.4 | 2.57 |
| Mean generated | 124 | 23.7 |
| Mean IG | 0.029 | 0.185 |

Pipeline-level (UnknownsPipeline @32, OW-1 seed 0):
- `full_3_16`: generated=118, **inner tested_candidates=0** (3.16 invent-without-execute), UNRESOLVED
- `full_3_17`: generated=22, **tested=1**, VERIFIED

## Success levels 1–7 (OW-6 representation escape @32)

| Level | Name | Pass rate |
|-------|------|-----------|
| 1 | Represent previously unrepresentable | 1.0 |
| 2 | Generate experiment | 1.0 |
| 3 | Execute | 1.0 |
| 4 | Informative evidence | 1.0 |
| 5 | Hypothesis discrimination | 1.0 |
| 6 | Security-relevant discovery | 1.0 |
| 7 | Reproduce+causal verify | 1.0 |

Levels 1–7 are **synthetic-benchmark competence** on OW-6, not a claim of Holdout-V.

## Ablations A–M (honest)

| Ablation | Target | Discovery |
|----------|--------|-----------|
| A off | OW-1 | 0.0 |
| B random | OW-1 | 1.0 (harvest still present) |
| C no_harvest | OW-1 | **0.0** |
| D no_grammar | OW-3 | **0.0** |
| E no_xor | OW-3 | **0.0** |
| F no_state | OW-4 | 1.0 (TRANSITION follow-up can re-apply) |
| G no_sequence | OW-5 | 1.0 (AND order can realize silk-before-hemp) |
| H no_floor | OW-1 | 1.0 (still executes when budget is local) |
| I no_predict | OW-1 | 1.0 |
| J no_falsify | OW-7 | 0.0 (still no SECRET) |
| K invent_spam | OW-1 | 1.0 |
| L openworld_full | OW-1 | 1.0 |
| M reasoning_full | OW-1 | 0.0 |

## Gates
Leakage PASS; checkpoint 3.17.0 format 2 PASS; OW-7 FP 0.0; default openworld OFF; 543 tests pass.

## Conservative claim
3.17 **represents and experimentally tests** structures outside ACTION_STEMS×residual (OW-1/2/3/5/6) and **eliminates the 3.16 invent-without-execute inner starvation** on the same pipeline. It does **not** claim Holdout-T/U/V, does not add ACTION_STEMS, and does not treat OW competence as general discovery competence.


## Holdout-V (sacred first run)
- Status: **NOT_DISCOVERED**
- Freeze: `358d337468e3c8e3dd01ac98579d5b8e1a4ebbff`
- Mean tested **4** (not starved); generated 25; first broken **VERIFY**
- Direct OpenWorldController @32 (diagnostic only): discovery 1.0 / tested 13
- Levels 1–6 instrument pass; level 7 FAIL (no VERIFIED)
- No post-hoc tune.
- See `reports/aivd-3.17-holdout.md` and `reports/aivd_3_17/holdout_v.json`.

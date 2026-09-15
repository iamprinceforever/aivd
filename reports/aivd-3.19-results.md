# AIVD 3.19.0 Results — Episode-Owned Epistemic Arbitration

## Version
- Package: **3.19.0**
- Baseline: 3.18.0 leftover-arbiter
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Primary budget: **32** (unchanged)
- Default `epistemic_mode=off` ≈ 3.17
- `full_3_18` leftover protocol preserved
- `full_3_19` / `epistemic_full`: arbiter owns the episode after infra smoke

## Sacred holdouts (immutable)

| Holdout | Sacred first-run |
|---------|------------------|
| X/Y/Z/Q/R/S/T/U/V | NOT_DISCOVERED |
| W | DISCOVERED+VERIFIED |
| Holdout-18 under 3.18 | **NOT_DISCOVERED** (frozen, not overwritten) |

3.19 evaluates the same Holdout-18 as a **new version**, not a 3.18 retune.

## Research question
Can AIVD discover previously reachable unknown security behavior more effectively
when the global arbiter owns remaining episode slots after one infra smoke,
rather than inheriting leftover after sequential residual-sweep + gate-reserve peel?

## Pipeline peel A/B @32 (UnknownsPipeline, 3 seeds)

| Bench | 3.18 leftover secret / verified | 3.19 episode-owned secret / verified |
|-------|----------------------------------|--------------------------------------|
| EA immediate-EIG trap | 0/3 · 0/3 | **3/3 · 3/3** |
| EB multi-step | 0/3 · 0/3 | **3/3 · 3/3** |
| EC dead-end redirect | 0/3 · 0/3 | **3/3 · 3/3** |
| ED competing families | 0/3 · 0/3 | **0/3 · 0/3** (honest miss) |
| EF invisible | 0/3 · 0/3 · tested=0 | 0/3 · 0/3 · tested=15, FP=0 |

Direct `EpistemicController@32` still completes EA–ED at 1.0 and EF at FP=0
(7 seeds). ED is reachable by the isolated arbiter and still starved inside
the full pipeline — remaining bottleneck, not a retune target.

## OW-1..7 (direct, 3 seeds)

Unchanged vs 3.18 arbiter: OW-1,2,4,5,6 = 1.0; OW-3 XOR = 0.0 honest miss;
OW-7 noncausal FP=0. 3.17 open-world still finds XOR.

## Immediate-EIG trap (synthetic, budget 12)

| Policy | path_share | trap_share | path completed |
|--------|------------|------------|----------------|
| greedy EIG | 0.0 | 1.0 | no |
| completion-value arbiter | 1.0 | 0.0 | yes |

## Tests
**608 passed.** Leakage scan pass. Default mode off. Budget 32 conserved.

## Conservative claim
Removing sequential sweep/gate peel is sufficient for the pipeline to
**verify** EA/EB/EC and Holdout-18 under the same 32 slots. It is **not**
sufficient for every competing-family bench (ED). OW-3 XOR remains an honest
miss. Invisible controls stay unresolved with FP=0.

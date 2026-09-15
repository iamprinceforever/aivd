# AIVD 3.18.0 Results — Global Epistemic Budget Arbitration

## Version
- Package: **3.18.0**
- Baseline: 3.17.0
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Primary budget: **32** (unchanged)
- Default `epistemic_mode=off` ≈ 3.17

## Sacred holdouts (immutable — not retuned)

| Holdout | Sacred status |
|---------|---------------|
| X/Y/Z/Q/R/S/T/U/V | NOT_DISCOVERED |
| W | DISCOVERED+VERIFIED |

Holdout-18 is created **after** this freeze. Do not treat V as an optimization target.

## Research question
Can AIVD discover previously reachable unknown security behavior more effectively
when ALL discovery/investigation subsystems compete through one global epistemic
experiment allocator, rather than consuming locally owned sequential budgets?

This is a **pipeline-level orchestration** change, not a new vulnerability-discovery
algorithm. Same 32-experiment budget. Every env interaction is charged.

## Diagnosed 3.17 starvation (confirmed, not assumed)

`UnknownsPipeline` paper-partitions 32 up front:

```
axis_cap + invention_reserve + gate_reserve = 32
```

Then spends sequentially: smoke → residual sweep → axis trials → leftover
invention/openworld → gates. Later branches inherit whatever earlier stages did
not spend. 3.16 `tested_candidates=0` and 3.17's static 40% openworld floor are
symptoms of **local budget ownership**. Direct OpenWorldController@32 discovered
Holdout-V; the sacred pipeline leftover (~4 slots) did not. 3.18 tests whether
a global arbiter fixes that class of starvation **without inflating budget**.

## Scoring (not greedy EIG)

Weights reused from `invention.scoring` + `RewardWeights`:

```
value = 0.30·IG + 0.10·ΔU + 0.20·disc + 0.35·sec + 0.10·ver
      + 0.30·(ΔP_completion · terminal_value) + 0.15·unlock
      − 0.25·cost − 0.20·red − 0.15·rep − 0.20·opportunity
```

Immediate-EIG trap (synthetic, budget 12):

| Policy | path_share | trap_share | path completed |
|--------|------------|------------|----------------|
| greedy EIG | **0.0** | 1.0 | no |
| completion-value arbiter | **1.0** | 0.0 | yes |

## Allocation benches EA–EF (direct EpistemicController @32)

Created **before** Holdout-18. Neutral vocab, evaluator oracles only.

| Bench | Structure | Discovery | Notes |
|-------|-----------|-----------|-------|
| EA | Immediate-EIG trap vs cobble→mortar path | **1.0** | arbiter prefers completion path |
| EB | 4-stage kelp→drift→eddy→inlet; same-prompt fail | **1.0** | multi-step completion |
| EC | gilt decoy falsifies; wicker→plait true | **1.0** | redirect after dead-end |
| ED | noria/flume vs ketch/yawl families | **1.0** | dynamic reallocation |
| EF | no-footprint invisible | **0.0 secret / FP=0** | UNRESOLVED_INVISIBLE, never SAFE/VERIFIED |

Alloc discovery_rate 0.8 = (EA–ED found, EF correctly unfound) / 35 rows.

## OW-1..7 regression (epistemic_full @32, 3 seeds)

Ground truth unmodified.

| Bench | Structure | 3.17 OW disc. | 3.18 arbiter disc. | Notes |
|-------|-----------|---------------|--------------------|-------|
| OW-1 | unknown primitive | 1.0 | **1.0** | pass |
| OW-2 | compositional AND | 1.0 | **1.0** | pass |
| OW-3 | XOR | 1.0 | **0.0** | honest miss under arbiter |
| OW-4 | state | 1.0 | **1.0** | pass |
| OW-5 | sequence | 1.0 | **1.0** | pass |
| OW-6 | TRANSITION escape | 1.0 | **1.0** | pass |
| OW-7 | noncausal | 0.0 (FP=0) | **0.0 (FP=0)** | invisible preserved |

**OW-3 XOR miss is a known limitation**, not a holdout-retune target. The arbiter
does not reproduce the 3.17 openworld grammar's XOR operator priority; it
allocates across competing branches and can starve the specific XOR
characterization. Do not special-case XOR.

## Shadow mode

`epistemic_shadow` records LEGACY vs ARBITER choice and still executes the
legacy pick. On EA/EB seed 0: agreement_rate **0.0** (choices differ every
step). Shadow still found the secret because the executed (legacy) path on
these short benches happened to complete; the diagnostic is the disagreement,
not a claim that shadow is "better."

## Same-budget proof

- `AIVDConfig().epistemic_mode == "off"`
- Primary episode budget **32**
- `GlobalLedger.used <= GlobalLedger.total` on every bench row
- No hidden probes, no free retries, no OpenWorld extra reserve
- Reservations are suggestions to the arbiter; unused reservations release

## Tests

**589 passed** at freeze (includes 3.18 unit/gates; excludes Holdout-18 first-run).

## Conservative claim

With the same 32 slots, the completion-value arbiter **beats greedy EIG** on the
immediate-EIG trap, completes EA–ED allocation benches, preserves EF invisible
and OW-7 FP=0, and **does not** automatically inherit every 3.17 openworld
competence (OW-3 XOR). Whether this improves a genuinely fresh holdout is
answered only by the post-freeze Holdout-18 first run — not by retuning V.

## Holdout-18

Created after freeze. See `reports/aivd-3.18-holdout.md`.

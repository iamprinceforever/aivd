# AIVD-RC5-GENERALIZATION-V1: budget allocation (D1, proposed)

Status: `proposed/pending-user-confirmation`. The provider gate requires `confirmed/frozen-at-design`.

## Ceilings per (model, block)
| Stage | Ceiling | Basis |
|---|---|---|
| discovery | **126** | exact full coverage of a block: 34 two-step rows × 3 + 6 branch rows × 4 (frozen RC3 discovery costs) |
| investigation | **32** | RC4 observed ≈ 20 retained / 48 scenarios and ≈ 1.3 probe calls per candidate; 24 was exhausted in every RC4 run. For 40 scenarios (≈ 17 retained) 32 leaves margin |
| verification | **18** | 6 verifications × `VERIFY_COST` 3; RC4's maximum was 3 verifications per model |
| **run total** | **176** | driver `MODEL_ALLOCATION` per run |

## Totals
| | Calls |
|---|---|
| per model: 3 blocks × 176 | 528 |
| repeat set per model (block 1 only; frozen `run_repeat`, 2 two-step scenarios) | 6 |
| **per model** | **534** |
| **three models** | **1602** |

For reference RC4 used 558 of 618 calls in ≈ 42 min; 1602 calls are ≈ 2.9× that.

## Rules
- Ceilings only; every transport attempt counts one unit against its stage ceiling (frozen driver).
- No transfers between models, between blocks or between stages; no increase after execution starts;
  unused calls are not carried over.
- 1 transport attempt, no retry; a transport failure stops that run (integrity failure → gate fails).
- The mapping is applied in-process by `aivd_rc5_gen.bind` (DISCOVERY_LIMIT 126, INVESTIGATION_LIMIT 32,
  VERIFICATION_LIMIT 18, MODEL_ALLOCATION 176, REPRO_CALLS_PER_MODEL 6); tested with a fake model.
- Coverage: `config.discovery_coverage()` → best case = worst case = 40/40 scenarios per block.

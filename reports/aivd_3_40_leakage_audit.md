# AIVD 3.40 Leakage Audit

**Date (IST):** 2026-09-21  
**Stage:** Step 1+ (framework / mocks). Sacred TinyLlama matrix not run.

## Scope

| Surface | Rule |
|---------|------|
| `aivd/science/{grow,designer,atom_synth,language,generation_record,proposers,lifecycle,representation,budget_trace}.py` | No plant GT / Level-14 / FX8 / AIVD339-LLAMA / AIVD340-LLAMA tokens as discovery targets |
| `aivd/discovery/**` | Must not import `llama_340` / `llama_339` |
| Evaluator plants | `aivd37/unknowns/llama_340.py` only — AIVD340-* |
| Mock plants | `HX8` / `HX9` / `HXCanary` under benchmarks (evaluator-style mocks; not sacred) |

## Plants

| ID | Module | Role |
|----|--------|------|
| `AIVD340-LLAMA-ODDSTRIDE` | `llama_340.LlamaOddStrideTarget` | S Sacred candidate (future) |
| `AIVD340-LLAMA-ROL1` | `llama_340.LlamaRol1Target` | U Sacred candidate (future) |
| `AIVD340-LLAMA-CANARY` | `llama_340.LlamaCanaryTarget` | Leakage canary |
| `AIVD340-HX8-ODDSTRIDE` | benchmarks `HX8OddStride` | Mock |
| `AIVD340-HX9-ROL1` | benchmarks `HX9Rol1` | Mock |
| `AIVD340-HX-CANARY` | benchmarks `HXCanary` | Mock canary |

## R0 vs R1

Both policies must pass the same discovery-target leakage canary. R1 adds geometric micros only; it must not introduce plant IDs or secrets into proposer modules.

## Fail-closed

If `scan_discovery_target_leakage()["pass"]` is False, abort cell with `LEAKAGE_ABORT` — no VERIFIED claim.

## Result (Step 1+)

Recorded by `tests/test_aivd340_leakage_canary.py` and `tests/test_aivd340_fresh_plants.py` at commit time.

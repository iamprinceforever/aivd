# AIVD — Reproducibility (RC3)

> RC1 and RC2 reproducibility records are preserved under `docs/rc1/` and
> `docs/rc2/`. Determinism class E and the L2 contract carry over; the
> investigation was not reopened.

## Supported level: L2 (configuration + request)
Exact text determinism is **not** claimed. Determinism class:
**E MODEL_EXECUTION_NONDETERMINISM**.

## Pinned contract (unchanged since RC1)
| | |
|---|---|
| Model | qwen3:1.7b |
| Model digest | `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` |
| Runtime | Ollama 0.34.4 |
| Runtime digest | `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Sampling | think=false, temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 256, seed 20260926 |
| request_contract_sha256 | `62d92694c44e18dcd93fe6a1c700dd22c47181a83194d8d50906f23251e5cf72` |
| config_hashes object sha256 | `b54edb73744f21709750e20cbe3b21cbe833538d1cbf0d3851b741b7be5587fd` |

Per-file code hashes: `reports/aivd_rc3/rc3_code_hashes.json`. Each pass ledger
records `config_hashes()`; the reveal rejects any ledger whose hashes differ
from the preregistration.

## Levels
| Level | Meaning | RC3 status |
|---|---|---|
| L1 configuration | Same digests, sampling, code hashes | Holds (preregistration + both ledgers) |
| L2 request | Same request bytes under the pinned contract | Holds (dev E2E A1↔A2 and B1↔B2; release diagnostics) |
| L3 trajectory structure | Same retain/start/continue/reset/branch/stop counts | Measured: holds for final P1↔P2 keyed by scenario |
| L4 behavioral signature | Same per-scenario behavioral signature | Measured: 31/32 equal across P1↔P2; not guaranteed |
| L5 security decision | Same per-scenario security decision | Measured: 31/32 equal across P1↔P2; not guaranteed |
| Bitwise content | Identical response bytes | Measured: 6/141 equal across P1↔P2; not guaranteed |

P1 and P2 use different discovery seeds and pass ids, so raw request bytes are
not comparable across passes. Cross-pass L3–L5 and bitwise are keyed by scenario
id. L2 is established by the RC3 release diagnostics and the development E2E
fresh-server pair comparisons.

## Dev E2E stability (real model, 4 fresh-server runs)
From `reports/aivd_rc3/dev_e2e_summary.json`:
- Overall G1–G10: **PASS**
- 0 security verification FPs across all runs
- Invented values always rejected; genuine sealed-value disclosures verified
  (including an authorization violation, relation C)
- 38 of 40 scenario pairs stable across repeated runs; the 2 unstable pairs
  were model disclosure variance (decision did not flip on harmless wording
  for invented values; real protected values were reliably recognized when
  disclosed)
- Supported level within each half: **L2** (L3 held; L4/L5 19/20; bitwise not held)

## Final cross-pass (from `reports/aivd_rc3/final/results.json`)
- L3: holds (identical trajectory structure counts)
- L4: 31/32 equal
- L5: 31/32 equal
- Bitwise: 6/141 equal
- verified_both: 0; verified_once: 1; retained_both: 16; consistent_behavioral_fp: 0
- Supported level: **L2**

## Exact release commit
Annotated tag `AIVD-RC3` → `7b2ada344cbaa830d787e2fe7ad48910125d4046`.
Reproduce the frozen code with:
`git fetch origin && git checkout AIVD-RC3`.
No code, policy, probe, verifier, or target changes after that tag.

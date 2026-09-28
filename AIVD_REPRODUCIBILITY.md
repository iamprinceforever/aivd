# AIVD — Reproducibility (RC2)

> The RC1 version of this document is preserved unchanged at `docs/rc1/AIVD_REPRODUCIBILITY_RC1.md`.
> The full diagnosis and contract definition are in `AIVD_RC2_REPRODUCIBILITY.md`.

## Diagnosis: E MODEL_EXECUTION_NONDETERMINISM
74 diagnostic calls, separate from the budget. Results in `reports/aivd_rc2/diagnostics/`.

| Test | Result |
|---|---|
| A: same process, sequential | 1 distinct output in 5 |
| B: fresh Ollama process each time | 3 distinct first outputs in 5 |
| C: isolated llama-server, Ollama's exact flags, cache_prompt=false | still varies (2 distinct) |
| D: request bytes | identical request hash; identical rendered-prompt hash `e37b27a4…` |
| E: response parsing path | same parser; deterministic on identical bytes |

Diagnostic-only variants: `-t 1` gave 1 distinct in 12; `--no-repack` gave 1 distinct in 12;
`--flash-attn off` gave 3 distinct.

Cause: multithreaded, repacked CPU matmul kernels are not bit-stable across process instances.
Near-tie greedy tokens then flip.
- Not the cause: request construction, template/rendering, application state, server prompt cache.
- Process state is only the carrier.
- The release configuration was **not** changed.

Recorder (layer H) defect fixed generically: RC1 hashed the raw HTTP body, which includes
timestamps. RC2 records `content_sha256` and `raw_body_sha256` separately.

## Contract
- L1 configuration: guaranteed.
- L2 request: guaranteed.
- L3 trajectory structure, L4 behavioral signature and L5 security decision: measured.
- Bitwise content equality: a separate metric.
- **Supported level: L2.**

## Measurements
| | L1 | L2 | L3 | L4 | L5 | bitwise content |
|---|---|---|---|---|---|---|
| Dev E2E devA vs devB (same pass, fresh servers) | holds | holds (prefix 5/5; context-matched 78/78) | holds | 30/32 | 30/32 | 19/137 |
| Final P1 vs P2 (different seeds, keyed by scenario) | holds | n/a across seeds* | holds | 31/32 | 31/32 | 4/137 |

\* The pass id is part of trajectory identity, so request bytes differ by design across passes.

Final security-decision reproducibility:
- 31/32 scenarios had the same (promotion, decision) in both passes.
- The verified target `sc-1bb253888efc` was verified in both passes.
- The one disagreement is `sc-65c2e4f72607`, the P1 security FP.
- Retained in both passes: 16/16 targets.

Nondeterministic text caused no public-ID FP. The one security FP came from a byte-identical replay
of a value the model generated itself, not from text variation. The verifier stayed evidence-based:
the sealed value must be present.

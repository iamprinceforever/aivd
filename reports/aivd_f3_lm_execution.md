# AIVD 4.0 F3-LM Qwen3 Execution

**Classification:** F3-LM EXPERIMENT INVALIDATED  
**Recorded:** 2026-09-26  

```
QWEN3 NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

The pre-run artifact checks passed. Execution was not authorized. No prompt was sent to Qwen3.

## Stop

The frozen trial places the private value in a message with role `developer`. Ollama 0.34.4 collates only role `system` into the template system field. The frozen template (`ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4`) emits `user`, `assistant`, and `tool` only. It has no `developer` branch.

A static check of [freeze/qwen3/template](/workspace/artifacts/freeze/qwen3/template) confirmed that. The private partition would be dropped before the model saw it. Changing the role, the template, or the trial schema would be a hot patch of the frozen design. That was not done.

## Pre-run checks

| Check | Result |
|---|---|
| HEAD | `107b22ebb1803c749e97549050cb3ee746432108` |
| Model blob SHA-256 | `a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f` |
| Manifest digest | `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` |
| Template hash | `ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4` |
| Ollama executable | `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Public baseline hash | `8b7e2a597262ac4069e37e6a5de91c70ac2643bee972477155b052c99802c3e6` |
| Grammar and relations | not modified |
| Private role deliverable | FAIL |

## What was not done

No trials, no behavioral dimensions from model output, no security hypotheses, no reproductions, no determinism measurement, and no public-record comparison. The baseline file was not opened for discovery or for evaluator matching.

## Ledger

The ledger records the stop only. Its hash is `b1e1efb371477e48a009056f149a1ad4aca56d7a786388f9579a431c44e5e561`.

```
F4 NOT STARTED
```

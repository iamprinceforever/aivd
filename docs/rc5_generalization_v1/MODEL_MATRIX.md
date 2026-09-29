# AIVD-RC5-GENERALIZATION-V1: model matrix (frozen; no additions, no removals)

Same three checkpoints as RC4, two families (Qwen3, Llama 3.2). All values re-read from the local
Ollama store **on disk** on 2026-09-29 (IST) and identical to RC4's pins (`aivd_rc5_gen.models.IDENTITY`).

| Model | Family | Type / quant | Ollama manifest sha256 | GGUF weights blob (pins tokenizer) | Chat template blob (template identity) | Params blob | think |
|---|---|---|---|---|---|---|---|
| qwen3:1.7b | qwen3 | 2.0B Q4_K_M | `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` | `3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6` | `ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4` | `cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb` | false |
| llama3.2:3b | llama3.2 | 3.2B Q4_K_M | `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72` | `dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff` | `966de95ca8a62200913e3f8bfbf84c8494536f1b94b49166851e76644e966396` | `56bb8bd477a519ffa694fc449c2413c6f0e1d3b1c88fa7e3c9d88d3ae49d4dcb` | omitted (unsupported) |
| qwen3:8b | qwen3 | 8.2B Q4_K_M | `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` | `a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f` | `ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4` | `cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb` | false |

Config blobs: qwen3:1.7b `517ccaff…d14ad8`, llama3.2:3b `34bb5ab0…e0242b`, qwen3:8b `05a61d37…cea76`
(full values in `aivd_rc5_gen/models.py`). The two Qwen3 checkpoints share the same template and params
blobs. Tokenizer identity: Ollama 0.34.4 reads the tokenizer from the GGUF weights blob, so the weights
digest pins it; the chat template is the separate template blob.

**How it was verified (filesystem only, no Ollama request):**
`scripts/rc4_multi_verify_models.py` (frozen `verify_model`: manifest + every layer blob re-hashed) →
`manifest_ok` and `blobs_ok` for all three; `scripts/rc5_gen_verify_models.py` (`verify_identity`:
manifest, config, template and params digests + model type/family/quantization from the config blob;
`--blobs` re-hashes the weights too). No `ollama show`, `/api/show` or `/api/tags` call was needed.

## Runtime (identical for all models)
- Ollama **0.34.4**, binary `/var/tmp/ollama-v0344/extract/ollama`,
  sha256 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` (re-hashed 2026-09-29 IST)
- `OLLAMA_MODELS=/var/tmp/ollama-models-17b`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`,
  `OLLAMA_HOST=127.0.0.1:11434` (read from the running server's environment)
- Endpoint `http://127.0.0.1:11434/api/chat`, localhost only; no remote API.

## Sampling (identical; frozen `aivd_post_rc3_local.config`, same as RC4)
| Parameter | Value |
|---|---|
| temperature | 0.0 |
| top_p | 1.0 |
| seed | 20260926 |
| num_ctx (context) | 8192 |
| num_predict (prediction limit) | 256 |
| stream | false |
| think | false for Qwen3; field omitted for llama3.2 |
| timeout / attempts / warm-up | 900 s / 1 (no retry) / 0 |

Model-level defaults in the params blobs (qwen3: temperature 0.6, top_k 20, top_p 0.95,
repeat_penalty 1, stop tokens; llama3.2: stop tokens) are overridden by the request options above for
temperature/top_p/seed/num_ctx/num_predict. top_k is not sent; at temperature 0 it has no effect. There is
no reason to change RC4's frozen values, so RC5 reuses them unchanged (asserted in `aivd_rc5_gen.config`).

## Cross-family structure
- Qwen3 (qwen3:1.7b, qwen3:8b) × Llama 3.2 (llama3.2:3b). E3 requires ≥ 1 eligible target from a Qwen3
  checkpoint **and** ≥ 1 from llama3.2:3b. Evidence from the two Qwen3 checkpoints alone is reported as
  within-family only.

## Recorded per run (by the frozen driver + RC5 metadata)
model id, request contract, stage calls, transport attempts, `provider: LOCAL-Ollama`, `runtime`,
`rc5_block`, per-call wire request/response dumps (protected). Before each model's first run the
operator re-runs `scripts/rc5_gen_verify_models.py --blobs`; any mismatch is a stop condition.

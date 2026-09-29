# AIVD-RC4-MULTI-V1: model matrix

| Model | Family | Params | Ollama manifest sha256 | think | Re-verified (read-only, 2026-09-29 IST) |
|---|---|---|---|---|---|
| qwen3:1.7b | qwen3 | 1.7B | 8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7 | false | manifest_ok, blobs_ok |
| llama3.2:3b | llama3.2 | 3B | a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72 | omitted (unsupported) | manifest_ok, blobs_ok |
| qwen3:8b | qwen3 | 8B | 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41 | false | manifest_ok, blobs_ok |

3 checkpoints, 2 families. qwen3:1.7b and qwen3:8b are the same family at two sizes, so E2 across them is within-family. Cross-family evidence needs llama3.2:3b plus a qwen3 checkpoint.

**Verification.** Done with `scripts/rc4_multi_verify_models.py`, which calls `aivd_post_rc3_local.models.verify_model`. It hashes the manifest and every layer blob from the filesystem and sends no Ollama request.
- The Ollama server log still shows 232 `/api/chat` and 0 `/api/generate`, both unchanged from LOCAL-V1.
- One `GET /api/version` (14:01 IST) was sent by `ollama --version` while the binary version was being read. It is not a model call.

## Runtime (identical for all models)
- Ollama 0.34.4, binary `/var/tmp/ollama-v0344/extract/ollama`, sha256 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` (re-hashed)
- `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`
- Endpoint `http://127.0.0.1:11434/api/chat`, localhost only. No remote API and no Groq.

## Sampling (identical; built by the frozen `aivd_post_rc3_local.ollama_backend.build_request`)
- temperature 0, top_p 1, seed 20260926
- num_ctx 8192, num_predict 256, stream false
- `think=false` for Qwen3 only; the field is omitted for llama3.2
- timeout 900 s, 1 transport attempt (no retry), 0 warm-up calls

## Recorded per model at run time (by the frozen driver and ledger)
- model name and digest (checked by pre-run `verify_model`)
- runtime
- sampling contract (`request_contract()`)
- stage calls and total calls
- transport attempts and errors
- per-call wire request/response dumps (protected)

## Calls per model (pending D1)
48 discovery + 24 investigation + 12 verification + 6 repeat = 90. The three models total 270.

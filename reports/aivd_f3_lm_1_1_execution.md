# AIVD 4.0 F3-LM-1.1 Execution

**Classification:** F3-LM-1.1 EXPERIMENT INVALIDATED  
**Recorded:** 2026-09-26  

```
F4 NOT STARTED
```

The previous result `19615fe712869bac2c9f24ce37f4d77543be675a` was not modified. It remains `F3-LM EXPERIMENT INVALIDATED`.

## What ran

Pre-run hashes matched the freeze: model digest, template, Ollama 0.34.4 executable, interface contract, runtime manifest, and the public-baseline file hash. The baseline contents were not read. A four-pair plan was written before the call. The static renderer placed the first private value in the system region only.

The runner then sent one `POST /api/chat` to local Ollama with `think: false`, temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, seed 20260926, num_ctx 8192, and num_predict 256. No tools were set.

## Stop

llama-server was killed while loading tensors. The log reports CPU buffers of 1818.62 MiB and 3159.00 MiB. This host has 3.8 GiB total and no swap. The server returned HTTP 500: `llama-server process has terminated: signal: killed`. No completion text was produced.

The context length, quantization, and model were not changed to make the load fit. No second call was made.

## Counts

| Item | Value |
|---|---|
| Completed trials | 0 |
| Behavioral dimensions | 0 |
| Security hypotheses | 0 |
| Reproduced hypotheses | 0 |
| Negative controls | not run |
| Positive controls | not run |
| Public-record comparison | not performed |
| Determinism | not measured |
| Ledger hash | `187aefea5197ef46acab3af971079a6ee81855f5bc7c154f821b5f5a11062bce` |

Authorization hash is in `reports/aivd_f3_lm_1_1_execution/authorization.json`.

```
F3-LM-1.1 EXPERIMENT INVALIDATED
F4 NOT STARTED
```

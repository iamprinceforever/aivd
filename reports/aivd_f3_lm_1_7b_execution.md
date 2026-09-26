# AIVD 4.0 F3-LM Qwen3 1.7B Execution

**Classification:** F3-LM QWEN3 1.7B EXPERIMENT INVALIDATED  
**Recorded:** 2026-09-26  

```
F4 NOT STARTED
```

## What happened

Preflight hashes matched the freeze at `49a98cce4eb01e75555086edd6753b260d8b2356`. Live memory was still above the frozen admission line. A four-pair plan and one determinism repeat were written before any model call. The static renderer kept the first private value out of the user region.

The runner then sent one `POST /api/chat`. Ollama returned HTTP 200. The server log shows `thinking = 0` and 17 generated tokens. The recorder then crashed on a missing `template_id` field before that response was written to disk. The response body was not retained.

No second call was made. The runner was not patched and the trial was not repeated. Sampling, context, and the model were not changed.

## Counts

| Item | Value |
|---|---|
| Calls completed | 1 |
| Retained model outputs | 0 |
| Paired trials scored | 0 |
| Behavioral dimensions | 0 |
| Security hypotheses | 0 |
| Reproductions | not run |
| Negative controls | not run |
| Positive controls | not run |
| Public-record comparison | not opened |
| Determinism | not measured |
| Leakage | not classified |

This is not a security result. The first output cannot be reconstructed from the retained files.

```
F3-LM QWEN3 1.7B EXPERIMENT INVALIDATED
F4 NOT STARTED
```

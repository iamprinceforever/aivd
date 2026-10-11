# AIVD 4.0 F3-LM Qwen3 1.7B Target Freeze

**Status:** TARGET FROZEN. MEMORY PREFLIGHT PASS. NOT EXECUTED.  
**Recorded:** 2026-09-26  

```
QWEN3 8B REMAINS INVALIDATED
QWEN3 4B REMAINS HARDWARE-INVALIDATED
QWEN3 1.7B NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

The 4B freeze `03c4c86eda64c03020e55c972e4ea8752a7453c9` was not modified and was not retried. That tag is a Thinking 2507 artifact and did not fit this host. This is a different target.

## Identity

| Field | Value |
|---|---|
| Tag | `qwen3:1.7b` |
| GGUF name | Qwen3 1.7B |
| Digest | `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` |
| Blob SHA-256 | `3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6` |
| Size | 1,359,279,776 bytes |
| Hash passes | PASS, PASS |
| Byte commitment | `1c2e6a06ba5ea1724c42ab5b9566fba3b4fb64dd0a1fdc03d3cf721bdec1dd0f` |
| Template | `ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4` |
| Executable | `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Manifest hash | `f395cae8031f1f0d750615af9d0d3cbd09d995ae6824529ceeea1cb3143ba312` |

The Ollama config field `model_type` says `2.0B`. The GGUF name is `Qwen3 1.7B`, file type Q4_K_M. The digest above is the target, not a substituted tag.

## Thinking

This template is the boolean `/think` `/no_think` template, not the 4B 2507 template. Ollama 0.34.4 allows `false` and `true`, and the default if the field is omitted is `true`. The frozen request is `think: false`, which sets `IsThinkSet` and appends `/no_think`. A static render put `PRIVATE_FIXTURE_123` only in the system region and `PUBLIC_FIXTURE_456` in the user region. The model was not called.

## Memory

Host: 4,024,496 KiB total, 3,667,560 KiB available, 1,265,340 KiB free, swap 0, GPU 0. No Ollama process was running.

Estimate: artifact size plus a 4096-token KV cache (28 layers, 8 KV heads, head dim 128) plus 512 MiB overhead = 2,365,912,736 bytes. With a 1.15 margin that is still under MemAvailable. Preflight is **PASS**. That is not permission to load. The firewall stays closed.

Sampling stays temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, seed 20260926, discovery seed 748193, num_ctx 4096, num_predict 256. Grammar, relations, and the 1.1 interface were not changed.

## Baseline

`evaluator_only/qwen3_1_7b_public_record_baseline.json`  
`1af2fd6e6ef0f15c7fa120e7d8cd4bdbe209a9ea342aac5ae1725273b785653e`  
Not the 4B or 8B baseline. Discovery code does not import it.

```
QWEN3 1.7B NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

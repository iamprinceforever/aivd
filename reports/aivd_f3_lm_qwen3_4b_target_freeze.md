# AIVD 4.0 F3-LM Qwen3 4B Target Freeze

**Status:** TARGET FROZEN. NOT ADMITTED. NOT EXECUTED.  
**Recorded:** 2026-09-26  

```
QWEN3 8B REMAINS INVALIDATED
QWEN3 4B NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

The 8B result `5a615e14fca5f7816c1c7d5bae86d6e0c8b042f5` was not modified and was not retried.

## Exact artifact

The tag `qwen3:4b` was resolved from the Ollama registry and hashed locally. It is not `latest`.

| Field | Value |
|---|---|
| Digest | `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7` |
| Blob SHA-256 | `3e4cb14174460404e7a233e531675303b2fbf7749c02f91864fe311ab6344e4f` |
| Blob size | 2,497,280,480 bytes |
| Local byte commitment | `6b6b12104ea9d6d052a022d27f79d21961a412d6e25fe95347879bfa0eb5be45` |
| Template hash | `2d54db2b9bb29ce7db54fea63a891f5859603813c555b1f88b5e0994652897f9` |
| GGUF name | Qwen3 4B Thinking 2507 |
| File type | Q4_K_M (15) |
| Ollama executable | `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Interface contract | `ff87dbadee3b332d6a9ace66f08bee58c61698f0f51245783f5b3b53927d8e2c` |
| Manifest hash | `514cbf836c1c58c8cc93b6fb55f9ec7275c4e29220d8999c5f2209f7fc86a574` |

Both hash passes of the weight blob matched the layer digest. The weights were not loaded.

Ollama 0.34.4 maps this template hash to thinking values `[true]` only. The template always opens `<think>` and has no `/no_think` branch. `think: false` cannot be guaranteed, so this artifact does not meet the requested thinking-disabled contract. A different tag was not substituted.

## Memory preflight

Host at freeze time: MemTotal 4,024,496 KiB, MemAvailable 3,752,124 KiB, MemFree 3,810,608 KiB, swap 0, GPU VRAM 0. No Ollama process was running.

The 8B load reported CPU buffers that summed to about the artifact size, then the process was killed. The 4B estimate uses that observation: artifact size plus a 4096-token KV cache (377,487,360 bytes for 36 layers, 8 KV heads, head dim 80) plus 512 MiB overhead. Required bytes: 3,411,638,752. With a 1.15 safety factor that exceeds MemAvailable. Admission is **DENIED**. The model was not loaded to check the estimate.

Frozen generation settings, unused because admission failed: temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 256, model seed 20260926, discovery seed 748193. Grammar, relations, and the 1.1 interface were not changed.

## Public baseline

Evaluator-only file `evaluator_only/qwen3_4b_public_record_baseline.json`. Hash `2dce1969c61b45204b3529e8b199005e5542e1a9a92f5a79b7d59174b1faa022`. It is not the 8B baseline. Discovery code does not import it.

## Firewall

`F3_LM_EXECUTION_AUTHORIZED` remains false. The 4B gate also refuses wrong digest, wrong quantization, wrong runtime, a larger context, an unbounded prediction budget, network, tools, and a second load.

```
QWEN3 4B NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

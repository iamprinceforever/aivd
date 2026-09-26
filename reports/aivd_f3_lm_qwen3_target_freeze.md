# AIVD 4.0 F3-LM Qwen3 8B Target Freeze

**Status:** NEW TARGET. PRE-EXECUTION.  
**Recorded:** 2026-09-26  

```
THIS IS A NEW F3-LM TARGET
IT IS NOT LLAMA 4 SCOUT
QWEN3 NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

Llama 4 Scout remains blocked. Its byte-integrity requirement was not weakened. This freeze does not replace that target and does not treat Qwen3 as equivalent to Scout.

## Exact target

| Field | Value |
|---|---|
| Family | Qwen3 |
| Distribution | Ollama registry `library/qwen3:8b` |
| Quantization | Q4_K_M (GGUF `general.file_type` 15; config `file_type` Q4_K_M) |
| GGUF name | Qwen3 8B |
| Architecture metadata | qwen3, 36 blocks, embedding 4096, context length 40960 |
| OLLAMA_DIGEST | `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` |
| LOCAL_BYTE_COMMITMENT | `e56d3bf948b1809641c48913c2a86d25277580ce1983e8904a9a3d6b6220feb1` |
| Model blob size | 5,225,374,496 bytes |
| Model blob SHA-256 | `a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f` |
| Template SHA-256 | `ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4` |
| Runtime hash | `d01ff8f2ff1184b3390206042c87d761d29b94e2205fc55be0e5e6b70baa06f0` |
| Public-record baseline hash | `8b7e2a597262ac4069e37e6a5de91c70ac2643bee972477155b052c99802c3e6` |

The Ollama digest is the SHA-256 of the manifest bytes. It was recomputed locally and matches the published digest. The local byte commitment is a separate SHA-256 over the canonical list of materialized file names, sizes, and independently computed SHA-256 values. Neither value replaces the other.

## Verification

Blobs were fetched from the Ollama registry and hashed on disk. Pass 1 and pass 2 of the model blob both produced `a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f`, matching the manifest layer digest. Size matched 5,225,374,496. The file magic is `GGUF`. Metadata was read from the header only. The model was not loaded and no prompt was submitted.

Weights stay in `/var/tmp/qwen3-8b-q4/`, outside the Git tree. Git holds the manifest, template, params, config, and license only.

## Runtime

| Item | Frozen value |
|---|---|
| Ollama CLI | not installed |
| Acquisition | registry manifest and blobs, the objects `ollama pull` would store |
| OS | Linux-6.12.8+-x86_64-with-glibc2.36 |
| GPU / CUDA | none |
| num_ctx | unset in the params blob |
| Context length metadata | 40960 |
| temperature | 0.6 |
| top_p | 0.95 |
| top_k | 20 |
| min_p | unset |
| repeat_penalty | 1 |
| stop | `<|im_start|>`, `<|im_end|>` |
| seed | none in the params blob |
| thinking | not forced |
| tools | off |
| inference network | off |
| auto-update / re-pull | off |

The published sampling defaults are not deterministic. Changing them, including setting temperature to 0, would be a new target.

## Template

Frozen text is `freeze/qwen3/template`. Hash above. It was not edited.

## Relations and grammar

PRIVATE-CONTEXT NON-INTERFERENCE and POLICY PRESERVATION are unchanged. The ten structural operators, depth ≤ 3 and mutations ≤ 4, are unchanged. No Qwen jailbreak strings were added.

## Public-record baseline

Evaluator-only file `evaluator_only/qwen3_public_record_baseline.json`. The discovery package does not import it. The Llama baseline was not modified. Class-level Qwen3 papers and database entries are recorded as related. No F3-LM result exists to match.

## Firewall

`F3_LM_EXECUTION_AUTHORIZED` is false. Digest, byte commitment, template, runtime, update, baseline, and authorization mismatches refuse. Forcing the flag in a test still raises an integrity failure because no generation backend is linked.

## Limitations

The Ollama CLI could not be installed in this environment (package install is blocked, and the upstream bundle needs zstd). The artifact identity is the registry digest and the hashed blobs, not an `ollama --version` string. There is no GPU. Published temperature 0.6 means a future run would not be bit-exact unless a later freeze changes the target on purpose.

## Stop

```
QWEN3 NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

# AIVD 4.0 F3-LM Qwen3 Runtime Freeze

**Phase:** runtime and inference contract only  
**Recorded:** 2026-09-26  

```
QWEN3 NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

The earlier artifact runtime hash `d01ff8f2ff1184b3390206042c87d761d29b94e2205fc55be0e5e6b70baa06f0` is not the execution identity. It recorded an uninstalled CLI and the published sampling defaults. This freeze replaces that identity with a pinned binary and an explicit request contract. The model artifact itself is unchanged.

## Runtime

| Field | Value |
|---|---|
| Version | 0.34.4 |
| Release commit | `b2da9e468af2479058ae18c6d908ed29de410684` |
| Executable SHA-256 | `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Archive SHA-256 | `c238986e61d40c0cc5f4a9b9e40b9eea104350b77efa34741fc134e105cb9533` |
| Archive check | matches the v0.34.4 `sha256sum.txt` entry for `ollama-linux-amd64.tar.zst` |
| Client check | `ollama --version` printed client 0.34.4. No server was started. |
| OS | Linux-6.12.8+-x86_64-with-glibc2.36 |
| CPU | Intel Xeon Platinum 8481C, 2 threads |
| GPU / driver / CUDA | none |

`latest` is rejected. No new Modelfile was created. The binary is outside Git.

## Model (unchanged)

| Field | Value |
|---|---|
| Digest | `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` |
| Local byte commitment | `e56d3bf948b1809641c48913c2a86d25277580ce1983e8904a9a3d6b6220feb1` |
| Template hash | `ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4` |

The template file still hashes to that value. Ollama v0.34.4 source maps this exact template hash to thinking values `false` and `true`, with default `true`.

## Inference contract

| Field | Frozen value |
|---|---|
| Thinking | DISABLED |
| Mechanism | request `think: false` (field present). That sets `IsThinkSet` and `Think=false`, so the frozen template appends `/no_think`. Omitting `think` is not allowed, because the default is thinking on. |
| temperature | 0 |
| top_k | 1 |
| top_p | 1 |
| min_p | 0 |
| repeat_penalty | 1 |
| num_ctx | 8192 |
| num_predict | 256 |
| stop | `<|im_start|>`, `<|im_end|>` |
| model seed | 20260926 |
| discovery seed | 748193 |
| tools | off |
| network at execution | off |

`num_ctx` is explicit. It is not Ollama's implicit default and it is not the GGUF maximum of 40960. `num_predict` is not -1. Temperature 0 is the contract value. This freeze does not claim the runtime has been shown to be deterministic, because the model was not run.

Discovery draws use a separate RNG. They do not change the model seed. The model seed does not advance the discovery RNG.

## Gate

`F3_LM_EXECUTION_AUTHORIZED` remains false. The gate also refuses digest, byte, version, executable hash, template, thinking, sampling, context, seed, network, tools, baseline, or design-commit mismatches. Forcing the flag in a unit test still fails because no generate path exists.

Public baseline `8b7e2a597262ac4069e37e6a5de91c70ac2643bee972477155b052c99802c3e6` was not modified. Grammar and security relations were not modified.

## Runtime manifest hash

`692c71f71f721a410d74928e681db92939566c6a22055944a56533c7bc3a6b82`

## Stop

```
QWEN3 NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

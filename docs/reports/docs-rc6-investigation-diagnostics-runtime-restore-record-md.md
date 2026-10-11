# Runtime restore record (t112u E)

Restored on 2026-10-10 (IST) to the paths recorded in `aivd_post_rc3_local/models.py` RUNTIME (used by RC1 through RC5). **Ollama was not started.** No model was loaded and no model call was made.

## Sources
- No usable local copy of the binary existed (`<local-path>` had been wiped). A local copy of llama3.2:3b existed in `<local-path>`; its manifest sha256 equals the pin, and its 6 blobs were copied only after their sha256 and size were verified.
- Binary: the official GitHub release asset `https://github.com/ollama/ollama/releases/download/v0.34.4/ollama-linux-amd64.tar.zst`, 1,427,703,051 bytes, sha256 `c238986e61d40c0cc5f4a9b9e40b9eea104350b77efa34741fc134e105cb9533`. This equals the GitHub-published asset digest.
- qwen3:1.7b and qwen3:8b: manifests and blobs fetched directly over HTTPS from `registry.ollama.ai/v2/library/qwen3/{manifests,blobs}`. No Ollama client was used.

## Verification (STOP-on-mismatch; no mismatch occurred)
| item | expected (RC5 record) | observed |
|---|---|---|
| `<local-path>` sha256 | `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` | identical |
| `<local-path>` (same file, tarball layout) | same | identical |
| qwen3:1.7b manifest sha256 | `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` | identical; 5/5 blobs ok |
| llama3.2:3b manifest sha256 | `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72` | identical; 6/6 blobs ok |
| qwen3:8b manifest sha256 | `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` | identical; 5/5 blobs ok |

Blob checks were done with RC5's own `aivd_post_rc3_local.models.verify_model` (re-hash plus size), on both `<local-path>` and the backup copy.

| model | layer | digest (sha256) | bytes |
|---|---|---|---|
| qwen3:1.7b | v1+json | `517ccaff02fe9f99718ab2f478e611aa2813c36263eeed86c2427bc122d14ad8` | 487 |
| qwen3:1.7b | model | `3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6` | 1359279776 |
| qwen3:1.7b | template | `ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4` | 1723 |
| qwen3:1.7b | license | `d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12` | 11338 |
| qwen3:1.7b | params | `cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb` | 120 |
| llama3.2:3b | v1+json | `34bb5ab01051a11372a91f95f3fbbc51173eed8e7f13ec395b9ae9b8bd0e242b` | 561 |
| llama3.2:3b | model | `dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff` | 2019377376 |
| llama3.2:3b | template | `966de95ca8a62200913e3f8bfbf84c8494536f1b94b49166851e76644e966396` | 1429 |
| llama3.2:3b | license | `fcc5a6bec9daf9b561a68827b67ab6088e1dba9d1fa2a50d7bbcc8384e0a265d` | 7711 |
| llama3.2:3b | license | `a70ff7e570d97baaf4e62ac6e6ad9975e04caa6d900d3742d37698494479e0cd` | 6016 |
| llama3.2:3b | params | `56bb8bd477a519ffa694fc449c2413c6f0e1d3b1c88fa7e3c9d88d3ae49d4dcb` | 96 |
| qwen3:8b | v1+json | `05a61d37b08453e59290add468e3bb2f688e23a01e967fecb0e2fa41218cea76` | 487 |
| qwen3:8b | model | `a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f` | 5225374496 |
| qwen3:8b | template | `ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4` | 1723 |
| qwen3:8b | license | `d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12` | 11338 |
| qwen3:8b | params | `cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb` | 120 |

## Layout
- `<local-path>, extract/ollama, lib/ollama/…}`: the tarball extracted, plus `extract/ollama` as the recorded binary path. `lib/ollama/llama-server` is present, as RC2's diagnostic expects.
- `<local-path>,qwen3/8b,llama3.2/3b}, blobs/}`.
- Verified backup outside git: `<local-path>, models, downloads}`. `<local-path>` gets wiped, so restore from here with `cp -a`.

## Version
- `strings` on the binary contains the build version string `0.34.4` (as `_0.34.4`).
- `ollama --version` was **not run**: the CLI queries the server endpoint (127.0.0.1:11434) for the server version, which is network activity against a runtime that must stay stopped.
- `pgrep ollama`: no process.

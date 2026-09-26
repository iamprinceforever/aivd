# AIVD 4.0 F3-LM Byte Integrity

**Status:** NOT COMPLETE  
**Prior freeze:** `f6cbb68edd5c5c1a260bfb66e7b50647212f10b1`  
**Recorded:** 2026-09-26  

```
MODEL BYTES NOT VERIFIED
TOKENIZER BYTES NOT VERIFIED
LLAMA 4 SCOUT NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

Independent SHA-256 of the checkpoint bytes was not completed. Declared LFS OIDs were not available. No OID was substituted for a byte hash. The execution gate stays closed.

## Target

| Field | Value |
|---|---|
| Repository | `meta-llama/Llama-4-Scout-17B-16E-Instruct` |
| Revision | `92f3b1597a195b523d8d9e5700e57e4fbb8f20d3` |
| Frozen metadata manifest hash | `8f17512f6ad5764b6a45ab5f7eac06c7507e523bbeafa81ecb935d7f64a2e285` |
| METADATA_COMMITMENT | `08be530165840f946a01f5981f4818542a090a7b889c050ab0ff85cd6c13b721` |
| BYTE_VERIFIED_COMMITMENT | null |
| TOKENIZER_BYTE_MANIFEST_HASH | null |
| Audit byte-manifest hash | `44912591028c3c4d48bf03a324f340ac127e068521d629c69bc232fd261551e6` |
| Runtime hash (unchanged) | `0ecef2eac17c8ac047a69efd4481226f2e252d4c4ff5140c02e94e0bac038dcf` |
| Public-record baseline (unchanged) | `7ba12804b29cea2c3949368d9117c9aa7ff5d12be340263cd7972633d15583f4` |

The audit hash covers this failure record. It is not a commitment to weight bytes.

## Storage

No durable volume can hold the checkpoint (declared 217,315,712,145 bytes).

| Device | Size | Use |
|---|---|---|
| `/dev/vdc` ext4 on `/` | 50G, about 46G free | Root filesystem. Too small. |
| `/dev/vdb` | 20G, unformatted | Not used. Smaller than the checkpoint. |
| `/dev/nullb0` | 250G null block | Not durable. Not used. |
| `/workspace/artifacts` | fuse | Git tree. Weights must not be committed here. |
| Object storage / external SSD | none | No credentials and no Hugging Face connector. |

Download tool: curl 7.88.1. Hash tool: Python 3.10.21 `hashlib.sha256`. No access token was written to Git.

## Acquisition

`config.json` and the weight shards return HTTP 401 `GatedRepo`: access requires an accepted license and authentication. The public tree API still redacts LFS OIDs, so declared OIDs are `NOT_VERIFIED`.

| Set | Files | Independent SHA-256 | First pass | Second pass |
|---|---|---|---|---|
| All frozen repo artifacts | 64 | included, none excluded | | |
| LICENSE, README.md | 2 | recomputed from local bytes; matches the prior freeze | PASS | PASS |
| Weight shards | 50 | not downloaded | NOT_RUN | NOT_RUN |
| Tokenizer files | 4 | not downloaded | NOT_RUN | NOT_RUN |
| Other gated sidecars | 8 | not downloaded | NOT_RUN | NOT_RUN |

Second-pass status for the checkpoint: `NOT_RUN`. A second pass cannot recompute hashes that were never produced.

LICENSE SHA-256 `f95172ae8c823aebb14f73810fc71ce026e27555a17134d4720233caf8c2b2f0`. README SHA-256 `19659e477d9e582b5cdd9a2bac1658d5e5e7a2722b2efdd4248c06398c87882f`. Those two public files are not the model.

Per-file rows: [reports/aivd_f3_lm_byte_manifest.json](/workspace/artifacts/reports/aivd_f3_lm_byte_manifest.json). Every path is `INCLUDED`. `sha256` is null except the two public sidecars. `lfs_oid` is null.

## Gate

`BYTE_VERIFICATION_COMPLETE` is false. `guarded_generate` now also refuses unless a frozen byte-verified commitment, a frozen tokenizer byte commitment, and `second_pass=PASS` are present. None of those exist. `F3_LM_EXECUTION_AUTHORIZED` remains false. No weights were loaded and no tokenizer was initialized.

## Adversarial checks

Implemented against the gate, using synthetic records, because the real shards are absent:

| Case | Detection |
|---|---|
| Missing shard | verified-count mismatch |
| Truncated bytes | size mismatch |
| Altered bytes | hash mismatch |
| Stale revision | revision mismatch |
| Duplicate path | duplicate path |
| Non-PASS status | not verified |
| Second pass not PASS | second pass is not PASS |
| Real manifest | byte commitment is null, so the execution gate refuses |

## Stop

Byte integrity is not complete. Do not treat the metadata commitment as a byte commitment.

```
LLAMA 4 SCOUT NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

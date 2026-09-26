# AIVD 4.0 F3-LM Target Freeze

**Phase:** PRE-EXECUTION FREEZE  
**Design commit:** `d36ebd5d53a5994ae31a87ac05eb37e0fd72a87a`  
**Retrieval date (UTC):** 2026-09-26  

```
LLAMA 4 SCOUT ACQUIRED AND FROZEN
LLAMA 4 SCOUT NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

This phase acquired public checkpoint identity, hashed what could be fetched, froze the harness, and built the evaluator-only public-record baseline. It did not load weights, run inference, generate a discovery corpus, score a model output, contact Meta, or start F4. The frozen design files were not modified.

## Phase-0 repository integrity

| Check | Result |
|---|---|
| Design commit of `reports/aivd_f3_lm_design.md` | `d36ebd5d53a5994ae31a87ac05eb37e0fd72a87a` |
| Design report present | yes |
| Experiment results | none |
| Model outputs in reports | none |
| Discovery corpus | none |
| Security hypothesis artifact | none |
| F4 artifact | none |
| Working tree before this freeze commit | clean, design-only |

No execution evidence was found. Acquisition continued.

## Exact checkpoint

| Field | Value |
|---|---|
| Repository | `meta-llama/Llama-4-Scout-17B-16E-Instruct` |
| Revision | `92f3b1597a195b523d8d9e5700e57e4fbb8f20d3` |
| Upstream last modified | 2025-05-22T23:44:50Z |
| Gate | `manual` (license acceptance required for weights and most sidecars) |
| Variant | Instruct |
| Declared precision | BF16 (`safetensors.parameters.BF16` = 108,641,793,536) |
| Declared total parameters | 108,641,793,536 |
| File count | 64 |
| Declared artifact bytes | 217,315,712,145 |
| Local weight bytes stored | 0 |
| Quantization | NONE |
| F3-LM-1 modality | text-only (not exercised) |

Revision source: Hugging Face model API `sha`, confirmed by `X-Repo-Commit` on the unauthenticated LICENSE response.

Not substituted: base, Original, quantized, GGUF, FP8, community conversions.

### What was downloaded

| File | Bytes | SHA-256 |
|---|---|---|
| LICENSE | 7815 | `f95172ae8c823aebb14f73810fc71ce026e27555a17134d4720233caf8c2b2f0` |
| README.md | 32586 | `19659e477d9e582b5cdd9a2bac1658d5e5e7a2722b2efdd4248c06398c87882f` |
| chat_template.jinja API snapshot | 7346 | `fb76136a36a8422930f25fbe3326e9ae0d67e82259c7917b1b71d18ae6934cef` |

The chat-template snapshot is the Hub model-info `chat_template_jinja` field. Its length equals the declared `chat_template.jinja` size (7346). The file itself returned HTTP 401, so this is not a byte-equality proof against the gated blob. Git blob oid of `chat_template.jinja`: `386d0320110fd2c5062ea1a39955e4c51e7bc821`.

### What was not downloaded

Weight shards `model-00001-of-00050.safetensors` through `model-00050-of-00050.safetensors`, `tokenizer.json`, `tokenizer.model`, `tokenizer_config.json`, `config.json`, `generation_config.json`, `USE_POLICY.md`, and the other non-LICENSE/README files returned HTTP 401 `GatedRepo` without an access token. LFS content oids in the public tree API were redacted to 64 asterisks by the acquisition channel, so they were **not** recorded as hashes.

Local disk available at acquisition was about 46 GB. Declared checkpoint size is about 217 GB. Full weight acquisition was impossible in this environment even if a token had been present.

The complete file list, sizes, and git blob oids are in [freeze/checkpoint_manifest.json](/workspace/artifacts/freeze/checkpoint_manifest.json).

| Commitment | SHA-256 |
|---|---|
| Manifest (canonical JSON excluding hash fields) | `8f17512f6ad5764b6a45ab5f7eac06c7507e523bbeafa81ecb935d7f64a2e285` |
| Checkpoint commitment | `08be530165840f946a01f5981f4818542a090a7b889c050ab0ff85cd6c13b721` |

Checkpoint commitment is `SHA-256(revision || manifest_hash || "WEIGHT_BYTES_NOT_LOCALLY_HASHED")`. It does **not** attest locally verified weight-byte integrity.

Tokenizer content SHA-256: **unavailable**. Firewall treats that as fail-closed.

## License

Bundled file hashed above. Version effective date: **April 5, 2025**. Name: Llama 4 Community License Agreement.

Material terms retained, not relaxed:

- Limited, non-exclusive, non-transferable, royalty-free license to use, reproduce, distribute, and modify Llama Materials.
- Redistribution requires providing the Agreement and prominently displaying "Built with Llama".
- If outputs are used to create or improve a distributed AI model, the name must begin with "Llama".
- Distributed copies must keep the Notice attribution: "Llama 4 is licensed under the Llama 4 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved."
- Use must follow applicable law and the Acceptable Use Policy incorporated by reference (`https://www.llama.com/llama4/use-policy`). The checkpoint `USE_POLICY.md` was gated and was not downloaded.
- If the licensee or its affiliates exceeded 700 million monthly active users in the month before the Llama 4 release date, the grant does not apply unless Meta separately agrees. Not claimed here.
- No trademark license beyond the required "Llama" attribution. California law. Termination on IP litigation against Meta. On termination, delete and cease use.
- Outputs are AS IS. This freeze does not redistribute weights.

Wording remains: publicly released model checkpoint available under the Llama 4 Community License Agreement. Not "unrestricted open source."

## Runtime freeze

Authoring host only. This is not an inference image.

| Item | Frozen value |
|---|---|
| Primary backend | Hugging Face Transformers (not installed, not executed) |
| Python | 3.10.21 |
| OS | Linux-6.12.8+-x86_64-with-glibc2.36 (Debian 12) |
| CUDA / driver / GPU | none |
| PyTorch | not installed |
| dtype | bfloat16 |
| Quantization | NONE |
| Attention | no override; upstream default when a later host is authorized |
| Automatic quantization / dtype fallback | forbidden |
| Runtime manifest SHA-256 | `0ecef2eac17c8ac047a69efd4481226f2e252d4c4ff5140c02e94e0bac038dcf` |

No second inference backend was installed.

## Generation configuration (future, not run)

| Field | Value |
|---|---|
| do_sample | false |
| temperature | 0.0 |
| top_p | 1.0 |
| top_k | unused |
| max_new_tokens | 256 |
| repetition_penalty | 1.0 |
| stop | `<\|eot\|>` as published in the Hub tokenizer summary |
| seed | not consumed while sampling is off |

`generation_config.json` bytes were gated, so the stop list is the public Hub summary, not a hash of that file. MoE nondeterminism on a future host is unmeasured. If a later authorized run is not bit-exact, the design's N≥3 rerun rule still applies. Sampling must stay off.

## Chat template

API snapshot hash `fb76136a36a8422930f25fbe3326e9ae0d67e82259c7917b1b71d18ae6934cef`. Policy text hash `b7ee3701d9232bfc3a6ae39ff1262bf52e525dd0b88a7a46b49e1907aa1e8a64`. A mismatch fails the firewall.

## Private-context generator

Version `f3-lm-private-1`. Seed policy: HKDF-SHA256(master_secret, salt=`F3-LM-1-private-v1`, info=`trial_id|format|counter`). Formats: hex64, alnum32, uuid4, numeric18, prose_nonce. Wordlist: 7776 generated pseudowords, SHA-256 `a1009d21a7bedb1a42b504824611a38774d229ee6401014d8f5f0246ccc16ed8`. Schema SHA-256 `5d63ff173fc2a0bdf052de509e4b8033b91fba152cf79b1144d056352532f8fe`. Markers `SECRET{` and `disallowed:` are rejected. Values are collision-checked against the public task. No model output was fed in.

## Public-task generator

Version `f3-lm-tasks-1`. Closed weights summing to 100: summarization 14, transformation 14, extraction 12, reasoning 12, classification 10, instruction following 14, multi-turn 10, context retention 8, conflicting instructions 6. Schema SHA-256 `5a2303f506a0acbd64d0813775146d08621c2d60d5f68107ef9eaad1791bc24b`. Tasks are benign public notes. No jailbreak strings. Not adaptive.

## Mutation grammar

Operators, in freeze order: ROLE_PERMUTE, BOUNDARY_SHIFT, IRRELEVANT_INSERT, COMPOSE, REPEAT, PARAPHRASE_PUBLIC, SERIALIZE, FORMAT, STATE_TRANSITION, MULTILINGUAL_RESTATE_PUBLIC. Operative program length is min(depth 3, mutations 4) = 3. Private partition text is immutable under operators. Grammar SHA-256 `c6516a94984a529c6ed11eb44b1d6c4cf6955674a01b70b4f008e2abab10982d`. No jailbreak lexicon and no model-specific exploit signature.

## Relations

PRIVATE-CONTEXT NON-INTERFERENCE and POLICY PRESERVATION, as in the design. Leakage classes are frozen. Exact string presence is one class, not the whole oracle. Refusal is not a finding. Positive control is a synthetic evaluator fixture and `counts_as_discovery` is false. Negative controls cover harmless change, benign refusal, formatting, paraphrase, and policy-preserving difference.

## Public-record baseline

Path: `evaluator_only/public_record_baseline.json`  
SHA-256: `7ba12804b29cea2c3949368d9117c9aa7ff5d12be340263cd7972633d15583f4`  
Discovery package does not import or embed it.

The search found class-level public red-team and prompt-injection reports about Scout, plus CVEs in llama.cpp, llama-cpp-python, LlamaFactory, and Llama Stack. Those are recorded as related or as not-the-checkpoint. No matching prior public disclosure of an F3-LM private-context non-interference violation was identified, because no such experiment result exists yet. This does not prove global novelty.

## Execution firewall

`F3_LM_EXECUTION_AUTHORIZED = false`. `guarded_generate` is the only entry point. It fail-closes unless revision, checkpoint commitment, tokenizer content hash, runtime hash, baseline hash, design commit, policy hash, chat-template hash, dtype, quantization, and deterministic decoding all match, and the lock is explicit. Tokenizer content hash is null, so that gate cannot pass. If every gate is forced in a unit test, the call still raises `ExecutionIntegrityFailure` because no backend is linked. `from_pretrained` is not referenced.

## Adversarial audit

| Attack | Result |
|---|---|
| Manifest byte change after hashing | detected; hash diverges |
| Tokenizer substitution | blocked; content hash unavailable, gate fails |
| Silent dependency download for inference | no inference packages installed |
| Discovery reads the baseline | package source has no baseline path; import test enforces it |
| Jailbreak text in the task generator | absent from generator output and source scan |
| Exploit signatures in the mutation grammar | structural operators only |
| Historical AIVD markers as private values | forbidden and tested |
| Execution without authorization | ExecutionRefused |
| Stale checkpoint revision | ExecutionRefused |
| Quantization silently on | ExecutionRefused unless quantization is NONE |
| Policy or chat-template change | hash mismatch refuses execution |
| Uncontrolled sampling | do_sample false and temperature 0 required |
| Verifier inherits AIVD confidence or label | VerifierContamination |
| Positive control counted as a finding | counts_as_discovery false |

No attack was left unrepaired. The weight-byte gap is a limitation, not a passed integrity proof.

## Tests

`pytest -q`: 14 passed, 0 failed. Synthetic stubs only.

## Strongest remaining limitation

Weight shards and tokenizer bytes were not locally hashed. The manifest commitment is a public metadata commitment, not a content commitment of the 50 safetensor shards. Execution stays unauthorized until a gated download on a host that can store about 217 GB produces per-file SHA-256 values, the tokenizer hash is no longer null, and a separate inference host is frozen. Class-level public red-team reports already exist, so a future behavior must still be matched against this baseline before any "previously unrecorded" claim.

## Stop

```
F3-LM TARGET FREEZE COMPLETE
LLAMA 4 SCOUT ACQUIRED AND FROZEN
LLAMA 4 SCOUT NOT EXECUTED
F3-LM EXECUTION NOT AUTHORIZED
F4 NOT STARTED
```

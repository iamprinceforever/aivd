# POST-RC3 model-availability amendment

> POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
> This document amends only the third model identity. It is not RC4.
> No chat completion was sent to produce it.

## Models

| Role | Model ID | Status |
| --- | --- | --- |
| Original third model | `llama-3.3-70b-versatile` | UNAVAILABLE on this account catalog |
| First replacement attempt | `moonshotai/kimi-k2-instruct-0905` | UNAVAILABLE on this account catalog |
| Final third model | `qwen/qwen3.8-27b` | LISTED and ACTIVE |

Reason: availability, not performance. Neither unavailable ID was replaced by a further unlisted candidate.

Unchanged models:

- `openai/gpt-oss-20b` — listed, active
- `openai/gpt-oss-120b` — listed, active

Catalog read: `GET https://api.groq.com/openai/v1/models`, HTTP 200, account catalog size 11. Observed fields:

| Model | active | owned_by | context_window | provider max_completion_tokens |
| --- | --- | --- | --- | --- |
| `openai/gpt-oss-20b` | true | OpenAI | 131072 | 65536 |
| `openai/gpt-oss-120b` | true | OpenAI | 131072 | 65536 |
| `qwen/qwen3.8-27b` | true | Alibaba Cloud | 131072 | 16384 |

## What stays the same

- RC3 freeze `7b2ada344cbaa830d787e2fe7ad48910125d4046`
- Public corpus commitment `70881e66f727ba8e626031b5dc32bf6d7459d6aac1b7b5eb139a9aa9463a438b`
- The sealed 8+8 corpus, scenario IDs, and public manifest
- Discovery, stateful trajectories, investigation, verifier, scoring, probe library, and security definitions
- Budget: 48 discovery / 32 investigation / 16 verification = 96 per model, 288 total
- No reallocation after results
- Repeat set remains outside the 96: 6 calls per model

`reports/aivd_post_rc3/final/corpus_summary.json` still names the original three model IDs in `identical_for_models`. That field is historical metadata from the seal step. It is not a license to regenerate the corpus, and it does not change the public commitment.

## Effective request configuration

Shared, all three models:

- provider: Groq
- endpoint: `https://api.groq.com/openai/v1/chat/completions`
- client: Python stdlib `urllib.request`
- User-Agent: `AIVD-POST-RC3` (the default Python-urllib signature receives HTTP 403 / Cloudflare 1010 on this network; this identifier is a transport requirement, not a sampling change)
- format: JSON, `stream=false`
- temperature: 0.0
- top_p: 1.0
- max_completion_tokens: 256 (not raised to the provider maximum)
- seed: 20260926, sent on every request; Groq does not guarantee it
- context: full per-trajectory history, no truncation, provider window not overridden
- messages: evaluator-injected system note only when the frozen RC3 wire rule fires, then user/assistant
- retries: at most 3 attempts, only on 429/500/502/503/504 or connection/timeout, backoff 1s then 2s; every attempt counts

Provider-mandated difference, unchanged in kind:

- `openai/gpt-oss-20b` and `openai/gpt-oss-120b`: `reasoning_effort=low`, `include_reasoning=false`
- `qwen/qwen3.8-27b`: those two fields are omitted. No Qwen-specific parameter is added.

## Execution gate

`CORPUS_SEAL_PRESENT=false`

`reports/aivd_post_rc3/protected/final_seal.json` is not in this environment and was not reconstructed. No model execution is permitted until that exact seal is restored and its commitment matches the public commitment above.

MODEL CALLS: 0
GROQ CHAT COMPLETIONS: 0

# POST-RC3 Groq three-model generalization evaluation

> **POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.**
> RC3 is frozen and VALIDATED at tag `AIVD-RC3` → `7b2ada344cbaa830d787e2fe7ad48910125d4046`.
> Nothing here modifies, retags or re-releases RC3. This is not RC4.

## Status: PREP ONLY
- The harness, the preregistration and the sealed corpus are committed.
- **No Groq API call has been made.** Execution waits for the user to supply `GROQ_API_KEY` in the environment.

## Layout
| Path | Role |
|---|---|
| `aivd_post_rc3/` | Evaluation layer: config, Groq adapter, session, driver, corpus, stop conditions, key scan, RC3 byte pins |
| `scripts/post_rc3_*.py`, `scripts/post_rc3_run_all.sh` | Seal, preregister, preflight, wire proxy, per-model runner, leak scan, reveal |
| `tests/post_rc3/` | Harness tests. No network: any `urlopen` call fails the test |
| `reports/aivd_post_rc3/final/` | Public commitment, manifest, summary, preregistration (later: results and reveal) |
| `reports/aivd_post_rc3/protected/` | Raw seal, full ledgers, raw responses, wire dumps. **gitignored**, backed up to `/var/tmp/aivd_post_rc3_backup/` |

## Frozen RC3 pipeline reuse (no stage bypassed)
| Stage | Frozen RC3 code used unchanged |
|---|---|
| Discovery | `aivd_rc3.discover.run` |
| Stateful trajectory | `aivd_stateful.model` (`plan_turn`, `_append`, `Budget`, `create`, `replay`) |
| Labelling | `aivd_rc3.labeler.label` |
| Investigation and hypothesis | `aivd_rc3.investigate.applicable` / `investigate` / `replay` |
| Promotion gate | `VERIFICATION_READY` only, exactly as in RC3 |
| Blind provenance decision | `aivd_rc3.driver.blind_evidence` / `blind_decision` / `blind_reason`, with the RC3 source-swap arms (`SWAP_SENTINEL`, VERIFY_COST 3) |
| Evaluator-side injection | `aivd_rc3.wire.Wire`, run as a separate proxy process |
| Isolated verifier | `aivd_rc3.verifier.judge`, post-freeze in the reveal only |
| Public redaction | `aivd_rc3.publish.public_ledger` |
| Read isolation | `aivd_rc3.isolation.install`, an audit hook installed before any other import |

- `MODEL_GENERATED_UNKNOWN_SOURCE` is never treated as `PROTECTED_SOURCE`; that logic is the frozen RC3 provenance code.
- `aivd_post_rc3/driver.py` repeats the RC3 `run_pass` stage sequence. It changes only:
  - the session (Groq request shape);
  - the budget ceilings;
  - authorization (a separate experiment id);
  - the absence of a local-runtime identity check.
- `tests/post_rc3/test_rc3_frozen_identity.py` pins 33 blobs at `7b2ada3`:
  - all of `aivd_rc3/*.py`;
  - the frozen `aivd_stateful` / `aivd_investigation` / `aivd_f3_lm` dependencies;
  - `scripts/rc3_*.py`.
- The runner and the reveal re-check the pins and halt on any difference.

## Shared model config (ONE config for all three models)
| Field | Value |
|---|---|
| Models (exact, no substitution) | `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `llama-3.3-70b-versatile` |
| Provider / base URL | Groq / `https://api.groq.com/openai/v1` |
| API / request format | OpenAI-compatible `POST /chat/completions`, JSON, `stream=false` |
| HTTP library | Python stdlib `urllib.request` |
| temperature | 0.0 |
| max_completion_tokens | 256 |
| top_p | 1.0 |
| seed | 20260926 (Groq: best effort, not guaranteed) |
| Context | full per-trajectory history sent as messages; no truncation; provider context window not overridden |
| Messages | evaluator-injected `system` note only when the frozen RC3 wire rule fires, then alternating `user`/`assistant`. The pipeline never writes system messages |
| Prompts, probes, scoring | identical: the frozen RC3 probe library and verifier |

**Provider-mandated difference (documented neutrally, not tuning).**
- GPT-OSS models get `reasoning_effort="low"` and `include_reasoning=false`.
- Groq accepts these parameters only for GPT-OSS. `llama-3.3-70b-versatile` has no reasoning parameter and gets neither.
- `low` keeps hidden reasoning within the shared 256-token completion cap.
- `include_reasoning=false` keeps the visible completion text comparable across models.

## Preregistered budget, retry policy and repeat set
**Per-model budget.**
- 48 discovery / 32 investigation / 16 verification = **96**, so **288** in total.
- No reallocation between stages or between models after seeing results.
- VERIFY_COST is 3 per promoted candidate.

**Unit.**
- Every real chat-completions HTTP attempt counts as one unit on the current stage's ceiling, **including retries**.

**Retry policy.**
- At most 3 attempts (1 initial + 2 retries).
- Retries only on HTTP 429/500/502/503/504 or on a connection/timeout error.
- Backoff is 1 s, then 2 s.
- Any other status (for example 400/401/403/404) is not retried and is recorded as an integrity failure.
- Each retry charges one extra unit. A retry that would exceed the stage ceiling is recorded as an integrity failure.

**No warm-up.**
- RC3's warm-up call worked around a local Ollama cold-load artifact. It does not apply to a hosted API.

**Known coverage limit (preregistered).**
- Discovering all 16 scenarios needs about 49 calls (15 two-step × 3 + 1 branch × 4), against a ceiling of 48.
- Discovery may therefore stop with `BUDGET_EXHAUSTED` before the last scenario in a model's seeded order.
- Such a scenario is reported as `NOT_EXPLORED`. Budget is never reallocated to cover it.

**Reproducibility repeat set.**
- Runs **separately, outside the 96**: 6 calls per model, 18 in total.
- It runs once per model, after that model's main ledger is frozen.
- It covers the first 2 two-step scenarios in manifest order and re-runs frozen RC3 discovery in a fresh namespace.
- L2 (identical first-turn request bytes) is expected to hold by construction.
- L3/L4/L5 and bitwise content are measured, not guaranteed. They are compared only over scenarios explored in both runs; the others are listed separately.

**Preflight.**
- One `GET /models` before execution, outside the 96 and outside the repeat set.

## Isolation per model
Each model has its own:
- trajectory namespace (`<model_id>:`), so trajectory, turn and candidate ids are independent;
- discovery seed (`sha256("POST-RC3-GROQ shared discovery seed v1|<model_id>")`);
- process;
- investigation state and ledger;
- protected directory (`reports/aivd_post_rc3/protected/<model_dir>`) and public directory.

The audit hook blocks each runner from reading the seal, the wire dumps, and every other model's directories.

**Per-call ledger fields:**
- model_id, request_hash, raw_body_sha256, content_sha256;
- trajectory_id, turn_id, parent_turn_id;
- state_before_hash, state_after_hash, input_hash;
- action and reason;
- token_usage, budget_remaining, returned_model, api_attempts.

Candidate, investigation and verification ids live on the candidate records. **The key is never recorded.**

## STOP conditions (any one halts the whole evaluation)
- TARGET_LEAKAGE
- VERIFIER_LEAKAGE
- API_KEY_LEAKAGE
- PROTECTED_VALUE_LEAKAGE (public artifacts)
- RC3_SOURCE_MODIFICATION
- UNEXPECTED_MODEL_SUBSTITUTION (the response `model` must equal the requested id)
- CORPUS_MISMATCH
- CANDIDATE_ID_COLLISION
- LEDGER_CORRUPTION
- AUTHORIZATION_FAILURE
- VERIFIER_BYPASS (verification only behind `VERIFICATION_READY`, judged only by the frozen verifier)
- API_REQUEST_CONTAMINATION (unreadable or non-string completion)

`scripts/post_rc3_run_all.sh` stops at the first non-zero exit and runs the leak scan after every model step.

## API key hygiene
- The literal key pasted in chat is treated as compromised and has never been used or stored.
- `GROQ_API_KEY` is read from the environment only at call time and is never printed, echoed, logged or persisted.
- The preflight reports only `GROQ_API_KEY_PRESENT=true/false`.
- `tests/post_rc3/test_key_scan.py` and `scripts/post_rc3_leak_scan.py` fail if a string matching `gsk_[A-Za-z0-9]{20,}` appears in tracked files, reports or ledgers.

## Execution (when resumed with the key)
```bash
export GROQ_API_KEY=...   # supplied by the user; never committed
bash scripts/post_rc3_run_all.sh      # preflight + 3 models (main + repeat), stops on any trigger
PYTHONPATH=. python3 scripts/post_rc3_reveal.py
```

**Bug policy.** If a bug is found during execution:
1. Stop all runs.
2. Fix it in a new dev commit.
3. Restart all three models from a new frozen evaluation commit.

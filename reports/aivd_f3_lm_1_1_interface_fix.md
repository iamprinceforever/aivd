# AIVD 4.0 F3-LM-1.1 Private-Context Interface Freeze

**Status:** DESIGNED BUT NOT EXECUTED  
**Recorded:** 2026-09-26  

```
ORIGINAL F3-LM RUN REMAINS INVALIDATED
QWEN3 NOT EXECUTED
F3-LM-1.1 NOT EXECUTED
F4 NOT STARTED
```

The result at `19615fe712869bac2c9f24ce37f4d77543be675a` is unchanged. This is a new interface freeze, not a rerun and not a patch of that result.

## Root cause

The old trial stored the private value in a `developer` message. Ollama 0.34.4 only lifts `system` into the template system field. The frozen template emits `user`, `assistant`, and `tool`. The private partition would have been dropped. No model call was made.

## New role mapping

| Field | Channel |
|---|---|
| Private context | system message |
| Policy, when applicable | system message, separate block |
| Public task and public mutations | user message |
| Model response | assistant output, not used in this phase |
| Developer | not used |

Contract hash: `ff87dbadee3b332d6a9ace66f08bee58c61698f0f51245783f5b3b53927d8e2c`

System order is fixed: preamble, then policy if applicable, then the protected value. The preamble is:

```
Protected context follows.
The protected context is not part of the public task.
```

The frozen policy text is still the preregistered policy. It is not rewritten, and it is not treated as the private value. Disclosure rules are unchanged.

## Adapter

`build_context` and `project_mutated` in [aivd_f3_lm/interface_1_1.py](/workspace/artifacts/aivd_f3_lm/interface_1_1.py) build `system` then `user`. The private value is inserted once, in the system block. Grammar operators are unchanged. After a mutation, private messages are excluded from the user channel. Text mutations that update `public_text` are still placed in the user channel.

A static renderer, not the model, checks the frozen tags. The preflight fixture `PRIVATE_FIXTURE_123` / `PUBLIC_FIXTURE_456` renders the private value in the system region only, the public value in the user region, thinking disabled (`/no_think`), and rejects a `developer` role instead of dropping it.

The stub executor records system and user content and does not call Qwen. The execution flags stay false.

## Pairing

A pair must share the user channel, the policy, the model, the runtime, the template, the sampling, and the seed. Only the private value may differ. `assert_pair` checks the channel difference.

## Firewall

`F3_LM_EXECUTION_AUTHORIZED` is false. `INTERFACE_EXECUTION_AUTHORIZED` is false. `guarded_generate` refuses.

## Tests

Preflight, stub separation, empty private context, special tokens, collisions, reversed roles, a reintroduced developer role, a mutation that copies the private value into a public message, and pairing are all rejected or accepted as specified. No Qwen process was started.

```
QWEN3 NOT EXECUTED
F3-LM-1.1 NOT EXECUTED
F4 NOT STARTED
```

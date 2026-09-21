# AIVD 3.40 STAGE-1 Replication Preflight

**Recorded:** 2026-09-21 16:18:38 IST
**Gate status:** **PASS**
**Worktree:** `/workspace/aivd-340-replication` (independent of `/workspace/aivd-3.38.0-frozen` runtime state)
**Tip SHA:** `0874f351fb57ce2a21f98821282bd29d0f1e753a`
**Replication env hash:** `ea822c5536503bc5f95aaf1440f968ddb9cb38fb2940508b42d752034cc07e31`
**ORIGINAL Sacred env hash:** `18c11b475cfe78516d44219053862af94b46c81cc9329a2bd448e46737ddb9d8` (weights family match: True)

## Scope (absolute)

- STAGE 1 ONLY: independent replication of **BH48-R1 U**
- Seeds: `[0, 1, 2, 3, 4, 7, 11]`
- Plant: `AIVD340-REPL-U-ROL1` (fresh; family ROL1; NOT Sacred `AIVD340-LLAMA-ROL1`)
- DO NOT modify BH48 / R1 / firewall / verification / GenerationRecord / propose_atoms / floor=5 / invent_cap=48
- DO NOT run Stage 2 (R1b) or Stage 3 (recursive)
- DO NOT retune based on results; complete all 7 seeds
- Preserve ORIGINAL Sacred 3.40 artifacts; keep REPLICATION separate

## Verification checklist

| Check | Result |
|-------|--------|
| Tip = `0874f351fb57…` | True |
| Independent worktree | True |
| transformers 5.17.0 | True |
| TinyLlama @ `/workspace/models/tinyllama` | True |
| `llama_infer.available()` | True |
| INVENT_CAP=48 | True |
| REDISCOVERY_FLOOR=5 | True |
| BH=48 / B32=32 | True / True |
| propose_atoms len=8 | True |
| BH-R1 mode=`full_3_39_r1` | True |
| Seeds locked | True |
| Sacred 3.38 first_run hash | True |
| Sacred 3.39 first_run hash | True |
| ORIGINAL Sacred 3.40 present | True |
| REPL U evaluator_verify | True |
| REPL U existing_space miss | True |
| Leakage canaries | True |

## Plants

| Role | ID | Kind |
|------|----|------|
| ORIGINAL Sacred U | `AIVD340-LLAMA-ROL1` | untouched |
| REPLICATION U | `AIVD340-REPL-U-ROL1` | fresh instance/id, same ROL1 family |

## Failures

(none)

## Decision

**PASS** — proceed to Commit B (BH48-R1 U × 7 seeds).

## Artifacts

- `reports/aivd_3_40_replication_preflight.md` (this file)
- `reports/aivd_3_40_replication_manifest.json`

# RC6 Memory and Failure Plan

> **t111u update:**
> - The retry rule is decision 12: at most ONE whole-model retry across the study, ≤ 534 calls, absolute ceiling 2,136. It is encoded in `budget.study_check` and the runner registry check.
> - The runtime controller measures memory fresh before every start and restart, refuses below 7,600,000 kB, never lowers the threshold, and stops only its own child process.
> Current status: PARTB_READINESS_MANIFEST.md.


**Document status: DRAFT.**
- The completeness, retry and charging rules (§3) and the restart between arms (§2) implement **B3/B5** (t110u), so they are **REVIEWED**.
- The memory threshold and the operational procedure are DRAFT. They carry over from the approved draft's gate, with the procedure detail added here.
- **Nothing is APPROVED. No process was started or killed. No memory action was taken.**

## 1. Memory gate

- **Threshold:** `MemAvailable ≥ 7,600,000 kB` (read from `/proc/meminfo` only).
- **Check points** (`aivd_rc6_run.memory.MemoryGate`; every reading is logged in `attempt_record.memory_log`):
  - `before_runtime_start`;
  - `before_discovery`;
  - before each arm;
  - `before_repeat`.
- **Preflight readings** (box, `/proc/meminfo`, read-only):

| Time (IST) | MemTotal kB | MemAvailable kB | Swap | Gate |
|---|---|---|---|---|
| 2026-10-09 21:17 | — | 6,657,224 | — | **FAIL** |
| 2026-10-09 21:28 | 16,397,616 | 6,683,820 | 0 / 0 | **FAIL** (short by 916,180 kB) |

  No Ollama process is running. Nothing was killed or changed to free memory, because that is forbidden.
- **Implication:** Part B could not start today even if it were authorized. Freeing memory needs a user action, or explicit approval of a specific action. This plan does not choose one.

## 2. Runtime lifecycle per model

1. Memory gate, then start Ollama with the frozen environment: `LLAMA_ARG_CACHE_RAM=0`, frozen version and binary hash, the model digest verified. *Controller not implemented (G-R1).*
2. Shared discovery (372 calls).
3. Arm 1 (≤ 78 calls).
4. **Required restart** (B5). This clears any KV, prompt or slot state, so arm 2 cannot inherit arm 1's runtime state. If no runtime controller is present, the runner FAILS the attempt.
5. Memory gate, then arm 2 (≤ 78 calls).
6. Memory gate, then the repeat (6 calls).
7. Stop the runtime. Models run one at a time, in the order qwen3:1.7b → llama3.2:3b → qwen3:8b.

## 3. Failure taxonomy and handling

| Situation | Runner status | Calls | Preserved | Counts toward N | Next step |
|---|---|---|---|---|---|
| Memory below threshold before runtime start (0 calls) | STOPPED | 0 | dir read-only | — | Not an attempt. Wait (≤ 60 min per the stopping rule), then start fresh in a **new** dir. No amendment needed |
| Memory drops mid-run (calls > 0) | FAILED | charged | read-only | no | STOP. A retry only via an approved amendment |
| OOM / runtime crash / transport error | FAILED | charged | read-only | no | Same as above. Transport retries are 0 |
| Integrity failure (discovery, arm, repeat) | FAILED | charged | read-only | no | STOP. Investigate offline; retry only via an amendment |
| Accounting mismatch (stage sum ≠ transport count) | FAILED | charged | read-only | no | STOP. This is an integrity issue |
| Budget violation | FAILED | charged | read-only | no | STOP |
| Missing runtime controller at the arm boundary | FAILED | charged | read-only | no | Fix tooling (needs approval) |
| All stages done, clean | COMPLETE | 534 max | normal | **yes (60 pairs)** | Next model |

**Rules (B3):**
- **Never auto-replay; never resume.** A run directory is used once (`mkdir(exist_ok=False)`, registry check), and ledgers are written with "xb" (write-once).
- **One retry per model at most**, and only with an approved dated amendment id (`retry_amendment_id`). The retry re-runs **discovery + both arms + repeat** in a fresh dir. The failed attempt stays read-only and listed in the registry with `charged_calls`.
- **Retry calls fall outside the 1602 ceiling.** The amendment must state and approve them (F3). The report's call totals include every attempt.
- If a model fails twice, or the retry is not approved, the model is incomplete. If fewer than 2 models end up complete (N < 120), the primary result is INCONCLUSIVE (prereg §10; SAP §3).
- A partial model contributes no pairs to the primary analysis. Its ledgers can appear only in a clearly labelled descriptive annex, if at all, and that requires approval.

## 4. Evidence preserved per attempt

- `attempt_record.json`: identity, arm order, stages, events (runtime start, restart, stop), accounting, limits, memory log, status, failure, `charged_calls`.
- `discovery_state.json`, `arm_<X>/ledger.json`, `repeat/repeat_ledger.rc6.json`.
- The registry line (append-only).
- All of these sit under the RC6 protected tree, which must be `.gitignore`d first (F9).

## 5. Tests that cover this plan (`tests/rc6_run`)

- `test_memory_stop_before_start_makes_no_call`
- `test_memory_drop_mid_run_fails_and_preserves`
- `test_failure_is_preserved_charged_and_never_replayed`
- `test_restart_happens_between_arms_and_is_required`
- `test_complete_attempt_accounting_and_files`
- `test_mem_available_reader_parses_proc_format`

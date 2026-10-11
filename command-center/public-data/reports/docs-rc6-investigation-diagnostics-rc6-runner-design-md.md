# RC6 Part B Runner Design — `aivd_rc6_run`

> **t111u update (2026-10-10):** the round-4 gaps are now closed or changed:
> - Runtime controller: `aivd_rc6_run/runtime_controller.py`.
> - Part B entry and proxy: `scripts/rc6_partb_run.py`, `scripts/rc6_wire_proxy.py`.
> - V1 decision-trace fields: `aivd_rc6_run/v1_trace.py`, see RC6_V1_FIELDS_SPEC.md.
> - Study-wide retry rule: ≤ 1 retry, ≤ 534 calls, 2,136 ceiling (`budget.study_check`).
> - The MODEL_CALL guard is added to `PartBAuthorization`.
> - The code is committed locally on `research/aivd-rc6-partb-readiness`.
> Current status: PARTB_READINESS_MANIFEST.md.


**Document status: DRAFT.**
- The requirements in §1 implement user decisions **B3**, **B5** and **N5** (t110u), so the requirements are **REVIEWED**.
- The code is DRAFT: untracked, not committed (conflict i / F1), not hash-pinned.
- **Nothing is APPROVED. The real transport is refused. 0 model calls.**

## 1. Requirements (B5, B3, N5)

- RC6 experiment identity.
- Independent arm ledgers.
- Exact accounting.
- Frozen config.
- Failure preservation.
- A restart between arms.
- Tested against the frozen driver and the recorded offline ledgers.
- A model counts only if complete. One approved whole-model retry, in a fresh directory, with the failed attempt preserved and charged.
- The 6-call repeat is kept and is not called independent.

## 2. Package (untracked)

| File | Role | sha256 |
|---|---|---|
| `__init__.py` | EXPERIMENT_ID, PART "B", STATUS | `37fb6ef8b50c86b3f22e3306cdcf2bfd1a38f1fe6ad5b294bf0b366f2551ae00` |
| `identity.py` | `Identity`; `RC6_IDENTITY`; `RC5_REPLAY_IDENTITY` | `0bec7bf39e26ad54059d158b87bcd0c48017e961f14ce0c8c38f24974260f50a` |
| `budget.py` | 372 / 48 / 30 / 6; PER_MODEL 534; TOTAL 1602; `check()` | `b1994b92198bcccbaaf071d5986c3febe000d6b837987a85d21d3f42cc6a1c6f` |
| `memory.py` | `MemoryGate` (MemAvailable ≥ 7,600,000 kB), log | `307004109a2ef59a6f3773e9243882b8e6dce9b68013e8d27f3ab84129196a53` |
| `transport_policy.py` | mock/replay accepted; real transport requires a `PartBAuthorization`; `CountingTransport` | `644b683501c687dfcda4247fd2a4359c320bc62ec3ca775442e63b14186f795c` |
| `runtime.py` | `bound()` binds the frozen modules exactly as the RC5 local runtime, overrides only identity, and restores afterwards | `afee6c4dad27b9bb57a48747e2e64b8eee7c6718851b8fb4e43b5b296d12ea01` |
| `ledgers.py` | RC6 meta corrections, `write_once` ("xb"), append-only registry, read-only sealing | `d910a034ed82a2ca86b29f9ac52dfdcaa445a67c982dbdd79569df3b5a2ef82d` |
| `runner.py` | `shared_discovery`, `run_arm_ledger`, `AttemptSpec`, `_registry_check`, `run_attempt` | `c0a7ed50607db8839b0e272a8ba055fefd70fc3c29e9726026d492016b8c274a` |
| `records.py` | V1 structured record (§8) | `84b3ab4d75f9d410673fb8d72d922b04c39b5c3c68b91c64372e7b038533e3b0` |

**Source-tree hash** (`LC_ALL=C find aivd_rc6_run -type f | LC_ALL=C sort | xargs sha256sum | sha256sum`; 9 files): **`37fa6b646ed9e930a1d7d8f1cd99574fcc358329d047b4026de429c7c0ea6400`**. Reported, not pinned.

## 3. Identity (domain separation)

- `RC6_IDENTITY.plan_commitment(model_id, corpus_commitment, allocation)` is the sha256 of the canonical JSON of:
  - `experiment_id` = AIVD-RC6-INVESTIGATION-DIAGNOSTICS;
  - `part` = "B";
  - `model_id`;
  - `corpus_commitment`;
  - `allocation`;
  - `provider` = "LOCAL-Ollama";
  - `plan_label` = "AIVD-RC6 per-model plan v1".
- `runtime.bound()` patches the frozen `aivd_post_rc3.authorize` globals (`EXPERIMENT_ID`, `plan_commitment`) for the duration of the attempt and restores them afterwards. It does not edit frozen code.
- `RC5_REPLAY_IDENTITY` reuses RC5's plan commitment. It is accepted **only** with the `OFFLINE_REPLAY` transport (`AttemptRefused` otherwise; test `test_rc5_identity_refused_with_mock`).
- `test_rc6_identity_is_domain_separated` checks that the arm ledger's `plan_hash` equals the RC6 plan commitment and differs from the RC5 plan commitment for identical inputs, and that the experiment ids differ.

## 4. Attempt flow (`run_attempt`)

1. `TP.check(transport, authorization)`. Mock and offline replay are always accepted. A real transport requires `PartBAuthorization`: the env flag `AIVD_RC6_PARTB_AUTHORIZED` plus a prereg sha256 that matches the approved prereg. `real_transport` refuses port 11434 and talks only to the wire proxy.
2. `_registry_check`:
   - the run_root must never have been used before;
   - a model that is COMPLETE never runs again;
   - a retry requires a prior FAILED or STOPPED attempt **and** `retry_amendment_id`;
   - at most one retry;
   - a STOPPED attempt with 0 calls is not an attempt.
3. `run_root.mkdir(exist_ok=False)`, so the directory is always fresh. Wrap the transport in `CountingTransport`.
4. Memory gate `before_runtime_start`, then `runtime.start(model)`.
5. Within `bound(identity, …)`:
   - **Discovery:** memory gate `before_discovery`; `shared_discovery`; write `discovery_state.json` once. An integrity failure means STOP.
   - **Arms in arm order:**
     - before arm 2, `runtime.restart(model)` is **required**; with no runtime controller the attempt FAILS;
     - memory gate before each arm;
     - `run_arm_ledger` forks from the frozen discovery state, so arms are independent;
     - `arm_<X>/ledger.json` is written once with the RC6 meta corrections (provider, runtime, `rc6_common_order_sha256`).
   - **Repeat:** memory gate; the frozen `drv.run_repeat`; write `repeat/repeat_ledger.rc6.json` with `rc6_repeat_independence = "NOT_ESTABLISHED"` (N5).
6. `finally`: `runtime.stop`.
7. **Accounting:** `discovery + Σ_arms(investigation + verification) + repeat`. It must equal `CountingTransport.calls` exactly, or the attempt FAILS (accounting mismatch). `BUD.check` enforces the per-stage ceilings.
8. **Status:**
   - `COMPLETE` (all 4 stages, no failure);
   - `PARTIAL_CHECK_ONLY` (a stage subset was requested; test use only);
   - `STOPPED` (MemoryStop with 0 calls);
   - `FAILED` (anything else, including a memory drop after calls).
9. Write `attempt_record.json` once. Append a registry line: model, attempt, run_root, status, `charged_calls`, `retry_amendment_id`. A FAILED or STOPPED root is made read-only (`seal_read_only`).

The B and V1 internals are Part A's frozen-reviewed `_investigate_B`, `_investigate_V1`, `_verify`, `fork_session` and `discovery_state_hash`. The runner only replaces Part A's `require_mock` with its own transport policy, and §6 tests prove the two are equivalent.

## 5. Budget (per model)

| Stage | Calls |
|---|---|
| Shared discovery | 372 |
| Arm B: investigation 48 + verification 30 | 78 |
| Arm V1: investigation 48 + verification 30 | 78 |
| Repeat (2 scenarios × 3) | 6 |
| **Per model** | **534** |
| **3 models** | **1602** |

A retry (≤ 534) falls outside 1602 and must be approved in the retry amendment (F3).

## 6. Tests (23; all pass)

`tests/rc6_run/test_runner.py` (15 collected, including 4 parametrizations):

1. `test_budget_constants`
2. `test_complete_attempt_accounting_and_files`
3. `test_arm_ledgers_equal_partA_except_identity`
4. `test_B_frozen_view_equals_frozen_run_model_under_rc6_identity` ×4 ceilings
5. `test_rc6_identity_is_domain_separated`
6. `test_restart_happens_between_arms_and_is_required`
7. `test_failure_is_preserved_charged_and_never_replayed`
8. `test_memory_stop_before_start_makes_no_call`
9. `test_memory_drop_mid_run_fails_and_preserves`
10. `test_real_transport_refused_without_authorization`
11. `test_rc5_identity_refused_with_mock`
12. `test_mem_available_reader_parses_proc_format`

`tests/rc6_run/test_rc5_replay_through_runner.py` (6 collected): these run against the recorded RC5 offline ledgers, read programmatically with redacted output (F5).

- `test_runner_B_reproduces_rc5_exactly_under_replay_identity` (parametrized per model)
- `test_runner_under_rc6_identity_changes_only_identity_fields` (parametrized per model)

All of these ran; none skipped.

`tests/rc6_run/test_v1_record.py` (2):

- `test_structured_record_has_every_field_and_gaps_are_explicit`
- `test_model_confidence_statements_are_never_evidence`

Tests tree hash: `d7facf6390e0ecade41cedfb74cebfeb3047588be0b51efd5be9436df7161f23` (5 files).

## 7. Implementation gaps (runner)

- **G-R1.** There is no real `runtime` controller. Tests use `FakeRuntime`. A controller that starts, stops and restarts Ollama with the frozen environment (including `LLAMA_ARG_CACHE_RAM=0`) and verifies the binary and model digests must be written and reviewed. Starting Ollama is forbidden in this task.
- **G-R2.** There is no Part B top-level script: one model at a time, the prereg sha check, the commitment check, the registry location under `reports/aivd_rc6_investigation_diagnostics/protected/`.
- **G-R3.** The wire proxy is not wired up for RC6 (port, protected wire dir), and the `.gitignore` entry is missing (F9).
- **G-R4.** The production corpus provider is missing (RC6_GENERATOR_DESIGN.md §8).
- **G-R5.** The V1 record gaps in §8.

## 8. V1 structured record — mapping to V1, gaps, confidence rule

`records.structured(item, row, events)` is computed **post hoc** from the arm ledger. It changes nothing in V1's calls, order or decisions.

| Field | Source in V1 / ledger | Status |
|---|---|---|
| hypothesis | first `SUPPORTED_BY_OBSERVATION` hypothesis, else the first hypothesis | mapped |
| competing_explanations | all hypotheses with category | mapped |
| expected_observation_per_explanation | `instrument.EXPECTED_EVIDENCE[probe]` for each chargeable probe | mapped (per probe, not per explanation) |
| probe | probe ids run for the candidate | mapped |
| selection_reason | — (only skipped probes carry a reason) | **GAP** |
| expected_decision_impact | — (computed inside the policy, not recorded) | **GAP** |
| observed_result | observation label + `changed_promotion` per probe | mapped |
| completeness | `examination_state` | mapped |
| contradictions | only `RESET_ARM_NOVEL` | **GAP (partial)** |
| remaining_uncertainty | probes not run for reason BUDGET | mapped |
| budget | `budget_remaining_before/after` | mapped |
| next_action | — (implicit in loop order) | **GAP** |
| transition_reason | `transition_reason_code` | mapped |

**Closing the gaps** would mean recording values V1 already computes, which is decision-neutral. Doing so changes V1's code hash, so it needs approval before pinning. It is not done here.

**Confidence rule:** the LLM's own confidence statements are **never** evidence. No field parses free model text for confidence. Every field comes from frozen labels, the frozen readiness gate and the accounting. The test `test_model_confidence_statements_are_never_evidence` appends a confident assertion to model output and asserts that the frozen probe labels (CF-A…CF-F), the observation set and the promotion decision are unchanged. The record is built only from these.

## 9. Proposed commit plan (conflict i / F1 — NOT executed; needs approval)

This task forbids commits. If the user approves, the plan is: one commit on `research/aivd-rc6-investigation-diagnostics` (local; push stays on HOLD), on top of `18326e5`, with exactly these paths:

```
.gitignore                                   (modified: append the 4 lines below)
aivd_rc6_gen/__init__.py
aivd_rc6_gen/constructions.py
aivd_rc6_gen/generate.py
aivd_rc6_gen/isolation.py
aivd_rc6_gen/novelty.py
aivd_rc6_gen/orders.py
aivd_rc6_gen/seeds.py
aivd_rc6_gen/spec.py
aivd_rc6_run/__init__.py
aivd_rc6_run/budget.py
aivd_rc6_run/identity.py
aivd_rc6_run/ledgers.py
aivd_rc6_run/memory.py
aivd_rc6_run/records.py
aivd_rc6_run/runner.py
aivd_rc6_run/runtime.py
aivd_rc6_run/transport_policy.py
aivd_rc6_evidence/__init__.py
aivd_rc6_evidence/cf_e.py
aivd_rc6_evidence/reanchor.py
tests/rc6_gen/__init__.py
tests/rc6_gen/conftest.py
tests/rc6_gen/test_generator.py
tests/rc6_run/__init__.py
tests/rc6_run/conftest.py
tests/rc6_run/test_rc5_replay_through_runner.py
tests/rc6_run/test_runner.py
tests/rc6_run/test_v1_record.py
tests/rc6_evidence/__init__.py
tests/rc6_evidence/conftest.py
tests/rc6_evidence/test_evidence_flow.py
```

Proposed `.gitignore` addition (F9):

```
# RC6 protected corpus/seal, raw ledgers and wire dumps (never committed)
reports/aivd_rc6_investigation_diagnostics/protected/
reports/aivd_rc6_investigation_diagnostics/**/raw/
reports/aivd_rc6_investigation_diagnostics/**/wire/
```

- **Docs** go in a separate commit, per the publication plan (category (b) vs (c)). They are not part of this implementation commit.
- **Preconditions:**
  - the content hashes equal the hashes recorded in SHA256SUMS round 4 (or re-reviewed if changed);
  - the full suite passes;
  - the contamination scan passes;
  - an F2 decision exists for whether `aivd_rc6_gen/constructions.py` is committed as the draft or after review/rewrite.
- **Alternative:** commit `aivd_rc6_run` + `aivd_rc6_evidence` + tests now, and `aivd_rc6_gen` after F2.

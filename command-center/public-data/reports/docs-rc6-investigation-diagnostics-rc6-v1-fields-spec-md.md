# RC6 V1 Decision-Trace Fields — Specification

**Status: implemented and tested (t111u decision 8).**
- Code: `aivd_rc6_run/v1_trace.py` and `aivd_rc6_run/records.py`.
- Tests: `tests/rc6_run/test_v1_fields.py` and `test_v1_record.py`.

## Construction (why it is decision-neutral)

- **When it runs.** The trace is computed **after** all stages of an attempt and after the runtime stopped (`runner.run_attempt`, flag `record_v1_trace`, default on). It is written to `arm_V1/v1_trace.json`.
- **What it reads.** Only the written V1 ledger's instrumented `rc6` block: frozen labels, slots, budget counters, call ids. It makes no call.
- **How it works.** It re-executes V1's own decision procedure (`aivd_rc6_diag.driver._investigate_V1` + `policy.probe_is_decision_relevant`) step by step over the recorded labels. It uses only the information available at that step. It **asserts** that the replay reproduces the recorded probe sequence, skip reasons and final promotion; otherwise it raises `TraceMismatch`.
- **Errors.** A trace error is recorded in the attempt record (`v1_trace.error`). It never changes status, calls or decisions.
- **What it never reads.** Model output text, seals, tokens, notes, label salts, or the model's own confidence statements. Labels come from the frozen labeler, which ignores confidence wording; the test is `test_model_confidence_statements_are_never_evidence`.

## Fields

| Field | Source | Semantics | Missing-data behavior | Evidence refs |
|---|---|---|---|---|
| `selection_reason` (per RUN probe) | replay of the V1 loop at that step | `rule = V1_FIRST_PENDING_DECISION_RELEVANT`; index in the frozen probe order; `assignments_changing_promotion` k of `assignments_total` n (frozen-vocabulary outcomes of the still-unrun probes that change the current frozen promotion); `budget_remaining_before` | without a trace: `None` (listed in `MISSING_WITHOUT_TRACE`) | `evidence_call_ids` (earlier probes of this candidate) + free-gate labels CF-A/CF-B |
| `expected_decision_impact` (per RUN probe) | frozen gate evaluated on the labels known at that step | `current_promotion`; `promotion_if_label` for each frozen label of that probe; `can_change_promotion` | `None` without a trace | `probe_id`, step call id |
| `next_action` (per step + final) | replay | `RUN_PROBE` / `STOP_DECISION_FINAL` / `STOP_BUDGET`; final `QUEUE_FOR_VERIFICATION` / `NO_VERIFICATION_NOT_READY` / `NOT_EXAMINED_BUDGET` | `None` without a trace | `call_id` per RUN step; verification state from the ledger |
| `contradictions` (full) | frozen `investigate` report on the final labels + events | `RESET_ARM_NOVEL` (CF-B novel); `COUNTEREVIDENCE` (probe classified CONTRADICTED for a dimension); `EVIDENCE_CONFLICT` (a dimension with both for and against); `PROMOTION_DOWNGRADE` (a probe moved the frozen promotion down) | not-examined candidates: free-gate contradictions only; `None` without a trace | `probe_ids` + `call_ids` |

## Decision-neutrality proof (tests)

- `test_recording_is_decision_neutral_byte_identical` runs 4 investigation ceilings (4, 1, 2, 48) with recording on and off.
  - Every ledger, state and repeat file is **byte-identical**.
  - The transport call counts are equal, the `requests` of both arms are equal, and the attempt records are equal apart from the trace fields and wall-clock memory timestamps.
  - The only extra file is `arm_V1/v1_trace.json`.
- `test_trace_replays_v1_exactly_and_fills_every_field`: the replay equals the ledger, and every field is filled for every candidate.
- `test_trace_covers_every_action_kind_across_ceilings`: RUN_PROBE, STOP_DECISION_FINAL, STOP_BUDGET, QUEUE_FOR_VERIFICATION and NOT_EXAMINED_BUDGET are all exercised.
- `test_tampered_ledger_is_detected`: TraceMismatch on a removed event or flipped skip reasons.
- `test_trace_contains_only_enums_ids_ints_bools` and `test_trace_module_reads_no_output_seal_label_or_confidence` (static).
- **Part A equality checks stay green.** Part A code is unchanged: `tests/rc6_diag` (45) and `test_arm_ledgers_equal_partA_except_identity`.

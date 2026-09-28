# AIVD RC1 — Final Pipeline Audit (Phase 0) and Generic Failure Analysis (Phase 1)

Base: `research/aivd-endgame-3-autonomous-security-discovery` @ `40c5a6885cc2c6ef5c02d3b58cc486903d6d7c88`.
Baseline at audit time: 132 tests pass / 0 fail, 431 tracked files (confirmed after the pinned
runtime was installed in `/var/tmp`; without it 4 END-GOAL-2/3 tests fail because they hash
`/var/tmp/ollama-v0344/extract/ollama`, see A0).

No sealed benchmark was run for this audit. All frozen stages (F3, F4, F5, F6, END-GOAL + its
forensic analysis, STATEFUL-1, END-GOAL-2, END-GOAL-3, investigation design) are left byte-for-
byte unchanged; `tests/test_rc1_frozen.py` enforces this against 40c5a68. RC1 is a new package
`aivd_rc1/` that reuses the frozen trajectory, recording and transport primitives.

## Runtime identity (verified)

| Item | Expected | Observed on box |
|---|---|---|
| Ollama archive `ollama-linux-amd64.tar.zst` v0.34.4 | `c238986e…9533` | `c238986e…9533` (matches release `sha256sum.txt`) |
| Runtime digest = sha256 of `bin/ollama` | `ad9c5344…2ff4` | `ad9c5344…2ff4` |
| Model digest = sha256 of manifest `qwen3/1.7b` | `8f68893c…30e7` | `8f68893c…30e7` |
| Model blob | `3d0b7905…ab6` | `3d0b7905…ab6` |
| Template blob | `ae370d88…fc4` | `ae370d88…fc4` |

Binary at `/var/tmp/ollama-v0344/extract/ollama`, models at `/var/tmp/ollama-models-17b`
(both outside Git). Request contract unchanged (`aivd_stateful/transport.py`): think=false,
temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 256,
seed 20260926. (`aivd_f3_lm/qwen3_runtime.py` records num_ctx 8192 for the older F3 contract;
the 1.7B stateful contract used by END-GOAL-2/3 and RC1 imports 4096 from
`qwen3_1_7b_target.py`. RC1 does not change either.)

## Audit findings

Severity: H = can change a scientific result, M = weakens evidence/provenance, L = hygiene.

| Id | Sev | Area | Finding | RC1 action |
|---|---|---|---|---|
| A0 | M | runtime | Tests for END-GOAL-2/3 read the runtime binary from `/var/tmp`; without it they fail with FileNotFoundError rather than a clear skip/identity error. | Documented; RC1 identity check raises `IdentityError` with an explicit reason. Frozen tests untouched. |
| A1 | H | discovery / budget | Frozen discovery ran a behavioral repeat (`verify`) inside the discovery budget for every retained candidate, duplicating the verification stage and consuming discovery budget. | RC1 discovery removes the duplicate; verification happens once, in its own stage. |
| A2 | H | state exploration | Two-step scenarios only compare history-kept vs reset once. There is no representation of a state *transition* (policy change, revocation, one-time consumption, role switch) as a probe dimension; CF-F ("mutation") existed in the library but no slot ever enabled it (`mutation` was never set). | RC1 declares `transition_slot` from public structure (a follow-up that differs from its opening), enabling CF-F for every two-step candidate. |
| A3 | H | investigation | Frozen `_category` could return SUPPORTED only for CF-C / CF-D. CF-E (branch) and CF-F (mutation) could never support a hypothesis, so context-isolation / policy / instruction hypotheses were structurally stuck at PLAUSIBLE_BUT_UNTESTED or CONTRADICTED. | RC1 engine maps every probe to generic dimensions; any probe can support or contradict. |
| A4 | H | hypotheses | Each hypothesis took only the *last* matching record; evidence could not accumulate for and against. | RC1 accumulates evidence and counterevidence per dimension. |
| A5 | H | FP path | Promotion to VERIFICATION_READY required CF-A+CF-B presence *or* a supported CF-C/CF-D — novelty alone (a restricted-looking span) could promote, with no matched counterfactual separating novelty from security relevance. | RC1 requires a supported dimension **and** a clean reset arm (CF-B shows no novel restricted span) before VERIFICATION_READY. |
| A6 | M | evidence loss | The END-GOAL-3 driver passed `preserved_output`/`contrast_output` to investigation but did not forward probe outputs, probe trajectory ids, state hashes or the investigation records to the ledger; verification only saw promotion. | RC1 ledger stores per candidate: trajectory, turns, state hashes, contrast trajectory, slots, probe calls (trajectory/turn/output hash), observations, records, hypotheses, promotion, verification call and blind decision. |
| A7 | H | FP/FN path | The novelty rule treated any ≥12-char alphanumeric run as a restricted value, so ordinary long English words ("Additionally", "confidential…") counted as "novel restricted spans". | RC1 `novel_spans` requires a token-like span (mixed letters and digits) absent from the public transcript. |
| A8 | H | verification | Verification in END-GOAL-3 was a repeat of the follow-up **appended** to the preserved trajectory (a third turn), not an independent repeat of the same state; the verifier then only checked token presence. The pipeline itself made no verification decision before reveal. | RC1 verification re-executes the follow-up from the same pre-follow-up state (independent sibling branch) and records a blind, seal-free decision (`CONFIRMED`/`NOT_CONFIRMED`). The offline verifier requires both that decision and the sealed predicate. |
| A9 | M | budget | Investigation reused `session.execute(... "continue")` so probe turns were appended to the retained trajectory, mutating the object later used for verification (`shells` held the pre-probe object but `session.trajectories` was overwritten). | RC1 runs probes as `branch` children, so the retained trajectory is never mutated; budget counters are read from one session and cross-checked (`sum(stage_calls) == calls`). |
| A10 | M | budget | Integrity-failure path set `calls = discovery+investigation+verification` from partially updated counters; a failure mid-investigation reported investigation_calls = 0. | RC1 computes stage counts from the session and flags any mismatch as an integrity failure. |
| A11 | M | provenance | Candidate IDs are content hashes but duplicates were never checked; trajectory IDs across passes could collide because they hash only scenario id + config. | RC1 namespaces trajectory roots by pass id and rejects duplicate candidate ids; tests cover both. |
| A12 | M | target isolation | Public scenario ids are hashes of relation + token; the relation *names* never enter the public text, which is good, but the END-GOAL-3 note text names the relation shape (e.g. "Single-use waiver"). Notes reach the model only through the wire. | RC1 keeps the same wire isolation; discovery/investigation modules have an import firewall test (no provider/wire/verifier imports). |
| A13 | L | dead paths | `aivd_investigation.firewall.dispatch`, `verifier_boundary.independent_check`, `select_action`, `compose` are unused by END-GOAL-3. `aivd_stateful.session` duplicates most of `aivd_endgame3.session`. | Left frozen; RC1 uses one session class. |
| A14 | M | silent fallback | END-GOAL-3 driver's `_shell` returned `None` silently for a missing branch trajectory and the probe was skipped with no record. | RC1 raises (integrity failure) when a retained trajectory is missing. |
| A15 | M | determinism | First call after a cold model load produced a different output than later identical calls (observed on the box with pinned sampling). Replays and verification repeats compare exact hashes. | RC1 performs one recorded, budgeted warm-up call per pass; determinism is measured in the dev E2E (criterion E8) and reported. |
| A16 | M | protected values | No test prevented raw target values from entering tracked files or reports. | `tests/test_rc1_protected.py` scans tracked files for protected values drawn from the ignored protected store and for token-like values in RC1 public reports. `.gitignore` covers protected dirs. |

## Phase 1 — generic failure analysis of the END-GOAL-3 pattern

Historical pattern (evidence only; not a tuning target): 4 sealed, 4 retained behaviorally, 2
verified, 2 missed at INVESTIGATED_NO_SECURITY_EVIDENCE, 2 behavioral FPs, 0 verification FPs.

- **State exploration breadth.** Every target was retained, so breadth at the discovery level was
  not the bottleneck. The bottleneck was after retention.
- **Context-boundary transitions.** For branch-shaped scenarios the only boundary-specific probe
  (CF-E) could not produce SUPPORTED (A3). A context-isolation violation could therefore never be
  promoted, whatever the model did. This is a representation gap, not a model property.
- **One-time / state-transition authorization.** A violation that appears only on a *repeat* after
  a state change needs a transition probe. CF-F was in the library but never enabled (A2); the
  verification repeat was appended as a third turn rather than re-run from the same state (A8).
- **State-transition representation.** Turns record input/output/state hashes, but no field
  represents "this follow-up changes the declared state". RC1 derives it structurally from public
  text (transition_slot / auth_slot) without reading labels.
- **Generic counterfactuals.** The reset counterfactual existed (CF-B) but was never used to
  *discount* novelty; novelty and security relevance were conflated (A5, A7).
- **Retention of trajectory evidence.** Probe outputs and state hashes were not carried to the
  ledger (A6), so a missed target cannot be diagnosed after the fact beyond its stage.
- **Hypotheses stuck at PLAUSIBLE_BUT_UNTESTED.** Structural: six of eight hypotheses mapped to
  probes that were never applicable or could never support (A2, A3).
- **Evidence lost between stages.** Investigation saw preserved/contrast outputs; verification saw
  only promotion; the verifier saw only three strings. RC1 forwards the full record.
- **Budget allocation.** 17 of 24 discovery units, 13 of 16 investigation, 2 of 8 verification were
  used; part of discovery went to the duplicate repeat (A1). Budget was not the binding
  constraint for the misses.
- **Behavioral FPs.** Both misses were counted as behavioral FPs by the frozen judge because they
  were retained and investigated without promotion. RC1 separates target outcomes from benign FP
  accounting: behavioral FPs are counted only on benign distractors.

Fixes are expressed generically (context-boundary transitions, one-time/state transitions,
matched counterfactuals, evidence forwarding). No RC1 module references a historical target
relation; `tests/test_rc1_adversarial.py::test_no_historical_target_logic` enforces that.

# Stateful discovery design

**Status:** DESIGN ONLY

MODEL CALLS: 0

OLLAMA CALLS: 0

QWEN CALLS: 0

No hidden target is created. No historical relation is an input. F3, F4, F5, F6, and the end-goal result stay frozen. This stage does not claim that stateful discovery improves AIVD.

## Current limitation

The frozen end-goal interface returned one string per arm. One arm was recorded as two calls, but the scored string was the last completion, and that completion's prompt was not longer than a fresh public prompt. A behavior that exists only as an ordered sequence of turns could not remain a candidate. The lifecycle stopped at four rejected contrasts: nothing was ranked, selected, or retained.

## What this stage adds

`aivd_stateful.model` is an offline trajectory model. A trajectory is an immutable object. Continuing, branching, or resetting returns a new object and leaves the parent unchanged. A turn records the public input, the supplied output, both hashes, the state hash before the turn, and the state hash after it. The ordered signature keeps every turn. A candidate stores that full list of turn ids, not only the last output.

No function in this package calls a model. Tests supply output strings. A later experiment would have to attach a real model under a separate preregistration. `dispatch` refuses.

## State

A state hash covers the trajectory id, isolation mode, parent id, inherited prefix, and the input and output hashes of this trajectory's own turns. The prefix is a copy of the parent's observed triples `(turn id, input hash, output hash)`. It is not a live pointer into the parent.

Isolation modes are `independent`, `branch`, and `reset`. An independent trajectory starts empty. A branch copies the declared prefix and then adds its own turn. A reset copies nothing.

## Turns and identity

Ids are SHA-256 digests of canonical JSON. The same config, public input, parent, and isolation produce the same trajectory id. Each turn id is a digest of the trajectory id, parent turn id, input hash, and index. Replay recomputes the input hash, output hash, parent link, order, and both state hashes from the stored turn text.

## Policy and budget

`select_action` chooses among caller-supplied options in a fixed priority and requires a written reason. Continuation is not mandatory: if it is not offered, a new trajectory can be chosen instead. Each supplied output charges exactly one `turn_executions` unit, and also increments `continuations`, `branches`, or `resets` when that is the action. Creation is counted separately and is not a model call. The counters stop with a named reason: `BUDGET_EXHAUSTED`, `POLICY_TERMINATED`, `FRONTIER_EMPTY`, `VERIFICATION_COMPLETE`, or `NO_UNEXPLORED_ACTION` when no option is offered.

## Candidates

`candidate_from` builds one behavioral candidate for the whole trajectory. `compose` concatenates observations from two candidates on the same trajectory and records both parent ids. It has no special case for any vulnerability. Security classification is not performed here.

## Compatibility

This repository does not define `GenerationRecord`, `CandidateOrigin`, `BehavioralSignature`, `BehavioralMemory`, or `BehavioralNoveltyFrontier`. They were not copied into new classes under those names. `aivd_f3_lm.recorder_1_2.Recorder` is locked to experiment `F3-LM-1.2` and was not modified. The historical `authorize_execution` functions were not modified and are not called. This package does not issue an execution token.

## Lifecycle

A multi-turn trajectory remains one candidate after the last turn. Its `turn_ids` list is the provenance. It does not disappear because the evidence is spread across turns. Ranking and security verification are outside this design.

The stateful discovery capability has not yet been demonstrated against a real model. This stage establishes only the offline architecture and correctness of trajectory/state handling.

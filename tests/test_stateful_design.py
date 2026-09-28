from dataclasses import replace
from pathlib import Path

import pytest

from aivd_stateful.firewall import ExecutionRefused, dispatch
from aivd_stateful.hashing import digest
from aivd_stateful.model import (
    Budget,
    BudgetExhausted,
    Config,
    LeakageError,
    PolicyError,
    ReplayError,
    branch,
    candidate_from,
    compose,
    continue_trajectory,
    create,
    replay,
    reset,
    select_action,
    signature,
)
from aivd_stateful.spec import EXECUTION_AUTHORIZED, MODEL_CALLS

CFG = Config(model="offline-stand-in", seed=7, runtime="none")


def _two():
    budget = Budget(limit=4)
    budget.note_creation()
    root = create("task", CFG, meta={})
    first = continue_trajectory(root, "turn-1", "alpha", reason="record the first output", budget=budget)
    second = continue_trajectory(first, "turn-2", "beta", reason="preserve history", budget=budget)
    return root, first, second, budget


def test_state_creation_and_hash_are_deterministic():
    assert create("task", CFG).trajectory_id == create("task", CFG).trajectory_id
    assert create("task", CFG).state_hash() == create("task", CFG).state_hash()
    assert create("task", CFG).state_hash() != create("other", CFG).state_hash()


def test_turns_keep_parent_links_and_reconstruct():
    _root, first, second, _budget = _two()
    assert second.turns[0].parent_turn_id is None
    assert second.turns[1].parent_turn_id == first.turns[0].turn_id
    assert [turn.turn_index for turn in second.turns] == [0, 1]
    replay(second)


def test_branch_inherits_parent_state_and_does_not_mutate_it():
    _root, first, _second, budget = _two()
    child = branch(first, "turn-2", "gamma", reason="fork from the recorded prefix", budget=budget)
    assert first.turns == (_two()[1].turns)
    assert child.parent_trajectory_id == first.trajectory_id
    assert child.prefix == ((first.turns[0].turn_id, first.turns[0].input_hash, first.turns[0].output_hash),)
    assert child.turns[0].parent_turn_id == first.turns[0].turn_id
    assert child.trajectory_id != first.trajectory_id
    replay(child)


def test_independent_trajectories_do_not_share_mutable_state():
    left = create("task", CFG)
    right = create("task", CFG)
    moved = continue_trajectory(left, "turn-1", "alpha", reason="only the left copy advances")
    assert left.turns == ()
    assert right.turns == ()
    assert moved.turns != left.turns


def test_reset_removes_context_that_preservation_keeps():
    _root, first, preserved, budget = _two()
    cleared = reset(first, "turn-2", "beta", reason="drop history", budget=budget)
    assert cleared.prefix == ()
    assert cleared.turns[0].parent_turn_id is None
    assert preserved.turns[1].state_before_hash == first.state_hash()
    assert cleared.turns[0].state_before_hash != first.state_hash()
    assert cleared.turns[0].input_hash == preserved.turns[1].input_hash
    altered = continue_trajectory(first, "turn-2", "beta", reason="same request after a different history")
    # first is unchanged; build a different history explicitly
    other_first = continue_trajectory(create("task", CFG), "turn-1", "omega", reason="different first output")
    other_second = continue_trajectory(other_first, "turn-2", "beta", reason="same second request")
    assert other_second.turns[1].state_before_hash != preserved.turns[1].state_before_hash
    assert altered.turns[1].input_hash == preserved.turns[1].input_hash
    replay(cleared)


def test_signature_keeps_every_turn():
    _root, first, second, _budget = _two()
    observed = signature(second)
    assert len(observed) == 2
    assert digest(list(observed)) != digest([observed[-1]])
    other = continue_trajectory(first, "turn-2", "other", reason="different second output")
    assert signature(second) != signature(other)
    assert second.turns[1].state_after_hash != second.turns[1].state_before_hash


def test_candidate_provenance_spans_the_trajectory():
    _root, _first, second, _budget = _two()
    found = candidate_from(second)
    assert found["turn_ids"] == [turn.turn_id for turn in second.turns]
    assert found["origin"] == "trajectory"
    earlier = candidate_from(continue_trajectory(create("other-task", CFG), "turn-1", "alpha", reason="different root"))
    # Compose only inside one trajectory: split the same trajectory's observations.
    left = dict(found)
    right = {
        "trajectory_id": found["trajectory_id"],
        "turn_ids": [found["turn_ids"][1]],
        "observations": [found["observations"][1]],
        "composed_from": [],
        "origin": "trajectory",
    }
    right["candidate_id"] = digest(right)
    merged = compose(left, right)
    assert merged["origin"] == "composition"
    assert found["turn_ids"][0] in merged["turn_ids"]
    assert found["turn_ids"][1] in merged["turn_ids"]
    with pytest.raises(PolicyError):
        compose(found, earlier)


def test_replay_rejects_a_tampered_output_hash():
    _root, _first, second, _budget = _two()
    bad_turn = replace(second.turns[1], output_hash="0" * 64)
    damaged = replace(second, turns=second.turns[:1] + (bad_turn,))
    with pytest.raises(ReplayError):
        replay(damaged)


def test_budget_counts_each_turn_once_and_records_the_stop():
    budget = Budget(limit=1)
    budget.note_creation()
    root = create("task", CFG)
    continue_trajectory(root, "turn-1", "alpha", reason="the only funded turn", budget=budget)
    assert budget.turn_executions == 1
    assert budget.continuations == 1
    assert budget.creations == 1
    with pytest.raises(BudgetExhausted):
        continue_trajectory(root, "turn-2", "beta", reason="over the ceiling", budget=budget)
    assert budget.stops == ("BUDGET_EXHAUSTED",)
    budget.stop("POLICY_TERMINATED")
    budget.stop("FRONTIER_EMPTY")
    assert "VERIFICATION_COMPLETE" not in budget.stops
    budget.stop("VERIFICATION_COMPLETE")
    assert budget.stops[-1] == "VERIFICATION_COMPLETE"


def test_policy_records_why_and_does_not_force_continuation():
    chosen, reason = select_action((("new", "start a separate trajectory"), ("continue", "history is still open")))
    assert chosen == "continue"
    assert reason == "history is still open"
    chosen, reason = select_action((("new", "no open history"), ("stop", "nothing left to open")))
    assert chosen == "new"
    with pytest.raises(PolicyError):
        select_action((("continue", ""),))


def test_hidden_fields_are_rejected_and_dispatch_stays_closed():
    with pytest.raises(LeakageError):
        create("task", CFG, meta={"secret": "nope"})
    assert EXECUTION_AUTHORIZED is False
    assert MODEL_CALLS == 0
    with pytest.raises(ExecutionRefused):
        dispatch({})
    source = "\n".join(path.read_text(encoding="utf-8") for path in Path("aivd_stateful").glob("*.py"))
    assert "CROSS_TURN_CARRY" not in source

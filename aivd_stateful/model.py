"""Immutable trajectories. Applying a turn returns a new object."""

from dataclasses import dataclass

from aivd_stateful.hashing import digest
from aivd_stateful.spec import FORBIDDEN_STATE_KEYS


class LeakageError(Exception):
    pass


class BudgetExhausted(Exception):
    pass


class ReplayError(Exception):
    pass


class PolicyError(Exception):
    pass


def reject_hidden(meta: dict | None) -> None:
    if meta and FORBIDDEN_STATE_KEYS & set(meta):
        raise LeakageError("discovery state cannot carry a hidden field")


@dataclass(frozen=True)
class Config:
    model: str
    seed: int
    runtime: str

    def digest(self) -> str:
        return digest({"model": self.model, "seed": self.seed, "runtime": self.runtime})


@dataclass(frozen=True)
class Turn:
    trajectory_id: str
    turn_id: str
    parent_turn_id: str | None
    turn_index: int
    public_input: str
    output: str
    input_hash: str
    output_hash: str
    state_before_hash: str
    state_after_hash: str
    model: str
    seed: int
    action: str
    reason: str


@dataclass(frozen=True)
class Trajectory:
    trajectory_id: str
    config: Config
    isolation: str
    parent_trajectory_id: str | None
    prefix: tuple
    turns: tuple
    stop_reason: str | None = None

    def state_hash(self) -> str:
        return state_hash(self.isolation, self.prefix, self.turns, self.parent_trajectory_id, self.trajectory_id)

    def tip(self) -> str | None:
        if self.turns:
            return self.turns[-1].turn_id
        if self.prefix:
            return self.prefix[-1][0]
        return None


def state_hash(isolation: str, prefix: tuple, turns: tuple, parent_trajectory_id: str | None, trajectory_id: str) -> str:
    return digest(
        {
            "isolation": isolation,
            "trajectory_id": trajectory_id,
            "parent_trajectory_id": parent_trajectory_id,
            "prefix": [list(item) for item in prefix],
            "turns": [
                {"turn_id": turn.turn_id, "output_hash": turn.output_hash, "input_hash": turn.input_hash}
                for turn in turns
            ],
        }
    )


def _identity(kind: str, config: Config, public_input: str, parent: str | None, isolation: str) -> str:
    return digest(
        {
            "kind": kind,
            "config": config.digest(),
            "public_input": public_input,
            "parent": parent,
            "isolation": isolation,
        }
    )


def _turn(trajectory_id: str, parent_turn_id: str | None, index: int, public_input: str, output: str, before: str, after: str, config: Config, action: str, reason: str) -> Turn:
    if not reason:
        raise PolicyError("an action requires a recorded reason")
    input_hash = digest({"public_input": public_input})
    output_hash = digest({"output": output})
    turn_id = digest(
        {
            "trajectory_id": trajectory_id,
            "parent_turn_id": parent_turn_id,
            "input_hash": input_hash,
            "index": index,
        }
    )
    return Turn(
        trajectory_id=trajectory_id,
        turn_id=turn_id,
        parent_turn_id=parent_turn_id,
        turn_index=index,
        public_input=public_input,
        output=output,
        input_hash=input_hash,
        output_hash=output_hash,
        state_before_hash=before,
        state_after_hash=after,
        model=config.model,
        seed=config.seed,
        action=action,
        reason=reason,
    )


def create(public_input: str, config: Config, *, meta: dict | None = None) -> Trajectory:
    reject_hidden(meta)
    return Trajectory(
        trajectory_id=_identity("independent", config, public_input, None, "independent"),
        config=config,
        isolation="independent",
        parent_trajectory_id=None,
        prefix=(),
        turns=(),
    )


def _append(trajectory: Trajectory, public_input: str, output: str, action: str, reason: str, budget) -> Trajectory:
    if budget is not None:
        budget.charge(action)
    before = trajectory.state_hash()
    parent_turn = trajectory.tip()
    index = len(trajectory.prefix) + len(trajectory.turns)
    draft = Trajectory(
        trajectory_id=trajectory.trajectory_id,
        config=trajectory.config,
        isolation=trajectory.isolation,
        parent_trajectory_id=trajectory.parent_trajectory_id,
        prefix=trajectory.prefix,
        turns=trajectory.turns,
    )
    after_turns = trajectory.turns + (
        _turn(
            trajectory.trajectory_id,
            parent_turn,
            index,
            public_input,
            output,
            before,
            "pending",
            trajectory.config,
            action,
            reason,
        ),
    )
    after_hash = state_hash(trajectory.isolation, trajectory.prefix, after_turns, trajectory.parent_trajectory_id, trajectory.trajectory_id)
    final_turn = Turn(**{**after_turns[-1].__dict__, "state_after_hash": after_hash})
    return Trajectory(
        trajectory_id=draft.trajectory_id,
        config=draft.config,
        isolation=draft.isolation,
        parent_trajectory_id=draft.parent_trajectory_id,
        prefix=draft.prefix,
        turns=after_turns[:-1] + (final_turn,),
    )


def continue_trajectory(trajectory: Trajectory, public_input: str, output: str, *, reason: str, budget=None) -> Trajectory:
    return _append(trajectory, public_input, output, "continue", reason, budget)


def _history(trajectory: Trajectory) -> tuple:
    return trajectory.prefix + tuple((turn.turn_id, turn.input_hash, turn.output_hash) for turn in trajectory.turns)


def branch(trajectory: Trajectory, public_input: str, output: str, *, reason: str, budget=None) -> Trajectory:
    child_id = _identity("branch", trajectory.config, public_input, trajectory.trajectory_id, "branch")
    child = Trajectory(
        trajectory_id=child_id,
        config=trajectory.config,
        isolation="branch",
        parent_trajectory_id=trajectory.trajectory_id,
        prefix=_history(trajectory),
        turns=(),
    )
    return _append(child, public_input, output, "branch", reason, budget)


def reset(trajectory: Trajectory, public_input: str, output: str, *, reason: str, budget=None) -> Trajectory:
    child_id = _identity("reset", trajectory.config, public_input, trajectory.trajectory_id, "reset")
    child = Trajectory(
        trajectory_id=child_id,
        config=trajectory.config,
        isolation="reset",
        parent_trajectory_id=trajectory.trajectory_id,
        prefix=(),
        turns=(),
    )
    return _append(child, public_input, output, "reset", reason, budget)


def plan_turn(trajectory: Trajectory, public_input: str, action: str) -> tuple:
    """Identify the turn before any model call. The shell has no new output yet."""
    if action == "continue":
        shell = trajectory
    elif action == "branch":
        shell = Trajectory(
            trajectory_id=_identity("branch", trajectory.config, public_input, trajectory.trajectory_id, "branch"),
            config=trajectory.config,
            isolation="branch",
            parent_trajectory_id=trajectory.trajectory_id,
            prefix=_history(trajectory),
            turns=(),
        )
    elif action == "reset":
        shell = Trajectory(
            trajectory_id=_identity("reset", trajectory.config, public_input, trajectory.trajectory_id, "reset"),
            config=trajectory.config,
            isolation="reset",
            parent_trajectory_id=trajectory.trajectory_id,
            prefix=(),
            turns=(),
        )
    elif action == "verify":
        shell = Trajectory(
            trajectory_id=_identity("verify", trajectory.config, public_input, trajectory.trajectory_id, "branch"),
            config=trajectory.config,
            isolation="branch",
            parent_trajectory_id=trajectory.trajectory_id,
            prefix=_history(trajectory),
            turns=(),
        )
    else:
        raise PolicyError("unknown action")
    parent_turn = shell.tip()
    index = len(shell.prefix) + len(shell.turns)
    input_hash = digest({"public_input": public_input})
    turn_id = digest(
        {
            "trajectory_id": shell.trajectory_id,
            "parent_turn_id": parent_turn,
            "input_hash": input_hash,
            "index": index,
        }
    )
    return shell, {
        "trajectory_id": shell.trajectory_id,
        "turn_id": turn_id,
        "parent_turn_id": parent_turn,
        "state_before_hash": shell.state_hash(),
        "input_hash": input_hash,
        "action": action,
    }


@dataclass
class Budget:
    limit: int
    creations: int = 0
    turn_executions: int = 0
    branches: int = 0
    continuations: int = 0
    resets: int = 0
    verifications: int = 0
    stops: tuple = ()

    def charge(self, action: str) -> None:
        if self.turn_executions >= self.limit:
            self.stops = self.stops + ("BUDGET_EXHAUSTED",)
            raise BudgetExhausted("turn budget is exhausted")
        self.turn_executions += 1
        if action == "continue":
            self.continuations += 1
        elif action == "branch":
            self.branches += 1
        elif action == "reset":
            self.resets += 1
        elif action == "verify":
            self.verifications += 1

    def note_creation(self) -> None:
        self.creations += 1

    def stop(self, reason: str) -> None:
        self.stops = self.stops + (reason,)


def select_action(options: tuple) -> tuple:
    if any(not item[1] for item in options):
        raise PolicyError("an action requires a recorded reason")
    priority = ("verify", "continue", "branch", "reset", "compose", "new", "stop")
    offered = {name: reason for name, reason in options}
    for name in priority:
        if name in offered:
            return name, offered[name]
    raise PolicyError("no unexplored action")


def replay(trajectory: Trajectory) -> None:
    previous = trajectory.prefix[-1][0] if trajectory.prefix else None
    running_turns = ()
    for turn in trajectory.turns:
        if turn.trajectory_id != trajectory.trajectory_id:
            raise ReplayError("turn trajectory mismatch")
        if turn.parent_turn_id != previous:
            raise ReplayError("parent turn mismatch")
        if digest({"public_input": turn.public_input}) != turn.input_hash:
            raise ReplayError("input hash mismatch")
        if digest({"output": turn.output}) != turn.output_hash:
            raise ReplayError("output hash mismatch")
        before = state_hash(trajectory.isolation, trajectory.prefix, running_turns, trajectory.parent_trajectory_id, trajectory.trajectory_id)
        if turn.state_before_hash != before:
            raise ReplayError("state hash mismatch")
        if running_turns and turn.turn_index != running_turns[-1].turn_index + 1:
            raise ReplayError("turn order mismatch")
        running_turns = running_turns + (turn,)
        after = state_hash(trajectory.isolation, trajectory.prefix, running_turns, trajectory.parent_trajectory_id, trajectory.trajectory_id)
        if turn.state_after_hash != after:
            raise ReplayError("state hash mismatch")
        previous = turn.turn_id
    if trajectory.state_hash() != state_hash(trajectory.isolation, trajectory.prefix, running_turns, trajectory.parent_trajectory_id, trajectory.trajectory_id):
        raise ReplayError("state hash mismatch")


def signature(trajectory: Trajectory) -> tuple:
    inherited = tuple(
        {"turn_id": turn_id, "input_hash": input_hash, "output_hash": output_hash, "inherited": True}
        for turn_id, input_hash, output_hash in trajectory.prefix
    )
    own = tuple(
        {
            "turn_id": turn.turn_id,
            "input_hash": turn.input_hash,
            "output_hash": turn.output_hash,
            "state_hash": turn.state_after_hash,
            "inherited": False,
        }
        for turn in trajectory.turns
    )
    return inherited + own


def candidate_from(trajectory: Trajectory, *, composed_from: tuple = ()) -> dict:
    observations = signature(trajectory)
    if not observations:
        raise PolicyError("a candidate requires a trajectory")
    body = {
        "trajectory_id": trajectory.trajectory_id,
        "turn_ids": [item["turn_id"] for item in observations],
        "observations": list(observations),
        "composed_from": list(composed_from),
        "origin": "trajectory",
    }
    body["candidate_id"] = digest(body)
    return body


def compose(left: dict, right: dict) -> dict:
    if left["trajectory_id"] != right["trajectory_id"]:
        raise PolicyError("composition stays inside one trajectory")
    merged_ids = left["turn_ids"] + [turn_id for turn_id in right["turn_ids"] if turn_id not in left["turn_ids"]]
    body = {
        "trajectory_id": left["trajectory_id"],
        "turn_ids": merged_ids,
        "observations": left["observations"] + right["observations"],
        "composed_from": [left["candidate_id"], right["candidate_id"]],
        "origin": "composition",
    }
    body["candidate_id"] = digest(body)
    return body

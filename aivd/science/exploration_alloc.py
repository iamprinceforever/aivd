"""AIVD 3.45 — General EXPLOIT + EXPLORE materialization allocation.

Bounded anti-starvation for atom materialization under lazy width.
Candidate-identity agnostic: keys are opaque structural ids (e.g. body keys).
Does not bypass novelty, firewall, invent_cap, equivalence, or verification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Bounds — keep exploration strictly subdominant to exploitation.
DEFAULT_SKIP_THRESHOLD = 1
DEFAULT_MAX_EXPLORE_SLOTS = 1
DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE = 1
DEFAULT_CHAIN_FLOOR = 3  # invent+repro+verify floor used by planner budget gates


@dataclass
class CandidateExploreState:
    """Bounded per-candidate exploration bookkeeping (general fields only)."""

    skip_count: int = 0
    materialization_count: int = 0
    exploration_opportunities: int = 0
    last_materialized_epoch: int = -1


@dataclass
class AllocationDecision:
    """Result of one EXPLOIT+EXPLORE decision. Deterministic for identical inputs."""

    n_mat: int
    exploit_n: int
    explore_n: int
    ordered: list[Any]
    explore_keys: list[str]
    reason: str
    epoch: int


@dataclass
class ExplorationAllocator:
    """Tracks skip/materialization pressure and computes bounded materialization width.

    Invariant: low rank ≠ permanent invisibility unless an explicit terminal reason
    applies (rejected / duplicate / invalid / budget exhausted / novelty exhausted /
    already explored / opportunity budget spent).
    """

    skip_threshold: int = DEFAULT_SKIP_THRESHOLD
    max_explore_slots: int = DEFAULT_MAX_EXPLORE_SLOTS
    max_opportunities_per_candidate: int = DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE
    chain_floor: int = DEFAULT_CHAIN_FLOOR
    epoch: int = 0
    states: dict[str, CandidateExploreState] = field(default_factory=dict)

    def state_of(self, key: str) -> CandidateExploreState:
        st = self.states.get(key)
        if st is None:
            st = CandidateExploreState()
            self.states[key] = st
        return st

    def reset(self) -> None:
        self.epoch = 0
        self.states.clear()

    def _key_of(self, cand: Any) -> str:
        if hasattr(cand, "key") and callable(cand.key):
            return str(cand.key())
        return str(getattr(cand, "candidate_key", getattr(cand, "name", cand)))

    def _is_under_explored(self, st: CandidateExploreState) -> bool:
        return (
            st.materialization_count <= 0
            and st.exploration_opportunities < self.max_opportunities_per_candidate
        )

    def _starvation_pressure(self, st: CandidateExploreState) -> bool:
        """True when repeatedly skipped (or never given a chance) with insufficient exploration."""
        if not self._is_under_explored(st):
            return False
        return st.skip_count >= self.skip_threshold

    def _first_window_diversity(self, *, n_beyond: int, any_materialized: bool) -> bool:
        """Bounded first-call diversity when many valid candidates sit beyond exploit cut."""
        if any_materialized:
            return False
        return n_beyond > 0 and self.epoch == 0

    def decide(
        self,
        candidates: list[Any],
        *,
        lazy: bool,
        invent_slots_left: int,
        leftover: int,
        rejected_keys: set[str] | None = None,
    ) -> AllocationDecision:
        """Compute adaptive n_mat and an ordered materialization queue.

        EXPLOIT: preserve rank-driven top selection (width 1 lazy / 4 eager).
        EXPLORE: at most max_explore_slots extra when anti-starvation fires and
        budget/cap allow. Explore opportunity ≠ guaranteed invention (downstream
        gates still apply).
        """
        rejected_keys = rejected_keys or set()
        n = len(candidates)
        base = 1 if lazy else 4
        if n == 0 or invent_slots_left <= 0:
            return AllocationDecision(
                n_mat=0,
                exploit_n=0,
                explore_n=0,
                ordered=list(candidates),
                explore_keys=[],
                reason="empty_or_no_cap",
                epoch=self.epoch,
            )

        affordable = max(0, int(leftover) // max(1, self.chain_floor))
        affordable = min(affordable, int(invent_slots_left), n)
        exploit_n = min(base, affordable)

        keys = [self._key_of(c) for c in candidates]
        any_mat = any(self.state_of(k).materialization_count > 0 for k in keys)
        beyond = [
            (i, c, keys[i])
            for i, c in enumerate(candidates)
            if i >= exploit_n and keys[i] not in rejected_keys
        ]

        starved: list[tuple[int, int, int, Any, str]] = []
        for i, c, k in beyond:
            st = self.state_of(k)
            if not self._is_under_explored(st):
                continue
            if not (
                self._starvation_pressure(st)
                or self._first_window_diversity(n_beyond=len(beyond), any_materialized=any_mat)
            ):
                continue
            # Higher skip_count first; then earlier proposal_index; then board index.
            prop = int(getattr(c, "proposal_index", i) or 0)
            starved.append((st.skip_count, prop, i, c, k))
        starved.sort(key=lambda t: (-t[0], t[1], t[2]))

        explore_budget = max(0, affordable - exploit_n)
        want_explore = min(self.max_explore_slots, explore_budget, len(starved))
        explore_n = int(want_explore)

        ordered = list(candidates)
        explore_keys: list[str] = []
        if explore_n > 0 and starved:
            # Surface up to explore_n starved candidates just after the exploit cut.
            picks = starved[:explore_n]
            pick_keys = {k for *_, k in picks}
            head = [c for i, c in enumerate(candidates) if i < exploit_n]
            head_keys = {self._key_of(c) for c in head}
            # Do not pull someone already in the exploit window.
            surfaced = [c for *_, c, k in picks if k not in head_keys]
            mid_keys = {self._key_of(c) for c in surfaced}
            explore_keys = [self._key_of(c) for c in surfaced]
            tail = [
                c
                for c in candidates
                if self._key_of(c) not in head_keys and self._key_of(c) not in mid_keys
            ]
            ordered = head + surfaced + tail
            # Record opportunities (not inventions).
            for k in explore_keys:
                self.state_of(k).exploration_opportunities += 1

        n_mat = min(exploit_n + explore_n, affordable, n)
        if explore_n > 0:
            reason = "exploit_plus_bounded_explore"
        elif exploit_n > 0:
            reason = "exploit_only"
        else:
            reason = "budget_insufficient"

        return AllocationDecision(
            n_mat=n_mat,
            exploit_n=exploit_n,
            explore_n=explore_n,
            ordered=ordered,
            explore_keys=explore_keys,
            reason=reason,
            epoch=self.epoch,
        )

    def observe_call(
        self,
        *,
        board_keys_before: list[str],
        materialized_keys: list[str],
        decision: AllocationDecision,
    ) -> None:
        """Update skip/materialization counters after one materialization call."""
        mat_set = set(materialized_keys)
        for k in board_keys_before:
            st = self.state_of(k)
            if k in mat_set:
                st.materialization_count += 1
                st.last_materialized_epoch = self.epoch
            else:
                # Still valid on board / considered but not taken → skip pressure.
                st.skip_count += 1
        self.epoch += 1

    def note_terminal(self, key: str, *, reason: str) -> None:
        """Mark a candidate as no longer eligible for exploration pressure.

        Terminal reasons (rejected/duplicate/invalid/…) freeze further opportunities
        by saturating exploration_opportunities and materialization_count semantics
        via skip suppression: we set opportunities to max so _is_under_explored fails.
        """
        st = self.state_of(key)
        st.exploration_opportunities = max(
            st.exploration_opportunities, self.max_opportunities_per_candidate
        )
        # Keep reason discoverable for audits without affecting selection.
        setattr(st, "terminal_reason", reason)


__all__ = [
    "CandidateExploreState",
    "AllocationDecision",
    "ExplorationAllocator",
    "DEFAULT_SKIP_THRESHOLD",
    "DEFAULT_MAX_EXPLORE_SLOTS",
    "DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE",
    "DEFAULT_CHAIN_FLOOR",
]

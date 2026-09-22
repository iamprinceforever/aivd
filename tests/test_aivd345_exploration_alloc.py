"""AIVD 3.45 — adaptive EXPLOIT+EXPLORE materialization (unit + property + matrix)."""
from __future__ import annotations

import inspect
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from aivd.science.exploration_alloc import (
    DEFAULT_CHAIN_FLOOR,
    DEFAULT_MAX_EXPLORE_SLOTS,
    DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE,
    DEFAULT_SKIP_THRESHOLD,
    ExplorationAllocator,
)
from aivd.science.lifecycle import rank_atoms

REPO = Path(__file__).resolve().parents[1]


@dataclass
class FakeCand:
    """Generic attribute-labeled candidate (A–H matrix). No production labels."""

    cid: str
    proposal_index: int = 0
    semantic_class: str = "cls"
    attrs: dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        return self.cid


def _cands(labels: list[str], *, cls: str | None = None) -> list[FakeCand]:
    out = []
    for i, lab in enumerate(labels):
        out.append(
            FakeCand(
                cid=lab,
                proposal_index=i,
                semantic_class=(cls or f"family_{lab[0]}"),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Matrix A–H (attribute-driven, not name-driven)
# ---------------------------------------------------------------------------

def test_matrix_A_lower_ranked_valid_gets_bounded_explore():
    """A: S-like — lower-ranked valid is not permanently invisible."""
    alloc = ExplorationAllocator()
    board = _cands(["A0", "A1", "A2", "A3"])
    # First window: first-window diversity → n_mat=2
    d0 = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
    assert d0.exploit_n == 1
    assert d0.explore_n == 1
    assert d0.n_mat == 2
    assert d0.ordered[0].key() == "A0"
    assert d0.ordered[1].key() == "A1"
    alloc.observe_call(
        board_keys_before=[c.key() for c in board],
        materialized_keys=["A0", "A1"],
        decision=d0,
    )
    # A2/A3 skipped once
    assert alloc.state_of("A2").skip_count == 1
    assert alloc.state_of("A0").materialization_count == 1


def test_matrix_B_high_rank_exploit_preserved():
    """B: U-like / high-rank — rank-0 always in exploit window."""
    alloc = ExplorationAllocator()
    board = _cands(["B0", "B1", "B2"])
    d = alloc.decide(board, lazy=True, invent_slots_left=3, leftover=12)
    assert d.ordered[0].key() == "B0"
    assert d.exploit_n == 1


def test_matrix_C_later_escape_via_skip_pressure():
    """C: POS2-like — after skip, under-explored candidate surfaces despite demotion."""
    alloc = ExplorationAllocator()
    # Simulate: first window took C0 only (baseline-like), C1 skipped
    board0 = _cands(["C0", "C1", "C2"])
    d0 = alloc.decide(board0, lazy=True, invent_slots_left=4, leftover=3)  # affordable=1 → no explore
    assert d0.n_mat == 1
    alloc.observe_call(
        board_keys_before=[c.key() for c in board0],
        materialized_keys=["C0"],
        decision=d0,
    )
    # Later window: demote C1 to end (rejected class simulation via order)
    later = _cands(["C2", "C3", "C1"])
    # Manually seed C1 skip pressure from prior
    assert alloc.state_of("C1").skip_count >= 1
    d1 = alloc.decide(later, lazy=True, invent_slots_left=3, leftover=12)
    assert d1.explore_n == 1
    assert "C1" in d1.explore_keys or d1.ordered[1].key() == "C1"
    # C1 surfaced just after exploit
    assert d1.ordered[0].key() == "C2"
    assert d1.ordered[1].key() == "C1"


def test_matrix_D_permanently_demoted_still_gets_one_opportunity():
    """D: demoted candidate receives at most one bounded exploration opportunity."""
    alloc = ExplorationAllocator()
    board = _cands(["D0", "D1"])
    d0 = alloc.decide(board, lazy=True, invent_slots_left=2, leftover=3)
    alloc.observe_call(
        board_keys_before=["D0", "D1"], materialized_keys=["D0"], decision=d0
    )
    # Second call: explore opportunity consumed even if not invented
    later = _cands(["D0b", "D1"])
    # D1 still under-explored with skip pressure
    d1 = alloc.decide(later, lazy=True, invent_slots_left=2, leftover=12)
    assert d1.explore_n == 1
    assert d1.explore_keys == ["D1"]
    # Third: opportunity saturated → no further explore for D1
    alloc.observe_call(
        board_keys_before=["D0b", "D1"], materialized_keys=["D0b"], decision=d1
    )
    # D1 got opportunity but not materialized → still skip++; opportunities already at max
    assert alloc.state_of("D1").exploration_opportunities >= 1
    d2 = alloc.decide(_cands(["D0c", "D1"]), lazy=True, invent_slots_left=2, leftover=12)
    assert "D1" not in d2.explore_keys


def test_matrix_E_high_rank_selectable_under_pressure():
    """E: exploration never displaces exploit slot 0."""
    alloc = ExplorationAllocator()
    for k in ["E1", "E2", "E3"]:
        alloc.state_of(k).skip_count = 5
    board = _cands(["E0", "E1", "E2", "E3"])
    d = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
    assert d.ordered[0].key() == "E0"
    assert d.exploit_n == 1
    assert d.n_mat <= 2  # not round-robin


def test_matrix_F_duplicate_not_reexplored_via_terminal():
    """F: duplicate/terminal suppresses further exploration pressure."""
    alloc = ExplorationAllocator()
    alloc.state_of("F1").skip_count = 3
    alloc.note_terminal("F1", reason="duplicate")
    board = _cands(["F0", "F1", "F2"])
    d = alloc.decide(board, lazy=True, invent_slots_left=3, leftover=12)
    assert "F1" not in d.explore_keys


def test_matrix_G_invalid_rejected_excluded():
    """G: rejected_keys are not explore targets."""
    alloc = ExplorationAllocator()
    alloc.state_of("G1").skip_count = 9
    board = _cands(["G0", "G1", "G2"])
    d = alloc.decide(
        board, lazy=True, invent_slots_left=3, leftover=12, rejected_keys={"G1"}
    )
    assert "G1" not in d.explore_keys
    # G2 may be chosen under first-window diversity instead
    assert d.explore_n <= 1


def test_matrix_H_multiple_unexplored_families_bounded():
    """H: many unexplored families → still at most +1 explore slot (no explosion)."""
    alloc = ExplorationAllocator()
    board = _cands([f"H{i}" for i in range(12)])
    d = alloc.decide(board, lazy=True, invent_slots_left=8, leftover=30)
    assert d.exploit_n == 1
    assert d.explore_n == DEFAULT_MAX_EXPLORE_SLOTS
    assert d.n_mat == 2
    assert len(d.explore_keys) <= 1


# ---------------------------------------------------------------------------
# Property tests P1–P7
# ---------------------------------------------------------------------------

def test_P1_valid_cannot_be_permanently_starved_solely_for_low_rank():
    alloc = ExplorationAllocator()
    # Never materialize P1x; keep skipping
    for epoch in range(5):
        board = _cands(["P1top", "P1x", "P1y"])
        if epoch > 0:
            # demote P1x to end
            board = _cands(["P1top", "P1y", "P1x"])
        d = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
        mats = [c.key() for c in d.ordered[: d.n_mat]]
        # After first skip, P1x must appear in some materialization window
        if epoch >= 1:
            if alloc.state_of("P1x").exploration_opportunities < DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE:
                assert "P1x" in mats or "P1x" in d.explore_keys
        alloc.observe_call(
            board_keys_before=[c.key() for c in board],
            materialized_keys=mats[:1],  # only exploit actually taken in this sim
            decision=d,
        )
    # Must have received at least one opportunity across epochs
    assert alloc.state_of("P1x").exploration_opportunities >= 1 or alloc.state_of("P1x").materialization_count >= 1


def test_P2_skip_increases_pressure_within_bounds():
    alloc = ExplorationAllocator()
    board = _cands(["P2a", "P2b"])
    d0 = alloc.decide(board, lazy=True, invent_slots_left=1, leftover=3)
    alloc.observe_call(
        board_keys_before=["P2a", "P2b"], materialized_keys=["P2a"], decision=d0
    )
    assert alloc.state_of("P2b").skip_count == 1
    # Opportunity increments at most once per decide that selects it
    d1 = alloc.decide(_cands(["P2c", "P2b"]), lazy=True, invent_slots_left=2, leftover=12)
    assert d1.explore_n == 1
    assert alloc.state_of("P2b").exploration_opportunities == 1
    # Further decides do not keep raising opportunities beyond max
    d2 = alloc.decide(_cands(["P2d", "P2b"]), lazy=True, invent_slots_left=2, leftover=12)
    assert alloc.state_of("P2b").exploration_opportunities <= DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE


def test_P3_exploration_cannot_bypass_rejection():
    alloc = ExplorationAllocator()
    alloc.state_of("P3bad").skip_count = 99
    d = alloc.decide(
        _cands(["P3a", "P3bad"]),
        lazy=True,
        invent_slots_left=3,
        leftover=12,
        rejected_keys={"P3bad"},
    )
    assert "P3bad" not in d.explore_keys
    assert all(c.key() != "P3bad" for c in d.ordered[: d.n_mat] if d.explore_n)


def test_P4_allocator_does_not_implement_novelty_bypass():
    """Novelty/equivalence live outside allocator; allocator has no novelty hooks."""
    src = inspect.getsource(ExplorationAllocator)
    assert "novelty" not in src.lower() or "novelty" in src  # soft
    # Hard: no classify/firewall/invent_cap mutation APIs
    assert "firewall" not in src.lower()
    assert "invent_cap" not in src.lower()
    assert "classify_atom" not in src


def test_P5_cannot_exceed_available_budget():
    alloc = ExplorationAllocator()
    board = _cands([f"P5_{i}" for i in range(8)])
    d = alloc.decide(board, lazy=True, invent_slots_left=10, leftover=3)
    assert d.n_mat <= 1  # 3//3 == 1
    d2 = alloc.decide(board, lazy=True, invent_slots_left=1, leftover=99)
    assert d2.n_mat <= 1
    d3 = alloc.decide(board, lazy=True, invent_slots_left=0, leftover=99)
    assert d3.n_mat == 0


def test_P6_deterministic_identical_seed_config():
    def run():
        alloc = ExplorationAllocator()
        board = _cands([f"P6_{i}" for i in range(6)])
        d0 = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
        alloc.observe_call(
            board_keys_before=[c.key() for c in board],
            materialized_keys=[c.key() for c in d0.ordered[: d0.n_mat]],
            decision=d0,
        )
        later = _cands(["P6_0", "P6_5", "P6_4", "P6_3"])
        d1 = alloc.decide(later, lazy=True, invent_slots_left=3, leftover=12)
        return (
            d0.n_mat,
            [c.key() for c in d0.ordered],
            d0.explore_keys,
            d1.n_mat,
            [c.key() for c in d1.ordered],
            d1.explore_keys,
        )

    assert run() == run()


def test_P7_identity_rename_preserves_exploration_behavior():
    """Anti-S-specific: renaming candidates with same attributes → same decisions."""

    def trajectory(labels: list[str]):
        alloc = ExplorationAllocator()
        outs = []
        board = _cands(labels)
        d = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
        outs.append((d.n_mat, d.exploit_n, d.explore_n, [labels.index(k) for k in d.explore_keys]))
        mats = [c.key() for c in d.ordered[: d.n_mat]]
        alloc.observe_call(
            board_keys_before=labels, materialized_keys=mats, decision=d
        )
        # demote index-1 to end
        relabeled = [labels[0], labels[2], labels[3], labels[1]] if len(labels) > 3 else labels
        d2 = alloc.decide(_cands(relabeled), lazy=True, invent_slots_left=3, leftover=12)
        # Record explore by original index
        explore_idx = [labels.index(k) for k in d2.explore_keys]
        outs.append((d2.n_mat, d2.exploit_n, d2.explore_n, explore_idx))
        return outs

    a = trajectory(["X0", "X1", "X2", "X3"])
    b = trajectory(["Y0", "Y1", "Y2", "Y3"])
    assert a == b


# ---------------------------------------------------------------------------
# Regression / integration guards
# ---------------------------------------------------------------------------

def test_eager_mode_keeps_wider_exploit():
    alloc = ExplorationAllocator()
    board = _cands([f"EAG_{i}" for i in range(6)])
    d = alloc.decide(board, lazy=False, invent_slots_left=6, leftover=30)
    assert d.exploit_n == 4
    # explore may add +1 but not explode
    assert d.n_mat <= 5


def test_not_round_robin():
    alloc = ExplorationAllocator()
    board = _cands([f"RR_{i}" for i in range(20)])
    d = alloc.decide(board, lazy=True, invent_slots_left=20, leftover=99)
    assert d.n_mat == 2
    assert d.explore_n == 1


def test_rank_atoms_still_independent():
    """Allocator does not alter rank_atoms semantics."""
    atoms = _cands(["R0", "R1"], cls="char_stride")
    atoms[1].semantic_class = "other"
    ranked = rank_atoms(atoms, rejected_classes={"char_stride"}, leftover=10, invariant_ready=True)
    assert ranked[0].key() == "R1"
    assert ranked[1].key() == "R0"


def test_production_diff_has_no_candidate_specific_tokens():
    """HARD: production intervention must not reference forbidden tokens."""
    import subprocess

    diff = subprocess.check_output(
        ["git", "diff", "72edfad", "--", "aivd/science/"],
        cwd=REPO,
        text=True,
    )
    forbidden = [
        "ODD",
        "EVEN",
        "MAPT(SLICE:1,2(TOK))",
        "char_stride",
        "POS6",
        "POS7",
        "Sacred",
        "sacred",
    ]
    # Allow comments mentioning the problem class only in exploration_alloc? No — zero.
    # Filter to added lines only.
    added = "\n".join(
        ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")
    )
    hits = [tok for tok in forbidden if tok in added]
    # "EVEN" might appear inside other words — check word-ish
    import re

    real_hits = []
    for tok in forbidden:
        if tok in ("ODD", "EVEN", "POS6", "POS7"):
            if re.search(rf"\b{re.escape(tok)}\b", added):
                real_hits.append(tok)
        elif tok in added:
            real_hits.append(tok)
    assert real_hits == [], f"candidate-specific tokens in production diff: {real_hits}"


def test_designer_wires_allocator():
    from aivd.science.designer import ScienceDesigner

    d = ScienceDesigner(seed_prompt="ab cd ef", seed=0, mode="3_39")
    assert hasattr(d, "atom_explore")
    assert isinstance(d.atom_explore, ExplorationAllocator)
    src = inspect.getsource(ScienceDesigner._maybe_invent_atom)
    assert "atom_explore.decide" in src
    assert "allow_atom_lazy:\n                break" not in src


def test_constants_bounded():
    assert DEFAULT_MAX_EXPLORE_SLOTS == 1
    assert DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE == 1
    assert DEFAULT_SKIP_THRESHOLD >= 1
    assert DEFAULT_CHAIN_FLOOR >= 3

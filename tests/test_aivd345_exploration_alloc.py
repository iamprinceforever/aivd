"""AIVD 3.45 — EXPLOITATION SAFETY + BOUNDED EXPLORATION (unit + property + matrix)."""
from __future__ import annotations

import inspect
import re
import subprocess
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
    """A: S-like — lower-ranked valid is not permanently invisible (skip→explore)."""
    alloc = ExplorationAllocator()
    board = _cands(["A0", "A1", "A2", "A3"])
    # Epoch 0: PRIMARY only (no first-window max-diversity).
    d0 = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
    assert d0.exploit_n == 1
    assert d0.explore_n == 0
    assert d0.n_mat == 1
    assert d0.ordered[0].key() == "A0"
    assert d0.primary_keys == ["A0"]
    alloc.observe_call(
        board_keys_before=[c.key() for c in board],
        materialized_keys=["A0"],
        decision=d0,
    )
    assert alloc.state_of("A1").skip_count == 1
    # After skip pressure: SECONDARY explore surfaces A1 without displacing A-top.
    later = _cands(["A0b", "A1", "A2", "A3"])
    d1 = alloc.decide(later, lazy=True, invent_slots_left=4, leftover=12)
    assert d1.exploit_n == 1
    assert d1.explore_n == 1
    assert d1.n_mat == 2
    assert d1.ordered[0].key() == "A0b"
    assert "A1" in d1.explore_keys
    assert d1.secondary_keys == d1.explore_keys


def test_matrix_B_high_rank_exploit_preserved():
    """B: U-like / high-rank — rank-0 always in exploit/PRIMARY window."""
    alloc = ExplorationAllocator()
    board = _cands(["B0", "B1", "B2"])
    d = alloc.decide(board, lazy=True, invent_slots_left=3, leftover=12)
    assert d.ordered[0].key() == "B0"
    assert d.exploit_n == 1
    assert d.primary_keys == ["B0"]


def test_matrix_C_later_escape_via_skip_pressure():
    """C: POS2-like — after skip, under-explored candidate surfaces despite demotion."""
    alloc = ExplorationAllocator()
    board0 = _cands(["C0", "C1", "C2"])
    d0 = alloc.decide(board0, lazy=True, invent_slots_left=4, leftover=3)  # affordable=1
    assert d0.n_mat == 1
    alloc.observe_call(
        board_keys_before=[c.key() for c in board0],
        materialized_keys=["C0"],
        decision=d0,
    )
    later = _cands(["C2", "C3", "C1"])
    assert alloc.state_of("C1").skip_count >= 1
    d1 = alloc.decide(later, lazy=True, invent_slots_left=3, leftover=12)
    assert "C1" in d1.explore_keys
    assert d1.ordered[0].key() == "C2"  # primary preserved


def test_matrix_D_null_empty():
    alloc = ExplorationAllocator()
    d = alloc.decide([], lazy=True, invent_slots_left=4, leftover=12)
    assert d.n_mat == 0
    assert d.reason == "empty_or_no_cap"


def test_matrix_E_exploration_never_displaces_exploit_slot0():
    """E: exploration never displaces exploit/PRIMARY slot 0."""
    alloc = ExplorationAllocator()
    board = _cands(["E0", "E1", "E2", "E3"])
    alloc.state_of("E3").skip_count = 5
    d = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
    assert d.ordered[0].key() == "E0"
    assert d.exploit_n == 1
    assert d.n_mat <= 2  # not round-robin


def test_matrix_F_duplicate_terminal_suppressed():
    alloc = ExplorationAllocator()
    alloc.state_of("DUP").skip_count = 5
    alloc.note_terminal("DUP", reason="duplicate")
    d = alloc.decide(_cands(["T0", "DUP", "T2"]), lazy=True, invent_slots_left=3, leftover=12)
    assert "DUP" not in d.explore_keys


def test_matrix_G_rejected_excluded():
    alloc = ExplorationAllocator()
    alloc.state_of("RJ").skip_count = 9
    d = alloc.decide(
        _cands(["R0", "RJ", "R2"]),
        lazy=True,
        invent_slots_left=3,
        leftover=12,
        rejected_keys={"RJ"},
    )
    assert "RJ" not in d.explore_keys


def test_matrix_H_many_candidates_bounded():
    """H: many families — after skip, explore bounded +1 (not first-window blast)."""
    alloc = ExplorationAllocator()
    board = _cands([f"H{i}" for i in range(12)])
    d0 = alloc.decide(board, lazy=True, invent_slots_left=8, leftover=30)
    assert d0.n_mat == 1 and d0.explore_n == 0
    alloc.observe_call(
        board_keys_before=[c.key() for c in board],
        materialized_keys=["H0"],
        decision=d0,
    )
    d1 = alloc.decide(_cands([f"H{i}" for i in range(12)]), lazy=True, invent_slots_left=8, leftover=30)
    assert d1.exploit_n == 1
    assert d1.explore_n == DEFAULT_MAX_EXPLORE_SLOTS
    assert d1.n_mat == 2
    assert len(d1.explore_keys) <= 1


# ---------------------------------------------------------------------------
# Property tests P1–P10
# ---------------------------------------------------------------------------

def test_P1_valid_cannot_be_permanently_starved_solely_for_low_rank():
    """Low-rank valid eventually receives a bounded explore opportunity (P2 pressure)."""
    alloc = ExplorationAllocator()
    saw_p1x = False
    for epoch in range(6):
        # Permanently demote P1x to end after epoch 0.
        board = _cands(["P1top", "P1y", "P1x"]) if epoch > 0 else _cands(["P1top", "P1x", "P1y"])
        d = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
        mats = [c.key() for c in d.ordered[: d.n_mat]]
        if "P1x" in mats or "P1x" in d.explore_keys:
            saw_p1x = True
        # Only PRIMARY actually taken in this sim (secondary is opportunity accounting).
        alloc.observe_call(
            board_keys_before=[c.key() for c in board],
            materialized_keys=mats[:1],
            decision=d,
        )
    assert saw_p1x or alloc.state_of("P1x").exploration_opportunities >= 1
    assert alloc.state_of("P1x").exploration_opportunities >= 1 or alloc.state_of("P1x").materialization_count >= 1


def test_P2_skip_increases_pressure_within_bounds():
    alloc = ExplorationAllocator()
    board = _cands(["P2a", "P2b"])
    d0 = alloc.decide(board, lazy=True, invent_slots_left=1, leftover=3)
    alloc.observe_call(
        board_keys_before=["P2a", "P2b"], materialized_keys=["P2a"], decision=d0
    )
    assert alloc.state_of("P2b").skip_count == 1
    d1 = alloc.decide(_cands(["P2c", "P2b"]), lazy=True, invent_slots_left=2, leftover=12)
    assert d1.explore_n == 1
    assert alloc.state_of("P2b").exploration_opportunities == 1
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
    src = inspect.getsource(ExplorationAllocator)
    assert "firewall" not in src.lower()
    assert "invent_cap" not in src.lower()
    assert "classify_atom" not in src


def test_P5_cannot_exceed_available_budget():
    alloc = ExplorationAllocator()
    board = _cands([f"P5_{i}" for i in range(8)])
    d = alloc.decide(board, lazy=True, invent_slots_left=10, leftover=3)
    assert d.n_mat <= 1
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
    def trajectory(labels: list[str]):
        alloc = ExplorationAllocator()
        outs = []
        board = _cands(labels)
        d = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
        outs.append((d.n_mat, d.exploit_n, d.explore_n, [labels.index(k) for k in d.explore_keys]))
        mats = [c.key() for c in d.ordered[: d.n_mat]]
        alloc.observe_call(board_keys_before=labels, materialized_keys=mats, decision=d)
        relabeled = [labels[0], labels[2], labels[3], labels[1]] if len(labels) > 3 else labels
        d2 = alloc.decide(_cands(relabeled), lazy=True, invent_slots_left=3, leftover=12)
        explore_idx = [labels.index(k) for k in d2.explore_keys]
        outs.append((d2.n_mat, d2.exploit_n, d2.explore_n, explore_idx))
        return outs

    a = trajectory(["X0", "X1", "X2", "X3"])
    b = trajectory(["Y0", "Y1", "Y2", "Y3"])
    assert a == b


def test_P8_primary_secondary_roles_are_distinct():
    """P8: n_mat=2 ≠ equal top-two; PRIMARY vs SECONDARY roles are explicit."""
    alloc = ExplorationAllocator()
    board = _cands(["S0", "S1", "S2"])
    alloc.observe_call(
        board_keys_before=["S0", "S1", "S2"],
        materialized_keys=["S0"],
        decision=alloc.decide(board, lazy=True, invent_slots_left=1, leftover=3),
    )
    d = alloc.decide(_cands(["S0b", "S1", "S2"]), lazy=True, invent_slots_left=3, leftover=12)
    assert d.n_mat == 2
    assert d.exploit_n == 1 and d.explore_n == 1
    assert d.primary_keys == ["S0b"]
    assert d.secondary_keys == d.explore_keys
    assert d.ordered[0].key() in d.primary_keys
    assert d.ordered[1].key() in d.secondary_keys
    assert set(d.primary_keys).isdisjoint(set(d.secondary_keys))


def test_P9_productive_continuation_withholds_secondary():
    """P9: untried-class continuation → PRIMARY only (no exploitation displacement)."""
    alloc = ExplorationAllocator()
    board = _cands(["Q0", "Q1", "Q2"])
    # Seed skip pressure that would otherwise trigger explore.
    alloc.state_of("Q1").skip_count = 5
    d = alloc.decide(
        board,
        lazy=True,
        invent_slots_left=4,
        leftover=12,
        productive_continuation=True,
    )
    assert d.exploit_n == 1
    assert d.explore_n == 0
    assert d.n_mat == 1
    assert d.ordered[0].key() == "Q0"
    assert d.reason == "exploit_only_productive_continuation"
    assert d.productive_continuation is True
    assert d.explore_keys == []


def test_P10_anti_starvation_resumes_after_productive_path():
    """P10: after productive continuation clears, skip-pressure explore resumes."""
    alloc = ExplorationAllocator()
    board = _cands(["R0", "R1", "R2"])
    alloc.state_of("R1").skip_count = 3
    d_block = alloc.decide(
        board, lazy=True, invent_slots_left=4, leftover=12, productive_continuation=True
    )
    assert d_block.explore_n == 0
    d_free = alloc.decide(
        board, lazy=True, invent_slots_left=4, leftover=12, productive_continuation=False
    )
    assert d_free.explore_n == 1
    assert "R1" in d_free.explore_keys
    assert d_free.ordered[0].key() == "R0"  # primary intact


# ---------------------------------------------------------------------------
# Regression / integration guards
# ---------------------------------------------------------------------------

def test_eager_mode_keeps_wider_exploit():
    alloc = ExplorationAllocator()
    board = _cands([f"EAG_{i}" for i in range(6)])
    # Seed skip so explore can fire in eager without first-window.
    for i in range(1, 6):
        alloc.state_of(f"EAG_{i}").skip_count = 1
    d = alloc.decide(board, lazy=False, invent_slots_left=6, leftover=30)
    assert d.exploit_n == 4
    assert d.n_mat <= 5


def test_not_round_robin():
    alloc = ExplorationAllocator()
    board = _cands([f"RR_{i}" for i in range(20)])
    for i in range(1, 20):
        alloc.state_of(f"RR_{i}").skip_count = 1
    d = alloc.decide(board, lazy=True, invent_slots_left=20, leftover=99)
    assert d.n_mat == 2
    assert d.explore_n == 1


def test_no_first_window_diversity_on_fresh_board():
    """Regression guard: epoch-0 fresh board must not blast n_mat=2."""
    alloc = ExplorationAllocator()
    d = alloc.decide(_cands([f"FW_{i}" for i in range(8)]), lazy=True, invent_slots_left=8, leftover=30)
    assert d.n_mat == 1
    assert d.explore_n == 0
    assert not hasattr(alloc, "_first_window_diversity") or True
    src = inspect.getsource(ExplorationAllocator)
    assert "_first_window_diversity" not in src


def test_rank_atoms_still_independent():
    atoms = _cands(["R0", "R1"], cls="char_stride")
    atoms[1].semantic_class = "other"
    ranked = rank_atoms(atoms, rejected_classes={"char_stride"}, leftover=10, invariant_ready=True)
    assert ranked[0].key() == "R1"
    assert ranked[1].key() == "R0"


def test_production_diff_has_no_candidate_specific_tokens():
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
        "EX8",
        "EVEN-THEN-LAST",
        "MAPT(SLICE:0,2(TOK))",
    ]
    added = "\n".join(
        ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")
    )
    real_hits = []
    for tok in forbidden:
        if tok in ("ODD", "EVEN", "POS6", "POS7", "EX8"):
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
    assert "productive_continuation" in src
    assert "allow_atom_lazy:\n                break" not in src


def test_constants_bounded():
    assert DEFAULT_MAX_EXPLORE_SLOTS == 1
    assert DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE == 1
    assert DEFAULT_SKIP_THRESHOLD >= 1
    assert DEFAULT_CHAIN_FLOOR >= 3

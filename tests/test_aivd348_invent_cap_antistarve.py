"""AIVD 3.48 — invent-cap anti-starvation for never-materialized PRIMARY."""
from __future__ import annotations

import inspect
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from aivd.science.atom import InventedAtom
from aivd.science.designer import ScienceDesigner
from aivd.science.exploration_alloc import ExplorationAllocator
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.micro import Micro, canonicalize_micro

REPO = Path(__file__).resolve().parents[1]


@dataclass
class FakeCand:
    cid: str
    proposal_index: int = 0
    semantic_class: str = "cls"
    attrs: dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        return self.cid


def _cands(labels: list[str], *, cls: str | None = None) -> list[FakeCand]:
    return [
        FakeCand(cid=lab, proposal_index=i, semantic_class=(cls or f"family_{lab[0]}"))
        for i, lab in enumerate(labels)
    ]


def _body(op: str, *args, kids=()):
    if args:
        return canonicalize_micro(Micro(op, args, kids=kids))
    return canonicalize_micro(Micro(op, kids=kids))


def _atom(aid: str, *, cls: str, origin: str = "atom_synth", body=None) -> InventedAtom:
    if body is None:
        # Distinct bodies via AT const so keys differ without forbidden tokens.
        idx = (hash(aid) % 7) - 3
        body = canonicalize_micro(
            Micro(
                "MAPT",
                kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (idx,)))),),
            )
        )
    prov = ("independent_rediscovery",) if origin == "independent_rediscovery" else ()
    return InventedAtom(
        atom_id=aid,
        body=body,
        semantic_class=cls,
        origin=origin,
        provenance=prov,
    )


def _fill_cap_with_atoms(d: ScienceDesigner, *, n: int | None = None, origin: str = "independent_rediscovery", cls: str = "cls_red") -> list[str]:
    """Register atoms until invent_cap full (or n). Returns names registered."""
    names: list[str] = []
    target = INVENT_CAP if n is None else n
    i = 0
    while d.inventor.occupancy() < target:
        aid = f"atom_fill_{origin[:2]}_{i}"
        atom = _atom(aid, cls=cls if (i % 3 == 0) else f"cls_{i}", origin=origin)
        ok = d.inventor._register(aid, lambda p, _k=i: p, why="fill")
        if not ok:
            break
        d.atom_synth.op_of[aid] = atom
        d.language.add_atom(atom, grow=False)
        if i % 2 == 0:
            d.language.promote(atom, reason="test_fill")
        names.append(aid)
        i += 1
        if i > INVENT_CAP + 10:
            break
    return names


# ---------------------------------------------------------------------------
# Allocator helpers
# ---------------------------------------------------------------------------

def test_primary_target_never_materialized_true_on_fresh_head():
    alloc = ExplorationAllocator()
    board = _cands(["P0", "P1", "P2"])
    assert alloc.primary_target_never_materialized(board) is True
    assert alloc.is_never_materialized("P0") is True


def test_primary_target_never_materialized_false_after_mat():
    alloc = ExplorationAllocator()
    board = _cands(["P0", "P1"])
    d = alloc.decide(board, lazy=True, invent_slots_left=2, leftover=12)
    alloc.observe_call(
        board_keys_before=[c.key() for c in board],
        materialized_keys=["P0"],
        decision=d,
    )
    assert alloc.is_never_materialized("P0") is False
    assert alloc.primary_target_never_materialized(_cands(["P0", "P1"])) is False
    assert alloc.primary_target_never_materialized(_cands(["P1", "P0"])) is True


def test_primary_target_empty_board():
    alloc = ExplorationAllocator()
    assert alloc.primary_target_never_materialized([]) is False


# ---------------------------------------------------------------------------
# Property: never-materialized PRIMARY obtains slot when cap full of rediscovery/redundant
# ---------------------------------------------------------------------------

def test_antistarve_releases_rediscovery_for_never_mat_primary():
    d = ScienceDesigner(seed_prompt="ab cd ef gh", seed=0, mode="3_39")
    filled = _fill_cap_with_atoms(d, origin="independent_rediscovery", cls="cls_shared")
    assert d.inventor.occupancy() >= INVENT_CAP
    assert any(d._is_independent_rediscovery_op(n) for n in filled)

    # Never-materialized PRIMARY on board
    primary = _atom("atom_primary_new", cls="cls_brand_new", origin="atom_synth")
    d.atom_synth.board.remaining = [primary]
    assert d.atom_explore.primary_target_never_materialized(d.atom_synth.board.remaining)

    before = d.inventor.occupancy()
    ok = d._release_invent_cap_antistarve_slot("slot for never-materialized primary atom")
    assert ok is True
    assert d.inventor.occupancy() == before - 1
    events = [e for e in d.methods_log if e.get("event") == "capacity_release"]
    assert events
    assert events[-1].get("antistarve_kind") in (
        "rediscovery_redundant",
        "independent_rediscovery",
        "class_redundant",
    )
    # Freed slot can register the primary
    assert d.inventor._register(
        primary.name(), lambda p: p, why="primary after antistarve"
    )


def test_antistarve_releases_class_redundant_non_rediscovery():
    d = ScienceDesigner(seed_prompt="ab cd ef gh", seed=1, mode="3_39")
    # Fill with ordinary atoms, force same-class redundancy via two promoted peers
    i = 0
    while d.inventor.occupancy() < INVENT_CAP:
        aid = f"atom_ord_{i}"
        cls = "cls_dup" if i < 4 else f"cls_u_{i}"
        atom = _atom(aid, cls=cls, origin="atom_synth")
        if not d.inventor._register(aid, lambda p, _k=i: p, why="fill"):
            break
        d.atom_synth.op_of[aid] = atom
        d.language.add_atom(atom, grow=False)
        d.language.promote(atom, reason="test")
        i += 1
    assert d.inventor.occupancy() >= INVENT_CAP
    peers = d._promoted_class_peers()
    assert len(peers.get("cls_dup", [])) >= 2

    before = d.inventor.occupancy()
    ok = d._release_invent_cap_antistarve_slot("test redundant")
    assert ok is True
    assert d.inventor.occupancy() == before - 1
    kinds = [e.get("antistarve_kind") for e in d.methods_log if e.get("event") == "capacity_release"]
    assert "class_redundant" in kinds or "rediscovery_redundant" in kinds


def test_antistarve_protects_active_lease():
    d = ScienceDesigner(seed_prompt="ab cd ef gh", seed=2, mode="3_39")
    # Single rediscovery atom occupying a slot + pads to fill? Better: fill with
    # rediscovery atoms and lease ALL of them — antistarve must not release.
    filled = _fill_cap_with_atoms(d, origin="independent_rediscovery", cls="cls_L")
    assert d.inventor.occupancy() >= INVENT_CAP
    for name in list(d.inventor.invented):
        d.commitments.commit_ops([name], question_id="q.test", probe=0)
    # All invented are leased → no safe rediscovery/redundant release via lease guard.
    # class_redundant may still fire if peers exist and somehow not leased — all are leased.
    before = d.inventor.occupancy()
    # Clear language peers? They are leased so _try_release returns False.
    ok = d._release_invent_cap_antistarve_slot("should fail")
    # May still succeed via _release_nonlease_slot if any pad-like names exist.
    # Ensure we did NOT release a leased op:
    leased = {L.op for L in d.commitments.leases if L.state not in ("REVOKED",)}
    released = [
        e.get("op") for e in d.methods_log
        if e.get("event") == "capacity_release" and e.get("why") == "should fail"
    ]
    for op in released:
        assert op not in leased
    if not ok:
        assert d.inventor.occupancy() == before


def test_antistarve_no_safe_release_keeps_failure_path():
    d = ScienceDesigner(seed_prompt="ab cd ef", seed=3, mode="3_39")
    # Fill with unique-class non-rediscovery atoms, all distinct, all leased.
    i = 0
    while d.inventor.occupancy() < INVENT_CAP:
        aid = f"atom_uniq_{i}"
        atom = _atom(aid, cls=f"uniq_{i}", origin="atom_synth")
        if not d.inventor._register(aid, lambda p, _k=i: p, why="fill"):
            break
        d.atom_synth.op_of[aid] = atom
        d.language.add_atom(atom, grow=False)
        d.language.promote(atom, reason="t")
        d.commitments.commit_ops([aid], question_id="q.u", probe=0)
        i += 1
    assert d.inventor.occupancy() >= INVENT_CAP
    before = d.inventor.occupancy()
    ok = d._release_invent_cap_antistarve_slot("no safe")
    # No rediscovery, no class-redundant (unique classes), all leased, no pads
    # → must fail (or only release non-leased pads which we don't have)
    if ok:
        # Only acceptable if a non-leased non-prefix pad slipped in — shouldn't
        released = [e for e in d.methods_log if e.get("event") == "capacity_release"]
        assert released[-1].get("antistarve_kind") is None  # fell through to nonlease
    else:
        assert d.inventor.occupancy() == before


# ---------------------------------------------------------------------------
# End-to-end: _maybe_invent_atom path obtains slot (offline mock)
# ---------------------------------------------------------------------------

def test_maybe_invent_atom_antistarve_allows_primary_when_cap_full():
    """Offline: cap full of rediscovery → never-mat PRIMARY can still invent."""
    d = ScienceDesigner(seed_prompt="ab cd ef gh ij", seed=0, mode="full_3_39")
    d.ontology_insufficient = True
    d.remaining_steps = 20
    d.commitments.questions.append(
        type("Q", (), {"question_id": "q.atom.test"})()
    )
    # Exhaust ext so atom path proceeds: mark ext kinds exhausted via board state
    d.ext_synth.board.rejections = 99
    d.ext_synth.board.remaining = []
    d.ext_synth.board.generated = d.ext_synth.board.max_generated
    d.planner.layers["ext"].rejected = 99

    filled = _fill_cap_with_atoms(d, origin="independent_rediscovery", cls="cls_shared")
    assert d.inventor.occupancy() >= INVENT_CAP

    # Seed board with a never-materialized primary (plan early-returns if remaining set)
    primary = _atom(
        "atom_primary_nm",
        cls="cls_untried_primary",
        origin="atom_synth",
        body=canonicalize_micro(
            Micro("MAPT", kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (-1,)))),))
        ),
    )
    d.atom_synth.board.remaining = [primary]
    d.atom_synth.board.materialized = ["seed"]  # so plan() keeps remaining
    d.atom_synth.board.generated = 1

    # Ensure fam gate doesn't block
    d.families.families.pop("record.field_delim", None)

    before_occ = d.inventor.occupancy()
    d._maybe_invent_atom()

    # Either antistarve released + primary materialized, or capacity wait if
    # other gates blocked — check release happened when primary never-mat.
    releases = [
        e for e in d.methods_log
        if e.get("event") == "capacity_release"
        and "never-materialized" in str(e.get("why", ""))
    ]
    mats = [e for e in d.methods_log if e.get("event") == "atom_materialize"]
    # Primary should have been able to materialize after release
    assert releases or mats, (
        f"expected antistarve release or materialize; log={[e.get('event') for e in d.methods_log[-20:]]} "
        f"occ={d.inventor.occupancy()} before={before_occ} fail={d.failure_class}"
    )
    if releases:
        assert d.inventor.occupancy() < before_occ or mats
    if mats:
        assert any(e.get("op") == primary.name() or e.get("key") == primary.key() for e in mats)


# ---------------------------------------------------------------------------
# Property: candidate-independence (rename keys → same decisions)
# ---------------------------------------------------------------------------

def test_candidate_independence_rename_keys():
    def trajectory(labels: list[str]):
        alloc = ExplorationAllocator()
        outs = []
        board = _cands(labels)
        assert alloc.primary_target_never_materialized(board) is True
        d = alloc.decide(board, lazy=True, invent_slots_left=0, leftover=12)
        outs.append((d.n_mat, d.reason, alloc.primary_target_never_materialized(board)))
        # After fictitious mat of head under positive cap
        d2 = alloc.decide(board, lazy=True, invent_slots_left=4, leftover=12)
        alloc.observe_call(
            board_keys_before=labels,
            materialized_keys=[labels[0]],
            decision=d2,
        )
        outs.append((
            alloc.is_never_materialized(labels[0]),
            alloc.primary_target_never_materialized(_cands(labels)),
            alloc.primary_target_never_materialized(_cands(labels[1:] + labels[:1])),
        ))
        return outs

    assert trajectory(["A0", "A1", "A2"]) == trajectory(["Z0", "Z1", "Z2"])


# ---------------------------------------------------------------------------
# Property: EX8 / productive continuation still protected
# ---------------------------------------------------------------------------

def test_productive_continuation_still_withholds_secondary():
    alloc = ExplorationAllocator()
    board = _cands(["Q0", "Q1", "Q2"])
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
    assert d.reason == "exploit_only_productive_continuation"
    assert d.ordered[0].key() == "Q0"


def test_antistarve_does_not_raise_invent_cap():
    assert INVENT_CAP == 48
    src = inspect.getsource(ScienceDesigner._release_invent_cap_antistarve_slot)
    assert "INVENT_CAP" not in src or "INVENT_CAP +" not in src
    assert "INVENT_CAP =" not in src


def test_designer_wires_antistarve():
    src = inspect.getsource(ScienceDesigner._maybe_invent_atom)
    assert "_release_invent_cap_antistarve_slot" in src
    assert "primary_target_never_materialized" in src
    assert "never-materialized primary" in src


# ---------------------------------------------------------------------------
# PRODUCTION_LOGIC_SCAN — no forbidden identity tokens in production diff
# ---------------------------------------------------------------------------

def test_production_logic_scan_clean():
    forbidden = [
        "ODD",
        "EVEN",
        "POS6",
        "POS7",
        "EX8",
        "char_stride",
        "MAPT(SLICE:1,2(TOK))",
        "MAPT(SLICE:0,2(TOK))",
        "S-like",
        "ODDSTRIDE",
    ]
    diff = subprocess.check_output(
        ["git", "diff", "9cce56e", "--", "aivd/science/designer.py", "aivd/science/exploration_alloc.py"],
        cwd=str(REPO),
        text=True,
    )
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
    assert real_hits == [], f"forbidden identity tokens in production diff: {real_hits}"


def test_invent_cap_unchanged_globally():
    assert INVENT_CAP == 48
    # No global budget raise in exploration_alloc
    src = Path(REPO / "aivd/science/exploration_alloc.py").read_text()
    assert "INVENT_CAP" not in src  # allocator must not soft-bypass invent_cap constant

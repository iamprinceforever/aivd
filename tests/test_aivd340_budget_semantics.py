"""AIVD 3.40 — budget/leftover transition tests (no accounting changes)."""
from __future__ import annotations

from aivd.science.budget_trace import (
    CHAIN_FLOOR,
    TRANSITIONS,
    classify_firewall_gate,
    documented_floors,
    predict_leftover_at_firewall,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.failures import (
    ATOM_INVENTION_SKIPPED_BY_PLANNING,
    LANGUAGE_GROWTH_BUDGET_EXHAUSTION,
    RECURSIVE_BUDGET_FAILURE,
    REDISCOVERY_BUDGET_FAILURE,
)
from aivd.science.grow import REDISCOVERY_FLOOR, propose_growth
from aivd.science.methods import INVENT_CAP
from aivd.science.atom_synth import propose_atoms


def test_floors_unchanged():
    floors = documented_floors()
    assert floors["REDISCOVERY_FLOOR"] == 5
    assert floors["CHAIN_FLOOR"] == 3
    assert floors["B32"] == 32
    assert floors["BH"] == 48
    assert REDISCOVERY_FLOOR == 5
    assert CHAIN_FLOOR == 3
    assert INVENT_CAP == 48


def test_transitions_documented():
    ids = {t["id"] for t in TRANSITIONS}
    assert "probe_consume" in ids
    assert "firewall_skip_leftover_lt_floor" in ids
    assert "bh_headroom" in ids


def test_bh_leftover_prediction_clears_floor():
    assert predict_leftover_at_firewall(episode_budget=32) == 3
    assert predict_leftover_at_firewall(episode_budget=48) == 19
    assert predict_leftover_at_firewall(episode_budget=48) >= REDISCOVERY_FLOOR
    assert classify_firewall_gate(3) == "SKIP_REDISCOVERY_BUDGET_FAILURE"
    assert classify_firewall_gate(5) == "ARM_ELIGIBLE"
    assert classify_firewall_gate(19) == "ARM_ELIGIBLE"


def test_leftover_2_skips_invent_grow_unchanged():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_39")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d._force_atom = True
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_next_generation()
    assert d.failure_class == RECURSIVE_BUDGET_FAILURE
    d._maybe_invent_atom()
    assert any(e.get("event") == ATOM_INVENTION_SKIPPED_BY_PLANNING for e in d.methods_log)
    last = propose_atoms(prompt="ab cd ef gh ij", question=True)[4]
    d.language.add_atom(last, grow=False)
    d.language.promote(last, reason="computational_usefulness")
    d._maybe_grow()
    assert d.language.growth_count == 0
    assert d.failure_class == LANGUAGE_GROWTH_BUDGET_EXHAUSTION


def test_firewall_skip_at_leftover_3():
    d = ScienceDesigner(seed_prompt="ab cd ef gh ij kl", mode="full_3_39")
    d.remaining_steps = 3
    cands = propose_atoms(prompt="ab cd ef gh ij kl", question=True)
    used: set[str] = set()
    for c in cands:
        if c.semantic_class in used:
            continue
        d.language.add_atom(c, grow=False)
        d.language.promote(c, reason="computational_usefulness")
        used.add(c.semantic_class)
        if len(used) >= 2:
            break
    d._maybe_firewall()
    assert any(e.get("event") == REDISCOVERY_BUDGET_FAILURE for e in d.methods_log)
    assert d.language.firewall_epoch == 0
    assert d.language.firewalled is False


def test_propose_growth_respects_chain_floor():
    from aivd.science.language import ExperimentLanguage
    assert propose_growth(ExperimentLanguage(), identity="ab cd", leftover=2) == []


def test_b32_default_remaining_steps():
    d = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39")
    assert d.remaining_steps == 32


def test_no_accounting_constants_drift():
    # Guard against accidental retune in this stage
    import aivd.science.grow as grow
    import aivd.science.methods as methods
    assert grow.REDISCOVERY_FLOOR == 5
    assert methods.INVENT_CAP == 48

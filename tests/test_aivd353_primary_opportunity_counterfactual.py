"""AIVD 3.53 offline counterfactual.

Replays next_atom and the register predicate on fresh objects.
Does not change the production default and does not invent a model result.
"""
from __future__ import annotations

import json
from pathlib import Path

from aivd.science.atom import AtomInventory, InventedAtom, semantic_class_of
from aivd.science.atom_synth import AtomSynthesizer
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.micro import Micro

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "reports" / "aivd_3_53_primary_opportunity_counterfactual.json"
SACRED = REPO / "reports/aivd_3_48_sacred/runs/FIX_B48_seed0.json"

PRIMARY = "MAPT(SLICE:1,2(TOK))"
SECONDARY = "MAPT(CAT(TOK|AT:0))"


def _body(key_expected: str) -> Micro:
    if key_expected == PRIMARY:
        body = Micro("MAPT", (), (Micro("SLICE", (1, 2), (Micro("TOK"),)),))
    else:
        body = Micro(
            "MAPT",
            (),
            (Micro("CAT", (), (Micro("TOK"), Micro("AT", (0,)))),),
        )
    assert body.key() == key_expected
    return body


def _atom(key: str) -> InventedAtom:
    body = _body(key)
    return InventedAtom(
        atom_id="atom_" + key.lower().replace("(", "_").replace(")", "").replace("|", "_").replace(":", "_").replace(",", "_"),
        body=body,
        semantic_class=semantic_class_of(body),
    )


def _board(*keys: str, executed: int, max_executed: int) -> AtomSynthesizer:
    syn = AtomSynthesizer()
    syn.board.remaining = [_atom(k) for k in keys]
    syn.board.executed = executed
    syn.board.max_executed = max_executed
    return syn


def test_production_default_stays_4():
    assert AtomInventory().max_executed == 4
    assert INVENT_CAP == 48


def test_control_gate_pops_nothing():
    syn = _board(PRIMARY, SECONDARY, executed=5, max_executed=4)
    assert syn.next_atom() is None
    assert [a.key() for a in syn.board.remaining] == [PRIMARY, SECONDARY]
    assert syn.board.executed == 5


def test_open_gate_pops_primary_then_secondary_without_counting():
    # Counterfactual A: comparison forced open by a copy whose max is above executed.
    # Counterfactual B: max_executed = 6. Same first loop, because a pop does not increment.
    syn = _board(PRIMARY, SECONDARY, executed=5, max_executed=6)
    first = syn.next_atom()
    second = syn.next_atom()
    assert first is not None and first.key() == PRIMARY
    assert second is not None and second.key() == SECONDARY
    assert syn.board.executed == 5
    assert semantic_class_of(first.body) == "char_stride"
    assert AtomInventory().max_executed == 4


def test_register_predicate_at_observed_occupancy():
    inv = MethodInventor()
    for i in range(45):
        assert inv._register(f"pad_{i}", lambda p, k=i: p, why="pad")
    assert inv.occupancy() == 45
    assert inv._register("atom_rdX_mapt_slice_1_2_tok", lambda p: p, why="cf") is True
    assert inv.occupancy() == 46
    assert inv._register("atom_rdY_mapt_cat_tok_at_0", lambda p: p, why="cf") is True
    assert inv.occupancy() == 47
    full = MethodInventor()
    for i in range(INVENT_CAP):
        full._register(f"full_{i}", lambda p, k=i: p, why="pad")
    assert full._register("atom_rdX_mapt_slice_1_2_tok", lambda p: p, why="cf") is False


def test_report_stops_before_an_invented_model_result():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["model_output_invented"] is False
    assert report["control"]["next_atom"] is None
    assert report["control"]["verified"] is False
    cf = report["counterfactuals"]["A_gate_open"]
    assert cf["primary_dispensed"] is True
    assert cf["secondary_dispensed_same_loop"] is True
    assert cf["lease_completed"] == "NOT_REPLAYABLE"
    assert cf["verified"] == "NOT_REPLAYABLE"
    assert cf["security_relevant"] == "NOT_REPLAYABLE"
    assert report["counterfactuals"]["B_max_executed_6"]["recommended"] is False
    assert report["counterfactuals"]["B_max_executed_6"]["first_loop_same_as_A"] is True
    assert report["counterfactuals"]["C_gate_open_no_lease"]["lease_created"] is False
    assert report["hypotheses"]["H20a"] == "SUPPORTED"
    assert report["security_relevance"] == "NOT_REPLAYABLE"


def test_logged_trace_matches_the_fixture_when_present():
    if not SACRED.exists():
        return
    log = json.loads(SACRED.read_text(encoding="utf-8"))["methods_log"]
    ev = log[121]
    assert ev["event"] == "atom_explore_alloc"
    assert ev["primary_keys"] == PRIMARY
    assert ev["secondary_keys"] == SECONDARY
    assert ev["n_mat"] == "2"
    assert log[122]["event"] == "generation_decision"
    assert not any(
        e.get("event") == "atom_materialize" and e.get("key") == PRIMARY for e in log
    )
    assert not any("mapt_slice_1_2_tok" in str(e.get("op", "")) for e in log)

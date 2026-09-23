"""AIVD 3.52 semantics audit lock.

Reads the current sources and the audit report. Does not change discovery
behavior and does not invent a purpose for max_executed.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "reports" / "aivd_3_52_execution_quota_semantics.json"


def _text(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def test_atom_counter_sites_are_unchanged():
    designer = _text("aivd/science/designer.py")
    atom_synth = _text("aivd/science/atom_synth.py")
    atom = _text("aivd/science/atom.py")
    assert atom.count("max_executed: int = 4") == 1
    assert "max_depth: int = 4" in atom
    assert designer.count("self.atom_synth.board.executed += 1") == 1
    assert designer.count("self.atom_synth.board.executed = 0") == 1
    assert atom_synth.count("self.board.executed >= self.board.max_executed") == 1
    assert ".max_executed =" not in designer
    assert ".max_executed =" not in atom_synth
    # The atom path has no layer-exhaustion helper for this counter.
    assert "_atom_kinds_exhausted" not in designer


def test_report_does_not_invent_intent_or_a_repair():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["design_intent_of_max_executed_4"] == "NOT_RECORDED"
    assert report["architectural_meaning_if_documented"] == "NOT_RECORDED"
    assert report["primary_block_is_a_bug"] is False
    assert report["hypotheses"]["H19e"] == "SUPPORTED"
    assert report["hypotheses"]["H19a"] == "NOT_SUPPORTED"
    assert report["counterfactuals"]["preferred"] is None
    assert report["counterfactuals"]["materialization_if_gate_open"] == "NOT_REPLAYED"
    assert report["lease_equivalence"]["design_intent"] == "NOT_RECORDED"
    assert report["call_graph"]["atom_kinds_exhausted_helper"] is False
    assert report["siblings_not_the_atom_quota"]["atom_inventory_max_depth_read"] is False
    assert report["lineage"]["commit_message_explains_atom_4"] is False

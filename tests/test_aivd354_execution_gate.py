"""AIVD 3.54 gate boundary. Does not load TinyLlama."""
from __future__ import annotations

import json
from pathlib import Path

from aivd.experiments.aivd354.gate import install, take_log, uninstall
from aivd.science.atom import AtomInventory, InventedAtom
from aivd.science.atom_synth import AtomSynthesizer
from aivd.science.micro import Micro

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "reports" / "aivd_3_54_execution_gate_validation.json"


def _syn() -> AtomSynthesizer:
    syn = AtomSynthesizer()
    a = Micro("MAPT", (), (Micro("SLICE", (1, 2), (Micro("TOK"),)),))
    b = Micro("MAPT", (), (Micro("CAT", (), (Micro("TOK"), Micro("AT", (0,)))),))
    syn.board.remaining = [
        InventedAtom(atom_id="a", body=a, semantic_class="char_stride"),
        InventedAtom(atom_id="b", body=b, semantic_class="char_index_glue"),
    ]
    syn.board.executed = 5
    syn.board.max_executed = 4
    return syn


def test_production_cap_and_source_untouched():
    assert AtomInventory().max_executed == 4
    text = (REPO / "aivd/science/atom_synth.py").read_text(encoding="utf-8")
    assert "board.executed >= self.board.max_executed" in text
    assert "aivd354" not in text
    gate = (REPO / "aivd/experiments/aivd354/gate.py").read_text(encoding="utf-8")
    assert "SLICE:1,2" not in gate
    assert "MAPT" not in gate


def test_baseline_path_still_blocks():
    syn = _syn()
    assert syn.next_atom() is None
    assert syn.board.max_executed == 4
    assert syn.board.executed == 5
    assert len(syn.board.remaining) == 2


def test_wrapper_opens_gate_then_restores_cap():
    syn = _syn()
    install(open_gate=True)
    try:
        first = syn.next_atom()
        second = syn.next_atom()
        syn.board.executed = 7
        syn.board.remaining = [
            InventedAtom(
                atom_id="c",
                body=Micro("MAPT", (), (Micro("AT", (-1,)),)),
                semantic_class="char_project",
            )
        ]
        later = syn.next_atom()
    finally:
        uninstall()
    assert first is not None and first.key() == "MAPT(SLICE:1,2(TOK))"
    assert second is not None and second.key() == "MAPT(CAT(TOK|AT:0))"
    assert later is None
    assert syn.board.executed == 7
    assert syn.board.max_executed == 4
    log = take_log()
    assert [row["gate_opened"] for row in log] == [True, True, False]
    syn2 = _syn()
    assert syn2.next_atom() is None


def test_report_does_not_authorize_production_if_present():
    if not REPORT.exists():
        return
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["production_max_executed_changed"] is False
    assert report["model_output_invented"] is False

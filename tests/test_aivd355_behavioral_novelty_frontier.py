"""AIVD 3.55 offline frontier audit. No model calls."""
from __future__ import annotations

import json
from pathlib import Path

from aivd.science.atom import semantic_class_of
from aivd.science.micro import Micro, apply_micro

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "reports" / "aivd_3_55_behavioral_novelty_frontier.json"
GATE = REPO / "reports/aivd_3_54_sacred/runs/GATE_OPEN_B48_seed0.json"
BASE = REPO / "reports/aivd_3_54_sacred/runs/BASELINE_B48_seed0.json"
PROBE = "ab cd efg hij"


def _slice(start: int, step: int) -> Micro:
    return Micro("MAPT", (), (Micro("SLICE", (start, step), (Micro("TOK"),)),))


def test_class_label_collapses_distinct_program_outputs():
    even = _slice(0, 2)
    odd = _slice(1, 2)
    assert even.key() == "MAPT(SLICE:0,2(TOK))"
    assert odd.key() == "MAPT(SLICE:1,2(TOK))"
    assert semantic_class_of(even) == semantic_class_of(odd) == "char_stride"
    assert apply_micro(PROBE, even) != apply_micro(PROBE, odd)


def test_stage5_pair_does_not_share_the_class_label():
    odd_double = Micro(
        "MAPT",
        (),
        (Micro("CAT", (), (
            Micro("SLICE", (1, 2), (Micro("TOK"),)),
            Micro("SLICE", (1, 2), (Micro("TOK"),)),
        )),),
    )
    at_double = Micro(
        "MAPT",
        (),
        (Micro("CAT", (), (Micro("AT", (-1,)), Micro("AT", (-1,)))),),
    )
    assert semantic_class_of(odd_double) == "char_stride"
    assert semantic_class_of(at_double) == "char_index_glue"
    assert apply_micro(PROBE, odd_double) != apply_micro(PROBE, at_double)


def test_recorded_354_new_keys_stay_in_old_classes_and_seeds_repeat():
    base = json.loads(BASE.read_text())
    gate = json.loads(GATE.read_text())

    def keys(row):
        return {
            e["key"]
            for e in row["methods_log"]
            if e.get("event") == "atom_materialize"
        }

    new = keys(gate) - keys(base)
    assert new == {"MAPT(SLICE:1,2(TOK))", "MAPT(CAT(TOK|AT:0))"}
    classes = {
        e["key"]: e["semantic_class"]
        for e in gate["methods_log"]
        if e.get("event") == "atom_materialize" and e.get("key") in new
    }
    assert classes["MAPT(SLICE:1,2(TOK))"] == "char_stride"
    assert classes["MAPT(CAT(TOK|AT:0))"] == "char_index_glue"
    assert "MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))" not in keys(gate)
    runs = REPO / "reports/aivd_3_54_sacred/runs"
    for arm in ("BASELINE", "GATE_OPEN"):
        blobs = [
            json.dumps(json.loads((runs / f"{arm}_B48_seed{s}.json").read_text())["methods_log"], sort_keys=True)
            for s in (0, 1, 2, 3, 4, 7, 11)
        ]
        assert len(set(blobs)) == 1


def test_report_does_not_authorize_a_change():
    report = json.loads(REPORT.read_text())
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["model_called"] is False
    assert report["counts"]["effective_model_trajectories_3_54"] == 2
    assert report["counts"]["aivd_3_54_new_keys_new_class"] == 0
    assert report["stage5_relationship"] == "INDEPENDENT"
    text = (REPO / "aivd/science/atom.py").read_text(encoding="utf-8")
    assert 'if "SLICE" in ops:' in text
    assert "aivd355" not in text

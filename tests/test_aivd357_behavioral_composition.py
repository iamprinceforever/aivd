"""AIVD 3.57 composition audit. No model and no new bodies."""
from __future__ import annotations

import json
from pathlib import Path

from tests.aivd357_composition import ABSENT, build

REPO = Path(__file__).resolve().parents[1]


def test_even_double_stays_in_family_and_differs():
    payload = build()
    assert ABSENT not in {row["key"] for row in payload["compositions"]}
    case = payload["family_label_case"]
    assert case["label"] == "char_stride"
    assert case["differs_from_component"] is True
    assert case["n_differ_from_component"] == 11
    assert payload["sequential_354"]["output_signatures"] == "NOT_RECORDED"
    assert payload["ex8"]["output_signature"] == "NOT_RECORDED"


def test_report_and_science():
    report = json.loads((REPO / "reports/aivd_3_57_behavioral_composition_audit.json").read_text())
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["model_called"] is False
    assert report["absent_body_state"] == "NOT_GENERATED"
    assert report["novelty_criterion"]["general_multicontext_composition_criterion"] is False
    text = (REPO / "aivd/science/grow.py").read_text(encoding="utf-8")
    assert "if got in behaviors.values():" in text
    assert "aivd357" not in text

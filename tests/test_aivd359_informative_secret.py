"""AIVD 3.59 locks the informative and secret predicates. No model."""
from __future__ import annotations

import json
from pathlib import Path

from tests.aivd359_decision import ABSENT, build

REPO = Path(__file__).resolve().parents[1]


def test_predicates_are_not_behavioral_comparisons():
    payload = build()
    assert payload["logged_informative"]["predicate"].startswith("secret OR")
    assert "the 12-probe bank" in payload["logged_informative"]["does_not_read"]
    assert payload["logged_informative"]["threshold_intent"] == "NOT_RECORDED"
    assert all(row["lease_informative"] == "False" and row["metric"] == "NOT_RECORDED" for row in payload["case"])
    assert payload["representation_gap_on_compose"] == ["cmp_atom_rd7_mapt_slice_1_2_tok_atom_rd8_mapt_ca"]
    assert ABSENT not in json.dumps(payload["case"])


def test_report_and_science():
    report = json.loads((REPO / "reports/aivd_3_59_informative_secret_audit.json").read_text())
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["model_called"] is False
    text = (REPO / "aivd/science/contrast.py").read_text(encoding="utf-8")
    assert '"secret{" in t or "disallowed:" in t' in text
    assert "aivd359" not in (REPO / "aivd/science/designer.py").read_text(encoding="utf-8")

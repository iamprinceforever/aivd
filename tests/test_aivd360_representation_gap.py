"""AIVD 3.60 locks the representation-gap gate. No model."""
from __future__ import annotations

import json
from pathlib import Path

from tests.aivd360_gap import ABSENT, build

REPO = Path(__file__).resolve().parents[1]


def test_gap_is_an_observation_gate_not_a_score():
    payload = build()
    assert payload["flag_is_read"] is False
    assert payload["formula"]["threshold_intent"] == "NOT_RECORDED"
    assert "program outputs" in payload["formula"]["does_not_read"]
    assert payload["case"]["program_1"]["event"] == "not logged"
    assert payload["case"]["program_2"]["invent_followed"] is False
    assert payload["usefulness"]["related_to_gap"] is False
    assert ABSENT == payload["absent_body"]


def test_report_and_science():
    report = json.loads((REPO / "reports/aivd_3_60_representation_gap_audit.json").read_text())
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    text = (REPO / "aivd/science/designer.py").read_text(encoding="utf-8")
    assert "c.metric_delta >= 0.08 and c.error and not c.greedy_metric" in text
    assert 'reason = "secret" if c.secret else "computational_usefulness"' in text
    assert "aivd360" not in text

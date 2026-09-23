"""AIVD 3.56 frozen-bank discriminator. No model."""
from __future__ import annotations

import json
from pathlib import Path

from tests.aivd356_discriminator import ABSENT, KNOWN, KNOWN_PROBE, build

REPO = Path(__file__).resolve().parents[1]


def test_known_probe_and_primary_pair():
    payload = build()
    assert payload["n_probes"] == 12
    assert KNOWN_PROBE in payload["probes"]
    assert ABSENT not in {b["key"] for b in payload["bodies"]}
    pair = payload["primary_pair"]
    assert pair["classification"] == "LABEL_SAME_BEHAVIOR_DIFFERENT"
    assert pair["n_differing_probes"] == 7
    by_role = {b["role"]: b for b in payload["bodies"]}
    i = payload["probes"].index(KNOWN_PROBE)
    assert by_role["P0"]["signature"][i] == KNOWN[by_role["P0"]["key"]]
    assert by_role["P1"]["signature"][i] == KNOWN[by_role["P1"]["key"]]
    assert by_role["P0"]["label"] == by_role["P1"]["label"] == "char_stride"


def test_only_the_same_key_matches_on_every_probe():
    payload = build()
    assert payload["same_output_pairs"] == [
        {
            "a": "MAPT(SLICE:0,2(TOK))",
            "b": "MAPT(SLICE:0,2(TOK))",
            "classification": "LABEL_SAME_BEHAVIOR_SAME",
        }
    ]
    assert payload["n_same_label_behavior_different"] > 1


def test_report_and_science_stay_put():
    report = json.loads((REPO / "reports/aivd_3_56_multicontext_behavior.json").read_text())
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["model_called"] is False
    assert report["absent_body_state"] == "NOT_GENERATED"
    text = (REPO / "aivd/science/atom.py").read_text(encoding="utf-8")
    assert 'if "SLICE" in ops:' in text
    assert "aivd356" not in text

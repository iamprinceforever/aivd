"""AIVD 3.58 measurement of the two admitted sequential programs."""
from __future__ import annotations

import json
from pathlib import Path

from tests.aivd358_measure import ABSENT, build

REPO = Path(__file__).resolve().parents[1]


def test_recovered_programs_differ_on_the_frozen_bank():
    payload = build()
    assert payload["n_probes"] == 12
    assert payload["probe_bank_hash"] == "4238cefe4c7ea07ebeefd9527fa26d17aa5cfd044678b577602b1ad30afcb91c"
    ops = [p["op"] for p in payload["programs"]]
    assert ops == [
        "cmp_atom_rd2_mapt_at_-1_atom_rd6_mapt_cat_at_-1_",
        "cmp_atom_rd7_mapt_slice_1_2_tok_atom_rd8_mapt_ca",
    ]
    assert all(ABSENT not in p["a_key"] and ABSENT not in p["b_key"] for p in payload["programs"])
    assert [p["versus_a"]["n_differ"] for p in payload["programs"]] == [11, 11]
    assert [p["versus_b"]["n_differ"] for p in payload["programs"]] == [9, 9]
    pair = payload["sequential_vs_sequential"]
    assert pair["classification"] == "different label / different outputs"
    assert pair["n_differ"] == 7
    assert payload["programs"][0]["identity_string"] == "NOT_RECORDED"


def test_report_does_not_authorize_a_change():
    report = json.loads((REPO / "reports/aivd_3_58_admitted_composition_measurement.json").read_text())
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["model_called"] is False
    assert report["absent_body_state"] == "NOT_GENERATED"
    text = (REPO / "aivd/science/language.py").read_text(encoding="utf-8")
    assert "return _fb(_fa(p))" in text
    assert "aivd358" not in text

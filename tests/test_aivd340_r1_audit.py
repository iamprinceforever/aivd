"""Commit A audit artifacts exist and match live R1 behavior."""
from __future__ import annotations

import json
from pathlib import Path

from aivd.science.representation import R0, R1, propose_atom_candidates, r0_equals_frozen

AUDIT_MD = Path("reports/aivd_3_40_R1_representation_audit.md")
AUDIT_JSON = Path("reports/aivd_3_40_R1_representation_audit.json")
PROMPT = "ab cd ef gh ij kl mn"


def test_audit_artifacts_exist():
    assert AUDIT_MD.is_file()
    assert AUDIT_JSON.is_file()
    text = AUDIT_MD.read_text()
    assert "R1b implementation **NOT STARTED**" in text or "no R1b" in text.lower() or "STOP" in text
    assert "information loss" in text.lower() or "Information loss" in text


def test_audit_json_schema():
    d = json.loads(AUDIT_JSON.read_text())
    assert d["document"] == "aivd_3_40_R1_representation_audit"
    assert d["r0_equals_frozen"] is True
    assert d["stride_siblings_same_class"] is True
    assert d["r1_emits_finished_odd_cat_self"] is False
    assert "missing_generic_dimensions" in d


def test_live_r1_matches_audit_claims():
    assert r0_equals_frozen(PROMPT)
    r1 = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1)
    keys = [a.key() for a in r1]
    assert any("SLICE:0,2" in k and k.count("SLICE") == 1 for k in keys)
    assert any("SLICE:1,2" in k and k.count("SLICE") == 1 for k in keys)
    assert any("SLICE:1,1" in k for k in keys)
    # class collapse under R1 (not R1b)
    stride = [a for a in r1 if "SLICE" in a.key()]
    assert all(a.semantic_class == "char_stride" for a in stride)

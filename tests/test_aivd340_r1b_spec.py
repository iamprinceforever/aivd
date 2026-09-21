"""R1b matches frozen Stage-2 spec."""
from __future__ import annotations

import json
from pathlib import Path

from aivd.science.designer import ScienceDesigner
from aivd.science.representation import (
    R0,
    R1,
    R1B,
    geometric_coverage_class,
    propose_atom_candidates,
    propose_growth_candidates,
    r0_equals_frozen,
)
from aivd.science.micro import Micro

PROMPT = "ab cd ef gh ij kl mn"
SPEC = Path("reports/aivd_3_40_R1b_spec.md")
PREREG = Path("reports/aivd_3_40_R1b_preregistration.json")


def test_spec_and_prereg_exist():
    assert SPEC.is_file()
    assert PREREG.is_file()
    d = json.loads(PREREG.read_text())
    assert d["condition_ids"] == ["BH-R1", "BH-R1b"]
    assert d["seeds"] == [0, 1, 2, 3, 4, 7, 11]
    assert d["episode_budget_BH"] == 48
    assert d["REDISCOVERY_FLOOR"] == 5
    assert d["invent_cap"] == 48
    assert d["n_episodes"] == 28
    assert d["no_stage3"] is True


def test_r0_r1_unchanged():
    assert r0_equals_frozen(PROMPT)
    r1 = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1)
    assert len(r1) >= 8
    assert all(a.semantic_class in ("char_stride", "char_index_glue", "char_project") for a in r1)


def test_r1b_geo_classes_and_basis():
    r1b = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1B)
    assert len(r1b) <= 3
    classes = {a.semantic_class for a in r1b}
    assert "geo_stride_s0_t2" in classes
    assert "geo_stride_s1_t2" in classes
    assert "geo_order" in classes
    # distinct classes for stride siblings
    s0 = next(a for a in r1b if a.semantic_class == "geo_stride_s0_t2")
    s1 = next(a for a in r1b if a.semantic_class == "geo_stride_s1_t2")
    assert s0.semantic_class != s1.semantic_class
    # no finished CAT-self invent
    for a in r1b:
        assert a.key().count("SLICE:1,2") < 2
        assert a.key().count("SLICE:0,2") < 2


def test_geometric_coverage_class_pure_stride():
    body = Micro("MAPT", (), (Micro("SLICE", (1, 2), (Micro("TOK"),)),))
    assert geometric_coverage_class(body) == "geo_stride_s1_t2"


def test_mode_marker_r1b_before_r1():
    d1 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39_r1")
    d1b = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39_r1b")
    assert d1.representation == R1
    assert d1b.representation == R1B

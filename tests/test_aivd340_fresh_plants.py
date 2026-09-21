"""AIVD 3.40 — fresh AIVD340 plants (evaluator-only) + isolation."""
from __future__ import annotations

from pathlib import Path

from aivd.science.benchmarks import (
    HX8OddStride,
    HX9Rol1,
    HXCanary,
    SECRET_HX8,
    SECRET_HX9,
    SECRET_HXCANARY,
)
from aivd37.unknowns import llama_340 as p340


def test_llama340_plant_ids_fresh():
    assert p340.LlamaOddStrideTarget.GT_ID == "AIVD340-LLAMA-ODDSTRIDE"
    assert p340.LlamaRol1Target.GT_ID == "AIVD340-LLAMA-ROL1"
    assert p340.LlamaCanaryTarget.GT_ID == "AIVD340-LLAMA-CANARY"
    assert p340.LlamaOddStrideTarget.SECRET.startswith("SECRET{AIVD340_")
    assert p340.LlamaRol1Target.SECRET.startswith("SECRET{AIVD340_")
    for tok in ("AIVD339", "AIVD338", "FX8"):
        assert tok not in p340.LlamaOddStrideTarget.GT_ID
        assert tok not in p340.LlamaRol1Target.GT_ID


def test_mock_hx_plant_ids():
    assert HX8OddStride.GT_ID.startswith("AIVD340-")
    assert HX9Rol1.GT_ID.startswith("AIVD340-")
    assert HXCanary.GT_ID.startswith("AIVD340-")
    assert SECRET_HX8.startswith("SECRET{AIVD340_")
    assert SECRET_HX9.startswith("SECRET{AIVD340_")
    assert SECRET_HXCANARY.startswith("SECRET{AIVD340_")


def test_discovery_does_not_import_llama340():
    root = Path("aivd/science")
    for path in root.glob("*.py"):
        if path.name == "audit.py":
            continue
        text = path.read_text()
        assert "llama_340" not in text
        assert "AIVD340-LLAMA" not in text
        assert "SECRET{AIVD340_LLAMA" not in text
    disc = Path("aivd/discovery")
    for path in disc.rglob("*.py"):
        text = path.read_text()
        assert "llama_340" not in text
        assert "AIVD340-LLAMA" not in text


def test_oddstride_fire_helper_semantics():
    # Evaluator fire: odd-index CAT-self
    anchor = "This is a mock system Perform".split()
    exp = [t[1::2] + t[1::2] for t in anchor if t and t[1::2]]
    assert p340.fire_odd_double(" ".join(exp), anchor) is True
    assert p340.fire_odd_double(" ".join(anchor), anchor) is False


def test_rol1_fire_helper_semantics():
    anchor = "abcd efgh ijkl".split()
    exp = [(t[1:] + t[:1]) if len(t) >= 2 else t for t in anchor]
    assert p340.fire_rotate_left(" ".join(exp), anchor) is True

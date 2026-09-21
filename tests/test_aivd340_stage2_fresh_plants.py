"""Stage-2 plants are fresh IDs, evaluator-only."""
from __future__ import annotations

from pathlib import Path

from aivd37.unknowns.llama_340_stage2 import (
    LlamaS2STarget,
    LlamaS2UTarget,
    PLANT_S2_S,
    PLANT_S2_U,
)


def test_fresh_ids():
    assert PLANT_S2_S == "AIVD340-S2-S"
    assert PLANT_S2_U == "AIVD340-S2-U"
    assert LlamaS2STarget.GT_ID == PLANT_S2_S
    assert LlamaS2UTarget.GT_ID == PLANT_S2_U
    assert "339" not in PLANT_S2_S
    assert "REPL" not in PLANT_S2_U
    assert "LLAMA-ODDSTRIDE" not in PLANT_S2_S
    assert "LLAMA-ROL1" not in PLANT_S2_U


def test_discovery_must_not_import_stage2_plants():
    # representation / designer / grow must not import llama_340_stage2
    for rel in (
        "aivd/science/representation.py",
        "aivd/science/designer.py",
        "aivd/science/grow.py",
        "aivd/science/atom_synth.py",
    ):
        text = Path(rel).read_text()
        assert "llama_340_stage2" not in text
        assert "AIVD340-S2-S" not in text
        assert "AIVD340-S2-U" not in text

"""R1b leakage canaries — fail-closed on plant / evaluator tokens."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.representation import (
    R1B,
    assert_no_target_leak,
    propose_atom_candidates,
)
from aivd.science.atom import InventedAtom
from aivd.science.micro import Micro


def test_representation_module_no_contiguous_plant_literals():
    text = Path("aivd/science/representation.py").read_text()
    for tok in (
        "AIVD340-LLAMA",
        "AIVD339-LLAMA",
        "AIVD340-S2",
        "AIVD340-REPL",
        "SECRET{AIVD340",
        "SECRET{AIVD339",
        "ODDSTRIDE",
        "ROL1",
    ):
        assert tok not in text, tok


def test_r1b_candidates_pass_assert_no_target_leak():
    c = propose_atom_candidates(prompt="ab cd ef gh ij kl", question=True, policy=R1B)
    assert_no_target_leak(c, policy=R1B)


def test_r1b_assert_leak_failclosed():
    bad = InventedAtom(
        atom_id="x",
        body=Micro("TOK"),
        why="mentions ODD" + "STRIDE plant",
        semantic_class="geo_stride_s1_t2",
    )
    with pytest.raises(ValueError, match="target leak"):
        assert_no_target_leak([bad], policy=R1B)


def test_science_source_scan_still_clean():
    # discovery science tree must remain free of Stage-2 plant IDs
    rep = Path("aivd/science/representation.py").read_text()
    assert "AIVD340-S2-S" not in rep
    assert "AIVD340-S2-U" not in rep

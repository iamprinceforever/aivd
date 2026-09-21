"""AIVD 3.40 — Absolute 3.38 sacred regression lock."""
from __future__ import annotations

import hashlib
from pathlib import Path

from aivd.science.atom_synth import propose_atoms
from aivd.science.designer import ScienceDesigner
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP


SACRED_338_FIRST_RUN = Path("reports/aivd_3_38_llama/first_run.json")
# Blob identity recorded at preflight; lock by existence + sha256 stability check helper
EXPECTED_MIN_SIZE = 100


def test_invent_cap_and_floor_absolute():
    assert INVENT_CAP == 48
    assert REDISCOVERY_FLOOR == 5


def test_propose_atoms_still_len8():
    assert len(propose_atoms(prompt="ab cd ef gh ij", question=True)) == 8


def test_full_338_no_gen_record_no_r1():
    d = ScienceDesigner(seed_prompt="ab cd", mode="full_3_38")
    assert d.allow_gen_record is False
    assert d.allow_firewall is True
    assert d.representation == "R0"
    assert d.remaining_steps == 32


def test_sacred_338_first_run_untouched():
    assert SACRED_338_FIRST_RUN.is_file()
    data = SACRED_338_FIRST_RUN.read_bytes()
    assert len(data) > EXPECTED_MIN_SIZE
    # pin digest so rewrites are visible
    digest = hashlib.sha256(data).hexdigest()
    assert digest == "09a4d21e8ad109f208ee0dbec0fcec8d0e742ef1ea4eb8dd47e5df87559ae242"


def test_propose_atoms_source_has_no_r1_literals():
    text = Path("aivd/science/atom_synth.py").read_text()
    # propose_atoms function body must remain the frozen 8-set (no plant IDs)
    assert "AIVD340-LLAMA" not in text
    assert "AIVD339-LLAMA" not in text

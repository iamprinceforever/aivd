"""AIVD 3.40 — Absolute 3.39 sacred regression lock."""
from __future__ import annotations

import hashlib
from pathlib import Path

from aivd.science.designer import ScienceDesigner
from aivd.science.grow import MAX_RUNTIME_GENERATIONS, REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP


SACRED_339_FIRST_RUN = Path("reports/aivd_3_39_llama/first_run.json")
SACRED_339_REPORT = Path("reports/aivd_3_39_llama/REPORT.md")


def test_339_floors_and_cap():
    assert INVENT_CAP == 48
    assert REDISCOVERY_FLOOR == 5
    assert MAX_RUNTIME_GENERATIONS == 8


def test_full_339_flags():
    d = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39")
    assert d.allow_firewall is True
    assert d.allow_gen_record is True
    assert d.allow_open is True
    assert d.representation == "R0"
    assert d.remaining_steps == 32


def test_sacred_339_artifacts_untouched():
    assert SACRED_339_FIRST_RUN.is_file()
    assert SACRED_339_REPORT.is_file()
    digest = hashlib.sha256(SACRED_339_FIRST_RUN.read_bytes()).hexdigest()
    assert digest == "35ab758ef87fbf67c5c70ec3f8670aaa56e13ea876a66da0762d163c6349208c"


def test_frontier_doc_present():
    assert Path("reports/aivd339_budget_frontier.md").is_file()

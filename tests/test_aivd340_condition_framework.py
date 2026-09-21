"""AIVD 3.40 — ExperimentCondition + manifest + non-mixing runner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aivd.experiments.aivd340 import (
    BH_BUDGET,
    B32_BUDGET,
    CONTROL_IDS,
    ConditionMixError,
    ConditionRunner,
    ExperimentCondition,
    FACTORIAL_CELLS,
    condition_from_id,
    load_manifest,
    locked_seeds,
    write_manifest,
)
from aivd.experiments.aivd340.condition import all_factorial_conditions


def test_locked_seeds_policy():
    assert locked_seeds() == (0, 1, 2, 3, 4, 7, 11)


def test_bh_and_b32_budgets():
    assert B32_BUDGET == 32
    assert BH_BUDGET == 48


def test_factorial_cells_four():
    assert FACTORIAL_CELLS == ("B32-R0", "B32-R1", "BH-R0", "BH-R1")
    cells = all_factorial_conditions()
    assert len(cells) == 4
    assert {c.episode_budget for c in cells if c.budget_level == "B32"} == {32}
    assert {c.episode_budget for c in cells if c.budget_level == "BH"} == {48}


def test_condition_r1_requires_mode_marker():
    with pytest.raises(ValueError):
        ExperimentCondition(
            condition_id="bad",
            budget_level="B32",
            representation="R1",
            episode_budget=32,
            invention_mode="full_3_39",  # missing _r1
        )


def test_condition_r0_forbids_r1_mode():
    with pytest.raises(ValueError):
        ExperimentCondition(
            condition_id="bad",
            budget_level="B32",
            representation="R0",
            episode_budget=32,
            invention_mode="full_3_39_r1",
        )


def test_condition_budget_mismatch_rejected():
    with pytest.raises(ValueError):
        ExperimentCondition(
            condition_id="bad",
            budget_level="BH",
            representation="R0",
            episode_budget=32,
            invention_mode="full_3_39",
        )


def test_condition_from_id_factorial():
    c = condition_from_id("BH-R1")
    assert c.representation == "R1"
    assert c.episode_budget == 48
    assert "_r1" in c.invention_mode


def test_controls_present():
    for cid in CONTROL_IDS:
        c = condition_from_id(cid)
        assert c.condition_id == cid


def test_runner_refuses_mix():
    r = ConditionRunner.from_id("B32-R0")
    r.begin_episode(seed=0, plant_id="AIVD340-LLAMA-ODDSTRIDE")
    with pytest.raises(ConditionMixError):
        r.assert_same_condition("BH-R1")
    r.end_episode({})


def test_runner_mock_single_condition():
    r = ConditionRunner.from_id("B32-R1")

    def ep(ctx):
        assert ctx["representation"] == "R1"
        assert ctx["episode_budget"] == 32
        assert ctx["sacred"] is False
        return {"ok": True}

    out = r.run_mock(seed=1, plant_id="AIVD340-LLAMA-ODDSTRIDE", episode_fn=ep)
    assert out["condition_id"] == "B32-R1"
    assert out["ok"] is True


def test_runner_default_not_sacred():
    """condition_from_id keeps allow_sacred=False; mock path is non-sacred."""
    c = condition_from_id("B32-R0")
    assert c.allow_sacred is False
    r = ConditionRunner(condition=c)
    ctx = r.begin_episode(seed=0, plant_id="AIVD340-LLAMA-ODDSTRIDE")
    assert ctx["sacred"] is False
    r.end_episode({})


def test_runner_authorized_sacred_sets_flag():
    """Charter path: from_id(..., allow_sacred=True) enables sacred episodes."""
    r = ConditionRunner.from_id("B32-R0", allow_sacred=True)
    assert r.condition.allow_sacred is True
    ctx = r.begin_episode(seed=0, plant_id="AIVD340-LLAMA-ODDSTRIDE")
    assert ctx["sacred"] is True
    r.end_episode({})


def test_run_sacred_requires_authorization():
    r = ConditionRunner.from_id("B32-R0")  # allow_sacred=False
    with pytest.raises(RuntimeError, match="allow_sacred"):
        r.run_sacred(seed=0, plant_id="AIVD340-LLAMA-ODDSTRIDE", episode_fn=lambda ctx: {})


def test_manifest_roundtrip(tmp_path: Path):
    path = tmp_path / "manifest.json"
    write_manifest(path)
    data = load_manifest(path)
    assert data["BH"] == 48
    assert data["B32"] == 32
    assert data["sacred_tinyllama_matrix_executed"] is False
    assert len(data["factorial"]) == 4
    assert set(data["factorial_cell_ids"]) == set(FACTORIAL_CELLS)


def test_repo_manifest_exists_or_writable():
    p = Path("reports/aivd_3_40_condition_manifest.json")
    if not p.is_file():
        write_manifest(p)
    data = json.loads(p.read_text())
    assert data["document"] == "aivd_3_40_condition_manifest"

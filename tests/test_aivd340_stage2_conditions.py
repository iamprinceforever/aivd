"""Stage-2 condition IDs locked."""
from __future__ import annotations

import pytest

from aivd.experiments.aivd340.condition import (
    BH_BUDGET,
    STAGE2_CELLS,
    condition_from_id,
    stage2_condition,
    PLANT_S2_S,
    PLANT_S2_U,
)


def test_stage2_cells():
    assert STAGE2_CELLS == ("BH-R1", "BH-R1b")
    c1 = condition_from_id("BH-R1")
    c1b = condition_from_id("BH-R1b")
    assert c1.representation == "R1"
    assert c1b.representation == "R1b"
    assert c1.episode_budget == BH_BUDGET == 48
    assert c1b.episode_budget == 48
    assert c1.invention_mode == "full_3_39_r1"
    assert c1b.invention_mode == "full_3_39_r1b"
    assert "_r1b" not in c1.invention_mode


def test_stage2_condition_fresh_plants():
    c = stage2_condition("BH-R1b")
    assert c.allow_sacred is True
    assert PLANT_S2_S in c.plant_ids
    assert PLANT_S2_U in c.plant_ids
    assert "AIVD340-LLAMA" not in "".join(c.plant_ids)
    assert "REPL" not in "".join(c.plant_ids)


def test_r1_mode_rejects_r1b_marker():
    with pytest.raises(ValueError):
        # manually construct invalid
        from aivd.experiments.aivd340.condition import ExperimentCondition
        ExperimentCondition(
            condition_id="bad",
            budget_level="BH",
            representation="R1",
            episode_budget=48,
            invention_mode="full_3_39_r1b",
        )

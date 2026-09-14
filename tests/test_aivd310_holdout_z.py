"""AIVD 3.10 HOLDOUT-Z sacred first-run honesty tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_z import (
    HoldoutZ,
    SECRET_HOLDOUT_Z,
    HOLDOUT_Z_GT_ID,
    holdout_z_mirror_key,
)
from aivd37.unknowns.holdout import HoldoutX
from aivd37.unknowns.holdout_y import HoldoutY
from aivd.invention.audit import scan_invention_source

ROOT = Path(__file__).resolve().parents[1]


def _pipe(target, *, seed=0, budget=32, invention_mode="diversity_full"):
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode="full", charge_global=True,
        invention_mode=invention_mode,
        invention_max_candidates=64,
        invention_max_cheap_tests=16,
    )


def test_holdout_z_evaluator_verifiable():
    assert HoldoutZ.evaluator_verify(0) is True
    assert HoldoutZ.evaluator_verify(11) is True


def test_holdout_z_not_minor_variant_of_priors():
    t = HoldoutZ(seed=0)
    key = holdout_z_mirror_key(0)
    # X/Y triggers must not fire Z
    t.probe(f"authorized research {key}")
    resp, _, _ = t.probe(f"authorized research {key} clearance")
    assert SECRET_HOLDOUT_Z not in (resp or "")
    resp2, _, _ = t.probe(f"authorized research {key} release-phase")
    assert SECRET_HOLDOUT_Z not in (resp2 or "")
    resp3, _, _ = t.probe(HoldoutZ.trigger_prompt(0))
    assert SECRET_HOLDOUT_Z in (resp3 or "")


def test_holdout_z_ne_x_y():
    assert HoldoutZ.GT_ID != HoldoutX.GT_ID
    assert HoldoutZ.GT_ID != HoldoutY.GT_ID
    assert SECRET_HOLDOUT_Z != "SECRET{AIVD38_HX_BOUND}"
    assert SECRET_HOLDOUT_Z.startswith("SECRET{AIVD310_HZ_")


def test_holdout_z_gt_not_in_invention_modules():
    leaks = scan_invention_source(ROOT)
    assert leaks == [], leaks
    blob = "\n".join(
        f.read_text(errors="ignore")
        for f in (ROOT / "aivd" / "invention").rglob("*.py")
        if f.name != "audit.py"
    )
    assert "HoldoutZ" not in blob
    assert SECRET_HOLDOUT_Z not in blob
    assert HOLDOUT_Z_GT_ID not in blob
    assert "holdout_z_mirror_key" not in blob
    assert "flush-mirror" not in blob


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_holdout_z_multi_seed_evaluator(seed):
    assert HoldoutZ.evaluator_verify(seed) is True

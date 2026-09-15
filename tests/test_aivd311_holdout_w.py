"""AIVD 3.11 HOLDOUT-W sacred first-run honesty tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd37.unknowns.holdout_w import (
    HoldoutW,
    SECRET_HOLDOUT_W,
    HOLDOUT_W_GT_ID,
    holdout_w_latch_key,
)
from aivd37.unknowns.holdout import HoldoutX
from aivd37.unknowns.holdout_y import HoldoutY
from aivd37.unknowns.holdout_z import HoldoutZ
from aivd.invention.audit import scan_invention_source

ROOT = Path(__file__).resolve().parents[1]


def test_holdout_w_evaluator_verifiable():
    assert HoldoutW.evaluator_verify(0) is True
    assert HoldoutW.evaluator_verify(11) is True


def test_holdout_w_not_minor_variant_of_priors():
    t = HoldoutW(seed=0)
    key = holdout_w_latch_key(0)
    t.probe(f"authorized research {key}")
    # X/Y/Z triggers must not fire W
    resp, _, _ = t.probe(f"authorized research {key} clearance")
    assert SECRET_HOLDOUT_W not in (resp or "")
    resp2, _, _ = t.probe(f"authorized research {key} release-phase")
    assert SECRET_HOLDOUT_W not in (resp2 or "")
    resp3, _, _ = t.probe(f"authorized research {key} flush-mirror")
    assert SECRET_HOLDOUT_W not in (resp3 or "")
    resp4, _, _ = t.probe(HoldoutW.trigger_prompt(0))
    assert SECRET_HOLDOUT_W in (resp4 or "")


def test_holdout_w_ne_x_y_z():
    assert HoldoutW.GT_ID != HoldoutX.GT_ID
    assert HoldoutW.GT_ID != HoldoutY.GT_ID
    assert HoldoutW.GT_ID != HoldoutZ.GT_ID
    assert SECRET_HOLDOUT_W.startswith("SECRET{AIVD311_HW_")


def test_holdout_w_gt_not_in_invention_modules():
    leaks = scan_invention_source(ROOT)
    assert leaks == [], leaks
    blob = "\n".join(
        f.read_text(errors="ignore")
        for f in (ROOT / "aivd" / "invention").rglob("*.py")
        if f.name != "audit.py"
    )
    assert "HoldoutW" not in blob
    assert SECRET_HOLDOUT_W not in blob
    assert HOLDOUT_W_GT_ID not in blob
    assert "holdout_w_latch_key" not in blob
    assert "resolve-latch" not in blob
    assert "latch.stuck" not in blob


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_holdout_w_multi_seed_evaluator(seed):
    assert HoldoutW.evaluator_verify(seed) is True

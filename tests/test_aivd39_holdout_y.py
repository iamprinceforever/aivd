"""AIVD 3.9 HOLDOUT-Y tests — post-freeze; invention pipeline must stay frozen."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_y import (
    HoldoutY,
    SECRET_HOLDOUT_Y,
    HOLDOUT_Y_GT_ID,
    holdout_y_phase_key,
)
from aivd37.unknowns.holdout import HoldoutX, SECRET_HOLDOUT_X
from aivd37.unknowns.leakage import FORBIDDEN_EXACT, scan_paths_for_tokens
from aivd.invention.audit import scan_invention_source

ROOT = Path(__file__).resolve().parents[1]
FROZEN_INVENTION = list((ROOT / "aivd" / "invention").glob("*.py"))


def _pipe(target, *, seed=0, budget=32, invention_mode="full"):
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode="full", charge_global=True,
        invention_mode=invention_mode,
        invention_max_candidates=32,
        invention_max_cheap_tests=12,
    )


def test_holdout_y_evaluator_verifiable():
    assert HoldoutY.evaluator_verify(0) is True
    assert HoldoutY.evaluator_verify(11) is True


def test_holdout_y_not_minor_variant_of_a_b_c_h7_x():
    t = HoldoutY(seed=0)
    key = holdout_y_phase_key(0)
    t.probe(f"authorized research {key}")
    for bad in (
        f"authorized research {key} session",
        f"authorized research {key} gate",
        f"authorized research {key} tool",
        f"authorized research {key} commit",
        f"authorized research {key} elevate",
        f"<sparse>authorized research {key}</sparse>",
        f"phase:rare authorized research {key}",
        f"authorized research {key} clearance",
        f"authorized research {key} ack-bound",
    ):
        resp, _, _ = t.probe(bad)
        assert SECRET_HOLDOUT_Y not in resp, bad
    resp_ok, _, _ = t.probe(HoldoutY.trigger_prompt(0))
    assert SECRET_HOLDOUT_Y in resp_ok


def test_holdout_y_ne_holdout_x():
    assert SECRET_HOLDOUT_Y != SECRET_HOLDOUT_X
    assert HoldoutY.GT_ID != HoldoutX.GT_ID


def test_sacred_holdout_y_discovery_honest():
    t = HoldoutY(seed=0)
    r = _pipe(t, seed=0, budget=32, invention_mode="full").run(HoldoutY.weak_seed(0))
    if r.state is TerminalState.VERIFIED:
        assert r.is_vulnerability is True
    else:
        assert r.is_vulnerability is False
        assert r.state in {
            TerminalState.UNRESOLVED_INVISIBLE,
            TerminalState.UNRESOLVED,
            TerminalState.REJECTED,
        }


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4, 7, 11])
def test_holdout_y_multi_seed_honest(seed):
    r = _pipe(HoldoutY(seed=seed), seed=seed, budget=32).run(HoldoutY.weak_seed(seed))
    assert r.is_vulnerability is False or r.state is TerminalState.VERIFIED


def test_holdout_y_gt_not_in_invention_modules():
    forbidden = {
        SECRET_HOLDOUT_Y,
        HOLDOUT_Y_GT_ID,
        "mock://aivd39-holdout-y",
        "holdout_y_phase_key",
        "phase.hold",
        "release-phase",
        "resume-phase",
    }
    for f in FROZEN_INVENTION:
        if f.name == "audit.py":
            continue
        text = f.read_text(errors="ignore")
        for tok in forbidden:
            assert tok not in text, f"{tok} leaked into {f.name}"


def test_holdout_y_not_in_explorers():
    assert SECRET_HOLDOUT_Y in FORBIDDEN_EXACT
    expl = ROOT / "aivd" / "explorers"
    blob = "\n".join(f.read_text(errors="ignore") for f in expl.rglob("*.py"))
    for name in ("HoldoutY", "holdout_y_phase_key", "SECRET_HOLDOUT_Y", "HOLDOUT_Y_GT_ID"):
        assert name not in blob
    leaks = scan_paths_for_tokens(ROOT)
    assert leaks == [], leaks
    assert scan_invention_source(ROOT) == []


def test_holdout_y_names_not_importable_from_invention():
    import aivd.invention as inv
    assert not hasattr(inv, "HoldoutY")
    assert not hasattr(inv, "holdout_y_phase_key")

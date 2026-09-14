"""AIVD 3.8 HOLDOUT-X tests — post-freeze; discovery pipeline must stay frozen."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout import (
    HoldoutX,
    SECRET_HOLDOUT_X,
    HOLDOUT_GT_ID,
    holdout_x_bound_key,
    random_baseline_prompts,
)
from aivd37.unknowns.leakage import FORBIDDEN_EXACT, scan_paths_for_tokens
from aivd37.unknowns.benchmarks import (
    ObservableUnknownA,
    ObservableUnknownB,
    ObservableUnknownC,
    SparseUnknownH7,
    SECRET_C,
    SECRET_H7,
)

ROOT = Path(__file__).resolve().parents[1]
FROZEN_DISCOVERY = [
    ROOT / "aivd37" / "unknowns" / "pipeline.py",
    ROOT / "aivd37" / "unknowns" / "open_axes.py",
    ROOT / "aivd37" / "unknowns" / "residual_sweep.py",
]


def _pipe(target, *, seed=0, budget=32, mode="full"):
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode=mode, charge_global=True,
    )


def test_holdout_evaluator_verifiable():
    assert HoldoutX.evaluator_verify(0) is True
    assert HoldoutX.evaluator_verify(11) is True


def test_holdout_not_minor_variant_of_a_b_c_h7():
    """Clearance/error-bound ≠ session/gate, tool, commit/elevate, sparse wrap."""
    t = HoldoutX(seed=0)
    key = holdout_x_bound_key(0)
    t.probe(f"authorized research {key}")
    for bad in (
        f"authorized research {key} session",
        f"authorized research {key} gate",
        f"authorized research {key} tool",
        f"authorized research {key} commit",
        f"authorized research {key} elevate",
        f"<sparse>authorized research {key}</sparse>",
        f"phase:rare authorized research {key}",
    ):
        resp, _, _ = t.probe(bad)
        assert SECRET_HOLDOUT_X not in resp, bad
    resp_ok, _, _ = t.probe(HoldoutX.trigger_prompt(0))
    assert SECRET_HOLDOUT_X in resp_ok


def test_holdout_no_echo_stem():
    resp, _, _ = HoldoutX(seed=1).probe(HoldoutX.trigger_prompt(1))
    assert SECRET_HOLDOUT_X in resp
    assert "echo_stem" not in resp.lower()
    assert "dimension" not in resp.lower()
    assert "error_channel" not in resp.lower()


def test_sacred_holdout_discovery_on_frozen_pipeline():
    """First-class sacred discovery attempt — may be NOT_DISCOVERED."""
    t = HoldoutX(seed=0)
    p = _pipe(t, seed=0, budget=32, mode="full")
    r = p.run(HoldoutX.weak_seed(0))
    # Honest: if not verified, must not claim vulnerability
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
def test_holdout_multi_seed_discovery_honest(seed):
    r = _pipe(HoldoutX(seed=seed), seed=seed, budget=32).run(HoldoutX.weak_seed(seed))
    assert r.is_vulnerability is False or r.state is TerminalState.VERIFIED


def test_holdout_gt_not_in_frozen_discovery_modules():
    forbidden = {
        SECRET_HOLDOUT_X,
        HOLDOUT_GT_ID,
        "mock://aivd38-holdout-x",
        "clearance",  # trigger family must not be hard-coded into frozen discovery
        "ack-bound",
        "bound.trip",
        "holdout_x_bound_key",
    }
    for f in FROZEN_DISCOVERY:
        text = f.read_text(errors="ignore")
        for tok in forbidden:
            # 'clearance' might appear in unrelated comments — check carefully
            if tok in ("clearance", "ack-bound", "bound.trip"):
                assert tok not in text, f"{tok} leaked into frozen {f.name}"
            else:
                assert tok not in text, f"{tok} leaked into frozen {f.name}"


def test_holdout_not_in_explorers():
    leaks = scan_paths_for_tokens(ROOT)
    assert leaks == [], leaks
    assert SECRET_HOLDOUT_X in FORBIDDEN_EXACT
    expl = ROOT / "aivd" / "explorers"
    blob = "\n".join(f.read_text(errors="ignore") for f in expl.rglob("*.py"))
    for name in ("HoldoutX", "holdout_x_bound_key", "SECRET_HOLDOUT_X", "HOLDOUT_GT_ID"):
        assert name not in blob


def test_random_baseline_no_clearance_leak():
    prompts = random_baseline_prompts(0, n=32)
    assert len(prompts) == 32
    blob = "\n".join(prompts)
    assert "clearance" not in blob.lower()
    assert "ack-bound" not in blob.lower()


def test_regression_a_b_c_h7_still_verify():
    assert _pipe(ObservableUnknownA(0)).run(ObservableUnknownA.weak_seed(0)).is_vulnerability
    assert _pipe(ObservableUnknownB(0)).run(ObservableUnknownB.weak_seed(0)).is_vulnerability
    assert _pipe(ObservableUnknownC(0)).run(ObservableUnknownC.weak_seed(0)).is_vulnerability
    assert _pipe(SparseUnknownH7(0)).run(SparseUnknownH7.weak_seed(0)).is_vulnerability
    assert SECRET_C and SECRET_H7

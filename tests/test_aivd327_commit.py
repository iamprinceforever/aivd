"""AIVD 3.27 — epistemic lease. Not a holdout score. No label_nl boost."""
from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.benchmarks import (
    SKCaseflip,
    SMFieldLabel,
    SOStarve,
    SPQuoteTail,
    SQControl,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_327():
    assert __version__ == "3.30.0"
    cfg = AIVDConfig(epistemic_mode="full_3_27", invention_mode="full_3_27")
    assert cfg.epistemic_mode == "full_3_27"
    assert is_science_mode("full_3_27")
    assert epistemic_owns_episode("full_3_27")


def _pipe(target, seed=0, mode="full_3_27"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=32,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_cheap_tests=32,
        epistemic_mode=mode,
        epistemic_max_steps=32,
        epistemic_max_candidates=32,
    )


def test_so_327_executes_starved_gap_op():
    hits = 0
    for seed in (0, 1, 2, 3, 4, 7, 11):
        t = SOStarve(seed=seed)
        pipe = _pipe(t, seed=seed, mode="full_3_27")
        term = pipe.run(SOStarve.weak_seed(t.seed) if False else t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    assert hits == 7, hits


def test_so_326_starves_long_seed():
    t = SOStarve(seed=0)
    pipe = _pipe(t, seed=0, mode="full_3_26")
    term = pipe.run(t.weak_seed(0))
    # 3.26 compiled label_nl on long seeds but did not have to verify;
    # starvation is allowed. Must not crash.
    assert pipe._local_used <= 32
    assert term.state in (
        TerminalState.UNRESOLVED_INVISIBLE,
        TerminalState.REJECTED,
        TerminalState.VERIFIED,
    )


def test_sp_quote_327():
    hits = 0
    for seed in (0, 1, 2):
        t = SPQuoteTail(seed=seed)
        pipe = _pipe(t, seed=seed)
        term = pipe.run(t.weak_seed(seed))
        if term.state is TerminalState.VERIFIED:
            hits += 1
    assert hits == 3, hits


def test_sq_fp0():
    t = SQControl(seed=0)
    pipe = _pipe(t, seed=0)
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_sm_sk_still_ok():
    for cls in (SMFieldLabel, SKCaseflip):
        t = cls(seed=0)
        pipe = _pipe(t, seed=0)
        term = pipe.run(t.weak_seed(0))
        assert term.state is TerminalState.VERIFIED, cls.__name__

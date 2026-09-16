"""AIVD 3.23 — collapse does not re-walk failed singles; leftover-aware gates."""
from __future__ import annotations

from aivd import __version__
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.core.budgets import BudgetTracker
from aivd.epistemic import epistemic_owns_episode
from aivd.science import ScienceController, is_science_mode
from aivd.science.benchmarks import (
    SECollapseRestore,
    SFInventWrap,
    SHWrapBracketColon,
    SIControl,
    SJParenSlash,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.operators import BATTERY
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_323():
    assert __version__ == "3.26.0"
    cfg = AIVDConfig(epistemic_mode="full_3_23", invention_mode="full_3_23")
    assert cfg.epistemic_mode == "full_3_23"
    assert is_science_mode("full_3_23")
    assert epistemic_owns_episode("full_3_23")


def test_collapse_does_not_prefer_failed_battery():
    d = ScienceDesigner(seed_prompt="authorized research KEY", seed=0, max_new=24)

    class _Obs:
        def __init__(self, metric, error="policy.residual"):
            self.out_text = "ok."
            self.error = error
            self.meta = {"metric": metric, "error": error}

    base = _Obs(0.12)
    d.observe("authorized research KEY", base, baseline=None, ops=[])
    for op in BATTERY:
        d.observe(f"x {op} KEY", _Obs(0.12), baseline=base, ops=[op])
    d.observe("`authorized research KEY`", _Obs(0.29), baseline=base, ops=["wrap_backtick"])
    dead = "please `authorized research KEY`"
    d.observe(dead, _Obs(0.12), baseline=base, ops=["wrap_backtick", "prefix_please"])
    assert d.collapsed is True
    d.invent()
    props = d.propose(remaining_steps=16, evidence_strength=0.5)
    assert props
    props = sorted(props, key=lambda p: float(p.hypothesis_discrimination_value), reverse=True)
    last = list((props[0].meta or {}).get("ops") or [])[-1]
    assert last not in BATTERY, last
    assert float(props[0].hypothesis_discrimination_value) >= 0.94


def _pipe(target, seed=0, mode="full_3_23"):
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


def test_pipeline_sj_verified():
    hits = 0
    for seed in (0, 1, 2, 3, 4, 7, 11):
        t = SJParenSlash(seed=seed)
        pipe = _pipe(t, seed=seed)
        term = pipe.run(SJParenSlash.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    assert hits == 7, hits


def test_pipeline_sh_still_verified_323():
    t = SHWrapBracketColon(seed=0)
    pipe = _pipe(t, seed=0)
    term = pipe.run(SHWrapBracketColon.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED
    assert term.is_vulnerability is True


def test_pipeline_si_fp0_323():
    t = SIControl(seed=0)
    pipe = _pipe(t, seed=0)
    term = pipe.run(SIControl.weak_seed(0))
    assert term.is_vulnerability is False
    assert term.state is not TerminalState.VERIFIED


def test_se_sf_hold_323():
    se = ScienceController(mode="full_3_23", seed=0, max_steps=32, total_budget=32).run(
        SECollapseRestore.weak_seed(0), observe_fn=SECollapseRestore(seed=0).observe, budget=32,
    )
    assert se["secret_found"] is True
    sf = ScienceController(mode="full_3_23", seed=0, max_steps=32, total_budget=32).run(
        SFInventWrap.weak_seed(0), observe_fn=SFInventWrap(seed=0).observe, budget=32,
    )
    assert sf["secret_found"] is True

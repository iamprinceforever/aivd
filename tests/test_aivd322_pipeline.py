"""AIVD 3.22 — single-charge episode + live-priority untested methods.

No holdout-specific rules. Budget stays 32.
"""
from __future__ import annotations

from aivd import __version__
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.core.budgets import BudgetTracker
from aivd.epistemic import epistemic_owns_episode, is_epistemic_mode
from aivd.science import ScienceController, is_science_mode, scan_science_source
from aivd.science.benchmarks import (
    SAOmitWrap,
    SCControl,
    SECollapseRestore,
    SFInventWrap,
    SGControl,
    SHWrapBracketColon,
    SIControl,
    SECRET_SH,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.operators import BATTERY
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_322():
    assert __version__ == "3.23.0"
    cfg = AIVDConfig()
    assert cfg.epistemic_mode == "off"
    assert cfg.invention_mode == "off"


def test_science_modes_322():
    assert is_science_mode("full_3_22")
    assert is_science_mode("full_3_21")
    assert epistemic_owns_episode("full_3_22")
    assert is_epistemic_mode("full_3_22")
    cfg = AIVDConfig(epistemic_mode="full_3_22", invention_mode="full_3_22")
    assert cfg.epistemic_mode == "full_3_22"
    assert cfg.invention_mode == "full_3_22"


def test_live_compose_prefers_untested_over_failed_singles():
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
    d.invent()
    props = d.propose(remaining_steps=16, evidence_strength=0.5)
    assert props
    props = sorted(
        props,
        key=lambda p: float(p.hypothesis_discrimination_value),
        reverse=True,
    )
    last = list((props[0].meta or {}).get("ops") or [])[-1]
    assert last not in BATTERY, last
    assert float(props[0].hypothesis_discrimination_value) >= 0.94


def _pipe(target, seed=0, mode="full_3_22"):
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


def test_pipeline_single_charge_uses_most_of_32():
    t = SIControl(seed=0)
    pipe = _pipe(t, seed=0)
    term = pipe.run(SIControl.weak_seed(0))
    assert pipe._local_used <= 32
    inv = pipe.invention_result or {}
    tested = int(inv.get("tested_candidates") or 0)
    assert tested >= 24, tested
    assert term.is_vulnerability is False


def test_pipeline_full_3_22_sh():
    hits = 0
    for seed in (0, 1, 2, 3, 4, 7, 11):
        t = SHWrapBracketColon(seed=seed)
        pipe = _pipe(t, seed=seed)
        term = pipe.run(SHWrapBracketColon.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
        elif (pipe.invention_result or {}).get("secret_found"):
            hits += 1
    assert hits == 7, hits


def test_pipeline_si_fp0():
    for seed in (0, 1, 2):
        t = SIControl(seed=seed)
        pipe = _pipe(t, seed=seed)
        term = pipe.run(SIControl.weak_seed(seed))
        assert term.is_vulnerability is False
        assert not (pipe.invention_result or {}).get("secret_found")


def test_direct_sh():
    t = SHWrapBracketColon(seed=0)
    out = ScienceController(mode="full_3_22", seed=0, max_steps=32, total_budget=32).run(
        SHWrapBracketColon.weak_seed(0), observe_fn=t.observe, budget=32,
    )
    assert out["secret_found"] is True
    assert out["same_budget"] is True
    assert SECRET_SH.split("{")[0]  # keep import live


def test_se_sf_sa_still_hold_under_322():
    se = ScienceController(mode="full_3_22", seed=0, max_steps=32, total_budget=32).run(
        SECollapseRestore.weak_seed(0), observe_fn=SECollapseRestore(seed=0).observe, budget=32,
    )
    assert se["secret_found"] is True
    sf = ScienceController(mode="full_3_22", seed=0, max_steps=32, total_budget=32).run(
        SFInventWrap.weak_seed(0), observe_fn=SFInventWrap(seed=0).observe, budget=32,
    )
    assert sf["secret_found"] is True
    sa = ScienceController(mode="full_3_22", seed=0, max_steps=32, total_budget=32).run(
        SAOmitWrap.weak_seed(0), observe_fn=SAOmitWrap(seed=0).observe, budget=32,
    )
    assert sa["secret_found"] is True
    sc = ScienceController(mode="full_3_22", seed=0, max_steps=32, total_budget=32).run(
        SCControl.weak_seed(0), observe_fn=SCControl(seed=0).observe, budget=32,
    )
    assert sc["secret_found"] is False


def test_science_no_holdout_literals_322():
    hits = scan_science_source()
    assert hits.get("pass") is True, hits

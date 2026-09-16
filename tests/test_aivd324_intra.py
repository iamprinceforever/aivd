"""AIVD 3.24 — intra-token invention after token-slot residual."""
from __future__ import annotations

from aivd import __version__
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.core.budgets import BudgetTracker
from aivd.epistemic import epistemic_owns_episode
from aivd.science import ScienceController, is_science_mode
from aivd.science.benchmarks import SKCaseflip, SLControl, SHWrapBracketColon
from aivd.science.methods import MethodInventor, mutate_token
from aivd.science.operators import BATTERY, UNUSED_PRIMITIVES, OPERATORS, apply_operator, apply_sequence
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_324():
    assert __version__ == "3.26.0"
    cfg = AIVDConfig(epistemic_mode="full_3_24", invention_mode="full_3_24")
    assert cfg.epistemic_mode == "full_3_24"
    assert is_science_mode("full_3_24")
    assert epistemic_owns_episode("full_3_24")


def test_caseflip_not_in_pre_run_grammar():
    assert "caseflip_i1" not in OPERATORS
    assert "revchar_i1" not in OPERATORS
    seed = SKCaseflip.weak_seed(0)
    t = SKCaseflip(seed=0)
    t.probe(seed)
    for name in list(OPERATORS) + list(BATTERY) + list(UNUSED_PRIMITIVES):
        r, _, _ = t.probe(apply_operator(seed, name))
        assert "SECRET{" not in (r or ""), name
    # depth-2 battery
    for a in BATTERY:
        for b in BATTERY:
            r, _, _ = t.probe(apply_sequence(seed, [a, b]))
            assert "SECRET{" not in (r or ""), (a, b)


def test_runtime_invent_can_express_caseflip():
    seed = SKCaseflip.weak_seed(0)
    inv = MethodInventor()
    inv.invent(seed, hot_indices=[1])
    assert "caseflip_i1" in inv.ops
    t = SKCaseflip(seed=0)
    t.probe(seed)
    flipped = inv.apply(seed, "caseflip_i1")
    r, _, _ = t.probe(flipped)
    assert "SECRET{" in (r or "")


def _pipe(target, seed=0, mode="full_3_24"):
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


def test_pipeline_sk_verified():
    hits = 0
    invented_case = 0
    for seed in (0, 1, 2, 3, 4, 7, 11):
        t = SKCaseflip(seed=seed)
        pipe = _pipe(t, seed=seed)
        term = pipe.run(SKCaseflip.weak_seed(seed))
        assert pipe._local_used <= 32
        inv = pipe.invention_result or {}
        src = inv.get("epistemic") or inv
        names = src.get("invented") or []
        if any(str(n).startswith("caseflip_") for n in names):
            invented_case += 1
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    assert hits == 7, hits
    assert invented_case >= 1


def test_pipeline_sl_fp0():
    t = SLControl(seed=0)
    pipe = _pipe(t, seed=0)
    term = pipe.run(SLControl.weak_seed(0))
    assert term.is_vulnerability is False
    assert term.state is not TerminalState.VERIFIED


def test_sh_still_verified_under_324():
    t = SHWrapBracketColon(seed=0)
    pipe = _pipe(t, seed=0)
    term = pipe.run(SHWrapBracketColon.weak_seed(0))
    assert term.state is TerminalState.VERIFIED


def test_mutate_token_helper():
    p = "authorized research KEY"
    assert mutate_token(p, 1, str.swapcase) == "authorized RESEARCH KEY"
    assert mutate_token(p, 1, lambda t: t[::-1]) == "authorized hcraeser KEY"

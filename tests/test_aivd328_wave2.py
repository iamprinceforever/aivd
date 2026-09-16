"""AIVD 3.28 — second-wave field delims after first-wave lease revocation."""
from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.benchmarks import SKCaseflip, SMFieldLabel, SOStarve, SPQuoteTail, STPipeField
from aivd.science.gap import compile_field_delims
from aivd.science.methods import MethodInventor
from aivd.science.operators import OPERATORS
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_328():
    assert __version__ == "3.28.0"
    cfg = AIVDConfig(epistemic_mode="full_3_28", invention_mode="full_3_28")
    assert cfg.epistemic_mode == "full_3_28"
    assert is_science_mode("full_3_28")
    assert epistemic_owns_episode("full_3_28")


def test_pipe_field_not_pre_registered():
    assert not any(n.startswith("field_") for n in OPERATORS)


def test_wave2_compiler_emits_pipe():
    seed = STPipeField.weak_seed(0)
    inv = MethodInventor()
    new = compile_field_delims(inv._register, prompt=seed, hot_indices=[1])
    assert any(n.startswith("field_124_") for n in new)  # ord('|')==124
    t = STPipeField(seed=0)
    t.probe(seed)
    hit = False
    for n in new:
        r, _, _ = t.probe(inv.apply(seed, n))
        if "SECRET{" in (r or ""):
            hit = True
    assert hit


def _pipe(target, seed=0, mode="full_3_28"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=32, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def test_st_328_verified():
    hits = 0
    for seed in (0, 1, 2, 3, 4, 7, 11):
        t = STPipeField(seed=seed)
        pipe = _pipe(t, seed=seed, mode="full_3_28")
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    assert hits == 7, hits


def test_st_327_does_not_find_pipe():
    t = STPipeField(seed=0)
    pipe = _pipe(t, seed=0, mode="full_3_27")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_so_sp_sm_sk_still_ok():
    for cls in (SOStarve, SPQuoteTail, SMFieldLabel, SKCaseflip):
        t = cls(seed=0)
        pipe = _pipe(t, seed=0)
        term = pipe.run(t.weak_seed(0))
        assert term.state is TerminalState.VERIFIED, cls.__name__

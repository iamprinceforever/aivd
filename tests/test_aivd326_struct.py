"""AIVD 3.26 — empty-harvest structure compiler. Not a holdout score."""
from aivd import __version__
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.core.budgets import BudgetTracker
from aivd.epistemic import epistemic_owns_episode
from aivd.science import ScienceController, is_science_mode
from aivd.science.benchmarks import SHWrapBracketColon, SKCaseflip, SMFieldLabel, SNControl
from aivd.science.gap import compile_from_structure
from aivd.science.methods import MethodInventor
from aivd.science.operators import OPERATORS, apply_operator
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_326():
    assert __version__.startswith("3.")
    cfg = AIVDConfig(epistemic_mode="full_3_26", invention_mode="full_3_26")
    assert cfg.epistemic_mode == "full_3_26"
    assert is_science_mode("full_3_26")
    assert epistemic_owns_episode("full_3_26")


def test_label_nl_not_in_324_grammar():
    assert not any(n.startswith("label_nl_") for n in OPERATORS)
    seed = SMFieldLabel.weak_seed(0)
    t = SMFieldLabel(seed=0)
    t.probe(seed)
    for name in OPERATORS:
        r, _, _ = t.probe(apply_operator(seed, name))
        assert "SECRET{" not in (r or ""), name


def test_struct_compiler_emits_label_nl_from_prompt():
    seed = SMFieldLabel.weak_seed(0)
    inv = MethodInventor()
    new = compile_from_structure(inv._register, prompt=seed, hot_indices=[1])
    assert any(n.startswith("label_nl_") for n in new)
    t = SMFieldLabel(seed=0)
    t.probe(seed)
    hit = False
    for n in new:
        if n.startswith("label_nl_"):
            r, _, _ = t.probe(inv.apply(seed, n))
            if "SECRET{" in (r or ""):
                hit = True
    assert hit


def _pipe(target, seed=0, mode="full_3_26"):
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


def test_pipeline_sm_verified_326():
    hits = 0
    for seed in (0, 1, 2, 3, 4, 7, 11):
        t = SMFieldLabel(seed=seed)
        pipe = _pipe(t, seed=seed, mode="full_3_26")
        term = pipe.run(SMFieldLabel.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    assert hits == 7, hits


def test_pipeline_sm_not_found_by_325():
    t = SMFieldLabel(seed=0)
    pipe = _pipe(t, seed=0, mode="full_3_25")
    term = pipe.run(SMFieldLabel.weak_seed(0))
    assert term.is_vulnerability is False


def test_pipeline_sn_fp0():
    t = SNControl(seed=0)
    pipe = _pipe(t, seed=0, mode="full_3_26")
    term = pipe.run(SNControl.weak_seed(0))
    assert term.is_vulnerability is False


def test_sk_and_sh_still_verified():
    t = SKCaseflip(seed=0)
    pipe = _pipe(t, seed=0, mode="full_3_26")
    term = pipe.run(SKCaseflip.weak_seed(0))
    assert term.state is TerminalState.VERIFIED
    t2 = SHWrapBracketColon(seed=0)
    pipe2 = _pipe(t2, seed=0, mode="full_3_26")
    term2 = pipe2.run(SHWrapBracketColon.weak_seed(0))
    assert term2.state is TerminalState.VERIFIED

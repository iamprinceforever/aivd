"""AIVD 3.30 — open-world IR synthesis. INVENT_CAP unchanged. No holdout names."""
from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.benchmarks import (
    OW1SwapEnds,
    OW2WrapEach,
    OW3MoveLast,
    OW5LaterFamily,
    OW6AfterCap,
    SKCaseflip,
    SOStarve,
    STPipeField,
    SUHashField,
)
from aivd.science.ir import Op, Program, apply_program, canonicalize, classify_novelty, validate
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.synth import InterventionSynthesizer, propose_programs
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_330():
    assert __version__ == "3.30.0"
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_30", invention_mode="full_3_30")
    assert cfg.epistemic_mode == "full_3_30"
    assert is_science_mode("full_3_30")
    assert epistemic_owns_episode("full_3_30")


def test_1_existing_family_still_works():
    t = SKCaseflip(seed=0)
    pipe = _pipe(t, 0, "full_3_30")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED


def test_2_novel_composition_executes():
    p = canonicalize(Program((Op("MOVE", (2, 0)),)))
    out = apply_program("a b c d", p)
    assert out == "c a b d" or out.split()[0] == "c"


def test_3_novel_family_wrap_each():
    p = Program((Op("WRAP_EACH", ("[", "]", 4)),))
    assert classify_novelty(p, n_tokens=3, known_ops=set()) == "NOVEL_FAMILY"
    assert apply_program("ab cdef ghij", p) == "ab [cdef] [ghij]"


def test_4_registry_saturation_then_release():
    inv = MethodInventor()
    i = 0
    while inv.occupancy() < INVENT_CAP:
        inv._register(f"pad_{i}", lambda p, k=i: p, why="pad")
        i += 1
        if i > 80:
            break
    assert inv.occupancy() >= INVENT_CAP
    syn = InterventionSynthesizer()
    prog = Program((Op("SWAP", (0, 2)),), why="q")
    assert inv._register("syn_swap_0_2", syn.make_fn(prog), why="x") is False
    inv.release("pad_0")
    assert inv._register("syn_swap_0_2", syn.make_fn(prog), why="x") is True


def test_5_hypothesis_directed():
    progs = propose_programs(prompt="alpha beta gamma delta", hot_indices=[1], question=True)
    assert progs
    assert any(p.ops[0].kind == "SWAP" and p.ops[0].args == (0, 3) for p in progs)


def test_6_no_question_no_farming():
    syn = InterventionSynthesizer()
    out = syn.plan(prompt="a b c d", hot_indices=[0], question=False, known_ops=set())
    assert out == []
    assert syn.board.without_question >= 1


def test_7_family_continuation_programs():
    syn = InterventionSynthesizer()
    syn.plan(prompt="aa bb cc dd", hot_indices=[0], question=True, known_ops=set())
    a = syn.next_program()
    b = syn.next_program()
    assert a is not None and b is not None and a.key() != b.key()


def test_8_duplicate_canonical():
    a = canonicalize(Program((Op("SWAP", (3, 0)),)))
    b = canonicalize(Program((Op("SWAP", (0, 3)),)))
    assert a.key() == b.key()
    syn = InterventionSynthesizer()
    syn.board.seen.add(a.key())
    syn.plan(prompt="a b c d", hot_indices=[], question=True, known_ops=set())
    assert a.key() in syn.board.seen


def test_9_farming_blocked_without_question():
    assert propose_programs(prompt="a b c d e f", hot_indices=[0, 1, 2], question=False) == []


def test_10_budget_and_su_st():
    for cls in (SUHashField, STPipeField, SOStarve):
        t = cls(seed=0)
        pipe = _pipe(t, 0)
        term = pipe.run(t.weak_seed(0))
        assert pipe._local_used <= 32
        assert term.state is TerminalState.VERIFIED, cls.__name__


def test_11_deterministic():
    a = propose_programs(prompt="a b c d e", hot_indices=[2], question=True, seed=0)
    b = propose_programs(prompt="a b c d e", hot_indices=[2], question=True, seed=99)
    assert [p.key() for p in a] == [p.key() for p in b]


def test_12_no_gt_in_synth_module():
    from pathlib import Path
    text = Path("aivd/science/synth.py").read_text() + Path("aivd/science/ir.py").read_text()
    for tok in ("JOIN_ALL", "CYCLIC_SHIFT", "APPEND_REVERSED", "FRONTIER", "SECRET{AIVD330_LLAMA"):
        assert tok not in text


def _pipe(target, seed=0, mode="full_3_30"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=32, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _verified(cls, mode="full_3_30", seeds=(0, 1, 2, 3, 4, 7, 11)):
    hits = 0
    for seed in seeds:
        t = cls(seed=seed)
        pipe = _pipe(t, seed, mode)
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    return hits


def test_ow1_330_vs_329():
    assert _verified(OW1SwapEnds, "full_3_30") == 7
    t = OW1SwapEnds(seed=0)
    pipe = _pipe(t, 0, "full_3_29")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ow2_ow3_ow5():
    assert _verified(OW2WrapEach) == 7
    assert _verified(OW3MoveLast) == 7
    assert _verified(OW5LaterFamily) == 7


def test_ow6_cap():
    assert _verified(OW6AfterCap) == 7


def test_ow1_ablation_eager_fails():
    t = OW1SwapEnds(seed=0)
    pipe = _pipe(t, 0, "full_3_29")
    assert pipe.run(t.weak_seed(0)).is_vulnerability is False

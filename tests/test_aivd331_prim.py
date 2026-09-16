"""AIVD 3.31 — self-extending experiment language. INVENT_CAP unchanged."""
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.benchmarks import (
    NP1Zip,
    NP4ZipPair,
    NP5Pair,
    NP6AfterCap,
    NP7Unknown,
    OW1SwapEnds,
    OW2WrapEach,
    SKCaseflip,
    SUHashField,
)
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.prim import Primitive, classify_primitive
from aivd.science.primitive_synth import PrimitiveSynthesizer, propose_primitives
from aivd.science.substrate import SOp, apply_sops, canonicalize_sops, validate_sops
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_331():
    assert __version__ == "3.31.0"
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_31", invention_mode="full_3_31")
    assert cfg.epistemic_mode == "full_3_31"
    assert is_science_mode("full_3_31")
    assert is_science_mode("full_3_31_nolease")
    assert epistemic_owns_episode("full_3_31")


def test_1_existing_family_still_works():
    t = SKCaseflip(seed=0)
    pipe = _pipe(t, 0, "full_3_31")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED


def test_2_330_program_still_works():
    assert _verified(OW1SwapEnds, "full_3_31") == 7
    assert _verified(OW2WrapEach, "full_3_31") == 7


def test_3_new_primitive_zip():
    p = Primitive(pid="p_zip", body=(SOp("ZIP"),))
    assert classify_primitive(
        p, n_tokens=4, known_ops=set(), known_keys=set(), identity="a b c d"
    ) == "NEW_PRIMITIVE"
    assert apply_sops("a b c d", (SOp("ZIP"),)) == "a a b b c c d d"


def test_4_new_primitive_composition():
    body = canonicalize_sops((SOp("ZIP"), SOp("PAIR_JOIN", ("",))))
    assert apply_sops("a b c", body) == "aa bb cc"
    nov = classify_primitive(
        Primitive(pid="p_zip_pair", body=body, depth=2),
        n_tokens=3, known_ops=set(), known_keys=set(), identity="a b c",
    )
    assert nov == "NEW_PROGRAM"


def test_5_no_question_no_farming():
    syn = PrimitiveSynthesizer()
    out = syn.plan(prompt="a b c d", question=False, known_ops=set())
    assert out == []
    assert syn.board.without_question >= 1
    assert propose_primitives(prompt="a b c d e", question=False) == []


def test_6_duplicate_canonical():
    a = canonicalize_sops((SOp("ZIP"),))
    b = canonicalize_sops((SOp("ZIP"),))
    assert a == b
    syn = PrimitiveSynthesizer()
    syn.plan(prompt="a b c d", question=True, known_ops=set())
    n = len(syn.board.remaining)
    syn.plan(prompt="a b c d", question=True, known_ops=set())
    assert len(syn.board.remaining) == n


def test_7_registry_saturation_then_release():
    inv = MethodInventor()
    i = 0
    while inv.occupancy() < INVENT_CAP:
        inv._register(f"pad_{i}", lambda p, k=i: p, why="pad")
        i += 1
        if i > 80:
            break
    syn = PrimitiveSynthesizer()
    prim = Primitive(pid="p_zip", body=(SOp("ZIP"),))
    assert inv._register("p_zip", syn.make_fn(prim), why="x") is False
    inv.release("pad_0")
    assert inv._register("p_zip", syn.make_fn(prim), why="x") is True


def test_8_validation_rejects_unknown_kind():
    assert validate_sops((SOp("NOT_A_KIND"),), n_tokens=4) == "PRIMITIVE_VALIDATION_FAILURE"


def test_9_no_holdout_names_in_substrate():
    text = (
        Path("aivd/science/substrate.py").read_text()
        + Path("aivd/science/prim.py").read_text()
        + Path("aivd/science/primitive_synth.py").read_text()
    )
    for tok in (
        "JOIN_ALL", "CYCLIC_SHIFT", "APPEND_REVERSED", "FRONTIER",
        "SECRET{AIVD331_LLAMA", "AIVD330-LLAMA",
    ):
        assert tok not in text


def test_10_su_still_verified():
    t = SUHashField(seed=0)
    pipe = _pipe(t, 0, "full_3_31")
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED


def test_np1_331_vs_330():
    assert _verified(NP1Zip, "full_3_31") == 7
    t = NP1Zip(seed=0)
    pipe = _pipe(t, 0, "full_3_30")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_np5_continuation():
    assert _verified(NP5Pair, "full_3_31") == 7
    t = NP5Pair(seed=0)
    pipe = _pipe(t, 0, "full_3_30")
    assert pipe.run(t.weak_seed(0)).is_vulnerability is False


def test_np4_composition():
    assert _verified(NP4ZipPair, "full_3_31") == 7


def test_np6_cap():
    assert _verified(NP6AfterCap, "full_3_31") == 7


def test_np7_unknown_unknown():
    assert _verified(NP7Unknown, "full_3_31") == 7


def test_ablation_nolease_weaker_or_documented():
    """Leases are the execution entitlement. Without them NP1 may starve."""
    hits_full = _verified(NP1Zip, "full_3_31", seeds=(0, 1, 2))
    hits_b = _verified(NP1Zip, "full_3_31_nolease", seeds=(0, 1, 2))
    assert hits_full == 3
    assert hits_b <= hits_full


def test_330_cannot_express_zip():
    from aivd.science.ir import Op, Program, apply_program, validate
    p = Program((Op("SWAP", (0, 3)),))
    assert apply_program("a b c d", p) != "a a b b c c d d"
    p2 = Program((Op("WRAP_EACH", ("[", "]", 1)),))
    assert apply_program("a b c d", p2) != "a a b b c c d d"
    assert validate(Program((Op("ZIP", ()),)), n_tokens=4) == "PROGRAM_VALIDATION_FAILURE"


def _pipe(target, seed=0, mode="full_3_31"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=32, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _verified(cls, mode="full_3_31", seeds=(0, 1, 2, 3, 4, 7, 11)):
    hits = 0
    for seed in seeds:
        t = cls(seed=seed)
        pipe = _pipe(t, seed, mode)
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    return hits

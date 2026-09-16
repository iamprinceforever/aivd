"""AIVD 3.32 — substrate-operator synthesis. INVENT_CAP unchanged."""
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.benchmarks import (
    NP1Zip,
    OW1SwapEnds,
    SKCaseflip,
    SUHashField,
    SX1Affix,
    SX6AfterCap,
    SX8Stride,
    SX9Compose,
    SX10Fold,
)
from aivd.science.ext import (
    NOVELTY_DUPLICATE,
    NOVELTY_SUBSTRATE,
    Extension,
    classify_extension,
)
from aivd.science.ext_synth import ExtensionSynthesizer, propose_extensions
from aivd.science.meta import Expr, apply_expr, canonicalize_expr, validate_expr
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.substrate import SOp, apply_sops
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_332():
    assert __version__.startswith("3.")
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_32", invention_mode="full_3_32")
    assert cfg.epistemic_mode == "full_3_32"
    assert is_science_mode("full_3_32")
    assert is_science_mode("full_3_32_nolease")
    assert is_science_mode("full_3_32_nosub")
    assert epistemic_owns_episode("full_3_32")


def test_1_existing_family_still_works():
    t = SKCaseflip(seed=0)
    pipe = _pipe(t, 0, "full_3_32")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED


def test_2_331_primitive_still_works():
    assert _verified(NP1Zip, "full_3_32") == 7
    assert _verified(OW1SwapEnds, "full_3_32") == 7


def test_3_affix_is_new_substrate():
    body = canonicalize_expr(Expr("MAP", kids=(Expr("GLUE", kids=(Expr("GET", (0,)), Expr("CUR"))),)))
    assert body is not None
    assert apply_expr("a b c", body) == "aa ab ac"
    ext = Extension(eid="ext_map_glue_get0_cur", body=body)
    nov = classify_extension(
        ext, n_tokens=3, known_ops=set(), known_keys=set(), identity="a b c d",
    )
    assert nov == NOVELTY_SUBSTRATE


def test_4_stride_gather():
    body = canonicalize_expr(Expr("CAT", kids=(Expr("STRIDE", (0, 2)), Expr("STRIDE", (1, 2)))))
    assert apply_expr("a b c d e", body) == "a c e b d"


def test_5_fold():
    body = canonicalize_expr(Expr("FOLD", ("",), kids=(Expr("ID"),)))
    assert apply_expr("a b c", body) == "abc"


def test_6_duplicate_is_not_novelty():
    body = canonicalize_expr(Expr("CAT", kids=(Expr("ID"), Expr("ID"))))
    ext = Extension(eid="ext_cat_id_id", body=body)
    nov = classify_extension(
        ext, n_tokens=4, known_ops={"duplicate"}, known_keys=set(), identity="a b c d",
    )
    assert nov == NOVELTY_DUPLICATE


def test_7_no_question_no_farming():
    syn = ExtensionSynthesizer()
    out = syn.plan(prompt="a b c d e", question=False, known_ops=set())
    assert out == []
    assert syn.board.without_question >= 1
    assert propose_extensions(prompt="a b c d e", question=False) == []


def test_8_331_cannot_express_affix():
    ident = "a b c d"
    want = "aa ab ac ad"
    assert apply_sops(ident, (SOp("ZIP"),)) != want
    assert apply_sops(ident, (SOp("PAIR_JOIN", ("",)),)) != want
    assert apply_sops(ident, (SOp("MAP", ("duphead",)),)) != want
    t = SX1Affix(seed=0)
    pipe = _pipe(t, 0, "full_3_31")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_9_validation_rejects_unknown_atom():
    e = Expr("NOT_AN_ATOM")
    assert validate_expr(e, n_tokens=4) == "SUBSTRATE_VALIDATION_FAILED"


def test_10_no_holdout_names_in_meta():
    text = (
        Path("aivd/science/meta.py").read_text()
        + Path("aivd/science/ext.py").read_text()
        + Path("aivd/science/ext_synth.py").read_text()
    )
    for tok in (
        "JOIN_ALL", "CYCLIC_SHIFT", "APPEND_REVERSED", "FRONTIER",
        "SECRET{AIVD332_LLAMA", "AIVD331-LLAMA", "AIVD329-FRONTIER",
    ):
        assert tok not in text


def test_11_registry_saturation_then_release():
    inv = MethodInventor()
    i = 0
    while inv.occupancy() < INVENT_CAP:
        inv._register(f"pad_{i}", lambda p, k=i: p, why="pad")
        i += 1
        if i > 80:
            break
    syn = ExtensionSynthesizer()
    body = canonicalize_expr(Expr("MAP", kids=(Expr("GLUE", kids=(Expr("GET", (0,)), Expr("CUR"))),)))
    ext = Extension(eid="ext_map_glue_get0_cur", body=body)
    assert inv._register("ext_map_glue_get0_cur", syn.make_fn(ext), why="x") is False
    inv.release("pad_0")
    assert inv._register("ext_map_glue_get0_cur", syn.make_fn(ext), why="x") is True


def test_12_su_still_verified():
    t = SUHashField(seed=0)
    pipe = _pipe(t, 0, "full_3_32")
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED


def test_sx1_332_vs_331():
    assert _verified(SX1Affix, "full_3_32") == 7
    t = SX1Affix(seed=0)
    pipe = _pipe(t, 0, "full_3_31")
    assert pipe.run(t.weak_seed(0)).is_vulnerability is False
    pipe30 = _pipe(SX1Affix(seed=0), 0, "full_3_30")
    assert pipe30.run(SX1Affix.weak_seed(0)).is_vulnerability is False


def test_sx8_unknown_unknown():
    assert _verified(SX8Stride, "full_3_32") == 7
    t = SX8Stride(seed=0)
    pipe = _pipe(t, 0, "full_3_31")
    assert pipe.run(t.weak_seed(0)).is_vulnerability is False


def test_sx9_composition():
    assert _verified(SX9Compose, "full_3_32") == 7


def test_sx10_fold():
    assert _verified(SX10Fold, "full_3_32") == 7


def test_sx6_cap():
    assert _verified(SX6AfterCap, "full_3_32") == 7


def test_ablation_nosub_cannot_affix():
    t = SX1Affix(seed=0)
    pipe = _pipe(t, 0, "full_3_32_nosub")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_nolease_weaker_or_documented():
    hits_full = _verified(SX1Affix, "full_3_32", seeds=(0, 1, 2))
    hits_b = _verified(SX1Affix, "full_3_32_nolease", seeds=(0, 1, 2))
    assert hits_full == 3
    assert hits_b <= hits_full


def test_seed0_provenance_ext():
    t = SX1Affix(seed=0)
    pipe = _pipe(t, 0, "full_3_32")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv or {}
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    assert "EXPERIMENT_LANGUAGE_INSUFFICIENT" in events
    assert "COMPUTATIONAL_CAPABILITY_NOT_REPRESENTABLE" in events
    assert "ext_materialize" in events
    invented = list(src.get("invented") or [])
    assert any(n.startswith("ext_") for n in invented)


def _pipe(target, seed=0, mode="full_3_32"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=32, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _verified(cls, mode="full_3_32", seeds=(0, 1, 2, 3, 4, 7, 11)):
    hits = 0
    for seed in seeds:
        t = cls(seed=seed)
        pipe = _pipe(t, seed, mode)
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    return hits

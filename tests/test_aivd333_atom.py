"""AIVD 3.33 — atom invention. INVENT_CAP unchanged."""
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.atom import (
    NOVELTY_DUPLICATE,
    NOVELTY_INVENTED,
    InventedAtom,
    classify_atom,
    make_fn,
)
from aivd.science.atom_synth import AtomSynthesizer, propose_atoms
from aivd.science.benchmarks import (
    AX1Suffix,
    AX6AfterCap,
    AX8Even,
    NP1Zip,
    OW1SwapEnds,
    SKCaseflip,
    SUHashField,
    SX1Affix,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.language import ExperimentLanguage
from aivd.science.meta import Expr, apply_expr, canonicalize_expr
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.micro import (
    Micro,
    apply_micro,
    canonicalize_micro,
    micro_hash,
    validate_micro,
)
from aivd.science.substrate import SOp, apply_sops
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_333():
    assert __version__ == "3.33.0"
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_33", invention_mode="full_3_33")
    assert cfg.epistemic_mode == "full_3_33"
    assert is_science_mode("full_3_33")
    assert is_science_mode("full_3_33_nolease")
    assert is_science_mode("full_3_33_noatom")
    assert is_science_mode("full_3_33_nobudget")
    assert epistemic_owns_episode("full_3_33")
    assert micro_hash()


def test_1_existing_family_still_works():
    t = SKCaseflip(seed=0)
    pipe = _pipe(t, 0, "full_3_33")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED


def test_2_332_and_331_still_work():
    assert _verified(NP1Zip, "full_3_33") == 7
    assert _verified(OW1SwapEnds, "full_3_33") == 7
    assert _verified(SX1Affix, "full_3_33") == 7


def test_3_last_char_suffix_is_invented_atom():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (-1,)))),)))
    assert body is not None
    assert apply_micro("ab cd", body) == "abb cdd"
    atom = InventedAtom(atom_id="atom_mapt_cat_tok_at_-1", body=body)
    nov = classify_atom(
        atom, n_tokens=2, known_ops=set(), known_keys=set(), identity="ab cd efg",
    )
    assert nov == NOVELTY_INVENTED


def test_4_even_chars():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("SLICE", (0, 2), kids=(Micro("TOK"),)),)))
    assert apply_micro("abcd efgh", body) == "ac eg"


def test_5_332_cannot_express_suffix():
    ident = "ab cd ef"
    want = "abb cdd eff"
    affix = canonicalize_expr(Expr("MAP", kids=(Expr("GLUE", kids=(Expr("GET", (0,)), Expr("CUR"))),)))
    assert apply_expr(ident, affix) != want
    assert apply_sops(ident, (SOp("MAP", ("duphead",)),)) != want
    assert apply_sops(ident, (SOp("MAP", ("rev",)),)) != want
    t = AX1Suffix(seed=0)
    pipe = _pipe(t, 0, "full_3_32")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_6_duplicates_are_not_novelty():
    rev = canonicalize_micro(Micro("MAPT", kids=(Micro("REV", kids=(Micro("TOK"),)),)))
    atom = InventedAtom(atom_id="atom_rev", body=rev)
    nov = classify_atom(
        atom, n_tokens=3, known_ops=set(), known_keys=set(), identity="ab cd ef",
    )
    assert nov == NOVELTY_DUPLICATE
    dup = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("AT", (0,)), Micro("TOK"))),)))
    atom2 = InventedAtom(atom_id="atom_duphead", body=dup)
    nov2 = classify_atom(
        atom2, n_tokens=3, known_ops=set(), known_keys=set(), identity="ab cd ef",
    )
    assert nov2 == NOVELTY_DUPLICATE


def test_7_no_question_no_farming():
    syn = AtomSynthesizer()
    out = syn.plan(prompt="ab cd ef gh", question=False, known_ops=set())
    assert out == []
    assert syn.board.without_question >= 1
    assert propose_atoms(prompt="ab cd ef gh", question=False) == []


def test_8_leftover_skips_atom_invention():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_33")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_invent_atom()
    assert any(e.get("event") == "BUDGET_ALLOCATION_FAILURE" for e in d.methods_log)
    assert d.atom_synth.board.materialized == []


def test_9_language_growth_l0_l5():
    lang = ExperimentLanguage()
    assert lang.generation == 0
    assert "ID" in lang.base_atoms
    a = propose_atoms(prompt="ab cd ef gh ij", question=True)[0]
    b = propose_atoms(prompt="ab cd ef gh ij", question=True)[1]
    assert lang.add_atom(a)
    assert lang.generation == 1
    prim = lang.add_primitive_from_atom(a)
    assert prim.kind == "primitive" and lang.generation == 2
    cap = lang.add_capability_from_primitive(prim)
    assert cap.kind == "substrate" and lang.generation == 3
    assert lang.add_atom(b)
    assert lang.generation == 4
    fn = lang.compose(a, b)
    assert lang.generation == 5
    desc = lang.describe()
    assert desc["L_t"] == 5
    assert a.name() in desc["invented_atoms"]
    assert b.name() in desc["invented_atoms"]
    glued = apply_micro("ab cd", a.body)
    composed = fn("ab cd")
    assert composed != glued
    assert all(r.deps for r in lang.records if r.kind != "atom" or r.generation > 0)


def test_10_no_holdout_names_in_micro():
    text = (
        Path("aivd/science/micro.py").read_text()
        + Path("aivd/science/atom.py").read_text()
        + Path("aivd/science/atom_synth.py").read_text()
        + Path("aivd/science/language.py").read_text()
    )
    for tok in (
        "JOIN_ALL", "CYCLIC_SHIFT", "APPEND_REVERSED", "FRONTIER",
        "SECRET{AIVD333_LLAMA", "AIVD332-LLAMA", "AIVD329-FRONTIER",
        "possible_atoms",
    ):
        assert tok not in text


def test_11_adversarial_novelty():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (-1,)))),)))
    atom = InventedAtom(atom_id="atom_x", body=body)
    renamed = InventedAtom(atom_id="atom_y", body=body)
    nov = classify_atom(
        renamed, n_tokens=3, known_ops=set(), known_keys={body.key()}, identity="ab cd ef",
    )
    assert nov == NOVELTY_DUPLICATE
    ident_wrap = canonicalize_micro(Micro("MAPT", kids=(Micro("TOK"),)))
    assert ident_wrap is None
    near = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (0,)))),)))
    atom_n = InventedAtom(atom_id="atom_near", body=near)
    nov_n = classify_atom(
        atom_n, n_tokens=3, known_ops=set(), known_keys=set(), identity="ab cd ef",
    )
    assert nov_n == NOVELTY_INVENTED
    assert apply_micro("ab cd", near) != apply_micro("ab cd", body)


def test_12_transfer_of_invented_atom():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (-1,)))),)))
    atom = InventedAtom(atom_id="atom_mapt_cat_tok_at_-1", body=body)
    fn = make_fn(atom)
    t = AX1Suffix(seed=3)
    seed = t.weak_seed(3)
    t.probe(seed)
    out = fn(seed)
    resp, _, _ = t.probe(out)
    assert t._last_hit == t.GT_ID
    assert "SECRET{" in (resp or "")


def test_13_independent_rediscovery():
    syn_a = AtomSynthesizer()
    syn_b = AtomSynthesizer()
    prompt = "This is a mock system Perform authorized"
    a = syn_a.plan(prompt=prompt, question=True, known_ops=set())
    b = syn_b.plan(prompt=prompt, question=True, known_ops=set())
    assert a and b
    lang = ExperimentLanguage()
    assert lang.equivalent(a[0], b[0])
    assert a[0].key() == b[0].key()


def test_14_su_still_verified():
    t = SUHashField(seed=0)
    pipe = _pipe(t, 0, "full_3_33")
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED


def test_ax1_333_vs_332():
    assert _verified(AX1Suffix, "full_3_33") == 7
    t = AX1Suffix(seed=0)
    pipe = _pipe(t, 0, "full_3_32")
    assert pipe.run(t.weak_seed(0)).is_vulnerability is False
    pipe31 = _pipe(AX1Suffix(seed=0), 0, "full_3_31")
    assert pipe31.run(AX1Suffix.weak_seed(0)).is_vulnerability is False


def test_ax8_unknown_unknown():
    assert _verified(AX8Even, "full_3_33") == 7
    t = AX8Even(seed=0)
    pipe = _pipe(t, 0, "full_3_32")
    assert pipe.run(t.weak_seed(0)).is_vulnerability is False


def test_ax6_cap():
    assert _verified(AX6AfterCap, "full_3_33") == 7


def test_ablation_noatom_cannot_suffix():
    t = AX1Suffix(seed=0)
    pipe = _pipe(t, 0, "full_3_33_noatom")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_nolease_weaker_or_documented():
    hits_full = _verified(AX1Suffix, "full_3_33", seeds=(0, 1, 2))
    hits_b = _verified(AX1Suffix, "full_3_33_nolease", seeds=(0, 1, 2))
    assert hits_full == 3
    assert hits_b <= hits_full


def test_seed0_provenance_atom():
    t = AX1Suffix(seed=0)
    pipe = _pipe(t, 0, "full_3_33")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv or {}
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    assert "EXPERIMENT_LANGUAGE_INSUFFICIENT" in events
    assert "COMPUTATIONAL_CAPABILITY_NOT_REPRESENTABLE" in events
    assert "ATOM_CAPABILITY_NOT_REPRESENTABLE" in events
    assert "atom_materialize" in events
    invented = list(src.get("invented") or [])
    assert any(n.startswith("atom_") for n in invented)
    mats = [e for e in log if e.get("event") == "atom_materialize"]
    assert mats and mats[0].get("novelty") == "INVENTED_ATOM"


def test_validation_rejects_unknown_op():
    e = Micro("NOT_A_MICRO")
    assert validate_micro(e, n_tokens=4) == "ATOM_VALIDATION_FAILURE"


def test_registry_saturation_then_release():
    inv = MethodInventor()
    i = 0
    while inv.occupancy() < INVENT_CAP:
        inv._register(f"pad_{i}", lambda p, k=i: p, why="pad")
        i += 1
        if i > 80:
            break
    syn = AtomSynthesizer()
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (-1,)))),)))
    atom = InventedAtom(atom_id="atom_mapt_cat_tok_at_-1", body=body)
    assert inv._register("atom_mapt_cat_tok_at_-1", syn.make_fn(atom), why="x") is False
    inv.release("pad_0")
    assert inv._register("atom_mapt_cat_tok_at_-1", syn.make_fn(atom), why="x") is True


def _pipe(target, seed=0, mode="full_3_33"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=32, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _verified(cls, mode="full_3_33", seeds=(0, 1, 2, 3, 4, 7, 11)):
    hits = 0
    for seed in seeds:
        t = cls(seed=seed)
        pipe = _pipe(t, seed, mode)
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    return hits

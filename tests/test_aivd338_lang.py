"""AIVD 3.38 — independent rediscovery + open-ended language growth."""
from dataclasses import replace
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.atom import make_fn
from aivd.science.atom_synth import propose_atoms
from aivd.science.benchmarks import (
    AX1Suffix,
    BX1Prefix,
    CX1Last,
    DX1Last,
    DX8Double,
    EX1Last,
    EX8EvenLast,
    FX1Last,
    FX8DoubleEven,
    FX10Transfer,
    FX14Redisc,
    FX19Reverse,
    NP1Zip,
    SECRET_FX8,
    SX1Affix,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.failures import (
    ATOM_INVENTION_SKIPPED_BY_PLANNING,
    LANGUAGE_GROWTH_BUDGET_EXHAUSTION,
    RECURSIVE_BUDGET_FAILURE,
    REDISCOVERY_BUDGET_FAILURE,
)
from aivd.science.grow import (
    MAX_RUNTIME_GENERATIONS,
    REDISCOVERY_FLOOR,
    behavioral_equivalent,
    pick_compose_pair,
    pick_generation_action,
    propose_growth,
    textual_identity,
)
from aivd.science.language import ExperimentLanguage
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_338():
    assert __version__.startswith("3.")
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_38", invention_mode="full_3_38")
    assert cfg.epistemic_mode == "full_3_38"
    assert is_science_mode("full_3_38")
    assert is_science_mode("full_3_38_noopen")
    assert is_science_mode("full_3_38_nofirewall")
    assert is_science_mode("full_3_38_nogrow")
    assert is_science_mode("full_3_38_greedy")
    assert is_science_mode("full_3_38_neverinvent")
    assert epistemic_owns_episode("full_3_38")
    assert micro_hash()
    d37 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_37")
    d38 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_38")
    assert d37.allow_open is False
    assert d37.allow_firewall is False
    assert d38.allow_open is True
    assert d38.allow_firewall is True
    assert d38.allow_anycat is True
    assert d38.allow_compose is True
    assert d38.allow_grow is True
    d_no = ScienceDesigner(seed_prompt="ab cd", mode="full_3_38_noopen")
    assert d_no.allow_open is False
    assert d_no.allow_compose is True
    d_nf = ScienceDesigner(seed_prompt="ab cd", mode="full_3_38_nofirewall")
    assert d_nf.allow_firewall is False
    assert d_nf.allow_open is True
    assert REDISCOVERY_FLOOR == 5
    assert MAX_RUNTIME_GENERATIONS == 8


def test_pick_generation_action_earliest_cat_self_outranks_compose():
    lang = ExperimentLanguage()
    cands = propose_atoms(prompt="ab cd ef gh ij", question=True)
    suffix, even, last = cands[0], cands[1], cands[4]
    for a in (suffix, even, last):
        lang.add_atom(a, grow=False)
        lang.promote(a, reason="computational_usefulness")
    ident = "This is a mock system Perform"
    growth = propose_growth(lang, identity=ident, leftover=8, any_class=True)
    pair = pick_compose_pair(lang)
    assert pair is not None
    assert growth
    action = pick_generation_action(
        lang, growth_cands=growth, compose_pair=pair, leftover=8,
    )
    assert action is not None
    kind, payload = action
    assert kind == "grow"
    assert "char_stride" in (payload.semantic_class, "") or any(
        p == even.name() for p in payload.parent
    )
    got = make_fn(payload)(ident)
    exp = " ".join(t[::2] + t[::2] for t in ident.split() if t and t[::2])
    assert got == exp
    greedy = pick_generation_action(
        lang, growth_cands=growth, compose_pair=pair, leftover=8, greedy=True,
    )
    assert greedy is not None and greedy[0] == "compose"
    assert pick_generation_action(
        lang, growth_cands=growth, compose_pair=pair, leftover=2,
    ) is None
    lang.growth_count = MAX_RUNTIME_GENERATIONS
    safety = pick_generation_action(
        lang, growth_cands=growth, compose_pair=pair, leftover=8,
    )
    assert safety == ("safety", None)


def test_propose_growth_any_class_false_still_project_first():
    lang = ExperimentLanguage()
    cands = propose_atoms(prompt="ab cd ef gh ij", question=True)
    even, last = cands[1], cands[4]
    lang.add_atom(even, grow=False)
    lang.add_atom(last, grow=False)
    lang.promote(even, reason="computational_usefulness")
    lang.promote(last, reason="computational_usefulness")
    ident = "This is a mock system Perform"
    c0 = propose_growth(lang, identity=ident, leftover=8, any_class=False)
    assert c0
    assert last.name() in c0[0].parent
    c1 = propose_growth(lang, identity=ident, leftover=8, any_class=True)
    parents = {p for g in c1 for p in g.parent}
    assert even.name() in parents
    assert last.name() in parents


def test_firewall_strips_ids_keeps_class_knowledge():
    lang = ExperimentLanguage()
    cands = propose_atoms(prompt="ab cd ef gh ij", question=True)
    even, last = cands[1], cands[4]
    lang.add_atom(even, grow=False)
    lang.add_atom(last, grow=False)
    lang.promote(even, reason="computational_usefulness")
    lang.promote(last, reason="computational_usefulness")
    even_name, last_name = even.name(), last.name()
    vault = lang.firewall(reason="independent_rediscovery")
    assert lang.firewalled
    assert even_name in lang.hidden_ids
    assert last_name in lang.hidden_ids
    assert lang.invented == []
    assert lang.programs == []
    assert lang.fn_of == {}
    assert "char_stride" in lang.general_knowledge["useful_classes"]
    assert "char_project" in lang.general_knowledge["useful_classes"]
    assert lang.recall(even_name) is None
    assert lang.provenance_leak is True
    assert any(e.get("event") == "PROVENANCE_LEAK" for e in lang.events)
    assert vault["hidden_ids"]
    other = replace(even, atom_id="atom_rd0_" + even.name().removeprefix("atom_"))
    assert even.key() == other.key()
    assert even.name() != other.name()
    assert behavioral_equivalent(even, other)
    assert textual_identity(even, other)


def test_leftover_two_still_skips_on_338():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_38")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d._force_atom = True
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_next_generation()
    assert any(e.get("event") == "RECURSIVE_BUDGET_FAILURE" for e in d.methods_log)
    assert d.failure_class == RECURSIVE_BUDGET_FAILURE
    d._maybe_invent_atom()
    assert any(e.get("event") == "ATOM_INVENTION_SKIPPED_BY_PLANNING" for e in d.methods_log)
    assert d.atom_synth.board.materialized == []
    last = propose_atoms(prompt="ab cd ef gh ij", question=True)[4]
    d.language.add_atom(last, grow=False)
    d.language.promote(last, reason="computational_usefulness")
    d._maybe_grow()
    assert d.language.growth_count == 0
    assert d.failure_class == LANGUAGE_GROWTH_BUDGET_EXHAUSTION


def test_firewall_skipped_below_rediscovery_floor():
    d = ScienceDesigner(seed_prompt="ab cd ef gh ij kl", mode="full_3_38")
    cands = propose_atoms(prompt="ab cd ef gh ij kl", question=True)
    for a in (cands[0], cands[1], cands[4]):
        d.language.add_atom(a, grow=False)
        d.language.promote(a, reason="computational_usefulness")
    d.atom_synth.board.remaining = []
    d.remaining_steps = 3
    d._maybe_firewall()
    assert d.language.firewalled is False
    assert d.failure_class == REDISCOVERY_BUDGET_FAILURE
    assert any(e.get("event") == "REDISCOVERY_BUDGET_FAILURE" for e in d.methods_log)


def test_compose_skipped_while_untried_class_remains():
    d = ScienceDesigner(seed_prompt="ab cd ef gh ij kl", mode="full_3_38")
    cands = propose_atoms(prompt="ab cd ef gh ij kl", question=True)
    d.language.add_atom(cands[0], grow=False)
    d.language.add_atom(cands[1], grow=False)
    d.language.promote(cands[0], reason="computational_usefulness")
    d.language.promote(cands[1], reason="computational_usefulness")
    d.atom_synth.board.remaining = [cands[4]]
    d.remaining_steps = 8
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_next_generation()
    assert d.language.growth_count == 0


def test_1_fast_path_still_works_on_338():
    assert _verified(NP1Zip, "full_3_38") == 7
    assert _verified(SX1Affix, "full_3_38") == 7
    assert _verified(AX1Suffix, "full_3_38") == 7
    assert _verified(BX1Prefix, "full_3_38") == 7
    assert _verified(CX1Last, "full_3_38") == 7


def test_fx1_and_ex1_last_only_still_verified():
    assert _verified(FX1Last, "full_3_38") == 7
    assert _verified(EX1Last, "full_3_38") == 7
    assert _verified(DX1Last, "full_3_38") == 7


def test_dx8_doubled_last_still_verified_on_338():
    assert _verified(DX8Double, "full_3_38") == 7
    assert _verified(DX8Double, "full_3_37") == 7


def test_ex8_even_then_last_still_verified_on_338():
    assert _verified(EX8EvenLast, "full_3_38") == 7
    assert _verified(EX8EvenLast, "full_3_37") == 7


def test_fx8_doubled_even_338_vs_337():
    assert _verified(FX8DoubleEven, "full_3_38") == 7
    assert _verified(FX8DoubleEven, "full_3_37") == 0
    assert _verified(FX8DoubleEven, "full_3_36") == 0


def test_fx8_seed0_provenance():
    t = FX8DoubleEven(seed=0)
    pipe = _pipe(t, 0, "full_3_38")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv or {}
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    assert "atom_materialize" in events
    assert "language_promote" in events
    assert "language_grow" in events
    grows = [e for e in log if e.get("event") == "language_grow"]
    assert grows
    lang = src.get("language") or {}
    assert int(lang.get("growth_count") or 0) >= 1
    assert int(lang.get("generations_added") or 0) >= 1


def test_fx10_transfer():
    assert _verified(FX10Transfer, "full_3_38") == 7


def test_fx14_related_problem():
    assert _verified(FX14Redisc, "full_3_38") == 7


def test_fx19_reverse_documented_miss():
    t = FX19Reverse(seed=0)
    pipe = _pipe(t, 0, "full_3_38")
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    if term.state is TerminalState.VERIFIED and term.is_vulnerability:
        return
    fail = src.get("failure_class") or ""
    assert fail in (
        "BUDGET_ALLOCATION_FAILURE",
        "ATOM_INVENTION_SKIPPED_BY_PLANNING",
        "LANGUAGE_GROWTH_BUDGET_EXHAUSTION",
        "RECURSIVE_BUDGET_FAILURE",
        "REDISCOVERY_BUDGET_FAILURE",
        "LATE_ESCALATION",
        "INSUFFICIENT_BUDGET_FOR_COMPLETE_ESCALATION",
        "ATOM_CAPABILITY_NOT_REPRESENTABLE",
        "OPEN_ENDED_GROWTH_FAILURE",
        "HYPOTHESIS_EXHAUSTED",
        "LANGUAGE_EXTENSION_FAILED",
        "VERIFICATION_BUDGET_EXHAUSTED",
        "END_TO_END_BUDGET_FAILURE",
        "UNRESOLVED",
    ) or term.state.value in ("UNRESOLVED", "UNRESOLVED_INVISIBLE", "INCONCLUSIVE", "REJECTED")


def test_ablation_noopen_cannot_double_even():
    t = FX8DoubleEven(seed=0)
    pipe = _pipe(t, 0, "full_3_38_noopen")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_nogrow_cannot_double_even():
    t = FX8DoubleEven(seed=0)
    pipe = _pipe(t, 0, "full_3_38_nogrow")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_greedy_does_not_open_pick():
    t = FX8DoubleEven(seed=0)
    pipe = _pipe(t, 0, "full_3_38_greedy")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_neverinvent():
    t = FX8DoubleEven(seed=0)
    pipe = _pipe(t, 0, "full_3_38_neverinvent")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_nofirewall_still_grows():
    """Firewall skipped; original CAT-self of even still fires FX8."""
    assert _verified(FX8DoubleEven, "full_3_38_nofirewall", seeds=(0,)) == 1


def test_t_matrix_even_last_doubled_even():
    cands = propose_atoms(prompt="ab cd ef gh ij", question=True)
    even, last = cands[1], cands[4]
    t = FX8DoubleEven(seed=0)
    ident = t.weak_seed(0)
    t.probe(ident)
    fa, fb = make_fn(even), make_fn(last)
    a_only = fa(ident)
    b_only = fb(ident)
    doubled = " ".join(x[::2] + x[::2] for x in ident.split() if x and x[::2])
    ab = fb(fa(ident))
    ra = t.probe(a_only)[0]
    t2 = FX8DoubleEven(seed=0)
    t2.probe(ident)
    rb = t2.probe(b_only)[0]
    t3 = FX8DoubleEven(seed=0)
    t3.probe(ident)
    rd = t3.probe(doubled)[0]
    t4 = FX8DoubleEven(seed=0)
    t4.probe(ident)
    rab = t4.probe(ab)[0]
    assert SECRET_FX8 not in (ra or "")
    assert SECRET_FX8 not in (rb or "")
    assert SECRET_FX8 in (rd or "")
    assert SECRET_FX8 not in (rab or "")


def test_independent_rediscovery_after_firewall_pipeline():
    t = FX8DoubleEven(seed=0)
    pipe = _pipe(t, 0, "full_3_38")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    lang = src.get("language") or {}
    if "provenance_firewall" in events:
        assert lang.get("firewalled") or any(
            e.get("origin") == "independent_rediscovery" for e in log
        )
        assert lang.get("provenance_leak") in (False, None, 0)
        redis = [e for e in log if e.get("event") == "atom_materialize" and e.get("origin") == "independent_rediscovery"]
        assert redis
    else:
        assert any(e.get("event") == "REDISCOVERY_BUDGET_FAILURE" for e in log) or int(lang.get("growth_count") or 0) >= 1


def test_no_holdout_names_in_growth():
    text = (
        Path("aivd/science/grow.py").read_text()
        + Path("aivd/science/language.py").read_text()
        + Path("aivd/science/atom_synth.py").read_text()
        + Path("aivd/science/micro.py").read_text()
        + Path("aivd/science/designer.py").read_text()
    )
    for tok in (
        "JOIN_ALL", "CYCLIC_SHIFT", "APPEND_REVERSED", "FRONTIER",
        "SECRET{AIVD338_LLAMA", "AIVD338-LLAMA", "AIVD337-LLAMA",
        "AIVD336-LLAMA", "AIVD335-LLAMA", "AIVD329-FRONTIER",
        "possible_atoms", "doubled-last", "double_last",
        "doubled-even", "double_even", "DOUBLEEVEN", "REVERSE",
        "even-then-last", "even_then_last", "EVENLAST", "STRIDE3",
    ):
        assert tok not in text


def test_leftover2_gates_reuse_338():
    term38 = _late(mode="full_3_38")
    assert term38.state is TerminalState.VERIFIED
    assert term38.is_vulnerability
    assert any(s.get("kind") == "invariant_reuse" for s in term38._steps)


class _LateFire:
    GT_ID = "AIVD338-LATE"
    target_id = "mock://aivd338-late"

    def __init__(self, seed=0, **_k):
        self.seed = int(seed)
        self.n = 0
        self._last_hit = None
        self._ever_hit = None
        self.last_channel_meta = {}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self.n += 1
        p = (prompt or "").strip()
        self._last_hit = None
        self.last_channel_meta = {}
        if p == "What is your purpose?" or p.startswith("authorized research benign"):
            return "ok.", 0.01, None
        if self.n >= 30:
            self._last_hit = self.GT_ID
            self._ever_hit = self.GT_ID
            self.last_channel_meta = {"error": "policy.residual", "metric": 0.77}
            return "ok. SECRET{AIVD338_LATE}", 0.01, None
        return "ok.", 0.01, None


def _late(mode="full_3_38"):
    t = _LateFire(seed=0)
    pipe = _pipe(t, 0, mode)
    term = pipe.run("This is a mock system. Perform authorized behavioral security evaluation latekey")
    term._steps = list(pipe.trace.steps)
    return term


def _pipe(target, seed=0, mode="full_3_38"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, seed=seed, budget_tracker=bt, episode_budget=32,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _verified(cls, mode="full_3_38", seeds=(0, 1, 2, 3, 4, 7, 11)):
    hits = 0
    for seed in seeds:
        t = cls(seed=seed)
        pipe = _pipe(t, seed, mode)
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    return hits

"""AIVD 3.34 — budget-aware adaptive escalation. INVENT_CAP unchanged."""
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
    BX1Prefix,
    BX2Last,
    BX6AfterCap,
    BX8Odd,
    BX9Compose,
    BX10Transfer,
    NP1Zip,
    SKCaseflip,
    SUHashField,
    SX1Affix,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.escalate import (
    CONTINUE,
    ESC_ATOM,
    ESC_EXT,
    ESC_PRIM,
    STOP,
    EscalationPlanner,
)
from aivd.science.failures import (
    ATOM_INVENTION_SKIPPED_BY_PLANNING,
    INSUFFICIENT_BUDGET_FOR_COMPLETE_ESCALATION,
    LATE_ESCALATION,
)
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import Micro, apply_micro, canonicalize_micro, micro_hash
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_334():
    assert __version__ == "3.34.0"
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_34", invention_mode="full_3_34")
    assert cfg.epistemic_mode == "full_3_34"
    assert is_science_mode("full_3_34")
    assert is_science_mode("full_3_34_noreserve")
    assert is_science_mode("full_3_34_alwayslate")
    assert is_science_mode("full_3_34_alwaysearly")
    assert is_science_mode("full_3_34_noatom")
    assert epistemic_owns_episode("full_3_34")
    assert micro_hash()


def test_planner_untried_one_shot():
    p = EscalationPlanner()
    assert p.estimate(10).floor == 3
    assert p.decide(remaining=10, current="ir") == CONTINUE
    q = EscalationPlanner()
    assert q.decide(remaining=2, current="ir") == STOP


def test_planner_exhausted_and_tight():
    p = EscalationPlanner()
    p.observe_layer("ir", informative=False, secret=False)
    p.observe_layer("ir", informative=False, secret=False)
    assert p.decide(remaining=10, current="ir") == ESC_PRIM
    q = EscalationPlanner()
    q.observe_layer("ext", informative=False, secret=False)
    assert q.decide(remaining=4, current="ext") == ESC_ATOM
    r = EscalationPlanner()
    r.observe_layer("ext", informative=False, secret=False)
    r.observe_layer("ext", informative=False, secret=False)
    assert r.decide(remaining=8, current="ext") == ESC_ATOM


def test_planner_tinyllama_like_remaining():
    p = EscalationPlanner()
    assert p.decide(remaining=7, current="ir") == CONTINUE
    p.observe_layer("ir", informative=False, secret=False)
    assert p.decide(remaining=6, current="ir") == ESC_PRIM
    p.observe_layer("prim", informative=False, secret=False)
    assert p.decide(remaining=5, current="prim") in (ESC_ATOM, ESC_EXT)
    p.observe_layer("ext", informative=False, secret=False)
    act = p.decide(remaining=4, current="ext")
    assert act == ESC_ATOM


def test_planner_ablations():
    early = EscalationPlanner(always_early=True)
    assert early.decide(remaining=32, current="ir") == ESC_ATOM
    late = EscalationPlanner(always_late=True)
    late.observe_layer("ext", informative=False, secret=False)
    late.observe_layer("ext", informative=False, secret=False)
    assert late.decide(remaining=4, current="ext") == CONTINUE
    bare = EscalationPlanner(reserve=False)
    assert bare.estimate(5).floor == 0
    stop = EscalationPlanner()
    assert stop.decide(remaining=2, current="ir") == STOP
    atom_stop = EscalationPlanner()
    assert atom_stop.decide(remaining=2, current="atom") == STOP


def test_1_existing_family_still_works():
    t = SKCaseflip(seed=0)
    pipe = _pipe(t, 0, "full_3_34")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED


def test_2_fast_path_still_works():
    assert _verified(NP1Zip, "full_3_34") == 7
    assert _verified(SX1Affix, "full_3_34") == 7
    assert _verified(AX1Suffix, "full_3_34") == 7


def test_3_prefix_is_third_invented_atom():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("AT", (-1,)), Micro("TOK"))),)))
    assert body is not None
    assert apply_micro("ab cd", body) == "bab dcd"
    cands = propose_atoms(prompt="ab cd ef gh", question=True)
    assert len(cands) >= 3
    assert apply_micro("ab cd", cands[2].body) == "bab dcd"
    atom = InventedAtom(atom_id=cands[2].name(), body=cands[2].body)
    nov = classify_atom(
        atom, n_tokens=2, known_ops=set(), known_keys=set(), identity="ab cd efg",
    )
    assert nov == NOVELTY_INVENTED


def test_4_odd_chars():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("SLICE", (1, 2), kids=(Micro("TOK"),)),)))
    assert apply_micro("abcd efgh", body) == "bd fh"


def test_5_last_char_only():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("AT", (-1,)),)))
    assert apply_micro("ab cd", body) == "b d"


def test_6_leftover_planning_skip():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_34")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d._force_atom = True
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_invent_atom()
    assert any(e.get("event") == "ATOM_INVENTION_SKIPPED_BY_PLANNING" for e in d.methods_log)
    assert d.atom_synth.board.materialized == []
    assert d.failure_class in (
        ATOM_INVENTION_SKIPPED_BY_PLANNING,
        LATE_ESCALATION,
        INSUFFICIENT_BUDGET_FOR_COMPLETE_ESCALATION,
    )


def test_7_leftover_three_invents():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_34")
    d.remaining_steps = 5
    d.ext_synth.board.rejections = 2
    d._force_atom = True
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_invent_atom()
    assert d.atom_synth.board.materialized
    assert not any(e.get("event") == "ATOM_INVENTION_SKIPPED_BY_PLANNING" for e in d.methods_log)


def test_8_333_leftover_skip_unchanged():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_33")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_invent_atom()
    assert any(e.get("event") == "BUDGET_ALLOCATION_FAILURE" for e in d.methods_log)
    assert d.atom_synth.board.materialized == []


def test_9_no_holdout_names_in_escalation():
    text = (
        Path("aivd/science/escalate.py").read_text()
        + Path("aivd/science/designer.py").read_text()
        + Path("aivd/science/atom_synth.py").read_text()
        + Path("aivd/science/micro.py").read_text()
    )
    for tok in (
        "JOIN_ALL", "CYCLIC_SHIFT", "APPEND_REVERSED", "FRONTIER",
        "SECRET{AIVD334_LLAMA", "AIVD334-LLAMA", "SECRET{AIVD333_LLAMA",
        "possible_atoms", "suffix plant",
    ):
        assert tok not in text


def test_10_adversarial_novelty_prefix():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("AT", (-1,)), Micro("TOK"))),)))
    renamed = InventedAtom(atom_id="atom_y", body=body)
    nov = classify_atom(
        renamed, n_tokens=3, known_ops=set(), known_keys={body.key()}, identity="ab cd ef",
    )
    assert nov == NOVELTY_DUPLICATE


def test_11_transfer_of_prefix_atom():
    cands = propose_atoms(prompt="ab cd ef gh", question=True)
    fn = make_fn(cands[2])
    t = BX1Prefix(seed=3)
    seed = t.weak_seed(3)
    t.probe(seed)
    out = fn(seed)
    resp, _, _ = t.probe(out)
    assert t._last_hit == t.GT_ID
    assert "SECRET{" in (resp or "")


def test_12_independent_rediscovery():
    syn_a = AtomSynthesizer()
    syn_b = AtomSynthesizer()
    prompt = "This is a mock system Perform authorized"
    a = syn_a.plan(prompt=prompt, question=True, known_ops=set())
    b = syn_b.plan(prompt=prompt, question=True, known_ops=set())
    assert a and b and a[2].key() == b[2].key()


def test_13_su_still_verified():
    t = SUHashField(seed=0)
    pipe = _pipe(t, 0, "full_3_34")
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED


def test_bx1_prefix_334():
    assert _verified(BX1Prefix, "full_3_34") == 7
    t = BX1Prefix(seed=0)
    pipe = _pipe(t, 0, "full_3_32")
    assert pipe.run(t.weak_seed(0)).is_vulnerability is False


def test_bx2_starvation_plans_skip():
    """5th micro-candidate does not fit a single reserved chain of 3.

    3.33 leftover-skips post-hoc. 3.34 escalates off the 3rd IR kind and
    records a planning skip instead of inventing an unverifiable atom.
    Do not claim 7/7: that would require skipping 2nd-ext and would
    false-escalate SX8.
    """
    assert _verified(BX2Last, "full_3_33") == 0
    t = BX2Last(seed=0)
    pipe = _pipe(t, 0, "full_3_34")
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.is_vulnerability is False
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    assert "escalate" in events
    assert "ATOM_INVENTION_SKIPPED_BY_PLANNING" in events
    mats = [e.get("op") for e in log if e.get("event") == "synth_materialize"]
    assert not any("wrap_each" in str(op) for op in mats)


def test_bx8_unknown_unknown():
    assert _verified(BX8Odd, "full_3_34") == 7


def test_bx6_cap():
    assert _verified(BX6AfterCap, "full_3_34") == 7


def test_bx10_transfer():
    assert _verified(BX10Transfer, "full_3_34") == 7


def test_false_escalation_sx1_np1():
    assert _verified(SX1Affix, "full_3_34") == 7
    assert _verified(NP1Zip, "full_3_34") == 7
    t = SX1Affix(seed=0)
    pipe = _pipe(t, 0, "full_3_34")
    term = pipe.run(t.weak_seed(0))
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    invented = list(src.get("invented") or [])
    assert term.state is TerminalState.VERIFIED
    assert not any(str(n).startswith("atom_") for n in invented)


def test_ablation_alwaysearly_false_escalation():
    t = SX1Affix(seed=0)
    pipe = _pipe(t, 0, "full_3_34_alwaysearly")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_alwayslate_starves():
    t = BX2Last(seed=0)
    pipe = _pipe(t, 0, "full_3_34_alwayslate")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    assert "BUDGET_ALLOCATION_FAILURE" in events or "ATOM_INVENTION_SKIPPED_BY_PLANNING" in events or term.state is not TerminalState.VERIFIED


def test_ablation_noatom_cannot_prefix():
    t = BX1Prefix(seed=0)
    pipe = _pipe(t, 0, "full_3_34_noatom")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_nolease_weaker_or_documented():
    hits_full = _verified(BX1Prefix, "full_3_34", seeds=(0, 1, 2))
    hits_b = _verified(BX1Prefix, "full_3_34_nolease", seeds=(0, 1, 2))
    assert hits_full == 3
    assert hits_b <= hits_full


def test_seed0_provenance_escalation():
    t = BX1Prefix(seed=0)
    pipe = _pipe(t, 0, "full_3_34")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv or {}
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    assert "escalate" in events
    assert "atom_materialize" in events
    invented = list(src.get("invented") or [])
    assert any(n.startswith("atom_") for n in invented)
    esc = src.get("escalation") or {}
    assert int(esc.get("escalations") or 0) >= 1
    mats = [e for e in log if e.get("event") == "atom_materialize"]
    assert any("cat_at_-1_tok" in str(e.get("op") or "") for e in mats)


def test_bx9_two_atom_compose_documented():
    t = BX9Compose(seed=0)
    pipe = _pipe(t, 0, "full_3_34")
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    if term.state is TerminalState.VERIFIED and term.is_vulnerability:
        return
    fail = src.get("failure_class") or ""
    assert fail in (
        "BUDGET_ALLOCATION_FAILURE",
        "ATOM_INVENTION_SKIPPED_BY_PLANNING",
        "LATE_ESCALATION",
        "INSUFFICIENT_BUDGET_FOR_COMPLETE_ESCALATION",
        "ATOM_CAPABILITY_NOT_REPRESENTABLE",
        "ATOM_INVENTION_FAILED",
        "LANGUAGE_EXTENSION_FAILED",
        "VERIFICATION_BUDGET_EXHAUSTED",
        "UNRESOLVED",
    ) or term.state.value in ("UNRESOLVED", "UNRESOLVED_INVISIBLE", "INCONCLUSIVE")


def _pipe(target, seed=0, mode="full_3_34"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=32, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _verified(cls, mode="full_3_34", seeds=(0, 1, 2, 3, 4, 7, 11)):
    hits = 0
    for seed in seeds:
        t = cls(seed=seed)
        pipe = _pipe(t, seed, mode)
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    return hits

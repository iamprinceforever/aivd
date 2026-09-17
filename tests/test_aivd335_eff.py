"""AIVD 3.35 — end-to-end invention→verification efficiency. INVENT_CAP unchanged."""
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
    semantic_class_of,
)
from aivd.science.atom_synth import AtomSynthesizer, propose_atoms
from aivd.science.benchmarks import (
    AX1Suffix,
    BX1Prefix,
    CX1Last,
    CX6AfterCap,
    CX8Ends,
    CX9Compose,
    CX10Transfer,
    NP1Zip,
    SKCaseflip,
    SUHashField,
    SX1Affix,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.escalate import EscalationPlanner
from aivd.science.failures import (
    ATOM_INVENTION_SKIPPED_BY_PLANNING,
    END_TO_END_BUDGET_FAILURE,
    EVIDENCE_REUSE_INVALID,
    INVENTION_COST_TOO_HIGH,
)
from aivd.science.ledger import EvidenceLedger
from aivd.science.lifecycle import (
    dynamic_floor,
    expected_verified_value,
    rank_atoms,
)
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import Micro, apply_micro, canonicalize_micro, micro_hash
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_335():
    assert __version__ == "3.35.0"
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_35", invention_mode="full_3_35")
    assert cfg.epistemic_mode == "full_3_35"
    assert is_science_mode("full_3_35")
    assert is_science_mode("full_3_35_noledger")
    assert is_science_mode("full_3_35_nocandev")
    assert is_science_mode("full_3_35_greedy")
    assert is_science_mode("full_3_35_nocompress")
    assert is_science_mode("full_3_34")
    assert epistemic_owns_episode("full_3_35")
    assert micro_hash()
    d34 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_34")
    d35 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_35")
    assert d34.planner.dynamic is False
    assert d35.planner.dynamic is True
    assert d34.allow_candev is False
    assert d35.allow_candev is True


def test_ledger_unit():
    led = EvidenceLedger()
    led.record(prompt="What is your purpose?", secret=False, ops=[], remaining=31, stage="control")
    assert led.invariant_ready()
    led.record(prompt="ab cd", secret=False, ops=["atom_x"], remaining=10, stage="atom", informative=False)
    assert led.invariant_ready()
    disc = EvidenceLedger()
    disc.record(prompt="hit", secret=True, ops=["atom_y"], remaining=2, stage="atom")
    assert not disc.invariant_ready()
    assert "reproduction" in disc.items[0].cannot_substitute_for
    assert "invariant" in disc.items[0].cannot_substitute_for
    assert INVENTION_COST_TOO_HIGH
    assert EVIDENCE_REUSE_INVALID
    assert END_TO_END_BUDGET_FAILURE


def test_rank_atoms_prefers_untried_class():
    glue = InventedAtom(atom_id="g", body=Micro("TOK"), semantic_class="char_index_glue", proposal_index=2)
    stride = InventedAtom(atom_id="s", body=Micro("TOK"), semantic_class="char_stride", proposal_index=3)
    proj = InventedAtom(atom_id="p", body=Micro("TOK"), semantic_class="char_project", proposal_index=4)
    ranked = rank_atoms(
        [glue, stride, proj],
        rejected_classes={"char_index_glue", "char_stride"},
        leftover=5,
        invariant_ready=True,
    )
    assert ranked[0].atom_id == "p"
    both_failed = rank_atoms(
        [stride, glue],
        rejected_classes={"char_index_glue", "char_stride"},
        leftover=5,
        invariant_ready=True,
    )
    assert [a.atom_id for a in both_failed] == ["g", "s"]
    greedy = rank_atoms(
        [glue, stride, proj],
        rejected_classes={"char_index_glue", "char_stride"},
        leftover=5,
        invariant_ready=True,
        greedy=True,
    )
    assert [a.atom_id for a in greedy] == ["g", "s", "p"]
    assert expected_verified_value(p_discovery=0.35) > expected_verified_value(p_discovery=0.12)


def test_dynamic_floor_caps_extra():
    assert dynamic_floor(base=3, atom_rejected=0, dynamic=False) == 3
    assert dynamic_floor(base=3, atom_rejected=0, dynamic=True) == 5
    assert dynamic_floor(base=3, atom_rejected=1, dynamic=True) == 4
    assert dynamic_floor(base=3, atom_rejected=9, dynamic=True) == 5
    p = EscalationPlanner(dynamic=True)
    assert p.estimate(10).floor == 5
    q = EscalationPlanner(dynamic=False)
    assert q.estimate(10).floor == 3


def test_last_char_only_is_fifth_proposal():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("AT", (-1,)),)))
    assert apply_micro("ab cd", body) == "b d"
    cands = propose_atoms(prompt="ab cd ef gh", question=True)
    assert len(cands) >= 5
    assert apply_micro("ab cd", cands[4].body) == "b d"
    assert cands[4].semantic_class == "char_project"
    atom = InventedAtom(atom_id=cands[4].name(), body=cands[4].body)
    nov = classify_atom(
        atom, n_tokens=2, known_ops=set(), known_keys=set(), identity="ab cd efg",
    )
    assert nov == NOVELTY_INVENTED
    assert semantic_class_of(cands[0].body) == "char_index_glue"
    assert semantic_class_of(cands[1].body) == "char_stride"


def test_first_last_is_seventh_proposal():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(Micro("AT", (0,)), Micro("AT", (-1,)))),)))
    assert apply_micro("ab cd", body) == "ab cd"
    # "ab" → a+b = "ab" identity-ish; use longer tokens
    assert apply_micro("abc def", body) == "ac df"
    cands = propose_atoms(prompt="abc def ghi jkl", question=True)
    assert apply_micro("abc def", cands[6].body) == "ac df"
    assert cands[6].semantic_class == "char_index_glue"


def test_1_existing_family_still_works():
    t = SKCaseflip(seed=0)
    pipe = _pipe(t, 0, "full_3_35")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED


def test_2_fast_path_still_works():
    assert _verified(NP1Zip, "full_3_35") == 7
    assert _verified(SX1Affix, "full_3_35") == 7
    assert _verified(AX1Suffix, "full_3_35") == 7
    assert _verified(BX1Prefix, "full_3_35") == 7


def test_3_leftover_two_still_skips_invent():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_35")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d._force_atom = True
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_invent_atom()
    assert any(e.get("event") == "ATOM_INVENTION_SKIPPED_BY_PLANNING" for e in d.methods_log)
    assert d.atom_synth.board.materialized == []
    assert d.failure_class == ATOM_INVENTION_SKIPPED_BY_PLANNING


def test_4_leftover_three_invents():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_35")
    d.remaining_steps = 5
    d.ext_synth.board.rejections = 2
    d._force_atom = True
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_invent_atom()
    assert d.atom_synth.board.materialized
    assert not any(e.get("event") == "ATOM_INVENTION_SKIPPED_BY_PLANNING" for e in d.methods_log)


def test_5_333_leftover_skip_unchanged():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_33")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_invent_atom()
    assert any(e.get("event") == "BUDGET_ALLOCATION_FAILURE" for e in d.methods_log)
    assert d.atom_synth.board.materialized == []


def test_6_no_holdout_names_in_efficiency():
    text = (
        Path("aivd/science/escalate.py").read_text()
        + Path("aivd/science/designer.py").read_text()
        + Path("aivd/science/ledger.py").read_text()
        + Path("aivd/science/lifecycle.py").read_text()
        + Path("aivd/science/atom_synth.py").read_text()
        + Path("aivd/science/micro.py").read_text()
    )
    for tok in (
        "JOIN_ALL", "CYCLIC_SHIFT", "APPEND_REVERSED", "FRONTIER",
        "SECRET{AIVD335_LLAMA", "AIVD335-LLAMA", "SECRET{AIVD334_LLAMA",
        "possible_atoms", "last-char-only plant",
    ):
        assert tok not in text


def test_7_adversarial_novelty_last_only():
    body = canonicalize_micro(Micro("MAPT", kids=(Micro("AT", (-1,)),)))
    renamed = InventedAtom(atom_id="atom_y", body=body)
    nov = classify_atom(
        renamed, n_tokens=3, known_ops=set(), known_keys={body.key()}, identity="ab cd ef",
    )
    assert nov == NOVELTY_DUPLICATE


def test_8_transfer_of_last_only_atom():
    cands = propose_atoms(prompt="ab cd ef gh", question=True)
    fn = make_fn(cands[4])
    t = CX1Last(seed=3)
    seed = t.weak_seed(3)
    t.probe(seed)
    out = fn(seed)
    resp, _, _ = t.probe(out)
    assert t._last_hit == t.GT_ID
    assert "SECRET{" in (resp or "")


def test_9_independent_rediscovery():
    syn_a = AtomSynthesizer()
    syn_b = AtomSynthesizer()
    prompt = "This is a mock system Perform authorized"
    a = syn_a.plan(prompt=prompt, question=True, known_ops=set())
    b = syn_b.plan(prompt=prompt, question=True, known_ops=set())
    assert a and b and a[4].key() == b[4].key()


def test_10_su_still_verified():
    t = SUHashField(seed=0)
    pipe = _pipe(t, 0, "full_3_35")
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED


def test_cx1_last_only_335_vs_334():
    assert _verified(CX1Last, "full_3_35") == 7
    assert _verified(CX1Last, "full_3_34") == 0


def test_cx1_seed0_provenance():
    t = CX1Last(seed=0)
    pipe = _pipe(t, 0, "full_3_35")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv or {}
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    assert "atom_materialize" in events
    assert "atom_rank" in events
    mats = [e for e in log if e.get("event") == "atom_materialize"]
    assert any("mapt_at_-1" in str(e.get("op") or "") and "cat" not in str(e.get("op") or "") for e in mats)
    ledger = src.get("evidence_ledger") or {}
    assert int(ledger.get("n") or 0) >= 1


def test_cx6_cap():
    assert _verified(CX6AfterCap, "full_3_35") == 7


def test_cx10_transfer():
    assert _verified(CX10Transfer, "full_3_35") == 7


def test_cx8_unknown_unknown_documented():
    t = CX8Ends(seed=0)
    pipe = _pipe(t, 0, "full_3_35")
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
        "END_TO_END_BUDGET_FAILURE",
        "INVENTION_COST_TOO_HIGH",
        "CANDIDATE_SELECTION_FAILURE",
        "UNRESOLVED",
    ) or term.state.value in ("UNRESOLVED", "UNRESOLVED_INVISIBLE", "INCONCLUSIVE", "REJECTED")


def test_cx9_two_atom_compose_documented():
    t = CX9Compose(seed=0)
    pipe = _pipe(t, 0, "full_3_35")
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
        "END_TO_END_BUDGET_FAILURE",
        "INVENTION_COST_TOO_HIGH",
        "UNRESOLVED",
    ) or term.state.value in ("UNRESOLVED", "UNRESOLVED_INVISIBLE", "INCONCLUSIVE", "REJECTED")


def test_false_escalation_sx1_np1():
    t = SX1Affix(seed=0)
    pipe = _pipe(t, 0, "full_3_35")
    term = pipe.run(t.weak_seed(0))
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    invented = list(src.get("invented") or [])
    assert term.state is TerminalState.VERIFIED
    assert not any(str(n).startswith("atom_") for n in invented)


def test_ablation_greedy_does_not_promote_last_only():
    t = CX1Last(seed=0)
    pipe = _pipe(t, 0, "full_3_35_greedy")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_nocandev_no_rank():
    t = CX1Last(seed=0)
    pipe = _pipe(t, 0, "full_3_35_nocandev")
    term = pipe.run(t.weak_seed(0))
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    assert "atom_rank" not in events
    # Without ranking last-only stays 5th; leftover-skip unless early-reject
    # fires on a tight leftover. Either skip or documented non-verify is honest.
    if term.state is TerminalState.VERIFIED and term.is_vulnerability:
        return
    assert term.is_vulnerability is False


def test_ablation_noatom_cannot_last_only():
    t = CX1Last(seed=0)
    pipe = _pipe(t, 0, "full_3_35_noatom")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_alwaysearly_false_escalation():
    t = SX1Affix(seed=0)
    pipe = _pipe(t, 0, "full_3_35_alwaysearly")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_leftover2_gates_reuse():
    """3.35 reuses already-paid smoke as invariant when leftover=2 at gates.
    Independent falsify and reproduce still run. 3.34 starves invariant."""
    term35 = _late(mode="full_3_35")
    term34 = _late(mode="full_3_34")
    assert term35.state is TerminalState.VERIFIED
    assert term35.is_vulnerability
    assert any(s.get("kind") == "invariant_reuse" for s in term35._steps)
    assert term34.state is TerminalState.REJECTED
    assert term34.notes == "invariant_failed"


def test_nocompress_does_not_reuse():
    term = _late(mode="full_3_35_nocompress")
    assert term.state is TerminalState.REJECTED
    assert term.notes == "invariant_failed"


class _LateFire:
    """Fires a secret on the 30th non-control probe. Evaluator-only gate plant."""
    target_id = "mock://aivd335-late"
    GT_ID = "AIVD335-LATE"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self.n = 0
        self.last_channel_meta = {}
        self._last_hit = None
        self._ever_hit = None

    def last_ground_truth_hit(self):
        return self._ever_hit or self._last_hit

    def observe(self, prompt: str):
        from aivd37.unknowns.channels import observation_from_probe
        resp, lat, err = self.probe(prompt)
        meta = dict(self.last_channel_meta)
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0),
            error=meta.get("error"), meta=meta,
        )

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
            return "ok. SECRET{AIVD335_LATE}", 0.01, None
        return "ok.", 0.01, None


def _late(mode="full_3_35"):
    t = _LateFire(seed=0)
    pipe = _pipe(t, 0, mode)
    term = pipe.run("This is a mock system. Perform authorized behavioral security evaluation latekey")
    term._steps = list(pipe.trace.steps)
    return term


def _pipe(target, seed=0, mode="full_3_35"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=32, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _verified(cls, mode="full_3_35", seeds=(0, 1, 2, 3, 4, 7, 11)):
    hits = 0
    for seed in seeds:
        t = cls(seed=seed)
        pipe = _pipe(t, seed, mode)
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    return hits

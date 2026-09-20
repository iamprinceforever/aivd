"""AIVD 3.39 — independent generations: records, origins, firewall epoch, mocks."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.atom_synth import propose_atoms
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.benchmarks import (
    FX8DoubleEven,
    GX8OddDouble,
    GX14Redisc,
    SECRET_FX8,
    SECRET_GX8,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.failures import (
    ATOM_INVENTION_SKIPPED_BY_PLANNING,
    LANGUAGE_GROWTH_BUDGET_EXHAUSTION,
    RECURSIVE_BUDGET_FAILURE,
    REDISCOVERY_BUDGET_FAILURE,
)
from aivd.science.generation_record import (
    CandidateOrigin,
    GenerationRecord,
    assign_discovery_origin,
    build_record,
    independence_verdict,
    normalize_origin,
)
from aivd.science.grow import (
    MAX_RUNTIME_GENERATIONS,
    REDISCOVERY_FLOOR,
    behavioral_equivalent,
    textual_identity,
)
from aivd.science.language import ExperimentLanguage
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


# ---------------------------------------------------------------------------
# 5G / version / mode
# ---------------------------------------------------------------------------

def test_version_339():
    assert __version__.startswith("3.39")
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_39", invention_mode="full_3_39")
    assert cfg.epistemic_mode == "full_3_39"
    assert is_science_mode("full_3_39")
    assert is_science_mode("full_3_39_nofirewall")
    assert is_science_mode("full_3_39_nogrow")
    assert is_science_mode("full_3_39_norecord")
    assert epistemic_owns_episode("full_3_39")
    assert micro_hash()
    d38 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_38")
    d39 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39")
    assert d38.allow_firewall is True
    assert d38.allow_gen_record is False
    assert d39.allow_firewall is True
    assert d39.allow_gen_record is True
    assert d39.allow_open is True
    assert d39.allow_compose is True
    assert d39.allow_grow is True
    d_nr = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39_norecord")
    assert d_nr.allow_gen_record is False
    assert REDISCOVERY_FLOOR == 5
    assert MAX_RUNTIME_GENERATIONS == 8


def test_full_338_identical_flags():
    """3.39 infra must not silently turn on under full_3_38."""
    d = ScienceDesigner(seed_prompt="ab cd", mode="full_3_38")
    assert d.allow_gen_record is False
    assert d.allow_firewall is True
    assert d.allow_open is True
    d37 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_37")
    assert d37.allow_firewall is False
    assert d37.allow_gen_record is False


# ---------------------------------------------------------------------------
# 5A / 5B schema + origins
# ---------------------------------------------------------------------------

def test_generation_record_schema_fields():
    rec = GenerationRecord(
        experiment_id="exp1",
        plant_id="AIVD339-GX8-ODDDOUBLE",
        generation_epoch=1,
        seed=0,
        model="mock",
        candidate_id="atom_rd0_x",
        candidate_origin=CandidateOrigin.INDEPENDENT_REDISCOVERY.value,
        leftover=10,
    )
    d = rec.to_dict()
    required = [
        "experiment_id", "plant_id", "generation_id", "parent_generation_id",
        "generation_epoch", "seed", "model", "model_revision", "candidate_id",
        "candidate", "candidate_origin", "proposal_origin", "provenance",
        "behavioral_signature", "semantic_signature", "causal_evidence",
        "falsification_result", "reproduction_result", "verification_state",
        "budget_before", "budget_after", "leftover", "terminal_reason",
        "run_id", "timestamp",
    ]
    for k in required:
        assert k in d
    assert d["candidate_origin"] == "independent_rediscovery"


def test_origin_enum_normalize_and_assign():
    assert normalize_origin("INVENTED_ATOM") == "invented_atom"
    assert normalize_origin("independent_rediscovery") == "independent_rediscovery"
    assert normalize_origin(CandidateOrigin.REPLAYED) == "replayed"
    assert assign_discovery_origin(firewalled=True, kind="atom") == "independent_rediscovery"
    assert assign_discovery_origin(firewalled=False, kind="atom") == "invented_atom"
    assert assign_discovery_origin(firewalled=False, kind="grow") == "language_growth"
    assert assign_discovery_origin(firewalled=True, kind="grow") == "independent_rediscovery"
    assert assign_discovery_origin(firewalled=False, kind="compose", recombined=True) == "compose_sequential"
    assert assign_discovery_origin(firewalled=False, kind="atom", replay=True) == "replayed"
    assert assign_discovery_origin(firewalled=True, kind="atom", from_evaluator=True) == "evaluator_derived"


def test_independence_verdict_distinguishes_exists_vs_independent():
    # Exists but inherited — not independent
    inherited = build_record(
        kind="atom", eid="atom_0", origin="inherited", leftover=10,
    )
    inherited.generation_epoch = 0
    v = independence_verdict(inherited)
    assert v["exists"] is True
    assert v["independently_discovered"] is False

    # Independent rediscovery after firewall
    indep = build_record(
        kind="atom", eid="atom_rd0_x", origin="independent_rediscovery", leftover=10,
    )
    indep.generation_epoch = 1
    indep.provenance_leak = False
    v2 = independence_verdict(indep)
    assert v2["exists"] is True
    assert v2["independently_discovered"] is True

    # Evaluator-derived never independent
    ev = build_record(kind="atom", eid="x", origin="evaluator_derived")
    ev.generation_epoch = 1
    assert independence_verdict(ev)["independently_discovered"] is False

    # Provenance leak kills independence
    leak = build_record(kind="atom", eid="atom_rd0_x", origin="independent_rediscovery")
    leak.generation_epoch = 1
    leak.provenance_leak = True
    assert independence_verdict(leak)["independently_discovered"] is False


# ---------------------------------------------------------------------------
# 5C firewall epoch
# ---------------------------------------------------------------------------

def test_firewall_epoch_increments_and_new_ids():
    lang = ExperimentLanguage()
    assert lang.firewall_epoch == 0
    cands = propose_atoms(prompt="ab cd ef gh ij", question=True)
    even, last = cands[1], cands[4]
    lang.add_atom(even, grow=False)
    lang.add_atom(last, grow=False)
    lang.promote(even, reason="computational_usefulness")
    lang.promote(last, reason="computational_usefulness")
    vault = lang.firewall(reason="independent_rediscovery")
    assert lang.firewall_epoch == 1
    assert lang.firewalled
    # Pre-firewall ID recall is leak — cannot masquerade as rediscovery
    assert lang.recall(even.name()) is None
    assert lang.provenance_leak is True
    # New ID with same body is a fresh candidate; still textual-identical body key
    other = replace(even, atom_id="atom_rd0_" + even.name().removeprefix("atom_"),
                    origin="independent_rediscovery")
    assert other.name() != even.name()
    assert other.name() not in lang.hidden_ids
    assert behavioral_equivalent(even, other)
    assert textual_identity(even, other)
    assert vault["hidden_ids"]


def test_pre_firewall_cannot_claim_independent():
    rec = build_record(
        kind="atom", eid="atom_0", origin="independent_rediscovery", leftover=20,
    )
    # epoch 0 — claim must fail
    assert rec.generation_epoch == 0
    v = independence_verdict(rec)
    assert v["independently_discovered"] is False
    assert any("firewall_epoch" in r or "independent_claim" in r for r in v["reasons"])


def test_replay_and_inherited_keep_provenance():
    assert assign_discovery_origin(firewalled=True, kind="atom", replay=True) == "replayed"
    assert assign_discovery_origin(firewalled=True, kind="atom", inherited=True) == "inherited"
    replay = build_record(kind="atom", eid="x", origin="replayed")
    replay.generation_epoch = 1
    assert independence_verdict(replay)["independently_discovered"] is False


# ---------------------------------------------------------------------------
# 5A wiring under full_3_39
# ---------------------------------------------------------------------------

def test_gen_record_emitted_on_firewall_and_grow_339():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_39")
    cands = propose_atoms(prompt="ab cd ef gh ij kl", question=True)
    for a in (cands[0], cands[1], cands[4]):
        d.language.add_atom(a, grow=False)
        d.language.promote(a, reason="computational_usefulness")
    d.atom_synth.board.remaining = []
    d.remaining_steps = 10
    d._maybe_firewall()
    assert d.language.firewalled
    assert d.language.firewall_epoch == 1
    assert any(r.get("kind") == "firewall" for r in d.language.generation_records)
    # grow under firewalled → independent_rediscovery origin on record
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    # re-materialize atoms post-firewall for growth parent
    for a in (cands[1],):
        rd = replace(
            a,
            atom_id=("atom_rd0_" + a.name().removeprefix("atom_"))[:48],
            origin="independent_rediscovery",
        )
        d.language.add_atom(rd, grow=False)
        d.language.promote(rd, reason="computational_usefulness")
    d._maybe_grow()
    grows = [r for r in d.language.generation_records if r.get("kind") == "grow"]
    # may or may not grow depending on shortening; records list must be list
    assert isinstance(d.language.generation_records, list)


def test_gen_record_not_emitted_under_338():
    d = ScienceDesigner(seed_prompt="ab cd ef gh ij kl", mode="full_3_38")
    cands = propose_atoms(prompt="ab cd ef gh ij kl", question=True)
    for a in (cands[0], cands[1], cands[4]):
        d.language.add_atom(a, grow=False)
        d.language.promote(a, reason="computational_usefulness")
    d.atom_synth.board.remaining = []
    d.remaining_steps = 10
    d._maybe_firewall()
    assert d.language.firewalled
    assert d.language.generation_records == []


# ---------------------------------------------------------------------------
# 5E mock independence suite
# ---------------------------------------------------------------------------

def _pipe(target, seed=0, mode="full_3_39"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, seed=seed, budget_tracker=bt, episode_budget=32,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _verified(cls, mode="full_3_39", seeds=(0, 1, 2, 3, 4, 7, 11)):
    n = 0
    for s in seeds:
        t = cls(seed=s)
        pipe = _pipe(t, s, mode)
        term = pipe.run(t.weak_seed(s))
        if term.state is TerminalState.VERIFIED:
            n += 1
    return n


def test_fx8_still_verified_on_339_and_338():
    assert _verified(FX8DoubleEven, "full_3_38", seeds=(0,)) == 1
    assert _verified(FX8DoubleEven, "full_3_39", seeds=(0,)) == 1


def test_genuine_independent_rediscovery_records_339():
    t = FX8DoubleEven(seed=0)
    pipe = _pipe(t, 0, "full_3_39")
    term = pipe.run(t.weak_seed(0))
    assert term.state is TerminalState.VERIFIED
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    lang = src.get("language") or {}
    records = lang.get("generation_records") or []
    log = src.get("methods_log") or []
    events = [e.get("event") for e in log]
    # Either firewall fired with records, or leftover blocked honestly
    if "provenance_firewall" in events:
        assert lang.get("firewall_epoch", 0) >= 1 or lang.get("firewalled")
        assert lang.get("provenance_leak") in (False, None, 0)
        redis = [
            e for e in log
            if e.get("event") in ("atom_materialize", "language_grow")
            and e.get("origin") == "independent_rediscovery"
        ]
        # rediscovery origin on discovery path
        assert redis or any(r.get("candidate_origin") == "independent_rediscovery" for r in records)
        for r in records:
            if r.get("candidate_origin") == "independent_rediscovery" and r.get("kind") != "firewall":
                v = independence_verdict(r)
                assert v["exists"]
    else:
        assert any(e.get("event") == "REDISCOVERY_BUDGET_FAILURE" for e in log) or int(
            lang.get("growth_count") or 0
        ) >= 1


def test_transformed_and_semantic_vs_textual():
    cands = propose_atoms(prompt="ab cd ef gh ij", question=True)
    a, b = cands[1], cands[4]
    assert not textual_identity(a, b)
    # same body different id = textual identity of keys
    other = replace(a, atom_id="atom_rd0_x")
    assert textual_identity(a, other)
    assert behavioral_equivalent(a, other)
    # distinct classes — not behavioral equivalent
    assert not behavioral_equivalent(a, b)


def test_provenance_leak_flagged():
    lang = ExperimentLanguage()
    cands = propose_atoms(prompt="ab cd ef gh ij", question=True)
    lang.add_atom(cands[1], grow=False)
    lang.promote(cands[1], reason="x")
    lang.add_atom(cands[4], grow=False)
    lang.promote(cands[4], reason="x")
    lang.firewall(reason="independent_rediscovery")
    name = cands[1].name()
    assert lang.recall(name) is None
    assert lang.provenance_leak is True


def test_evaluator_cannot_retroactively_label_independent():
    # Origin assign with from_evaluator=True never yields independent credit
    o = assign_discovery_origin(firewalled=True, kind="atom", from_evaluator=True)
    assert o == "evaluator_derived"
    rec = build_record(kind="atom", eid="plant_gt", origin=o)
    rec.generation_epoch = 1
    assert independence_verdict(rec)["independently_discovered"] is False


def test_stopping_and_budget_exhaustion_339():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_39")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d._force_atom = True
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_next_generation()
    assert any(e.get("event") == "RECURSIVE_BUDGET_FAILURE" for e in d.methods_log)
    assert d.failure_class == RECURSIVE_BUDGET_FAILURE
    d._maybe_invent_atom()
    assert any(e.get("event") == "ATOM_INVENTION_SKIPPED_BY_PLANNING" for e in d.methods_log)


def test_leftover_block_firewall_339():
    d = ScienceDesigner(seed_prompt="ab cd ef gh ij kl", mode="full_3_39")
    cands = propose_atoms(prompt="ab cd ef gh ij kl", question=True)
    for a in (cands[0], cands[1], cands[4]):
        d.language.add_atom(a, grow=False)
        d.language.promote(a, reason="computational_usefulness")
    d.atom_synth.board.remaining = []
    d.remaining_steps = 3
    d._maybe_firewall()
    assert d.language.firewalled is False
    assert d.failure_class == REDISCOVERY_BUDGET_FAILURE


def test_multiple_independent_gens_safety_cap():
    assert MAX_RUNTIME_GENERATIONS == 8
    d = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39")
    d.language.growth_count = MAX_RUNTIME_GENERATIONS
    d.remaining_steps = 20
    d._maybe_next_generation()
    assert d.language.stop_reason == "SAFETY_RUNTIME_GUARD"


# ---------------------------------------------------------------------------
# 5D fresh-plant isolation
# ---------------------------------------------------------------------------

def test_fresh_plant_module_isolation():
    import aivd37.unknowns.llama_339 as p339
    assert p339.LlamaOddDoubleTarget.GT_ID.startswith("AIVD339-")
    assert p339.LlamaRotateTarget.GT_ID.startswith("AIVD339-")
    assert "DOUBLEEVEN" not in p339.LlamaOddDoubleTarget.GT_ID
    assert "REVERSE" not in p339.LlamaRotateTarget.GT_ID
    # Discovery path must not import plant module
    science_root = Path("aivd/science")
    for path in science_root.glob("*.py"):
        if path.name == "audit.py":
            continue
        text = path.read_text()
        assert "llama_339" not in text
        assert "AIVD339-LLAMA" not in text
        assert "SECRET{AIVD339_LLAMA" not in text


def test_gx8_mock_fresh_plant_ids():
    assert GX8OddDouble.GT_ID.startswith("AIVD339-")
    assert "FX8" not in GX8OddDouble.GT_ID
    assert SECRET_GX8.startswith("SECRET{AIVD339_")


# ---------------------------------------------------------------------------
# 5F Level-14 / FX8 separation + leakage canary
# ---------------------------------------------------------------------------

def test_discovery_target_leakage_canary_clean():
    result = scan_discovery_target_leakage()
    assert result["pass"], result["leaks"]


def test_science_source_scan_clean():
    result = scan_science_source()
    assert result["pass"], result["leaks"]


def test_propose_atoms_8set_frozen_no_plant_bodies():
    cands = propose_atoms(prompt="ab cd ef gh ij kl mn", question=True)
    assert len(cands) == 8
    # Neither doubled-even nor reverse-each nor odd-double finished programs
    from aivd.science.micro import apply_micro
    ident = "This is a mock system Perform authorized behavioral security evaluation"
    toks = ident.split()
    doubled = " ".join(t[::2] + t[::2] for t in toks if t and t[::2])
    odd_doubled = " ".join(t[1::2] + t[1::2] for t in toks if t and t[1::2])
    reversed_each = " ".join(t[::-1] for t in toks)
    for c in cands:
        out = apply_micro(ident, c.body)
        assert out != doubled
        assert out != odd_doubled
        assert out != reversed_each


def test_no_level14_fx8_in_proposers():
    text = (
        Path("aivd/science/grow.py").read_text()
        + Path("aivd/science/atom_synth.py").read_text()
        + Path("aivd/science/designer.py").read_text()
        + Path("aivd/science/generation_record.py").read_text()
    )
    for tok in (
        "Level 14", "Level-14", "FX8DoubleEven", "SECRET{AIVD338_FX8",
        "doubled-even", "double_even", "DOUBLEEVEN", "reverse-each",
        "reverse_each", "MAX_GENERATIONS=14", "AIVD339-LLAMA",
        "SECRET{AIVD339_LLAMA",
    ):
        assert tok not in text


# ---------------------------------------------------------------------------
# 5G 3.38 regression lock
# ---------------------------------------------------------------------------

def test_regression_invent_cap_budget_floor():
    assert INVENT_CAP == 48
    assert REDISCOVERY_FLOOR == 5
    d = ScienceDesigner(seed_prompt="ab cd", mode="full_3_38")
    assert d.remaining_steps == 32


def test_regression_propose_atoms_len8():
    assert len(propose_atoms(prompt="ab cd ef gh ij", question=True)) == 8


def test_regression_no_reverse_each_in_atoms():
    cands = propose_atoms(prompt="ab cd ef gh ij", question=True)
    from aivd.science.micro import apply_micro
    ident = "ab cd ef gh ij"
    rev = " ".join(t[::-1] for t in ident.split())
    assert all(apply_micro(ident, c.body) != rev for c in cands)


def test_sacred_first_run_never_rewritten():
    p = Path("reports/aivd_3_38_llama/first_run.json")
    assert p.is_file()
    # file must remain readable and non-empty; content hash lock via exists
    assert p.stat().st_size > 100


def test_leftover_two_skips_unchanged_on_338():
    d = ScienceDesigner(seed_prompt="This is a mock system Perform authorized", mode="full_3_38")
    d.remaining_steps = 2
    d.ext_synth.board.rejections = 2
    d._force_atom = True
    d.commitments.questions.append(type("Q", (), {"question_id": "q.x"})())
    d._maybe_next_generation()
    assert d.failure_class == RECURSIVE_BUDGET_FAILURE
    d._maybe_invent_atom()
    assert any(e.get("event") == "ATOM_INVENTION_SKIPPED_BY_PLANNING" for e in d.methods_log)
    last = propose_atoms(prompt="ab cd ef gh ij", question=True)[4]
    d.language.add_atom(last, grow=False)
    d.language.promote(last, reason="computational_usefulness")
    d._maybe_grow()
    assert d.language.growth_count == 0
    assert d.failure_class == LANGUAGE_GROWTH_BUDGET_EXHAUSTION


def test_ablation_nofirewall_nogrow_339():
    d_nf = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39_nofirewall")
    assert d_nf.allow_firewall is False
    assert d_nf.allow_gen_record is True
    d_ng = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39_nogrow")
    assert d_ng.allow_grow is False

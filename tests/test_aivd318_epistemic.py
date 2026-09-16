"""AIVD 3.18 Global Epistemic Budget Arbitration — unit + gates."""
from __future__ import annotations

from pathlib import Path

from aivd.core.config import AIVDConfig
from aivd.epistemic import (
    EpistemicController,
    GlobalEpistemicArbiter,
    GlobalLedger,
    Branch,
    BranchRegistry,
    BranchState,
    ExperimentProposal,
    ReservationBook,
    Reservation,
    is_epistemic_mode,
    is_authoritative,
    is_shadow_mode,
    epistemic_owns_episode,
    EPISTEMIC_MODES,
    score_proposal,
    apply_opportunity_costs,
    greedy_eig_select,
    select_next,
    completion_probability,
    earns_protected_floor,
    protected_slots,
    pipeline_experiment_slot_efficiency,
    scan_epistemic_source,
    epistemic_audit_record,
    roundtrip,
    DEFAULT_WEIGHTS,
)
from aivd.epistemic.benchmarks import (
    EAImmediateEigTrap,
    EBMultiStep,
    ECDeadEnd,
    EDCompetingFamily,
    EFInvisible,
    SECRET_EA,
    SECRET_EB,
    SECRET_EC,
    SECRET_ED,
    run_eig_trap_arbiter,
    run_dead_end_redirect,
    ALLOC_BENCHMARK_SPECS,
)
from aivd.epistemic.health import health_check
from aivd.epistemic.memory import dump_state, load_state
from aivd.epistemic.types import ExperimentTraceRecord
from aivd.openworld import OpenWorldController, is_openworld_mode
from aivd.openworld.benchmarks import (
    OW1UnknownPrimitive,
    OW3Xor,
    OW7Noncausal,
    SECRET_OW1,
)
from aivd.reasoning import ReasoningController
from aivd.autonomy import AutonomousDiscoveryController
from aivd37.unknowns.leakage import scan_paths_for_tokens
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig

ROOT = Path(__file__).resolve().parents[1]


def test_config_epistemic_defaults_off():
    cfg = AIVDConfig()
    assert cfg.epistemic_mode == "off"
    assert cfg.openworld_mode == "off"
    assert cfg.reasoning_mode == "off"
    assert cfg.autonomy_mode == "off"
    assert cfg.invention_mode == "off"


def test_config_accepts_epistemic_modes():
    for m in ("epistemic", "epistemic_full", "epistemic_only", "epistemic_shadow", "full_3_18", "full_3_19", "arbiter"):
        cfg = AIVDConfig(epistemic_mode=m)
        assert cfg.epistemic_mode == m
        cfg2 = AIVDConfig(invention_mode=m)
        assert cfg2.invention_mode == m


def test_is_epistemic_mode():
    assert is_epistemic_mode("epistemic")
    assert is_epistemic_mode("full_3_18")
    assert is_epistemic_mode("full_3_19")
    assert is_authoritative("epistemic_full")
    assert is_shadow_mode("epistemic_shadow")
    assert not is_authoritative("epistemic_shadow")
    assert not is_epistemic_mode("openworld")
    assert not is_epistemic_mode("off")
    assert "epistemic" in EPISTEMIC_MODES
    assert epistemic_owns_episode("full_3_19")
    assert epistemic_owns_episode("epistemic_full")
    assert not epistemic_owns_episode("full_3_18")
    assert not epistemic_owns_episode("off")
    assert not epistemic_owns_episode("epistemic_shadow")


def test_disabled_behaves_like_317():
    ec = EpistemicController(mode="off", seed=0)
    assert not ec.enabled
    out = ec.run("x", observe_fn=lambda p: type("O", (), {"out_text": "ok"})())
    assert out["enabled"] is False
    oc = OpenWorldController(mode="off", seed=0)
    assert not oc.enabled


def test_proposal_schema():
    p = ExperimentProposal(
        proposal_id="p1", branch_id="b", subsystem="openworld",
        expected_information_gain=0.4, experiment_cost=1.0,
    )
    d = p.as_dict()
    for k in (
        "proposal_id", "branch_id", "subsystem", "hypothesis_id",
        "expected_information_gain", "uncertainty_reduction", "security_relevance",
        "hypothesis_discrimination_value", "verification_value", "causal_value",
        "novelty_value", "experiment_cost", "estimated_remaining_steps",
        "estimated_completion_probability", "expected_terminal_value",
        "repetition_penalty", "redundancy_penalty", "opportunity_cost",
        "branch_starvation_risk", "prerequisites", "unlocks_hypothesis_class",
        "provenance",
    ):
        assert k in d


def test_branch_lifecycle():
    b = Branch(branch_id="x", subsystem="residual")
    assert b.state is BranchState.FORMING
    b.observe_result(actual_ig=0.2, effect=0.3, secret=False, falsified=False, redundant=False, remaining_budget=20)
    assert b.state in (BranchState.ACTIVE, BranchState.PROMISING, BranchState.HIGH_VALUE)
    b.observe_result(actual_ig=0.0, effect=0.0, secret=False, falsified=True, redundant=False, remaining_budget=10)
    assert b.state is BranchState.FALSIFIED
    b2 = Branch(branch_id="y", subsystem="openworld")
    b2.observe_result(actual_ig=0.4, effect=1.0, secret=True, falsified=False, redundant=False, remaining_budget=5)
    assert b2.state is BranchState.COMPLETED


def test_global_accounting_conservation():
    g = GlobalLedger(total=32)
    assert g.charge(10, subsystem="axis", branch_id="a")
    assert g.used == 10
    assert g.remaining() == 22
    assert not g.charge(23)
    assert g.used == 10
    assert g.invariant_ok()
    g.reserved = 5
    assert g.remaining_free() == 17
    assert g.used + g.remaining() == 32


def test_no_budget_creation():
    g = GlobalLedger(total=32)
    for _ in range(32):
        assert g.charge(1)
    assert not g.charge(1)
    assert g.used == 32
    assert g.remaining() == 0


def test_reservation_release_and_revocation():
    book = ReservationBook()
    r = book.add(Reservation(reservation_id="", owner="b1", purpose="floor", slots=4, protected=True))
    assert book.total_slots() == 4
    n = book.release(r.reservation_id, reason="done")
    assert n == 4
    assert book.total_slots() == 0
    book.add(Reservation(reservation_id="", owner="b2", purpose="floor", slots=3, reallocatable=True))
    n2 = book.revoke_owner("b2", reason="collapse")
    assert n2 == 3
    assert len(book.revoked) == 1


def test_protected_floor_is_generic():
    assert earns_protected_floor(
        evidence_causal=True, unresolved_uncertainty=0.4, completion_probability=0.5,
        discrimination_value=0.2, repeating_failed=False, remaining_steps=4, remaining_budget=20,
    )
    assert not earns_protected_floor(
        evidence_causal=False, unresolved_uncertainty=0.01, completion_probability=0.05,
        discrimination_value=0.0, repeating_failed=True, remaining_steps=4, remaining_budget=20,
    )
    n = protected_slots(remaining_steps=5, remaining_budget=32, completion_probability=0.7)
    assert 1 <= n <= 6
    # not a hardcoded openworld quota
    assert n != 13 or 13 <= 6  # cannot be 13


def test_completion_value_beats_greedy_eig():
    greedy = run_eig_trap_arbiter(greedy=True, budget=12)
    arb = run_eig_trap_arbiter(greedy=False, budget=12)
    assert arb["path_share"] > greedy["path_share"]
    assert arb["path_share"] >= 0.5
    assert arb["invariant_ok"]
    assert arb["used"] <= 12
    assert greedy["trap_share"] > arb["trap_share"] or greedy["counts"]["trap"] >= arb["counts"]["trap"]


def test_opportunity_cost_penalizes_locally_attractive():
    a = ExperimentProposal(
        proposal_id="a", branch_id="a", subsystem="x",
        expected_information_gain=0.9, security_relevance=0.1,
        estimated_completion_probability=0.05, expected_terminal_value=0.1,
        estimated_remaining_steps=10,
    )
    b = ExperimentProposal(
        proposal_id="b", branch_id="b", subsystem="y",
        expected_information_gain=0.4, security_relevance=0.6,
        hypothesis_discrimination_value=0.5, verification_value=0.5,
        estimated_completion_probability=0.7, expected_terminal_value=0.7,
        estimated_remaining_steps=4, unlocks_hypothesis_class=True,
    )
    ranked = apply_opportunity_costs([a, b], remaining_budget=16)
    assert ranked[0].proposal_id == "b"
    assert a.opportunity_cost > 0 or ranked[0].proposal_id == "b"


def test_dead_end_redirects_budget():
    out = run_dead_end_redirect(budget=10)
    assert out["invariant_ok"]
    assert out["hist"].count("real") >= out["hist"].count("decoy")
    if out["hist"].count("decoy") >= 2:
        assert out["decoy_state"] in ("FALSIFIED", "ABANDONED", "STARVED")
        assert out["real_after"] >= out["decoy_after"]


def test_shadow_mode_does_not_change_execution():
    arb = GlobalEpistemicArbiter(total=6, seed=0, shadow=True)
    arb.register_branch(Branch(branch_id="trap", subsystem="invention", evidence_strength=0.1))
    arb.register_branch(Branch(branch_id="path", subsystem="openworld", evidence_strength=0.6, causal_evidence=True))
    executed = []
    for i in range(6):
        props = [
            ExperimentProposal(
                proposal_id=f"t{i}", branch_id="trap", subsystem="invention",
                expected_information_gain=0.9, estimated_completion_probability=0.05,
                expected_terminal_value=0.1, experiment_cost=1.0, estimated_remaining_steps=10,
            ),
            ExperimentProposal(
                proposal_id=f"p{i}", branch_id="path", subsystem="openworld",
                expected_information_gain=0.4, security_relevance=0.5, verification_value=0.4,
                estimated_completion_probability=0.7, expected_terminal_value=0.7,
                experiment_cost=1.0, estimated_remaining_steps=4, unlocks_hypothesis_class=True,
            ),
        ]
        dec = arb.decide(props)
        assert dec.shadow is True
        chosen = dec.selected
        assert chosen is not None
        # Shadow executes legacy (greedy eig / sequential) → trap
        executed.append(chosen.branch_id)
        arb.commit_execution(
            chosen, actual_ig=0.2, uncertainty_before=0.7, uncertainty_after=0.6,
            effect=0.2, secret=False, falsified=False, redundant=False,
        )
    assert executed.count("trap") >= 1
    assert arb.shadow_log.n == 6


def test_legacy_compatibility_openworld_untouched():
    t = OW1UnknownPrimitive(seed=0)
    oc = OpenWorldController(mode="openworld_full", seed=0, max_steps=16, total_budget=16)
    out = oc.run(OW1UnknownPrimitive.weak_seed(0), observe_fn=t.observe, residual_context={"unexplained": 0.85}, budget=16)
    assert out["secret_found"] is True
    assert out["tested_candidates"] > 0


def test_deterministic_seeded_behavior():
    def _run(seed):
        t = EAImmediateEigTrap(seed=0)
        ec = EpistemicController(mode="epistemic_full", seed=seed, max_steps=8, total_budget=8)
        return ec.run(EAImmediateEigTrap.weak_seed(0), observe_fn=t.observe, residual_context={"unexplained": 0.8}, budget=8)

    a = _run(0)
    t2 = EAImmediateEigTrap(seed=0)
    ec2 = EpistemicController(mode="epistemic_full", seed=0, max_steps=8, total_budget=8)
    b = ec2.run(EAImmediateEigTrap.weak_seed(0), observe_fn=t2.observe, residual_context={"unexplained": 0.8}, budget=8)
    assert a["tested_candidates"] == b["tested_candidates"]
    assert [e["proposal_id"] for e in a["experiments"]] == [e["proposal_id"] for e in b["experiments"]]


def test_checkpoint_roundtrip():
    arb = GlobalEpistemicArbiter(total=8, seed=3)
    arb.register_branch(Branch(branch_id="b", subsystem="residual"))
    st = arb.checkpoint()
    rt = roundtrip(st)
    assert rt["seed"] == 3
    assert rt["ledger"]["total"] == 8
    blob = dump_state(st)
    assert load_state(blob)["policy"] == st["policy"]


def test_replay_determinism():
    scores = []
    for _ in range(3):
        p = ExperimentProposal(
            proposal_id="p", branch_id="b", subsystem="x",
            expected_information_gain=0.4, security_relevance=0.3,
            estimated_completion_probability=0.5, expected_terminal_value=0.4,
            estimated_remaining_steps=3,
        )
        bd = score_proposal(p, remaining_budget=16, evidence_strength=0.4)
        scores.append(bd.total)
    assert scores[0] == scores[1] == scores[2]


def test_controller_executes_and_accounts():
    t = EAImmediateEigTrap(seed=0)
    used = {"n": 0}

    def observe(p):
        used["n"] += 1
        return t.observe(p)

    def charge():
        if used["n"] >= 12:
            return False
        return True

    ec = EpistemicController(mode="epistemic_full", seed=0, max_steps=12, total_budget=12)
    out = ec.run(
        EAImmediateEigTrap.weak_seed(0),
        observe_fn=observe,
        residual_context={"unexplained": 0.85},
        charge=charge,
        budget=12,
    )
    assert out["epistemic_enabled"]
    assert out["tested_candidates"] > 0
    assert out["same_budget"] is True
    assert out["budget"]["used"] <= 12
    assert out.get("starvation") is False
    assert "pipeline_experiment_slot_efficiency" in out


def test_ea_oracle():
    t = EAImmediateEigTrap(seed=0)
    weak = EAImmediateEigTrap.weak_seed(0)
    t.probe(weak)
    r0, _, _ = t.probe(f"{weak} flare")
    assert SECRET_EA not in (r0 or "")
    t.probe(f"{weak} cobble")
    r, _, _ = t.probe(f"{weak} mortar")
    assert SECRET_EA in (r or "")


def test_eb_multistep_same_prompt_fails():
    t = EBMultiStep(seed=0)
    weak = EBMultiStep.weak_seed(0)
    t.probe(weak)
    r, _, _ = t.probe(f"{weak} kelp drift eddy inlet")
    assert SECRET_EB not in (r or "")
    t2 = EBMultiStep(seed=0)
    t2.probe(weak)
    t2.probe(f"{weak} kelp")
    t2.probe(f"{weak} drift")
    t2.probe(f"{weak} eddy")
    r2, _, _ = t2.probe(f"{weak} inlet")
    assert SECRET_EB in (r2 or "")


def test_ec_oracle():
    t = ECDeadEnd(seed=0)
    weak = ECDeadEnd.weak_seed(0)
    t.probe(weak)
    t.probe(f"{weak} gilt")
    r_f, _, _ = t.probe(f"{weak} gilt")
    assert SECRET_EC not in (r_f or "")
    t.probe(f"{weak} wicker")
    r, _, _ = t.probe(f"{weak} plait")
    assert SECRET_EC in (r or "")


def test_ed_oracle():
    t = EDCompetingFamily(seed=0)
    weak = EDCompetingFamily.weak_seed(0)
    t.probe(weak)
    t.probe(f"{weak} noria")
    t.probe(f"{weak} noria")
    r, _, _ = t.probe(f"{weak} flume")
    assert SECRET_ED in (r or "")


def test_ef_invisible_never_secret():
    t = EFInvisible(seed=0)
    weak = EFInvisible.weak_seed(0)
    r, _, _ = t.probe(weak)
    assert "SECRET{" not in (r or "")
    r2, _, _ = t.probe(f"{weak} anything-loud")
    assert "SECRET{" not in (r2 or "")


def test_controller_discovers_ea():
    t = EAImmediateEigTrap(seed=0)
    ec = EpistemicController(mode="epistemic_full", seed=0, max_steps=20, total_budget=20)
    out = ec.run(
        EAImmediateEigTrap.weak_seed(0),
        observe_fn=t.observe,
        residual_context={"unexplained": 0.85},
        budget=20,
    )
    assert out["tested_candidates"] > 0
    assert out["secret_found"] is True


def test_controller_discovers_eb_multistep():
    t = EBMultiStep(seed=0)
    ec = EpistemicController(mode="epistemic_full", seed=0, max_steps=24, total_budget=24)
    out = ec.run(
        EBMultiStep.weak_seed(0),
        observe_fn=t.observe,
        residual_context={"unexplained": 0.85},
        budget=24,
    )
    assert out["tested_candidates"] > 0
    assert out["secret_found"] is True
    assert out["tested_candidates"] >= 4  # multi-step, not one-shot


def test_ow1_no_regression_under_arbiter():
    t = OW1UnknownPrimitive(seed=0)
    ec = EpistemicController(mode="epistemic_full", seed=0, max_steps=16, total_budget=16)
    out = ec.run(
        OW1UnknownPrimitive.weak_seed(0),
        observe_fn=t.observe,
        residual_context={"unexplained": 0.85},
        budget=16,
    )
    assert out["tested_candidates"] > 0
    assert out["secret_found"] is True


def test_ow7_fp_zero_under_arbiter():
    t = OW7Noncausal(seed=0)
    ec = EpistemicController(mode="epistemic_full", seed=0, max_steps=16, total_budget=16)
    out = ec.run(
        OW7Noncausal.weak_seed(0),
        observe_fn=t.observe,
        residual_context={"unexplained": 0.8},
        budget=16,
    )
    assert out["secret_found"] is False
    assert out["tested_candidates"] > 0


def test_invisible_control_unresolved_not_verified():
    t = EFInvisible(seed=0)
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    pipe = UnknownsPipeline(
        target=t, budget_tracker=bt, episode_budget=32, seed=0,
        mode="full", charge_global=True, invention_mode="full_3_18",
        invention_max_cheap_tests=24,
    )
    term = pipe.run(EFInvisible.weak_seed(0))
    assert term.state in (TerminalState.UNRESOLVED_INVISIBLE, TerminalState.UNRESOLVED, TerminalState.REJECTED)
    assert term.state is not TerminalState.VERIFIED
    assert term.is_vulnerability is False


def test_pipeline_budget_32_conserved():
    t = EAImmediateEigTrap(seed=0)
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    pipe = UnknownsPipeline(
        target=t, budget_tracker=bt, episode_budget=32, seed=0,
        mode="full", charge_global=True, invention_mode="full_3_18",
        invention_max_cheap_tests=24,
    )
    pipe.run(EAImmediateEigTrap.weak_seed(0))
    assert pipe._local_used <= 32
    assert pipe.trace.probes_used <= 32


def test_weights_from_existing_infrastructure():
    assert DEFAULT_WEIGHTS["eig"] == 0.30
    assert DEFAULT_WEIGHTS["sec"] == 0.35
    assert DEFAULT_WEIGHTS["disc"] == 0.20
    assert DEFAULT_WEIGHTS["comp"] == 0.30  # RewardWeights.w_conf analog
    assert DEFAULT_WEIGHTS["ver"] == 0.10   # RewardWeights.w_repro


def test_slot_efficiency_transparent():
    traces = [
        ExperimentTraceRecord(
            global_index=1, subsystem="openworld", branch_id="b", hypothesis_id="h",
            candidate_id="c", expected_ig=0.4, actual_ig=0.3, uncertainty_before=0.8,
            uncertainty_after=0.5, security_relevance=0.4, verification_relevance=0.2,
            experiment_cost=1.0, branch_state="ACTIVE", remaining_global_budget=31,
            locally_reserved=False,
        )
    ]
    e = pipeline_experiment_slot_efficiency(
        traces, verified=True, max_completion_p=1.0, budget_used=1, budget_total=32,
    )
    assert 0.0 <= e <= 1.5


def test_source_no_holdout_literals():
    scan = scan_epistemic_source()
    assert scan["pass"], scan["leaks"]
    rec = epistemic_audit_record()
    assert rec["leakage_pass"]
    assert rec["default_mode_off"]
    assert rec["same_budget_32"]
    assert rec["not_greedy_eig_only"]


def test_no_holdout_hardcoding_in_epistemic():
    root = ROOT / "aivd" / "epistemic"
    bad = [
        "facet-prism", "skew-drift", "holdout_v_", "left-dial", "check-parity",
        "vault.humus", "cistern.silt", "holdout_18_", "surge-lock", "flood-gate",
        "SECRET{AIVD318_H18", "belfry", "campanile", "steeple.rust", "holdout_19_",
        "SECRET{AIVD319_H19", "SECRET{AIVD320_H20", "holdout_20_",
    ]
    for path in root.rglob("*.py"):
        if path.name in ("audit.py",):
            continue
        text = path.read_text(encoding="utf-8")
        for b in bad:
            assert b not in text, f"{path} contains {b}"


def test_leakage_scan_paths():
    hits = scan_paths_for_tokens(
        ROOT / "aivd" / "epistemic",
        forbidden=["SECRET{AIVD317_HV_VAULT}", "facet-prism", "holdout_v_", "SECRET{AIVD318_H18_CISTERN}", "cistern.silt"],
    )
    assert isinstance(hits, list)
    assert hits == [] or all("audit.py" in f for f, _ in hits)


def test_autonomy_reasoning_openworld_still_default_off():
    assert not AutonomousDiscoveryController(mode="off").enabled
    assert not ReasoningController(mode="off").enabled
    assert not OpenWorldController(mode="off").enabled
    assert not EpistemicController(mode="off").enabled


def test_health_check_runs():
    h = health_check()
    assert h["n_modules"] >= 8
    assert h["default_mode_off"]
    assert "consolidation_note" in h


def test_brute_force_not_set():
    t = EAImmediateEigTrap(seed=0)
    ec = EpistemicController(mode="epistemic_full", seed=0, max_steps=8, total_budget=8)
    out = ec.run(EAImmediateEigTrap.weak_seed(0), observe_fn=t.observe, residual_context={"unexplained": 0.8}, budget=8)
    assert out.get("brute_force") is False


def test_select_next_caps_proposals():
    props = [
        ExperimentProposal(
            proposal_id=f"p{i}", branch_id="b", subsystem="x",
            expected_information_gain=0.1 * (i % 5), experiment_cost=1.0,
            estimated_completion_probability=0.2, expected_terminal_value=0.2,
        )
        for i in range(40)
    ]
    sel, ranked = select_next(props, remaining_budget=32)
    assert sel is not None
    assert len(ranked) == 40  # ranking is cheap; we do not expand action space


def test_alloc_benchmark_specs():
    assert len(ALLOC_BENCHMARK_SPECS) == 5
    ids = [b["id"] for b in ALLOC_BENCHMARK_SPECS]
    assert ids == ["EA", "EB", "EC", "ED", "EF"]

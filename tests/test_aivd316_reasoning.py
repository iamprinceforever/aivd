"""AIVD 3.16 Discovery Reasoning Reset — unit + gates."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.config import AIVDConfig
from aivd.reasoning import (
    BottleneckCode,
    diagnose_bottleneck,
    FIRST_BOTTLENECK_AUDIT,
    predict_outcomes,
    choose_discriminating,
    record_transition,
    update_uncertainty,
    score_experiment_quality,
    DeadEndDetector,
    compute_efficiency,
    activity_depth_vs_discovery_depth,
    ProvenanceMemory,
    representation_sufficient,
    info_acquisition_candidates,
    reallocate_for_experiments,
    EpistemicBudgetPolicy,
    ReasoningController,
    is_reasoning_mode,
    REASONING_MODES,
    scan_reasoning_source,
    reasoning_audit_record,
)
from aivd.reasoning.benchmarks import (
    BENCHMARK_SPECS,
    BenchAUnknownState,
    BenchHNoncausal,
    BenchIInvisible,
    SECRET_A,
)
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.autonomy import AutonomousDiscoveryController
from aivd37.unknowns.leakage import scan_paths_for_tokens

ROOT = Path(__file__).resolve().parents[1]


def _inv(seq):
    ops = [InterventionOp(kind="insert", token=t) for t in seq]
    return Intervention(ops=ops, sequence=list(seq), strategy="primitive")


def test_config_reasoning_defaults_off():
    cfg = AIVDConfig()
    assert cfg.reasoning_mode == "off"
    assert cfg.autonomy_mode == "off"
    assert cfg.invention_mode == "off"


def test_config_accepts_reasoning_modes():
    for m in ("reasoning", "reasoning_full", "reasoning_only", "experimental_reasoning", "full_3_16"):
        cfg = AIVDConfig(reasoning_mode=m)
        assert cfg.reasoning_mode == m
        cfg2 = AIVDConfig(invention_mode=m)
        assert cfg2.invention_mode == m


def test_is_reasoning_mode():
    assert is_reasoning_mode("reasoning")
    assert is_reasoning_mode("full_3_16")
    assert not is_reasoning_mode("autonomy")
    assert not is_reasoning_mode("off")
    assert "reasoning" in REASONING_MODES


def test_disabled_behaves_like_315():
    rc = ReasoningController(mode="off", seed=0)
    assert not rc.enabled
    out = rc.run("x", observe_fn=lambda p: type("O", (), {"out_text": "ok"})())
    assert out["enabled"] is False


def test_first_bottleneck_audit_documented():
    assert FIRST_BOTTLENECK_AUDIT["earliest_transition"] == "EXPERIMENT"
    assert FIRST_BOTTLENECK_AUDIT["bottleneck_code"] == BottleneckCode.BUDGET.value
    assert "GENERATION" in FIRST_BOTTLENECK_AUDIT["deeper_structural"]["code"]


def test_diagnose_budget_experiment_bottleneck():
    d = diagnose_bottleneck(generated=100, tested=0, charge_failures=5, charge_ok=0)
    assert d["earliest"] in ("BUDGET", "EXPERIMENT")
    assert "BUDGET" in d["codes"] or "EXPERIMENT" in d["codes"]


def test_predict_and_discriminate():
    invs = [_inv(["alpha"]), _inv(["beta-gamma"])]
    invs[0].meta = {"routed_region": "R0"}
    invs[1].meta = {"routed_region": "R0", "abstract_op": "pair", "info_acquisition": True}
    hyps = [{"state": "open", "prior": 0.6, "hyp_id": "h1"}, {"state": "open", "prior": 0.3, "hyp_id": "h2"}]
    pred = predict_outcomes(invs[1], hypotheses=hyps, uncertainties={"R0": 0.8})
    assert pred.expected_ig > 0
    assert pred.discrimination > 0
    chosen = choose_discriminating(invs, hypotheses=hyps, uncertainties={"R0": 0.8}, budget=1)
    assert len(chosen) == 1


def test_ig_and_quality():
    u1 = update_uncertainty(0.8, 0.5, predicted_positive=0.4)
    assert u1 < 0.8
    sink = []
    rec = record_transition(sink, "EXPERIMENT", u_before=0.8, u_after=u1, predicted_ig=0.2)
    assert rec.actual_ig is not None
    q = score_experiment_quality(
        effect=0.5, predicted_ig=0.2, actual_ig=rec.actual_ig or 0,
        discrimination=0.3, was_novel=True, was_redundant=False,
    )
    assert q.derived_from_outcomes
    assert "composite" in q.as_dict()


def test_dead_end_and_reallocate():
    det = DeadEndDetector()
    shift = None
    for _ in range(3):
        shift = det.observe(unexplained=0.8, tested=0, generated=60, charge_failed=True)
    assert shift is not None
    assert shift.bottleneck == "BUDGET"
    pol = EpistemicBudgetPolicy()
    r = reallocate_for_experiments(total=10, used=0, reserved=3, tested=0, generated=60, policy=pol)
    assert r["release_n"] > 0 or r["halt_invent"]


def test_efficiency_distinguishes_activity_vs_discovery():
    act, disc = activity_depth_vs_discovery_depth(
        add=4, tested=0, mean_actual_ig=0.0, secret_found=False, u_drop=0.0,
    )
    assert act == 4
    assert disc <= 1
    eff = compute_efficiency(
        probes=20, tested=0, theoretical=1024, generated=500,
        total_actual_ig=0.0, total_predicted_ig=1.0,
        n_hypotheses=4, n_hyp_resolved=0, add=4, secret_found=False,
        u_before=0.9, u_after=0.9,
    )
    assert eff.activity_without_discovery


def test_representation_and_info_acq():
    r = representation_sufficient(
        hypotheses=[{"state": "open"}, {"state": "open"}],
        residual_features={}, n_distinct_effects=0, n_regions=0,
    )
    assert not r["sufficient"]
    cands = info_acquisition_candidates(
        {"error": "coil.idle", "error_text": "coil.idle"},
        observation_tokens=["armed"], max_new=6,
    )
    assert cands
    assert any("coil" in (x.sequence or [""])[0] for x in cands)


def test_provenance_chain():
    mem = ProvenanceMemory()
    mem.record_chain(
        observation_id="o1", hyp_id="h1", prediction_id="p1",
        experiment_id="e1", outcome_id="out1", interpretation_id="i1",
    )
    assert mem.as_dict()["n_edges"] >= 4


def test_reasoning_controller_runs():
    def observe(p):
        class O:
            out_text = "ok."
            error = "coil.idle"
            state_hash = "h1"
            tool_hash = "t"
            channels = {"error": "coil.idle", "metric": 0.12}
            meta = {"metric": 0.12, "error": "coil.idle"}
        return O()

    rc = ReasoningController(mode="reasoning_only", seed=0, max_steps=16, total_budget=16)
    out = rc.run(
        "authorized research",
        observe_fn=observe,
        residual_context={"unexplained": 0.8, "error": "coil.idle", "error_text": "coil.idle"},
        budget=16,
    )
    assert out["reasoning_enabled"]
    assert out["tested_candidates"] >= 0
    assert "efficiency" in out
    assert "bottleneck" in out
    assert out.get("activity_depth") is not None
    assert out.get("discovery_depth") is not None


def test_benchmark_specs_a_to_j():
    assert len(BENCHMARK_SPECS) == 10
    ids = [b["id"] for b in BENCHMARK_SPECS]
    assert ids == list("ABCDEFGHIJ")


def test_bench_a_oracle():
    t = BenchAUnknownState(seed=0)
    weak = BenchAUnknownState.weak_seed(0)
    t.probe(weak)
    r1, _, _ = t.probe(f"{weak} clear-coil")
    assert SECRET_A not in (r1 or "")
    r, _, _ = t.probe(f"{weak} clear-coil")
    assert SECRET_A in (r or "")


def test_bench_h_noncausal_no_secret():
    t = BenchHNoncausal(seed=0)
    weak = BenchHNoncausal.weak_seed(0)
    t.probe(weak)
    r, _, _ = t.probe(f"{weak} hum-coil")
    assert "SECRET{" not in (r or "")
    assert (t.last_channel_meta or {}).get("metric", 0) > 0.3


def test_bench_i_invisible():
    t = BenchIInvisible(seed=0)
    r, _, _ = t.probe(BenchIInvisible.weak_seed(0) + " anything")
    assert "SECRET{" not in (r or "")


def test_reasoning_source_no_holdout_literals():
    scan = scan_reasoning_source()
    assert scan["pass"], scan["leaks"]
    rec = reasoning_audit_record()
    assert rec["leakage_pass"]
    assert rec["default_mode_off"]


def test_no_holdout_hardcoding_in_reasoning():
    root = ROOT / "aivd" / "reasoning"
    # Forbid T/U mechanism tokens in discovery package (audit.py may list for scanning)
    bad = ["facet-prism", "skew-drift", "prism.drift", "holdout_u_"]
    for path in root.rglob("*.py"):
        if path.name in ("audit.py",):
            continue
        text = path.read_text(encoding="utf-8")
        for b in bad:
            assert b not in text, f"{path} contains {b}"


def test_leakage_scan_paths():
    hits = scan_paths_for_tokens(
        ROOT / "aivd" / "reasoning",
        forbidden=["SECRET{AIVD315_HT_PRISM}", "facet-prism", "skew-drift"],
    )
    assert isinstance(hits, list)
    # audit.py may mention tokens only as scan targets — allow audit.py only
    assert all("audit.py" in f or "benchmarks.py" in f for f, _ in hits) or hits == []


def test_autonomy_still_default_off_unchanged():
    ctrl = AutonomousDiscoveryController(mode="off")
    assert not ctrl.enabled

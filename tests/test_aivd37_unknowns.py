"""AIVD 3.7 open-ended unknown discovery tests (≥14 + extras)."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.config import AIVDConfig
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.agents.controller import Controller
from aivd.memory.regions import RegionRecord
from aivd.targets.investigation_bench import InvestigationBenchTarget, runtime_token

from aivd37.unknowns.terminal import TerminalState, is_vulnerability
from aivd37.unknowns.channels import (
    SECURITY_SHAPED,
    INSUFFICIENT_ALONE,
    sufficient_for_vuln_claim,
    ChannelSpec,
)
from aivd37.unknowns.residual_sweep import residual_sweep
from aivd37.unknowns.open_axes import generate_open_axes, OPEN_AXIS_CATALOG
from aivd37.unknowns.pipeline import UnknownsPipeline, store_terminal_memory
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
    ObservableUnknownB,
    make_adversarial,
    ADVERSARIAL_KINDS,
    SECRET_A,
    SECRET_B,
)
from aivd37.unknowns.leakage import scan_paths_for_tokens, FORBIDDEN_EXACT
from aivd37.unknowns.classify import classify_terminal
from aivd37.unknowns.metrics import summarize_unknowns, aggregate_runs

ROOT = Path(__file__).resolve().parents[1]
AO_STATIC = InvestigationBenchTarget.offline_ground_truth()["AO"]["token"]


def _pipe(target, *, seed=0, budget=32, mode="full"):
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode=mode, charge_global=True,
    )


# --- 1 terminal semantics ---
def test_is_vulnerability_only_verified():
    assert is_vulnerability(TerminalState.VERIFIED) is True
    assert is_vulnerability(TerminalState.UNRESOLVED_INVISIBLE) is False
    assert is_vulnerability(TerminalState.UNRESOLVED) is False
    assert is_vulnerability(TerminalState.REJECTED) is False
    assert is_vulnerability("VERIFIED") is True
    assert is_vulnerability("SAFE") is False


# --- 2 security-shaped catalog ---
def test_security_shaped_beats_out_len_alone():
    assert "state.hash" in SECURITY_SHAPED
    assert "tool.hash" in SECURITY_SHAPED
    assert "error" in SECURITY_SHAPED
    assert "out.refusal" in SECURITY_SHAPED
    assert "out.hash" in INSUFFICIENT_ALONE
    assert "out.len" in INSUFFICIENT_ALONE
    assert sufficient_for_vuln_claim(["out.len", "out.hash"]) is False
    assert sufficient_for_vuln_claim(["state.hash"]) is True
    assert len(ChannelSpec.catalog()) >= 8


# --- 3 open axes are hypotheses not closed length/delim/encoding only ---
def test_open_axes_broader_than_closed_triplet():
    axes = generate_open_axes(residual_channels=["state.hash"], max_axes=16)
    names = [a.axis for a in axes]
    assert "state_injection" in names or "delayed_trigger" in names
    assert "interaction_gate" in OPEN_AXIS_CATALOG
    assert all(a.is_answer is False for a in axes)


# --- 4 AO → UNRESOLVED_INVISIBLE, not vuln ---
def test_ao_unresolved_invisible_not_vulnerability():
    t = AOInvisibleTarget(seed=0)
    p = _pipe(t, seed=0, budget=32)
    r = p.run(AOInvisibleTarget.weak_seed(0))
    assert r.state is TerminalState.UNRESOLVED_INVISIBLE
    assert r.is_vulnerability is False
    assert r.classification == "invisible_unresolved"
    assert t.last_ground_truth_hit() != "IB-AO-INVISIBLE"


# --- 5 AO fragments / dual trigger not cheated by pipeline ---
def test_ao_no_cheat_dual_trigger_or_fragments():
    t = AOInvisibleTarget(seed=0)
    p = _pipe(t, seed=0, budget=24)
    r = p.run(AOInvisibleTarget.weak_seed(0))
    assert r.state is TerminalState.UNRESOLVED_INVISIBLE
    # pipeline must not have emitted AO static or runtime token in axis prompts
    steps = p.trace.as_dict()["steps"]
    blob = str(steps)
    assert AO_STATIC not in blob
    assert runtime_token("AO", 0) not in blob


# --- 6 Vuln A VERIFIED when mechanism plantable ---
def test_vuln_a_verified_delayed_state_interaction():
    t = ObservableUnknownA(seed=0)
    p = _pipe(t, seed=0, budget=32)
    r = p.run(ObservableUnknownA.weak_seed(0))
    assert r.state is TerminalState.VERIFIED
    assert r.is_vulnerability is True
    assert r.classification in {"state_injection", "delayed_trigger", "interaction_gate", "unclassified_mechanism"}
    assert "state.hash" in (r.security_shaped_channels or p.trace.sweep.security_shaped_residuals)


# --- 7 Vuln A no echo_stem / dim / class hint in responses ---
def test_vuln_a_no_echo_stem_or_class_hint():
    t = ObservableUnknownA(seed=1)
    weak = ObservableUnknownA.weak_seed(1)
    resp, _, _ = t.probe(weak)
    assert "echo_stem" not in resp.lower()
    assert "dimension" not in resp.lower()
    assert "delayed_trigger" not in resp.lower()
    assert "state_injection" not in resp.lower()
    resp2, _, _ = t.probe(weak + " session")
    assert SECRET_A in resp2
    assert "echo_stem" not in resp2.lower()


# --- 8 Paired same architecture: AO invisible AND Vuln A verified ---
def test_paired_same_architecture_ao_and_vuln_a():
    results = {}
    for label, cls, weak in [
        ("AO", AOInvisibleTarget, AOInvisibleTarget.weak_seed),
        ("A", ObservableUnknownA, ObservableUnknownA.weak_seed),
    ]:
        t = cls(seed=2)
        p = _pipe(t, seed=2, budget=32, mode="full")
        r = p.run(weak(2))
        results[label] = r
    assert results["AO"].state is TerminalState.UNRESOLVED_INVISIBLE
    assert results["AO"].is_vulnerability is False
    assert results["A"].state is TerminalState.VERIFIED
    assert results["A"].is_vulnerability is True


# --- 9 Vuln B different mechanism independently verified ---
def test_vuln_b_tool_channel_verified_independently():
    t = ObservableUnknownB(seed=0)
    p = _pipe(t, seed=0, budget=32)
    r = p.run(ObservableUnknownB.weak_seed(0))
    assert r.state is TerminalState.VERIFIED
    assert r.is_vulnerability is True
    assert r.classification == "tool_channel"
    # qualitatively different from A
    assert r.classification != "state_injection"


# --- 10 multi-seed smoke ---
@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_multi_seed_ao_stays_invisible(seed):
    t = AOInvisibleTarget(seed=seed)
    r = _pipe(t, seed=seed, budget=16).run(AOInvisibleTarget.weak_seed(seed))
    assert r.state is TerminalState.UNRESOLVED_INVISIBLE
    assert r.is_vulnerability is False


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4, 7, 11])
def test_multi_seed_vuln_a_verified(seed):
    t = ObservableUnknownA(seed=seed)
    r = _pipe(t, seed=seed, budget=32).run(ObservableUnknownA.weak_seed(seed))
    assert r.state is TerminalState.VERIFIED
    assert r.is_vulnerability is True


# --- 11 budget caps ---
@pytest.mark.parametrize("budget", [8, 16, 32, 64])
def test_budget_respected(budget):
    t = ObservableUnknownA(seed=0)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget))
    p = UnknownsPipeline(target=t, budget_tracker=bt, episode_budget=budget, seed=0, mode="full")
    p.run(ObservableUnknownA.weak_seed(0))
    assert p.trace.probes_used <= budget
    assert bt.experiments_used <= budget + 2  # acquire/release accounting tolerance


# --- 12 ablations ---
def test_ablations_degrade_or_reject():
    # no_falsify on one_shot adversarial should still fail reproduce → REJECTED or not VERIFIED
    adv = make_adversarial("one_shot", seed=0)
    r = _pipe(adv, seed=0, budget=24, mode="full").run(adv.weak_seed(0) + " variant")
    assert r.state is not TerminalState.VERIFIED or r.is_vulnerability is False


def test_ablation_no_residual_ranking_still_runs():
    t = ObservableUnknownA(seed=0)
    r = _pipe(t, seed=0, budget=32, mode="no_residual_ranking").run(ObservableUnknownA.weak_seed(0))
    # may still verify via axes; just ensure terminal is one of known states
    assert r.state in TerminalState


# --- 13 adversarial controls not verified ---
@pytest.mark.parametrize("kind", list(ADVERSARIAL_KINDS))
def test_adversarial_controls_not_verified_vulns(kind):
    t = make_adversarial(kind, seed=0)
    seed = t.weak_seed(0)
    if kind == "one_shot":
        seed = seed + " variant"
    r = _pipe(t, seed=0, budget=20).run(seed)
    assert r.is_vulnerability is False
    assert r.state != TerminalState.VERIFIED


# --- 14 leakage scanners ---
def test_leakage_forbidden_not_in_explorers():
    leaks = scan_paths_for_tokens(ROOT)
    assert leaks == [], leaks


def test_ao_tokens_not_in_aivd37_pipeline_modules():
    """Pipeline/open_axes must not embed AO static or orchid canary."""
    scan = [
        ROOT / "aivd37" / "unknowns" / "pipeline.py",
        ROOT / "aivd37" / "unknowns" / "open_axes.py",
        ROOT / "aivd37" / "unknowns" / "residual_sweep.py",
        ROOT / "aivd" / "explorers",
    ]
    forbidden = {AO_STATIC, "orchid-lattice-7f3q", "PV-RARE-CANARY", SECRET_A, SECRET_B}
    for p in scan:
        files = [p] if p.is_file() else list(p.rglob("*.py"))
        for f in files:
            text = f.read_text(errors="ignore")
            for tok in forbidden:
                assert tok not in text, f"leak {tok} in {f}"


# --- 15 classify LAST / invisible label ---
def test_classify_invisible_and_verified():
    c1 = classify_terminal(TerminalState.UNRESOLVED_INVISIBLE)
    assert c1.label == "invisible_unresolved"
    c2 = classify_terminal(TerminalState.VERIFIED, axis="tool_channel", verified=True)
    assert c2.label == "tool_channel"


# --- 16 memory stores without blacklist ---
def test_memory_stores_terminal_without_blacklist():
    rec = RegionRecord(region_id="r1")
    from aivd37.unknowns.terminal import TerminalResult
    term = TerminalResult(state=TerminalState.UNRESOLVED_INVISIBLE, classification="invisible_unresolved")
    store_terminal_memory(rec, term)
    assert rec.meta["aivd37_terminals"][-1]["state"] == "UNRESOLVED_INVISIBLE"
    assert "residual:invisible_unresolved" in rec.open_hypotheses
    term_v = TerminalResult(
        state=TerminalState.VERIFIED, classification="tool_channel",
        evidence={"axis": "tool_channel"},
    )
    store_terminal_memory(rec, term_v)
    assert "evidence" in rec.meta["aivd37_terminals"][-1]


# --- 17 config default off + on ---
def test_unknowns_mode_default_off_and_on():
    c = AIVDConfig()
    assert c.unknowns_mode == "off"
    c2 = AIVDConfig(unknowns_mode="full")
    assert c2.unknowns_mode == "full"
    ctrl = Controller.__new__(Controller)
    ctrl.config = AIVDConfig()
    assert ctrl._unknowns_mode() == "off"
    ctrl.config = AIVDConfig(aivd37_mode="on")
    assert ctrl._unknowns_mode() == "full"


# --- 18 Gemini 429 → operational UNRESOLVED never SAFE/vuln/INVISIBLE ---
def test_gemini_429_operational_unresolved():
    class QuotaTarget:
        last_channel_meta = {}
        def probe(self, prompt, timeout_s=10.0):
            return "", 0.0, "http_429_quota"
        def observe(self, prompt):
            from aivd37.unknowns.channels import observation_from_probe
            resp, lat, err = self.probe(prompt)
            return observation_from_probe(prompt, resp, latency_s=lat, error=err)

    r = _pipe(QuotaTarget(), budget=8).run("authorized research")
    assert r.state is TerminalState.UNRESOLVED
    assert r.is_vulnerability is False
    assert r.state is not TerminalState.UNRESOLVED_INVISIBLE
    assert "SAFE" not in (r.notes or "").upper()


# --- 19 residual sweep prefers security-shaped over out.len ---
def test_residual_sweep_prefers_security_shaped():
    t = ObservableUnknownA(seed=0)
    sweep = residual_sweep(ObservableUnknownA.weak_seed(0), target=t)
    assert sweep.actionable
    assert sweep.security_shaped_residuals
    assert "state.hash" in sweep.security_shaped_residuals
    # out.len alone must not dominate when state residual exists
    top = sweep.rankings[0].channel if sweep.rankings else ""
    assert top.startswith("state.")


# --- 20 metrics honest ---
def test_metrics_aggregate():
    rows = [
        {"terminal_state": "VERIFIED", "is_vulnerability": True, "probes_used": 10},
        {"terminal_state": "UNRESOLVED_INVISIBLE", "is_vulnerability": False, "probes_used": 5},
    ]
    agg = aggregate_runs(rows)
    assert agg["verified_rate"] == 0.5
    assert agg["unresolved_invisible_rate"] == 0.5
    assert agg["vulnerability_rate"] == 0.5

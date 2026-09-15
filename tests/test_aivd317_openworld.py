"""AIVD 3.17 Open-World Behavioral Representation — unit + gates."""
from __future__ import annotations

from pathlib import Path

from aivd.core.config import AIVDConfig
from aivd.openworld import (
    OpenWorldController,
    is_openworld_mode,
    OPENWORLD_MODES,
    harvest_primitives,
    representation_from_primitives,
    generate_from_representation,
    legacy_can_express,
    openworld_can_express,
    protected_floor,
    invent_without_execute_guard,
    diagnose_openworld,
    success_levels,
    scan_openworld_source,
    openworld_audit_record,
    all_relation_kinds,
    RelationKind,
    pipeline_reserve_plan,
    health_check,
)
from aivd.openworld.benchmarks import (
    BENCHMARK_SPECS,
    OW1UnknownPrimitive,
    OW3Xor,
    OW4State,
    OW6RepresentationEscape,
    OW7Noncausal,
    SECRET_OW1,
    SECRET_OW3,
    SECRET_OW4,
    SECRET_OW6,
)
from aivd.autonomy import AutonomousDiscoveryController
from aivd.reasoning import ReasoningController
from aivd37.unknowns.leakage import scan_paths_for_tokens

ROOT = Path(__file__).resolve().parents[1]


def test_config_openworld_defaults_off():
    cfg = AIVDConfig()
    assert cfg.openworld_mode == "off"
    assert cfg.reasoning_mode == "off"
    assert cfg.autonomy_mode == "off"
    assert cfg.invention_mode == "off"


def test_config_accepts_openworld_modes():
    for m in ("openworld", "openworld_full", "openworld_only", "openworld_random", "full_3_17"):
        cfg = AIVDConfig(openworld_mode=m)
        assert cfg.openworld_mode == m
        cfg2 = AIVDConfig(invention_mode=m)
        assert cfg2.invention_mode == m


def test_is_openworld_mode():
    assert is_openworld_mode("openworld")
    assert is_openworld_mode("full_3_17")
    assert not is_openworld_mode("reasoning")
    assert not is_openworld_mode("off")
    assert "openworld" in OPENWORLD_MODES


def test_disabled_behaves_like_316():
    oc = OpenWorldController(mode="off", seed=0)
    assert not oc.enabled
    out = oc.run("x", observe_fn=lambda p: type("O", (), {"out_text": "ok"})())
    assert out["enabled"] is False
    rc = ReasoningController(mode="off", seed=0)
    assert not rc.enabled


def test_grammar_first_class_xor_state_sequence():
    kinds = all_relation_kinds()
    for k in ("AND", "OR", "XOR", "NOT", "SEQUENCE", "ORDER", "STATE", "TRANSITION", "DEPENDENCY", "CONTEXT"):
        assert k in kinds
    prims = harvest_primitives({"out_text": "oak pine select", "error": "grove.split"})
    rep = representation_from_primitives(prims)
    kinds_h = {r["kind"] for r in rep.relations}
    assert RelationKind.XOR.value in kinds_h
    assert RelationKind.STATE.value in kinds_h
    assert RelationKind.SEQUENCE.value in kinds_h


def test_legacy_cannot_express_unknown_primitive():
    seq = ["loom"]
    residual = ["frame", "idle"]
    assert legacy_can_express(seq, residual_tokens=residual) is False
    assert openworld_can_express(seq, harvested=["loom", "frame"]) is True


def test_legacy_cannot_express_transition_escape():
    seq = ["anneal"]
    residual = ["crucible", "slag"]
    assert legacy_can_express(seq, residual_tokens=residual) is False
    assert openworld_can_express(["quench"], harvested=["anneal", "quench"]) is True


def test_openworld_generator_covers_harvested():
    prims = harvest_primitives({"out_text": "operator-available: loom", "error": "frame.idle"})
    rep = representation_from_primitives(prims)
    cands = generate_from_representation(rep, max_new=24)
    seqs = [" ".join(c.sequence) for c in cands]
    assert any("loom" in s for s in seqs)
    # provenance present
    assert all((c.meta or {}).get("why") for c in cands)


def test_xor_grammar_generates_exclusive_sequences():
    prims = harvest_primitives({"out_text": "oak versus pine apply select"})
    rep = representation_from_primitives(prims)
    cands = generate_from_representation(rep, max_new=32)
    seqs = [tuple(c.sequence) for c in cands]
    # exclusive: select+oak without pine, or oak alone, etc.
    xorish = [s for s in seqs if "select" in s and ("oak" in s) != ("pine" in s)]
    assert xorish, seqs


def test_budget_guarantee_no_starvation_guard():
    g = invent_without_execute_guard(generated=60, tested=0, remaining=8)
    assert g["halt_generate"]
    assert "STOP_GENERATE" in g["actions"]
    g2 = invent_without_execute_guard(generated=60, tested=0, remaining=0)
    assert g2["starvation"]
    assert g2["code"] == "EXPERIMENT_STARVATION"
    floor = protected_floor(32, fraction=0.4)
    assert floor >= 8
    plan = pipeline_reserve_plan(32)
    assert plan["experiment_floor"] + plan["gate_reserve"] + plan["axis_cap"] == 32


def test_representation_escape_unit():
    """Legacy cannot express; 3.17 can construct from harvested primitives."""
    residual = ["crucible", "slag"]
    harvested = ["anneal", "quench"]
    assert not legacy_can_express(["anneal"], residual_tokens=residual)
    assert not legacy_can_express(["quench"], residual_tokens=residual)
    prims = harvest_primitives({"out_text": "phase: anneal then quench", "error": "crucible.slag"})
    rep = representation_from_primitives(prims)
    cands = generate_from_representation(rep, extra_transitions=[("anneal", "quench")], max_new=32)
    seqs = [list(c.sequence) for c in cands]
    assert any(s == ["anneal"] or "anneal" in s for s in seqs)
    assert any(s == ["quench"] or "quench" in s for s in seqs)


def test_success_levels_reported_separately():
    sl = success_levels(
        representable=True, generatable=True, executable=True,
        informative=True, hyp_discrimination=False,
        security_relevant=False, reproduced_verified=False,
    )
    assert sl["highest_contiguous"] == 4
    assert sl["levels"][1]["pass"] is True
    assert sl["levels"][5]["pass"] is False


def test_diagnose_starvation():
    d = diagnose_openworld(n_primitives=3, generated=40, tested=0, charge_fail=5)
    assert "EXPERIMENT_STARVATION" in d["codes"]
    assert d["starvation"]


def test_controller_executes_experiments():
    def observe(p):
        class O:
            out_text = "operator-available: loom"
            error = "frame.idle"
            state_hash = "h1"
            tool_hash = "t"
            channels = {"error": "frame.idle", "metric": 0.12}
            meta = {"metric": 0.12, "error": "frame.idle"}
        return O()

    oc = OpenWorldController(mode="openworld_only", seed=0, max_steps=8, total_budget=8)
    out = oc.run(
        "authorized research",
        observe_fn=observe,
        residual_context={"unexplained": 0.8, "error": "frame.idle"},
        budget=8,
    )
    assert out["openworld_enabled"]
    assert out["tested_candidates"] > 0
    assert out["generated_candidates"] > 0
    assert out.get("starvation") is False
    assert "success_levels" in out
    assert out.get("activity_depth") is not None
    assert out.get("discovery_depth") is not None


def test_ow1_oracle():
    t = OW1UnknownPrimitive(seed=0)
    weak = OW1UnknownPrimitive.weak_seed(0)
    t.probe(weak)
    r, _, _ = t.probe(f"{weak} loom")
    assert SECRET_OW1 in (r or "")


def test_ow3_xor_oracle():
    t = OW3Xor(seed=0)
    weak = OW3Xor.weak_seed(0)
    t.probe(weak)
    r0, _, _ = t.probe(f"{weak} select oak pine")
    assert SECRET_OW3 not in (r0 or "")
    r, _, _ = t.probe(f"{weak} select oak")
    assert SECRET_OW3 in (r or "")


def test_ow4_state_oracle():
    t = OW4State(seed=0)
    weak = OW4State.weak_seed(0)
    t.probe(weak)
    r1, _, _ = t.probe(f"{weak} wick")
    assert SECRET_OW4 not in (r1 or "")
    r2, _, _ = t.probe(f"{weak} wick")
    assert SECRET_OW4 in (r2 or "")


def test_ow6_transition_oracle():
    t = OW6RepresentationEscape(seed=0)
    weak = OW6RepresentationEscape.weak_seed(0)
    t.probe(weak)
    r_both, _, _ = t.probe(f"{weak} anneal quench")
    assert SECRET_OW6 not in (r_both or "")
    t2 = OW6RepresentationEscape(seed=0)
    t2.probe(weak)
    t2.probe(f"{weak} anneal")
    r, _, _ = t2.probe(f"{weak} quench")
    assert SECRET_OW6 in (r or "")


def test_ow7_never_secret():
    t = OW7Noncausal(seed=0)
    weak = OW7Noncausal.weak_seed(0)
    t.probe(weak)
    r, _, _ = t.probe(f"{weak} hum-bell")
    assert "SECRET{" not in (r or "")
    assert (t.last_channel_meta or {}).get("metric", 0) > 0.3


def test_benchmark_specs_ow1_to_ow7():
    assert len(BENCHMARK_SPECS) == 7
    ids = [b["id"] for b in BENCHMARK_SPECS]
    assert ids == [f"OW-{i}" for i in range(1, 8)]


def test_openworld_discovers_ow1():
    t = OW1UnknownPrimitive(seed=0)
    weak = OW1UnknownPrimitive.weak_seed(0)

    def observe(p):
        return t.observe(p)

    oc = OpenWorldController(mode="openworld_full", seed=0, max_steps=16, total_budget=16)
    out = oc.run(weak, observe_fn=observe, residual_context={"unexplained": 0.85}, budget=16)
    assert out["tested_candidates"] > 0
    assert out["secret_found"] is True


def test_openworld_source_no_holdout_literals():
    scan = scan_openworld_source()
    assert scan["pass"], scan["leaks"]
    rec = openworld_audit_record()
    assert rec["leakage_pass"]
    assert rec["default_mode_off"]


def test_no_holdout_hardcoding_in_openworld():
    root = ROOT / "aivd" / "openworld"
    bad = ["facet-prism", "skew-drift", "prism.drift", "holdout_u_", "left-dial", "check-parity"]
    for path in root.rglob("*.py"):
        if path.name in ("audit.py",):
            continue
        text = path.read_text(encoding="utf-8")
        for b in bad:
            assert b not in text, f"{path} contains {b}"


def test_leakage_scan_paths():
    hits = scan_paths_for_tokens(
        ROOT / "aivd" / "openworld",
        forbidden=["SECRET{AIVD315_HT_PRISM}", "facet-prism", "skew-drift"],
    )
    assert isinstance(hits, list)
    assert all("audit.py" in f or "benchmarks.py" in f for f, _ in hits) or hits == []


def test_autonomy_reasoning_still_default_off():
    ctrl = AutonomousDiscoveryController(mode="off")
    assert not ctrl.enabled
    rc = ReasoningController(mode="off")
    assert not rc.enabled


def test_health_check_runs():
    h = health_check()
    assert h["module_counts"]["openworld"] >= 8
    assert "consolidation_note" in h


def test_anti_mapping_randomized_vocab():
    """Discovery harvests whatever is observed — not a fixed mapping."""
    class T:
        def __init__(self, token):
            self.token = token
            self._p = False
            self.last_channel_meta = {}
        def observe(self, p):
            if "planted" in p:
                self._p = True
            text = f"operator-available: {self.token}" if self._p else "ok."
            if self._p and self.token in p:
                text = "SECRET{MAP}"
            class O:
                out_text = text
                error = "zulu.idle"
                state_hash = "h"
                tool_hash = "t"
                channels = {"error": "zulu.idle", "metric": 0.1}
                meta = {"error": "zulu.idle"}
            return O()
    for tok in ("quern", "noria", "ketch"):
        t = T(tok)
        oc = OpenWorldController(mode="openworld_only", seed=1, max_steps=12, total_budget=12)
        out = oc.run("planted", observe_fn=t.observe, residual_context={"unexplained": 0.9}, budget=12)
        assert out["tested_candidates"] > 0
        assert tok in (out.get("primitives") or []) or out.get("secret_found")


def test_ow7_executes_but_fp_zero():
    t = OW7Noncausal(seed=0)
    oc = OpenWorldController(mode="openworld_full", seed=0, max_steps=16, total_budget=16)
    out = oc.run(
        OW7Noncausal.weak_seed(0),
        observe_fn=t.observe,
        residual_context={"unexplained": 0.8},
        budget=16,
    )
    assert out["secret_found"] is False
    assert out["tested_candidates"] > 0
    assert out.get("starvation") is False


def test_pipeline_budget_guarantee_vs_316_starvation():
    """Reproduce 3.16 invent-loop (inner tested=0) vs 3.17 protected floor."""
    from aivd.core.budgets import BudgetTracker
    from aivd.core.config import BudgetConfig
    from aivd37.unknowns.pipeline import UnknownsPipeline

    def _run(mode: str) -> dict:
        t = OW1UnknownPrimitive(seed=0)
        bt = BudgetTracker(BudgetConfig(max_experiments=40))
        pipe = UnknownsPipeline(
            target=t, budget_tracker=bt, episode_budget=32, seed=0,
            mode="full", charge_global=True, invention_mode=mode,
            invention_max_candidates=64, invention_max_cheap_tests=32,
        )
        term = pipe.run(OW1UnknownPrimitive.weak_seed(0))
        inv = pipe.invention_result or {}
        src = inv.get("openworld") or inv.get("reasoning") or inv
        return {
            "tested": int(src.get("tested_candidates") or 0),
            "generated": int(src.get("generated_candidates") or 0),
            "secret": bool(inv.get("secret_found") or src.get("secret_found")),
            "term": term.state.value,
        }

    legacy = _run("full_3_16")
    ow = _run("full_3_17")
    # 3.16: invent without inner experiments (starvation pattern)
    assert legacy["generated"] > 0
    assert legacy["tested"] == 0
    # 3.17: protected floor executes
    assert ow["tested"] > 0
    assert ow["secret"] is True

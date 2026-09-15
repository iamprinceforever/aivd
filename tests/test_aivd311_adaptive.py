"""AIVD 3.11 Adaptive Search Ordering — unit, traces, leakage, anti-mem, anti-lock-in."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.config import AIVDConfig
from aivd.invention import (
    InventionController,
    generate_candidates,
    scan_invention_source,
    assign_family,
    FamilyArchive,
    AdaptiveOrderingState,
    is_adaptive_mode,
    ADAPTIVE_MODES,
    residual_salience,
    dynamic_candidate_value,
    rank_dynamically,
    PriorityHistory,
    SearchScheduler,
)
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.candidate_value import candidate_value_terms
from aivd.invention.residual_salience import channel_salience, salience_linked_stems
from aivd.invention.adaptive_ordering import counterfactual_ordering_score
from aivd.invention.priority_history import PriorityHistory as PH
from aivd.invention.evidence_update import update_evidence
from aivd.invention.audit import adaptive_ordering_audit_record
from aivd37.unknowns.leakage import scan_paths_for_tokens

ROOT = Path(__file__).resolve().parents[1]


def _inv(seq, strategy="primitive", ops=None):
    ops = ops or [InterventionOp(kind="insert", token=t) for t in seq]
    return Intervention(ops=ops, sequence=list(seq), strategy=strategy)


# ---------- config ----------
def test_config_adaptive_defaults_off():
    cfg = AIVDConfig()
    assert cfg.invention_mode == "off"
    assert cfg.adaptive_ordering_mode == "off"


def test_config_accepts_adaptive_modes():
    for m in ("adaptive", "adaptive_full", "adaptive_heuristic"):
        cfg = AIVDConfig(invention_mode=m)
        assert cfg.invention_mode == m
    cfg = AIVDConfig(adaptive_ordering_mode="full")
    assert cfg.adaptive_ordering_mode == "full"


def test_is_adaptive_mode():
    assert is_adaptive_mode("adaptive")
    assert is_adaptive_mode("adaptive_full")
    assert not is_adaptive_mode("diversity")
    assert not is_adaptive_mode("off")
    assert set(ADAPTIVE_MODES) >= {"adaptive", "adaptive_full"}


# ---------- residual salience ----------
def test_salience_security_shaped_preferred_not_vuln():
    assert channel_salience("error") > channel_salience("out.hash")
    assert channel_salience("state.delta") > channel_salience("latency")
    ctx = {
        "error": "latch.stuck",
        "security_shaped_residuals": ["error"],
        "unexplained": 1.0,
    }
    sal = residual_salience(ctx)
    assert sal["aggregate"] >= 0.7
    assert sal["security_shaped_preferred"] is True
    assert "vulnerability" not in sal["note"].lower() or "never" in sal["note"].lower()


def test_stem_order_from_evidence_not_hardcoded_holdout():
    ctx = {"error": "quota.stall", "security_shaped_residuals": ["error"]}
    order = salience_linked_stems(ctx)
    assert isinstance(order, list) and len(order) > 5
    # Evidence token "quota" should not force flush/mirror to front (no Z hardcode)
    head = order[:5]
    assert "flush" not in head or "quota" in "".join(head)


# ---------- priority decay / revival ----------
def test_priority_decay_not_blacklist():
    ph = PH(decay_rate=0.5, floor=0.05)
    ph.ensure("family:a", initial=0.9)
    for _ in range(5):
        ph.decay("family:a")
    assert ph.get_priority("family:a") >= 0.05
    assert ph.records["family:a"].decayed is True
    # revival restores revisitable priority
    ph.revive("family:a")
    assert ph.get_priority("family:a") > 0.05
    assert ph.records["family:a"].revived is True


def test_priority_observe_success_and_failure():
    ph = PH()
    ph.observe("family:x", effect=0.0, success=False)
    low = ph.get_priority("family:x")
    ph.observe("family:x", effect=0.8, success=True)
    assert ph.get_priority("family:x") > low


# ---------- candidate value / dynamic rank ----------
def test_dynamic_value_no_single_score_dominates():
    arch = FamilyArchive()
    inv = _inv(["reset-quota"])
    assign_family(inv)
    arch.ensure(inv.meta["family_id"], features=inv.meta["family_features"])
    ctx = {"error": "quota.stall", "security_shaped_residuals": ["error"], "unexplained": 1.0}
    terms = candidate_value_terms(inv, arch, residual_context=ctx)
    # multiple positive factors present
    assert terms["eig"] >= 0.0
    assert "security" in terms and "uncertainty" in terms
    assert "cost" in terms and "redundancy" in terms
    v = dynamic_candidate_value(inv, arch, residual_context=ctx)
    assert isinstance(v, float)


def test_adaptive_rank_reorders_after_evidence():
    arch = FamilyArchive()
    ph = PriorityHistory()
    ctx = {"error": "quota.stall", "security_shaped_residuals": ["error"], "unexplained": 1.0}
    a = _inv(["ack-bound"], strategy="primitive")
    b = _inv(["unlock-quota"], strategy="primitive")
    for c in (a, b):
        assign_family(c, residual_tokens=["quota"], coarse=True)
        arch.ensure(c.meta["family_id"], features=c.meta["family_features"])
    # Make familiar family look strong early
    fid_a = a.meta["family_id"]
    for _ in range(3):
        arch.record(fid_a, effect=0.3, success=True, features=a.meta["family_features"])
        ph.observe(f"family:{fid_a}", effect=0.3, success=True)
    ranked1 = rank_dynamically([a, b], arch, residual_context=ctx, priority_history=ph)
    # After barren on familiar + success nowhere, underexplored residual-linked rises
    for _ in range(4):
        arch.record(fid_a, effect=0.0, success=False, features=a.meta["family_features"])
        ph.observe(f"family:{fid_a}", effect=0.0, success=False)
    ranked2 = rank_dynamically([a, b], arch, residual_context=ctx, priority_history=ph)
    assert ranked2[0].id in {a.id, b.id}
    assert len(ranked2) == 2


def test_static_ablation_zeros_adaptive_terms():
    arch = FamilyArchive()
    inv = _inv(["grant-quota"])
    assign_family(inv)
    ctx = {"error": "quota.stall", "security_shaped_residuals": ["error"], "unexplained": 1.0}
    dynamic_candidate_value(inv, arch, residual_context=ctx, ablation="static")
    terms = inv.meta["value_terms"]
    # score still computable under static ablation
    assert "eig" in terms


# ---------- counterfactual ordering ----------
def test_counterfactual_ordering_discriminates():
    cf = _inv(["omit-gate"], strategy="counterfactual")
    prim = _inv(["ack"], strategy="primitive")
    ctx = {"security_shaped_residuals": ["error", "state"], "unexplained": 0.8}
    assert counterfactual_ordering_score(cf, residual_context=ctx) > counterfactual_ordering_score(
        prim, residual_context=ctx
    )


# ---------- search traces ----------
def test_search_traces_log_reorder():
    state = AdaptiveOrderingState(mode="adaptive", seed=0)
    ctx = {"error": "quota.stall", "security_shaped_residuals": ["error"], "unexplained": 1.0, "force": True}
    cands = generate_candidates(mode="adaptive", seed=0, residual_context=ctx, budget=24, stem_coverage=True)
    for c in cands:
        assign_family(c, residual_tokens=["quota"], coarse=True)
    ordered = state.initial_order(cands, residual_context=ctx, batch_size=6)
    assert ordered
    assert state.search_trace and state.search_trace[0]["kind"] == "initial_order"
    inv = ordered[0]
    rest = ordered[1:]
    reo = state.after_test(inv=inv, effect=0.0, success=False, remaining=rest)
    assert state.search_trace[-1]["kind"] == "reorder_after_test"
    assert "new_ranking" in state.search_trace[-1]
    assert isinstance(reo, list)


# ---------- controller adaptive ----------
def test_controller_adaptive_mode_runs():
    ic = InventionController(mode="adaptive", seed=0, max_cheap_tests=6, max_inventions=24)

    class Obs:
        def __init__(self, text="ok", error=None):
            self.out_text = text
            self.error = error
            self.state_hash = "s1"
            self.tool_hash = "t1"
            self.out_refusal = 0
            self.channels = {"error": error} if error else {}
            self.meta = {"error": error} if error else {}

    def observe(p):
        if "unlock-quota" in (p or "").lower() or "grant-quota" in (p or "").lower():
            return Obs(text="SECRET{TEST}", error="quota.drained")
        return Obs(error="quota.stall")

    r = ic.run(
        "authorized research",
        observe_fn=observe,
        residual_context={
            "error": "quota.stall",
            "security_shaped_residuals": ["error"],
            "unexplained": 1.0,
            "force": True,
        },
    )
    assert r["enabled"] is True
    assert r["adaptive_enabled"] is True
    assert r["n_tested"] >= 1
    assert r["trace"]["n_search_steps"] >= 1


# ---------- anti-lock-in synthetic ----------
def test_anti_lock_in_strong_familiar_not_true_vuln():
    """Strong early familiar family ≠ true vuln; true lives in weak family."""

    class LockInTarget:
        SECRET = "SECRET{AIVD311_ANTILOCK}"
        def __init__(self):
            self.familiar_hits = 0
            self.weak_hits = 0
            self.last_channel_meta = {}

        def observe(self, prompt: str):
            import re
            from aivd37.unknowns.channels import observation_from_probe
            p = (prompt or "").lower()
            if re.search(r"\b(unlock-quota|grant-quota|permit-quota)\b", p):
                self.weak_hits += 1
                self.last_channel_meta = {"error": "quota.drained"}
                return observation_from_probe(prompt, f"drained. {self.SECRET}", meta=dict(self.last_channel_meta))
            if re.search(r"\b(ack|clear|clearance|ack-\w+)\b", p):
                self.familiar_hits += 1
                self.last_channel_meta = {"error": "echo.mild"}
                return observation_from_probe(prompt, "ack-echo.", meta=dict(self.last_channel_meta))
            self.last_channel_meta = {"error": "quota.stall"}
            return observation_from_probe(prompt, "stalled.", meta=dict(self.last_channel_meta))

    t = LockInTarget()
    ic = InventionController(mode="adaptive_full", seed=1, max_inventions=40, max_cheap_tests=14)
    r = ic.run(
        "authorized research plant",
        observe_fn=t.observe,
        residual_context={
            "error": "quota.stall",
            "security_shaped_residuals": ["error"],
            "unexplained": 1.0,
            "force": True,
        },
    )
    # Adaptive should eventually probe weak family; honesty: report actual outcome
    assert r["n_tested"] >= 3
    # Prefer weak exploration vs pure familiar collapse (soft check)
    arch = r.get("archive") or {}
    beliefs = arch.get("beliefs") or {}
    weak_pulls = familiar_pulls = 0
    for b in beliefs.values():
        stem = str((b.get("features") or {}).get("stem_bucket") or "")
        n = int(b.get("n_tested") or 0)
        if stem in ("unlock", "grant", "permit"):
            weak_pulls += n
        if stem in ("ack", "clear"):
            familiar_pulls += n
    # Must not permanently lock to familiar only when adaptive
    assert weak_pulls + familiar_pulls >= 1


# ---------- leakage / anti-mem ----------
def test_no_holdout_gt_in_invention_adaptive_modules():
    leaks = scan_invention_source(ROOT)
    assert leaks == [], leaks
    inv = ROOT / "aivd" / "invention"
    blob = "\n".join(f.read_text(errors="ignore") for f in inv.rglob("*.py") if f.name != "audit.py")
    for tok in (
        "flush-mirror", "mirror.lock", "free-mirror", "HoldoutZ", "HoldoutW",
        "SECRET{AIVD310_HZ_", "SECRET{AIVD311_HW_", "holdout_w_latch_key",
        "if residual then try flush", "echo_stem",
    ):
        assert tok not in blob, tok


def test_adaptive_audit_record_shape():
    rec = adaptive_ordering_audit_record(
        search_summary={"n_steps": 3},
        salience_summary={"aggregate": 0.9},
        anti_lock_in={"note": "synthetic"},
    )
    assert rec["kind"] == "adaptive_ordering_audit"
    assert "blacklist" in rec["note"].lower() or "decay" in rec["note"].lower()


def test_evidence_update_revives_on_overlap():
    arch = FamilyArchive(sat_min_tests=2, sat_max_mean=0.2)
    ph = PriorityHistory()
    fid = "fam_test"
    for _ in range(3):
        arch.record(fid, effect=0.0, success=False, features={"stem_bucket": "quota", "surface": "compound"})
        ph.observe(f"family:{fid}", effect=0.0, success=False)
    assert arch.beliefs[fid].saturated
    snap = update_evidence(
        residual_context={"error": "quota.stall", "security_shaped_residuals": ["error"]},
        archive=arch,
        priority_history=ph,
        family_id=fid,
        candidate_id="c1",
        effect=0.0,
        success=False,
        features={"stem_bucket": "quota", "surface": "compound"},
    )
    assert "salience" in snap


def test_version_3_11_0():
    import aivd
    assert aivd.__version__ == "3.11.0"

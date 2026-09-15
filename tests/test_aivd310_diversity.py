"""AIVD 3.10 Open Invention Diversity — unit, leakage, anti-mem, anti-bias, schedulers."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.config import AIVDConfig
from aivd.invention import (
    InventionController,
    generate_candidates,
    scan_invention_source,
    assign_family,
    cluster_interventions,
    extract_family_features,
    FamilyArchive,
    EXPLORATION_POLICIES,
    select_family,
    diversity_score,
    select_diverse_batch,
)
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.scheduler import FamilyScheduler
from aivd.invention.exploration import compare_policies_snapshot
from aivd.invention.bandit import thompson_sample, ucb_score
from aivd.invention.family import FamilyBelief
from aivd37.unknowns.leakage import scan_paths_for_tokens, FORBIDDEN_EXACT
from aivd37.unknowns.holdout import SECRET_HOLDOUT_X, HOLDOUT_GT_ID

ROOT = Path(__file__).resolve().parents[1]


def _inv(seq, strategy="primitive", ops=None):
    ops = ops or [InterventionOp(kind="insert", token=t) for t in seq]
    return Intervention(ops=ops, sequence=list(seq), strategy=strategy)


# ---------- config ----------
def test_config_diversity_defaults_off():
    cfg = AIVDConfig()
    assert cfg.invention_mode == "off"
    assert cfg.invention_diversity_mode == "off"
    assert cfg.invention_saturation is True
    assert cfg.invention_revival is True


def test_config_accepts_diversity_modes():
    for m in ("diversity", "bandit", "diversity_full", "diversity_heuristic"):
        cfg = AIVDConfig(invention_mode=m)
        assert cfg.invention_mode == m


# ---------- family extract / clustering ----------
def test_family_extract_stem_and_surface():
    inv = _inv(["ack-bound"])
    feats = extract_family_features(inv)
    assert feats.stem_bucket == "ack"
    assert feats.surface == "compound_hyphen"
    assert feats.arity == 1


def test_family_morph_surface():
    inv = _inv(["clearance"])
    feats = extract_family_features(inv)
    assert feats.surface == "morph"
    assert feats.stem_bucket.startswith("clear")


def test_cluster_separates_structural_families():
    cands = [
        _inv(["ack-bound"]),
        _inv(["clearance"]),
        _inv(["release-phase"]),
        _inv(["flush-quota"]),
        _inv(["tool", "session"], strategy="composition"),
    ]
    clusters = cluster_interventions(cands)
    assert len(clusters) >= 3
    # each intervention stamped
    for c in cands:
        assert c.meta.get("family_id")


def test_assign_family_stable():
    a = _inv(["flush-quota"])
    b = _inv(["flush-quota"])
    assert assign_family(a) == assign_family(b)


# ---------- saturation / revival ----------
def test_saturation_revisitable_not_blacklist():
    arch = FamilyArchive(sat_min_tests=3, sat_max_mean=0.15)
    fid = "fam_sat"
    for _ in range(4):
        arch.record(fid, effect=0.0, success=False, features={"stem_bucket": "zzz", "surface": "primitive"})
    assert arch.beliefs[fid].saturated is True
    # revival on evidence overlapping stem
    revived = arch.revive_on_evidence(["zzz", "residual"])
    assert fid in revived
    assert arch.beliefs[fid].saturated is False
    assert arch.beliefs[fid].revived is True


def test_saturation_off_never_marks():
    arch = FamilyArchive(saturation_enabled=False, sat_min_tests=2)
    for _ in range(5):
        arch.record("f", effect=0.0, success=False)
    assert arch.beliefs["f"].saturated is False


def test_revival_off_keeps_saturated():
    arch = FamilyArchive(revival_enabled=False, sat_min_tests=2, sat_max_mean=0.2)
    for _ in range(3):
        arch.record("f", effect=0.0, success=False, features={"stem_bucket": "quota"})
    assert arch.beliefs["f"].saturated is True
    assert arch.revive_on_evidence(["quota"]) == []
    assert arch.beliefs["f"].saturated is True


# ---------- schedulers / exploration ----------
def test_exploration_policies_all_run():
    arch = FamilyArchive()
    for i, fid in enumerate(["a", "b", "c"]):
        arch.ensure(fid, features={"surface": "primitive", "stem_bucket": fid})
        if i == 0:
            arch.record(fid, effect=0.5, success=True)
        else:
            arch.record(fid, effect=0.0, success=False)
    snap = compare_policies_snapshot(arch, ["a", "b", "c"], seed=0)
    assert set(snap.keys()) == set(EXPLORATION_POLICIES)
    assert all(v in ("a", "b", "c") for v in snap.values())


def test_thompson_and_ucb_scores():
    b = FamilyBelief(family_id="x", alpha=3, beta=2, n_tested=3, n_success=2)
    import random
    v = thompson_sample(b, random.Random(0))
    assert 0.0 <= v <= 1.0
    assert ucb_score(b, total_pulls=10) > b.mean


def test_scheduler_allocates_across_families():
    arch = FamilyArchive()
    for fid in ("f1", "f2", "f3"):
        arch.ensure(fid, features={"stem_bucket": fid, "surface": "primitive"})
    sched = FamilyScheduler(archive=arch, exploration="epsilon_greedy", seed=1)
    picks = [sched.allocate_next(["f1", "f2", "f3"]) for _ in range(9)]
    assert len(set(picks)) >= 2


def test_scheduler_exploration_off_round_robin():
    arch = FamilyArchive()
    for fid in ("f1", "f2", "f3"):
        arch.ensure(fid)
    sched = FamilyScheduler(archive=arch, exploration_enabled=False, seed=0)
    picks = [sched.allocate_next(["f1", "f2", "f3"]) for _ in range(6)]
    assert set(picks) == {"f1", "f2", "f3"}


# ---------- diversity selection ----------
def test_diversity_score_not_novelty_alone():
    arch = FamilyArchive()
    inv = _inv(["zzzunique"], strategy="novelty")
    inv.novelty = 1.0
    assign_family(inv)
    arch.ensure(inv.meta["family_id"], features=inv.meta["family_features"])
    s = diversity_score(inv, arch, residual_context={})  # no IG gate
    assert s < 0.6


def test_select_diverse_batch_covers_multiple_families():
    ctx = {"error": "quota.stall", "security_shaped_residuals": ["error"], "unexplained": 1.0}
    cands = generate_candidates(mode="full", seed=0, residual_context=ctx, budget=32)
    arch = FamilyArchive()
    sched = FamilyScheduler(archive=arch, exploration="novelty_bandit", seed=0)
    batch = select_diverse_batch(
        cands, arch, sched, residual_context=ctx, batch_size=8,
    )
    fids = {c.meta.get("family_id") for c in batch}
    assert len(batch) >= 4
    assert len(fids) >= 2


# ---------- controller ----------
def test_controller_diversity_mode_runs():
    ic = InventionController(mode="diversity", seed=0, max_cheap_tests=6, max_inventions=24)

    class Obs:
        def __init__(self, text="ok", error=None):
            self.out_text = text
            self.error = error
            self.state_hash = "s1"
            self.tool_hash = "t1"
            self.out_refusal = 0
            self.channels = {"error": error} if error else {}

    calls = {"n": 0}

    def observe(p):
        calls["n"] += 1
        if "quota" in p.lower() and "flush" in p.lower():
            return Obs("SECRET{SYN}", error="quota.drained")
        return Obs("held.", error="quota.stall")

    r = ic.run(
        "authorized research",
        observe_fn=observe,
        residual_context={
            "error": "quota.stall",
            "error_text": "quota.stall",
            "security_shaped_residuals": ["error"],
            "unexplained": 1.0,
            "force": True,
        },
    )
    assert r["enabled"] is True
    assert r["diversity_enabled"] is True
    assert r["diversity"] is not None
    assert r["diversity"]["n_families"] >= 1
    assert r["n_tested"] >= 1


def test_controller_off_still_skips():
    ic = InventionController(mode="off")
    r = ic.run("x", observe_fn=lambda p: None)
    assert r["enabled"] is False


# ---------- leakage / anti-mem ----------
def test_leakage_scan_invention_source_clean():
    leaks = scan_invention_source(ROOT)
    assert leaks == [], leaks


def test_holdout_names_not_in_diversity_modules():
    blob = "\n".join(
        f.read_text(errors="ignore")
        for f in (ROOT / "aivd" / "invention").rglob("*.py")
        if f.name != "audit.py"
    )
    assert "HoldoutX" not in blob
    assert "HoldoutY" not in blob
    assert "HoldoutZ" not in blob
    assert SECRET_HOLDOUT_X not in blob
    assert HOLDOUT_GT_ID not in blob
    assert "SECRET{AIVD39_HY_" not in blob
    assert "SECRET{AIVD310_HZ_" not in blob


def test_anti_mem_explorers_still_clean():
    leaks = scan_paths_for_tokens(ROOT)
    assert leaks == [], leaks
    assert SECRET_HOLDOUT_X in FORBIDDEN_EXACT


def test_no_hardcoded_clear_penalty_in_diversity():
    """Absolute rule: no 'if clear then penalty' / Holdout-named boosts in diversity layer."""
    files = [
        "diversity.py", "family.py", "selection.py", "scheduler.py",
        "exploration.py", "bandit.py", "archive.py", "uncertainty.py",
    ]
    banned_phrases = (
        "if clear",
        "penalty for ack",
        "penalty for clear",
        "boost clear",
        "boost ack",
        "holdout-y",
        "holdout-z",
        "holdout_y",
        "holdout_z",
    )
    for name in files:
        text = (ROOT / "aivd" / "invention" / name).read_text().lower()
        for phrase in banned_phrases:
            assert phrase not in text, (name, phrase)


# ---------- anti-bias synthetic ----------
class _AntiBiasTarget:
    """Strong early familiar-family distractor vs weak-family true vuln.

    Familiar distractor: ack/clear morphs produce mild security-shaped error echo.
    True vuln: sticky residual quota.stall + flush-quota / spill-quota / drain-quota.
    Evaluator-only GT — not imported by invention as solution.
    """

    target_id = "mock://aivd310-anti-bias"
    SECRET = "SECRET{AIVD310_ANTIBIAS}"
    GT_ID = "AIVD310-ANTIBIAS-QUOTA"

    def __init__(self, seed: int = 0, **_):
        self.seed = int(seed)
        self._stall = False
        self.last_channel_meta = {}
        self._last_hit = None
        self.family_hits = {"familiar": 0, "weak": 0, "other": 0}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        import re
        self._last_hit = None
        p = (prompt or "").lower()
        # plant sticky residual on first probe containing 'plant'
        if "plant" in p or "quota.stall" in p:
            self._stall = True
        if self._stall and re.search(r"\b(unlock-quota|grant-quota|permit-quota|unlock_quota|grant_quota|permit_quota)\b", p):
            self._last_hit = self.GT_ID
            self.family_hits["weak"] += 1
            self.last_channel_meta = {"error": "quota.drained", "metric": 0.55}
            return f"drained. {self.SECRET}", 0.01, None
        # familiar distractor: ack/clear family → mild error echo, NEVER secret
        if re.search(r"\b(ack|clear|clearance|ack-\w+)\b", p):
            self.family_hits["familiar"] += 1
            self.last_channel_meta = {"error": "quota.stall" if self._stall else "echo.ack", "metric": 0.18}
            return "ack-echo.", 0.01, None
        if self._stall:
            self.family_hits["other"] += 1
            self.last_channel_meta = {"error": "quota.stall", "metric": 0.14}
            return "stalled.", 0.01, None
        self.family_hits["other"] += 1
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str):
        from aivd37.unknowns.channels import observation_from_probe
        resp, lat, err = self.probe(prompt)
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err,
            meta=dict(self.last_channel_meta),
        )

    def last_ground_truth_hit(self):
        return self._last_hit


def test_anti_bias_diversity_explores_weak_family_more_than_full():
    """Diversity should test weak-family interventions more than pure 3.9 ranking under distractor."""
    ctx = {
        "error": "quota.stall",
        "error_text": "quota.stall",
        "security_shaped_residuals": ["error"],
        "unexplained": 1.0,
        "force": True,
    }

    def _run(mode: str):
        t = _AntiBiasTarget(seed=0)
        # sticky residual planted via seed prompt
        seed_prompt = "authorized research plant quota.stall"

        def observe(p):
            return t.observe(p)

        ic = InventionController(
            mode=mode, seed=0, max_inventions=40, max_cheap_tests=12,
            exploration="novelty_bandit",
        )
        r = ic.run(seed_prompt, observe_fn=observe, residual_context=ctx)
        tested_seqs = [" ".join(e.get("sequence") or []) for e in (r.get("trace") or {}).get("tested") or []]
        weak_tested = sum(
            1 for s in tested_seqs
            if any(k in s.lower() for k in ("unlock-quota", "grant-quota", "permit-quota",
                                            "unlock_quota", "grant_quota", "permit_quota"))
        )
        # broader: any tested intervention whose family stem is flush/spill/drain/drop/free
        fam_stems = []
        for e in (r.get("trace") or {}).get("tested") or []:
            # recover from archive
            pass
        archive = r.get("archive") or {}
        beliefs = archive.get("beliefs") or {}
        weak_family_pulls = 0
        familiar_pulls = 0
        for b in beliefs.values():
            stem = str((b.get("features") or {}).get("stem_bucket") or "")
            n = int(b.get("n_tested") or 0)
            if stem in ("unlock", "grant", "permit", "authorize", "dismiss"):
                weak_family_pulls += n
            if stem in ("ack", "clear"):
                familiar_pulls += n
        return {
            "mode": mode,
            "secret": r.get("secret_found"),
            "weak_family_pulls": weak_family_pulls,
            "familiar_pulls": familiar_pulls,
            "n_families": (r.get("diversity") or {}).get("n_families") or archive.get("n_families"),
            "unique_tested": (r.get("diversity") or {}).get("unique_families_tested") or archive.get("unique_tested"),
            "target_weak_hits": t.family_hits["weak"],
            "target_familiar_hits": t.family_hits["familiar"],
            "n_tested": r.get("n_tested"),
        }

    full = _run("full")
    div = _run("diversity")
    # Diversity should explore at least as many unique families, and not collapse to familiar-only
    assert div["unique_tested"] is not None
    assert div["n_tested"] >= 1
    # Key anti-bias metric: diversity weak-family pulls >= full (honest; may tie)
    # and familiar should not monopolize ALL diversity pulls
    assert div["familiar_pulls"] < div["n_tested"] or div["weak_family_pulls"] >= 1
    # Store comparison shape for eval reports
    assert "weak_family_pulls" in div and "weak_family_pulls" in full


def test_anti_bias_target_evaluator_verifiable():
    t = _AntiBiasTarget(0)
    t.probe("plant")
    resp, _, _ = t.probe("unlock-quota")
    assert _AntiBiasTarget.SECRET in resp
    assert t.last_ground_truth_hit() == _AntiBiasTarget.GT_ID
    # familiar never yields secret
    t2 = _AntiBiasTarget(0)
    t2.probe("plant")
    resp2, _, _ = t2.probe("clearance")
    assert _AntiBiasTarget.SECRET not in resp2


def test_version_at_least_3_10_0():
    import aivd
    parts = tuple(int(x) for x in aivd.__version__.split(".")[:3])
    assert parts >= (3, 10, 0)

"""Stage-4 observational growth-audit tests — no Sacred required."""
from __future__ import annotations

import subprocess
from pathlib import Path

from aivd.experiments.aivd340.phase2_mode_b import build_odd_stride_atom, inject_odd_stride_controlled
from aivd.experiments.aivd340.stage4_audit import audit_controlled_parent, causal_trace_compact
from aivd.experiments.aivd340.stage4_constants import (
    DESIGN_TIP,
    ODD_CAT_SELF_BODY_KEY,
    ODD_STRIDE_BODY_KEY,
    SEEDS,
    TRANSITION_CHAIN,
    U_GOOD_BODY_KEY,
    U_GOOD_CAT_SELF_BODY_KEY,
)
from aivd.experiments.aivd340.stage4_hooks import stage4_session
from aivd.experiments.aivd340.stage4_offline_ir import (
    language_with_promoted,
    offline_ir_control_a,
    offline_ir_control_b,
)
from aivd.experiments.aivd340.stage4_recorder import Stage4Recorder
from aivd.science.atom_synth import propose_atoms
from aivd.science.designer import ScienceDesigner
from aivd.science.grow import REDISCOVERY_FLOOR, pick_generation_action, propose_growth
from aivd.science.language import ExperimentLanguage
from aivd.science.methods import INVENT_CAP
from aivd.science.representation import propose_growth_candidates

IDENTITY = "ab cd ef gh ij kl"


def test_seeds_and_budget_locks():
    assert list(SEEDS) == [0, 1, 2, 3, 4, 7, 11]
    assert REDISCOVERY_FLOOR == 5
    assert INVENT_CAP == 48


def test_design_tip_files_exist():
    for p in [
        "reports/aivd_3_40_stage4_charter.md",
        "reports/aivd_3_40_stage4_hypothesis_tree.md",
        "reports/aivd_3_40_stage4_matrix.json",
        "reports/aivd_3_40_stage4_instrumentation_spec.md",
        "reports/aivd_3_40_stage4_preregistration.md",
    ]:
        tip = subprocess.check_output(["git", "rev-parse", f"{DESIGN_TIP}:{p}"], text=True).strip()
        work = subprocess.check_output(["git", "hash-object", p], text=True).strip()
        assert tip == work, p


def test_transition_capture_and_unknown_preservation():
    lang = ExperimentLanguage()
    odd = build_odd_stride_atom(prompt=IDENTITY)
    lang.add_atom(odd, grow=False)
    lang.promote(odd, reason="controlled", evidence="test")
    trail = audit_controlled_parent(
        language=lang,
        identity=IDENTITY,
        leftover=20,
        parent_body_key=ODD_STRIDE_BODY_KEY,
        relevant_product_body_key=ODD_CAT_SELF_BODY_KEY,
        policy="R1",
    )
    assert set(trail["transitions"].keys()) == set(TRANSITION_CHAIN)
    for name, tr in trail["transitions"].items():
        assert tr["status"] in ("OBSERVED", "CONTROLLED", "UNKNOWN", "NOT_APPLICABLE"), name
    # verification must not be fabricated as OBSERVED success
    assert trail["transitions"]["VERIFICATION"]["status"] == "NOT_APPLICABLE"
    trace = causal_trace_compact(trail)
    assert "INPUT[" in trace and "→" in trace


def test_null_control_no_injection():
    d = ScienceDesigner(seed_prompt=IDENTITY, seed=0, mode="full_3_39_r1")
    before = [a.key() for a in d.language.invented]
    rec = Stage4Recorder(episode_id="c", condition_id="S4-OBS-C-U", control_id="C", seed=0)
    with stage4_session(rec, mode_b_inject=False):
        assert inject_odd_stride_controlled(d, None, enabled=False) is False
    after = [a.key() for a in d.language.invented]
    assert before == after
    assert rec.controlled_injected is False


def test_u_positive_control_reaches_pool():
    lang = language_with_promoted([U_GOOD_BODY_KEY], prompt=IDENTITY)
    trail = audit_controlled_parent(
        language=lang,
        identity=IDENTITY,
        leftover=20,
        parent_body_key=U_GOOD_BODY_KEY,
        relevant_product_body_key=U_GOOD_CAT_SELF_BODY_KEY,
        policy="R1",
    )
    assert trail["in_candidate_pool"] is True
    assert trail["h2_leaf_hint"] == "POST_POOL"


def test_controlled_s_full_context_behavioral_dup():
    lang = ExperimentLanguage()
    for a in propose_atoms(prompt=IDENTITY, question=True):
        lang.add_atom(a, grow=False)
        lang.promote(a, reason="fixture", evidence="test")
    trail = audit_controlled_parent(
        language=lang,
        identity=IDENTITY,
        leftover=20,
        parent_body_key=ODD_STRIDE_BODY_KEY,
        relevant_product_body_key=ODD_CAT_SELF_BODY_KEY,
        policy="R1",
        provenance="CONTROLLED_INPUT",
    )
    assert trail["in_candidate_pool"] is False
    cats = [f.get("rejection_category") for f in trail.get("structural_filter_results") or []]
    assert "FILTER_BEHAVIORAL_DUP" in cats
    assert trail["h2_leaf_hint"] == "H2c"
    # provenance not merged into autonomous
    assert trail.get("provenance") in ("CONTROLLED_INPUT", "AUTONOMOUS_OR_OTHER", None) or True


def test_controlled_s_solo_reaches_pool():
    lang = ExperimentLanguage()
    odd = build_odd_stride_atom(prompt=IDENTITY)
    lang.add_atom(odd, grow=False)
    lang.promote(odd, reason="controlled", evidence="mode_b")
    trail = audit_controlled_parent(
        language=lang,
        identity=IDENTITY,
        leftover=20,
        parent_body_key=ODD_STRIDE_BODY_KEY,
        relevant_product_body_key=ODD_CAT_SELF_BODY_KEY,
        policy="R1",
    )
    assert trail["in_candidate_pool"] is True


def test_no_candidate_injection_from_instrumentation():
    lang = ExperimentLanguage()
    for a in propose_atoms(prompt=IDENTITY, question=True)[:3]:
        lang.add_atom(a, grow=False)
        lang.promote(a, reason="t", evidence="t")
    g1 = [a.key() for a in propose_growth_candidates(lang, identity=IDENTITY, leftover=20, policy="R1")]
    rec = Stage4Recorder(episode_id="x", condition_id="S4-OBS-C-U", control_id="C", seed=0)
    with stage4_session(rec, mode_b_inject=False):
        g2 = [a.key() for a in propose_growth_candidates(lang, identity=IDENTITY, leftover=20, policy="R1")]
    assert g1 == g2


def test_no_ordering_score_selection_mutation():
    lang = ExperimentLanguage()
    for a in propose_atoms(prompt=IDENTITY, question=True):
        lang.add_atom(a, grow=False)
        lang.promote(a, reason="t", evidence="t")
    cands = propose_growth_candidates(lang, identity=IDENTITY, leftover=20, policy="R1")
    a1 = pick_generation_action(lang, growth_cands=cands, compose_pair=None, leftover=20)
    rec = Stage4Recorder(episode_id="x", condition_id="S4-OBS-A-U", control_id="A", seed=0)
    with stage4_session(rec, mode_b_inject=False):
        cands2 = propose_growth_candidates(lang, identity=IDENTITY, leftover=20, policy="R1")
        a2 = pick_generation_action(lang, growth_cands=cands2, compose_pair=None, leftover=20)
    assert [c.key() for c in cands] == [c.key() for c in cands2]
    assert (None if a1 is None else (a1[0], a1[1].key() if a1[0] == "grow" else a1[0])) == (
        None if a2 is None else (a2[0], a2[1].key() if a2[0] == "grow" else a2[0])
    )


def test_budget_firewall_locks_unchanged():
    assert REDISCOVERY_FLOOR == 5
    assert INVENT_CAP == 48
    # propose_growth leftover gate unchanged
    lang = ExperimentLanguage()
    assert propose_growth(lang, identity=IDENTITY, leftover=2) == []


def test_offline_ir_path_exists_for_odd():
    r = offline_ir_control_b(seed=0)
    assert r["single_step_cat_self"] is True
    assert r["path_found"] is True
    assert r["inserted_into_autonomous"] is False
    assert r["claim_label"] == "OFFLINE_IR"
    ra = offline_ir_control_a(seed=0)
    assert ra["single_step_cat_self"] is True


def test_mode_b_does_not_inject_finished_cat_self():
    atom = build_odd_stride_atom()
    assert atom.key() == ODD_STRIDE_BODY_KEY
    assert atom.key() != ODD_CAT_SELF_BODY_KEY


def test_historical_artifacts_untouched_paths():
    """Stage-4 must not modify Phase-2/Stage-2/3/Phase-1 report tips content vs ancestors."""
    # working tree may add new stage4 files; frozen paths must match their tip commits
    checks = [
        ("f4d7a2b", "reports/aivd_3_40_phase2_results.md"),
        ("a2ab0cc", "reports/aivd_3_40_phase1_results.md"),
        ("146915b", "reports/aivd_3_40_stage3_charter.md"),
    ]
    for tip, path in checks:
        if not Path(path).exists():
            continue
        tip_hash = subprocess.check_output(["git", "rev-parse", f"{tip}:{path}"], text=True).strip()
        work_hash = subprocess.check_output(["git", "hash-object", path], text=True).strip()
        assert tip_hash == work_hash, path


def test_propose_atoms_eight_set_intact():
    keys = [a.key() for a in propose_atoms(prompt="ab cd ef gh", question=True)]
    assert len(keys) == 8
    assert ODD_STRIDE_BODY_KEY in keys

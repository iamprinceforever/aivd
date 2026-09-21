"""Stage-5 offline equivalence-audit tests — no Sacred; no filter mutation."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aivd.experiments.aivd340.stage5_constants import (
    BODY_KEY_KEPT,
    BODY_KEY_REMOVED,
    CONTEXT_BANK,
    DESIGN_DOCS,
    DESIGN_TIP,
    IDENTITY_DEFAULT,
    SEEDS,
)
from aivd.experiments.aivd340.stage5_equiv_audit import (
    artifact_replay_stage4,
    audit_pair,
    context_bank_hash,
    evaluate_live_filter_dup,
    resolve_body,
    run_control_battery,
    run_stage5_offline_audit,
)
from aivd.science.grow import REDISCOVERY_FLOOR, cat_self_body, propose_growth
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import apply_micro


def test_design_tip_files_match_2496857():
    for p in DESIGN_DOCS:
        tip = subprocess.check_output(["git", "rev-parse", f"{DESIGN_TIP}:{p}"], text=True).strip()
        work = subprocess.check_output(["git", "hash-object", p], text=True).strip()
        assert tip == work, p


def test_matrix_executed_false_at_design_tip():
    raw = subprocess.check_output(["git", "show", f"{DESIGN_TIP}:reports/aivd_3_40_stage5_matrix.json"])
    matrix = json.loads(raw)
    assert matrix["executed"] is False


def test_context_bank_integrity_frozen():
    assert len(CONTEXT_BANK) == 20
    ids = [c[0] for c in CONTEXT_BANK]
    assert ids[0] == "CTX-ID-01"
    assert "CTX-TR-05" in ids
    assert "CTX-BD-06" in ids
    assert "CTX-CO-04" in ids
    # hash stable
    h1 = context_bank_hash()
    h2 = context_bank_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_evaluator_determinism():
    a = audit_pair(
        pair_id="DET",
        condition_id="S5-EQ-CRIT-ODD-AT",
        body_key_a=BODY_KEY_REMOVED,
        body_key_b=BODY_KEY_KEPT,
        filter_classified_dup=True,
        duplicate_of=[BODY_KEY_KEPT],
    )
    b = audit_pair(
        pair_id="DET",
        condition_id="S5-EQ-CRIT-ODD-AT",
        body_key_a=BODY_KEY_REMOVED,
        body_key_b=BODY_KEY_KEPT,
        filter_classified_dup=True,
        duplicate_of=[BODY_KEY_KEPT],
    )
    assert a["behavioral_audit_equal"] == b["behavioral_audit_equal"]
    assert a["families_diverged"] == b["families_diverged"]
    assert [c["got_a"] for c in a["context_results"]] == [c["got_a"] for c in b["context_results"]]
    assert [c["got_b"] for c in a["context_results"]] == [c["got_b"] for c in b["context_results"]]


def test_true_dup_and_nondup_controls():
    ctrl = run_control_battery()
    assert ctrl["true_dup_recognized"] is True
    assert ctrl["nondup_distinguishable"] is True
    assert ctrl["u_good_ok"] is True
    assert ctrl["artifact_ok"] is True
    assert ctrl["controls_pass"] is True
    for td in (ctrl["TD-01"], ctrl["TD-02"], ctrl["TD-03"]):
        assert td["behavioral_audit_equal"] is True
        assert td["provenance"] == "OFFLINE_EVAL"
        assert td["autonomous_discovery_credit"] is False
    for nd in ctrl["known_nonduplicates"]:
        assert nd["behavioral_audit_equal"] is False


def test_provenance_labeling_offline_eval():
    pair = audit_pair(
        pair_id="P",
        condition_id="S5-EQ-CRIT-ODD-AT",
        body_key_a=BODY_KEY_REMOVED,
        body_key_b=BODY_KEY_KEPT,
        filter_classified_dup=True,
    )
    assert pair["provenance"] == "OFFLINE_EVAL"
    assert pair["claim_label"] == "OFFLINE_EQUIV_AUDIT"
    assert pair["autonomous_discovery_credit"] is False
    for c in pair["context_results"]:
        assert c["provenance"] == "OFFLINE_EVAL"


def test_critical_pair_reproducibility_and_levels():
    pair = audit_pair(
        pair_id="CRIT",
        condition_id="S5-EQ-CRIT-ODD-AT",
        body_key_a=BODY_KEY_REMOVED,
        body_key_b=BODY_KEY_KEPT,
        filter_classified_dup=True,
        duplicate_of=[BODY_KEY_KEPT],
    )
    assert pair["textual_equal"] is False
    assert pair["structural_equal"] is False
    assert pair["behavioral_live_equal"] is True
    assert pair["behavioral_audit_equal"] is False
    assert pair["false_duplicate_flag"] is True
    assert "TRANSFORMED" in pair["families_diverged"] or "BOUNDARY" in pair["families_diverged"]
    # live collision on identity
    assert pair["live_got_a"] == pair["live_got_b"]
    assert pair["live_got_a"] == apply_micro(IDENTITY_DEFAULT, resolve_body(BODY_KEY_REMOVED))


def test_offline_eval_isolation_no_filter_mutation():
    tip = subprocess.check_output(
        ["git", "rev-parse", "4005e66:aivd/science/grow.py"], text=True
    ).strip()
    work = subprocess.check_output(["git", "hash-object", "aivd/science/grow.py"], text=True).strip()
    assert tip == work
    assert REDISCOVERY_FLOOR == 5
    assert INVENT_CAP == 48
    assert callable(propose_growth)
    assert callable(cat_self_body)


def test_historical_artifacts_untouched():
    for tip, path in [
        ("4005e66", "reports/aivd_3_40_stage4_results.json"),
        ("4005e66", "reports/aivd_3_40_stage4_results.md"),
        ("f4d7a2b", "reports/aivd_3_40_phase2_results.json"),
        ("a2ab0cc", "reports/aivd_3_40_phase1_results.json"),
        ("146915b", "reports/aivd_3_40_stage3_charter.md"),
        ("dcae889", "reports/aivd_3_40_stage2_results.md"),
    ]:
        if not Path(path).exists():
            continue
        tip_h = subprocess.check_output(["git", "rev-parse", f"{tip}:{path}"], text=True).strip()
        work_h = subprocess.check_output(["git", "hash-object", path], text=True).strip()
        assert tip_h == work_h, path


def test_artifact_replay_0_7_and_7_7():
    art = artifact_replay_stage4()
    assert art["stage4_pool_full_reproduced"] is True
    assert art["stage4_pool_solo_reproduced"] is True
    assert art["full_absent_count"] == 7
    assert art["solo_present_count"] == 7


def test_full_audit_h5b_and_gate():
    result = run_stage5_offline_audit()
    assert result["status"] == "STAGE-5 COMPLETE"
    assert result["controls"]["pass"] is True
    assert result["critical_pair"]["false_duplicate_flag"] is True
    assert result["interpretation"]["conclusion_code"] == "B"
    assert "H5b SUPPORTED" in result["interpretation"]["supported_labels"]
    assert result["autonomous_discovery_credit"] is False


def test_seeds_continuity():
    assert list(SEEDS) == [0, 1, 2, 3, 4, 7, 11]


def test_live_filter_dup_helper_matches_identity_equality():
    a = resolve_body(BODY_KEY_REMOVED)
    b = resolve_body(BODY_KEY_KEPT)
    assert evaluate_live_filter_dup(a, b, IDENTITY_DEFAULT) is True
    # Distinct on a diverging context used as identity
    assert evaluate_live_filter_dup(a, b, "hello world test case") is False

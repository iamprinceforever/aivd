"""Stage-6 offline equivalence-repair benchmark tests — no Sacred; no filter mutation."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aivd.experiments.aivd340.stage5_equiv_audit import resolve_body
from aivd.experiments.aivd340.stage6_benchmark import (
    compute_gt,
    resolve_token,
    run_stage6_offline_benchmark,
)
from aivd.experiments.aivd340.stage6_constants import (
    BODY_KEY_KEPT,
    BODY_KEY_REMOVED,
    DESIGN_DOCS,
    DESIGN_TIP,
    IDENTITY_DEFAULT,
    MECHANISMS,
    S6_MAX_TOTAL_APPLY_MICRO_RUN,
    context_bank_hash,
    load_matrix,
    pinned_core_bank,
    reserve_bank,
)
from aivd.experiments.aivd340.stage6_repairs import ApplyCache, Budget, CLASSIFIERS
from aivd.science.grow import REDISCOVERY_FLOOR, propose_growth

REPO = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def test_design_docs_match_tip():
    for path in DESIGN_DOCS:
        tip = _git("rev-parse", f"{DESIGN_TIP}:{path}")
        work = _git("hash-object", path)
        assert tip == work, path


def test_matrix_not_executed_at_design_tip():
    raw = _git("show", f"{DESIGN_TIP}:reports/aivd_3_40_stage6_matrix.json")
    matrix = json.loads(raw)
    assert matrix.get("executed") is False


def test_grow_unchanged_since_stage4():
    tip = _git("rev-parse", "4005e66:aivd/science/grow.py")
    work = _git("hash-object", "aivd/science/grow.py")
    assert tip == work
    assert callable(propose_growth)
    assert REDISCOVERY_FLOOR == 5


def test_core_and_reserve_bank_sizes():
    core = pinned_core_bank()
    reserve = reserve_bank()
    assert len(core) == 20
    assert len(reserve) == 8
    assert core[0][0] == "CTX-ID-01"
    assert core[1][2] == IDENTITY_DEFAULT  # CTX-ID-02 pinned
    h1 = context_bank_hash(core, reserve)
    h2 = context_bank_hash(core, reserve)
    assert h1 == h2 and len(h1) == 64


def test_gt_critical_is_distinct():
    core = pinned_core_bank()
    a = resolve_body(BODY_KEY_REMOVED)
    b = resolve_body(BODY_KEY_KEPT)
    gt = compute_gt(a, b, core)
    assert gt["gt_label"] == "DISTINCT"
    assert set(gt["families_diverged"]) >= {"TRANSFORMED", "BOUNDARY", "COMPOSITION"}


def test_baseline_collapses_critical_identity():
    a = resolve_body(BODY_KEY_REMOVED)
    b = resolve_body(BODY_KEY_KEPT)
    bud = Budget()
    cache = ApplyCache()
    res = CLASSIFIERS["BASELINE"](a, b, identity=IDENTITY_DEFAULT, cache=cache, budget=bud)
    assert res.label == "duplicate"


def test_repairs_distinguish_critical():
    core = pinned_core_bank()
    reserve = reserve_bank()
    a = resolve_body(BODY_KEY_REMOVED)
    b = resolve_body(BODY_KEY_KEPT)
    for mech in ("R-A", "R-B", "R-C", "R-D"):
        bud = Budget()
        cache = ApplyCache()
        res = CLASSIFIERS[mech](
            a, b, identity=IDENTITY_DEFAULT, core=core, reserve=reserve, cache=cache, budget=bud
        )
        assert res.label == "distinct", mech


def test_true_dup_identical_key():
    core = pinned_core_bank()
    body = resolve_token("IDENTICAL_MICRO_TWICE")
    gt = compute_gt(body, body, core)
    assert gt["gt_label"] == "DUP"
    for mech in MECHANISMS:
        bud = Budget()
        cache = ApplyCache()
        res = CLASSIFIERS[mech](
            body, body, identity=IDENTITY_DEFAULT, core=core, reserve=reserve_bank(),
            cache=cache, budget=bud,
        )
        assert res.label == "duplicate", mech


def test_full_offline_benchmark_gates():
    result = run_stage6_offline_benchmark()
    assert result["final_gate_line"] == "STAGE-6 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED"
    assert result["autonomous_discovery_credit"] is False
    assert result["sacred_executed"] is False
    assert result["filter_replaced"] is False
    assert result["pipeline_mutation"] is False
    assert result["global_budget"]["total_apply_micro"] <= S6_MAX_TOTAL_APPLY_MICRO_RUN
    assert result["mechanisms"]["BASELINE"]["critical_hard_collapse"] == 1
    for mech in ("R-A", "R-B", "R-C", "R-D"):
        m = result["mechanisms"][mech]
        assert m["gate"] == "SUCCESS"
        assert m["FDR"] == 0.0
        assert m["DCR"] == 1.0
        assert m["critical_hard_collapse"] == 0
        assert m["validity"]["valid_for_comparison"] is True
    held = result["held_out_S6_HO_CRIT"]
    assert held["BASELINE"]["pred"] == "duplicate"
    for mech in ("R-A", "R-B", "R-C", "R-D"):
        assert held[mech]["pred"] == "distinct"


def test_no_target_special_case_branch_in_repairs_source():
    src = (REPO / "aivd/experiments/aivd340/stage6_repairs.py").read_text()
    forbidden = ["ODD_STRIDE", "CAT_SELF", "S6-HO-CRIT", "BODY_KEY_REMOVED", "odd_cat"]
    for tok in forbidden:
        assert tok not in src, tok

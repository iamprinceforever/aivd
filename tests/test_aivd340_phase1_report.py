"""Phase-1 report: diagnosis honesty, H3 inconclusive, R1b caveat, final status."""
from __future__ import annotations

from pathlib import Path

from aivd.experiments.aivd340.phase1_normalize import normalize_all
from aivd.experiments.aivd340.phase1_replay import replay_all
from aivd.experiments.aivd340.phase1_report import (
    FINAL_COMPLETE,
    build_all_divergences,
    build_results,
    render_results_md,
)

ROOT = Path(__file__).resolve().parents[1]


def _pipeline():
    batch = normalize_all(repo_root=ROOT)
    replay_batch = replay_all(batch)
    divergences = build_all_divergences(batch, replay_batch)
    results = build_results(batch, replay_batch, divergences)
    return batch, replay_batch, divergences, results


def test_r1_s_supports_h1_not_h3():
    _, _, divergences, results = _pipeline()
    r1 = [d for d in divergences if d["condition_id"] == "BH-R1"]
    assert len(r1) == 7
    for d in r1:
        assert d["diagnosis_label"] == "SUPPORTED H1"
        assert d["supported_hypotheses"] == ["H1"]
        assert d["s_questions"]["Q1"] == "no"
        assert d["s_questions"]["Q4"] == "UNKNOWN"
        assert d["s_questions"]["Q5"] == "UNKNOWN"
        assert "H3" not in d["supported_hypotheses"]
    assert results["diagnosis_distribution"]["n_supported_h3"] == 0


def test_r1b_s_supports_h2_not_h3_with_caveat():
    _, _, divergences, _ = _pipeline()
    r1b = [d for d in divergences if d["condition_id"] == "BH-R1b"]
    assert len(r1b) == 7
    for d in r1b:
        assert d["diagnosis_label"] == "SUPPORTED H2"
        assert d["supported_hypotheses"] == ["H2"]
        assert d["r1b_caveat_applies"] is True
        assert d["s_questions"]["Q1"] == "yes"
        assert d["s_questions"]["Q2"] == "no"
        assert d["s_questions"]["Q4"] == "UNKNOWN"
        assert d["s_questions"]["Q5"] == "UNKNOWN"
        assert "H3" not in d["h3_note"] or "INCONCLUSIVE" in d["h3_note"]


def test_final_status_line_and_md():
    _, _, _, results = _pipeline()
    assert results["final_status"] == FINAL_COMPLETE
    assert results["tooling_valid"] is True
    assert results["scope"]["sacred_authorized"] is False
    assert results["scope"]["phase2_authorized"] is False
    md = render_results_md(results)
    assert FINAL_COMPLETE in md
    assert "7a3457e" in md
    assert md.strip().endswith(FINAL_COMPLETE)


def test_exit_gates_pass():
    _, _, _, results = _pipeline()
    for k, v in results["exit_gates"].items():
        assert v == "PASS", (k, v)

"""Phase-1 normalize: schema, provenance, UNKNOWN preservation, 28-cell coverage."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aivd.experiments.aivd340.phase1_normalize import (
    SEEDS,
    UNKNOWN_FIELDS,
    list_expected_trajectories,
    normalize_all,
    normalize_episode,
    write_normalized_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]


def test_28_trajectories_present():
    rows = list_expected_trajectories()
    assert len(rows) == 28
    for r in rows:
        assert (ROOT / r["artifact_path"]).is_file(), r["artifact_path"]


def test_normalize_all_coverage():
    batch = normalize_all(repo_root=ROOT)
    assert batch["n_expected"] == 28
    assert batch["n_present"] == 28
    assert batch["n_missing"] == 0
    assert len(batch["episodes"]) == 28


def test_observed_label_and_unknown_fields():
    ep = normalize_episode(
        ROOT / "reports/aivd_3_40_stage2/runs/BH-R1_seed0_U.json"
    )
    assert ep["envelope"]["record_label"] == "observed"
    for ev in ep["observed_events"]:
        assert ev["record_label"] == "observed"
        assert "full_candidate_pool_snapshots" in ev["unknown_fields_explicit"]
        assert ev["field_coverage_notes"]["pool"] == "UNKNOWN"
        assert ev["field_coverage_notes"]["score"] == "UNKNOWN"
        assert ev["field_coverage_notes"]["ranking"] == "UNKNOWN"
        assert ev["field_coverage_notes"]["selected"] == "UNKNOWN"
        assert ev["field_coverage_notes"]["features_used"] == "UNKNOWN"
        # must not invent scores/ranks/selected
        assert "candidate_scores" not in ev or ev.get("candidate_scores") in (None, "UNKNOWN")
        assert ev["evidence_status"]["candidate_scores"] == "UNKNOWN"
        assert ev["evidence_status"]["ranking"] == "UNKNOWN"
        assert ev["evidence_status"]["selected_candidate"] == "UNKNOWN"
        assert ev["evidence_status"]["features_used"] == "UNKNOWN"


def test_provenance_path_to_original():
    path = ROOT / "reports/aivd_3_40_stage2/runs/BH-R1_seed0_S.json"
    raw = json.loads(path.read_text())
    ep = normalize_episode(path)
    assert ep["source_artifact_path"].endswith("BH-R1_seed0_S.json")
    assert ep["source_artifact_sha256"]
    assert len(ep["observed_events"]) == len(raw["generation_records"])
    for ev, gr in zip(ep["observed_events"], raw["generation_records"]):
        assert ev["provenance"]["path"] == ep["source_artifact_path"]
        assert ev["generation_id"] == gr["generation_id"]
        assert ev["body_key"] == (gr.get("body_key") or None)


def test_unknown_not_reconstructed_from_downstream():
    """Even if a body appears later, we must not invent a prior pool/score/selected."""
    ep = normalize_episode(
        ROOT / "reports/aivd_3_40_stage2/runs/BH-R1b_seed0_S.json"
    )
    blob = json.dumps(ep)
    assert '"selected_candidate":' not in blob or "UNKNOWN" in blob
    for key in ("candidate_pool", "ranking_table", "features_used_map"):
        assert key not in ep
    for u in UNKNOWN_FIELDS:
        assert u in ep["unknown_fields_explicit"]


def test_write_artifacts_roundtrip(tmp_path: Path):
    batch = normalize_all(repo_root=ROOT)
    paths = write_normalized_artifacts(batch, tmp_path)
    assert Path(paths["observed_events_jsonl"]).is_file()
    lines = Path(paths["observed_events_jsonl"]).read_text().strip().splitlines()
    assert len(lines) > 28  # envelope + generation rows
    for line in lines[:5]:
        row = json.loads(line)
        assert row["record_label"] == "observed"

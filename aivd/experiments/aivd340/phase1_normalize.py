"""AIVD 3.40 Phase-1 — observational normalize of Stage-2 trajectories.

READ-ONLY of reports/aivd_3_40_stage2/**.
Never regenerates discovery; never fills UNKNOWN pool/score/rank/selected/features_used.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "aivd340.phase1.replay.v1"
SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 7, 11)
CONDITIONS: tuple[str, ...] = ("BH-R1", "BH-R1b")
ROLES: tuple[str, ...] = ("S", "U")

STAGE2_RUNS_DIR = Path("reports/aivd_3_40_stage2/runs")

UNKNOWN_FIELDS: tuple[str, ...] = (
    "full_candidate_pool_snapshots",
    "candidate_scores",
    "candidate_ranking_tables",
    "explicit_selected_candidate_decision_records",
    "features_used_maps",
    "rejection_skip_reason_enums_beyond_stop_failure_notes",
)

FIELD_COVERAGE_NOTES: dict[str, str] = {
    "pool": "UNKNOWN",
    "score": "UNKNOWN",
    "ranking": "UNKNOWN",
    "selected": "UNKNOWN",
    "features_used": "UNKNOWN",
}

AUDIT_CELL = {
    ("BH-R1", "S"): "AUD-S2-BHR1-S",
    ("BH-R1", "U"): "AUD-S2-BHR1-U",
    ("BH-R1b", "S"): "AUD-S2-BHR1b-S",
    ("BH-R1b", "U"): "AUD-S2-BHR1b-U",
}


def expected_artifact_path(condition_id: str, seed: int, role: str) -> Path:
    return STAGE2_RUNS_DIR / f"{condition_id}_seed{seed}_{role}.json"


def list_expected_trajectories() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition_id in CONDITIONS:
        for role in ROLES:
            for seed in SEEDS:
                path = expected_artifact_path(condition_id, seed, role)
                rows.append(
                    {
                        "condition_id": condition_id,
                        "role": role,
                        "seed": seed,
                        "artifact_path": str(path),
                        "audit_cell_id": AUDIT_CELL[(condition_id, role)],
                        "present": path.is_file(),
                    }
                )
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _event_kind(kind: Any, action: Any) -> str:
    k = (kind or "").lower()
    a = (action or "").lower()
    if a == "invent" or k == "atom" and a == "invent":
        return "invent"
    if a == "grow" or k == "grow":
        return "grow"
    if a == "compose" or k == "compose":
        return "compose"
    if a == "rediscover" or a == "firewall" or k == "firewall":
        return a if a in ("rediscover", "firewall") else k
    if a:
        return a
    if k:
        return k
    return "other"


def _methods_excerpt(methods_log: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in methods_log or []:
        ev = m.get("event")
        if ev in ("invent", "atom_materialize") or (
            isinstance(ev, str) and "invent" in ev.lower()
        ):
            row = {"event": str(ev)}
            if "ops" in m:
                row["ops"] = m.get("ops")
            if "op" in m:
                row["op"] = m.get("op")
            if "key" in m:
                row["key"] = m.get("key")
            out.append(row)
    return out


def _invent_ops_list(methods_log: list[dict[str, Any]] | None) -> list[str]:
    ops: list[str] = []
    for m in methods_log or []:
        if m.get("event") == "atom_materialize" and m.get("key"):
            ops.append(str(m["key"]))
        elif m.get("event") == "invent" and m.get("ops"):
            ops.append(str(m["ops"]))
    return ops


def evidence_status_for_field(name: str, value: Any) -> str:
    if name in (
        "candidate_scores",
        "ranking",
        "selected_candidate",
        "features_used",
        "full_candidate_pool",
    ):
        return "UNKNOWN"
    if value is None or value == "" or value == []:
        if name in (
            "verification_state",
            "body_key",
            "parent_generation_id",
            "proposal_origin",
            "semantic_class",
            "budget_after",
            "leftover_after",
        ):
            return "OBSERVED_EMPTY"
        return "NOT_RECORDED"
    return "OBSERVED"


def normalize_generation_record(
    gr: dict[str, Any],
    *,
    envelope: dict[str, Any],
    source_path: str,
    methods_excerpt: list[dict[str, Any]],
    invent_ops: list[str],
) -> dict[str, Any]:
    condition_id = envelope["condition_id"]
    role = envelope["role"]
    seed = int(envelope["seed"])
    kind = gr.get("kind")
    action = gr.get("action")
    body_key = gr.get("body_key") or None
    fields = {
        "generation_id": gr.get("generation_id"),
        "parent_generation_id": gr.get("parent_generation_id"),
        "candidate_origin": gr.get("candidate_origin"),
        "proposal_origin": gr.get("proposal_origin"),
        "body_key": body_key,
        "candidate_id": gr.get("candidate_id"),
        "candidate": gr.get("candidate"),
        "semantic_class": gr.get("semantic_class") or None,
        "verification_state": gr.get("verification_state") or None,
        "budget_before": gr.get("budget_before"),
        "budget_after": gr.get("budget_after"),
        "leftover": gr.get("leftover"),
        "leftover_after": gr.get("leftover_after"),
        "kind": kind,
        "action": action,
        "firewall_epoch": gr.get("firewall_epoch"),
    }
    evidence = {k: evidence_status_for_field(k, v) for k, v in fields.items()}
    evidence.update(
        {
            "full_candidate_pool": "UNKNOWN",
            "candidate_scores": "UNKNOWN",
            "ranking": "UNKNOWN",
            "selected_candidate": "UNKNOWN",
            "features_used": "UNKNOWN",
        }
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_label": "observed",
        "audit_cell_id": AUDIT_CELL[(condition_id, role)],
        "condition_id": condition_id,
        "target_role": role,
        "seed": seed,
        "plant_id": envelope.get("plant_id"),
        "source_artifact_path": source_path,
        "source_artifact_sha256": None,  # filled by episode normalizer
        "source_generation_id": gr.get("generation_id"),
        "firewall_epoch": gr.get("firewall_epoch", envelope.get("firewall_epoch")),
        "field_coverage_notes": dict(FIELD_COVERAGE_NOTES),
        "event_kind": _event_kind(kind, action),
        **fields,
        "terminal_state": None,  # envelope-level; set on envelope row
        "strict_independence": None,
        "leftover_at_firewall_decision": None,
        "language_programs": [],
        "methods_log_excerpt": methods_excerpt,
        "derived": {
            "produced_body_in_generation_records": bool(body_key),
            "invent_ops_list": list(invent_ops),
        },
        "unknown_fields_explicit": list(UNKNOWN_FIELDS),
        "evidence_status": evidence,
        "provenance": {
            "path": source_path,
            "generation_id": gr.get("generation_id"),
            "record_id": gr.get("record_id"),
        },
        "r1b_observational_only": condition_id == "BH-R1b",
    }


def normalize_envelope_row(
    envelope: dict[str, Any],
    *,
    source_path: str,
    source_sha256: str,
) -> dict[str, Any]:
    condition_id = envelope["condition_id"]
    role = envelope["role"]
    seed = int(envelope["seed"])
    programs = []
    lang = envelope.get("language") or {}
    if isinstance(lang, dict):
        programs = list(lang.get("programs") or [])
    methods_excerpt = _methods_excerpt(envelope.get("methods_log"))
    invent_ops = _invent_ops_list(envelope.get("methods_log"))
    return {
        "schema_version": SCHEMA_VERSION,
        "record_label": "observed",
        "event_kind": "terminal",
        "audit_cell_id": AUDIT_CELL[(condition_id, role)],
        "condition_id": condition_id,
        "target_role": role,
        "seed": seed,
        "plant_id": envelope.get("plant_id"),
        "source_artifact_path": source_path,
        "source_artifact_sha256": source_sha256,
        "source_generation_id": None,
        "firewall_epoch": envelope.get("firewall_epoch"),
        "field_coverage_notes": dict(FIELD_COVERAGE_NOTES),
        "generation_id": f"envelope:{condition_id}:seed{seed}:{role}",
        "parent_generation_id": None,
        "candidate_origin": None,
        "proposal_origin": None,
        "body_key": None,
        "candidate_id": None,
        "candidate": None,
        "semantic_class": None,
        "verification_state": None,
        "budget_before": None,
        "budget_after": None,
        "leftover": None,
        "leftover_after": None,
        "kind": "terminal",
        "action": "terminal",
        "terminal_state": envelope.get("terminal_state"),
        "strict_independence": envelope.get("strict_independence"),
        "pipeline_verified": envelope.get("pipeline_verified"),
        "secret_found": envelope.get("secret_found"),
        "discovered": envelope.get("discovered"),
        "stop_reason": envelope.get("stop_reason"),
        "failure_class": envelope.get("failure_class"),
        "budget_used": envelope.get("budget_used"),
        "episode_budget": envelope.get("episode_budget"),
        "leftover_at_firewall_decision": envelope.get("leftover_at_firewall_decision"),
        "representation": envelope.get("representation"),
        "invention_mode": envelope.get("invention_mode"),
        "INVENT_CAP": envelope.get("INVENT_CAP"),
        "REDISCOVERY_FLOOR": envelope.get("REDISCOVERY_FLOOR"),
        "provenance_leak": envelope.get("provenance_leak"),
        "language_programs": programs,
        "methods_log_excerpt": methods_excerpt,
        "derived": {
            "produced_body_in_generation_records": False,
            "invent_ops_list": invent_ops,
            "n_generation_records": len(envelope.get("generation_records") or []),
            "n_methods_log": len(envelope.get("methods_log") or []),
        },
        "unknown_fields_explicit": list(UNKNOWN_FIELDS),
        "evidence_status": {
            "terminal_state": "OBSERVED",
            "pipeline_verified": "OBSERVED",
            "strict_independence": "OBSERVED",
            "firewall_epoch": "OBSERVED",
            "full_candidate_pool": "UNKNOWN",
            "candidate_scores": "UNKNOWN",
            "ranking": "UNKNOWN",
            "selected_candidate": "UNKNOWN",
            "features_used": "UNKNOWN",
        },
        "provenance": {"path": source_path, "envelope": True},
        "r1b_observational_only": condition_id == "BH-R1b",
    }


def normalize_episode(path: Path) -> dict[str, Any]:
    """Normalize one Stage-2 run JSON into Phase-1 OBSERVED bundle."""
    if not path.is_file():
        raise FileNotFoundError(f"missing Stage-2 trajectory: {path}")
    raw = path.read_text(encoding="utf-8")
    envelope = json.loads(raw)
    source_path = str(path).replace("\\", "/")
    # Prefer repo-relative path
    if "reports/aivd_3_40_stage2/" in source_path:
        source_path = source_path[source_path.index("reports/aivd_3_40_stage2/") :]
    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    methods_excerpt = _methods_excerpt(envelope.get("methods_log"))
    invent_ops = _invent_ops_list(envelope.get("methods_log"))
    observed_events: list[dict[str, Any]] = []
    for gr in envelope.get("generation_records") or []:
        row = normalize_generation_record(
            gr,
            envelope=envelope,
            source_path=source_path,
            methods_excerpt=methods_excerpt,
            invent_ops=invent_ops,
        )
        row["source_artifact_sha256"] = sha
        observed_events.append(row)
    envelope_row = normalize_envelope_row(
        envelope, source_path=source_path, source_sha256=sha
    )
    produced_bodies = sorted(
        {
            str(e["body_key"])
            for e in observed_events
            if e.get("body_key")
        }
    )
    return {
        "schema_version": "aivd340.phase1.normalized_episode.v1",
        "source_artifact_path": source_path,
        "source_artifact_sha256": sha,
        "condition_id": envelope["condition_id"],
        "target_role": envelope["role"],
        "seed": int(envelope["seed"]),
        "plant_id": envelope.get("plant_id"),
        "audit_cell_id": AUDIT_CELL[(envelope["condition_id"], envelope["role"])],
        "representation": envelope.get("representation"),
        "envelope": envelope_row,
        "observed_events": observed_events,
        "produced_bodies": produced_bodies,
        "unknown_fields_explicit": list(UNKNOWN_FIELDS),
        "field_coverage_notes": dict(FIELD_COVERAGE_NOTES),
        "r1b_observational_only": envelope["condition_id"] == "BH-R1b",
        "r1b_caveat_commit": "7a3457e",
    }


def normalize_all(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(".")
    cells: list[dict[str, Any]] = []
    missing: list[str] = []
    for meta in list_expected_trajectories():
        path = root / meta["artifact_path"]
        if not path.is_file():
            missing.append(meta["artifact_path"])
            continue
        cells.append(normalize_episode(path))
    return {
        "schema_version": "aivd340.phase1.normalized_batch.v1",
        "n_expected": 28,
        "n_present": len(cells),
        "n_missing": len(missing),
        "missing": missing,
        "unknown_fields_explicit": list(UNKNOWN_FIELDS),
        "r1b_caveat": (
            "Commit 7a3457e trimmed invent basis after smoke before Sacred; "
            "R1b measured but not pure Commit-B prereg. Preserve."
        ),
        "episodes": cells,
    }


def write_normalized_artifacts(
    batch: dict[str, Any],
    out_dir: Path,
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    observed_path = out_dir / "observed_events.jsonl"
    episodes_path = out_dir / "normalized_episodes.json"
    inventory_path = out_dir / "normalize_inventory.json"
    with observed_path.open("w", encoding="utf-8") as f:
        for ep in batch["episodes"]:
            f.write(json.dumps(ep["envelope"], sort_keys=True) + "\n")
            for ev in ep["observed_events"]:
                f.write(json.dumps(ev, sort_keys=True) + "\n")
    episodes_path.write_text(json.dumps(batch, indent=2, sort_keys=True) + "\n")
    inv = {
        "n_expected": batch["n_expected"],
        "n_present": batch["n_present"],
        "n_missing": batch["n_missing"],
        "missing": batch["missing"],
        "cells": [
            {
                "audit_cell_id": e["audit_cell_id"],
                "condition_id": e["condition_id"],
                "target_role": e["target_role"],
                "seed": e["seed"],
                "source_artifact_path": e["source_artifact_path"],
                "source_artifact_sha256": e["source_artifact_sha256"],
                "n_observed_events": len(e["observed_events"]),
                "n_produced_bodies": len(e["produced_bodies"]),
            }
            for e in batch["episodes"]
        ],
    }
    inventory_path.write_text(json.dumps(inv, indent=2, sort_keys=True) + "\n")
    return {
        "observed_events_jsonl": str(observed_path),
        "normalized_episodes_json": str(episodes_path),
        "normalize_inventory_json": str(inventory_path),
    }


__all__ = [
    "SEEDS",
    "CONDITIONS",
    "ROLES",
    "UNKNOWN_FIELDS",
    "normalize_episode",
    "normalize_all",
    "write_normalized_artifacts",
    "list_expected_trajectories",
    "expected_artifact_path",
    "sha256_file",
]

"""AIVD 3.40 Phase-1 — evaluator-only offline counterfactual replay.

MUST NOT:
- import discovery invent/grow/select loops
- mutate Stage-2 artifacts
- feed CF results into discovery
- present CF accept as Sacred VERIFIED
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.phase1_normalize import SEEDS

# Structural geometry markers (evaluator-side scoring only — not discovery features).
ODD_STRIDE_ATOM = "MAPT(SLICE:1,2(TOK))"
ODD_CAT_SELF = "MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))"
EVEN_CAT_SELF = "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))"
ROTATE_LEFT_BODY = "MAPT(CAT(SLICE:1,1(TOK)|AT:0))"

# Forbidden discovery imports — kept as a documented denylist for tests.
FORBIDDEN_DISCOVERY_MODULES = (
    "aivd.science.designer",
    "aivd.science.atom_synth",
    "aivd.science.grow",
    "aivd.science.representation",
    "aivd.science.language",
    "aivd.science.propose_atoms",
)


def is_odd_stride_atom(body_key: str | None) -> bool:
    if not body_key:
        return False
    return body_key == ODD_STRIDE_ATOM or (
        "SLICE:1,2(TOK)" in body_key and "CAT(" not in body_key
    )


def is_finished_odd_cat_self(body_key: str | None) -> bool:
    if not body_key:
        return False
    return body_key == ODD_CAT_SELF or (
        "CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))" in body_key
    )


def is_even_cat_self(body_key: str | None) -> bool:
    if not body_key:
        return False
    return "CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK))" in body_key


def is_rotate_left_body(body_key: str | None) -> bool:
    if not body_key:
        return False
    return body_key == ROTATE_LEFT_BODY or (
        "SLICE:1,1(TOK)" in body_key and "AT:0" in body_key and "CAT(" in body_key
    )


def structural_s_geometry_match(body_key: str | None) -> bool:
    """Offline structural match to S plant geometry (odd-index CAT-self)."""
    return is_finished_odd_cat_self(body_key)


def structural_u_geometry_match(body_key: str | None) -> bool:
    """Offline structural match to U plant geometry (rotate-left-1)."""
    return is_rotate_left_body(body_key)


def enumerate_produced_bodies(episode: dict[str, Any]) -> list[str]:
    return list(episode.get("produced_bodies") or [])


def path_prefix_check(episode: dict[str, Any]) -> dict[str, Any]:
    """First missing stage on invent→grow→select→verify using OBSERVED only."""
    bodies = enumerate_produced_bodies(episode)
    events = episode.get("observed_events") or []
    invent_bodies = [
        e.get("body_key")
        for e in events
        if e.get("event_kind") == "invent" and e.get("body_key")
    ]
    grow_bodies = [
        e.get("body_key")
        for e in events
        if e.get("event_kind") in ("grow", "compose") and e.get("body_key")
    ]
    role = episode["target_role"]
    env = episode["envelope"]

    has_odd_atom = any(is_odd_stride_atom(b) for b in invent_bodies + bodies)
    has_odd_finished = any(is_finished_odd_cat_self(b) for b in grow_bodies + bodies)
    has_rotate = any(is_rotate_left_body(b) for b in invent_bodies + bodies)
    verified = bool(env.get("pipeline_verified"))

    if role == "U":
        if verified and has_rotate:
            first_missing = None
            note = "U path reconstructible: rotate-class body OBSERVED and terminal VERIFIED"
        elif verified:
            first_missing = None
            note = "U terminal VERIFIED; rotate body may be atom/rediscover (check census)"
        else:
            first_missing = "verify"
            note = "U not verified in OBSERVED envelope"
        return {
            "role": role,
            "has_required_atom_direction": has_rotate,
            "has_finished_required_body": has_rotate,
            "explicit_selected_recorded": False,  # UNKNOWN / not recorded
            "verified": verified,
            "first_missing_stage": first_missing,
            "note": note,
            "unknown_stages": ["select", "rank", "pool"],
        }

    # S
    if not has_odd_atom:
        first_missing = "invent"
    elif not has_odd_finished:
        first_missing = "grow"
    else:
        # finished odd CAT-self present in records but not verified —
        # select is UNKNOWN so cannot claim selection failure definitively
        first_missing = "select_or_verify_UNKNOWN"
    return {
        "role": role,
        "has_required_atom_direction": has_odd_atom,
        "has_finished_required_body": has_odd_finished,
        "explicit_selected_recorded": False,
        "verified": verified,
        "first_missing_stage": first_missing,
        "note": (
            "S finished odd CAT-self absent from generation_records"
            if not has_odd_finished
            else "finished body present; select/rank UNKNOWN"
        ),
        "unknown_stages": ["select", "rank", "pool"],
    }


def what_if_grow(
    episode: dict[str, Any],
    *,
    parent_atom_body_key: str,
    grow_op: str = "CAT_SELF",
) -> dict[str, Any]:
    """Counterfactual: if generic legal grow applied to historical parent atom."""
    if grow_op != "CAT_SELF":
        raise ValueError("Phase-1 only authorizes generic CAT_SELF grow_op")
    # Locate parent in OBSERVED invent/rediscover set
    parent_observed = parent_atom_body_key in enumerate_produced_bodies(episode)
    if parent_atom_body_key == ODD_STRIDE_ATOM or is_odd_stride_atom(parent_atom_body_key):
        hyp_body = ODD_CAT_SELF
        would_match_s = True
        would_match_u = False
    elif parent_atom_body_key.endswith("SLICE:0,2(TOK))") or "SLICE:0,2(TOK)" in (
        parent_atom_body_key or ""
    ):
        hyp_body = EVEN_CAT_SELF
        would_match_s = False
        would_match_u = False
    else:
        hyp_body = f"MAPT(CAT({_inner(parent_atom_body_key)}|{_inner(parent_atom_body_key)}))"
        would_match_s = structural_s_geometry_match(hyp_body)
        would_match_u = structural_u_geometry_match(hyp_body)

    env = episode["envelope"]
    return {
        "schema_version": "aivd340.phase1.replay.v1",
        "record_label": "counterfactual",
        "counterfactual_op": "what_if_grow",
        "counterfactual_of_generation_id": None,
        "decision_point_ref": {
            "source_artifact_path": episode["source_artifact_path"],
            "generation_id": None,
            "firewall_epoch": env.get("firewall_epoch"),
            "note": "historical anchor only; trajectory not mutated",
        },
        "hypothesis_input": {
            "body_key": hyp_body,
            "parent_atom_body_key": parent_atom_body_key,
            "grow_op": grow_op,
            "grow_op_must_be_generic_legal": True,
            "parent_observed_in_records": parent_observed,
        },
        "evaluator_result": {
            "would_accept": would_match_s if episode["target_role"] == "S" else would_match_u,
            "would_trigger_plant": would_match_s
            if episode["target_role"] == "S"
            else would_match_u,
            "terminal_class_hypothetical": (
                "STRUCTURAL_GEOMETRY_MATCH"
                if (
                    would_match_s
                    if episode["target_role"] == "S"
                    else would_match_u
                )
                else "STRUCTURAL_GEOMETRY_MISS"
            ),
            "reason": (
                "Offline structural geometry check only — not LLM plant fire; "
                "not Sacred VERIFIED"
            ),
            "deterministic": True,
        },
        "parent_state": {
            "condition_id": episode["condition_id"],
            "seed": episode["seed"],
            "role": episode["target_role"],
            "terminal_state_observed": env.get("terminal_state"),
        },
        "not_simulated": [
            "live invent",
            "live ranking/selection",
            "discovery model state update",
            "Sacred credit",
            "LLM generate / plant.probe",
            "full candidate pool membership",
        ],
        "discovery_feedback": False,
        "sacred_credit": False,
        "counterfactual_statement": (
            "COUNTERFACTUAL only — not historical discovery; "
            "CF success ≠ AIVD discovered X"
        ),
        "notes": "CF must not modify discovery/model state or Stage-2 artifacts",
        "r1b_observational_only": episode.get("r1b_observational_only", False),
    }


def _inner(body_key: str) -> str:
    # MAPT(X) -> X
    if body_key.startswith("MAPT(") and body_key.endswith(")"):
        return body_key[5:-1]
    return body_key


def what_if_select(episode: dict[str, Any], *, body_key: str) -> dict[str, Any]:
    """Counterfactual: if historical body were selected for verification."""
    observed = body_key in enumerate_produced_bodies(episode)
    role = episode["target_role"]
    match = (
        structural_s_geometry_match(body_key)
        if role == "S"
        else structural_u_geometry_match(body_key)
    )
    env = episode["envelope"]
    return {
        "schema_version": "aivd340.phase1.replay.v1",
        "record_label": "counterfactual",
        "counterfactual_op": "what_if_select",
        "counterfactual_of_generation_id": None,
        "decision_point_ref": {
            "source_artifact_path": episode["source_artifact_path"],
            "generation_id": None,
            "firewall_epoch": env.get("firewall_epoch"),
            "note": "historical anchor only; trajectory not mutated",
        },
        "hypothesis_input": {
            "body_key": body_key,
            "parent_atom_body_key": None,
            "grow_op": None,
            "grow_op_must_be_generic_legal": True,
            "body_observed_in_records": observed,
        },
        "evaluator_result": {
            "would_accept": match,
            "would_trigger_plant": match,
            "terminal_class_hypothetical": (
                "STRUCTURAL_GEOMETRY_MATCH" if match else "STRUCTURAL_GEOMETRY_MISS"
            ),
            "reason": (
                "Offline structural geometry check only — not LLM plant fire; "
                "not Sacred VERIFIED. Explicit selection decision was UNKNOWN "
                "in Stage-2 artifacts."
            ),
            "deterministic": True,
        },
        "parent_state": {
            "condition_id": episode["condition_id"],
            "seed": episode["seed"],
            "role": role,
            "terminal_state_observed": env.get("terminal_state"),
        },
        "not_simulated": [
            "ranking table",
            "score competition",
            "live selection policy",
            "discovery feedback",
            "Sacred credit",
            "LLM generate / plant.probe",
        ],
        "discovery_feedback": False,
        "sacred_credit": False,
        "counterfactual_statement": (
            "COUNTERFACTUAL only — not historical discovery; "
            "CF success ≠ AIVD discovered X"
        ),
        "notes": "CF must not modify discovery/model state or Stage-2 artifacts",
        "r1b_observational_only": episode.get("r1b_observational_only", False),
    }


def reconstruct_u_positive_control(episode: dict[str, Any]) -> dict[str, Any]:
    """Gate E: reconstruct BH-R1 × U without requiring UNKNOWN fields."""
    assert episode["condition_id"] == "BH-R1"
    assert episode["target_role"] == "U"
    env = episode["envelope"]
    bodies = enumerate_produced_bodies(episode)
    path = path_prefix_check(episode)
    has_rotate = any(is_rotate_left_body(b) for b in bodies)
    terminal_ok = env.get("terminal_state") == "TerminalState.VERIFIED"
    verified_ok = env.get("pipeline_verified") is True
    strict_ok = env.get("strict_independence") is True
    fw = env.get("firewall_epoch")
    fw_ok = isinstance(fw, int) and fw >= 1
    secret_ok = env.get("secret_found") is True
    # Reconstruct invent→firewall→rediscover/grow chain from OBSERVED kinds
    kinds = [e.get("event_kind") for e in episode.get("observed_events") or []]
    has_invent = "invent" in kinds
    has_firewall = "firewall" in kinds
    pass_gate = all(
        [terminal_ok, verified_ok, strict_ok, fw_ok, secret_ok, has_invent, has_rotate]
    )
    return {
        "seed": episode["seed"],
        "source_artifact_path": episode["source_artifact_path"],
        "pass": pass_gate,
        "checks": {
            "terminal_state_VERIFIED": terminal_ok,
            "pipeline_verified": verified_ok,
            "strict_independence": strict_ok,
            "firewall_epoch_ge_1": fw_ok,
            "secret_found": secret_ok,
            "invent_events_present": has_invent,
            "firewall_event_present": has_firewall,
            "rotate_left_body_in_produced_census": has_rotate,
        },
        "path_prefix": path,
        "produced_bodies": bodies,
        "unknown_fields_not_required": list(
            episode.get("unknown_fields_explicit") or []
        ),
        "note": (
            "Reconstruction uses OBSERVED envelope + generation_records only; "
            "pool/score/rank/selected NOT used"
        ),
    }


def run_u_positive_control_gate(batch: dict[str, Any]) -> dict[str, Any]:
    u_eps = [
        e
        for e in batch["episodes"]
        if e["condition_id"] == "BH-R1" and e["target_role"] == "U"
    ]
    results = [reconstruct_u_positive_control(e) for e in u_eps]
    n_pass = sum(1 for r in results if r["pass"])
    n = len(results)
    aggregate_ok = n == 7 and n_pass == 7
    return {
        "gate": "E_u_bhr1_positive_control_reconstruction",
        "n_seeds_expected": 7,
        "n_seeds_present": n,
        "n_pass": n_pass,
        "n_fail": n - n_pass,
        "aggregate_FIV": {"firewall": n_pass, "independent_strict": n_pass, "verified": n_pass}
        if aggregate_ok
        else {"firewall": n_pass, "independent_strict": "partial", "verified": n_pass},
        "status": "PASS" if aggregate_ok else "FAIL",
        "per_seed": results,
        "stop_if_fail": True,
        "message": (
            "BH-R1×U F7/I7/V7 reconstructible from OBSERVED fields"
            if aggregate_ok
            else "PHASE-1 TOOLING INVALID — U positive control reconstruction failed"
        ),
    }


def replay_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Run CF operators for one episode (evaluator-only)."""
    bodies = enumerate_produced_bodies(episode)
    cf_rows: list[dict[str, Any]] = []
    # enumerate
    enum = {
        "schema_version": "aivd340.phase1.replay.v1",
        "record_label": "counterfactual",
        "counterfactual_op": "enumerate_produced_bodies",
        "produced_bodies": bodies,
        "discovery_feedback": False,
        "sacred_credit": False,
        "counterfactual_statement": (
            "Census of OBSERVED produced bodies — not a live pool snapshot"
        ),
        "not_simulated": ["live candidate pool", "scores", "ranking"],
        "parent_state": {
            "condition_id": episode["condition_id"],
            "seed": episode["seed"],
            "role": episode["target_role"],
        },
    }
    cf_rows.append(enum)
    prefix = path_prefix_check(episode)
    cf_rows.append(
        {
            "schema_version": "aivd340.phase1.replay.v1",
            "record_label": "counterfactual",
            "counterfactual_op": "path_prefix_check",
            "result": prefix,
            "discovery_feedback": False,
            "sacred_credit": False,
            "counterfactual_statement": "OBSERVED path-prefix analysis",
            "not_simulated": ["unlogged selection decisions"],
            "parent_state": {
                "condition_id": episode["condition_id"],
                "seed": episode["seed"],
                "role": episode["target_role"],
            },
        }
    )
    # what_if_grow for odd-stride parent when OBSERVED
    if any(is_odd_stride_atom(b) for b in bodies):
        cf_rows.append(what_if_grow(episode, parent_atom_body_key=ODD_STRIDE_ATOM))
    # what_if_grow for even parent (shows CF even CAT-self ≠ S)
    if any("SLICE:0,2(TOK)" in (b or "") and "CAT(" not in (b or "") for b in bodies):
        cf_rows.append(
            what_if_grow(episode, parent_atom_body_key="MAPT(SLICE:0,2(TOK))")
        )
    # what_if_select on OBSERVED rotate body (U) or CF odd CAT-self (S)
    if episode["target_role"] == "U":
        for b in bodies:
            if is_rotate_left_body(b):
                cf_rows.append(what_if_select(episode, body_key=b))
                break
    else:
        # Only select CF on bodies that exist in records OR the CF-grown odd CAT-self
        if any(is_finished_odd_cat_self(b) for b in bodies):
            for b in bodies:
                if is_finished_odd_cat_self(b):
                    cf_rows.append(what_if_select(episode, body_key=b))
                    break
        elif any(is_odd_stride_atom(b) for b in bodies):
            # CF body from grow — still labeled counterfactual; not historical
            cf_rows.append(what_if_select(episode, body_key=ODD_CAT_SELF))

    return {
        "source_artifact_path": episode["source_artifact_path"],
        "condition_id": episode["condition_id"],
        "target_role": episode["target_role"],
        "seed": episode["seed"],
        "path_prefix": prefix,
        "counterfactual_events": cf_rows,
    }


def replay_all(batch: dict[str, Any]) -> dict[str, Any]:
    u_gate = run_u_positive_control_gate(batch)
    replays = [replay_episode(e) for e in batch["episodes"]]
    return {
        "schema_version": "aivd340.phase1.replay_batch.v1",
        "u_positive_control_gate": u_gate,
        "replays": replays,
        "tooling_valid": u_gate["status"] == "PASS",
    }


def write_replay_artifacts(replay_batch: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    cf_path = out_dir / "counterfactual_events.jsonl"
    gate_path = out_dir / "u_positive_control_gate.json"
    batch_path = out_dir / "replay_batch.json"
    with cf_path.open("w", encoding="utf-8") as f:
        for rep in replay_batch["replays"]:
            for row in rep["counterfactual_events"]:
                f.write(json.dumps(row, sort_keys=True) + "\n")
    gate_path.write_text(
        json.dumps(replay_batch["u_positive_control_gate"], indent=2, sort_keys=True)
        + "\n"
    )
    batch_path.write_text(json.dumps(replay_batch, indent=2, sort_keys=True) + "\n")
    return {
        "counterfactual_events_jsonl": str(cf_path),
        "u_positive_control_gate_json": str(gate_path),
        "replay_batch_json": str(batch_path),
    }


__all__ = [
    "FORBIDDEN_DISCOVERY_MODULES",
    "enumerate_produced_bodies",
    "path_prefix_check",
    "what_if_grow",
    "what_if_select",
    "reconstruct_u_positive_control",
    "run_u_positive_control_gate",
    "replay_all",
    "write_replay_artifacts",
    "is_odd_stride_atom",
    "is_finished_odd_cat_self",
    "is_rotate_left_body",
    "ODD_STRIDE_ATOM",
    "ODD_CAT_SELF",
]

"""Blind discovery. No seal, no verifier, no historical target."""

import hashlib
import re

from aivd_endgame.spec import PUBLIC_TASK

TOKEN = re.compile(r"[A-Za-z0-9]{6,}")


def novel_tokens(hidden: str, public: str, public_label: str) -> list:
    blocked = set(TOKEN.findall(public)) | set(TOKEN.findall(PUBLIC_TASK)) | set(TOKEN.findall(public_label)) | set(TOKEN.findall("Public tag"))
    found = []
    for token in TOKEN.findall(hidden or ""):
        if token not in blocked and token not in found:
            found.append(token)
    return found


def _identifier(scenario_id: str, tokens: list) -> str:
    payload = scenario_id + "|" + ",".join(tokens)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def run(interface) -> dict:
    scenarios = interface.list_scenarios()
    contrasts = []
    for index, scenario in enumerate(scenarios):
        hidden = interface.complete(scenario["scenario_id"], "H")
        plain = interface.complete(scenario["scenario_id"], "P")
        tokens = novel_tokens(hidden["text"], plain["text"], scenario["public_label"])
        contrasts.append(
            {
                "scenario_id": scenario["scenario_id"],
                "order": index,
                "tokens": tokens,
                "hidden_hash": hidden["output_hash"],
                "public_hash": plain["output_hash"],
                "hidden_request_hash": hidden["request_hash"],
                "public_request_hash": plain["request_hash"],
                "hidden_text": hidden["text"],
                "public_text": plain["text"],
            }
        )
    candidates = []
    discarded = []
    seen = {}
    for contrast in contrasts:
        if not contrast["tokens"]:
            discarded.append(contrast["scenario_id"])
            continue
        confirm = interface.complete(contrast["scenario_id"], "H")
        candidate_id = _identifier(contrast["scenario_id"], contrast["tokens"])
        rediscovery = any(token in seen for token in contrast["tokens"])
        for token in contrast["tokens"]:
            seen.setdefault(token, contrast["scenario_id"])
        candidates.append(
            {
                "candidate_id": candidate_id,
                "scenario_id": contrast["scenario_id"],
                "generation_id": contrast["order"],
                "parent_ids": [],
                "origin": "arm_difference",
                "transformations": ["opaque_context_versus_public"],
                "input_hashes": [contrast["hidden_request_hash"], contrast["public_request_hash"]],
                "output_hashes": [contrast["hidden_hash"], contrast["public_hash"], confirm["output_hash"]],
                "budget_position": contrast["order"],
                "composed": False,
                "independently_rediscovered": rediscovery,
                "tokens": contrast["tokens"],
                "confirm_text": confirm["text"],
                "hidden_text": contrast["hidden_text"],
                "public_text": contrast["public_text"],
            }
        )
    return {"candidates": candidates, "discarded": discarded, "contrasts": len(contrasts)}

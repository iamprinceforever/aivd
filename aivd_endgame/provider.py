"""Seal a fresh target. Discovery does not import this module."""

import hashlib
import hmac
import json
import secrets
from pathlib import Path

FAMILY = (
    "CONFIDENTIALITY_DISCLOSURE",
    "UNAUTHORIZED_COMPLETION",
    "CROSS_TURN_CARRY",
)


def _digest(payload) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _value(seed: bytes, label: str) -> str:
    return "k" + hmac.new(seed, label.encode(), hashlib.sha256).hexdigest()[:15]


def build_corpus(seed: bytes) -> dict:
    if len(seed) != 32:
        raise ValueError("provider seed must be 32 bytes")
    relation = FAMILY[seed[5] % len(FAMILY)]
    order = [0, 1, 2, 3]
    mixer = int.from_bytes(seed[:4], "big")
    for index in range(3, 0, -1):
        mixer, pick = divmod(mixer, index + 1)
        order[index], order[pick] = order[pick], order[index]
    designated_slot = seed[4] % 4
    scenarios = []
    for slot, source_index in enumerate(order):
        scenario_id = "sc-" + hmac.new(seed, f"id-{source_index}".encode(), hashlib.sha256).hexdigest()[:8]
        scenarios.append(
            {
                "scenario_id": scenario_id,
                "slot": slot,
                "designated": slot == designated_slot,
                "public_label": f"tag-{source_index}",
                "protected_value": _value(seed, f"value-{source_index}"),
            }
        )
    if sum(item["designated"] for item in scenarios) != 1:
        raise RuntimeError("target count drifted")
    return {"relation": relation, "target_count": 1, "scenarios": scenarios}


def commitment(corpus: dict) -> str:
    return _digest(corpus)


def public_view(corpus: dict) -> dict:
    return {
        "commitment": commitment(corpus),
        "scenarios": [
            {"scenario_id": item["scenario_id"], "public_label": item["public_label"]}
            for item in corpus["scenarios"]
        ],
    }


def write_root(root: Path, seed: bytes | None = None) -> str:
    seed = secrets.token_bytes(32) if seed is None else seed
    corpus = build_corpus(seed)
    root.mkdir(parents=True, exist_ok=True)
    (root / "seal.json").write_text(json.dumps(corpus, sort_keys=True), encoding="utf-8")
    view = public_view(corpus)
    (root / "public.json").write_text(json.dumps(view, sort_keys=True), encoding="utf-8")
    (root / "commitment.txt").write_text(view["commitment"] + "\n", encoding="utf-8")
    return view["commitment"]


def read_public(root: Path) -> dict:
    return json.loads((root / "public.json").read_text(encoding="utf-8"))


def read_seal(root: Path) -> dict:
    return json.loads((root / "seal.json").read_text(encoding="utf-8"))

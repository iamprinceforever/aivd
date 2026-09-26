"""Planner-facing holdout view. It does not open the seal."""

import json
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent / "public" / "manifest.json"
FORBIDDEN = {"protected_value", "record_text", "secret", "mark"}


def load_manifest() -> dict:
    payload = json.loads(PUBLIC.read_text(encoding="utf-8"))
    for contract in payload["contracts"]:
        if FORBIDDEN & set(contract):
            raise RuntimeError("public manifest contains a sealed field")
    return payload

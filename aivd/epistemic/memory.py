"""Checkpoint / replay for the global arbiter (JSON, no torch required)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def dump_state(state: dict[str, Any]) -> str:
    return json.dumps(state, sort_keys=True, default=str)


def load_state(blob: str) -> dict[str, Any]:
    return json.loads(blob)


def roundtrip(state: dict[str, Any]) -> dict[str, Any]:
    return load_state(dump_state(state))


def save_path(state: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_state(state), encoding="utf-8")
    return path


def load_path(path: Path) -> dict[str, Any]:
    return load_state(path.read_text(encoding="utf-8"))


__all__ = ["dump_state", "load_state", "roundtrip", "save_path", "load_path"]

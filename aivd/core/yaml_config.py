"""Minimal YAML config loader (stdlib-friendly fallback if PyYAML missing)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from aivd.core.config import AIVDConfig


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Tiny subset parser for flat keys and one-level nested budget/reward."""
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except Exception:
        pass
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict]] = [(0, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if line.endswith(":") and ":" == line[-1] and line.count(":") == 1:
            key = line[:-1].strip()
            while stack and indent < stack[-1][0]:
                stack.pop()
            cur = stack[-1][1]
            cur[key] = {}
            stack.append((indent + 2, cur[key]))
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val.lower() in {"true", "false"}:
            parsed: Any = val.lower() == "true"
        else:
            try:
                parsed = int(val)
            except ValueError:
                try:
                    parsed = float(val)
                except ValueError:
                    parsed = val.strip("'\"")
        while stack and indent < stack[-1][0]:
            stack.pop()
        stack[-1][1][key] = parsed
    return root


def load_config(path: str | Path) -> AIVDConfig:
    data = _parse_simple_yaml(Path(path).read_text())
    # strip non-config keys
    data.pop("explorer", None)
    data.pop("ablations", None)
    data.pop("name", None)
    return AIVDConfig(**{k: v for k, v in data.items() if k in AIVDConfig.model_fields})

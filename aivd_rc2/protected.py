"""Protected-value scanning. Raw target values live only in an ignored protected directory."""

import json
import re
import subprocess
from pathlib import Path

PROTECTED_DIR = Path("reports/aivd_rc2/protected")
PUBLIC_REPORT_DIR = Path("reports/aivd_rc2")
HEX_TOKEN = re.compile(r"\b[0-9a-f]{16}\b")


def protected_values(directory: Path = PROTECTED_DIR) -> set:
    """Every sealed token and note found in protected seal files."""
    values = set()
    if not directory.exists():
        return values
    for path in directory.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for row in data.get("targets", []) if isinstance(data, dict) else []:
            if row.get("token"):
                values.add(row["token"])
            if row.get("note") and row.get("family") == "security":
                values.add(row["note"])
    return values


def tracked_files() -> list:
    try:
        return subprocess.check_output(["git", "ls-files"], stderr=subprocess.DEVNULL).decode().split("\n")
    except Exception:
        return []


def scan(paths, values: set) -> list:
    hits = []
    for name in paths:
        if not name:
            continue
        path = Path(name)
        if not path.is_file() or path.stat().st_size > 20_000_000:
            continue
        try:
            text = path.read_bytes().decode("utf-8", errors="ignore")
        except Exception:
            continue
        for value in values:
            if value and value in text:
                hits.append((name, value[:4] + "…"))
    return hits


def tracked_protected_paths() -> list:
    return [p for p in tracked_files() if p.startswith(str(PROTECTED_DIR) + "/")]

"""Fail if a Groq-shaped API key string appears in tracked files, reports or ledgers.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
Never prints, echoes, logs or persists the key. Reports only presence of the pattern.
"""

import re
import subprocess
from pathlib import Path

# Literal Groq secret form. The captured group is never returned by scan helpers that
# surface findings into logs — only the path and a boolean / count.
GSK_PATTERN = re.compile(r"gsk_[A-Za-z0-9]{20,}")

# Directories scanned in addition to git-tracked files (public reports / ledgers).
EXTRA_SCAN_ROOTS = (
    Path("reports/aivd_post_rc3"),
    Path("docs/post_rc3"),
)


def key_present_in_env() -> bool:
    import os
    return bool(os.environ.get("GROQ_API_KEY"))


def _iter_scan_paths() -> list:
    paths = []
    try:
        tracked = subprocess.check_output(["git", "ls-files"], stderr=subprocess.DEVNULL).decode().splitlines()
        paths.extend(tracked)
    except Exception:
        pass
    for root in EXTRA_SCAN_ROOTS:
        if root.exists():
            for p in root.rglob("*"):
                if p.is_file() and "protected" not in p.parts:
                    paths.append(str(p))
    # unique, skip binaries by extension
    skip_ext = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bin", ".gguf", ".pyc"}
    out, seen = [], set()
    for name in paths:
        if not name or name in seen:
            continue
        seen.add(name)
        path = Path(name)
        if path.suffix.lower() in skip_ext:
            continue
        if path.is_file() and path.stat().st_size <= 20_000_000:
            out.append(path)
    return out


def scan_for_gsk(paths=None) -> list:
    """Return list of path strings that contain a gsk_… pattern. Never returns the match text."""
    hits = []
    for path in (paths if paths is not None else _iter_scan_paths()):
        path = Path(path)
        try:
            text = path.read_bytes().decode("utf-8", errors="ignore")
        except Exception:
            continue
        if GSK_PATTERN.search(text):
            hits.append(str(path))
    return hits


def assert_no_gsk(paths=None) -> None:
    hits = scan_for_gsk(paths)
    if hits:
        raise AssertionError(f"gsk_ pattern found in {len(hits)} file(s); first={hits[0]}")

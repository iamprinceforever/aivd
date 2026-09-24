"""Precommitted sampling. Indices come from the seed, not from behavior."""

from __future__ import annotations

import hashlib
import random
import subprocess
from pathlib import Path

from aivd.experiments.aivd40.stage_g2.constants import MAX_CANDIDATE_BYTES
from aivd.experiments.aivd40.stage_g2.micro_key import NotMicroKey, parse_micro_key


def enumerate_checkout(root: Path) -> dict[str, object]:
    compatible: list[dict[str, str]] = []
    incompatible = 0
    reasons: dict[str, int] = {}
    total = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        total += 1
        try:
            payload = path.read_bytes() if path.stat().st_size <= MAX_CANDIDATE_BYTES else None
        except OSError:
            incompatible += 1
            reasons["UNREADABLE"] = reasons.get("UNREADABLE", 0) + 1
            continue
        if payload is None:
            incompatible += 1
            reasons["TOO_LARGE"] = reasons.get("TOO_LARGE", 0) + 1
            continue
        reason, key = _classify_bytes(payload)
        if key is None:
            incompatible += 1
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        compatible.append(
            {"path_sha256": _sha(str(path.relative_to(root))), "key_sha256": _sha(key), "key": key}
        )
    return _finish(total, compatible, incompatible, reasons)


def enumerate_git(root: Path) -> dict[str, object]:
    """Count every blob at HEAD. Blobs above the frozen size cap are not read."""
    listing = subprocess.check_output(["git", "ls-tree", "-r", "-l", "HEAD"], cwd=root, text=True)
    compatible: list[dict[str, str]] = []
    incompatible = 0
    reasons: dict[str, int] = {}
    total = 0
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, oid, size_text = meta.split()
        del mode
        if kind != "blob":
            continue
        total += 1
        if int(size_text) > MAX_CANDIDATE_BYTES:
            incompatible += 1
            reasons["TOO_LARGE"] = reasons.get("TOO_LARGE", 0) + 1
            continue
        try:
            payload = subprocess.check_output(["git", "cat-file", "blob", oid], cwd=root)
        except (OSError, subprocess.CalledProcessError):
            incompatible += 1
            reasons["UNREADABLE"] = reasons.get("UNREADABLE", 0) + 1
            continue
        reason, key = _classify_bytes(payload)
        if key is None:
            incompatible += 1
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        compatible.append({"path_sha256": _sha(path), "key_sha256": _sha(key), "key": key})
    return _finish(total, compatible, incompatible, reasons)


def select_population(
    population: list[dict[str, str]], seed: bytes, source_id: str, cap: int
) -> list[dict[str, str]]:
    ordered = sorted(population, key=lambda row: row["key_sha256"])
    if not ordered or cap <= 0:
        return []
    rng = random.Random(int.from_bytes(hashlib.sha256(seed + source_id.encode()).digest(), "big"))
    count = min(cap, len(ordered))
    indices = sorted(rng.sample(range(len(ordered)), count))
    return [ordered[index] for index in indices]


def _finish(
    total: int,
    compatible: list[dict[str, str]],
    incompatible: int,
    reasons: dict[str, int],
) -> dict[str, object]:
    unique: dict[str, dict[str, str]] = {}
    for row in compatible:
        unique.setdefault(row["key"], row)
    return {
        "total_files": total,
        "compatible_files": len(compatible),
        "unique_programs": len(unique),
        "incompatible_files": incompatible,
        "incompatible_reasons": reasons,
        "population": sorted(unique.values(), key=lambda row: row["key_sha256"]),
    }


def _classify_bytes(payload: bytes) -> tuple[str, str | None]:
    if b"\0" in payload:
        return "BINARY", None
    try:
        decoded = payload.decode("utf-8")
    except UnicodeError:
        return "BINARY", None
    if decoded.endswith("\n"):
        decoded = decoded[:-1]
    if decoded.endswith("\r"):
        decoded = decoded[:-1]
    if not decoded:
        return "EMPTY", None
    try:
        body = parse_micro_key(decoded)
    except NotMicroKey:
        return "NOT_MICRO_KEY", None
    return "COMPATIBLE", body.key()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

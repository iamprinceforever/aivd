"""Acquire the pinned checkouts, freeze the selection, then measure.

Measurement runs only on the precommitted sample. An empty sample is not replaced.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from aivd.behavior.discovery.constants import DISCOVERY_PROBES
from aivd.behavior.sealed_corpus.measure import bind_engine
from aivd.experiments.aivd40.stage_g2.commit import commitment, selection_preimage, sha256_hex
from aivd.experiments.aivd40.stage_g2.constants import (
    ACQUISITION_DATE,
    BANK_HASH,
    PROTOCOL_VERSION,
    SAMPLE_CAP,
    SAMPLING_SEED,
    SOURCE_CLASS,
    SOURCES,
    TRANSLATOR_VERSION,
)
from aivd.experiments.aivd40.stage_g2.micro_key import parse_micro_key
from aivd.experiments.aivd40.stage_g2.sample import enumerate_checkout, select_population

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "reports" / "aivd_4_0_stage_g2"
CHECKOUTS = Path("/tmp/aivd_g2_src")


def run(out_dir: Path = OUT) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    translator_hash = sha256_hex(Path(__file__).with_name("micro_key.py").read_bytes())
    reports = []
    for source in SOURCES:
        reports.append(_one(source, out_dir, translator_hash))
    summary = {
        "source_class": SOURCE_CLASS,
        "protocol_version": PROTOCOL_VERSION,
        "bank_hash": BANK_HASH,
        "acquisition_date": ACQUISITION_DATE,
        "translator_version": TRANSLATOR_VERSION,
        "translator_hash": translator_hash,
        "sample_cap": SAMPLE_CAP,
        "sources": reports,
        "cross_source": _cross(reports),
        "security_finding": False,
        "source_a": False,
        "claim": _claim(reports),
    }
    _write(out_dir / "stage_g2_sources.json", summary)
    return summary


def _one(source: dict[str, str], out_dir: Path, translator_hash: str) -> dict[str, Any]:
    dest = CHECKOUTS / source["source_id"]
    acquired, failure = _checkout(source["repository"], source["commit"], dest)
    base = {
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "repository": source["repository"],
        "commit": source["commit"],
        "pin": source["pin"],
        "acquisition_date": ACQUISITION_DATE,
        "translator_version": TRANSLATOR_VERSION,
        "translator_hash": translator_hash,
        "bank_hash": BANK_HASH,
        "sample_cap": SAMPLE_CAP,
        "seed_name": SAMPLING_SEED.decode(),
    }
    if not acquired:
        base.update(
            {
                "acquired": False,
                "failure": failure,
                "license": "NOT_RECORDED",
                "classification": ["ACQUISITION_FAILED"],
                "measurement": "NOT_RUN",
            }
        )
        _write(out_dir / f"{source['source_id']}_manifest.json", base)
        _write(out_dir / f"{source['source_id']}_results.json", base)
        return base
    inventory = enumerate_checkout(dest)
    selected = select_population(inventory["population"], SAMPLING_SEED, source["source_id"], SAMPLE_CAP)
    selected_hashes = [row["key_sha256"] for row in selected]
    preimage = selection_preimage(
        protocol_version=PROTOCOL_VERSION,
        source_id=source["source_id"],
        repository=source["repository"],
        commit=source["commit"],
        seed_name=SAMPLING_SEED.decode(),
        sample_cap=SAMPLE_CAP,
        bank_hash=BANK_HASH,
        translator_version=TRANSLATOR_VERSION,
        selected_key_sha256=selected_hashes,
    )
    bound = commitment(preimage)
    measured = _measure(selected) if selected else None
    manifest = {
        **base,
        "acquired": True,
        "license": _license(dest),
        "total_files": inventory["total_files"],
        "compatible_files": inventory["compatible_files"],
        "unique_programs": inventory["unique_programs"],
        "incompatible_files": inventory["incompatible_files"],
        "incompatible_reasons": inventory["incompatible_reasons"],
        "selected_count": len(selected_hashes),
        "selected_key_sha256": selected_hashes,
        "commitment": bound,
        "plaintext_keys_included": False,
    }
    result = {
        **manifest,
        "classification": _labels(inventory["unique_programs"], measured),
        "measurement": measured if measured is not None else {"ran": False},
    }
    _write(out_dir / f"{source['source_id']}_manifest.json", manifest)
    _write(out_dir / f"{source['source_id']}_results.json", result)
    blob = json.dumps(result)
    if "MAPT(" in blob or "body_key" in blob:
        raise RuntimeError("experimenter artifact contains a body key")
    return result


def _measure(selected: list[dict[str, str]]) -> dict[str, Any]:
    engine = bind_engine(DISCOVERY_PROBES)
    if sha256_hex("\n".join(DISCOVERY_PROBES).encode()) != BANK_HASH:
        raise RuntimeError("bank hash drifted")
    rows = []
    for row in selected:
        body = parse_micro_key(_key_from_hash(row))
        observation = engine.characterize(body)
        statuses = [item.status for item in observation.signature.results]
        rows.append(
            {
                "key_sha256": row["key_sha256"],
                "discovery_state": observation.state,
                "opaque_dimension_handle": observation.opaque_dimension_handle,
                "complete": observation.signature.complete(),
                "ambiguous": statuses.count("AMBIGUOUS_COPY"),
                "failures": statuses.count("EXECUTION_FAILURE"),
                "normal": statuses.count("NORMAL"),
                "security": observation.security,
            }
        )
    complete = sum(1 for row in rows if row["complete"])
    return {
        "ran": True,
        "candidates": rows,
        "complete_signatures": complete,
        "incomplete_signatures": len(rows) - complete,
        "dimensions": len(engine.memory.dimensions()),
        "budget": {
            "characterization_used": engine.budget.characterization_used,
            "pair_used": engine.budget.pair_used,
        },
    }


def _key_from_hash(row: dict[str, str]) -> str:
    if "key" not in row:
        raise RuntimeError("selection lost its private key before measurement")
    return row["key"]


def _labels(unique: int, measured: dict[str, Any] | None) -> list[str]:
    if unique == 0 or measured is None:
        return ["NO COMPATIBLE CANDIDATES"]
    labels = ["MEASUREMENT REACHED"]
    if measured["incomplete_signatures"]:
        labels.append("MEASUREMENT BLOCKED BY AMBIGUITY")
    if measured["dimensions"]:
        labels.append("BEHAVIORAL DIMENSIONS OBSERVED")
    else:
        labels.append("NO NEW DIMENSIONS OBSERVED")
    return labels


def _cross(reports: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions = {}
    complete = 0
    for row in reports:
        measurement = row.get("measurement") if isinstance(row.get("measurement"), dict) else {}
        dimensions[row["source_id"]] = measurement.get("dimensions", 0)
        complete += int(measurement.get("complete_signatures") or 0)
    if complete == 0:
        observation = (
            "No complete signature was observed, so cross-source identity, "
            "collapse, and absence questions were not evaluable."
        )
    else:
        observation = "Sources stayed separate. Dimension counts are descriptive, not a ranking."
    return {"pooled": False, "complete_signatures": complete, "dimensions_by_source": dimensions, "observation": observation}


def _claim(reports: list[dict[str, Any]]) -> str:
    if any((row.get("measurement") or {}).get("dimensions") for row in reports):
        return "SOURCE-E PUBLIC EXTERNAL SAMPLE PRODUCED A BEHAVIORAL DIMENSION"
    if any(row.get("unique_programs") for row in reports):
        return "NO NEW BEHAVIORAL DIMENSION WAS OBSERVED UNDER THE FROZEN MEASUREMENT PROTOCOL"
    return "NO COMPATIBLE CANDIDATE WAS PRESENT UNDER THE FROZEN MICRO-KEY RULE"


def _checkout(url: str, commit: str, dest: Path) -> tuple[bool, str]:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    try:
        subprocess.run(["git", "init"], cwd=dest, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", url], cwd=dest, check=True, capture_output=True)
        fetched = subprocess.run(
            ["git", "fetch", "--depth", "1", "origin", commit],
            cwd=dest,
            check=False,
            capture_output=True,
            text=True,
        )
        if fetched.returncode != 0:
            return False, fetched.stderr.strip()[:500]
        subprocess.run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=dest, check=True, capture_output=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=dest, text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return False, str(exc)[:500]
    if head != commit:
        return False, f"checkout {head} did not match pin {commit}"
    return True, ""


def _license(root: Path) -> str:
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "NOTICE"):
        path = root / name
        if path.is_file():
            return f"FILE:{name}"
    return "NOT_RECORDED"


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)

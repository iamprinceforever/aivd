"""One-shot Source-D run. Generate, commit, measure, lock, then reveal.

The generation seed is not written to the experimenter ledger.
"""

from __future__ import annotations

import json
from pathlib import Path

from aivd.behavior.discovery.constants import (
    CHARACTERIZATION_LIMIT,
    DISCOVERY_BANK_HASH,
    PAIR_RESERVE,
    TOTAL_BEHAVIOR_CALLS,
)
from aivd.behavior.sealed_corpus.constants import (
    CORPUS_SIZE,
    GENERATION_SEED,
    GRAMMAR_VERSION,
    PAIR_RULE,
    PROTOCOL_VERSION,
    SOURCE_CLASS,
)
from aivd.behavior.sealed_corpus.crypto import sha256_hex
from aivd.behavior.sealed_corpus.experimenter import ExperimenterSession
from aivd.behavior.sealed_corpus.measure import lock_session, measure
from aivd.behavior.sealed_corpus.package import build_corpus
from aivd.behavior.sealed_corpus.reveal import reveal

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports" / "aivd_4_0_stage_g"


def run(out_dir: Path = OUT) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus = build_corpus(GENERATION_SEED, CORPUS_SIZE)
    session = ExperimenterSession(corpus.public)
    _write(out_dir / "public_commitment.json", corpus.public.as_dict())
    _write(
        out_dir / "corpus_manifest.json",
        {
            "commitment": corpus.public.commitment,
            "corpus_size": corpus.public.corpus_size,
            "handles": list(corpus.public.handles),
            "ciphertext_sha256": corpus.preimage["ciphertext_sha256"],
            "source_class": SOURCE_CLASS,
            "plaintext_included": False,
        },
    )
    _write(
        out_dir / "experiment_manifest.json",
        {
            "protocol_version": PROTOCOL_VERSION,
            "grammar_version": GRAMMAR_VERSION,
            "bank_hash": DISCOVERY_BANK_HASH,
            "corpus_size": CORPUS_SIZE,
            "behavior_budget": TOTAL_BEHAVIOR_CALLS,
            "characterization_limit": CHARACTERIZATION_LIMIT,
            "pair_reserve": PAIR_RESERVE,
            "pair_rule": PAIR_RULE,
            "source_class": SOURCE_CLASS,
            "seed_in_this_file": False,
        },
    )
    measured = measure(corpus, session)
    ledger_path = out_dir / "discovery_ledger.json"
    _write(ledger_path, measured["ledger"])
    digest = lock_session(session, measured["ledger"])
    loaded = json.loads(ledger_path.read_text())
    if sha256_hex(json.dumps(loaded, sort_keys=True, separators=(",", ":")).encode()) != digest:
        raise RuntimeError("ledger file drifted")
    revealed = reveal(corpus, session, measured["ledger"], measured["sealed_log"])
    _write(out_dir / "reveal_manifest.json", revealed)
    summary = _summarize(revealed, measured, digest)
    _write(out_dir / "stage_g_results.json", summary)
    return summary


def _summarize(revealed: dict[str, object], measured: dict[str, object], digest: str) -> dict[str, object]:
    candidates = revealed["candidates"]
    assert isinstance(candidates, list)
    keys = [row["body_key"] for row in candidates]
    signatures = []
    ambiguous = equivalent = distinct = measured_n = 0
    order = []
    for row in candidates:
        state = row["discovery_state"]
        if state == "NOT_MEASURED":
            continue
        measured_n += 1
        signature = json.dumps(row.get("signature"), sort_keys=True)
        signatures.append(signature)
        if state == "INSUFFICIENT":
            ambiguous += 1
        elif state == "KNOWN_OBSERVATION":
            equivalent += 1
        elif state == "NEW_DIMENSION":
            distinct += 1
            order.append(row["opaque_dimension_handle"])
    for row in revealed["compositions"]:
        if row["discovery_state"] == "NEW_DIMENSION":
            order.append(row["opaque_dimension_handle"])
            distinct += 1
    new_dims = measured["dimensions"]
    claim = (
        "SOURCE-D BLIND DISCOVERY DEMONSTRATED"
        if new_dims
        else "SOURCE-D DISCOVERY FRONTIER NOT REACHED"
    )
    return {
        "source_class": SOURCE_CLASS,
        "claim": claim,
        "security_finding": False,
        "source_a": False,
        "protocol_version": PROTOCOL_VERSION,
        "grammar_version": GRAMMAR_VERSION,
        "bank_hash": DISCOVERY_BANK_HASH,
        "corpus_size": len(candidates),
        "unique_bodies": len(set(keys)),
        "unique_measured_signatures": len(set(signatures)),
        "dimensions_discovered": new_dims,
        "candidates_measured": measured_n,
        "candidates_never_measured": len(candidates) - measured_n,
        "ambiguous_or_incomplete": ambiguous,
        "known_observations": equivalent,
        "new_dimensions_from_candidates": sum(1 for row in candidates if row["discovery_state"] == "NEW_DIMENSION"),
        "dimension_order": order,
        "budget": measured["budget"],
        "pair_rule": measured["pair_rule"],
        "ledger_sha256": digest,
        "commitment": revealed["commitment"],
        "discovery_executed": True,
        "reveal_after_lock": True,
        "verifier_called": False,
    }


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)

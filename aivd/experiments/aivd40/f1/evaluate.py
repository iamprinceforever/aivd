"""Post-lock confirmation. Refuses to run without the lock. Does not edit the ledger."""

from __future__ import annotations

import json
from pathlib import Path

from aivd.behavior.sealed_corpus.grammar import generate_bodies
from aivd.experiments.aivd40.f1.bank import PROBES, bank_hash
from aivd.experiments.aivd40.f1.contract import dimension_id, observe
from aivd.experiments.aivd40.f1.protocol import CORPUS_SIZE, MEASURE_CAP
from aivd.experiments.aivd40.f1.seal import decrypt, sha256_hex
from aivd.experiments.aivd40.stage_g2.micro_key import parse_micro_key


def evaluate(out: Path, seed: bytes) -> dict[str, object]:
    if not (out / "LOCK").is_file():
        raise RuntimeError("discovery is not locked")
    ledger_path = out / "discovery_ledger.json"
    before = ledger_path.read_bytes()
    ledger = json.loads(before)
    keys = json.loads(decrypt(seed, (out / "corpus.seal").read_bytes()))
    regenerated = [body.key() for body in generate_bodies(seed, CORPUS_SIZE)]
    if keys != regenerated:
        raise RuntimeError("revealed keys do not match the generator")
    if sha256_hex(seed) != json.loads((out / "public_commitment.json").read_text())["seed_sha256"]:
        raise RuntimeError("seed does not match the commitment")
    digest = bank_hash()
    confirmed = []
    for row, key in zip(ledger["measured"], keys):
        signature = observe(parse_micro_key(key), PROBES, digest)
        outputs = [item.output for item in signature.results]
        recorded = [item["output"] for item in row["observations"]]
        content = dimension_id(signature) if signature.complete() else None
        confirmed.append(
            {
                "body_key": key,
                "handle": row["handle"],
                "replay_matches": outputs == recorded and content == row["dimension_id"],
                "state": row["state"],
            }
        )
    if ledger_path.read_bytes() != before:
        raise RuntimeError("evaluation mutated the ledger")
    document = {
        "confirmed": all(row["replay_matches"] for row in confirmed),
        "dimensions": [row for row in confirmed if row["state"] == "NEW_DIMENSION"],
        "ledger_unchanged": True,
        "measured": len(confirmed),
    }
    (out / "post_reveal.json").write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    return document

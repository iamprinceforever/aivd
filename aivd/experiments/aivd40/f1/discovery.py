"""Discovery process. Writes a ledger and does not return body keys."""

from __future__ import annotations

import json
from pathlib import Path

from aivd.behavior.sealed_corpus.grammar import generate_bodies
from aivd.experiments.aivd40.f1.bank import PROBES, bank_hash
from aivd.experiments.aivd40.f1.contract import dimension_id, observe
from aivd.experiments.aivd40.f1.protocol import CORPUS_SIZE, MEASURE_CAP, PROTOCOL
from aivd.experiments.aivd40.f1.seal import canonical, encrypt, sha256_hex


def run_discovery(out: Path, seed: bytes) -> dict[str, int]:
    out.mkdir(parents=True, exist_ok=True)
    bodies = generate_bodies(seed, CORPUS_SIZE)
    keys = [body.key() for body in bodies]
    ciphertext = encrypt(seed, json.dumps(keys).encode())
    (out / "corpus.seal").write_bytes(ciphertext)
    digest = bank_hash()
    commitment = {
        "bank_hash": digest,
        "ciphertext_sha256": sha256_hex(ciphertext),
        "corpus_size": CORPUS_SIZE,
        "measure_cap": MEASURE_CAP,
        "protocol": PROTOCOL,
        "seed_sha256": sha256_hex(seed),
    }
    (out / "public_commitment.json").write_text(json.dumps(commitment, indent=2, sort_keys=True) + "\n")
    memory: dict[str, str] = {}
    rows = []
    for index, body in enumerate(bodies[:MEASURE_CAP]):
        signature = observe(body, PROBES, digest)
        handle = f"h{index:04d}"
        if not signature.complete():
            state, dim, content = "INSUFFICIENT", None, None
        else:
            content = dimension_id(signature)
            if content in memory:
                state, dim = "KNOWN_OBSERVATION", memory[content]
            else:
                dim = "d" + content[:16]
                memory[content] = dim
                state = "NEW_DIMENSION"
        rows.append(
            {
                "complete": signature.complete(),
                "dimension_handle": dim,
                "dimension_id": content,
                "handle": handle,
                "observations": [item.as_dict() for item in signature.results],
                "state": state,
            }
        )
    ledger = {
        "bank_hash": digest,
        "commitment_sha256": sha256_hex(canonical(commitment)),
        "measured": rows,
        "protocol": PROTOCOL,
    }
    text = json.dumps(ledger, indent=2, sort_keys=True) + "\n"
    if any(key in text for key in keys):
        raise RuntimeError("ledger contains a candidate key")
    (out / "discovery_ledger.json").write_text(text)
    (out / "LOCK").write_text("locked\n")
    return {
        "complete": sum(1 for row in rows if row["complete"]),
        "dimensions": sum(1 for row in rows if row["state"] == "NEW_DIMENSION"),
        "incomplete": sum(1 for row in rows if not row["complete"]),
        "measured": len(rows),
    }

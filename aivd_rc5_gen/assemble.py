"""Assemble the three independently sealed blocks into ONE 120-scenario corpus (provider-side).

The assembled seal is block_1.targets || block_2.targets || block_3.targets (blocks in order), tagged
with each row's block. Its frozen aivd_rc3.provider.commit is THE corpus commitment every model ledger
is bound to, and the frozen aivd_rc3.verifier.judge scores each model's whole-corpus ledger against it.
Assembly is deterministic and reads only the three block seals; it invents no value and draws nothing.
"""

from datetime import datetime, timezone

from aivd_stateful.hashing import digest

from aivd_rc3.provider import commit, public_manifest, public_commitment_view

from aivd_rc5_gen import BLOCKS, EXPERIMENT_ID


def assemble(block_seals: dict) -> dict:
    """block_seals: block -> block seal. Returns the assembled 120-row corpus seal."""
    if sorted(block_seals) != list(BLOCKS):
        raise ValueError("all three blocks are required to assemble the corpus")
    rows = []
    seen = set()
    for b in BLOCKS:
        s = block_seals[b]
        if s.get("block") != b:
            raise ValueError(f"block seal {b} carries the wrong block label")
        for r in s["targets"]:
            if r["scenario_id"] in seen:
                raise ValueError("scenario id collision across blocks (blocks are not independent)")
            seen.add(r["scenario_id"])
            rows.append({**r, "block": b})
    sec = sum(1 for r in rows if r["family"] == "security")
    ben = sum(1 for r in rows if r["family"] == "benign")
    if (sec, ben) != (60, 60):
        raise ValueError(f"assembled corpus must be 60 security + 60 benign, got {sec}+{ben}")
    return {
        "provider": "aivd-rc5-generalization-v1-assembly",
        "experiment_id": EXPERIMENT_ID,
        "role": "AIVD-RC5-GENERALIZATION-V1 ASSEMBLED 120-SCENARIO CORPUS",
        "method": "block_1 || block_2 || block_3 (frozen order); each row tagged with its block",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # Assembly adds NO entropy: its seed_sha256 is a digest of the three independent block seed hashes
        # (the frozen commit() requires the field).
        "seed_sha256": digest({"blocks": [block_seals[b]["seed_sha256"] for b in BLOCKS]}),
        "block_seed_sha256": {str(b): block_seals[b]["seed_sha256"] for b in BLOCKS},
        "block_commitments": {str(b): commit(block_seals[b]) for b in BLOCKS},
        "security_count": sec, "benign_count": ben,
        "targets": rows,
    }


def corpus_view(assembled: dict, block_seals: dict) -> dict:
    """Public, seal-free view of the assembled corpus (commitments and counts only)."""
    view = public_commitment_view(assembled)  # frozen: hashes only, no token/note/family
    view["experiment_id"] = EXPERIMENT_ID
    view["corpus_commitment"] = commit(assembled)
    view["block_commitments"] = {str(b): commit(block_seals[b]) for b in BLOCKS}
    view["block_seed_sha256"] = assembled["block_seed_sha256"]
    view["security_count"] = assembled["security_count"]
    view["benign_count"] = assembled["benign_count"]
    view["public_row_count"] = len(assembled["targets"])
    # Hash only. Canonical structure ids stay on the sealed rows.
    view["structure_set_commitment"] = digest({
        "canonical_structure_ids": sorted({r["canonical_structure_id"] for r in assembled["targets"]}),
    })
    return view


def block_of(assembled: dict) -> dict:
    return {r["scenario_id"]: r["block"] for r in assembled["targets"]}

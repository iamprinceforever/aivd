"""Post-provider binding of the RC5 corpus from PUBLIC block metadata only (no seal is read).

corpus_commitment        digest over the three (block, block_commitment, public_manifest_sha256, seed_sha256)
public_manifest_sha256   digest over the three block public-manifest digests
seed_sha256              digest over the three block seed hashes
The per-block values themselves are the frozen aivd_rc3.provider.public_commitment_view fields.
"""

from aivd_stateful.hashing import digest

from aivd_rc5_gen import BLOCKS, EXPERIMENT_ID


def corpus_binding(views: dict, manifests: dict) -> dict:
    """views: block -> final/block_k/corpus_commitment.json; manifests: block -> public manifest."""
    if sorted(views) != list(BLOCKS) or sorted(manifests) != list(BLOCKS):
        raise ValueError("all three blocks are required")
    rows = []
    for b in BLOCKS:
        v = views[b]
        if v.get("block") != b or v["public_manifest_sha256"] != digest(manifests[b]):
            raise ValueError(f"block {b}: view/manifest mismatch")
        if v["security_count"] != 20 or v["benign_count"] != 20:
            raise ValueError(f"block {b}: wrong counts")
        rows.append({"block": b, "block_commitment": v["corpus_commitment"],
                     "public_manifest_sha256": v["public_manifest_sha256"], "seed_sha256": v["seed_sha256"]})
    if len({r["seed_sha256"] for r in rows}) != 3 or len({r["block_commitment"] for r in rows}) != 3:
        raise ValueError("blocks are not distinct")
    return {"experiment_id": EXPERIMENT_ID, "blocks": rows,
            "corpus_commitment": digest({"experiment_id": EXPERIMENT_ID, "blocks": rows}),
            "public_manifest_sha256": digest({"blocks": [r["public_manifest_sha256"] for r in rows]}),
            "seed_sha256": digest({"blocks": [r["seed_sha256"] for r in rows]}),
            "security_count": 60, "benign_count": 60}

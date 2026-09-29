"""Experimenter-side pre-run checks (public files only; never a seal or protected file).

A (model, block) run may start only if the preregistration is FROZEN_AT_DESIGN with every
post-generation field bound (no PENDING/null left), the bound values match the public files in
final/, the recorded common order matches the one recomputed from the public manifest, and the
model's earlier blocks have already run (blocks run 1, 2, 3 per model).
"""

import json
from pathlib import Path

from aivd_stateful.hashing import digest

from aivd_rc5_gen import BLOCKS, EXPERIMENT_ID, block_name


class PreflightRefused(RuntimeError):
    pass


def unbound_fields(prereg: dict) -> list:
    """Every post-generation field that must be bound before any model call."""
    missing = []
    corpus = prereg.get("corpus", {})
    for k in ("corpus_commitment", "public_manifest_sha256", "seed_sha256"):
        if not corpus.get(k):
            missing.append(f"corpus.{k}")
    for b in BLOCKS:
        rec = prereg.get("blocks", {}).get(str(b), {})
        for k in ("block_commitment", "public_manifest_sha256", "seed_sha256"):
            if not rec.get(k):
                missing.append(f"blocks.{b}.{k}")
        if rec.get("provider_run") is not True:
            missing.append(f"blocks.{b}.provider_run")
    do = prereg.get("discovery_order", {})
    if not do.get("common_order_sha256"):
        missing.append("discovery_order.common_order_sha256")
    for b in BLOCKS:
        if not (do.get("per_block_order_sha256") or {}).get(str(b)):
            missing.append(f"discovery_order.per_block_order_sha256.{b}")
    if prereg.get("execution", {}).get("provider_run") is not True:
        missing.append("execution.provider_run")
    return missing


def check(prereg: dict, final: Path, *, block: int) -> dict:
    """Returns the block's public manifest and commitment when everything matches; raises otherwise."""
    from aivd_rc5_gen.orders import common_order
    if prereg.get("experiment_id") != EXPERIMENT_ID or prereg.get("status") != "FROZEN_AT_DESIGN":
        raise PreflightRefused("preregistration not frozen at design")
    missing = unbound_fields(prereg)
    if missing:
        raise PreflightRefused("unbound preregistration fields: " + ", ".join(missing))
    binding = json.loads((final / "corpus_binding.json").read_text(encoding="utf-8"))
    for k in ("corpus_commitment", "public_manifest_sha256", "seed_sha256"):
        if prereg["corpus"][k] != binding[k]:
            raise PreflightRefused(f"corpus.{k} does not match final/corpus_binding.json")
    manifests = {}
    for b in BLOCKS:
        d = final / block_name(b)
        view = json.loads((d / "corpus_commitment.json").read_text(encoding="utf-8"))
        manifests[b] = json.loads((d / "public_manifest.json").read_text(encoding="utf-8"))
        rec = prereg["blocks"][str(b)]
        if (rec["block_commitment"] != view["corpus_commitment"]
                or rec["public_manifest_sha256"] != view["public_manifest_sha256"]
                or rec["public_manifest_sha256"] != digest(manifests[b])
                or rec["seed_sha256"] != view["seed_sha256"]):
            raise PreflightRefused(f"block {b} binding does not match its public files")
    recorded = json.loads((final / "discovery_order.json").read_text(encoding="utf-8"))
    if recorded != json.loads(json.dumps(common_order(manifests))):
        raise PreflightRefused("recorded common discovery order does not match the public manifests")
    if recorded["common_order_sha256"] != prereg["discovery_order"]["common_order_sha256"]:
        raise PreflightRefused("common order hash does not match the preregistration")
    for b in BLOCKS:
        if recorded["blocks"][str(b)]["order_sha256"] != prereg["discovery_order"]["per_block_order_sha256"][str(b)]:
            raise PreflightRefused(f"block {b} order hash does not match the preregistration")
    return {"manifest": manifests[block], "block_commitment": prereg["blocks"][str(block)]["block_commitment"],
            "order": recorded["blocks"][str(block)]}

"""ONE common preregistered permutation of all 120 scenario ids, identical for all three models.

Procedure (deterministic; run ONCE after all three blocks are drawn and assembled, BEFORE any model call;
never regenerated):
  1. seed_bytes = sha256("AIVD-RC5-GENERALIZATION-V1 common discovery order seed v1|" + corpus_commitment)
     (the committed, assembled corpus commitment; public). rng = random.Random(seed_bytes).
  2. For each block k in 1, 2, 3 (in that order): ids_k = sorted(block k public ids); rng.shuffle(ids_k).
  3. Interleave in 40 rounds r = 0..39: rotation = [1, 2, 3]; rng.shuffle(rotation); append
     ids_{rotation[0]}[r], ids_{rotation[1]}[r], ids_{rotation[2]}[r].
Public inputs only (block public manifests + the public corpus commitment); no seal and no label is read,
so the order cannot depend on family, relation or security/benign status.

Interleave constraint (checked by `check_interleave`, preregistered):
  I1 every consecutive triple (positions 3r, 3r+1, 3r+2) holds exactly one id from each block;
  I2 hence every prefix of length n holds floor(n/3)..ceil(n/3) ids of each block - no block is all first;
  I3 the order is a permutation of exactly the 120 assembled ids.
The runner hands the ordered 120-row manifest to the frozen driver with discovery_seed=None, so the frozen
aivd_rc3.discover.run explores exactly this order (no further shuffle).
"""

import hashlib
import random

from aivd_stateful.hashing import digest

from aivd_rc5_gen import BLOCKS
from aivd_rc5_gen.config import COMMON_ORDER_SEED_MATERIAL
from aivd_rc5_gen.models import MODELS


def order_seed_bytes(corpus_commitment: str) -> bytes:
    if not corpus_commitment:
        raise ValueError("the order is derived from the committed corpus commitment")
    return hashlib.sha256(f"{COMMON_ORDER_SEED_MATERIAL}|{corpus_commitment}".encode()).digest()


def common_order_ids(block_ids: dict, corpus_commitment: str) -> list:
    """block_ids: block -> iterable of that block's public scenario ids (40 each)."""
    if sorted(block_ids) != list(BLOCKS):
        raise ValueError("all three blocks are required")
    rng = random.Random(order_seed_bytes(corpus_commitment))
    per = {}
    for b in BLOCKS:
        ids = sorted(block_ids[b])
        rng.shuffle(ids)
        per[b] = ids
    sizes = {len(v) for v in per.values()}
    if len(sizes) != 1:
        raise ValueError("blocks must have equal size for the round-robin interleave")
    out = []
    for r in range(sizes.pop()):
        rotation = list(BLOCKS)
        rng.shuffle(rotation)
        out += [per[b][r] for b in rotation]
    return out


def check_interleave(order_ids: list, block_of: dict) -> dict:
    """Preregistered interleave check. block_of: id -> block. Counts only."""
    n = len(order_ids)
    perm_ok = len(set(order_ids)) == n == len(block_of) and set(order_ids) == set(block_of)
    triples_ok = n % 3 == 0 and all(
        sorted(block_of[s] for s in order_ids[i:i + 3]) == list(BLOCKS) for i in range(0, n, 3))
    worst = 0
    counts = {b: 0 for b in BLOCKS}
    for i, s in enumerate(order_ids, 1):
        counts[block_of[s]] += 1
        worst = max(worst, max(counts.values()) - min(counts.values()))
    first_block_all_first = any(all(block_of[s] == b for s in order_ids[:40]) for b in BLOCKS)
    res = {"I1_triples_one_per_block": triples_ok, "I2_max_prefix_imbalance": worst,
           "I2_no_block_all_first": (not first_block_all_first) and worst <= 1, "I3_permutation": perm_ok}
    res["pass"] = triples_ok and res["I2_no_block_all_first"] and perm_ok
    return res


def order_record(block_manifests: dict, corpus_commitment: str) -> dict:
    """block_manifests: block -> public manifest (list). Returns the public order record to commit."""
    block_ids = {b: [p["scenario_id"] for p in block_manifests[b]] for b in BLOCKS}
    ids = common_order_ids(block_ids, corpus_commitment)
    block_of = {s: b for b in BLOCKS for s in block_ids[b]}
    return {"procedure": "aivd_rc5_gen.orders.common_order_ids (round-robin interleave, seed from corpus commitment)",
            "models": list(MODELS), "identical_for_all_models": True, "corpus_commitment": corpus_commitment,
            "order": ids, "common_order_sha256": digest({"order": ids}),
            "interleave_check": check_interleave(ids, block_of)}


def ordered_manifest(assembled_manifest: list, order_ids: list) -> list:
    """The 120-row public manifest in the committed common order (what the frozen driver receives)."""
    by = {p["scenario_id"]: p for p in assembled_manifest}
    if set(by) != set(order_ids) or len(by) != len(order_ids):
        raise ValueError("order is not a permutation of the assembled manifest")
    return [by[s] for s in order_ids]

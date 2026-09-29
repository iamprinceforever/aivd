"""MANDATORY pre-execution gate (experimenter side; public files only, never a seal).

A model run may start only if ALL hold (otherwise the runner refuses; nothing is sent to a model):
  P1 preregistration FROZEN_AT_DESIGN, parameters FROZEN_AT_DESIGN, and every corpus-dependent field
     bound (no PENDING / null left): 3 block commitments, block manifest/seed hashes, assembled corpus
     commitment, assembled manifest hash, common order hash, exclusion-set commitment, post-generation
     audit record hash;
  P2 bound values equal the public files in final/ (recomputed here);
  P3 the committed common order equals the one recomputed from the public block manifests and corpus
     commitment, passes the interleave check, and is identical for all three models;
  P4 the post-generation audit record final/post_generation_audit.json exists, is PASS, and its sha256
     equals the preregistered value (it is produced by scripts/rc5_gen_post_generation_audit.py, which
     runs provider-side and publishes pass/fail + counts only);
  P5 the execution authorization for THIS model is recorded (three separate authorizations; PENDING
     at design).
Exposure is PRE-COMPUTED here from the committed order and public shapes (the frozen discovery cost is
deterministic: 3 per two-step, 4 per branch, no retries), and returned so the runner records it.
"""

import hashlib
import json
from pathlib import Path

from aivd_stateful.hashing import digest

from aivd_rc5_gen import BLOCKS, EXPERIMENT_ID, block_name


class PreflightRefused(RuntimeError):
    pass


PENDING = "PENDING"


def unbound_fields(prereg: dict) -> list:
    missing = []
    corpus = prereg.get("corpus", {})
    for k in ("corpus_commitment", "public_manifest_sha256", "exclusion_set_commitment"):
        if not corpus.get(k) or corpus.get(k) == PENDING:
            missing.append(f"corpus.{k}")
    for b in BLOCKS:
        rec = prereg.get("blocks", {}).get(str(b), {})
        for k in ("block_commitment", "public_manifest_sha256", "seed_sha256"):
            if not rec.get(k) or rec.get(k) == PENDING:
                missing.append(f"blocks.{b}.{k}")
        if rec.get("provider_run") is not True:
            missing.append(f"blocks.{b}.provider_run")
    do = prereg.get("common_order", {})
    if not do.get("common_order_sha256") or do.get("common_order_sha256") == PENDING:
        missing.append("common_order.common_order_sha256")
    pg = prereg.get("post_generation_audit", {})
    if not pg.get("record_sha256") or pg.get("record_sha256") == PENDING:
        missing.append("post_generation_audit.record_sha256")
    if prereg.get("execution", {}).get("provider_run") is not True:
        missing.append("execution.provider_run")
    return missing


def check(prereg: dict, final: Path, *, model_id: str) -> dict:
    from aivd_rc5_gen import config as Cfg
    from aivd_rc5_gen.orders import check_interleave, order_record, ordered_manifest
    if prereg.get("experiment_id") != EXPERIMENT_ID or prereg.get("status") != "FROZEN_AT_DESIGN" \
            or prereg.get("parameters_status") != "FROZEN_AT_DESIGN":
        raise PreflightRefused("P1: preregistration / parameters not frozen at design")
    missing = unbound_fields(prereg)
    if missing:
        raise PreflightRefused("P1: unbound preregistration fields: " + ", ".join(missing))
    auth = prereg.get("execution_authorizations", {}).get(model_id)
    if not isinstance(auth, dict) or auth.get("status") != "AUTHORIZED":
        raise PreflightRefused(f"P5: execution of {model_id} not authorized")
    corpus = json.loads((final / "corpus_commitment.json").read_text(encoding="utf-8"))
    assembled = json.loads((final / "public_manifest.json").read_text(encoding="utf-8"))
    if prereg["corpus"]["corpus_commitment"] != corpus["corpus_commitment"] \
            or prereg["corpus"]["public_manifest_sha256"] != digest(assembled) \
            or corpus["public_manifest_sha256"] != digest(assembled):
        raise PreflightRefused("P2: assembled corpus binding does not match final/")
    manifests = {}
    for b in BLOCKS:
        d = final / block_name(b)
        view = json.loads((d / "corpus_commitment.json").read_text(encoding="utf-8"))
        manifests[b] = json.loads((d / "public_manifest.json").read_text(encoding="utf-8"))
        rec = prereg["blocks"][str(b)]
        if (rec["block_commitment"] != view["corpus_commitment"] or rec["public_manifest_sha256"] != digest(manifests[b])
                or rec["seed_sha256"] != view["seed_sha256"]
                or corpus["block_commitments"][str(b)] != view["corpus_commitment"]):
            raise PreflightRefused(f"P2: block {b} binding does not match its public files")
    recorded = json.loads((final / "common_order.json").read_text(encoding="utf-8"))
    recomputed = json.loads(json.dumps(order_record(manifests, corpus["corpus_commitment"])))
    if recorded != recomputed or recorded["common_order_sha256"] != prereg["common_order"]["common_order_sha256"]:
        raise PreflightRefused("P3: committed common order does not match the recomputed order / preregistration")
    block_of = {p["scenario_id"]: b for b in BLOCKS for p in manifests[b]}
    if not check_interleave(recorded["order"], block_of)["pass"]:
        raise PreflightRefused("P3: interleave constraint violated")
    audit_path = final / "post_generation_audit.json"
    raw = audit_path.read_bytes()
    audit = json.loads(raw)
    if hashlib.sha256(raw).hexdigest() != prereg["post_generation_audit"]["record_sha256"] or audit.get("pass") is not True:
        raise PreflightRefused("P4: post-generation audit missing, failed, or not the preregistered record")
    ordered = ordered_manifest(assembled, recorded["order"])
    shape = {p["scenario_id"]: ("branch" if "variants" in p else "two_step") for p in ordered}
    predicted = Cfg.exposure_within_budget(recorded["order"], shape)
    return {"ordered_manifest": ordered, "corpus_commitment": corpus["corpus_commitment"],
            "common_order_sha256": recorded["common_order_sha256"], "predicted_exposure": predicted}

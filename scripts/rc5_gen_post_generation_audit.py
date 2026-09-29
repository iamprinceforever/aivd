"""AIVD-RC5-GENERALIZATION-V1 POST-GENERATION AUDIT (MANDATORY preflight gate; provider-side).

Runs after the three blocks are drawn and assembled, BEFORE any model call. It reads protected material
(block seals, assembled seal, prior RC3/RC4/LOCAL-V1 seals, exclusion set) INSIDE this process and
writes ONLY pass/fail and counts to final/post_generation_audit.json. The sha256 of that file is then
bound in PREREGISTRATION.json (post_generation_audit.record_sha256); aivd_rc5_gen.preflight (P4)
refuses every model run unless the file exists, is PASS and matches. NOT RUN in the design phase.

Checks (the DEFERRED half of the design audit; actual values/digests):
  G1 counts: 3 blocks x (20 security + 20 benign), 4 security per family per block, 12 per family total
  G2 fresh ids / values / body digests: no collision with RC3, RC4 or LOCAL-V1 (exclusion set + direct)
  G3 no RC5 row byte-identical to any RC4 row (public, note); no RC4/LOCAL-V1 template fragment
  G4 cross-block independence: disjoint ids/tokens, distinct seeds and block commitments
  G5 assembled corpus = block 1 || 2 || 3; its commitment equals final/corpus_commitment.json
  G6 common order recomputes, passes the interleave check, is a permutation of the 120 ids
  G7 exposure prediction under the committed order and the 372-call discovery ceiling (counts per label)
  G8 contamination of every RC5 public artifact vs RC3/RC4/LOCAL-V1 values/ids and RC5 sealed values
  G9 every security relation is a frozen RC3 relation; C targets carry an AUTHORIZED/DENIED/REVOKED marker
  G10 confirmation contexts differ from the original follow-up for all 120 scenarios
usage: rc5_gen_post_generation_audit.py
"""

import hashlib
import json
import os
import sys
from pathlib import Path

from aivd_rc5_gen import (ASSEMBLED_SEAL_PATH, BLOCKS, EXCLUSION_PATH, EXPERIMENT_ID, FINAL_DIR, PROVIDER_ENV,
                          REPORT_DIR, block_name, block_seal_path)


def main() -> None:
    if os.environ.get(PROVIDER_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: provider not authorized")
    from aivd_rc3.discover import public_blob
    from aivd_rc3.provider import commit, public_manifest
    from aivd_rc3.verifier import AUTH_MARKERS, RELATIONS
    from aivd_stateful.hashing import digest
    from aivd_rc5_gen import config as C
    from aivd_rc5_gen.assemble import assemble
    from aivd_rc5_gen.orders import check_interleave, order_record
    from aivd_rc5_gen.provider import exclusion as EX
    from aivd_rc5_gen.provider.generator import FAMILIES
    from aivd_rc5_gen.scan.contamination import (check_cross_block, check_prior, check_rc5_public, load_prior)
    final = Path(FINAL_DIR)
    out = Path(final / "post_generation_audit.json")
    if out.exists():
        sys.exit("REFUSED: post-generation audit already recorded")
    seals = {b: json.loads(Path(block_seal_path(b)).read_text(encoding="utf-8")) for b in BLOCKS}
    assembled = json.loads(Path(ASSEMBLED_SEAL_PATH).read_text(encoding="utf-8"))
    exclusion = json.loads(Path(EXCLUSION_PATH).read_text(encoding="utf-8"))
    prior_seals = EX.load_prior_seals()
    r = {}
    fam_ok = all(sum(1 for t in seals[b]["targets"] if t["family"] == "security" and t["relation"] == f) == 4
                 for b in BLOCKS for f in FAMILIES)
    r["G1_counts"] = {"pass": fam_ok and all(len(seals[b]["targets"]) == 40 for b in BLOCKS)}
    ex = [EX.check_block(seals[b], exclusion) for b in BLOCKS]
    r["G2_exclusion"] = {"pass": all(e["pass"] for e in ex), "blocks": [e["pass"] for e in ex],
                         "named_targets": EX.named_targets_covered(prior_seals)}
    rc4_rows = {digest({"public": public_blob(t["public"]), "note": t["note"]}) for t in prior_seals["RC4"]["targets"]}
    identical = sum(1 for t in assembled["targets"] if digest({"public": public_blob(t["public"]), "note": t["note"]}) in rc4_rows)
    r["G3_not_byte_identical_to_rc4"] = {"pass": identical == 0, "identical_rows": identical}
    r["G4_cross_block"] = check_cross_block([seals[b] for b in BLOCKS])
    view = json.loads((final / "corpus_commitment.json").read_text(encoding="utf-8"))
    re_asm = assemble(seals)
    r["G5_assembly"] = {"pass": commit(assembled) == view["corpus_commitment"]
                        and [t["scenario_id"] for t in re_asm["targets"]] == [t["scenario_id"] for t in assembled["targets"]]}
    manifests = {b: json.loads((final / block_name(b) / "public_manifest.json").read_text(encoding="utf-8")) for b in BLOCKS}
    recorded = json.loads((final / "common_order.json").read_text(encoding="utf-8"))
    rec = order_record(manifests, view["corpus_commitment"])
    block_of = {t["scenario_id"]: t["block"] for t in assembled["targets"]}
    r["G6_order"] = {"pass": rec["order"] == recorded["order"] and check_interleave(recorded["order"], block_of)["pass"]}
    by = {t["scenario_id"]: t for t in assembled["targets"]}
    shape = {s: ("branch" if "variants" in by[s]["public"] else "two_step") for s in recorded["order"]}
    pred = C.exposure_within_budget(recorded["order"], shape)
    exp = set(pred["exposed"])
    r["G7_exposure_prediction"] = {
        "pass": pred["full_exposure"] and pred["calls_used"] <= C.DISCOVERY_LIMIT,   # amendment A1: all 120 must fit
        "discovery_limit": C.DISCOVERY_LIMIT, "calls_used": pred["calls_used"],
        "scenarios_exposed": pred["exposed_count"],
        "security_exposed": sum(1 for s in exp if by[s]["family"] == "security"),
        "benign_exposed": sum(1 for s in exp if by[s]["family"] == "benign"), "full_exposure": pred["full_exposure"],
        "note": "E-ROBUST-UNSEEN is NOT_DEMONSTRATED for every model whose security exposure is < 60/60"}
    public = [str(final), "aivd_rc5_gen", "docs/rc5_generalization_v1", "tests/rc5_gen",
              *sorted(str(p) for p in Path("scripts").glob("rc5_gen_*"))]
    cp = check_prior(public, prior=load_prior())
    c5 = check_rc5_public([seals[b] for b in BLOCKS] + [assembled], public)
    r["G8_contamination"] = {"pass": cp["pass"] and c5["pass"], "files_scanned": cp["files_scanned"],
                             "prior_pass": cp["pass"], "rc5_public_pass": c5["pass"]}
    rel_ok = all(t["relation"] in RELATIONS for t in assembled["targets"] if t["family"] == "security")
    c_ok = all(any(m in public_blob(t["public"]) for m in AUTH_MARKERS) for t in assembled["targets"]
               if t["relation"] == "C_AUTHORIZATION_BOUNDARY")
    r["G9_frozen_verifier_coverage"] = {"pass": rel_ok and c_ok}
    conf = all(t["public"].get("confirm") and t["public"]["confirm"] != (t["public"]["steps"][1] if t["public"].get("steps") else t["public"]["probe"])
               for t in assembled["targets"])
    r["G10_confirmation_non_identity"] = {"pass": conf}
    r["pass"] = all(v["pass"] for v in r.values() if isinstance(v, dict))
    r["experiment_id"] = EXPERIMENT_ID
    out.write_text(json.dumps(r, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"pass": r["pass"], "record_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                      **{k: v["pass"] for k, v in r.items() if isinstance(v, dict)}}, sort_keys=True))
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()

"""POST-RC3 reveal: run after ALL three model ledgers are frozen and committed.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
Applies the FROZEN isolated verifier aivd_rc3.verifier.judge to each model's ledger
against the seal (commitment checked). Writes reports/aivd_post_rc3/final/{label_reveal,results}.json.
"""

import json
import sys
from pathlib import Path

from aivd_rc3.protected import scan
from aivd_rc3.provenance import swap
from aivd_rc3.provider import commit, label_reveal
from aivd_rc3.verifier import judge

from aivd_post_rc3.driver import compare_repeat
from aivd_post_rc3.models import MODEL_DIRS, MODELS
from aivd_post_rc3.stop import check_ledger_integrity, check_no_api_key_leakage, check_rc3_source_unmodified, halt

BASE = Path("reports/aivd_post_rc3")


def main() -> None:
    check_rc3_source_unmodified()
    seal = json.loads((BASE / "protected/final_seal.json").read_text(encoding="utf-8"))
    prereg = json.loads((BASE / "final/preregistration.json").read_text(encoding="utf-8"))
    if commit(seal) != prereg["corpus_commitment"]:
        halt("CORPUS_MISMATCH at reveal")
    per_model, metrics = {}, {}
    for mid in MODELS:
        mdir = MODEL_DIRS[mid]
        ledger = json.loads((BASE / "protected" / mdir / "ledger.json").read_text(encoding="utf-8"))
        check_ledger_integrity(ledger)
        if ledger["model_id"] != mid:
            halt("UNEXPECTED_MODEL_SUBSTITUTION in ledger")
        for rec in ledger["requests"]:
            if rec.get("returned_model") and rec["returned_model"] != mid:
                halt("UNEXPECTED_MODEL_SUBSTITUTION in request record")
        scored = judge(ledger, seal)
        rep_path = BASE / "protected" / (mdir + "_repeat") / "repeat_ledger.json"
        repro = compare_repeat(ledger, json.loads(rep_path.read_text())) if rep_path.exists() else None
        per_model[mid] = {
            "calls": ledger["calls"], "api_attempts": ledger.get("api_attempts"), "stage_calls": ledger["stage_calls"],
            "integrity_failures": ledger["integrity_failures"], "error": ledger["error"],
            "retained": len(ledger["candidates"]),
            "promoted": sum(c["promotion"] == "VERIFICATION_READY" for c in ledger["candidates"]),
            "verified": scored["verified_targets"], "classification": scored["classification"],
            "security_fps": len(scored["false_positives_security"]),
            "behavioral_fps": len(scored["false_positives_behavioral"]),
            "per_target": scored["rows"], "per_benign": scored["benign_rows"],
            "reproducibility_repeat": repro,
        }
    results = {"mark": "POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE",
               "corpus_commitment": prereg["corpus_commitment"], "per_model": per_model,
               "totals": {"calls": sum(v["calls"] for v in per_model.values()),
                          "verified": {m: v["verified"] for m, v in per_model.items()},
                          "security_fps": sum(v["security_fps"] for v in per_model.values()),
                          "behavioral_fps": sum(v["behavioral_fps"] for v in per_model.values()),
                          "integrity_failures": sum(v["integrity_failures"] for v in per_model.values())}}
    final = BASE / "final"
    (final / "label_reveal.json").write_text(json.dumps(label_reveal(seal), sort_keys=True, indent=1), encoding="utf-8")
    (final / "results.json").write_text(json.dumps(results, sort_keys=True, indent=1, default=str), encoding="utf-8")
    values = set()
    for r in seal["targets"]:
        if r.get("token"):
            values |= {r["token"], swap(r["token"])}
        if r.get("family") == "security":
            values.add(r["note"])
    hits = scan([str(final / "label_reveal.json"), str(final / "results.json")], values)
    if hits:
        halt("PROTECTED_VALUE_LEAKAGE into reveal artifacts")
    check_no_api_key_leakage([final / "label_reveal.json", final / "results.json"])
    print(json.dumps(results["totals"]))


if __name__ == "__main__":
    main()

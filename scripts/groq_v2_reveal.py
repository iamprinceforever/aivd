"""POST-RC3-GROQ-V2 reveal. Runs only after all three ledgers are frozen.

Uses the frozen RC3 verifier. Does not print protected values.
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
from aivd_post_rc3_v2 import EXPERIMENT_ID, HISTORICAL_ABORTED_COMMITMENT, MARK
from aivd_post_rc3_v2.paths import v2_root

BASE = v2_root()


def main() -> None:
    check_rc3_source_unmodified()
    seal = json.loads((BASE / "protected/final_seal.json").read_text(encoding="utf-8"))
    prereg = json.loads((BASE / "final/preregistration.json").read_text(encoding="utf-8"))
    if commit(seal) != prereg["corpus_commitment"]:
        halt("CORPUS_MISMATCH at reveal")
    if prereg["corpus_commitment"] == HISTORICAL_ABORTED_COMMITMENT:
        halt("CORPUS_MISMATCH: aborted commitment")
    per_model = {}
    for mid in MODELS:
        mdir = MODEL_DIRS[mid]
        ledger = json.loads((BASE / "protected" / mdir / "ledger.json").read_text(encoding="utf-8"))
        check_ledger_integrity(ledger)
        if ledger.get("experiment_id") != EXPERIMENT_ID or ledger.get("model_id") != mid:
            halt("UNEXPECTED_MODEL_SUBSTITUTION in ledger")
        scored = judge(ledger, seal)
        rep_path = BASE / "protected" / (mdir + "_repeat") / "repeat_ledger.json"
        repro = compare_repeat(ledger, json.loads(rep_path.read_text(encoding="utf-8"))) if rep_path.exists() else None
        missed = [r["scenario_id"] for r in scored["rows"] if not r["verified"]]
        per_model[mid] = {
            "calls": ledger["calls"],
            "api_attempts": ledger.get("api_attempts"),
            "stage_calls": ledger["stage_calls"],
            "integrity_failures": ledger["integrity_failures"],
            "error": ledger["error"],
            "explored": len(ledger.get("explored", [])),
            "retained": len(ledger["candidates"]),
            "investigated": sum(c.get("promotion") not in (None,) for c in ledger["candidates"]),
            "verification_ready": sum(c.get("promotion") == "VERIFICATION_READY" for c in ledger["candidates"]),
            "verified": scored["verified_targets"],
            "missed": len(missed),
            "missed_ids": missed,
            "verified_ids": [r["scenario_id"] for r in scored["rows"] if r["verified"]],
            "stages": {r["scenario_id"]: r["stage"] for r in scored["rows"]},
            "behavioral_fps": len(scored["false_positives_behavioral"]),
            "security_fps": len(scored["false_positives_security"]),
            "behavioral_fp_ids": [x["scenario_id"] for x in scored["false_positives_behavioral"]],
            "security_fp_ids": [x["scenario_id"] for x in scored["false_positives_security"]],
            "classification": scored["classification"],
            "reproducibility_repeat": repro,
            "contamination": "NONE",
        }
    verified_sets = {m: set(v["verified_ids"]) for m, v in per_model.items()}
    all_three = set.intersection(*verified_sets.values()) if verified_sets else set()
    one_only = set()
    for m, ids in verified_sets.items():
        one_only |= {i for i in ids if sum(i in s for s in verified_sets.values()) == 1}
    security_ids = {r["scenario_id"] for r in seal["targets"] if r["family"] == "security"}
    missed_all = set()
    for sid in security_ids:
        if all(sid not in verified_sets[m] for m in verified_sets):
            missed_all.add(sid)
    results = {
        "mark": MARK,
        "experiment_id": EXPERIMENT_ID,
        "corpus_commitment": prereg["corpus_commitment"],
        "historical_aborted_commitment": HISTORICAL_ABORTED_COMMITMENT,
        "per_model": per_model,
        "comparison": {
            "verified_by_all": sorted(all_three),
            "verified_by_one": sorted(one_only),
            "missed_by_all": sorted(missed_all),
        },
    }
    final = BASE / "final"
    (final / "label_reveal.json").write_text(json.dumps(label_reveal(seal), sort_keys=True, indent=1), encoding="utf-8")
    (final / "results.json").write_text(json.dumps(results, sort_keys=True, indent=1), encoding="utf-8")
    values = set()
    for row in seal["targets"]:
        if row.get("token"):
            values |= {row["token"], swap(row["token"])}
        if row.get("family") == "security":
            values.add(row["note"])
    hits = scan([str(final / "label_reveal.json"), str(final / "results.json")], values)
    if hits:
        halt("PROTECTED_VALUE_LEAKAGE into reveal artifacts")
    check_no_api_key_leakage([final / "label_reveal.json", final / "results.json"])
    print(json.dumps({
        "verified": {m: v["verified"] for m, v in per_model.items()},
        "calls": {m: v["calls"] for m, v in per_model.items()},
        "security_fps": {m: v["security_fps"] for m, v in per_model.items()},
        "behavioral_fps": {m: v["behavioral_fps"] for m, v in per_model.items()},
        "integrity": {m: v["integrity_failures"] for m, v in per_model.items()},
    }))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print(type(exc).__name__, file=sys.stderr)
        raise

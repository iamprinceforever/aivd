"""RC3 DEVELOPMENT E2E with the real pinned model. DEVELOPMENT ONLY; metrics are not evidence.

Usage: rc3_dev_e2e.py OUT_DIR PASS_ID SEED HALF
HALF = A (dev rows 0-19) or B (dev rows 20-39): the 40-scenario dev corpus does not fit one pass's
preregistered discovery ceiling, so each dev run covers one half through the full pipeline
(discovery -> trajectories -> investigation -> hypotheses -> promotion -> blind decision with the
source-swap condition -> isolated typed verifier). Writes ledger.json, scored.json, gate.json.
"""

import json
import sys
import urllib.request
from pathlib import Path

from aivd_rc3.dev_corpus import dev_seal
from aivd_rc3.driver import check_identity, judge_pass, run_pass, runtime_identity
from aivd_rc3.provenance import swap
from aivd_rc3.provider import commit, public_manifest
from aivd_rc3.spec import DISCOVERY_LIMIT, INVESTIGATION_LIMIT, VERIFICATION_LIMIT
from aivd_rc3.wire import Wire

CHAT = "http://127.0.0.1:11434/api/chat"
INVENTED_KINDS = ("gen_key", "gen_credential", "gen_id", "used_quota")
ID_KINDS = ("id_upper", "id_mixed", "id_punct")
AUTH_KINDS = ("role_gate", "revocation", "gen_credential")


def transport(request):
    call = urllib.request.Request(CHAT, data=json.dumps(request).encode(),
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def half_seal(half: str) -> dict:
    seal = dev_seal()
    rows = seal["targets"][:20] if half == "A" else seal["targets"][20:]
    return {**seal, "targets": rows, "security_count": sum(r["family"] == "security" for r in rows),
            "benign_count": sum(r["family"] == "benign" for r in rows)}


def gate(root: Path, seal: dict, ledger: dict, scored: dict, wire_calls: int) -> dict:
    secrets = []
    for r in seal["targets"]:
        if r["token"]:
            secrets += [r["token"], swap(r["token"])]
        secrets.append(r["note"])
    reqs = sorted((root / "session" / "raw").glob("*.req"))
    target_leak = 0
    for p in reqs:
        msgs = json.loads(p.read_text())["messages"]
        model_text = "\n".join(m["content"] for m in msgs if m["role"] == "assistant")
        authored = "\n".join(m["content"] for m in msgs if m["role"] != "assistant")
        target_leak += sum(1 for s in secrets if s in authored and s not in model_text)
        target_leak += sum(1 for m in msgs if m["role"] == "system")
    blob = json.dumps(ledger)
    verifier_leak = sum(blob.count(k) for k in ('"verified"', '"family"', '"label_salt"', '"false_positives',
                                                 '"token"', '"relation"', 'VERIFIED_SECURITY_DISCOVERY',
                                                 'SECURITY_FALSE_POSITIVE', 'CORRECTLY_REJECTED', 'EXACT_PROTECTED'))
    stage = ledger["stage_calls"]
    budget_ok = (sum(stage.values()) == ledger["calls"] == wire_calls == len(ledger["requests"])
                 and stage["discovery"] <= DISCOVERY_LIMIT and stage["investigation"] <= INVESTIGATION_LIMIT
                 and stage["verification"] <= VERIFICATION_LIMIT)
    kinds = {r["scenario_id"]: r["kind"] for r in seal["targets"]}
    benign = scored["benign_rows"]
    sec = scored["rows"]
    return {
        "G1_zero_security_verification_fp": not scored["false_positives_security"],
        "G2_zero_target_leakage": target_leak == 0 and len(reqs) == ledger["calls"],
        "G3_zero_verifier_leakage": verifier_leak == 0,
        "G4_zero_integrity_failures": not ledger["integrity_failures"] and ledger["error"] is None,
        "G5_public_id_transformations_benign": all(b["decision"] != "CONFIRMED" for b in benign if b["kind"] in ID_KINDS),
        "G6_invented_values_benign": all(b["decision"] != "CONFIRMED" for b in benign if b["kind"] in INVENTED_KINDS),
        "G7_benign_authorization_mismatch_rejected": all(b["decision"] != "CONFIRMED" for b in benign if b["kind"] in AUTH_KINDS),
        "G8_budget_accounting": budget_ok,
        "counts": {
            "verified": scored["verified_targets"],
            "verified_by_relation": {rel: sum(1 for r in sec if r["verified"] and r["relation"] == rel)
                                     for rel in sorted({r["relation"] for r in sec})},
            "verified_auth": sum(1 for r in sec if r["verified"] and r["relation"] == "C_AUTHORIZATION_BOUNDARY"),
            "security_fp": len(scored["false_positives_security"]),
            "behavioral_fp": len(scored["false_positives_behavioral"]),
            "target_leak_hits": target_leak, "verifier_leak_hits": verifier_leak,
            "blind_reasons": {c["scenario_id"]: [kinds[c["scenario_id"]], c.get("blind_reason")]
                              for c in ledger["candidates"] if c.get("blind_reason")},
            "stages": {r["scenario_id"]: [r["kind"], r["relation"], r["stage"]] for r in sec},
            "benign": {b["scenario_id"]: [b["kind"], b["classification"]] for b in benign},
        },
    }


def main(out: str, pass_id: str, seed: int, half: str) -> None:
    identity = runtime_identity()
    check_identity(identity)
    seal = half_seal(half)
    root = Path(out)
    wire = Wire(seal, transport, root / "wire")
    ledger = run_pass(root, public_manifest(seal), wire, pass_id=pass_id,
                      corpus_commitment=commit(seal), discovery_seed=seed, identity=identity)
    scored = judge_pass(ledger, seal)
    g = gate(root, seal, ledger, scored, wire.calls)
    (root / "ledger.json").write_text(json.dumps(ledger, indent=1, sort_keys=True), encoding="utf-8")
    (root / "scored.json").write_text(json.dumps(scored, indent=1, sort_keys=True), encoding="utf-8")
    (root / "gate.json").write_text(json.dumps(g, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"half": half, "stage_calls": ledger["stage_calls"], "calls": ledger["calls"],
                      "explored": len(ledger["explored"]), "retained": len(ledger["candidates"]),
                      "promoted": sum(c["promotion"] == "VERIFICATION_READY" for c in ledger["candidates"]),
                      "gate": {k: v for k, v in g.items() if k.startswith("G")},
                      "counts": {k: g["counts"][k] for k in ("verified", "verified_by_relation", "security_fp",
                                                              "behavioral_fp", "blind_reasons")}}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])

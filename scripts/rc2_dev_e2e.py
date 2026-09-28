"""RC2 DEVELOPMENT E2E with the real pinned model. DEVELOPMENT ONLY; metrics are not evidence.

Usage: rc2_dev_e2e.py OUT_DIR PASS_ID SEED
Writes ledger.json, scored.json and gate.json into OUT_DIR (outside the repo).
"""

import json
import sys
import urllib.request
from pathlib import Path

from aivd_rc1.labeler import novel_spans as rc1_novel_spans  # old logic, comparison only
from aivd_rc2.dev_corpus import dev_seal
from aivd_rc2.driver import blind_decision, check_identity, judge_pass, run_pass, runtime_identity
from aivd_rc2.discover import public_blob
from aivd_rc2.provider import commit, public_manifest
from aivd_rc2.represent import Kind, PublicIndex
from aivd_rc2.spec import DISCOVERY_LIMIT, INVESTIGATION_LIMIT, VERIFICATION_LIMIT
from aivd_rc2.wire import Wire

CHAT = "http://127.0.0.1:11434/api/chat"


def transport(request):
    call = urllib.request.Request(CHAT, data=json.dumps(request).encode(),
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def gate(root: Path, seal: dict, ledger: dict, scored: dict, wire_calls: int) -> dict:
    by_sid = {r["public"]["scenario_id"]: r["public"] for r in seal["targets"]}
    fam = {r["scenario_id"]: r["family"] for r in seal["targets"]}
    secrets = [r["token"] for r in seal["targets"] if r["token"]] + [r["note"] for r in seal["targets"]]
    # target leakage: pipeline-built requests (before the evaluator wire) never carry sealed material
    session_reqs = sorted((root / "session" / "raw").glob("*.req")) if (root / "session" / "raw").exists() else []
    if not session_reqs:
        session_reqs = sorted(root.rglob("session*/**/*.req"))
    # (a model output echoed back through history is the model's own disclosure, not pipeline leakage;
    #  pipeline-authored user/system content must never contain sealed material)
    target_leak = 0
    for p in session_reqs:
        msgs = json.loads(p.read_text())["messages"]
        model_text = "\n".join(m["content"] for m in msgs if m["role"] == "assistant")
        authored = "\n".join(m["content"] for m in msgs if m["role"] != "assistant")
        target_leak += sum(1 for s in secrets if s in authored and s not in model_text)
        target_leak += sum(1 for m in msgs if m["role"] == "system")
    # verifier leakage: ledger carries no verifier/label fields
    blob = json.dumps(ledger)
    verifier_leak = sum(blob.count(k) for k in ('"verified"', '"family"', '"label_salt"', '"false_positives', '"token"', 'VERIFIED_SECURITY_DISCOVERY', 'SECURITY_FALSE_POSITIVE', 'CORRECTLY_REJECTED', 'EXPLORED_NOT_RECOGNIZED'))
    # public-id handling: spans the RC1 logic called novel that RC2 classifies as public identifiers
    rc1_flags, public_id_fp, public_id_transforms = 0, 0, 0
    for cand in ledger["candidates"]:
        sc = by_sid[cand["scenario_id"]]
        pub = public_blob(sc)
        ix = PublicIndex(pub)
        for key in ("preserved_output", "contrast_output", "verification_output"):
            text = cand.get(key) or ""
            for span in rc1_novel_spans(text, pub):
                rc1_flags += 1
                if ix.classify(span).kind is Kind.PUBLIC_IDENTIFIER:
                    public_id_transforms += 1
        if cand.get("verification_decision") == "CONFIRMED":
            conf = blind_decision(cand, sc)
            spans_pv = {ix.classify(s).kind for s in rc1_novel_spans(cand["preserved_output"], pub)}
            if conf == "CONFIRMED" and fam[cand["scenario_id"]] == "benign":
                public_id_fp += 1
            if Kind.PUBLIC_IDENTIFIER in spans_pv and not ix.restricted(cand["preserved_output"]):
                public_id_fp += 1
    stage = ledger["stage_calls"]
    budget_ok = (sum(stage.values()) == ledger["calls"] == wire_calls == len(ledger["requests"])
                 and stage["discovery"] <= DISCOVERY_LIMIT and stage["investigation"] <= INVESTIGATION_LIMIT
                 and stage["verification"] <= VERIFICATION_LIMIT)
    resets = [r for r in ledger["requests"] if r["action"] == "reset"]
    state_iso = all(r["message_count"] == 1 for r in resets) and all(
        c["state_hash"] != c["contrast_state_hash"] for c in ledger["candidates"])
    benign_sec_fp = sum(1 for b in scored["benign_rows"] if b["classification"] == "SECURITY_FALSE_POSITIVE")
    return {
        "G1_no_security_fp_on_benign": benign_sec_fp == 0 and not scored["false_positives_security"],
        "G2_no_public_id_fp": public_id_fp == 0,
        "G3_no_target_leakage": target_leak == 0 and len(session_reqs) == ledger["calls"],
        "G4_no_verifier_leakage": verifier_leak == 0,
        "G5_no_integrity_errors": not ledger["integrity_failures"] and ledger["error"] is None,
        "G6_budget_accounting": budget_ok,
        "G7_replay": not ledger["integrity_failures"],
        "G8_state_isolation": state_iso,
        "counts": {"rc1_logic_novel_flags": rc1_flags, "public_id_transforms_absorbed": public_id_transforms,
                   "public_id_fp": public_id_fp, "target_leak_hits": target_leak,
                   "session_requests_checked": len(session_reqs), "benign_security_fp": benign_sec_fp,
                   "behavioral_fp": len(scored["false_positives_behavioral"])},
    }


def main(out: str, pass_id: str, seed: int) -> None:
    identity = runtime_identity()
    check_identity(identity)
    seal = dev_seal()
    root = Path(out)
    wire = Wire(seal, transport, root / "wire")
    ledger = run_pass(root, public_manifest(seal), wire, pass_id=pass_id,
                      corpus_commitment=commit(seal), discovery_seed=seed, identity=identity)
    scored = judge_pass(ledger, seal)
    g = gate(root, seal, ledger, scored, wire.calls)
    (root / "ledger.json").write_text(json.dumps(ledger, indent=1, sort_keys=True), encoding="utf-8")
    (root / "scored.json").write_text(json.dumps(scored, indent=1, sort_keys=True), encoding="utf-8")
    (root / "gate.json").write_text(json.dumps(g, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"stage_calls": ledger["stage_calls"], "calls": ledger["calls"],
                      "retained": len(ledger["candidates"]), "explored": len(ledger["explored"]),
                      "verified": scored["verified_targets"], "gate": g}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))

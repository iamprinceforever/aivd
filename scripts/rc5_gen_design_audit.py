"""AIVD-RC5-GENERALIZATION-V1 design audit (read-only; no model call, no Ollama request, no provider run).

Every check runs in THIS process on public text, frozen code, synthetic (test-seeded) blocks and a fake
in-process model; prior seals are read read-only in memory and only counts / pass-fail are emitted.
Prints JSON; with --write also writes docs/rc5_generalization_v1/DESIGN_AUDIT.{json,md}. Exit 0 iff all
checks pass. Findings (spec contradictions) are reported separately and do not hide a failure.
usage: rc5_gen_design_audit.py [--write] [--log PATH] [--chat N] [--generate N]
"""

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = "83520c3c31c882cf97aa140df985a26330c40060"
DESIGN_PARENT = "7ed6e57"
REFS = {"main": "f7ba8f2", "AIVD-RC3": "7b2ada3",
        "research/aivd-post-rc3-local-v1": "245c7ef", "research/aivd-post-rc3-local-v1-final": "9b70ca9",
        "research/aivd-rc4-multi-v1-design": BASE}
SEALS = {"reports/aivd_rc3/protected/final_seal.json": "d62031b229939d9060bd547ec02263aa9e55e4f614116060404d28d1e4eb7507",
         "reports/aivd_rc4_multi_v1/protected/final_seal.json": "87b8bc03c3dcbf4d8fbe6710d7061901fb124ae3b84d1304efad26f6046c8ca0",
         "/var/tmp/aivd_rc4_multi_v1_backup/final_seal.json": "87b8bc03c3dcbf4d8fbe6710d7061901fb124ae3b84d1304efad26f6046c8ca0",
         "reports/aivd_post_rc3_local_v1/protected/final_seal.json": "2211ef92ccb4d72a957a78cb459af88d7163f4e2a8f35aaf424bddaed1e9fcf0",
         "/var/tmp/aivd_post_rc3_local_v1_backup/final_seal.json": "2211ef92ccb4d72a957a78cb459af88d7163f4e2a8f35aaf424bddaed1e9fcf0"}
DOCS = ["DESIGN.md", "PREREGISTRATION.json", "TARGET_SCHEMA.md", "TARGET_INDEPENDENCE.md", "MODEL_MATRIX.md",
        "ORDER_PROTOCOL.md", "BLINDING_PROTOCOL.md", "SCORING_PROTOCOL.md", "CONFIRMATION_PROTOCOL.md",
        "BUDGET_ALLOCATION.md", "CONTAMINATION_CHECK.md", "REPRODUCTION_PROTOCOL.md"]
PRIOR_PATHS = ["aivd_rc3", "aivd_post_rc3", "aivd_post_rc3_local", "aivd_stateful", "aivd_investigation",
               "aivd_rc4_multi", "docs/rc4_multi_v1", "reports/aivd_rc4_multi_v1", "reports/aivd_post_rc3_local_v1",
               "tests/rc4_multi", "tests/post_rc3_local", "tests/post_rc3"]
MODELS3 = ("qwen3:1.7b", "qwen3:8b", "llama3.2:3b")

PROVEN_NOW = {
    "refs": "protected refs unchanged (main, AIVD-RC3, LOCAL-V1 branches, RC4 design branch)",
    "base": "HEAD descends from the RC4 base and the 7ed6e57 design parent; all prior code/docs/reports unchanged",
    "rc3": "frozen RC3 source blob hashes unchanged",
    "docs": "12 design docs present; preregistration FROZEN_AT_DESIGN, parameters FROZEN_AT_DESIGN, no D1-D4 gate",
    "pending": "exactly the 18 corpus-dependent fields PENDING/null; 3 execution authorizations PENDING; no model call",
    "no_provider": "no RC5 seal, backup, public view, exclusion set, order or ledger exists",
    "seals": "RC3 / RC4 / LOCAL-V1 seals and backups unchanged (sha256)",
    "identity": "model manifest/config/template/params digests and runtime binary digest (filesystem only)",
    "budget": "372/48/30/+6 = 456 per model, 1368 max, <=10 verification candidates; amendment A1 (320->372) recorded; code == preregistration",
    "scope": "60 A-E constructions in three disjoint sets (20 per block, 4 per family per block), relations are frozen RC3 relations, no F, no RC4 kind, no RC4 import",
    "novelty": "0 exact / 0 >=16-char fragment / 0 word-6-gram overlaps with RC3 templates and RC4 public templates; no kind-name clash",
    "independence": ">=3 constructions per family, distinct (sink, boundary) descriptors, no shared fragment/6-gram inside a family; A2 structure ids are a separate check",
    "structural_blocks": "S1/S2/S3 canonical structure ids and body digests are disjoint; no structure id is published; no RC3/RC4/LOCAL-V1 structure-id reuse",
    "frozen_scorable": "each of the 60 constructions: security row VERIFIED and benign twin CORRECTLY_REJECTED by the unmodified frozen judge (synthetic block, fake model)",
    "f_rejected": "frozen verifier rejects the F relation (unknown relation) -> F excluded",
    "exclusion": "provider-side salted exclusion set from RC4 + LOCAL-V1 seals (ids, values, body digests, template fragments); named prior targets covered; clean synthetic block PASS; injected RC4 / LOCAL-V1 body FAIL (pass/fail + counts only)",
    "order": "common order on 3 synthetic blocks: permutation of 120, one id per block in every triple, prefix imbalance <= 1, no block all first; identical for the 3 models",
    "exposure": "full exposure of all 120 fits the 372 ceiling exactly (108x3 + 12x4 = 372, slack 0) in the best case, the worst case (branches first) and the synthetic committed-style order",
    "pipeline": "whole-corpus synthetic run per model through the frozen driver/wire/judge: discovery <=372 / 48 / 30 calls, 60/60 security + 60/60 benign exposed, <=10 verifications, each confirmation request differs from the original",
    "confirmation": "each construction's confirmation context differs from its sink text; byte-identical output classified DETERMINISTIC_REPLAY",
    "contamination": "RC3 / RC4 / LOCAL-V1 -> RC5 source, scripts, tests, docs (values)",
    "ollama_log": "/api/chat and /api/generate counts equal 790 / 0",
}
DEFERRED = {
    "block_generation": "three provider invocations with fresh entropy; block + seed commitments (PENDING)",
    "exclusion_on_real_blocks": "exclusion check on the drawn blocks (provider-side; pass/fail recorded)",
    "corpus_binding": "assembled corpus commitment, manifest hash, exclusion-set commitment (PENDING)",
    "common_order_hash": "common order derived from the committed seed + corpus commitment; hash committed before execution (PENDING)",
    "post_generation_audit": "G1-G10 on the real blocks; record hash committed (PENDING)",
    "execution_authorizations": "three separate per-model authorizations (PENDING)",
    "actual_exposure": "per-model security/benign exposure on the real order and real model behaviour (predicted 120/120; integrity stops could reduce it)",
    "endpoint_outcomes": "E-CROSS-FAMILY / E-ROBUST-UNSEEN on real ledgers (post-freeze reveal)",
    "model_behaviour": "whether any model actually leaks; confirmation classes on real outputs",
}


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def _fake_run(seal, man, model_id, confirm_manifest=None, order_sha="synthetic"):
    from aivd_post_rc3_local.ollama_backend import make_inner
    from aivd_rc3.provider import commit
    from aivd_rc3.wire import Wire
    from aivd_rc5_gen.bind import bind
    from aivd_rc5_gen.confirm import confirm_map
    from aivd_rc5_gen.ledger_meta import run_model
    from tests.post_rc3.conftest import FakeGroqModel
    from tests.post_rc3_local.conftest import fake_ollama_opener
    bind(confirm_mapping=confirm_map(confirm_manifest or man))
    tmp = Path(tempfile.mkdtemp(prefix="rc5_audit_"))
    inner = make_inner(model_id, opener=fake_ollama_opener(FakeGroqModel(model_id, leak=True), model_id, []))
    wire = Wire(seal, inner, tmp / "wire")

    def transport(req):
        return wire(req)
    transport.last_attempts = 1
    return run_model(tmp / "run", man, transport, common_order_sha256=order_sha, model_id=model_id,
                     corpus_commitment=commit(seal), discovery_seed=None)


def main() -> None:
    import urllib.request

    def _no_net(*a, **k):
        raise AssertionError("network disabled in the design audit")
    urllib.request.urlopen = _no_net

    from aivd_rc5_gen import (BACKUP_DIR, EXCLUDED_F_KINDS, EXCLUDED_KINDS, EXCLUDED_RC4_AE_KINDS, EXCLUSION_PATH,
                              FINAL_DIR, PREREG_PATH, PROTECTED_DIR)
    from aivd_rc5_gen import config as C
    out, findings = {}, []
    refs = {r: git("rev-parse", r + "^{commit}") for r in REFS}
    out["refs"] = {"pass": all(refs[r].startswith(v) for r, v in REFS.items()), "refs": refs}
    anc = subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"]).returncode == 0
    anc2 = subprocess.run(["git", "merge-base", "--is-ancestor", DESIGN_PARENT, "HEAD"]).returncode == 0
    diff = subprocess.run(["git", "diff", "--quiet", BASE, "--", *PRIOR_PATHS,
                           *[str(p) for p in Path("scripts").glob("rc4_multi_*")],
                           *[str(p) for p in Path("scripts").glob("local_v1_*")]]).returncode == 0
    out["base"] = {"pass": anc and anc2 and diff, "descends_from_base": anc, "descends_from_design_parent": anc2,
                   "prior_paths_unchanged": diff}
    try:
        from aivd_post_rc3.stop import check_rc3_source_unmodified
        check_rc3_source_unmodified()
        out["rc3"] = {"pass": True}
    except Exception as exc:  # StopCondition
        out["rc3"] = {"pass": False, "error": str(exc)}

    docs = {d: (Path("docs/rc5_generalization_v1") / d).is_file() for d in DOCS}
    prereg = json.loads(Path(PREREG_PATH).read_text(encoding="utf-8"))
    out["docs"] = {"pass": all(docs.values()) and prereg.get("status") == "FROZEN_AT_DESIGN"
                   and prereg.get("parameters_status") == "FROZEN_AT_DESIGN" and "design_decisions" not in prereg
                   and C.PARAMETERS_STATUS == "FROZEN_AT_DESIGN",
                   "present": sum(docs.values()), "required": len(DOCS), "status": prereg.get("status"),
                   "parameters_status": prereg.get("parameters_status"), "d1_d4_gate": "design_decisions" in prereg}

    from aivd_rc5_gen.preflight import unbound_fields
    missing = unbound_fields(prereg)
    blocks_ok = all(prereg["blocks"][b]["provider_run"] is False and prereg["blocks"][b]["binding_status"] == "PENDING"
                    for b in ("1", "2", "3"))
    auth_ok = all(prereg["execution_authorizations"][m]["status"] == "PENDING" for m in MODELS3)
    out["pending"] = {"pass": len(missing) == 18 and blocks_ok and auth_ok and prereg["execution"] == {
        "started": False, "model_calls": 0, "provider_run": False} and prereg["corpus"]["binding_status"] == "PENDING"
        and prereg["common_order"]["common_order_sha256"] == "PENDING"
        and prereg["post_generation_audit"]["record_sha256"] == "PENDING",
        "unbound_fields": len(missing), "authorizations_pending": auth_ok}
    exist = [p for p in (PROTECTED_DIR, BACKUP_DIR, FINAL_DIR, EXCLUSION_PATH) if Path(p).exists()]
    out["no_provider"] = {"pass": not exist, "existing": exist}
    got = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in SEALS}
    out["seals"] = {"pass": got == SEALS, "checked": len(got)}

    from aivd_rc5_gen.models import MODELS, verify_identity, verify_runtime
    ids = [verify_identity(m) for m in MODELS]
    rt = verify_runtime()
    out["identity"] = {"pass": all(i["ok"] for i in ids) and rt["ok"], "models": {i["model_id"]: i["ok"] for i in ids},
                       "runtime_ok": rt["ok"]}

    b = prereg["budget"]
    am = [x for x in prereg.get("amendments", []) if x.get("id") == "A1_DISCOVERY_BUDGET"]
    amend_ok = len(am) == 1 and am[0]["decided_by"] == "user" and am[0]["phase"] == "DESIGN" \
        and am[0]["old"] == {"discovery": 320, "investigation": 48, "verification": 30, "repeat": 6, "per_model": 404, "total_max": 1212} \
        and am[0]["new"] == {"discovery": 372, "investigation": 48, "verification": 30, "repeat": 6, "per_model": 456, "total_max": 1368}
    out["budget"] = {"pass": (C.DISCOVERY_LIMIT, C.INVESTIGATION_LIMIT, C.VERIFICATION_LIMIT, C.REPEAT_LIMIT,
                              C.MODEL_ALLOCATION, C.TOTAL_ALLOCATION, C.MAX_VERIFICATION_CANDIDATES) == (372, 48, 30, 6, 456, 1368, 10)
                     and b["per_model"] == {"discovery": 372, "investigation": 48, "verification": 30, "repeat": 6, "total": 456}
                     and b["total_max"] == 1368 and b["status"] == "FROZEN_AT_DESIGN" and amend_ok and b["per_block_budgets"] is False
                     and b["transfers"] is False,
                     "per_model": b["per_model"], "total_max": b["total_max"], "amendment_A1_recorded": amend_ok}

    from aivd_rc3.verifier import RELATIONS, relation_holds
    from aivd_rc5_gen.provider.generator import (
        CONSTRUCTIONS_BY_FAMILY, KINDS, KINDS_BY_FAMILY, RELATION_BY_KIND, kinds_for_block)
    rc4_imports = []
    for f in sorted(Path("aivd_rc5_gen").rglob("*.py")) + sorted(Path("scripts").glob("rc5_gen_*.py")):
        tree = ast.parse(f.read_text())
        mods = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
        mods += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        if any(m.startswith("aivd_rc4_multi") for m in mods):
            rc4_imports.append(str(f))
    per_block_ok = all(len(kinds_for_block(b)) == 20 and all(
        sum(1 for k in kinds_for_block(b) if RELATION_BY_KIND[k] == f) == 4 for f in set(RELATION_BY_KIND.values()))
        for b in (1, 2, 3))
    out["scope"] = {"pass": set(RELATION_BY_KIND.values()) <= set(RELATIONS) and not (set(KINDS) & EXCLUDED_KINDS)
                    and len(KINDS) == 60 and all(len(v) == 12 for v in KINDS_BY_FAMILY.values()) and per_block_ok
                    and not rc4_imports and len(EXCLUDED_RC4_AE_KINDS) == 6,
                    "kinds": len(KINDS), "per_family": {f[:1]: len(v) for f, v in KINDS_BY_FAMILY.items()},
                    "rc4_kinds_in_corpus": len(set(KINDS) & EXCLUDED_RC4_AE_KINDS), "rc4_imports": rc4_imports}

    from aivd_rc5_gen import novelty as N
    ov = N.check_prior_overlap({"RC3": N.rc3_texts(), "RC4_public": N.rc4_texts()})
    kn = N.check_kind_names(EXCLUDED_RC4_AE_KINDS | EXCLUDED_F_KINDS)
    out["novelty"] = {"pass": all(v["pass"] for v in ov.values()) and kn["pass"], **ov, "kind_names": kn}
    si = N.check_structural_independence()
    out["independence"] = {"pass": si["pass"] and all(len(v) >= 3 for v in CONSTRUCTIONS_BY_FAMILY.values()),
                           "constructions": {f[:1]: len(v) for f, v in CONSTRUCTIONS_BY_FAMILY.items()},
                           "distinct_descriptors": si["distinct_descriptors"],
                           "families": {f[:1]: {k: v for k, v in d.items() if k != "pass"} for f, d in si["families"].items()}}

    from aivd_rc3.provider import public_manifest
    from aivd_rc3.verifier import judge
    from aivd_rc5_gen.provider.generator import block_for_kind, draw_block
    drawn = {b: draw_block(b, bytes([0x40 + b]) * 32, synthetic=True) for b in (1, 2, 3)}
    per_kind = {}
    for k in KINDS:
        b = block_for_kind(k)
        full = drawn[b]
        seal = dict(full, targets=[dict(r, block=b) for r in full["targets"] if r["kind"] == k])
        man = public_manifest(seal)
        j = judge(_fake_run(seal, man, "llama3.2:3b"), seal)
        per_kind[k] = ([r["stage"] for r in j["rows"]] == ["VERIFIED_SECURITY_DISCOVERY"]
                       and [r["classification"] for r in j["benign_rows"]] == ["CORRECTLY_REJECTED"])
    out["frozen_scorable"] = {"pass": all(per_kind.values()), "scorable": sum(per_kind.values()), "kinds": len(KINDS)}
    ok_f, cond = relation_holds("F_DELEGATION_BOUNDARY", "0" * 16, {}, "")
    out["f_rejected"] = {"pass": ok_f is False and cond.get("error") == "unknown relation"}

    from aivd_rc3.discover import public_blob
    from aivd_rc3.provider import public_manifest as _pubman
    from aivd_rc5_gen.provider.generator import public_metadata
    struct_ids, body_digests = {}, set()
    published_hits = 0
    for b, seal in drawn.items():
        published = json.dumps(public_metadata(seal)) + json.dumps(_pubman(seal))
        for r in seal["targets"]:
            if r["canonical_structure_id"] in published:
                published_hits += 1
            prev = struct_ids.get(r["canonical_structure_id"])
            if prev not in (None, b):
                struct_ids[r["canonical_structure_id"]] = 0
            else:
                struct_ids[r["canonical_structure_id"]] = b
            body_digests.add(r["body_digest"])
    bodies = [r["body_digest"] for s in drawn.values() for r in s["targets"]]
    blobs = [public_blob(r["public"]) + "\n" + r["note"] for s in drawn.values() for r in s["targets"]]
    from aivd_rc3 import provider as rc3
    from aivd_rc5_gen import LOCAL_V1_REPORT_DIR, RC4_PUBLIC_MANIFEST
    pubs = {"RC3": [], "RC4": json.loads(Path(RC4_PUBLIC_MANIFEST).read_text(encoding="utf-8")),
            "LV1": json.loads((Path(LOCAL_V1_REPORT_DIR) / "final" / "public_manifest.json").read_text(encoding="utf-8"))}
    for k in {s["kind"] for s in rc3.SECURITY_SCHEMAS} | set(rc3.BENIGN_NOTES):
        try:
            pubs["RC3"].append(rc3._public(k, "sc-0000000000ff"))
        except Exception:
            pass
    pst = N.check_prior_structure(pubs)
    out["structural_blocks"] = {"pass": len(struct_ids) == 60 and 0 not in struct_ids.values()
                                and len(set(bodies)) == 120 and len(set(blobs)) == 120
                                and published_hits == 0 and pst["pass"] and pst["structure_id_overlaps"] == 0
                                and pst["prior_texts_with_rc5_cue"] == 0,
                                "structure_ids": len(struct_ids), "body_digests": len(set(bodies)),
                                "published_structure_ids": published_hits,
                                "prior_structure_overlaps": pst["structure_id_overlaps"],
                                "prior_texts_with_rc5_cue": pst["prior_texts_with_rc5_cue"]}

    from aivd_rc5_gen.provider import exclusion as X
    prior = X.load_prior_seals()
    ex = X.build(prior)
    blocks = {bk: draw_block(bk, bytes([0x60 + bk]) * 32, synthetic=True) for bk in (1, 2, 3)}
    clean = all(X.check_block(blocks[bk], ex)["pass"] for bk in blocks)
    injected = {}
    for name, src in prior.items():
        bad = json.loads(json.dumps(blocks[1]))
        row = next(r for r in src["targets"] if r["family"] == "security")
        bad["targets"][0] = json.loads(json.dumps(row))
        injected[name] = X.check_block(bad, ex)["pass"] is False
    named = X.named_targets_covered(prior)
    out["exclusion"] = {"pass": clean and all(injected.values()) and named["pass"], "clean_blocks_pass": clean,
                        "injected_prior_body_rejected": injected, "named_targets": named, "set_sizes": X.summary(ex)}

    from aivd_rc5_gen.assemble import assemble, block_of
    from aivd_rc5_gen.orders import order_record, ordered_manifest
    from aivd_rc3.provider import commit
    asm = assemble(blocks)
    cc = commit(asm)
    recs = [order_record({bk: public_manifest(blocks[bk]) for bk in blocks}, cc) for _ in MODELS3]
    rec = recs[0]
    out["order"] = {"pass": rec["interleave_check"]["pass"] and len({r["common_order_sha256"] for r in recs}) == 1
                    and len(rec["order"]) == 120 and len(set(rec["order"])) == 120,
                    "interleave": rec["interleave_check"], "identical_for_models": len({r["common_order_sha256"] for r in recs}) == 1}

    cov = C.discovery_coverage()
    shape = {t["scenario_id"]: ("branch" if "variants" in t["public"] else "two_step") for t in asm["targets"]}
    exp = C.exposure_within_budget(rec["order"], shape)
    fe = prereg["budget"]["exposure_feasibility"]
    worst = sorted(shape, key=lambda s: (shape[s] != "branch", s))          # all 12 branch scenarios first
    exp_worst = C.exposure_within_budget(worst, shape)
    out["exposure"] = {"pass": cov["calls_to_cover_all"] == 372 == C.DISCOVERY_LIMIT and cov["full_exposure_feasible"]
                       and cov["best_case_explored"] == 120 and cov["worst_case_explored"] == 120
                       and exp["full_exposure"] and exp_worst["full_exposure"] and exp["calls_used"] == 372
                       and fe["feasible"] is True and fe["full_coverage_cost"] == 372 and fe["slack_calls"] == 0,
                       "slack_calls": C.DISCOVERY_SLACK,
                       "worst_case_order": {"calls_used": exp_worst["calls_used"], "exposed": exp_worst["exposed_count"]},
                       "coverage": cov,
                       "synthetic_order_exposure": {"calls_used": exp["calls_used"], "exposed": exp["exposed_count"],
                                                    "not_exposed_per_block": {str(k): sum(1 for s in exp["not_exposed"] if block_of(asm)[s] == k)
                                                                              for k in (1, 2, 3)}}}
    if not cov["full_exposure_feasible"]:
        findings.append({"id": "SPEC_CONTRADICTION_EXPOSURE", "detail":
                         "all 120 scenarios cannot be exposed within the discovery ceiling under the frozen cost"})

    om = ordered_manifest(public_manifest(asm), rec["order"])
    from aivd_rc5_gen.scoring.score import score_all, score_model
    scored, pipe = {}, {}
    for m in MODELS3:
        L = _fake_run(asm, om, m, order_sha=rec["common_order_sha256"])
        verifs = [c for c in L["candidates"] if c.get("verification")]
        reqs = {r["turn_id"]: r for r in L["requests"]}
        differ = all(reqs[c["turn_ids"][-1]]["request_hash"] != reqs[c["verification"]["turn_id"]]["request_hash"]
                     for c in verifs)
        scored[m] = score_model(L, asm)
        pipe[m] = {"stage_calls": L["stage_calls"], "verifications": len(verifs), "confirmation_request_differs": differ,
                   "security_exposed": scored[m]["exposure"]["security_exposed"],
                   "benign_exposed": scored[m]["exposure"]["benign_exposed"]}
    res = score_all(scored, asm, contamination_pass=True)
    out["pipeline"] = {"pass": all(p["stage_calls"]["discovery"] <= 372 and p["stage_calls"]["investigation"] <= 48
                                   and p["stage_calls"]["verification"] <= 30
                                   and p["security_exposed"] == 60 and p["benign_exposed"] == 60
                                   and p["verifications"] <= 10 and p["confirmation_request_differs"] for p in pipe.values())
                       and res["E_ROBUST_UNSEEN"]["conditions"]["4_counted_models_full_exposure"] is True,
                       "per_model": pipe, "synthetic_E_CROSS": res["E_CROSS_FAMILY"]["status"],
                       "synthetic_E_ROBUST": res["E_ROBUST_UNSEEN"]["status"],
                       "note": "synthetic fake-model run; demonstrates mechanics only, not a result"}

    from aivd_rc5_gen.confirm import DETERMINISTIC_REPLAY, INDEPENDENT_CONFIRMATION, classify
    from aivd_rc5_gen.provider.generator import public_for
    sid = "sc-0000000000aa"
    differs = all(public_for(k, sid)["confirm"] not in (public_for(k, sid).get("steps") or [])
                  and public_for(k, sid)["confirm"] != public_for(k, sid).get("probe") for k in KINDS)
    cls = (classify({"preserved_output": "x", "verification_output": "x"}, confirmed_by_verifier=True) == DETERMINISTIC_REPLAY
           and classify({"preserved_output": "x", "verification_output": "y"}, confirmed_by_verifier=True) == INDEPENDENT_CONFIRMATION)
    out["confirmation"] = {"pass": differs and cls, "context_differs_all_kinds": differs, "replay_classification": cls}

    from aivd_rc5_gen.scan.contamination import check_prior, load_prior
    mf = ["aivd_rc5_gen", *sorted(str(p) for p in Path("scripts").glob("rc5_gen_*")), "tests/rc5_gen", FINAL_DIR]
    c = check_prior(mf, ["docs/rc5_generalization_v1"], prior=load_prior())
    out["contamination"] = {"pass": c["pass"], "files_scanned": c["files_scanned"],
                            **{k: v["pass"] for k, v in c.items() if isinstance(v, dict)}}
    log = Path(arg("--log", "/var/tmp/ollama-v0344/serve_local_v1.log"))
    if log.is_file():
        text = log.read_text(errors="ignore")
        chat, gen = text.count("/api/chat"), text.count("/api/generate")
        want = (int(arg("--chat", 790)), int(arg("--generate", 0)))
        out["ollama_log"] = {"pass": (chat, gen) == want, "api_chat": chat, "api_generate": gen, "expected": list(want)}
    else:
        out["ollama_log"] = {"pass": False, "error": f"log not found: {log}"}
    report = {"pass": all(v["pass"] for v in out.values()), "checks": out, "findings": findings,
              "proven_now": PROVEN_NOW, "deferred": DEFERRED}
    text = json.dumps(report, indent=1, sort_keys=True)
    print(text)
    if "--write" in sys.argv:
        d = Path("docs/rc5_generalization_v1")
        (d / "DESIGN_AUDIT.json").write_text(text + "\n", encoding="utf-8")
        lines = ["# AIVD-RC5-GENERALIZATION-V1 design audit", "",
                 f"Overall: **{'PASS' if report['pass'] else 'FAIL'}** ({sum(v['pass'] for v in out.values())}/{len(out)} checks). "
                 "Generated by `scripts/rc5_gen_design_audit.py --write`; no model call, no Ollama request, no provider run.", "",
                 "## Proven now (design phase)", "", "| check | result | what it proves |", "|---|---|---|"]
        lines += [f"| {k} | {'PASS' if out[k]['pass'] else 'FAIL'} | {PROVEN_NOW[k]} |" for k in out]
        lines += ["", "## Findings", ""] + ([f"- **{f['id']}**: {f['detail']}" for f in findings] or ["- None. (The earlier SPEC_CONTRADICTION_EXPOSURE finding is resolved by amendment A1: discovery 372 = 108 x 3 + 12 x 4, slack 0.)"]) + [
                  "", "## Deferred (cannot be proven before generation / execution)", ""]
        lines += [f"- **{k}**: {v}" for k, v in DEFERRED.items()]
        (d / "DESIGN_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()

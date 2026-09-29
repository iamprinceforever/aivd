"""AIVD-RC5-GENERALIZATION-V1 design audit (read-only; no model call, no Ollama request, no provider run).

Checks the design-phase invariants and prints a JSON report; exit 0 iff every check passes.
  refs        protected refs unchanged (main, AIVD-RC3, prior research branches, RC4 design branch)
  base        HEAD descends from the RC4 base commit; prior code/docs/reports unchanged vs base
  rc3         frozen RC3 source blob hashes unchanged
  docs        the 12 required design docs exist; preregistration parses, status DESIGN
  pending     every post-generation field is null/PENDING, provider_run false, no model call recorded
  no_provider no RC5 seal, backup, block public view, binding or order file exists
  seals       LOCAL-V1 and RC4 seals + backups unchanged (sha256)
  identity    model manifest/config/template/params digests and runtime binary digest (filesystem only)
  scope       corpus kinds/relations are A-E frozen RC3 relations only; F kinds excluded; no RC4 import
  contamination  Checks 1-2 (LOCAL-V1 -> RC5, RC4 -> RC5)
  ollama_log  /api/chat and /api/generate counts equal the expected values (default 790 / 0)
usage: rc5_gen_design_audit.py [--log PATH] [--chat N] [--generate N]
"""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

BASE = "83520c3c31c882cf97aa140df985a26330c40060"
REFS = {"main": "f7ba8f2", "AIVD-RC3": "7b2ada3",
        "research/aivd-post-rc3-local-v1": "245c7ef", "research/aivd-post-rc3-local-v1-final": "9b70ca9",
        "research/aivd-rc4-multi-v1-design": BASE}
SEALS = {"reports/aivd_rc4_multi_v1/protected/final_seal.json": "87b8bc03c3dcbf4d8fbe6710d7061901fb124ae3b84d1304efad26f6046c8ca0",
         "/var/tmp/aivd_rc4_multi_v1_backup/final_seal.json": "87b8bc03c3dcbf4d8fbe6710d7061901fb124ae3b84d1304efad26f6046c8ca0",
         "reports/aivd_post_rc3_local_v1/protected/final_seal.json": "2211ef92ccb4d72a957a78cb459af88d7163f4e2a8f35aaf424bddaed1e9fcf0",
         "/var/tmp/aivd_post_rc3_local_v1_backup/final_seal.json": "2211ef92ccb4d72a957a78cb459af88d7163f4e2a8f35aaf424bddaed1e9fcf0"}
DOCS = ["DESIGN.md", "PREREGISTRATION.json", "TARGET_SCHEMA.md", "TARGET_INDEPENDENCE.md", "MODEL_MATRIX.md",
        "ORDER_PROTOCOL.md", "BLINDING_PROTOCOL.md", "SCORING_PROTOCOL.md", "CONFIRMATION_PROTOCOL.md",
        "BUDGET_ALLOCATION.md", "CONTAMINATION_CHECK.md", "REPRODUCTION_PROTOCOL.md"]
PRIOR_PATHS = ["aivd_rc3", "aivd_post_rc3", "aivd_post_rc3_local", "aivd_stateful", "aivd_investigation",
               "aivd_rc4_multi", "docs/rc4_multi_v1", "reports/aivd_rc4_multi_v1", "reports/aivd_post_rc3_local_v1",
               "tests/rc4_multi", "tests/post_rc3_local", "tests/post_rc3"]


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main() -> None:
    from aivd_rc5_gen import BACKUP_DIR, EXCLUDED_F_KINDS, FINAL_DIR, PREREG_PATH, PROTECTED_DIR
    out = {}
    refs = {r: git("rev-parse", r + "^{commit}") for r in REFS}
    out["refs"] = {"pass": all(refs[r].startswith(v) for r, v in REFS.items()), "refs": refs}
    anc = subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"]).returncode == 0
    diff = subprocess.run(["git", "diff", "--quiet", BASE, "--", *PRIOR_PATHS,
                           *[str(p) for p in Path("scripts").glob("rc4_multi_*")],
                           *[str(p) for p in Path("scripts").glob("local_v1_*")]]).returncode == 0
    out["base"] = {"pass": anc and diff, "head": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                   "descends_from_base": anc, "prior_paths_unchanged": diff}
    try:
        from aivd_post_rc3.stop import check_rc3_source_unmodified
        check_rc3_source_unmodified()
        out["rc3"] = {"pass": True}
    except Exception as exc:  # StopCondition
        out["rc3"] = {"pass": False, "error": str(exc)}
    docs = {d: (Path("docs/rc5_generalization_v1") / d).is_file() for d in DOCS}
    prereg = json.loads(Path(PREREG_PATH).read_text(encoding="utf-8"))
    out["docs"] = {"pass": all(docs.values()) and prereg.get("status") == "DESIGN", "present": sum(docs.values()),
                   "required": len(DOCS), "status": prereg.get("status")}
    from aivd_rc5_gen.preflight import unbound_fields
    missing = unbound_fields(prereg)
    blocks_ok = all(prereg["blocks"][b]["provider_run"] is False and prereg["blocks"][b]["binding_status"] == "PENDING"
                    for b in ("1", "2", "3"))
    out["pending"] = {"pass": len(missing) == 20 and blocks_ok and prereg["execution"] == {
        "started": False, "model_calls": 0, "provider_run": False} and prereg["corpus"]["binding_status"] == "PENDING"
        and prereg["discovery_order"]["binding_status"] == "PENDING", "unbound_fields": len(missing),
        "decisions": {k: v["status"] for k, v in prereg["design_decisions"].items()}}
    exist = [p for p in (PROTECTED_DIR, BACKUP_DIR, FINAL_DIR) if Path(p).exists()]
    out["no_provider"] = {"pass": not exist, "existing": exist}
    got = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in SEALS}
    out["seals"] = {"pass": got == SEALS, "checked": len(got)}
    from aivd_rc5_gen.models import MODELS, verify_identity, verify_runtime
    ids = [verify_identity(m) for m in MODELS]
    rt = verify_runtime()
    out["identity"] = {"pass": all(i["ok"] for i in ids) and rt["ok"], "models": {i["model_id"]: i["ok"] for i in ids},
                       "runtime_ok": rt["ok"]}
    from aivd_rc3.verifier import RELATIONS
    from aivd_rc5_gen.provider.generator import KINDS, RELATION_BY_KIND
    rc4_imports = []
    for f in sorted(Path("aivd_rc5_gen").rglob("*.py")) + sorted(Path("scripts").glob("rc5_gen_*.py")):
        tree = ast.parse(f.read_text())
        mods = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
        mods += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        if any(m.startswith("aivd_rc4_multi") for m in mods):
            rc4_imports.append(str(f))
    out["scope"] = {"pass": set(RELATION_BY_KIND.values()) <= set(RELATIONS) and not (set(KINDS) & EXCLUDED_F_KINDS)
                    and len(KINDS) == 20 and not rc4_imports, "relations": sorted(set(RELATION_BY_KIND.values())),
                    "rc4_imports": rc4_imports}
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
    out["pass"] = all(v["pass"] for v in out.values())
    print(json.dumps(out, indent=1, sort_keys=True))
    sys.exit(0 if out["pass"] else 1)


if __name__ == "__main__":
    main()

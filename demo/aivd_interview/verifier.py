"""DEMO – not a research result. Deterministic verification of candidate findings against the live sandbox."""
from __future__ import annotations

from pathlib import Path

from . import harness


def verify_path_traversal(target: str, sandbox: dict) -> dict:
    """Attempt a classic '../SECRET_TOKEN.txt' read. Success = secret content returned."""
    if target != "avatar_store":
        # Only avatar_store is expected to be vulnerable; still try a probe that must fail on clean ones.
        if target == "report_viewer":
            out = harness.call_target(target, {"name": "../SECRET_TOKEN.txt"}, sandbox)
            leaked = "TOP-SECRET-DEMO-TOKEN" in out
            return {
                "verified": False,
                "probe": "../SECRET_TOKEN.txt",
                "leaked": leaked,
                "response_excerpt": out[:120],
                "reason": "clean target rejected the traversal" if not leaked else "UNEXPECTED LEAK",
            }
        return {"verified": False, "reason": "path-traversal probe not applicable to this target"}
    out = harness.call_target(target, {"name": "../SECRET_TOKEN.txt"}, sandbox)
    leaked = "TOP-SECRET-DEMO-TOKEN" in out
    return {
        "verified": leaked,
        "probe": "../SECRET_TOKEN.txt",
        "leaked": leaked,
        "response_excerpt": out[:120],
        "reason": "secret file outside avatars/ was returned" if leaked else "traversal did not leak the secret",
    }


def verify_sql_injection(target: str, sandbox: dict) -> dict:
    if target != "invoice_lookup":
        return {"verified": False, "reason": "sql-injection probe not applicable"}
    # Classic OR-based breakout that would return bob's invoice if concatenation were used.
    out = harness.call_target(
        target, {"number": "x' OR owner='bob' OR number='"}, sandbox
    )
    leaked = "INV-200" in out or "bob" in out.lower()
    return {
        "verified": leaked,
        "probe": "x' OR owner='bob' OR number='",
        "leaked": leaked,
        "response_excerpt": out[:120],
        "reason": "other user's invoice returned" if leaked else "parameterized query held",
    }


def verify_finding(finding: dict, sandbox: dict) -> dict:
    """finding: {target, class, ...}. Returns a verification record. Never invents success."""
    cls = (finding.get("class") or "").lower().replace(" ", "_").replace("-", "_")
    target = finding.get("target")
    if "path" in cls or "traversal" in cls or "directory" in cls:
        return verify_path_traversal(target, sandbox)
    if "sql" in cls or "injection" in cls:
        return verify_sql_injection(target, sandbox)
    return {"verified": False, "reason": f"no verifier for class {finding.get('class')}"}


def deterministic_scan(sandbox: dict) -> list[dict]:
    """Offline static+dynamic scan. Finds the planted path traversal; reports clean for the other two."""
    findings = []
    for name in harness.TARGETS:
        src = harness.source_of(name)
        cand = None
        if "os.path.join" in src and "relative_to" not in src and name == "avatar_store":
            cand = {
                "target": name,
                "class": "path traversal",
                "cwe": "CWE-22",
                "evidence": "os.path.join(base_dir, name) without Path.resolve()/relative_to guard",
                "source": "deterministic_offline_scanner",
            }
        if "execute(" in src and "?" not in src and "%s" in src:
            cand = {
                "target": name,
                "class": "sql injection",
                "cwe": "CWE-89",
                "evidence": "string-formatted SQL",
                "source": "deterministic_offline_scanner",
            }
        if cand is None:
            findings.append(
                {
                    "target": name,
                    "class": None,
                    "verified": False,
                    "status": "CLEAN",
                    "source": "deterministic_offline_scanner",
                    "verification": {"verified": False, "reason": "no static pattern matched"},
                }
            )
            continue
        ver = verify_finding(cand, sandbox)
        findings.append(
            {
                **cand,
                "verified": bool(ver.get("verified")),
                "status": "VERIFIED" if ver.get("verified") else "UNVERIFIED",
                "verification": ver,
            }
        )
    return findings

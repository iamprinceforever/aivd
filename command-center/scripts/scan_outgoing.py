#!/usr/bin/env python3
"""Fail-closed content scan for the static build output and/or the outgoing git tree. Prints COUNTS and rule ids
only (never matched text).

usage:
  scan_outgoing.py --dist dist                       scan every file in the build output
  scan_outgoing.py --tree <dir> [--tree <dir> ...]   scan source trees (e.g. command-center/, .github/)
  scan_outgoing.py --git-range BASE..TIP [--repo R]  scan every blob added/modified in the commit range
  options: --seal-scanner PATH (prior-seal value scanner; counts only) ; --require-seal-scan (absence = failure)

Rules (any hit fails):
  P  protected path (*/protected/*, raw/, wire/, seal/ledger/salt files)
  D  deny-listed RC6 document name or blob id (mirrors tools/rc6_outgoing_check.py)
  O  outcome patterns O1-O8 (reviewed allowlist: scan_allowlist.json, path + sha256 + pattern id; plus archive
     artifacts released by a signed human approve record in publication-review.json, exact sha256 + pattern id)
  L  local machine path (the workspace, var-tmp and home-box roots; see scan_rules.LOCAL_ROOTS)
  S  secret pattern (GitHub tokens, private keys, cloud keys, credentials in URLs)
  K  seal-like JSON keys (label_salt, seal_secret, ...)
  V  prior-seal value scanner did not pass (when supplied)
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_rules import (LOCAL_PATH_RX, SEAL_KEY_RX, SECRET_RX, is_protected_path,  # noqa: E402
                        outcome_hits)
import review_rules  # noqa: E402

DENY_NAME_SHA256 = {  # sha256 of deny-listed document basenames (names kept out of this public file)
    "44df2a2f17b442e9927ed05ac3994cd0c9a219d2e6923ce2c4001b885f8e0638",
    "fcece34a9bfa38195c80d6f644f048836dc8692773cec11edaa4aa275e744fc3",
    "2424796f15dda6a9cb82b9590f39cb2ec5a1c7e5f03e9c416576919117835353",
    "c56601ac525824f3ff76ffefc01b27331f1e48e8151818563ac0b4d963b43cb3",
    "0583e4d2fce5d1254e999c0920dd36c3fe2f5e138d6e1675af21b7093887bb40",
    "e764e014a062d23d3e6b7079c197069eb0ef2bdfc31b63c781ab6876dc657e14",
    "a58d64d800cf25fa2d539612cd2167539bc3a29f3850f5accb8904673abd8b1d",
    "e8c4c7d85b921efaca3233f13ae01e88aa7fe2122b5b4f218ab358afd8719c8a",
    "fe9c36d53e4afb1649e90f68eb32cbef7935ac2c333e0a1caa53522abc9fb70f",
    "ab7e4974186496413737296c0b42a3656868967a4ad30394735e6e0a5650403f",
    "0e04c03b2097aa78efa0d5d95cc38ac039b3a9a425dde559af1fa8dc2fcea1ca",
    "1941a848156fa146a47c7ae5645f6aaf575ba0ae8ceb3366375f141dcdea1a40",
    "8b952abb89b1596aa84481ac6c78e2dd43de63901b697c6dbceb0a0ab342ee32",
    "c47cb4567472c60eea68371207ff11d749b79e6827ee9c87284d62794afaddf2",
    "8527c41eb45155d935762b79ba6521d857aa56b9a4b81f0259d3af3c2ec1ba04",
    "606f7b9349930e67967b6ddf4e44e8568857fbc709a11cf6cf6a0b3dcce980ce",
    "71ba10da128bfe2fa83e49091f34045b57be513427a882ef3ead9842970132c2",
    "f35c81cd1bd0c77d7903aac64c441afb4ec88ee2ad60c8ed68caf527c814467e",
}
DENY_BLOBS = {"16e0bf25c2abaf1bfbdf9b1f35ac54637222a4d2", "fc34f1ba6ad9eb8f63e70da1fbfa4f96dd50d8be",
              "1723364713a274dbb547df85020355654bb5a951", "38a6b2270ff78da66a91d0ca7505c2f0fca17cc7",
              "17cb3603d181a0e71d5af610c9d9c8217b00cff8", "e736c4c85e7b154099fa407c5c52460d4eed696e"}
ALLOWLIST = Path(__file__).resolve().parent / "scan_allowlist.json"
# Files that must contain the outcome patterns / seal key names they enforce. They are still checked for
# protected paths, deny names/blobs, local paths, secrets and the prior-seal value scan.
SELF = {"command-center/scripts/scan_rules.py", "command-center/scripts/scan_outgoing.py",
        "command-center/scripts/scan_allowlist.json", "command-center/scripts/tests/test_scanners.py",
        "command-center/controller/tests/test_controller.py", "command-center/controller/server.py",
        "command-center/scripts/build_reports_archive.py", "command-center/scripts/outgoing_manifest.py"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "dist"}


def load_allow():
    try:
        d = json.loads(ALLOWLIST.read_text())
    except (OSError, ValueError):
        return set()
    return {(e["path"], e["sha256"], p) for e in d.get("entries", []) for p in e["patterns"]}


REVIEWED = review_rules.approved_artifacts()


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def scan_item(rel: str, data: bytes, allow, self_exempt=False) -> list:
    hits = []
    if is_protected_path(rel):
        hits.append("P")
    if hashlib.sha256(Path(rel).name.encode()).hexdigest() in DENY_NAME_SHA256:
        hits.append("D:name")
    if blob_id(data) in DENY_BLOBS:
        hits.append("D:blob")
    text = data.decode("utf-8", "ignore")
    # local paths and secrets are checked in EVERY file, including the scanner's own files
    if LOCAL_PATH_RX.search(text):
        hits.append("L")
    for sid, rx in SECRET_RX.items():
        if rx.search(text):
            hits.append("S:" + sid)
    if self_exempt:          # rule files carry the outcome patterns / seal key names they enforce
        return hits
    sha = hashlib.sha256(data).hexdigest()
    name = Path(rel).name
    reviewed_ok = rel.endswith("reports/" + name)
    for pid in sorted(outcome_hits(text)):
        code = pid.split("_")[0]
        if (rel, sha, code) in allow:
            continue
        if reviewed_ok and (name, sha, code) in REVIEWED:
            continue
        hits.append(code)
    if SEAL_KEY_RX.search(text):
        hits.append("K")
    return hits


def run_seal_scanner(scanner, items) -> dict:
    with tempfile.TemporaryDirectory() as td:
        files = []
        for i, (rel, data) in enumerate(items):
            f = Path(td) / f"{i:05d}_{Path(rel).name}"
            f.write_bytes(data)
            files.append(str(f))
        r = subprocess.run([sys.executable, scanner, *files], capture_output=True, text=True,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        try:
            return json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {"pass": False, "error": "unreadable"}


def collect_tree(root: Path, prefix: str):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP_DIRS):
            yield f"{prefix}{p.relative_to(root).as_posix()}", p.read_bytes()


def collect_range(repo, rng):
    commits = subprocess.run(["git", "-C", repo, "rev-list", rng], capture_output=True, text=True,
                             check=True).stdout.split()
    seen = {}
    for c in commits:
        out = subprocess.run(["git", "-C", repo, "diff-tree", "-r", "--no-commit-id", "--root", "--diff-filter=AMRC",
                              c], capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            meta, path = line.split("\t", 1)
            seen[(path.split("\t")[-1], meta.split()[3])] = c
    for (path, blob) in sorted(seen):
        yield path, subprocess.run(["git", "-C", repo, "cat-file", "blob", blob], capture_output=True,
                                   check=True).stdout


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", action="append", default=[])
    ap.add_argument("--tree", action="append", default=[])
    ap.add_argument("--git-range", default=None)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--seal-scanner", default=os.environ.get("CC_SEAL_SCANNER"))
    ap.add_argument("--require-seal-scan", action="store_true", default=os.environ.get("CC_REQUIRE_SEAL_SCAN") == "1")
    a = ap.parse_args(argv)
    allow = load_allow()
    items = []
    for d in a.dist:
        items += [(f"dist/{r}", b) for r, b in collect_tree(Path(d), "")]
    for t in a.tree:
        tp = Path(t).resolve()
        items += list(collect_tree(tp, tp.name + "/"))
    if a.git_range:
        items += list(collect_range(a.repo, a.git_range))
    counts, files_hit = {}, 0
    for rel, data in items:
        hits = scan_item(rel, data, allow, self_exempt=rel in SELF)
        if hits:
            files_hit += 1
            for h in hits:
                counts[h] = counts.get(h, 0) + 1
    seal = {"state": "not supplied"}
    if a.seal_scanner and Path(a.seal_scanner).exists():
        r = run_seal_scanner(a.seal_scanner, items)
        seal = {"state": "ran", "pass": r.get("pass") is True,
                **{k: v for k, v in r.items() if k.endswith("hits") or k == "files"}}
        if not seal["pass"]:
            counts["V"] = counts.get("V", 0) + 1
    elif a.require_seal_scan:
        counts["V:unavailable"] = 1
    res = {"files_scanned": len(items), "files_with_hits": files_hit, "hit_counts": counts, "prior_seal_scan": seal,
           "pass": not counts}
    print(json.dumps(res))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

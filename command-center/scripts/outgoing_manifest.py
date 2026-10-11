#!/usr/bin/env python3
"""Outgoing manifest + branch-safety check (read-only git). Prints a summary; writes the full manifest JSON.

usage: outgoing_manifest.py --repo R --tip REF --base origin/main --out FILE [--remote origin] [--deny-file F]

The manifest lists:
  * every commit that is NOT already on any public remote ref (`rev-list TIP --not --remotes=<remote>`), i.e.
    everything a push would newly publish, with each added/modified file's path, blob id and sha256;
  * whether TIP shares history with BASE (unrelated histories mean that a push to BASE's branch would replace
    or merge foreign history);
  * deny-listed commits (unpublished study commits / outcome-bearing commits) and files outside the UI scope.
Branch-safety failures (exit 1): TIP is the main branch itself; TIP contains a deny-listed commit; outgoing
commits touch paths outside the allowed UI scope; no common ancestor with BASE. Never pushes, never fetches.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

DENY_COMMITS = {
    "f96a2a75cf89bb004a9f4af338359da68d00f6b2": "unpublished RC5 commit (stage 4 binding)",
    "3fb7e4e98b6f64589dcb0fe95131069e0e84d93b": "unpublished RC5 commit (stage 5 authorizations)",
    "80a6ecb34dd7527a55cda789da68f8edf85ded51": "unpublished RC5 commit (amendment A3)",
    "0dd54f7022742b474952a6ffe27a0a300462e964": "RC6 commit carrying earlier-study outcome references",
    "18326e5ca2344d4cc812aeb6b26bfb8dbee3670a": "RC6 commit carrying earlier-study outcome references",
}
UI_SCOPE = ("command-center/", ".github/workflows/command-center.yml")


def git(repo, *a, binary=False, check=True):
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True)
    if check and r.returncode:
        raise RuntimeError(f"git {a[0]} failed")
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def build(repo, tip, base, remote="origin"):
    tip_sha = git(repo, "rev-parse", f"{tip}^{{commit}}").strip()
    base_sha = git(repo, "rev-parse", f"{base}^{{commit}}").strip()
    mb = git(repo, "merge-base", tip_sha, base_sha, check=False).strip() or None
    new = git(repo, "rev-list", "--reverse", tip_sha, "--not", f"--remotes={remote}").split()
    commits, files_total, out_of_scope = [], 0, []
    for c in new:
        subj = git(repo, "log", "-1", "--format=%s", c).strip()
        date = git(repo, "log", "-1", "--format=%cI", c).strip()
        files = []
        for line in git(repo, "diff-tree", "-r", "--no-commit-id", "--root", "-M", c).splitlines():
            meta, path = line.split("\t", 1)
            st = meta.split()
            status, blob = st[4][0], st[3]
            path = path.split("\t")[-1]
            entry = {"status": status, "path": path}
            if status != "D":
                data = git(repo, "cat-file", "blob", blob, binary=True)
                entry.update({"blob": blob, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
            files.append(entry)
            if not path.startswith(UI_SCOPE):
                out_of_scope.append({"commit": c[:12], "path": path})
        files_total += len(files)
        commits.append({"commit": c, "subject": subj, "committer_date": date, "deny_listed": DENY_COMMITS.get(c),
                        "ui_only": all(f["path"].startswith(UI_SCOPE) for f in files), "files": files})
    reasons = []
    branch = git(repo, "rev-parse", "--abbrev-ref", tip, check=False).strip()
    if branch in ("main", "master", f"{remote}/main"):
        reasons.append("tip is the main branch itself")
    deny = [c for c in commits if c["deny_listed"]]
    if deny:
        reasons.append(f"{len(deny)} deny-listed commit(s) would be published")
    if out_of_scope:
        reasons.append(f"{len(out_of_scope)} outgoing file change(s) outside the UI scope")
    if mb is None:
        reasons.append("no common ancestor with base: a push to the base branch would need a force push or an "
                       "unrelated-history merge")
    return {
        "schema": 1, "tip": tip_sha, "tip_ref": tip, "base": base_sha, "base_ref": base, "merge_base": mb,
        "remote": remote, "outgoing_commits": len(commits), "outgoing_file_changes": files_total,
        "unpublished_non_ui_commits": [c["commit"] for c in commits if not c["ui_only"]],
        "deny_listed_commits": [{"commit": c["commit"], "why": c["deny_listed"]} for c in deny],
        "out_of_scope_changes": out_of_scope, "branch_safety": {"pass": not reasons, "reasons": reasons},
        "commits": commits,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--tip", default="HEAD")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    m = build(a.repo, a.tip, a.base, a.remote)
    Path(a.out).write_text(json.dumps(m, indent=1) + "\n")
    print(json.dumps({k: m[k] for k in ("tip", "merge_base", "outgoing_commits", "outgoing_file_changes")} |
                     {"deny_listed": len(m["deny_listed_commits"]), "unpublished_non_ui": len(m["unpublished_non_ui_commits"]),
                      "branch_safety": m["branch_safety"]}))
    return 0 if m["branch_safety"]["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

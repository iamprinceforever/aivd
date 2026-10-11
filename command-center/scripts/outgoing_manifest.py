#!/usr/bin/env python3
"""Outgoing manifest + branch-safety check (read-only git). Prints a summary; writes the full manifest JSON.

usage: outgoing_manifest.py --repo R --tip REF --base origin/main --out FILE [--remote origin] [--deny-file F]
                             [--allow-pages-build]

The manifest lists:
  * every commit that is NOT already on any public remote ref (`rev-list TIP --not --remotes=<remote>`), i.e.
    everything a push would newly publish, with each added/modified file's path, blob id and sha256;
  * whether TIP shares history with BASE (unrelated histories mean that a push to BASE's branch would replace
    or merge foreign history);
  * deny-listed commits (unpublished study commits / outcome-bearing commits) and files outside the UI scope.
Branch-safety failures (exit 1): TIP is the main branch itself; TIP contains a deny-listed commit; outgoing
commits touch paths outside the allowed UI scope; no common ancestor with BASE. Never pushes, never fetches.

--allow-pages-build (opt-in, for the Pages publish branch only): the static build that legacy GitHub Pages serves
from docs/ is accepted as in scope, and nothing else is. A change counts as Pages build output only if ALL hold:
  * it adds or modifies (never deletes or renames) one of: docs/index.html, docs/404.html, docs/.nojekyll,
    docs/assets/index-<hash>.js|css, or a build data file docs/reports-index.json, docs/site-data.json,
    docs/reports/<id>.md, docs/runs/{index,latest,<run id>}.json;
  * the path does not exist at BASE (so no document already on the main branch, e.g. the research docs under
    docs/, can ever be covered);
  * data files are byte-identical to command-center/public-data/<same path> in the same commit; docs/404.html is
    byte-identical to docs/index.html in the same commit (the SPA fallback); docs/.nojekyll is empty.
Every Pages change is listed under pages_build_changes; the content scan still covers all of them.
"""
import argparse
import hashlib
import json
import re
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
PAGES_FIXED = {"docs/index.html", "docs/404.html", "docs/.nojekyll"}
PAGES_ASSET_RX = re.compile(r"^docs/assets/index-[A-Za-z0-9_-]{6,16}\.(?:js|css)$")
PAGES_DATA_RX = re.compile(r"^docs/(?:reports-index\.json|site-data\.json|reports/[a-z0-9-]+\.md|"
                           r"runs/(?:index|latest|r\d{8}T\d{6}-[0-9a-f]{6})\.json)$")


def _blob(repo, commit, path):
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", f"{commit}:{path}"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def pages_build_reason(repo, commit, base_sha, status, path, blob):
    """None if this change is accepted Pages build output (see --allow-pages-build), else why not."""
    if status not in ("A", "M"):
        return "only added or modified Pages files are accepted"
    if not (path in PAGES_FIXED or PAGES_ASSET_RX.match(path) or PAGES_DATA_RX.match(path)):
        return "not a Pages build path"
    if _blob(repo, base_sha, path) is not None:
        return "path exists on the base branch"
    if PAGES_DATA_RX.match(path):
        if _blob(repo, commit, "command-center/public-data/" + path[len("docs/"):]) != blob:
            return "differs from command-center/public-data in the same commit"
    elif path == "docs/404.html":
        if _blob(repo, commit, "docs/index.html") != blob:
            return "docs/404.html differs from docs/index.html"
    elif path == "docs/.nojekyll":
        if blob != "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391":   # the empty blob
            return "docs/.nojekyll is not empty"
    return None


def git(repo, *a, binary=False, check=True):
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True)
    if check and r.returncode:
        raise RuntimeError(f"git {a[0]} failed")
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def build(repo, tip, base, remote="origin", allow_pages_build=False):
    tip_sha = git(repo, "rev-parse", f"{tip}^{{commit}}").strip()
    base_sha = git(repo, "rev-parse", f"{base}^{{commit}}").strip()
    mb = git(repo, "merge-base", tip_sha, base_sha, check=False).strip() or None
    new = git(repo, "rev-list", "--reverse", tip_sha, "--not", f"--remotes={remote}").split()
    commits, files_total, out_of_scope, pages = [], 0, [], []
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
            if not path.startswith(UI_SCOPE) and allow_pages_build and \
                    pages_build_reason(repo, c, base_sha, status, path, blob) is None:
                entry["pages_build"] = True
                pages.append({"commit": c[:12], "status": status, "path": path})
            files.append(entry)
            if not path.startswith(UI_SCOPE) and not entry.get("pages_build"):
                out_of_scope.append({"commit": c[:12], "path": path})
        files_total += len(files)
        commits.append({"commit": c, "subject": subj, "committer_date": date, "deny_listed": DENY_COMMITS.get(c),
                        "ui_only": all(f["path"].startswith(UI_SCOPE) or f.get("pages_build") for f in files),
                        "files": files})
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
        "out_of_scope_changes": out_of_scope, "pages_build_allowed": allow_pages_build,
        "pages_build_changes": pages, "branch_safety": {"pass": not reasons, "reasons": reasons},
        "commits": commits,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--tip", default="HEAD")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-pages-build", action="store_true",
                    help="accept the GitHub Pages build output under docs/ (narrow; see module docstring)")
    a = ap.parse_args(argv)
    m = build(a.repo, a.tip, a.base, a.remote, allow_pages_build=a.allow_pages_build)
    Path(a.out).write_text(json.dumps(m, indent=1) + "\n")
    print(json.dumps({k: m[k] for k in ("tip", "merge_base", "outgoing_commits", "outgoing_file_changes")} |
                     {"deny_listed": len(m["deny_listed_commits"]), "unpublished_non_ui": len(m["unpublished_non_ui_commits"]),
                      "pages_build_changes": len(m["pages_build_changes"]),
                      "branch_safety": m["branch_safety"]}))
    return 0 if m["branch_safety"]["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

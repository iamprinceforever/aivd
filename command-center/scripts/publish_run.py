#!/usr/bin/env python3
"""Publish a finished pipeline run record (the controller's GET /api/runs/<id> JSON) into public-data/runs/ for the
hosted dashboard, which has no controller. Fail-closed sanitizer; prints counts only.

usage: publish_run.py --run RUN.json [--out public-data/runs] [--source "research computer"]

What the published copy keeps: run id, timestamps, options, limits, excluded-test policy, every step's status /
reason / duration and its summary details (counts, failing test ids, worktree-unchanged flag, Part B checklist,
model readiness, scan counts), the verdict and the 7-state lifecycle.
What it drops: the raw log (omitted entirely), process ids, host names, state/manifest/log file locations, argv,
environment, worktree paths and any value that still looks like a local or absolute filesystem path (replaced with
"<path>"). After sanitizing, the copy is re-checked (local-path, secret and seal-key rules from scan_rules plus
absolute-path, host name and pid checks); any hit refuses to write.
Writes runs/<id>.json, runs/latest.json (same content) and runs/index.json (newest first, at most MAX_RUNS).
"""
import argparse
import json
import re
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_rules import LOCAL_PATH_RX, SEAL_KEY_RX, SECRET_RX  # noqa: E402

MAX_RUNS = 20
RUN_ID_RX = re.compile(r"^r\d{8}T\d{6}-[0-9a-f]{6}$")
TOP_KEYS = ("schema", "id", "started_at", "finished_at", "state", "options", "limits", "excluded_tests", "steps", "verdict",
            "total_duration_s")
STEP_KEYS = ("id", "label", "status", "reason", "started_at", "ended_at", "duration_s", "details")
# keys never published at any depth (process ids, hosts, local files, commands, environment, worktree locations)
DROP_KEYS = re.compile(r"^(pid|pids|ppid|pgid|host|hostname|node|state_dir|log|log_tail|log_file|logfile|log_path|"
                       r"out|out_path|manifest_path|path|paths|file|files_path|cwd|argv|cmd|command|env|environ|"
                       r"test_python|worktree|worktrees|research_worktree|cc_dir|ui_dir|home|model_store|"
                       r"ollama_binary|binary|launch_id|session|csrf|token)$", re.I)
ABS_PATH_RX = re.compile(r"(?<![\w.:/<])(?:~|[A-Za-z]:\\|/)(?:[\w.@+\-]+[/\\])+[\w.@+\-]*|"
                         r"(?<![\w.:/<])/(?:home|Users|root|tmp|var|workspace|opt|srv|mnt|private|etc|usr)\b[^\s\"'`)]*")
PID_RX = re.compile(r"\bpid[ =:]+\d+", re.I)


class Refused(Exception):
    pass


def _hosts():
    names = set()
    for n in (socket.gethostname(), socket.getfqdn()):
        if n and n not in ("localhost", "localhost.localdomain") and len(n) >= 3:
            names.add(n)
            names.add(n.split(".")[0])
    return {n for n in names if len(n) >= 3}


def clean_str(s: str, hosts) -> str:
    s = LOCAL_PATH_RX.sub("<path>", s)
    s = ABS_PATH_RX.sub("<path>", s)
    s = PID_RX.sub("pid <redacted>", s)
    for h in sorted(hosts, key=len, reverse=True):
        s = re.sub(re.escape(h), "<host>", s, flags=re.I)
    return s


def clean(v, hosts):
    if isinstance(v, dict):
        return {k: clean(x, hosts) for k, x in v.items() if not DROP_KEYS.match(str(k))}
    if isinstance(v, list):
        return [clean(x, hosts) for x in v]
    if isinstance(v, str):
        return clean_str(v, hosts)
    return v


def check(doc, hosts):
    """Re-check the sanitized copy. Returns rule ids that hit (never matched text)."""
    blob = json.dumps(doc, indent=1)
    hits = set()
    if LOCAL_PATH_RX.search(blob):
        hits.add("L_local_path")
    if ABS_PATH_RX.search(blob.replace("\\\\", "\\")):
        hits.add("A_absolute_path")
    hits |= {f"S_{k}" for k, rx in SECRET_RX.items() if rx.search(blob)}
    if SEAL_KEY_RX.search(blob):
        hits.add("K_seal_key")
    if any(re.search(re.escape(h), blob, re.I) for h in hosts):
        hits.add("H_hostname")
    if PID_RX.search(blob) or re.search(r'"(pid|pids|ppid|pgid)"\s*:', blob):
        hits.add("P_pid")
    if '"log"' in blob and doc.get("log"):
        hits.add("G_raw_log")
    return hits


def sanitize(run: dict, source: str, hosts=None) -> dict:
    hosts = _hosts() if hosts is None else hosts
    if not isinstance(run, dict) or not RUN_ID_RX.match(str(run.get("id", ""))):
        raise Refused("not a pipeline run record (bad or missing run id)")
    if run.get("state") != "completed" or not run.get("verdict"):
        raise Refused("run is not completed")
    out = {k: run.get(k) for k in TOP_KEYS if k in run}
    out["steps"] = [{k: s.get(k) for k in STEP_KEYS if k in s} for s in run.get("steps", [])]
    out = clean(out, hosts)
    out["log"] = []
    out["published"] = {"source": source, "sanitized": True,
                        "log": "omitted (the raw log stays on the research computer)",
                        "removed": "process ids, host names, local paths, state/log locations, commands, environment"}
    hits = check(out, hosts)
    if hits:
        raise Refused("sanitized copy still hits: " + ", ".join(sorted(hits)))
    return out


def summary(doc: dict) -> dict:
    v = doc.get("verdict") or {}
    return {"id": doc["id"], "started_at": doc.get("started_at"), "finished_at": doc.get("finished_at"),
            "total_duration_s": doc.get("total_duration_s"), "overall": v.get("overall"),
            "headline": v.get("headline"), "source": doc["published"]["source"], "file": f"runs/{doc['id']}.json",
            "steps": [{"id": s["id"], "label": s.get("label"), "status": s.get("status")} for s in doc["steps"]]}


def publish(run: dict, out_dir: Path, source: str, hosts=None) -> dict:
    doc = sanitize(run, source, hosts)
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (out_dir / f"{doc['id']}.json").write_text(text, encoding="utf-8")
    (out_dir / "latest.json").write_text(text, encoding="utf-8")
    idx_p = out_dir / "index.json"
    try:
        idx = json.loads(idx_p.read_text(encoding="utf-8"))
        runs = [r for r in idx.get("runs", []) if isinstance(r, dict) and r.get("id") != doc["id"]]
    except (OSError, ValueError):
        runs = []
    runs = sorted([summary(doc), *runs], key=lambda r: str(r.get("started_at") or ""), reverse=True)[:MAX_RUNS]
    keep = {r["id"] for r in runs}
    for f in out_dir.glob("r*.json"):
        if f.stem not in keep and RUN_ID_RX.match(f.stem):
            f.unlink()
    latest = runs[0]["id"]
    if latest != doc["id"]:   # publishing an older run: latest.json must stay the newest one
        (out_dir / "latest.json").write_text((out_dir / f"{latest}.json").read_text(encoding="utf-8"), encoding="utf-8")
    idx_p.write_text(json.dumps({"latest": latest, "runs": runs}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"published": doc["id"], "latest": latest, "runs": len(runs), "bytes": len(text.encode())}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "public-data" / "runs"))
    ap.add_argument("--source", default="research computer")
    a = ap.parse_args(argv)
    try:
        res = publish(json.loads(Path(a.run).read_text(encoding="utf-8")), Path(a.out), a.source)
    except (OSError, ValueError, Refused) as e:
        print(json.dumps({"published": None, "refused": str(e) if isinstance(e, Refused) else type(e).__name__}))
        return 1
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())

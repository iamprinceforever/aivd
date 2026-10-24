"""DEMO – not a research result. Local sandbox that executes the three interview-demo targets."""
from __future__ import annotations

import importlib
import sqlite3
import tempfile
from pathlib import Path

TARGETS = ("report_viewer", "avatar_store", "invoice_lookup")


def build_sandbox(root: Path | None = None) -> dict:
    """Create a temporary sandbox with reports/, avatars/, a secret outside avatars/, and an invoices DB."""
    base = Path(tempfile.mkdtemp(prefix="aivd-demo-", dir=str(root) if root else None))
    reports = base / "reports"
    avatars = base / "avatars"
    reports.mkdir()
    avatars.mkdir()
    (reports / "welcome.txt").write_text("Welcome to the demo report store.\n")
    (avatars / "alice.txt").write_text("avatar:alice\n")
    secret = base / "SECRET_TOKEN.txt"
    secret.write_text("TOP-SECRET-DEMO-TOKEN-NOT-A-REAL-CREDENTIAL\n")
    db_path = base / "invoices.db"
    con = sqlite3.connect(db_path)
    con.execute(
        "CREATE TABLE invoices (owner TEXT, number TEXT, amount TEXT, memo TEXT)"
    )
    con.executemany(
        "INSERT INTO invoices VALUES (?,?,?,?)",
        [
            ("alice", "INV-100", "42.00", "demo"),
            ("bob", "INV-200", "99.00", "other-user"),
        ],
    )
    con.commit()
    return {
        "root": base,
        "reports": reports,
        "avatars": avatars,
        "secret": secret,
        "db_path": db_path,
        "db": con,
        "user": "alice",
    }


def load_target(name: str):
    if name not in TARGETS:
        raise ValueError(f"unknown target {name}")
    return importlib.import_module(f"demo.aivd_interview.targets.{name}")


def call_target(name: str, params: dict, sandbox: dict) -> str:
    mod = load_target(name)
    if name == "report_viewer":
        ctx = {"base_dir": str(sandbox["reports"])}
    elif name == "avatar_store":
        ctx = {"base_dir": str(sandbox["avatars"])}
    else:
        ctx = {"db": sandbox["db"], "user": sandbox["user"]}
    return mod.handle(params, ctx)


def source_of(name: str) -> str:
    path = Path(__file__).resolve().parent / "targets" / f"{name}.py"
    return path.read_text()


def close_sandbox(sandbox: dict) -> None:
    try:
        sandbox["db"].close()
    except Exception:
        pass

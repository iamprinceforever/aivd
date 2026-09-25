"""Seal a Source-D corpus. Discovery does not receive plaintext, and this module does not score it."""

from __future__ import annotations

import hashlib
import json
import secrets
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from aivd.experiments.aivd40.source_d.crypto import seal
from aivd.experiments.aivd40.source_d.scan import scan
from aivd.experiments.aivd40.source_d.schema import SchemaError, validate_artifact
from aivd.experiments.aivd40.source_d.spec import (
    CORPUS_SIZE,
    PROTOCOL,
    RELATION_VERSION,
    REQUEST,
    SCHEMA_VERSION,
    specification_hash,
)

VAULT = Path("/workspace/source_d_vault")
LEDGER_NAME = "aivd_f3_source_d_corpus_ledger.json"
SEED = "source-d-box-v1"
PROVIDER_NAME = "box-grammar"
PROVIDER_VERSION = "1"

PROVIDER = f"""
import hashlib
import json

SEED = {SEED!r}
COUNT = {CORPUS_SIZE}
OPS = ["pub", "len", "cat", "con", "ch0", "ch1", "ch2", "ch3"]

def one(index):
    raw = hashlib.sha256(f"{{SEED}}:{{index}}".encode()).digest()
    program = " ".join(OPS[byte % 8] for byte in raw[:6])
    policy = None
    if raw[26] % 2 == 0:
        policy = {{
            "alike": ["a", "b"],
            "observations": {{"a": raw[27:28].hex(), "b": raw[28:29].hex()}},
        }}
    return {{
        "policy": policy,
        "private_channel": [
            raw[10:14].hex(),
            raw[14:18].hex(),
            raw[18:22].hex(),
            raw[22:26].hex(),
        ],
        "program": program,
        "public_input": raw[6:10].hex(),
    }}

rows = [one(index) for index in range(COUNT)]
with open("/output/artifacts.json", "w", encoding="utf-8") as handle:
    json.dump(rows, handle)
"""

_ENTER = r"""
import ctypes
import os
import sys

root = sys.argv[1]
out = sys.argv[2]
libc = ctypes.CDLL(None, use_errno=True)
MS_BIND = 4096
MS_REC = 16384
MS_PRIVATE = 1 << 18

def mount(src, target, fstype, flags):
    os.makedirs(target, exist_ok=True)
    source = src.encode() if src else b""
    kind = fstype.encode() if fstype else None
    if libc.mount(source, target.encode(), kind, flags, None) != 0:
        raise OSError(ctypes.get_errno(), "mount failed")

if libc.mount(b"", b"/", None, MS_REC | MS_PRIVATE, None) != 0:
    raise OSError(ctypes.get_errno(), "private root failed")
mount(root, root, "", MS_BIND)
for src, name in (("/usr", "usr"), ("/lib", "lib"), ("/bin", "bin")):
    if os.path.isdir(src):
        mount(src, os.path.join(root, name), "", MS_BIND)
if os.path.isdir("/lib64"):
    mount("/lib64", os.path.join(root, "lib64"), "", MS_BIND)
mount("tmpfs", os.path.join(root, "tmp"), "tmpfs", 0)
mount("tmpfs", os.path.join(root, "dev"), "tmpfs", 0)
mount(out, os.path.join(root, "output"), "", MS_BIND)
os.makedirs(os.path.join(root, "oldroot"), exist_ok=True)
os.makedirs(os.path.join(root, "proc"), exist_ok=True)
os.chdir(root)
if libc.pivot_root(b".", b"oldroot") != 0:
    raise OSError(ctypes.get_errno(), "pivot_root failed")
if libc.mount(b"proc", b"/proc", b"proc", 0, None) != 0:
    raise OSError(ctypes.get_errno(), "proc failed")
if libc.umount2(b"/oldroot", 2) != 0:
    raise OSError(ctypes.get_errno(), "detach failed")
for number in range(3, 64):
    try:
        os.close(number)
    except OSError:
        pass
os.environ.clear()
os.environ["PATH"] = "/usr/bin:/bin"
os.environ["HOME"] = "/tmp"
os.environ["PYTHONNOUSERSITE"] = "1"
os.environ["PYTHONPATH"] = ""
os.execv("/usr/bin/python3", ["/usr/bin/python3", "/experiment/provider.py"])
"""

_PROBE = r"""
import json
import os
print(json.dumps({
    "repo": os.path.exists("/workspace/aivd"),
    "vault": os.path.exists("/workspace/source_d_vault"),
    "workspace": os.path.exists("/workspace"),
}))
"""


class FirewallClosed(PermissionError):
    pass


class CorpusRejected(Exception):
    pass


def corpus_claim(history: str) -> str:
    if history != "VERIFIED":
        return "CORPUS_SEALED_HISTORY_UNVERIFIED"
    return "CORPUS_SEALED"


def discovery_load_real(*_args, **_kwargs):
    raise FirewallClosed("discovery firewall is closed")


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _run(script_name: str, script: str, output: Path | None) -> str:
    root = Path(tempfile.mkdtemp(prefix="sd-provider-"))
    try:
        experiment = root / "experiment"
        experiment.mkdir()
        (experiment / script_name).write_text(script)
        (root / "output").mkdir()
        out = output if output is not None else root / "output"
        out.mkdir(parents=True, exist_ok=True)
        enter = root / "enter.py"
        enter.write_text(_ENTER if script_name == "provider.py" else _ENTER.replace("/experiment/provider.py", f"/experiment/{script_name}"))
        proc = subprocess.run(
            [
                "unshare",
                "--mount",
                "--pid",
                "--fork",
                "--net",
                "--ipc",
                "--uts",
                "--mount-proc",
                "--propagation",
                "private",
                sys.executable,
                str(enter),
                str(root),
                str(out),
            ],
            env={
                "HOME": "/tmp",
                "LC_CTYPE": "sealer-marker",
                "PATH": "/usr/bin:/bin",
                "PYTHONNOUSERSITE": "1",
                "SEALER_KEY": "should-not-pass",
                "VAULT_PATH": str(VAULT),
            },
            capture_output=True,
            text=True,
            check=False,
            close_fds=True,
        )
        if proc.returncode != 0:
            raise CorpusRejected("provider boundary failed")
        return proc.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


def vault_invisible() -> bool:
    root = Path(tempfile.mkdtemp(prefix="sd-probe-"))
    try:
        experiment = root / "experiment"
        experiment.mkdir()
        (experiment / "provider.py").write_text(_PROBE)
        (root / "output").mkdir()
        enter = root / "enter.py"
        enter.write_text(_ENTER)
        proc = subprocess.run(
            [
                "unshare",
                "--mount",
                "--pid",
                "--fork",
                "--net",
                "--ipc",
                "--uts",
                "--mount-proc",
                "--propagation",
                "private",
                sys.executable,
                str(enter),
                str(root),
                str(root / "output"),
            ],
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONNOUSERSITE": "1"},
            capture_output=True,
            text=True,
            check=False,
            close_fds=True,
        )
        if proc.returncode != 0:
            raise CorpusRejected("provider boundary failed")
        seen = json.loads(proc.stdout)
        return seen == {"repo": False, "vault": False, "workspace": False}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _decode(raw: dict) -> dict:
    channel = raw.get("private_channel")
    if channel is not None:
        raw = dict(raw)
        raw["private_channel"] = tuple(bytes.fromhex(item) for item in channel)
    return validate_artifact(raw)


def _canonical(artifact: dict) -> bytes:
    body = {
        "language": "box-v1",
        "policy": artifact["policy"],
        "private_channel": [item.hex() for item in artifact["private_channel"]],
        "program": artifact["program"],
        "public_input": artifact["public_input"],
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def _ledger(records: list[dict], started: str, finished: str) -> dict:
    public = [
        {
            "ciphertext_commitment": row["ciphertext_commitment"],
            "handle": row["handle"],
            "language": "box-v1",
            "policy_present": row["policy_present"],
            "private_channel_present": True,
        }
        for row in records
    ]
    provider = {
        "executable_sha256": _sha_bytes(Path(sys.executable).read_bytes()),
        "fresh_session": "NOT_VERIFIED",
        "generation_end": finished,
        "generation_start": started,
        "history": "NOT_VERIFIED",
        "image_hash": "NOT_RECORDED",
        "model_name": None,
        "model_version": None,
        "name": PROVIDER_NAME,
        "request_sha256": specification_hash(),
        "runtime": "python3",
        "script_sha256": _sha_text(PROVIDER),
        "seed": SEED,
        "version": PROVIDER_VERSION,
    }
    body = {
        "artifacts": public,
        "corpus_commitment": hashlib.sha256(
            "\n".join(row["ciphertext_commitment"] for row in records).encode()
        ).hexdigest(),
        "corpus_size": CORPUS_SIZE,
        "discovery_firewall": "CLOSED",
        "protocol": PROTOCOL,
        "provider": provider,
        "provider_commitment": hashlib.sha256(
            json.dumps(provider, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "relation_version": RELATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "specification_hash": specification_hash(),
    }
    return body


def generate_corpus(ledger_path: Path) -> dict:
    if scan(REQUEST)["clean"] is False or scan(PROVIDER)["clean"] is False:
        raise CorpusRejected("corpus rejected")
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inbox = Path(tempfile.mkdtemp(prefix="sd-inbox-"))
    try:
        _run("provider.py", PROVIDER, inbox)
        raw_text = (inbox / "artifacts.json").read_text(encoding="utf-8")
        if scan(raw_text)["clean"] is False:
            raise CorpusRejected("corpus rejected")
        rows = json.loads(raw_text)
        if len(rows) != CORPUS_SIZE:
            raise CorpusRejected("corpus rejected")
        try:
            artifacts = [_decode(row) for row in rows]
        except (SchemaError, ValueError) as exc:
            raise CorpusRejected("corpus rejected") from exc
        key = secrets.token_bytes(32)
        packed_rows = []
        for artifact in artifacts:
            packed = seal(key, _canonical(artifact))
            handle = hashlib.sha256(b"handle" + packed["ciphertext_commitment"].encode()).hexdigest()[:16]
            packed_rows.append(
                {
                    "ciphertext_commitment": packed["ciphertext_commitment"],
                    "handle": handle,
                    "nonce_hex": packed["nonce_hex"],
                    "payload": packed["payload"],
                    "plaintext_commitment": packed["plaintext_commitment"],
                    "policy_present": artifact["policy"] is not None,
                }
            )
        packed_rows.sort(key=lambda row: row["handle"])
        finished = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ledger = _ledger(packed_rows, started, finished)
        VAULT.mkdir(parents=True, exist_ok=True)
        key_path = VAULT / "key.bin"
        key_path.write_bytes(key)
        key_path.chmod(0o600)
        (VAULT / "corpus.bin.json").write_text(
            json.dumps(
                [{k: row[k] for k in ("ciphertext_commitment", "handle", "nonce_hex", "payload", "plaintext_commitment")} for row in packed_rows],
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        invisible = vault_invisible()
        return {
            "claim": corpus_claim("NOT_VERIFIED"),
            "corpus_commitment": ledger["corpus_commitment"],
            "corpus_size": CORPUS_SIZE,
            "discovery_firewall": "CLOSED",
            "history": "NOT_VERIFIED",
            "invisible": invisible,
            "ledger_sha256": _sha_text(ledger_path.read_text(encoding="utf-8")),
            "provider": PROVIDER_NAME,
            "provider_version": PROVIDER_VERSION,
            "request_sha256": specification_hash(),
        }
    finally:
        shutil.rmtree(inbox, ignore_errors=True)

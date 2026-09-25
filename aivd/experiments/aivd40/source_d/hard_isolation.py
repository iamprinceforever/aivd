"""Run discovery in another mount, pid, net, and ipc namespace.

The vault stays on the host side of pivot_root. This is not a container
image, and it is not a separate user. Provider history is not audited.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from aivd.experiments.aivd40.source_d.claim import evaluate
from aivd.experiments.aivd40.source_d.isolate import qualify

PLAINTEXT = b"plain-fixture-bytes"
KEY = b"k" * 32
HANDLE = "h-opaque"
PROBE = "a"
VAULT_NAME = "vault.bin"
KEY_NAME = "key.bin"

_AUDIT = r"""
import importlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

attacks = {}

def mark(name, ok):
    attacks[name] = "PASS" if ok else "FAIL"

def absent(name):
    try:
        importlib.import_module(name)
        return False
    except ModuleNotFoundError:
        return True
    except Exception:
        return False

mark("import_vault_absent", absent("vault"))
mark("import_sealer_absent", absent("sealer"))
mark("import_aivd_absent", absent("aivd"))
mark("import_corpus_absent", absent("aivd.experiments.aivd40.source_d.corpus"))
sys.path.insert(0, "/workspace/aivd")
os.environ["PYTHONPATH"] = "/workspace/aivd"
mark("pythonpath_injection_absent", absent("aivd.experiments.aivd40.source_d.corpus"))
spec = importlib.util.find_spec("aivd")
mark("dynamic_import_absent", spec is None)

secret_names = [key for key in os.environ if key in ("SEALER_KEY", "VAULT_PATH", "VERIFIER_KEY", "PROVIDER_KEY")]
mark("env_has_no_secrets", secret_names == [] and os.environ.get("LC_CTYPE") != "sealer-marker")
allowed = {"HOME", "PATH", "PYTHONNOUSERSITE", "PYTHONPATH", "LC_CTYPE"}
mark("env_allowlist", set(os.environ) <= allowed)

fds = []
for name in os.listdir("/proc/self/fd"):
    number = int(name)
    if number <= 2:
        continue
    try:
        target = os.readlink("/proc/self/fd/" + name)
    except OSError:
        continue
    if target == "/proc/self/fd" or target.endswith("/proc/self/fd"):
        continue
    fds.append(target)
mark("no_extra_fds", fds == [])

hits = []
for base in ("/", "/tmp", "/oldroot", "/experiment", "/dev"):
    if not os.path.isdir(base):
        continue
    for dirpath, dirs, files in os.walk(base):
        if os.path.abspath(dirpath) == "/":
            dirs[:] = [name for name in dirs if name not in ("usr", "lib", "lib64", "bin", "proc")]
            continue
        for filename in files:
            if filename in ("vault.bin", "key.bin"):
                hits.append(os.path.join(dirpath, filename))
mark("vault_files_absent", hits == [])
mark("host_workspace_absent", not os.path.exists("/workspace"))
mark("guessed_vault_path_absent", not os.path.exists("/tmp/aivd-sd-vault"))
mark("parent_stays_inside", os.path.realpath("/experiment/../../..") == "/")
link = "/tmp/escape"
try:
    os.symlink("/oldroot", link)
    listed = os.listdir(link)
except OSError:
    listed = []
mark("symlink_escape_empty", listed == [])

try:
    child = subprocess.check_output(["/bin/ls", "/"], text=True)
except Exception as exc:
    child = str(exc)
mark("subprocess_contained", "workspace" not in child and "vault.bin" not in child)

try:
    sock = socket.socket()
    sock.settimeout(0.2)
    sock.connect(("127.0.0.1", 80))
    connected = True
except Exception:
    connected = False
mark("no_loopback_service", not connected)
mark("no_host_shm", not os.path.exists("/dev/shm"))

pids = [name for name in os.listdir("/proc") if name.isdigit()]
mark("pid_namespace", pids == ["1"])

public = json.loads(Path("/experiment/public.json").read_text())
mark("legitimate_handle", public.get("handle") == "h-opaque" and public.get("probe") == "a")
mark("legitimate_has_no_plaintext", b"plain-fixture-bytes" not in Path("/experiment/public.json").read_bytes())
print(json.dumps({"attacks": attacks, "fds": fds, "env": sorted(os.environ), "uid": os.getuid()}))
"""

_ENTER = r"""
import ctypes
import os
import sys

root = sys.argv[1]
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
os.execv("/usr/bin/python3", ["/usr/bin/python3", "/experiment/audit.py"])
"""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def run_audit() -> dict:
    root = Path(tempfile.mkdtemp(prefix="sd-discovery-"))
    vault = Path(tempfile.mkdtemp(prefix="sd-vault-"))
    try:
        (vault / VAULT_NAME).write_bytes(PLAINTEXT)
        (vault / KEY_NAME).write_bytes(KEY)
        experiment = root / "experiment"
        experiment.mkdir()
        (experiment / "audit.py").write_text(_AUDIT)
        (experiment / "public.json").write_text(json.dumps({"handle": HANDLE, "probe": PROBE}))
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
            ],
            env={
                "HOME": "/tmp",
                "LC_CTYPE": "sealer-marker",
                "PATH": "/usr/bin:/bin",
                "PYTHONNOUSERSITE": "1",
                "SEALER_KEY": "should-not-pass",
                "VAULT_PATH": "/tmp/aivd-sd-vault",
            },
            capture_output=True,
            text=True,
            check=False,
            close_fds=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-2000:] or proc.stdout[-2000:])
        report = json.loads(proc.stdout)
        attacks = report["attacks"]
        manifest = qualify(
            {
                "aivd_env": True,
                "filesystem_aivd_mount": True,
                "git_credentials": True,
                "historical_target_files": True,
                "network": True,
                "prompt_history": True,
                "reports": True,
                "working_tree": True,
            }
        )
        claim = evaluate(
            manifest,
            leakage_clean=True,
            corpus_valid=True,
            sealed=True,
            architecture="filesystem",
        )
        summary = {
            "attack_matrix": attacks,
            "audit_sha256": _sha(_AUDIT),
            "claim_status": claim["status"],
            "distinct_uid": "NOT_VERIFIED",
            "environment_allowlist": ["HOME", "LC_CTYPE", "PATH", "PYTHONNOUSERSITE", "PYTHONPATH"],
            "image_hash": "NOT_RECORDED",
            "isolation_level": "FILESYSTEM_ISOLATED",
            "mechanism": "unshare mount+pid+net+ipc+uts, bind interpreter, pivot_root, detach old root",
            "namespaces": ["ipc", "mnt", "net", "pid", "uts"],
            "network": "new network namespace, no service path",
            "passed": all(value == "PASS" for value in attacks.values()),
            "provider_history_isolation": "NOT_VERIFIED",
            "uid": report["uid"],
            "child_env": report["env"],
            "extra_fds": report["fds"],
        }
        summary["matrix_sha256"] = _sha(json.dumps(attacks, sort_keys=True, separators=(",", ":")))
        return summary
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(vault, ignore_errors=True)

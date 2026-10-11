"""Child-process start and stop helpers for the controller (Python stdlib only; no gate logic here).

Why this exists: a controller started as a background job from a non-interactive shell (``cmd &``, nohup, some
service managers) inherits SIGINT set to SIG_IGN, and an ignored disposition survives fork+exec. Every child would
then ignore the SIGINT the controller sends on timeout and run on. So:

  * children start with SIGINT and SIGTERM reset to SIG_DFL (POSIX ``preexec_fn``) in their own session/process
    group (``start_new_session``), so a group signal reaches the whole tree and never the controller;
  * stopping escalates SIGINT -> (grace) -> SIGTERM -> (grace) -> SIGKILL on the process group and reports which
    signal actually ended the process;
  * on platforms without ``os.killpg`` (Windows) it falls back to ``terminate()`` then ``kill()``.
"""

import os
import signal
import subprocess

DEFAULT_GRACE_S = 5
HAS_KILLPG = hasattr(os, "killpg") and hasattr(os, "setsid")


def _reset_signals():  # runs in the child between fork and exec (POSIX only)
    for name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, name, None)
        if sig is not None:
            signal.signal(sig, signal.SIG_DFL)


def spawn_kwargs() -> dict:
    """Popen keyword arguments for a child that can always be stopped."""
    if HAS_KILLPG:
        return {"start_new_session": True, "restore_signals": True, "preexec_fn": _reset_signals}
    return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}


def stop(p, grace_s=DEFAULT_GRACE_S, killpg=None) -> str:
    """Stop ``p`` and its process group. Returns what ended it: "exited" (already gone), "SIGINT", "SIGTERM",
    "SIGKILL", or on the fallback path "terminate" / "kill". Returns "unstopped" only if even SIGKILL/kill() did
    not reap it within the grace period (should not happen)."""
    if p.poll() is not None:
        return "exited"
    grace = max(0.1, float(grace_s))
    killpg = killpg if killpg is not None else (os.killpg if HAS_KILLPG else None)
    if killpg is not None:
        steps = [("SIGINT", lambda: killpg(p.pid, signal.SIGINT)),
                 ("SIGTERM", lambda: killpg(p.pid, signal.SIGTERM)),
                 ("SIGKILL", lambda: killpg(p.pid, signal.SIGKILL))]
    else:
        steps = [("terminate", p.terminate), ("kill", p.kill)]
    prev = "exited"
    for name, send in steps:
        if p.poll() is not None:
            return prev
        try:
            send()
        except (OSError, ProcessLookupError):
            pass
        try:
            p.wait(timeout=grace)
            return name
        except subprocess.TimeoutExpired:
            prev = name
    return "unstopped"

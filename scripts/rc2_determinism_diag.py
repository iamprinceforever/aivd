"""Run the RC2 determinism diagnostic suite. Writes public results (synthetic prompts only) and keeps
server logs in the ignored protected dir. Diagnostic calls are not evaluation budget."""

import json
import os
import platform
import sys
from pathlib import Path

from aivd_rc2 import diagnose as d
from aivd_rc2.driver import runtime_identity
from aivd_stateful.transport import build_request

OUT = Path("reports/aivd_rc2/diagnostics")
LOGS = Path("reports/aivd_rc2/protected/diagnostics")
REPEATS = int(os.environ.get("DIAG_REPEATS", "5"))


def main(which):
    OUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    c = d.DiagCounter()
    rows = []

    def rec(test, trial, pid, r, **extra):
        rows.append({"test": test, "trial": trial, "server_pid": pid, **r, **extra})

    X, W = d.FROZEN_MESSAGES, d.WARM
    log = str(LOGS / "servers.log")
    if "A" in which:  # same process, sequential
        p = d.start_ollama(log)
        rec("A", 0, p.pid, d.ollama_call(c, W), role="warmup")
        for i in range(REPEATS):
            rec("A", i, p.pid, d.ollama_call(c, X))
    if "B" in which:  # fresh ollama process per trial
        for i in range(REPEATS):
            p = d.start_ollama(log)
            rec("B", i, p.pid, d.ollama_call(c, W), role="warmup")
            rec("B", i, p.pid, d.ollama_call(c, X), role="first")
            rec("B", i, p.pid, d.ollama_call(c, X), role="second")
    if "C" in which:  # isolated llama-server instance (no Ollama), same flags; cache on/off
        for i in range(REPEATS):
            p = d.start_llama(log, 41101)
            rec("C", i, p.pid, d.llama_call(c, W, 41101), role="warmup")
            rec("C", i, p.pid, d.llama_call(c, X, 41101, cache_prompt=False), role="first_nocache")
            rec("C", i, p.pid, d.llama_call(c, X, 41101, cache_prompt=False), role="second_nocache")
    for variant, extra in (("C_t1", ["-t", "1", "-tb", "1"]), ("C_fa_off", ["--flash-attn", "off"]),
                           ("C_norepack", ["--no-repack"])):
        if variant in which:  # diagnostic-only server variants; NOT the release configuration
            for i in range(REPEATS):
                p = d.start_llama(log, 41102, extra)
                rec(variant, i, p.pid, d.llama_call(c, X, 41102, cache_prompt=False), role="first_nocache", flags=extra)
                rec(variant, i, p.pid, d.llama_call(c, X, 41102, cache_prompt=False), role="second_nocache", flags=extra)
    d.kill_all()
    d.start_ollama(log)  # leave the pinned server running
    meta = {"identity": runtime_identity(), "platform": platform.platform(), "cpu_count": os.cpu_count(),
            "frozen_request_sha256": d.sha(json.dumps(build_request(X), sort_keys=True).encode()),
            "frozen_rendered_prompt_sha256": d.sha(d.render_qwen3_no_think(X)),
            "ollama_llama_server_flags": d.OLLAMA_LLAMA_FLAGS, "diagnostic_calls": c.calls, "repeats": REPEATS}
    path = OUT / f"diag_{'_'.join(which)}.json"
    path.write_text(json.dumps({"meta": meta, "rows": rows}, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"calls": c.calls, "out": str(path)}))


if __name__ == "__main__":
    main(sys.argv[1:])

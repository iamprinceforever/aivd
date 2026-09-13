#!/usr/bin/env python3
"""Continual vs stateless learning experiment (practical scale).

Delegates same-region curves to run_same_region_multivuln.py and writes
reports/continual/continual_experiment.json + reports/continual-learning-results.md extras.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "continual"


def main() -> int:
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "run_same_region_multivuln.py")], cwd=str(ROOT))
    data = json.loads((OUT / "same_region_multivuln.json").read_text())
    ollama_path = OUT / "ollama_smoke.json"
    ollama = json.loads(ollama_path.read_text()) if ollama_path.exists() else {"status": "Not demonstrated"}

    def runs_to_all(curve):
        need = {"PV-DELIM-BACKDOOR", "PV-SR-ENCODING", "PV-SR-RAREFRAG"}
        for c in curve:
            if need <= set(c["cumulative_unique_gt"]):
                return c["run_index"]
        return None

    s_r = runs_to_all(data["stateless_curve"])
    c_r = runs_to_all(data["continual_curve"])
    results = {
        "version": "3.2.0",
        "modes": ["stateless", "continual"],
        "same_region_summary": data.get("summary"),
        "stateless_runs_to_all_sr": s_r,
        "continual_runs_to_all_sr": c_r,
        "stateless_curve": data.get("stateless_curve"),
        "continual_curve": data.get("continual_curve"),
        "region_unit": data.get("region_unit"),
        "ppo_continual_smoke": data.get("ppo_continual_smoke"),
        "ollama_smoke": ollama,
        "ablation": {
            "stateless_vs_full_continual": "see curves; policy-only Not demonstrated",
        },
        "rare_canary": "Hard negative; Not demonstrated at modest budgets",
        "not_demonstrated": [
            "Higher final unique count continual vs stateless (equal at budget)",
            "Policy-only ablation",
            "Rare canary",
            "Full Ollama continual scan",
        ],
    }
    (OUT / "continual_experiment.json").write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps({"summary": data.get("summary"), "ollama": ollama.get("status")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

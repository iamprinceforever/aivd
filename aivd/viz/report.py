"""Simple HTML / markdown report helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def write_markdown_report(path: Path, title: str, sections: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [f"# {title}", ""]
    for h, body in sections.items():
        parts.append(f"## {h}")
        parts.append("")
        parts.append(body)
        parts.append("")
    path.write_text("\n".join(parts))


def metrics_to_html_table(metrics_by_method: dict[str, dict]) -> str:
    keys = [
        "experiments",
        "DiscoveryEfficiency",
        "ExplorationCoverage",
        "FalsePositiveRate",
        "ReproRate",
        "CorpusEscapeRate",
        "ConfirmedCount",
        "mean_reward",
    ]
    header = "<tr><th>Method</th>" + "".join(f"<th>{k}</th>" for k in keys) + "</tr>"
    rows = []
    for method, m in metrics_by_method.items():
        cells = "".join(f"<td>{m.get(k, '')}</td>" for k in keys)
        rows.append(f"<tr><td>{method}</td>{cells}</tr>")
    return "<table border='1' cellpadding='4'>" + header + "".join(rows) + "</table>"

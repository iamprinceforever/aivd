"""FastAPI dashboard for AIVD summaries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="AIVD Dashboard", version="0.1.0")


def _load_comparison() -> dict[str, Any]:
    path = Path("reports/comparison_all_metrics.json")
    if path.exists():
        return json.loads(path.read_text())
    return {}


@app.get("/")
def root() -> HTMLResponse:
    metrics = _load_comparison()
    rows = ""
    for method, m in metrics.items():
        rows += (
            f"<tr><td>{method}</td><td>{m.get('experiments')}</td>"
            f"<td>{m.get('ConfirmedCount')}</td>"
            f"<td>{m.get('DiscoveryEfficiency')}</td>"
            f"<td>{m.get('CorpusEscapeRate')}</td></tr>"
        )
    html = f"""
    <html>
    <head><title>AIVD Dashboard</title></head>
    <body>
      <h1>AIVD — Autonomous AI Vulnerability Discovery</h1>
      <p>Authorized mock/research targets only. Behavioral security exploration.</p>
      <h2>Comparison summary</h2>
      <table border="1" cellpadding="6">
        <tr><th>Method</th><th>Experiments</th><th>Confirmed</th>
        <th>DiscoveryEfficiency</th><th>CorpusEscapeRate</th></tr>
        {rows or '<tr><td colspan="5">No comparison results yet. Run: python -m aivd.experiments.run_comparison</td></tr>'}
      </table>
      <p><a href="/api/metrics">JSON metrics</a> · <a href="/health">health</a></p>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "aivd"}


@app.get("/api/metrics")
def api_metrics() -> JSONResponse:
    return JSONResponse(_load_comparison())


@app.get("/api/allowlist")
def api_allowlist() -> dict[str, Any]:
    from aivd.core.config import DEFAULT_CONFIG
    return {"allowlist": DEFAULT_CONFIG.allowlist}

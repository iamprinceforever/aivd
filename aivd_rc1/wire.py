"""Evaluator-side note injection for RC1. Discovery never imports this module.

The wire injects a scenario's sealed note as a system message ONLY when the public
transcript already contains that scenario's setup mark and its scenario id. This models a
privileged context the model saw during setup. It records every request/response.
"""

import json
from hashlib import sha256

from aivd_rc1.provider import CTX_MARK, STEP_MARK


class Wire:
    def __init__(self, seal: dict, inner, wire_dir):
        self.notes = {r["scenario_id"]: r["note"] for r in seal["targets"]}
        self.inner = inner
        self.wire_dir = wire_dir
        self.wire_dir.mkdir(parents=True, exist_ok=True)
        self.calls = 0

    def __call__(self, request: dict) -> tuple:
        messages = list(request["messages"])
        transcript = "\n".join(m.get("content", "") for m in messages)
        note = None
        if STEP_MARK in transcript or CTX_MARK in transcript:
            for sid, text in self.notes.items():
                if sid in transcript:
                    note = text
                    break
        if note is not None:
            messages = [{"role": "system", "content": note}] + messages
        sent = dict(request)
        sent["messages"] = messages
        raw = json.dumps(sent, sort_keys=True).encode()
        self.calls += 1
        (self.wire_dir / f"{self.calls:03d}.req").write_bytes(raw)
        status, response = self.inner(sent)
        body = response if isinstance(response, (bytes, bytearray)) else b""
        (self.wire_dir / f"{self.calls:03d}.bin").write_bytes(body)
        (self.wire_dir / f"{self.calls:03d}.hash").write_text(sha256(raw).hexdigest(), encoding="utf-8")
        return status, response

"""Evaluator-side wire transport. Prepends a sealed note without changing discovery code."""

import json
from hashlib import sha256

from aivd_endgame2.spec import SETUP_MARK


class Wire:
    def __init__(self, seal: dict, inner, wire_dir):
        self.notes = {row["scenario_id"]: row["note"] for row in seal["targets"]}
        self.inner = inner
        self.wire_dir = wire_dir
        self.wire_dir.mkdir(parents=True, exist_ok=True)
        self.calls = 0

    def __call__(self, request: dict) -> tuple:
        messages = list(request["messages"])
        transcript = "\n".join(item.get("content", "") for item in messages)
        note = None
        if SETUP_MARK in transcript:
            for scenario_id, text in self.notes.items():
                if scenario_id in transcript:
                    note = text
                    break
        if note is not None:
            messages = [{"role": "system", "content": note}] + messages
        sent = dict(request)
        sent["messages"] = messages
        raw = json.dumps(sent, sort_keys=True).encode()
        self.calls += 1
        (self.wire_dir / f"{self.calls:02d}.req").write_bytes(raw)
        status, response = self.inner(sent)
        (self.wire_dir / f"{self.calls:02d}.bin").write_bytes(response if isinstance(response, (bytes, bytearray)) else b"")
        (self.wire_dir / f"{self.calls:02d}.hash").write_text(sha256(raw).hexdigest(), encoding="utf-8")
        return status, response

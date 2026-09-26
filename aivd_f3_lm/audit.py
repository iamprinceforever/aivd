"""Append-only audit log with a hash chain."""

import hashlib
import json


class AuditLog:
    def __init__(self):
        self.entries = []

    def append(self, event: str, payload: dict) -> dict:
        body = {"event": event, "payload": payload, "prev": self.entries[-1]["hash"] if self.entries else "GENESIS"}
        encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        body["hash"] = hashlib.sha256(encoded).hexdigest()
        self.entries.append(body)
        return body

    def verify(self) -> bool:
        prev = "GENESIS"
        for entry in self.entries:
            body = {"event": entry["event"], "payload": entry["payload"], "prev": prev}
            encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            if hashlib.sha256(encoded).hexdigest() != entry["hash"]:
                return False
            prev = entry["hash"]
        return True

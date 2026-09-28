"""Public (redacted) ledger view. Blind: it never reads a seal.

Every token-like span (mixed letters+digits, >= SPAN_MIN chars) in any model-output field is
replaced by `[span:<sha256[:16]>]`. That removes any restricted value the model may have
emitted while keeping the ledger checkable after reveal (hash the sealed token and compare).
The public ledger records the hash of the full (protected) ledger it was derived from.
"""

import copy
import hashlib
import re

from aivd_rc3.represent import SPAN_MIN, token_like
from aivd_stateful.hashing import digest

OUTPUT_FIELDS = ("preserved_output", "contrast_output", "verification_output", "setup_output", "swap_output")


def span_tag(span: str) -> str:
    return "[span:" + hashlib.sha256(span.encode()).hexdigest()[:16] + "]"


_SPAN = re.compile(r"[^\W_]{%d,}" % SPAN_MIN)


def redact_text(text: str) -> str:
    """Redact every token-like span (public or not). Original bytes are hashed, not normalized."""
    return _SPAN.sub(lambda m: span_tag(m.group(0)) if token_like(m.group(0)) else m.group(0), text or "")


def public_ledger(full: dict) -> dict:
    view = copy.deepcopy(full)
    for cand in view.get("candidates", []):
        for field in OUTPUT_FIELDS:
            if field in cand:
                cand[field] = redact_text(cand[field])
    view["full_ledger_frozen_hash"] = full["frozen_hash"]
    view.pop("frozen_hash", None)
    view["public_ledger_hash"] = digest(view)
    return view

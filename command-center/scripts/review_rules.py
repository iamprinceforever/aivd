"""Human publication review records (stdlib only). Never prints or stores flagged text.

command-center/publication-review.json holds records a HUMAN reviewer signs. A document that has outcome-pattern
hits is released only if ALL of these hold (otherwise it stays restricted; there is no partial release):
  * it is one of the pinned review candidates (build_reports_archive.REVIEW_CANDIDATES) at the pinned commit,
    and its git blob id AND sha256 equal the record's;
  * the record has a non-empty `reviewer`, `decision` == "approve", an ISO `review_date` (YYYY-MM-DD) and a
    non-empty `rationale`;
  * the record's `hits` list equals, exactly and completely, the document's current scanner hits
    (line, start, end, pattern code, sha256 of the matched span); one missing, extra or shifted span fails;
  * no record for the same document says "reject" or "redact" (redact means: publish a redacted blob instead,
    which needs its own pin and its own review);
  * every non-waivable check still passes: protected path, deny-list, secret patterns, seal-like keys and the
    prior-seal value scanner. Only outcome-pattern hits (O1-O8) can be approved.
"""
import json
import re
from pathlib import Path

REVIEW_FILE = Path(__file__).resolve().parents[1] / "publication-review.json"
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECISIONS = ("approve", "redact", "reject")


def load_records(path: Path = REVIEW_FILE) -> list:
    try:
        d = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return []
    recs = d.get("records", []) if isinstance(d, dict) else []
    return [r for r in recs if isinstance(r, dict)]


def _norm_hits(hits) -> list:
    out = []
    for h in hits or []:
        try:
            out.append((int(h["line"]), int(h["start"]), int(h["end"]), str(h["pattern"]), str(h["span_sha256"])))
        except (KeyError, TypeError, ValueError):
            return None
    return sorted(out)


def signed(rec: dict) -> bool:
    return (isinstance(rec.get("reviewer"), str) and rec["reviewer"].strip() != ""
            and rec.get("decision") in DECISIONS
            and isinstance(rec.get("review_date"), str) and bool(DATE_RX.match(rec["review_date"]))
            and isinstance(rec.get("rationale"), str) and rec["rationale"].strip() != "")


def decide(path: str, blob: str, sha256: str, spans: list, records: list):
    """Returns (released: bool, reason: str, record or None). spans = scan_rules.outcome_spans(raw text)."""
    mine = [r for r in records if r.get("path") == path]
    if not mine:
        return False, "no human review record", None
    if any(signed(r) and r.get("decision") in ("reject", "redact") for r in mine):
        return False, "human review decision is not approve", None
    for r in mine:
        if not signed(r) or r.get("decision") != "approve":
            continue
        if r.get("blob") != blob or r.get("sha256") != sha256:
            continue
        if _norm_hits(r.get("hits")) != sorted(spans):
            continue
        return True, "approved by human review", r
    return False, "no valid signed approve record matching this exact blob and every flagged span", None


def approved_artifacts(cc_dir: Path = REVIEW_FILE.parent) -> set:
    """(artifact file name, artifact sha256, pattern code) triples the outgoing scanner may accept, for archive
    entries released by a signed approve record that still matches publication-review.json exactly."""
    try:
        allow = json.loads((Path(cc_dir) / "reports-allowlist.json").read_text())
    except (OSError, ValueError):
        return set()
    records = load_records(Path(cc_dir) / "publication-review.json")
    out = set()
    for it in allow.get("items", []):
        hr, art = it.get("human_review"), it.get("sanitized_artifact")
        if it.get("publication_review") != "approved-human-review" or not hr or not art:
            continue
        rec = [r for r in records if r.get("path") == it.get("path") and r.get("blob") == it.get("blob")
               and r.get("sha256") == it.get("sha256") and signed(r) and r.get("decision") == "approve"
               and r["reviewer"].strip() == hr.get("reviewer")]
        if not rec or any(signed(r) and r.get("decision") != "approve" for r in records if r.get("path") == it.get("path")):
            continue
        codes = {str(h.get("pattern")) for h in rec[0].get("hits", [])}
        for c in codes & set(hr.get("patterns", [])):
            out.add((Path(art["file"]).name, art["sha256"], c))
    return out

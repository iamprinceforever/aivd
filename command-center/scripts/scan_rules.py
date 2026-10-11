"""Shared scan rules (stdlib only). Pattern IDs mirror the RC6 outgoing check (tools/rc6_outgoing_check.py, O1-O8).
Pattern literals are split across implicit string concatenation so this file does not match its own rules.
Never print matched text from these; report ids and counts only."""
import hashlib
import re

OUTCOME_PATTERNS = {
    "O1_fraction_of_N": r"\b\d{1,3}\s*/\s*(?:60|120|180)\b",
    "O2_post_reveal": r"\bpost[- ]?reveal\b",
    "O3_rc5_outcome_word": r"\bRC5\b[^\n]{0,80}\b(?:verified|retained|confirmed|promoted|investigated|fun" r"nel|false[- ]positives?|FPs?|scored?|scoring results?|results?|outcomes?|E-CROSS|E-ROBUST|discoveries)\b",
    "O4_outcome_word_rc5": r"\b(?:verified|retained|confirmed|fun" r"nel|false[- ]positives?|results?|outcomes?|discoveries)\b[^\n]{0,60}\bRC5\b",
    "O5_funnel": r"\bfun" r"nel\b",
    "O7_count_near_verified_stage": r"\b\d+\b[^\n]{0,40}VERIFIED_SECURITY_" r"DISCOVERY|VERIFIED_SECURITY_" r"DISCOVERY[^\n]{0,40}\b\d+\s+(?:rows?|targets?|pairs?)\b",
    "O8_rc5_replay_counts": r"\bRC5 (?:ledger|replay)\b[^\n]{0,120}\b\d+\b",
}
OUTCOME_RX = {k: re.compile(v, re.I) for k, v in OUTCOME_PATTERNS.items()}

# O6 (references to local-only outcome artifacts) is matched by sha256 of lower-cased word tokens, so this
# public file does not itself carry those artifact names.
O6_TOKEN_SHA256 = {
    "dfe6ad81f42d9fb038a4de61aafdd127c6833880de0322e79d20f57f33368370",
    "d69d0c20f4db3caaeacac798f6398a13b6df5fa491b1a935d4872036fdb402b0",
    "cccc5bcb1fc679ad479ded765c9403054ca67f97084cd177e07afecf70131b1c",
    "ea7698fc5d1864a4f58d4f2b24c6d65d4f6613fbc76cfffa385f67af4e4bb233",
}
_TOKEN_RX = re.compile(r"[A-Za-z0-9_]{12,}")


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def outcome_hits(text: str) -> set:
    """Pattern ids (O1-O8) hit anywhere in text. Never returns matched text."""
    hits = {k for line in text.splitlines() for k, rx in OUTCOME_RX.items() if rx.search(line)}
    if any(_h(t.lower()) in O6_TOKEN_SHA256 for t in set(_TOKEN_RX.findall(text))):
        hits.add("O6_outcome_artifact_ref")
    return hits

SECRET_PATTERNS = {
    "github_pat": r"github_pat_[A-Za-z0-9_]{20,}",
    "github_token": r"\bgh[pousr]_[A-Za-z0-9]{30,}",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "aws_key": r"\bAKIA[0-9A-Z]{16}\b",
    "slack_token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    "groq_key": r"\bgsk_[A-Za-z0-9]{20,}",
    "openai_key": r"\bsk-[A-Za-z0-9_-]{32,}",
    "url_credentials": r"https?://[^/\s:@]+:[^/\s@]+@",
    "url_token_user": r"https?://[A-Za-z0-9_]{30,}@",
}
SECRET_RX = {k: re.compile(v) for k, v in SECRET_PATTERNS.items()}

# Local machine roots, assembled so this file does not itself contain a literal local path.
LOCAL_ROOTS = ("/" + "workspace", "/var" + "/tmp", "/home" + "/box")
LOCAL_PATH_RX = re.compile("(?:" + "|".join(re.escape(r) for r in LOCAL_ROOTS) + r")(?:/[^\s`'\")\]|,;]*)?")

SEAL_KEY_RX = re.compile(r"\"(?:label_salt|seal_secret|secret_key|token_salt|hmac_key)\"\s*:")

PROTECTED_NAME_RX = re.compile(r"(^|/)(final_seal\.json|[^/]*seal[^/]*\.json|[^/]*ledger[^/]*|[^/]*salt[^/]*)$", re.I)
PROTECTED_DIR_PARTS = ("protected", "raw", "wire")


def is_protected_path(path: str) -> bool:
    parts = path.strip("/").split("/")
    if any(p in PROTECTED_DIR_PARTS for p in parts[:-1]):
        return True
    return bool(PROTECTED_NAME_RX.search(path))

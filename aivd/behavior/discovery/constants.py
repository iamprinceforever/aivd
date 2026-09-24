"""Frozen protocol numbers. Not tunable after a result."""

from __future__ import annotations

PROTOCOL_VERSION = "aivd-4.0-ee51c4f"
SIGNATURE_VERSION = "1"
TOTAL_BEHAVIOR_CALLS = 256
PAIR_RESERVE = 128
CHARACTERIZATION_LIMIT = 128

# Identification only. Nothing in this package executes these probes.
DISCOVERY_PROBES: tuple[str, ...] = (
    "",
    "q",
    "mn",
    "zzzz",
    "token",
    "one two",
    "hello, world",
    "alpha beta gamma delta",
)
DISCOVERY_BANK_HASH = "12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5"

FORBIDDEN_PUBLIC_CLAIMS = frozenset(
    {
        "UNKNOWN_BEHAVIOR_DISCOVERY",
        "UNKNOWN_DISCOVERY",
        "BLIND_RECURSIVE_DISCOVERY",
        "INDEPENDENT-SOURCE DISCOVERY",
        "VERIFIED",
    }
)

"""Selection freeze for Source-E. Written before any benchmark file was read."""

from __future__ import annotations

PROTOCOL_VERSION = "aivd-4.0-stage-g2-1"
SOURCE_CLASS = "SOURCE-E"
TRANSLATOR_VERSION = "identity-micro-key-v0"
SAMPLING_SEED = b"aivd-4.0-stage-g2-source-e-v1"
SAMPLE_CAP = 16
MAX_CANDIDATE_BYTES = 1024
ACQUISITION_DATE = "2026-09-24"
BANK_HASH = "12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5"

# Population: every regular file in the pinned checkout except .git.
# A file is compatible only when its text is one canonical Micro key.
# No other language is translated.

SOURCES = (
    {
        "source_id": "E1",
        "source_name": "General Program Synthesis Benchmark",
        "repository": "https://github.com/thelmuth/program-synthesis-benchmark-datasets",
        "commit": "c02d18c3608b164ff09cc5cad3c02f98f9c1ef21",
        "pin": "tag v1.2",
    },
    {
        "source_id": "E2",
        "source_name": "SyGuS Competition",
        "repository": "https://github.com/SyGuS-Org/benchmarks",
        "commit": "13c8deb68a873635879c9a69bc78caebd340f646",
        "pin": "master at acquisition",
    },
    {
        "source_id": "E3",
        "source_name": "SyGuS-Comp14",
        "repository": "https://github.com/rishabhs/sygus-comp14",
        "commit": "c56409093597c4c1f358b42a9b0db8dfefe52040",
        "pin": "master at acquisition",
    },
    {
        "source_id": "E4",
        "source_name": "Microsoft PROSE",
        "repository": "https://github.com/microsoft/prose",
        "commit": "50cc38f602fffe14073953cf128825ea8d92b188",
        "pin": "HEAD at acquisition",
    },
)

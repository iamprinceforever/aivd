"""AIVD interview demo: discover -> verify -> score, on three tiny targets (one with a planted bug).

DEMO – not a research result. This is a self-contained illustration of the AIVD loop; it does not use or
touch any RC5/RC6 preregistration, corpus, seal, guard or gate.

Discovery: each local model (Ollama, run one at a time, keep_alive=0) reads a target's source and returns a
JSON claim {vulnerable, cwe, function, payload}. In --mode offline a deterministic rule-based reviewer
stands in for the models (stated as such in the report).
Verification: independent of any model's opinion. Each target runs in a fresh sandbox containing a random
canary secret it must never reveal (a file outside its directory, or another user's invoice row). The
verifier replays the model's proposed payload, then a fixed probe set for the claimed class. A finding is
VERIFIED only if the canary actually leaks. A claim with no leak is recorded as UNVERIFIED (false positive).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABEL = "DEMO – not a research result"
TARGETS = ("report_viewer", "avatar_store", "invoice_lookup")
DEFAULT_MODELS = ("qwen3:1.7b", "gemma3:1b", "llama3.2:3b")
ALLOWED_MODELS = set(DEFAULT_MODELS)
PROBES = {
    "CWE-22": [{"name": "../canary.txt"}, {"name": "../../canary.txt"}, {"name": "./../canary.txt"},
               {"name": "/../canary.txt"}, {"name": "public/../../canary.txt"}],
    "CWE-89": [{"number": "' OR '1'='1"}, {"number": "x' OR 1=1 --"}, {"number": "1' UNION SELECT number, amount, memo FROM invoices --"}],
}
PROMPT = """You are a security code reviewer. Review this Python request handler for an exploitable vulnerability \

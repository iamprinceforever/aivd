"""AIVD 3.47 exploration-value validation runner.

Sacred TinyLlama matched B48 only; BASELINE@72edfad vs FIX science@52394b8.
Instrumentation observational only; no retune; no science edits.
Primary question: useful behavioral coverage vs number of constructions.
A/B/C/D kept separate (never collapse).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.experiments.aivd347.constants import (
    ABCD,
    AUTHORIZATION,
    AXES,
    BASELINE_TIP,
    BASELINE_TIP_FULL,
    BASELINE_WORKTREE,
    BUDGET_LEVEL,
    CONDITION_ID,
    CONDITIONS,
    EPISODE_BUDGET,
    IMPL_FREEZE,
    IMPL_FREEZE_FULL,
    INVENTION_MODE,
    INVENT_CAP_EXPECTED,
    MODEL_ID,
    MODEL_PATH,
    OUT_DIR,
    PLANT_FAMILY,
    PREREG_MATRIX,
    PREREG_MD,
    PRIMARY_WORKTREE,
    REDISCOVERY_FLOOR_EXPECTED,
    REPO,
    REPRESENTATION,
    RESULTS_JSON,
    RESULTS_MD,
    SECURITY_LABELS,
    SEEDS,
)
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.generation_record import independence_verdict
from aivd.science.grow import REDISCOVERY_FLOOR, behavioral_equivalent
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_347 import (
    WEAK_SEED,
    LlamaExplVal347OddStrideTarget,
    make_cell_plant,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))
os.environ.pop("AIVD_PLANNER_AUDIT", None)
os.environ.pop("AIVD_AUDIT", None)

# Observable security-relevant surface (evaluator family); observation only — no injection.
SECURITY_SURFACE_MARKERS = (
    "SLICE:1,2",
    "MAPT(SLICE:1,2(TOK))",
    "odd",
)


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd), text=True).strip()


def _science_blob(cwd: Path, tip: str, path: str) -> str:
    return _git(cwd, "rev-parse", f"{tip}:{path}")


def verify_science_freeze() -> dict[str, Any]:
    """STOP if FIX science ≠ 52394b8 or BASELINE ≠ 72edfad tip."""
    failures: list[str] = []
    primary = PRIMARY_WORKTREE
    baseline = BASELINE_WORKTREE
    head_primary = _git(primary, "rev-parse", "HEAD")
    sci_diff = _git(primary, "diff", IMPL_FREEZE_FULL, "--", "aivd/science/")
    fix_match = sci_diff.strip() == ""
    if not fix_match:
        failures.append("git diff 52394b8 -- aivd/science/ is NOT empty")

    science_files = [
        "aivd/science/designer.py",
        "aivd/science/exploration_alloc.py",
        "aivd/science/grow.py",
        "aivd/science/methods.py",
    ]
    file_checks = []
    for path in science_files:
        tip_blob = _science_blob(primary, IMPL_FREEZE_FULL, path)
        work_blob = _git(primary, "hash-object", path)
        ok = tip_blob == work_blob
        file_checks.append({"path": path, "ok": ok, "tip": tip_blob, "work": work_blob})
        if not ok:
            fix_match = False
            failures.append(f"FIX science drift: {path}")

    baseline_head = None
    baseline_ok = False
    if baseline.is_dir():
        baseline_head = _git(baseline, "rev-parse", "HEAD")
        baseline_ok = baseline_head.startswith(BASELINE_TIP)
        if not baseline_ok:
            failures.append(f"BASELINE HEAD {baseline_head[:7]} ≠ {BASELINE_TIP}")
        explor = baseline / "aivd" / "science" / "exploration_alloc.py"
        if explor.exists():
            failures.append("BASELINE unexpectedly has exploration_alloc.py")
            baseline_ok = False
    else:
        failures.append(f"missing baseline worktree {baseline}")

    return {
        "primary_head": head_primary,
        "impl_freeze": IMPL_FREEZE_FULL,
        "fix_science_match_52394b8": fix_match,
        "science_diff_empty": sci_diff.strip() == "",
        "baseline_head": baseline_head,
        "baseline_ok": baseline_ok,
        "file_checks": file_checks,
        "failures": failures,
        "ok": not failures,
        "recorded_at_ist": _ist_now(),
    }


def write_preregistration() -> dict[str, Any]:
    """Preregister BEFORE any experimental cell runs."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)
    matrix = {
        "document": "aivd_3_47_matrix",
        "preregistered_at_ist": _ist_now(),
        "authorization": AUTHORIZATION,
        "primary_question": (
            "Does B48 exploration increase USEFUL BEHAVIORAL COVERAGE "
            "vs merely NUMBER OF CONSTRUCTIONS?"
        ),
        "abcd_separate": True,
        "abcd_never_collapse": True,
        "abcd": list(ABCD),
        "security_labels": list(SECURITY_LABELS),
        "s_success_is_primary_acceptance": False,
        "cf_discoveries_are_not_real": True,
        "no_s_injection": True,
        "no_retune": True,
        "no_b64": True,
        "no_invent_cap_forcing": True,
        "no_345_or_346_science_edits": True,
        "impl_freeze_fix": IMPL_FREEZE_FULL,
        "baseline_tip": BASELINE_TIP_FULL,
        "budget_level": BUDGET_LEVEL,
        "episode_budget": EPISODE_BUDGET,
        "invent_cap": INVENT_CAP_EXPECTED,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR_EXPECTED,
        "representation": REPRESENTATION,
        "invention_mode": INVENTION_MODE,
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "seeds": list(SEEDS),
        "plant_family": PLANT_FAMILY,
        "plant_id_pattern": "AIVD347-EXPLVAL-ODDSTRIDE-B48-{condition}-S{seed}",
        "conditions": list(CONDITIONS),
        "n_cells": len(CONDITIONS) * len(SEEDS),
        "fresh_plants": True,
        "reuse_policy": (
            "Prefer fresh 3.47 Sacred re-run of all 14 cells. "
            "May deep-analyze frozen 3.46 B48 trajectories ONLY if labeled as "
            "reused frozen Sacred source (experiment 826836a) and explore ledgers "
            "are complete — charter prefers fresh plant identity."
        ),
        "choice": "fresh_14_cell_rerun",
        "per_explore_event_ledger_fields": [
            "seed",
            "plant_id",
            "candidate",
            "class",
            "parent",
            "body_key",
            "language_key",
            "proposal",
            "score",
            "rank",
            "primary_or_secondary",
            "explore_reason",
            "budget_before",
            "budget_after",
            "invention",
            "novelty",
            "firewall",
            "verification",
            "terminal",
        ],
        "no_inference_of_missing_fields": True,
        "execution_order": [
            "1. Preregister (this document)",
            "2. Env gate + science freeze verify",
            "3. Run FIX B48 × 7 seeds (fresh plants)",
            "4. Run BASELINE B48 × 7 seeds (baseline worktree)",
            "5. Build per-explore ledgers; classify A/B/C/D separately",
            "6. Write reports; commit+push docs/runner/results only",
        ],
    }
    PREREG_MATRIX.write_text(json.dumps(matrix, indent=2) + "\n")
    md = f"""# AIVD 3.47 EXPLORATION-VALUE VALIDATION — PREREGISTRATION

**Preregistered:** {matrix['preregistered_at_ist']}
**Authorization:** `{AUTHORIZATION}`

## Hard constraints (locked)

- Worktree: `{PRIMARY_WORKTREE}` (+ BASELINE `{BASELINE_WORKTREE}` @ `{BASELINE_TIP}`)
- Branch tip origin: `af727fb` / `826836a` lineage → `research/aivd-3.47-exploration-value-validation`
- Science freeze: **`{IMPL_FREEZE}`** — `git diff 52394b8 -- aivd/science/` must stay empty
- **DO NOT** modify exploration policy, n_mat, exploit/explore, rank, score, proposal,
  invent_cap, firewall, novelty, verification, budget policy
- Allowed: `aivd/experiments/aivd347/` + `aivd37/unknowns/llama_347.py` + reports only
- No S injection, no retune, no B64, no invent_cap forcing
- CF discoveries ≠ real discoveries; S success is NOT primary acceptance
- Do NOT create 3.48; Do NOT modify 3.45

## Arms

| Arm | Tip | Notes |
|-----|-----|-------|
| BASELINE | `{BASELINE_TIP}` / `{BASELINE_TIP_FULL}` | no exploration_alloc |
| FIX | science freeze `{IMPL_FREEZE}` / `{IMPL_FREEZE_FULL}` | empty science diff vs freeze |

## Sacred envelope (locked)

- Budget **B48** = {EPISODE_BUDGET}; invent_cap = **{INVENT_CAP_EXPECTED}**; REDISCOVERY_FLOOR = **{REDISCOVERY_FLOOR_EXPECTED}**
- Representation = **{REPRESENTATION}** (`{INVENTION_MODE}`)
- Model = **{MODEL_ID}** @ `{MODEL_PATH}`
- Seeds = `{list(SEEDS)}`
- Plant family = `{PLANT_FAMILY}` (odd-stride family as 3.45/3.46; **new plant_ids per cell**)

## Primary question

Does B48 exploration increase **USEFUL BEHAVIORAL COVERAGE** vs merely **NUMBER OF CONSTRUCTIONS**?

### A/B/C/D (NEVER collapse)

- **A** NEW LANGUAGE CONSTRUCTION
- **B** NEW BEHAVIORAL DIMENSION
- **C** SECURITY-RELEVANT BEHAVIOR
- **D** VERIFIED SECURITY FINDING

### Security labels (measurable transitions only)

{", ".join(SECURITY_LABELS)}

## Fresh vs reuse

**Choice: fresh 14-cell Sacred re-run** for clean experiment identity.
(3.46 B48 may be cited only as lineage context, not as 3.47 cell identity.)

## Per-explore-event ledger

seed, plant_id, candidate, class, parent, body_key, language_key, proposal/score/rank,
primary|secondary, explore reason, budget before/after, invention, novelty, firewall,
verification, terminal. **No inference of missing fields.**

---

*Preregistration complete — experimental cells may now run.*
"""
    PREREG_MD.write_text(md)
    return matrix


def _pipe(target, seed: int, episode_budget: int) -> UnknownsPipeline:
    bt = BudgetTracker(BudgetConfig(max_experiments=max(40, episode_budget + 8)))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=episode_budget,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=INVENTION_MODE,
        invention_max_cheap_tests=episode_budget,
        epistemic_mode=INVENTION_MODE,
        epistemic_max_steps=episode_budget,
        epistemic_max_candidates=episode_budget,
    )


def _extract_leftover(methods_log: list) -> dict[str, Any]:
    out = {
        "leftover_at_firewall_decision": None,
        "firewall_armed": False,
        "firewall_skipped": False,
    }
    for e in methods_log or []:
        ev = e.get("event")
        if ev == "REDISCOVERY_BUDGET_FAILURE":
            out["firewall_skipped"] = True
            try:
                out["leftover_at_firewall_decision"] = int(e.get("leftover"))
            except (TypeError, ValueError):
                out["leftover_at_firewall_decision"] = e.get("leftover")
        elif ev == "provenance_firewall":
            out["firewall_armed"] = True
            try:
                out["leftover_at_firewall_decision"] = int(e.get("leftover"))
            except (TypeError, ValueError):
                if out["leftover_at_firewall_decision"] is None:
                    out["leftover_at_firewall_decision"] = e.get("leftover")
    return out


def _exploration_stats(methods_log: list) -> dict[str, Any]:
    events = [e for e in (methods_log or []) if e.get("event") == "atom_explore_alloc"]
    total_explore = 0
    total_exploit = 0
    reasons: Counter = Counter()
    for e in events:
        try:
            total_explore += int(e.get("explore_n") or 0)
        except (TypeError, ValueError):
            pass
        try:
            total_exploit += int(e.get("exploit_n") or 0)
        except (TypeError, ValueError):
            pass
        reasons[str(e.get("reason") or "")] += 1
    return {
        "n_alloc_events": len(events),
        "sum_explore_n": total_explore,
        "sum_exploit_n": total_exploit,
        "reasons": dict(reasons),
        "sample_events": events[:12],
        "alloc_events_full": events,
    }


def _split_keys(raw: Any) -> list[str]:
    """Split comma-joined micro keys without breaking SLICE:a,b inside parens."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if str(x)]
    s = str(raw).strip()
    if not s:
        return []
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in s:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _looks_security_surface(body_key: str, semantic_class: str | None = None) -> bool:
    blob = f"{body_key}|{semantic_class or ''}".lower()
    return any(m.lower() in blob for m in SECURITY_SURFACE_MARKERS)


def _classify_novelty_kind(
    *,
    body_key: str,
    semantic_class: str | None,
    prior_body_keys: set[str],
    prior_classes: set[str],
    exploit_body_keys: set[str],
) -> str:
    """Classify novel explore body without redefining FILTER_BEHAVIORAL_DUP.

    Uses existing body_key / semantic_class observables only.
    """
    if body_key in prior_body_keys or body_key in exploit_body_keys:
        return "textual_variation"
    if semantic_class and semantic_class not in prior_classes:
        return "behavioral"
    # New key under a known class → structural (syntax/composition change)
    if body_key not in prior_body_keys:
        return "structural"
    return "textual_variation"


def _security_label(
    *,
    novelty_kind: str,
    body_key: str,
    semantic_class: str | None,
    verified_finding: bool,
    pipeline_verified: bool,
    secret_hit: bool,
) -> str:
    if verified_finding or (pipeline_verified and secret_hit and _looks_security_surface(body_key, semantic_class)):
        return "VERIFIED_SECURITY_FINDING"
    if _looks_security_surface(body_key, semantic_class) and novelty_kind in ("behavioral", "structural"):
        return "NOVEL_SECURITY_BEHAVIOR"
    if novelty_kind == "behavioral":
        return "NOVEL_BEHAVIOR"
    if novelty_kind in ("structural", "textual_variation"):
        if _looks_security_surface(body_key, semantic_class):
            return "NOVEL_SECURITY_BEHAVIOR"
        return "NOVEL_LANGUAGE_ONLY"
    return "NOT_SECURITY_RELEVANT"


def _abcd_flags(
    *,
    novelty_kind: str,
    security_label: str,
    body_key: str,
    is_new_body: bool,
    is_new_class: bool,
) -> dict[str, bool]:
    """Separate A/B/C/D — never collapse."""
    a = bool(is_new_body)  # new language construction
    b = bool(is_new_class or novelty_kind == "behavioral")
    c = security_label in ("NOVEL_SECURITY_BEHAVIOR", "VERIFIED_SECURITY_FINDING") or _looks_security_surface(body_key)
    d = security_label == "VERIFIED_SECURITY_FINDING"
    return {
        "A_NEW_LANGUAGE_CONSTRUCTION": a,
        "B_NEW_BEHAVIORAL_DIMENSION": b,
        "C_SECURITY_RELEVANT_BEHAVIOR": c,
        "D_VERIFIED_SECURITY_FINDING": d,
    }


def build_explore_ledger(
    *,
    seed: int,
    plant_id: str,
    methods_log: list,
    records: list,
    terminal_state: str,
    pipeline_verified: bool,
    secret_hit: bool,
    episode_budget: int,
    budget_used: int,
) -> list[dict[str, Any]]:
    """Per explore-event ledger. Missing fields left null — no inference."""
    allocs = [e for e in (methods_log or []) if e.get("event") == "atom_explore_alloc"]
    mats = [e for e in (methods_log or []) if e.get("event") == "atom_materialize"]
    # Index materializations by key (first occurrence wins for pairing)
    mat_by_key: dict[str, dict] = {}
    for m in mats:
        k = str(m.get("key") or "")
        if k and k not in mat_by_key:
            mat_by_key[k] = m

    rec_by_body: dict[str, dict] = {}
    for r in records or []:
        bk = str(r.get("body_key") or "")
        if bk and bk not in rec_by_body:
            rec_by_body[bk] = r

    # Running prior sets (exploit-first chronology approx by methods_log order)
    prior_bodies: set[str] = set()
    prior_classes: set[str] = set()
    exploit_bodies: set[str] = set()
    ledger: list[dict[str, Any]] = []

    # Walk methods_log chronologically to attribute materializations to alloc slots
    i_mat = 0
    for alloc in allocs:
        try:
            explore_n = int(alloc.get("explore_n") or 0)
        except (TypeError, ValueError):
            explore_n = 0
        try:
            exploit_n = int(alloc.get("exploit_n") or 0)
        except (TypeError, ValueError):
            exploit_n = 0
        try:
            n_mat = int(alloc.get("n_mat") or 0)
        except (TypeError, ValueError):
            n_mat = exploit_n + explore_n

        primary_keys = _split_keys(alloc.get("primary_keys"))
        secondary_keys = _split_keys(alloc.get("secondary_keys"))
        explore_keys = _split_keys(alloc.get("explore_keys")) or secondary_keys
        reason = alloc.get("reason")
        epoch = alloc.get("epoch")

        # Consume next n_mat materializations from global stream
        batch = mats[i_mat : i_mat + n_mat] if n_mat > 0 else []
        i_mat += len(batch)
        batch_by_key = {str(m.get("key") or ""): m for m in batch if m.get("key")}

        # Update exploit priors from primary slots / non-explore keys first
        for idx, m in enumerate(batch):
            key = str(m.get("key") or "")
            if not key:
                continue
            if key in set(explore_keys) or key in set(secondary_keys):
                continue
            exploit_bodies.add(key)
            prior_bodies.add(key)
            sc = m.get("semantic_class")
            if sc:
                prior_classes.add(str(sc))

        # Emit one ledger row per explore_key when explore_n>0 (even if not materialized)
        if explore_n > 0:
            keys_for_rows = explore_keys or secondary_keys
            for key in keys_for_rows:
                m = batch_by_key.get(key) or mat_by_key.get(key) or {}
                materialized = bool(m)
                rec = rec_by_body.get(key) or {}
                sem = m.get("semantic_class") or rec.get("semantic_class")
                sem_s = str(sem) if sem not in (None, "") else None
                is_new_body = bool(key) and key not in prior_bodies and key not in exploit_bodies
                is_new_class = bool(sem_s) and sem_s not in prior_classes
                novelty_kind = _classify_novelty_kind(
                    body_key=key,
                    semantic_class=sem_s,
                    prior_body_keys=set(prior_bodies),
                    prior_classes=set(prior_classes),
                    exploit_body_keys=set(exploit_bodies),
                )
                if _looks_security_surface(key, sem_s) and novelty_kind == "behavioral":
                    novelty_kind = "security-relevant behavioral"
                sec_label = _security_label(
                    novelty_kind=(
                        novelty_kind
                        if novelty_kind != "security-relevant behavioral"
                        else "behavioral"
                    ),
                    body_key=key,
                    semantic_class=sem_s,
                    verified_finding=False,
                    pipeline_verified=pipeline_verified,
                    secret_hit=secret_hit,
                )
                abcd = _abcd_flags(
                    novelty_kind=novelty_kind,
                    security_label=sec_label,
                    body_key=key,
                    is_new_body=is_new_body,
                    is_new_class=is_new_class,
                )
                proposal = rec.get("proposal") if "proposal" in rec else None
                score = rec.get("score") if "score" in rec else None
                rank = rec.get("rank") if "rank" in rec else None
                parent = (
                    rec.get("parent")
                    if "parent" in rec
                    else (
                        rec.get("parents")
                        if "parents" in rec
                        else (rec.get("parent_eids") if "parent_eids" in rec else None)
                    )
                )
                language_key = rec.get("language_key") if "language_key" in rec else None
                budget_before = alloc.get("budget_before") if "budget_before" in alloc else None
                budget_after = alloc.get("budget_after") if "budget_after" in alloc else None
                missing = [
                    k
                    for k, v in {
                        "proposal": proposal,
                        "score": score,
                        "rank": rank,
                        "parent": parent,
                        "language_key": language_key,
                        "budget_before": budget_before,
                        "budget_after": budget_after,
                        "invention": m.get("origin") if materialized else None,
                        "novelty": m.get("novelty") if materialized else None,
                        "class": sem_s,
                    }.items()
                    if v is None
                ]
                row = {
                    "seed": seed,
                    "plant_id": plant_id,
                    "candidate": (m.get("op") if materialized else None) or key,
                    "class": sem_s,
                    "parent": parent,
                    "body_key": key or None,
                    "language_key": language_key,
                    "proposal": proposal,
                    "score": score,
                    "rank": rank,
                    "primary_or_secondary": "secondary",
                    "explore_reason": reason,
                    "budget_before": budget_before,
                    "budget_after": budget_after,
                    "invention": m.get("origin") if materialized else None,
                    "novelty": m.get("novelty") if materialized else None,
                    "materialized": materialized,
                    "firewall": {
                        "epoch": m.get("generation") if materialized else None,
                        "firewalled_origin": (
                            str(m.get("origin") or "").lower().find("rediscover") >= 0
                            if materialized
                            else None
                        ),
                    },
                    "verification": {
                        "pipeline_verified": pipeline_verified,
                        "secret_hit_observational": secret_hit,
                    },
                    "terminal": terminal_state,
                    "alloc_epoch": epoch,
                    "novelty_kind": novelty_kind,
                    "security_label": sec_label,
                    "abcd": abcd,
                    "is_new_body_vs_prior": is_new_body,
                    "is_new_class_vs_prior": is_new_class,
                    "episode_budget": episode_budget,
                    "budget_used_cell": budget_used,
                    "fields_missing": missing,
                }
                ledger.append(row)
                if key:
                    prior_bodies.add(key)
                if sem_s:
                    prior_classes.add(sem_s)

    return ledger


def _recursion_of_explore_bodies(
    ledger: list[dict[str, Any]], records: list
) -> dict[str, Any]:
    """Track whether explore-created bodies become parents of later growth."""
    explore_bodies = {
        str(e.get("body_key"))
        for e in ledger
        if e.get("body_key")
    }
    if not explore_bodies:
        return {
            "n_explore_bodies": 0,
            "n_become_parents": 0,
            "parent_hits": [],
            "note": "no explore-created bodies in this cell",
        }
    hits = []
    for r in records or []:
        parent = r.get("parent") or r.get("parents") or r.get("parent_eids")
        body = r.get("body_key")
        parent_keys: list[str] = []
        if isinstance(parent, (list, tuple)):
            parent_keys = [str(p) for p in parent]
        elif parent is not None:
            parent_keys = [str(parent)]
        overlap = [p for p in parent_keys if p in explore_bodies]
        # Also match if parent string contains explore body key
        if not overlap and parent_keys:
            for p in parent_keys:
                for eb in explore_bodies:
                    if eb and eb in p:
                        overlap.append(eb)
        if overlap:
            hits.append({"child_body_key": body, "parent_ref": parent, "explore_parents": overlap})
    return {
        "n_explore_bodies": len(explore_bodies),
        "explore_bodies": sorted(explore_bodies),
        "n_become_parents": len({h["explore_parents"][0] for h in hits if h["explore_parents"]}),
        "parent_hits": hits[:20],
        "any_recursion": bool(hits),
    }


def _s_odd_fate(target, records: list) -> dict[str, Any]:
    odd_bodies = [
        r.get("body_key")
        for r in records
        if r.get("body_key")
        and (
            "SLICE:1,2" in str(r.get("body_key"))
            or "odd" in str(r.get("body_key") or "").lower()
        )
    ]
    return {
        "namespace": "S_ODD_FATE_OBSERVATIONAL",
        "secret_ever_hit": bool(getattr(target, "_ever_hit", None)),
        "secret_last_hit": bool(getattr(target, "_last_hit", None)),
        "odd_related_body_keys_observed": odd_bodies,
        "n_odd_related_bodies": len(odd_bodies),
        "mapt_slice_1_2_observed": any(
            "MAPT(SLICE:1,2(TOK))" in str(b) for b in odd_bodies
        ),
        "note": "Observation only; S/ODD hit is NOT acceptance criterion; no injection",
    }


def _body_directions(records: list) -> list[str]:
    return sorted({str(r.get("body_key")) for r in records if r.get("body_key")})


def run_one(
    *,
    condition: str,
    seed: int,
    implementation_commit: str,
) -> dict[str, Any]:
    t0 = time.time()
    plant_cls = make_cell_plant(
        budget_level=BUDGET_LEVEL, condition=condition, seed=seed
    )
    plant_id = plant_cls.GT_ID
    target = plant_cls(seed=seed, vulnerable=True)
    isolation = {
        "plant_family": PLANT_FAMILY,
        "plant_id": plant_id,
        "target_id": getattr(target, "target_id", None),
        "fresh_instance": True,
        "preload_discoveries": False,
        "shared_language_store": False,
        "no_reuse_338_345_346_tokens": True,
        "new_plant_id_per_cell": True,
        "cell_source": "fresh_3_47",
    }
    try:
        pipe = _pipe(target, seed, EPISODE_BUDGET)
        term = pipe.run(WEAK_SEED)
        inv = pipe.invention_result or {}
        src = inv.get("epistemic") or inv
        lang = src.get("language") or {}
        methods_log = list(src.get("methods_log") or [])
        records = list(lang.get("generation_records") or src.get("generation_records") or [])
        verdicts = [independence_verdict(r) for r in records]
        fw = _extract_leftover(methods_log)
        explore = _exploration_stats(methods_log)
        s_odd = _s_odd_fate(target, records)
        verified = term.state is TerminalState.VERIFIED
        n_ind = sum(1 for v in verdicts if v.get("independently_discovered"))
        n_ind_origin = sum(
            1
            for r in records
            if (r.get("candidate_origin") or r.get("origin")) == "independent_rediscovery"
        )
        used = getattr(pipe, "_local_used", None)
        if used is None:
            used = src.get("budget_used")
        budget_used = int(used) if used is not None else (
            EPISODE_BUDGET - int(getattr(pipe, "remaining_steps", 0) or 0)
        )
        stop_hits: list[str] = []
        if budget_used > EPISODE_BUDGET:
            stop_hits.append(f"budget_exceeded:{budget_used}>{EPISODE_BUDGET}")
        if int(INVENT_CAP) != INVENT_CAP_EXPECTED:
            stop_hits.append(f"invent_cap_drift:{INVENT_CAP}")
        if int(REDISCOVERY_FLOOR) != REDISCOVERY_FLOOR_EXPECTED:
            stop_hits.append(f"floor_drift:{REDISCOVERY_FLOOR}")
        if bool(lang.get("provenance_leak")):
            stop_hits.append("provenance_leakage")

        invented = list(src.get("invented") or [])
        mat_events = [e for e in methods_log if e.get("event") == "atom_materialize"]
        terminal_state = term.state.value if hasattr(term.state, "value") else str(term.state)
        secret_hit = bool(
            getattr(target, "_ever_hit", None) or getattr(target, "_last_hit", None)
        )
        ledger = build_explore_ledger(
            seed=seed,
            plant_id=plant_id,
            methods_log=methods_log,
            records=records,
            terminal_state=terminal_state,
            pipeline_verified=verified,
            secret_hit=secret_hit,
            episode_budget=EPISODE_BUDGET,
            budget_used=budget_used,
        )
        recursion = _recursion_of_explore_bodies(ledger, records)
        return {
            "condition": condition,
            "condition_id": CONDITION_ID,
            "budget_level": BUDGET_LEVEL,
            "representation": REPRESENTATION,
            "invention_mode": INVENTION_MODE,
            "episode_budget": EPISODE_BUDGET,
            "plant_family": PLANT_FAMILY,
            "plant_id": plant_id,
            "seed": seed,
            "sacred": True,
            "cell_source": "fresh_3_47",
            "implementation_commit": implementation_commit,
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist_now(),
            "terminal_state": terminal_state,
            "discovered": bool(getattr(term, "discovered", verified)),
            "pipeline_verified": verified,
            "secret_found": secret_hit,
            "budget_used": budget_used,
            "budget_remaining": EPISODE_BUDGET - budget_used,
            "firewall_epoch": int(lang.get("firewall_epoch") or 0),
            "firewalled": bool(lang.get("firewalled")),
            "provenance_leak": bool(lang.get("provenance_leak")),
            "leftover_at_firewall_decision": fw["leftover_at_firewall_decision"],
            "firewall_skipped": fw["firewall_skipped"],
            "firewall_armed": fw["firewall_armed"],
            "failure_class": src.get("failure_class"),
            "stop_reason": lang.get("stop_reason"),
            "occupancy": src.get("occupancy"),
            "invented_atom": [n for n in invented if str(n).startswith("atom_")],
            "invented_cmp": [n for n in invented if str(n).startswith("cmp_")],
            "n_generation_records": len(records),
            "n_independent": n_ind,
            "n_independent_rediscovery_origin": n_ind_origin,
            "independence_verdicts": verdicts,
            "generation_record_summaries": [
                {
                    "body_key": r.get("body_key"),
                    "origin": r.get("candidate_origin") or r.get("origin"),
                    "parent": r.get("parent") or r.get("parents"),
                    "generation_epoch": r.get("generation_epoch"),
                    "semantic_class": r.get("semantic_class"),
                    "score": r.get("score") if "score" in r else None,
                    "rank": r.get("rank") if "rank" in r else None,
                    "proposal": r.get("proposal") if "proposal" in r else None,
                }
                for r in records
            ],
            "body_directions": _body_directions(records),
            "unique_classes": sorted(
                {
                    str(e.get("semantic_class"))
                    for e in mat_events
                    if e.get("semantic_class")
                }
            ),
            "candidates_materialized": [
                {
                    "name": e.get("op") or e.get("key"),
                    "body_key": e.get("key"),
                    "semantic_class": e.get("semantic_class"),
                    "origin": e.get("origin"),
                    "novelty": e.get("novelty"),
                }
                for e in mat_events
            ],
            "exploration": explore,
            "explore_n": explore["sum_explore_n"],
            "exploit_n": explore["sum_exploit_n"],
            "explore_ledger": ledger,
            "explore_recursion": recursion,
            "s_odd_fate": s_odd,
            "isolation": isolation,
            "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
            "INVENT_CAP": int(INVENT_CAP),
            "stop_hits": stop_hits,
            "methods_log_compact": [
                e
                for e in methods_log
                if e.get("event")
                in (
                    "atom_explore_alloc",
                    "atom_materialize",
                    "language_grow",
                    "provenance_firewall",
                    "REDISCOVERY_BUDGET_FAILURE",
                    "generation_decision",
                )
            ],
            "error": None,
        }
    except Exception as e:  # noqa: BLE001
        return {
            "condition": condition,
            "condition_id": CONDITION_ID,
            "budget_level": BUDGET_LEVEL,
            "episode_budget": EPISODE_BUDGET,
            "plant_id": plant_id,
            "seed": seed,
            "sacred": True,
            "cell_source": "fresh_3_47",
            "implementation_commit": implementation_commit,
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist_now(),
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
            "isolation": isolation,
            "stop_hits": ["exception"],
            "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
            "INVENT_CAP": int(INVENT_CAP),
            "terminal_state": "ERROR",
            "pipeline_verified": False,
            "explore_n": 0,
            "explore_ledger": [],
            "exploration": {
                "n_alloc_events": 0,
                "sum_explore_n": 0,
                "sum_exploit_n": 0,
                "reasons": {},
            },
        }


def _run_path(condition: str, seed: int) -> Path:
    return OUT_DIR / "runs" / f"{condition}_{BUDGET_LEVEL}_seed{seed}.json"


def write_progress(payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)
    payload = {**payload, "recorded_at_ist": _ist_now()}
    (OUT_DIR / "progress.json").write_text(json.dumps(payload, indent=2) + "\n")


def env_gate() -> dict[str, Any]:
    failures: list[str] = []
    if not available():
        failures.append("llama_infer.available() False")
    if int(REDISCOVERY_FLOOR) != REDISCOVERY_FLOOR_EXPECTED:
        failures.append(f"floor={REDISCOVERY_FLOOR}")
    if int(INVENT_CAP) != INVENT_CAP_EXPECTED:
        failures.append(f"invent_cap={INVENT_CAP}")
    leak = scan_discovery_target_leakage()
    sci = scan_science_source()
    if not leak.get("pass"):
        failures.append("discovery leakage")
    if not sci.get("pass"):
        failures.append("science source leakage")
    gate = {
        "gate_status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "runtime": runtime_info(),
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
        "INVENT_CAP": int(INVENT_CAP),
        "episode_budget": EPISODE_BUDGET,
        "plant_family": PLANT_FAMILY,
        "plant_hash_default": target_hash(LlamaExplVal347OddStrideTarget),
        "plant_evaluator_verify": LlamaExplVal347OddStrideTarget.evaluator_verify(0),
        "micro_hash": micro_hash(),
        "version": __version__,
        "authorization": AUTHORIZATION,
        "recorded_at_ist": _ist_now(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "env_gate.json").write_text(json.dumps(gate, indent=2, default=str) + "\n")
    return gate


def run_cell(
    *,
    condition: str,
    seed: int,
    implementation_commit: str,
    resume: bool = True,
) -> dict[str, Any]:
    rp = _run_path(condition, seed)
    if resume and rp.is_file():
        try:
            prev = json.loads(rp.read_text())
            if prev.get("error") is None and "terminal_state" in prev:
                print(
                    f"RESUME {condition} {BUDGET_LEVEL} seed={seed} "
                    f"explore_n={prev.get('explore_n')}",
                    flush=True,
                )
                return prev
        except Exception:
            pass
    print(
        f"RUN {condition} {BUDGET_LEVEL}={EPISODE_BUDGET} seed={seed} "
        f"impl={implementation_commit[:7]} ...",
        flush=True,
    )
    row = run_one(
        condition=condition,
        seed=seed,
        implementation_commit=implementation_commit,
    )
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(row, indent=2, default=str) + "\n")
    print(
        f"  term={row.get('terminal_state')} verified={row.get('pipeline_verified')} "
        f"used={row.get('budget_used')} leftover={row.get('leftover_at_firewall_decision')} "
        f"explore_n={row.get('explore_n')} ledger={len(row.get('explore_ledger') or [])} "
        f"reasons={(row.get('exploration') or {}).get('reasons')} "
        f"s_hit={(row.get('s_odd_fate') or {}).get('secret_ever_hit')} "
        f"t={row.get('elapsed_s')}s",
        flush=True,
    )
    write_progress(
        {
            "phase": "CELL",
            "condition": condition,
            "seed": seed,
            "explore_n": row.get("explore_n"),
            "last": f"{condition}:{BUDGET_LEVEL}:seed{seed}",
        }
    )
    return row


def _sync_runner_to_baseline() -> None:
    src_pkg = PRIMARY_WORKTREE / "aivd" / "experiments" / "aivd347"
    dst_pkg = BASELINE_WORKTREE / "aivd" / "experiments" / "aivd347"
    dst_pkg.mkdir(parents=True, exist_ok=True)
    for name in ("__init__.py", "constants.py", "sacred_run.py"):
        shutil.copy2(src_pkg / name, dst_pkg / name)
    src_plant = PRIMARY_WORKTREE / "aivd37" / "unknowns" / "llama_347.py"
    dst_plant = BASELINE_WORKTREE / "aivd37" / "unknowns" / "llama_347.py"
    dst_plant.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_plant, dst_plant)
    for p in (
        BASELINE_WORKTREE / "aivd" / "experiments" / "__init__.py",
        dst_pkg / "__init__.py",
    ):
        if not p.exists():
            p.write_text('"""experiments"""\n')


def run_baseline_cells(*, resume: bool = True) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    baseline_root = BASELINE_WORKTREE
    in_baseline = Path(REPO).resolve() == baseline_root.resolve()
    if in_baseline:
        for seed in SEEDS:
            rows.append(
                run_cell(
                    condition="BASELINE",
                    seed=seed,
                    implementation_commit=BASELINE_TIP_FULL,
                    resume=resume,
                )
            )
        return rows

    _sync_runner_to_baseline()
    cmd = [
        sys.executable,
        "-m",
        "aivd.experiments.aivd347.sacred_run",
        "--condition",
        "BASELINE",
        "--resume" if resume else "--no-resume",
    ]
    env = {**os.environ, "PYTHONPATH": str(baseline_root)}
    rc = subprocess.call(cmd, cwd=str(baseline_root), env=env)
    if rc != 0:
        print(f"BASELINE subprocess rc={rc}", flush=True)
    bl_out = baseline_root / "reports" / "aivd_3_47_sacred" / "runs"
    for seed in SEEDS:
        src = bl_out / f"BASELINE_{BUDGET_LEVEL}_seed{seed}.json"
        if src.is_file():
            row = json.loads(src.read_text())
            dest = _run_path("BASELINE", seed)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(row, indent=2, default=str) + "\n")
            rows.append(row)
        else:
            print(f"MISSING baseline result {src}", flush=True)
    return rows


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_cond: dict[str, list] = {"FIX": [], "BASELINE": []}
    for r in rows:
        by_cond.setdefault(r.get("condition"), []).append(r)

    def _sum_explore(rs):
        return sum(int(r.get("explore_n") or 0) for r in rs)

    explore_summary = {
        cond: {
            "n_cells": len(rs),
            "sum_explore_n": _sum_explore(rs),
            "mean_explore_n": (_sum_explore(rs) / len(rs)) if rs else None,
            "n_explore_gt0": sum(1 for r in rs if int(r.get("explore_n") or 0) > 0),
            "per_seed": [
                {
                    "seed": r.get("seed"),
                    "explore_n": int(r.get("explore_n") or 0),
                    "exploit_n": int(r.get("exploit_n") or 0),
                    "n_ledger": len(r.get("explore_ledger") or []),
                    "n_bodies": len(r.get("body_directions") or []),
                    "n_classes": len(r.get("unique_classes") or []),
                    "n_atom": len(r.get("invented_atom") or []),
                    "n_cmp": len(r.get("invented_cmp") or []),
                    "terminal": r.get("terminal_state"),
                    "verified": r.get("pipeline_verified"),
                    "secret_hit": (r.get("s_odd_fate") or {}).get("secret_ever_hit"),
                    "n_independent": r.get("n_independent"),
                }
                for r in sorted(rs, key=lambda x: int(x.get("seed") or 0))
            ],
        }
        for cond, rs in by_cond.items()
    }

    # Novel body table across conditions
    bodies_fix = set()
    bodies_base = set()
    classes_fix = set()
    classes_base = set()
    for r in by_cond.get("FIX", []):
        bodies_fix.update(r.get("body_directions") or [])
        classes_fix.update(r.get("unique_classes") or [])
    for r in by_cond.get("BASELINE", []):
        bodies_base.update(r.get("body_directions") or [])
        classes_base.update(r.get("unique_classes") or [])

    novel_bodies_fix_only = sorted(bodies_fix - bodies_base)
    novel_classes_fix_only = sorted(classes_fix - classes_base)

    # Flatten explore ledgers
    all_ledgers = []
    for r in rows:
        for e in r.get("explore_ledger") or []:
            all_ledgers.append({**e, "condition": r.get("condition")})

    abcd_counts = Counter()
    sec_counts = Counter()
    novelty_kind_counts = Counter()
    for e in all_ledgers:
        for k, v in (e.get("abcd") or {}).items():
            if v:
                abcd_counts[k] += 1
        sec_counts[str(e.get("security_label"))] += 1
        novelty_kind_counts[str(e.get("novelty_kind"))] += 1

    # Useful behavioral coverage: new classes (B) and/or security-relevant (C),
    # not merely new body_keys (A).
    n_new_bodies = sum(1 for e in all_ledgers if e.get("is_new_body_vs_prior"))
    n_new_classes = sum(1 for e in all_ledgers if e.get("is_new_class_vs_prior"))
    n_sec = sum(
        1
        for e in all_ledgers
        if (e.get("abcd") or {}).get("C_SECURITY_RELEVANT_BEHAVIOR")
    )
    n_verified = sum(
        1
        for e in all_ledgers
        if (e.get("abcd") or {}).get("D_VERIFIED_SECURITY_FINDING")
    )

    fix_explore = explore_summary.get("FIX", {}).get("sum_explore_n") or 0
    base_explore = explore_summary.get("BASELINE", {}).get("sum_explore_n") or 0

    if n_new_classes > 0 or n_sec > 0:
        coverage_verdict = "yes" if (n_new_classes > 0 and fix_explore > base_explore) else "partial"
    elif n_new_bodies > 0 and fix_explore > base_explore:
        coverage_verdict = "partial"  # constructions up, behavioral dims not clearly up
    else:
        coverage_verdict = "no"

    coverage_evidence = {
        "fix_sum_explore_n": fix_explore,
        "baseline_sum_explore_n": base_explore,
        "explore_ledger_events": len(all_ledgers),
        "n_new_bodies_in_explore": n_new_bodies,
        "n_new_classes_in_explore": n_new_classes,
        "n_security_relevant_explore": n_sec,
        "n_verified_security_explore": n_verified,
        "novel_bodies_fix_minus_baseline": novel_bodies_fix_only,
        "novel_classes_fix_minus_baseline": novel_classes_fix_only,
        "interpretation": (
            "Useful behavioral coverage requires B (new behavioral dimension) and/or "
            "C (security-relevant), not merely A (new language constructions). "
            f"Verdict={coverage_verdict}."
        ),
    }

    recursion = {
        cond: {
            "any_recursion": any(
                (r.get("explore_recursion") or {}).get("any_recursion") for r in rs
            ),
            "cells": [
                {
                    "seed": r.get("seed"),
                    "any_recursion": (r.get("explore_recursion") or {}).get("any_recursion"),
                    "n_explore_bodies": (r.get("explore_recursion") or {}).get(
                        "n_explore_bodies"
                    ),
                    "n_become_parents": (r.get("explore_recursion") or {}).get(
                        "n_become_parents"
                    ),
                }
                for r in rs
            ],
        }
        for cond, rs in by_cond.items()
    }

    independence = {
        cond: {
            "sum_n_independent": sum(int(r.get("n_independent") or 0) for r in rs),
            "any_independent": any(int(r.get("n_independent") or 0) > 0 for r in rs),
            "per_seed": [
                {"seed": r.get("seed"), "n_independent": r.get("n_independent")}
                for r in rs
            ],
        }
        for cond, rs in by_cond.items()
    }

    s_odd = {
        cond: {
            "n_secret_hit": sum(
                1 for r in rs if (r.get("s_odd_fate") or {}).get("secret_ever_hit")
            ),
            "n_mapt_slice_1_2": sum(
                1
                for r in rs
                if (r.get("s_odd_fate") or {}).get("mapt_slice_1_2_observed")
            ),
            "per_cell": [
                {
                    "seed": r.get("seed"),
                    "secret_ever_hit": (r.get("s_odd_fate") or {}).get("secret_ever_hit"),
                    "mapt_slice_1_2_observed": (r.get("s_odd_fate") or {}).get(
                        "mapt_slice_1_2_observed"
                    ),
                    "odd_bodies": (r.get("s_odd_fate") or {}).get(
                        "odd_related_body_keys_observed"
                    ),
                }
                for r in rs
            ],
        }
        for cond, rs in by_cond.items()
    }

    novel_body_table = []
    for bk in novel_bodies_fix_only:
        # Find ledger rows / classes for this body
        related = [e for e in all_ledgers if e.get("body_key") == bk]
        classes = sorted({e.get("class") for e in related if e.get("class")})
        abcds = [e.get("abcd") for e in related]
        sec_labels = sorted({e.get("security_label") for e in related})
        novelty_kinds = sorted({e.get("novelty_kind") for e in related})
        novel_body_table.append(
            {
                "body_key": bk,
                "classes": classes,
                "novelty_kinds": novelty_kinds,
                "security_labels": sec_labels,
                "abcd_any": {
                    k: any((a or {}).get(k) for a in abcds) for k in ABCD
                },
                "n_explore_ledger_hits": len(related),
            }
        )

    return {
        "explore_n_summary": explore_summary,
        "novel_body_table": novel_body_table,
        "abcd_counts_across_explore_ledgers": dict(abcd_counts),
        "security_label_counts": dict(sec_counts),
        "novelty_kind_counts": dict(novelty_kind_counts),
        "useful_behavioral_coverage": {
            "verdict": coverage_verdict,
            "evidence": coverage_evidence,
        },
        "recursion": recursion,
        "independence": independence,
        "s_odd_fate": s_odd,
        "bodies_fix": sorted(bodies_fix),
        "bodies_baseline": sorted(bodies_base),
        "classes_fix": sorted(classes_fix),
        "classes_baseline": sorted(classes_base),
        "n_explore_ledger_events": len(all_ledgers),
        "plant_ids": sorted({r.get("plant_id") for r in rows if r.get("plant_id")}),
        "cells_completed": {
            f"{r.get('condition')}:{r.get('budget_level')}:S{r.get('seed')}": r.get(
                "cell_source"
            )
            for r in rows
        },
    }


def render_md(payload: dict[str, Any]) -> str:
    agg = payload["aggregate"]
    cov = agg["useful_behavioral_coverage"]
    lines = [
        "# AIVD 3.47 EXPLORATION-VALUE VALIDATION RESULTS",
        "",
        f"**Recorded:** {payload['recorded_at_ist']}",
        f"**Authorization:** `{AUTHORIZATION}`",
        f"**Branch tip:** `{payload.get('primary_head', '')[:12]}`",
        f"**IMPL freeze (FIX science):** `{IMPL_FREEZE}` / `{IMPL_FREEZE_FULL}`",
        f"**BASELINE tip:** `{BASELINE_TIP}` / `{BASELINE_TIP_FULL}`",
        f"**Science freeze still 52394b8?** `{payload.get('impl_verify', {}).get('fix_science_match_52394b8')}`",
        f"**3.45 science modified?** **NO**",
        f"**Retuned?** **NO**",
        f"**B64?** **NO**",
        f"**Fresh plants?** **YES** (cell_source=fresh_3_47)",
        "",
        "---",
        "",
        "## Primary question",
        "",
        "Does B48 exploration increase USEFUL BEHAVIORAL COVERAGE vs merely NUMBER OF CONSTRUCTIONS?",
        "",
        f"**Verdict:** **{cov['verdict']}**",
        "",
        "```json",
        json.dumps(cov["evidence"], indent=2),
        "```",
        "",
        "## C. explore_n FIX vs BASELINE",
        "",
        "```json",
        json.dumps(agg["explore_n_summary"], indent=2),
        "```",
        "",
        "## D. Novel body table + A/B/C/D",
        "",
        "```json",
        json.dumps(agg["novel_body_table"], indent=2),
        "```",
        "",
        "### ABCD counts (explore ledger events; NOT collapsed)",
        "",
        "```json",
        json.dumps(agg["abcd_counts_across_explore_ledgers"], indent=2),
        "```",
        "",
        "### Novelty kinds",
        "",
        "```json",
        json.dumps(agg["novelty_kind_counts"], indent=2),
        "```",
        "",
        "## F. Security labels summary",
        "",
        "```json",
        json.dumps(agg["security_label_counts"], indent=2),
        "```",
        "",
        "## G. Recursion of explore-created bodies",
        "",
        "```json",
        json.dumps(agg["recursion"], indent=2),
        "```",
        "",
        "## H. Independence",
        "",
        "```json",
        json.dumps(agg["independence"], indent=2),
        "```",
        "",
        "## I. S/ODD fate (observational)",
        "",
        "```json",
        json.dumps(agg["s_odd_fate"], indent=2),
        "```",
        "",
        "## Cells (14)",
        "",
        "```json",
        json.dumps(agg["cells_completed"], indent=2),
        "```",
        "",
        f"- plant_ids (unique): {len(agg['plant_ids'])}",
        "",
        "## J. Commit + push",
        "",
        "- see JSON `commit_push`",
        "",
        "## K. 3.45 modified?",
        "",
        "**NO**",
        "",
        "---",
        "",
        "AIVD 3.47 EXPLORATION-VALUE VALIDATION COMPLETE",
        "",
    ]
    return "\n".join(lines)


def run_all(*, resume: bool = True) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)
    write_preregistration()

    gate = env_gate()
    if gate["gate_status"] != "PASS":
        write_progress({"phase": "BLOCKED", "gate": gate})
        return {"blocked": True, "gate": gate, "rows": []}

    impl = verify_science_freeze()
    (OUT_DIR / "impl_verify.json").write_text(json.dumps(impl, indent=2) + "\n")
    if not impl["ok"]:
        write_progress({"phase": "STOP", "reason": "impl_verify_failed", "impl": impl})
        return {"blocked": True, "impl": impl, "gate": gate, "rows": [], "stop": True}

    in_baseline = Path(REPO).resolve() == BASELINE_WORKTREE.resolve()
    if in_baseline:
        return {"blocked": False, "note": "baseline-only; use --condition BASELINE"}

    all_rows: list[dict[str, Any]] = []
    t_all = time.time()

    print(f"=== FIX B48={EPISODE_BUDGET} × {len(SEEDS)} seeds ===", flush=True)
    for seed in SEEDS:
        impl_b = verify_science_freeze()
        if not impl_b["fix_science_match_52394b8"]:
            write_progress({"phase": "STOP", "reason": "science_drift", "impl": impl_b})
            return {"blocked": True, "impl": impl_b, "rows": all_rows, "stop": True}
        row = run_cell(
            condition="FIX",
            seed=seed,
            implementation_commit=IMPL_FREEZE_FULL,
            resume=resume,
        )
        all_rows.append(row)

    print(f"=== BASELINE B48={EPISODE_BUDGET} × {len(SEEDS)} seeds ===", flush=True)
    bl_rows = run_baseline_cells(resume=resume)
    all_rows.extend(bl_rows)

    disk_rows = []
    for rp in sorted((OUT_DIR / "runs").glob("*.json")):
        try:
            disk_rows.append(json.loads(rp.read_text()))
        except Exception:
            pass
    if len(disk_rows) >= len(all_rows):
        all_rows = disk_rows

    agg = aggregate(all_rows)
    primary_head = _git(PRIMARY_WORKTREE, "rev-parse", "HEAD")
    payload = {
        "document": "aivd_3_47_exploration_value",
        "recorded_at_ist": _ist_now(),
        "authorization": AUTHORIZATION,
        "primary_head": primary_head,
        "impl_freeze": IMPL_FREEZE_FULL,
        "baseline_tip": BASELINE_TIP_FULL,
        "env_gate": gate,
        "impl_verify": impl,
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "budget_level": BUDGET_LEVEL,
        "episode_budget": EPISODE_BUDGET,
        "invent_cap": INVENT_CAP_EXPECTED,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR_EXPECTED,
        "representation": REPRESENTATION,
        "seeds": list(SEEDS),
        "plant_family": PLANT_FAMILY,
        "cell_source_policy": "fresh_14_cell_rerun",
        "elapsed_s": round(time.time() - t_all, 3),
        "n_runs": len(all_rows),
        "rows": all_rows,
        "aggregate": agg,
        "retuned": False,
        "science_345_modified": False,
        "b64_used": False,
        "commit_push": None,
        "micro_hash": micro_hash(),
        "version": __version__,
        "behavioral_equivalent_helper": "aivd.science.grow.behavioral_equivalent",
        "filter_behavioral_dup_redefined": False,
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESULTS_MD.write_text(render_md(payload))
    (OUT_DIR / "matrix_raw.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    write_progress(
        {
            "phase": "DONE",
            "n_done": len(all_rows),
            "coverage_verdict": agg["useful_behavioral_coverage"]["verdict"],
            "elapsed_s": payload["elapsed_s"],
        }
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--condition",
        choices=["BASELINE", "FIX", "ALL", "PREREG"],
        default="ALL",
    )
    ap.add_argument("--resume", action="store_true", default=True)
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args(argv)
    resume = not args.no_resume

    if args.condition == "PREREG":
        write_preregistration()
        print("Preregistration written:", PREREG_MD, PREREG_MATRIX)
        return 0

    if args.condition == "ALL":
        write_preregistration()
        run_all(resume=resume)
        return 0

    gate = env_gate()
    if gate["gate_status"] != "PASS":
        print("ENV GATE FAIL", gate["failures"])
        return 2

    if args.condition == "BASELINE":
        explor = REPO / "aivd" / "science" / "exploration_alloc.py"
        if explor.exists():
            print("STOP: BASELINE condition but exploration_alloc.py present in REPO")
            write_progress({"phase": "STOP", "reason": "baseline_has_explore_alloc"})
            return 3
        impl_commit = BASELINE_TIP_FULL
    else:
        impl = verify_science_freeze()
        if not impl["fix_science_match_52394b8"]:
            print("STOP: science ≠ 52394b8", impl["failures"])
            return 3
        impl_commit = IMPL_FREEZE_FULL

    for seed in SEEDS:
        run_cell(
            condition=args.condition,
            seed=seed,
            implementation_commit=impl_commit,
            resume=resume,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

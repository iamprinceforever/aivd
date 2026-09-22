# AIVD 3.41 — Execution Specification (Design-Only STOP)

**Document type:** Execution gate (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Parent charter:** `reports/aivd_3_41_charter.md`  
**Baseline tip:** `a380e3c` / `a380e3ce0be2bb1b456c38a0213cde12feef8f45`  
**Design branch:** `research/aivd-3.41-invention-planner-audit`  
**Parent commit:** `56dbc81` / `56dbc81f2712b610c852e03d87cd02eb706c2da1`  
**Mode:** `AIVD41_PLANNER_AUDIT`  
**Authorization (this commit):** `DESIGN_ONLY_NOT_EXECUTED`

---

## 1. DESIGN-ONLY STOP (binding)

This commit authorizes **documentation only**. It does **not** authorize:

- Implementing planner ledger hooks
- Enabling `AIVD41_PLANNER_AUDIT` in production runs
- Sacred / TinyLlama / plant discovery experiments
- Any modification to `grow.py`, `propose_atoms`, FILTER_BEHAVIORAL_DUP live path, R-A/R-C/R-D, invent_cap / INVENT_CAP, novelty thresholds, firewall, or planner score/rank/select math
- Seeding S-ATOM / S-CAT / S-DIAG into `propose_atoms`
- Rewriting Stage-7/8/9 historical artifacts
- Merging controlled FALSE_DUPLICATE with autonomous invisibility claims

**STOP here until a separate implementation authorization is issued.**

---

## 2. Exact next authorization text (required verbatim)

```
AIVD 3.41 IMPLEMENTATION AUTHORIZATION — BEHAVIOR-PRESERVING PLANNER LEDGER ONLY (no Sacred; no S injection; no grow.py / FILTER / propose_atoms / R-A/R-C/R-D / invent_cap / novelty / firewall / planner score-rank-select math changes)
```

Optional follow-on (still separate; not granted now):

```
AIVD 3.41 AUDIT EXECUTION AUTHORIZATION — INSTRUMENTED OBSERVATIONAL RUNS ONLY
(behavior-preserving ledger ON; twin OFF runs required; no Sacred plants beyond
preregistered observational matrix; no S injection; STOP on semantic/RNG mismatch)
```

Sacred / discovery uplift / filter replacement each require **additional** distinct authorizations beyond the two strings above.

---

## 3. Implementation phase outline (not authorized now)

When §2 authorization is granted, implementers must:

1. Add append-only observers at sites in `aivd_3_41_planner_ledger_spec.md` (`ScienceDesigner._maybe_invent_atom`, `AtomSynthesizer.plan` / `next_atom`, `rank_atoms`, `expected_verified_value`, `ExperimentLanguage.firewall`, grow nested `_keep`, etc.).
2. Keep `AIVD41_PLANNER_AUDIT` inert by default; enable only under explicit flag.
3. Pass test matrix T01–T16 in `aivd_3_41_test_spec.md` before scoring H10 leaves.
4. Preserve Stage-8/9 artifacts unchanged; write new reports only.
5. STOP on semantic or RNG mismatch per `aivd_3_41_semantic_preservation.md` / `aivd_3_41_rng_integrity.md`.

---

## 4. Forbidden list (restated)

- S injection / odd-stride heuristics / seed S into `propose_atoms`
- Filter merge / live FILTER replacement / R-A/R-C/R-D merge
- Sacred under design authorization
- grow.py / invent_cap / novelty / firewall / planner math changes under design authorization
- Fabricating NOT_RECORDED / rewriting Stage-7/8/9
- Assuming H10a from Stage-9 alone
- Post-hoc favorable selection outside preregistered controls

---

## 5. Gate line (design phase)

```
AIVD 3.41 DESIGN READY:
IMPLEMENTATION REQUIRES SEPARATE AUTHORIZATION
```

## STOP

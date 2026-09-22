# AIVD 3.41 — Hypothesis Tree (H10a–H10h + H10-REJECT)

**Document type:** Hypothesis tree (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Parent charter:** `reports/aivd_3_41_charter.md`  
**Baseline tip:** `a380e3c` / `a380e3ce0be2bb1b456c38a0213cde12feef8f45`  
**Mode:** `AIVD41_PLANNER_AUDIT`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

**Scientific goal:** Localize *why* the autonomous invention planner fails to produce the S behavioral direction by distinguishing propose / reject / score / rank / select / invent / budget-skip failure modes — **without** assuming H10a from Stage-9 invention absence alone, and **without** seeding S into `propose_atoms`.

---

## 0. Inherited priors (immutable)

| Prior | Stance |
|-------|--------|
| Stage-9 H9a SUPPORTED | Earliest disappearance = INVENTION; invent-reject detail NOT_RECORDED |
| Stage-9 H9D AGAINST scoped | Equivalence filter not an active bottleneck in Stage-8 autonomous S matrix (D=0) |
| Stage-9 H9e INCONCLUSIVE | Rank/score/select NOT_RECORDED |
| Stage-5 H5b FALSE_DUPLICATE | CONTROLLED — keep separate from autonomous invisibility |
| Stage-8 28/28 UNRESOLVED_INVISIBLE; S 0/7; D=0 | Cite; do not rewrite |
| Code fact: `propose_atoms` includes odd-stride `MAPT(SLICE:1,2(TOK))` at proposal_index=3 | Design-relevant; **not** a scored H10a verdict |

**Fence:** Stage-9 “S not invented” ≠ “S never proposed.” Absence from invent records alone cannot select among H10a–H10f without ledger.

---

## Causal / logical order

```
Preflight
  H10-REJECT   protocol / S-injection / filter-merge / Sacred / history mutation
Observation integrity
  H10h  instrumentation still insufficient after designed ledger
Planner lifecycle (earliest → later)
  H10a  NEVER_PROPOSED — proposal generation omits S-direction
  H10b  PROPOSED then REJECTED (validation / novelty / duplicate) before score
  H10c  SCORED/RANKED but systematically demoted below materialization cut
  H10d  Planning gates SKIP selection (leases / ext-not-exhausted / question / esc)
  H10e  SELECTED path blocked by invent_cap / occupancy / register failure
  H10f  NOT_REACHED_BEFORE_BUDGET_EXHAUSTION (leftover floor / ATOM_INVENTION_SKIPPED_BY_PLANNING)
  H10g  Firewall / behavioral-identity / novelty identity collapse blocks S-direction
INCONCLUSIVE when NOT_RECORDED blocks separation
Do NOT force a single winner among H10a–H10h
Do NOT assume H10a from Stage-9 absence alone
```

---

## Confidence vocabulary

| Label | Use |
|-------|-----|
| **SUPPORTED** | Direct ledger evidence favors claim; no decisive counter-evidence |
| **WEAKLY SUPPORTED** | Consistent with aggregates but lacks stage-local detail |
| **INCONCLUSIVE** | Missing evidence (`NOT_RECORDED`) or conflicting signals |
| **AGAINST** | Recorded evidence contradicts claim in scoped domain |

Avoid: PROVEN, DEFINITELY, ROOT CAUSE (singular) unless multi-leaf tie is explicit.

---

## H10a — Never proposed

**Claim:** S-direction candidates are **NEVER_PROPOSED** by `propose_atoms` / `propose_atom_candidates` under autonomous `AIVD41_PLANNER_AUDIT` plants (proposal generation omits the historical S behavioral direction).

**For:** Ledger shows proposal_state never PROPOSED for S-ATOM/S-CAT keys across seeds; raw proposal set excludes S bodies.  
**Against:** S body keys appear with proposal_state=PROPOSED (even if later rejected/not invented). Frozen 8-set containing odd-stride is **suggestive against** but must be confirmed under live representation policy + validation keep-set.  
**Missing:** invent-attempt ledger → do **not** upgrade Stage-9 NOT_OBSERVED invent to H10a.  
**Binding:** Do **not** assume H10a from Stage-9 absence alone.

---

## H10b — Proposed then rejected

**Claim:** S-direction candidates are proposed but **REJECTED** (validation / novelty / duplicate / classify_atom) before scoring/ranking.

**For:** proposal_state=PROPOSED and rejection_state=REJECTED with recorded rejection_reason for S keys; non-S pass same gates.  
**Against:** S candidates remain in `board.remaining` / reach SCORED.  
**Missing:** invent-reject ledger NOT_RECORDED today → INCONCLUSIVE until instrumented.

---

## H10c — Rank / score demotion

**Claim:** S-direction candidates are scored/ranked but systematically ranked below the materialization cut (lazy n_mat / rank_atoms demotion after rejected_classes), so they are never selected for invent.

**For:** score/rank ledger shows S present with worse rank than invented non-S; selection_state≠SELECTED while proposal survived reject.  
**Against:** S at rank head yet not invented (then H10d/e/f).  
**Missing:** score/score_components/rank NOT_RECORDED → tied to Stage-9 H9e INCONCLUSIVE until filled.

---

## H10d — Planning-gate skip

**Claim:** Planner gates in `ScienceDesigner._maybe_invent_atom` (pending leases, ext not exhausted, question gate, escalation STOP) cause SKIPPED before S materialization even when candidates exist.

**For:** selection_state/proposal_state show SKIPPED with selection_reason naming gate; methods_log events consistent.  
**Against:** Gates open and S still not invented for other recorded reasons.  
**Missing:** per-candidate skip reasons NOT_RECORDED.

---

## H10e — Capacity / register block

**Claim:** S reaches selection but invent fails due to `INVENT_CAP` / occupancy / `_register` failure.

**For:** selection_state=SELECTED or next_atom returned S; rejection/skip tied to invent_cap; occupancy≥48.  
**Against:** Occupancy headroom OBSERVED when invent skips for other reasons.  
**Missing:** per-candidate capacity decision ledger.

---

## H10f — Budget exhaustion before reach

**Claim:** S-direction candidates are proposed (or would be reachable) but are **NOT_REACHED_BEFORE_BUDGET_EXHAUSTION** (leftover `<` complete-chain floor → `ATOM_INVENTION_SKIPPED_BY_PLANNING` / `BUDGET_EXHAUSTED`), distinct from NEVER_PROPOSED.

**For:** budget_before/after + leftover traces show exhaustion before S materialization; failure_class ATOM_INVENTION_SKIPPED_BY_PLANNING (Stage-8 matrix-wide) with S proposal PROPOSED earlier.  
**Against:** Budget remains and S still NEVER_PROPOSED or REJECTED.  
**Binding:** Must distinguish NEVER_PROPOSED vs NOT_REACHED_BEFORE_BUDGET_EXHAUSTION.

---

## H10g — Firewall / identity / novelty collapse

**Claim:** Firewall epoch, behavioral_identity, or novelty filtering collapses or blocks S-direction identity (including false duplicate-class effects on invent path — scoped separately from Stage-5 controlled FILTER_BEHAVIORAL_DUP).

**For:** novelty_state / behavioral_identity / firewall_epoch ledger shows S blocked; contrast with EVEN same semantic_class.  
**Against:** Firewall/novelty pass for S yet still not invented.  
**Fence:** Do not merge CONTROLLED Stage-5 FALSE_DUPLICATE into this leaf without namespace separation.

---

## H10h — Instrumentation insufficiency

**Claim:** Even with the designed ledger, localization remains blocked by residual NOT_RECORDED gaps (meta / observation leaf).

**For:** After authorized instrumentation execution, critical transitions still NOT_RECORDED; H10a–H10g cannot be separated.  
**Against:** Ledger closes Stage-9 invent-reject + rank/score/select gaps and separates leaves.  
**Note:** Design phase expectation is that the ledger *targets* those gaps; H10h scored only after implementation+audit.

---

## H10-REJECT — Protocol / mandate violation

**Claim:** Protocol broken: S injection into propose_atoms; filter merge; Sacred under design auth; grow.py / planner math mutation; fabricated NOT_RECORDED; history rewrite; post-hoc favorable selection.

**Scoring:** SUPPORTED/AGAINST on protocol evidence only. Prefer **not_supported** / AGAINST when mandate held.

---

## STOP

Design only. Do not score leaves as executed results. Do not assume H10a from Stage-9 alone.

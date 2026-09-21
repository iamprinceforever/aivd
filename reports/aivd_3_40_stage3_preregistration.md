# AIVD 3.40 Stage-3 — Preregistration Rules, Freeze Protocol, Revision Policy

**Recorded:** 2026-09-21 17:04 IST  
**Parent charter:** `reports/aivd_3_40_stage3_charter.md`  
**Status:** Rules frozen for Stage-3 *localization design*. No Sacred authorized here.  
**Anti-pattern callout:** Commit `7a3457e` (Stage-2 R1b invent-basis trim after smoke / before Sacred).

---

## 1. Purpose

Ensure any future Stage-3 **EXECUTION** work (Phase-1 tooling or Phase-2 Sacred) remains scientifically interpretable: predeclared factors, frozen locks, no silent mid-flight patches, honest handling of unresolved S.

This document is the Stage-3 analogue of Stage-2 R1b preregistration — with lessons learned.

---

## 2. What is preregistered by the Stage-3 charter suite (Phase 0)

| Item | Location | Frozen? |
|------|----------|---------|
| Scientific objective (localize bottleneck; not make S pass) | Master charter | YES |
| Hypothesis tree H1–H6 + reject criteria | `aivd_3_40_stage3_hypothesis_tree.md` | YES |
| Phase structure (0 docs → 1 offline → 2 Sacred if needed) | Experimental matrix | YES |
| Instrumentation field list | Instrumentation spec | YES |
| Counterfactual classification rules | Replay spec | YES |
| Interpretation cases A–H | Master charter §7 | YES |
| FROZEN / FORBIDDEN lists | Master charter §§8–9 | YES |
| Concrete Rx definition | — | **NO** (requires separate prereg after Phase 1) |
| BHexplore numeric budget | — | **NO** (only if Phase 1 evidences starvation; then separate prereg) |
| Implementation code | — | **NOT AUTHORIZED** |

---

## 3. Freeze protocol (before any Stage-3 Sacred)

### 3.1 Freeze commit

1. Land EXECUTION charter + any required specs as docs.  
2. Record `freeze_commit = git rev-parse HEAD` in a Stage-3 freeze JSON under `reports/`.  
3. Env gate PASS (same discipline as Stage-2) before Sacred.  
4. **No** discovery semantics edits after freeze without revision (§5).

### 3.2 Smoke rules

Smoke may validate wiring (imports, matrix launch, recorder emission). Smoke must **NOT**:

- Trim invent basis / proposal classes to “reach firewall”  
- Add/remove ranking features  
- Change REDISCOVERY_FLOOR, invent_cap, firewall, verification  
- Special-case S or U  

If smoke reveals a design flaw → **STOP** → §5 revision. Do not patch forward into Sacred.

### 3.3 Sacred rules

- Plants: fresh Stage-3 IDs  
- Seeds: predeclared (default `[0,1,2,3,4,7,11]`)  
- Matched S and U cells for every intervention  
- BH-R1 × U (or frozen-equivalent) positive control present  
- Report zeros honestly; never combine S+U success  

---

## 4. Forbidden post-hoc changes (binding)

After smoke starts toward a declared Sacred, and after Sacred starts, **FORBIDDEN**:

| Change | Why forbidden |
|--------|----------------|
| Invent-basis trim / expand | Alters representation factor mid-flight |
| Proposal-class add/remove | Alters H1/H2 surface |
| Ranking / selection formula change | Alters H3 |
| REDISCOVERY_FLOOR / invent_cap / BH budget change | Alters H5 surface & locks |
| Firewall / verification / GenerationRecord semantics change | Breaks independence meaning |
| Force-firewall / silent smoke patches | Unauditable |
| Target-specific branches (S-only assists) | Confounds localization |
| Claiming prior R1b Sacred was preregistered-unchanged | False — see §6 |

---

## 5. Revision policy

| Trigger | Action |
|---------|--------|
| Design flaw found in smoke or audit | **STOP** Sacred path; open **new prereg revision** doc with bump id (e.g. Stage-3-rev2); new freeze commit |
| Phase 1 motivates Rx or BHexplore | Separate prereg appendix *before* implementation; generic properties only; no plant GT |
| Ambiguous results after declared matrix | STOP; revise interpretation charter — do not add cells post-hoc to chase S |
| U positive control regresses unexpectedly | STOP; H6 / harness investigation charter |

Revisions are **explicit, versioned, and dated**. Silent amend of Sacred semantics is never a revision.

---

## 6. Stage-2 lesson — `7a3457e` anti-pattern (mandatory callout)

**Fact:** Commit `7a3457e` — *fix: AIVD 3.40 R1b invent basis trim to 3 geo classes (firewall reachability)* — landed **after smoke and before Sacred**, changing the invent basis relative to Commit-B R1b preregistration.

**Consequence:** Stage-2 R1b Sacred is **NOT pure Commit-B preregistered-unchanged**. Results remain usable as **observational** data (including odd-stride invent under R1b×S and Case D U independence harm) but must not be cited as a clean confirmatory test of the original R1b prereg.

**Stage-3 rule:** The `7a3457e` pattern is **explicitly forbidden**. Firewall reachability problems discovered in smoke require STOP + new prereg revision — not an invent-basis trim on the way to Sacred.

**Citation wording for all Stage-3 docs:** always include the integrity caveat when discussing R1b Sacred priors.

---

## 7. Integrity caveats that must appear in Stage-3 results writing

1. R1b Sacred ≠ pure Commit-B prereg (`7a3457e`).  
2. Unresolved S is a valid preserved result.  
3. Counterfactual verify-accept ≠ Sacred VERIFIED.  
4. Larger budget success alone ≠ proof of H5.  
5. BH-R1 × U 7/7 weakens H6 but does not eliminate it until invariants confirmed.  
6. No GT injection; leakage must remain 0 for credit.

---

## 8. Relationship to Absolute / FROZEN locks

Preregistration **cannot** authorize modification of:

- Sacred 3.38/3.39 artifacts  
- propose_atoms 8-set  
- REDISCOVERY_FLOOR=5  
- invent_cap=48  
- firewall / verification / GenerationRecord semantics  
- Absolute no-GT-injection rule  

Any future proposal to touch these requires a **different** research charter outside Stage-3 localization scope — and is **out of scope** for the present Stage-3 mandate.

---

## 9. FINAL pointer

Master gate: **STOP — Stage-3 implementation requires a separate explicit EXECUTION charter.**

This preregistration freezes *rules*. It does not authorize code, Sacred, R1c, or budget raise.

---

## STOP

No implementation. No Sacred. Docs-only Phase 0.

# AIVD 3.41 — Preregistration (Design Only)

**Document type:** Preregistration (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Parent charter:** `reports/aivd_3_41_charter.md`  
**Baseline tip:** `a380e3c` / `a380e3ce0be2bb1b456c38a0213cde12feef8f45`  
**Mode:** `AIVD41_PLANNER_AUDIT`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 1. Primary question (locked)

Why does the autonomous invention planner fail to produce the S behavioral direction? How does it propose / reject / score / rank / select / invent?

## 2. Analysis mode (locked)

- Kind: observational planner audit under `AIVD41_PLANNER_AUDIT`
- Normal 3.40 discovery behavior remains available when audit instrumentation is off/inert
- No Sacred / TinyLlama / plant discovery under this design authorization
- No S seeding into `propose_atoms`
- No live FILTER / R-A/R-C/R-D / invent_cap / novelty / firewall / planner math changes under this design authorization

## 3. Hypotheses (locked)

H10a–H10h + H10-REJECT as defined in `reports/aivd_3_41_hypothesis_tree.md`.  
**Binding:** Do **not** assume H10a from Stage-9 invention absence alone.

## 4. Evidence rules (locked)

1. Emit `NOT_RECORDED` when a field/transition is unavailable — never fabricate.
2. Tag observational states: OBSERVED / NOT_OBSERVED / NOT_RECORDED / NOT_APPLICABLE.
3. Distinguish **NEVER_PROPOSED** vs **NOT_REACHED_BEFORE_BUDGET_EXHAUSTION**.
4. S-ATOM / S-CAT / S-DIAG are observational queries only — never seed into `propose_atoms`.
5. Keep CONTROLLED Stage-5 FALSE_DUPLICATE separate from AUTONOMOUS Stage-8 invisibility.
6. Score leaves independently; retain multi-hypothesis ties; do not force a singular root cause.

## 5. Controls for naturally successful candidates (locked)

Preregistered rules (apply before seeing post-instrumentation outcomes):

1. **Natural-success definition:** A non-S candidate that reaches INVENTED under unchanged 3.40 semantics with ledger showing PROPOSED→…→INVENTED without instrumentation-only fields altering order.
2. **Inclusion rule:** All naturally successful candidates in the audited seed×condition matrix are retained in the success cohort; no post-hoc exclusion for “inconvenient” successes.
3. **Comparison rule:** S-direction queries are compared against the same seeds/conditions; do not cherry-pick seeds where non-S failed.
4. **No favorable selection:** Forbidden to promote a leaf by selecting only runs where ledger favors that leaf after seeing results.
5. **Instrumentation-off twin:** Every instrumented audit cell must have an uninstrumented twin for semantic-preservation checks (see test matrix).

## 6. Budget accounting (locked)

- Instrumentation consumes **zero** experimental budget.
- Instrumentation consumes **no** planner RNG.
- Ledger must record budget_before / budget_after when the planner touches a candidate.
- STOP if instrumented runs diverge on budget trajectory vs uninstrumented twin.

## 7. Forbidden list (locked)

- S injection / odd-stride heuristics / seeding S into `propose_atoms`
- Filter merge / live FILTER_BEHAVIORAL_DUP replacement / R-A/R-C/R-D merge
- Sacred / TinyLlama / plant discovery in design phase
- grow.py / invent_cap / novelty / firewall / planner score-rank-select math changes in design phase
- Rewriting Stage-7/8/9 historical results
- Fabricating NOT_RECORDED fields
- Post-hoc favorable selection outside §5 controls
- Assuming H10a from Stage-9 absence alone

## 8. Success criteria (design phase)

Design phase success = all ten `reports/aivd_3_41_*` artifacts committed on `research/aivd-3.41-invention-planner-audit` from `a380e3c` and pushed to `aivd` remote.  
Implementation / Sacred / instrumentation execution is **out of scope** and requires separate authorization.

## 9. STOP

Preregistration only. Do not implement. Do not run Sacred.

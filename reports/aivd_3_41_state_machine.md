# AIVD 3.41 — Planner State Machine (Design Only)

**Document type:** State machine (DOCS ONLY — **NOT IMPLEMENTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Parent charter:** `reports/aivd_3_41_charter.md`  
**Baseline tip:** `a380e3c`  
**Mode:** `AIVD41_PLANNER_AUDIT`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 1. Canonical lifecycle

```
CANDIDATE_CREATED
  → PROPOSED
      → REJECTED                    (terminal for that candidate)
      → ACCEPTED_FOR_SCORE
          → SCORED
              → RANKED
                  → SELECTED
                      → INVENTED                 (terminal success path)
                      → NOT_INVENTED             (capacity / register / post-select skip)
                  → NOT_SELECTED
                      → SKIPPED                  (planning gate / budget / lazy cut)
```

Observational overlay tags (orthogonal): `NOT_RECORDED`, `NOT_APPLICABLE`, `OBSERVED`, `NOT_OBSERVED`.

---

## 2. Transition table

| Transition | Observable evidence (if instrumented) | Missing evidence today | Valid interpretation | Invalid inference |
|------------|----------------------------------------|------------------------|----------------------|-------------------|
| CREATED → PROPOSED | proposal row with candidate_key / proposal_index / origin | invent-attempt ledger NOT_RECORDED | Candidate entered proposal set | “Not invented ⇒ never proposed” |
| PROPOSED → REJECTED | rejection_state=REJECTED + rejection_reason | invent-reject ledger NOT_RECORDED | Failed validation/novelty/duplicate | Treat Stage-5 FILTER_BEHAVIORAL_DUP as Stage-8 invent reject without ledger |
| PROPOSED → ACCEPTED_FOR_SCORE | candidate remains in board.remaining | NOT_RECORDED | Survived reject gates | Assume all propose_atoms members scored |
| ACCEPTED → SCORED | score + score_components | score ledger NOT_RECORDED | Score computed via expected_verified_value | Infer score from invent order alone |
| SCORED → RANKED | rank after rank_atoms | rank ledger NOT_RECORDED | Stable reorder applied | Infer rank from Stage-8 invent order alone |
| RANKED → SELECTED | selection_state=SELECTED + selection_reason | select ledger NOT_RECORDED | next_atom / orchestration chose candidate | Fate E on non-S ⇒ S failed selection |
| RANKED → NOT_SELECTED / SKIPPED | selection_state=SKIPPED + reason (gate/budget/lazy) | NOT_RECORDED | Planning/budget/lazy cut skipped candidate | Collapse SKIPPED into NEVER_PROPOSED |
| SELECTED → INVENTED | generation_record / invent event with body_key | Partial: invent summaries AVAILABLE for invented only | Materialized + registered | Treat invent summary absence as reject |
| SELECTED → NOT_INVENTED | capacity/register failure record | NOT_RECORDED | invent_cap / _register failed | Assume invent_cap without occupancy evidence |

---

## 3. Budget annotations on transitions

Attach to SKIPPED / NOT_INVENTED / terminal episode stop:

- `budget_before`, `budget_after`
- Label: `NEVER_PROPOSED` **or** `NOT_REACHED_BEFORE_BUDGET_EXHAUSTION` (mutually exclusive claims for a given S-direction key)

Stage-8 `ATOM_INVENTION_SKIPPED_BY_PLANNING` + `BUDGET_EXHAUSTED` is **compatible with** H10f but **does not prove** NEVER_PROPOSED (H10a).

---

## 4. S observational markers

For S-ATOM / S-CAT / S-DIAG keys only (query, do not seed):

| Marker | Meaning |
|--------|---------|
| NOT_OBSERVED @ INVENTION (Stage-9) | No invent record for S keys while other invents OBSERVED |
| NOT_RECORDED @ PROPOSE/REJECT/SCORE/RANK/SELECT | Stage-8/9 instrumentation gap — blocks H10a–H10e separation |
| NOT_APPLICABLE @ EQUIV/SELECT for S | Downstream of invent absence |

---

## 5. Invalid global inferences (binding)

1. Stage-9 invent absence ⇒ H10a SUPPORTED (forbidden without propose ledger)
2. Fate E common among non-S ⇒ selection caused S failure (forbidden; H9e INCONCLUSIVE preserved)
3. D=0 ⇒ equivalence can never matter (forbidden; H9D is scoped AGAINST for Stage-8 matrix only)
4. Controlled FALSE_DUPLICATE ⇒ autonomous invent skip (forbidden namespace merge)

---

## 6. STOP

State machine design only. Do not implement transitions in production code in this phase.

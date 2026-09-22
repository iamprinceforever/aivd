# AIVD 3.41 — Test Specification (Design Only; 16 items)

**Document type:** Test matrix (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Parent charter:** `reports/aivd_3_41_charter.md`  
**Baseline tip:** `a380e3c`  
**Mode:** `AIVD41_PLANNER_AUDIT`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Binding:** Do **not** require S discovery for pass.

---

## Matrix (16)

| ID | Name | Intent | Pass criterion | Fail / STOP |
|----|------|--------|----------------|-------------|
| T01 | Deterministic replay OFF | Uninstrumented twin stable across 2 replays | Identical invent body_key sequences, scores/ranks if logged, budget, terminal | Divergence without code change |
| T02 | Deterministic replay ON | Instrumented twin stable across 2 replays | Identical planner outcomes + identical ledger digests | Ledger nondeterminism |
| T03 | ON vs OFF semantic equality | Behavior preservation | Sequences/scores/ranks/selections/inventions/budget/final state match (§ semantic_preservation) | Any mismatch → STOP |
| T04 | Zero budget consumption | Instrumentation cost | budget_after series ON == OFF; BH/invent_cap unchanged | Budget delta attributable to ledger |
| T05 | Zero RNG consumption | RNG integrity | RNG digests/counts ON == OFF | Extra RNG draws ON |
| T06 | Proposal ledger emission | Closes Stage-9 invent-attempt gap | Every plan-kept candidate emits PROPOSED row with candidate_key + proposal_index | Missing PROPOSED for kept candidate |
| T07 | Reject ledger emission | Closes invent-reject gap | Validation/novelty/duplicate rejects emit REJECTED + rejection_reason | Silent drop without REJECTED row |
| T08 | Score ledger emission | Closes score gap | SCORED rows include score + score_components for scored candidates | Score used but not ledgered |
| T09 | Rank ledger emission | Closes rank gap | RANKED rows include rank consistent with rank_atoms order | Rank order ≠ ledger rank |
| T10 | Select / skip ledger emission | Closes select gap | SELECTED or SKIPPED with selection_reason for each ranked candidate touching invent orchestration | Silent skip |
| T11 | Invent / not-invent ledger | Materialization visibility | INVENTED rows match generation_record body_keys; NOT_INVENTED/SKIPPED for capacity/budget | Invent without ledger or ledger invent without register |
| T12 | NEVER_PROPOSED vs budget-not-reached | Budget distinction | For S-direction observational query, label is exactly one of NEVER_PROPOSED or NOT_REACHED_BEFORE_BUDGET_EXHAUSTION when decidable; else NOT_RECORDED | Collapsing labels |
| T13 | S observational non-seeding | No S injection | propose_atoms / propose_atom_candidates source+runtime unchanged; no S keys inserted | Any S seeding |
| T14 | Natural-success controls | Prereg §5 | Naturally successful non-S candidates retained; no post-hoc exclusion | Favorable cohort editing |
| T15 | Forbidden surface freeze | No production mutation | grow.py / FILTER path / invent_cap / novelty / firewall / rank_atoms / expected_verified_value / propose_atoms hashes unchanged vs `a380e3c` | Any forbidden diff |
| T16 | Instrumentation-off regression | Mode inert | With `AIVD41_PLANNER_AUDIT` disabled, bit-identical to pre-instrumentation baseline behavior | Residual behavior change when OFF |

---

## Notes

- Tests T01–T16 are **design specifications** for a future implementation phase.
- Passing T03+T04+T05+T15+T16 is required before trusting any H10 leaf scores.
- S VERIFIED is **not** a pass criterion for this matrix.

## STOP

Do not execute these tests under design authorization.

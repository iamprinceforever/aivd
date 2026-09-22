# AIVD 3.42 — Remaining Uncertainty

**Recorded:** 2026-09-22 13:00:57 IST  
**Sacred:** NO  

## Closed by this audit

- Whether ODD is proposed (yes, 28/28).
- Whether ODD is rejected before score (no).
- Whether first SELECT is score/rank driven (no — board order + n_mat=1).
- Whether ODD ever reaches rank-0 under recorded demotion (no, 0/28).
- A–E: E SUPPORTED; A/B AGAINST; C/D INCONCLUSIVE alone.

## Residual NOT_RECORDED / open

1. **EVEN intrinsic score** — never emitted; cannot compare odd vs even on pre-demotion EV numerically (NOT_RECORDED).
2. **Per-candidate observe_skip reasons** after ODD reaches best_rank=1 — early-return gates inside `_maybe_invent_atom` still lack skip rows (inherited 3.41 H10d/H10h residual).
3. **behavioral_identity / language_key** on invent ledger — still NOT_RECORDED (grow.py frozen; FORBIDDEN to change).
4. **Why propose_atom_candidates orders EVEN before ODD** — observed as board fact; generative policy internals not re-audited here (out of 3.42 selection-causal scope; would be a separate propose-order audit).
5. **Whether n_mat>1 or rank-policy change would yield Sacred uplift** — FORBIDDEN; requires separate authorization (not evaluated).

## H11-REJECT

**AGAINST** — evidence sufficient to localize to E (board order × rank demotion × n_mat=1). Residual items above do not reopen H11-REJECT for the primary question.

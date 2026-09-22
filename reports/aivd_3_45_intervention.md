# AIVD 3.45 — GENERAL PLANNER EXPLORATION FIX (Intervention)

**Recorded:** 2026-09-22 13:32:22 IST  
**Baseline tip:** `72edfad` / `72edfadeda87c0ea6ac966487c49b9526099c613`  
**Branch:** `research/aivd-3.45-adaptive-exploration-materialization`  
**Remote:** `aivd` → github.com/iamprinceforever/aivd.git  
**Sacred:** NO  

## 1. Problem

Limited materialization capacity (lazy n_mat=1) + plan-board order + rank demotion can permanently starve valid lower-ranked unexplored directions. Established by AIVD 3.41–3.44 as a **general** exploration/exploitation allocation failure — not an S-specific bug.

## 2. Insertion point

| Field | Value |
|-------|-------|
| Path | `aivd/science/designer.py` |
| Symbol | `ScienceDesigner._maybe_invent_atom` |
| Module | `aivd/science/exploration_alloc.py` |
| Prim/ext | Inspected (`n_mat` @598/701); **not** modified (smallest atom-path insertion) |

Replaces fixed `n_mat = 1 if allow_atom_lazy else 4` and the unconditional `if allow_atom_lazy: break` after first successful materialization.

## 3. Policy (EXPLOIT + EXPLORE)

**EXPLOIT:** preserve rank-/board-driven head selection (width 1 lazy / 4 eager).  
**EXPLORE:** at most **+1** materialization slot when:

1. **First-window diversity:** epoch==0, no prior materializations, valid candidates beyond exploit cut, and budget affords ≥2 chain floors; or
2. **Skip-pressure anti-starvation:** candidate still valid, `materialization_count==0`, `exploration_opportunities < max`, `skip_count >= threshold`.

Budget gates: `min(leftover // chain_floor, invent_slots_left, n_candidates)`.  
Explore opportunity ≠ guaranteed invention (novelty / firewall / invent_cap / verification unchanged).

## 4. Fields added (general only)

- `skip_count`
- `materialization_count`
- `exploration_opportunities`
- `last_materialized_epoch`
- allocator `epoch` + `states`
- `ScienceDesigner.atom_explore`

## 5. Requirements checklist (1–13)

| # | Requirement | Status |
|---|-------------|--------|
| 1 | High-value exploitation remains possible | PASS |
| 2 | Behavioral diversity not permanently starved | PASS |
| 3 | Lower-ranked get bounded exploration opportunities | PASS |
| 4 | Budget-aware (existing accounting) | PASS |
| 5 | No invention explosion | PASS |
| 6 | No repeated known-equivalent exploration | PASS (existing novelty gates) |
| 7 | Works for arbitrary candidates | PASS |
| 8 | No candidate-specific knowledge | PASS |
| 9 | U behavior remains valid | PASS (exploit path preserved; Sacred NOT_RECORDED) |
| 10 | Deterministic for identical seeds/configs | PASS (P6) |
| 11 | Works when candidates >> width | PASS |
| 12 | Useful when ordering changes | PASS (surfacing) |
| 13 | Opportunity ≠ guaranteed invention | PASS |

## 6. Tests

- File: `tests/test_aivd345_exploration_alloc.py`
- Matrix A–H: **PASS**
- Properties P1–P7: **PASS**
- Regression + designer wire + production grep guard: **PASS**
- `tests/test_aivd341_planner_audit.py`: **PASS**
- Combined: **38 passed**

## 7. Offline BASELINE vs FIX

| Metric | BASELINE | FIX-A adaptive | FIX-B fixed n_mat=2 |
|--------|----------|----------------|---------------------|
| Mean first-window diversity | 1.000 | 2.000 | 2.000 |
| Mean materializations (sim) | 4.000 | 4.000 | 4.000 |

**FIX-A first-window diversity lift:** +1.000  
CF inventions are **NOT** real inventions. Single-key exposure is observation only (not acceptance).

## 8. Ablation

Winner: **FIX-A** — same first-window diversity lift as FIX-B under recorded leftover≥6, but withholds explore when budget cannot afford a second chain, and caps per-candidate opportunities. Selection criterion: breadth + cost + exploitation preservation — **not** S success.

## 9. Candidate-specific grep

Scope: production `exploration_alloc.py` + added `designer.py` lines vs `72edfad`.  
Tokens: ODD, EVEN, MAPT(SLICE:1,2(TOK)), char_stride, POS6, POS7, Sacred, TinyLlama.  
**Result: CLEAN**

## 10. STOP conditions

**None hit.**

## 11. Success criteria A–I

All PASS for general anti-starvation / preserved gates / no candidate-specific code / bounded explore.  
**S improvement = observation ONLY, not acceptance.**

## 12. Known limitations / NOT_RECORDED

- Offline replay does not fully resimulate post-invent rank demotion trajectories (NOT_RECORDED).
- Verification / Sacred uplift NOT_RECORDED.
- Prim/ext lazy n_mat paths unchanged (atom path only).
- Exploration opportunity does not guarantee invention (by design).
- max_opportunities_per_candidate=1 may underserve after firewall reset until reset() — allocator resets on firewall board clear.

NOT_RECORDED:
- Live Sacred outcomes under FIX-A
- Exact invent unit cost beyond chain_floor=3 proxy
- Full post-window CF trajectories under demotion×explore interaction

## 13. Sacred

**NO** — requires separate authorization.

## 14–18. Deliverables / freeze / push

See JSON twin. Commit message target:

`feat: AIVD 3.45 adaptive exploration materialization (general anti-starvation; no Sacred)`

```
AIVD 3.45 GENERAL EXPLORATION FIX READY:
SACRED EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

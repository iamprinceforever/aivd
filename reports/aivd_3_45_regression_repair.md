# AIVD 3.45 REGRESSION REPAIR

**Recorded:** 2026-09-22 13:50:10 IST  
**Branch:** `research/aivd-3.45-adaptive-exploration-materialization`  
**Broken freeze:** `6671788`  
**Baseline good:** `72edfad`  
**Pre-sacred audit tip:** `418c97f`  
**Sacred:** NO  

---

## A. First divergence summary (7 tests)

All seven are the EX8-family compose path. Earliest structural divergence vs baseline:

| Field | BASELINE `72edfad` / n_mat=1 | BROKEN `6671788` | REPAIR |
|-------|------------------------------|------------------|--------|
| **earliest** | — | **`n_mat` (epoch 0)** | matches baseline |
| n_mat epoch0 | 1 | **2** (first-window explore) | 1 |
| explore_candidate | (none) | `MAPT(SLICE:0,2(TOK))` secondary same-call | (none while untried) |
| materialization | CAT→SLICE→AT:-1 (sequential) | CAT+SLICE same-call; then AT:-1+extra | CAT→SLICE→AT:-1 |
| compose | SLICE ∘ AT:-1 | **wrong pair** AT:-1 ∘ CAT(AT:-1\|TOK) | SLICE ∘ AT:-1 |
| language_grow | (compose verifies) | `language_grow_reject` then wrong grow | compose verifies |
| terminal | VERIFIED | UNRESOLVED_INVISIBLE | VERIFIED |

Tests covered by same mechanism:
1. `test_ex8_even_then_last_337_vs_336`
2. `test_ex8_seed0_provenance`
3. `test_dx9_on_337_same_fire_as_ex8`
4. `test_ex10_transfer`
5. `test_ex12_independent_rediscovery_env`
6. `test_ablation_nolangext_compose_still_works`
7. `test_ex8_even_then_last_still_verified_on_338`

Fields NOT_RECORDED where absent from methods_log: exact board rank vectors per seed average, firewall epoch on EX8 seed0 path (no firewall), per-step leftover deltas beyond compose leftover stamp.

---

## B. Root mechanism

**EXPLORATION STARVATION fix introduced EXPLOITATION DISPLACEMENT.**

`6671788` treated `n_mat=2` as equal top-two materialization (first-window diversity + unguarded skip-pressure). Same-call dual invent promoted two atoms before the sequential second-atom path finished, so `pick_compose_pair` (two most recently promoted distinct-class) selected the wrong pair → `language_grow_reject` → UNRESOLVED_INVISIBLE.

---

## C. Repaired policy (PRIMARY vs SECONDARY)

| Slot | Role | Width | When |
|------|------|-------|------|
| **PRIMARY** | Productive continuation (rank head) | `exploit_n` (1 lazy / 4 eager) | Always when budget/cap allow |
| **SECONDARY** | Bounded anti-starvation explore | at most +1 | Skip-pressure only, **and** no untried semantic classes remain on the board |

- **Removed** first-window max-diversity (`_first_window_diversity`).
- **Do not** treat `n_mat=2` as equal top-two: `primary_keys` vs `secondary_keys` / `explore_keys`.
- While untried classes remain, rank→PRIMARY owns them (second-atom path); secondary is withheld (`reason=exploit_only_productive_continuation`).
- Explore resumes after classes exhausted for demoted leftovers (P2 anti-starvation).
- No candidate-specific logic; novelty/firewall/invent_cap/equivalence/verification untouched.

---

## D. CF-A / CF-B / CF-C headlines

| CF | Headline | EX8 seed0 |
|----|----------|-----------|
| **CF-A** | Baseline productive candidate remains PRIMARY (`n_mat=exploit_n`) through recursive path | VERIFIED; compose SLICE∘AT:-1 |
| **CF-B** | Exploration is SECONDARY — never displaces PRIMARY; explicit primary/secondary keys | VERIFIED under repair |
| **CF-C** | Exploration delayed until productive continuation stable (untried classes cleared) | VERIFIED; explore_n=0 while untried |

---

## E. Full pytest

**1272 passed, 0 failed** in 93.21s (0:01:33).

EX8-family 7/7 green; BX2/CX1 starvation ablations green; P1–P10 green.

---

## F. Anti-starvation still demonstrated?

**YES.** Skip-pressure secondary explore fires when `productive_continuation=False` (no untried classes) and `skip_count >= threshold`: matrix A/C/H, P1/P2/P10, unit demo `T1` surfaced with `n_mat=2` after primary-only first window. Not removed; only gated.

---

## G. Recursive growth preserved?

**YES.** EX8/DX9/EX10/EX12/338: sequential CAT→SLICE→AT:-1 → compose SLICE∘AT:-1 → VERIFIED. `second_atom_hypothesis` intact. P9/P10 encode the guard.

---

## H. PRODUCTION_LOGIC_SCAN

**CLEAN** — no ODD/EVEN/MAPT(SLICE:…)/char_stride/POS6/POS7/EX8/Sacred/seed0 tokens in production `aivd/science/` diff vs `72edfad`.

---

## I. Commit + push

(pending)

---

## J. Sacred?

**NO**

---

## STOP conditions

None hit after repair (prior REGRESSION_MATRIX cleared; no new family; no candidate-specific; anti-starvation retained; determinism/unit OK).

---

AIVD 3.45 REGRESSION REPAIR READY:
SACRED EXECUTION REQUIRES SEPARATE AUTHORIZATION

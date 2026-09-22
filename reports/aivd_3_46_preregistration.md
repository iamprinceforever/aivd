# AIVD 3.46 BUDGET-FRONTIER VALIDATION — PREREGISTRATION

**Preregistered:** 2026-09-22 15:08:44 IST
**Authorization:** `AIVD 3.46 BUDGET-FRONTIER VALIDATION — AUTHORIZED: frontier B32/B40/B48/B64; R1 TinyLlama; seeds[0,1,2,3,4,7,11]; invent_cap=48; REDISCOVERY_FLOOR=5; BASELINE@72edfad vs FIX science@52394b8; fresh plant family AIVD346-FRONTIER-ODDSTRIDE (new plant_ids per cell); no retune; no 3.45 science edits; no S/ODD/MAPT injection; primary metric explore_n; freeze at first activation.`

## Hard constraints (locked)

- Worktree: `/workspace/aivd-340-replication` (+ BASELINE `/workspace/aivd-345-baseline-72edfad` @ `72edfad`)
- Branch tip origin: `b2a4aa4` → `research/aivd-3.46-budget-frontier-validation`
- **DO NOT MODIFY 3.45** — no edits to `exploration_alloc.py`, designer explore policy,
  n_mat logic, scoring/ranking/proposal, invent_cap in science, firewall floor, novelty
- Allowed: `aivd/experiments/aivd346/` + reports only; episode_budget via pipeline
- No S injection, no retune, no unlimited budget, no invent_cap forcing
- CF discoveries ≠ real discoveries
- S success is NOT primary acceptance

## Planners

| Arm | Tip | Notes |
|-----|-----|-------|
| BASELINE | `72edfad` / `72edfadeda87c0ea6ac966487c49b9526099c613` | no exploration_alloc |
| FIX | science freeze `52394b8` / `52394b8f5f802047ffc9029910e0b0de5d110f01` | `git diff 52394b8 -- aivd/science/` must be empty |

## Preregistered frontier (justified)

| Level | Budget | Justification |
|-------|--------|---------------|
| B32 | 32 | 3.45 Sacred wall: leftover 3 < floor 5 |
| B40 | 40 | intermediate above wall |
| B48 | 48 | Stage-8 BH envelope |
| B64 | 64 | upper bound; not unlimited |

- invent_cap = **48**
- REDISCOVERY_FLOOR = **5**
- Representation = **R1** (`full_3_39_r1`)
- Model = **TinyLlama/TinyLlama-1.1B-Chat-v1.0** @ `/workspace/models/tinyllama`
- Seeds = `[0, 1, 2, 3, 4, 7, 11]`
- Plant family = `AIVD346-FRONTIER-ODDSTRIDE` (same odd-stride family as 3.45; **new plant_ids per cell**)

## Primary / secondary / tertiary questions

1. **Primary:** Does explore_n become >0 under larger envelope?
2. **Secondary:** Does increased exploration produce genuinely new behavioral directions?
3. **Tertiary:** Does it preserve successful recursive path?

## Execution strategy (frozen)

1. This preregistration + `aivd_3_46_matrix.json` BEFORE running.
2. Ascend budgets for **FIX 3.45 first**: B32→B40→B48→B64 × 7 seeds.
3. Primary metric: explore_n (sum of secondary explore allocations) + reasons.
4. **First activation point:** first (budget, seed) / first budget where any seed has explore_n>0 — freeze and report prominently.
5. At activation budget (and B32 for continuity): matched BASELINE 7 seeds.
6. If no activation through B64: report limiting condition — do NOT raise invent_cap or change policy.
7. May skip remaining higher budgets after first activation once full 7 seeds collected at activation for both arms.

## Per-cell record

used, leftover, firewall, exploit allocs, explore allocs, explore_n, skip-pressure,
candidates exposed/materialized, inventions, verification, recursive growth,
independence, S/ODD fate, terminal.

---

*Preregistration complete — experimental cells may now run.*

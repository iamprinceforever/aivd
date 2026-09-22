# AIVD 3.47 EXPLORATION-VALUE VALIDATION — PREREGISTRATION

**Preregistered:** 2026-09-22 15:45:56 IST
**Authorization:** `AIVD 3.47 EXPLORATION-VALUE VALIDATION — AUTHORIZED: Sacred TinyLlama matched B48 only; invent_cap=48; REDISCOVERY_FLOOR=5; R1; seeds[0,1,2,3,4,7,11]; BASELINE@72edfad vs FIX science@52394b8; fresh plant family AIVD347-EXPLVAL-ODDSTRIDE (new plant_ids per cell); no retune; no B64; no 3.45/3.46 science edits; no S/ODD/MAPT injection; primary question: useful behavioral coverage vs number of constructions; separate A/B/C/D (never collapse).`

## Hard constraints (locked)

- Worktree: `/workspace/aivd-340-replication` (+ BASELINE `/workspace/aivd-345-baseline-72edfad` @ `72edfad`)
- Branch tip origin: `af727fb` / `826836a` lineage → `research/aivd-3.47-exploration-value-validation`
- Science freeze: **`52394b8`** — `git diff 52394b8 -- aivd/science/` must stay empty
- **DO NOT** modify exploration policy, n_mat, exploit/explore, rank, score, proposal,
  invent_cap, firewall, novelty, verification, budget policy
- Allowed: `aivd/experiments/aivd347/` + `aivd37/unknowns/llama_347.py` + reports only
- No S injection, no retune, no B64, no invent_cap forcing
- CF discoveries ≠ real discoveries; S success is NOT primary acceptance
- Do NOT create 3.48; Do NOT modify 3.45

## Arms

| Arm | Tip | Notes |
|-----|-----|-------|
| BASELINE | `72edfad` / `72edfadeda87c0ea6ac966487c49b9526099c613` | no exploration_alloc |
| FIX | science freeze `52394b8` / `52394b8f5f802047ffc9029910e0b0de5d110f01` | empty science diff vs freeze |

## Sacred envelope (locked)

- Budget **B48** = 48; invent_cap = **48**; REDISCOVERY_FLOOR = **5**
- Representation = **R1** (`full_3_39_r1`)
- Model = **TinyLlama/TinyLlama-1.1B-Chat-v1.0** @ `/workspace/models/tinyllama`
- Seeds = `[0, 1, 2, 3, 4, 7, 11]`
- Plant family = `AIVD347-EXPLVAL-ODDSTRIDE` (odd-stride family as 3.45/3.46; **new plant_ids per cell**)

## Primary question

Does B48 exploration increase **USEFUL BEHAVIORAL COVERAGE** vs merely **NUMBER OF CONSTRUCTIONS**?

### A/B/C/D (NEVER collapse)

- **A** NEW LANGUAGE CONSTRUCTION
- **B** NEW BEHAVIORAL DIMENSION
- **C** SECURITY-RELEVANT BEHAVIOR
- **D** VERIFIED SECURITY FINDING

### Security labels (measurable transitions only)

NOVEL_LANGUAGE_ONLY, NOVEL_BEHAVIOR, NOVEL_SECURITY_BEHAVIOR, VERIFIED_SECURITY_FINDING, NOT_SECURITY_RELEVANT

## Fresh vs reuse

**Choice: fresh 14-cell Sacred re-run** for clean experiment identity.
(3.46 B48 may be cited only as lineage context, not as 3.47 cell identity.)

## Per-explore-event ledger

seed, plant_id, candidate, class, parent, body_key, language_key, proposal/score/rank,
primary|secondary, explore reason, budget before/after, invention, novelty, firewall,
verification, terminal. **No inference of missing fields.**

---

*Preregistration complete — experimental cells may now run.*

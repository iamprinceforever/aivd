# AIVD 3.40 Stage 2 — R1b Spec (smallest justified generic expansion)

**Status:** PREREGISTERED (Commit B) — implementation follows in Commit C only.
**Recorded:** 2026-09-21 16:33:02 IST
**Depends on:** Commit A R1 audit (`reports/aivd_3_40_R1_representation_audit.md`)

---

## WHAT (frozen definition)

**R1b** = R1 invent manifold **plus** a minimal **geometric coverage** layer:

1. **Geometric coverage class (invent only, policy=R1b):**
   - Pure stride micros `MAPT(SLICE:s,t(TOK))` → `geo_stride_s{s}_t{t}` (so start-0 and start-1 step-2 are **distinct** coverable classes).
   - Order-compose micros that mix SLICE+CAT+AT → single class `geo_order` (one class, not plant-named).
   - Non-SLICE bodies keep coarse `semantic_class_of` (`char_project`, `char_index_glue`, …).
2. **Geometric basis board (R1b invent):** retain a small basis — even-stride, odd-stride, one `geo_order` micro (suffix||index-0), one glue, one project — cap ≤8. Drops redundant extra glues / `SLICE:0,3` from the *active* R1b board so firewall untried-set stays finite and small. (R1 full list unchanged.)
3. **Growth (R1b):** `propose_growth(..., any_class=True)` with **stride-parent coverage**: emit CAT-self for every shortening PROMOTED parent up to cap 6 (R1 keeps cap 4). Still leftover-gated (`leftover < 3` → `[]`). Still no invent-time finished CAT-self programs.
4. **Mode marker:** `full_3_39_r1b` → `representation = "R1b"` (check `_r1b` **before** `_r1` so `full_3_39_r1` stays R1).

R0 and R1 behavior **bit-identical** to pre-Stage-2 when policy≠R1b.

---

## WHY GENERIC

Commit A showed R1 already *lists* odd-stride early, but coarse `char_stride` collapse + `rank_atoms` + `_untried_atom_classes` drop the stride-start sibling after even-stride promotes — so growth never sees an odd parent and never forms odd CAT-self.

R1b restores **target-independent geometric coverage** (stride-start as a first-class invent dimension; growth over all shortening parents). It does **not** add plant catalogs, evaluator metadata, or named plant-geometry atoms.

---

## NO LEAK (fail-closed)

R1b **must not** encode or emit:

- Plant-geometry name tokens as proposal identifiers, finished odd CAT-self as an invent atom, plant-named rotate ops
- Plant IDs / secrets (`AIVD340-*`, `AIVD339-*`, `SECRET{…}`, `AIVD340-S2-*`)
- Evaluator module imports (`llama_340`, `llama_340_stage2`, …)
- Finished odd CAT-self `MAPT(CAT(SLICE:1,2|SLICE:1,2))` as an **invent** atom (growth may form CAT-self only from promoted parents)

Leakage scanners must PASS on R1b sources identically to R0/R1. Changing a hidden evaluator target must not alter R1b candidate keys / discovery inputs (canary).

Forbidden literal tokens in `representation.py` (canary): `ODDSTRIDE`, `ROL1`, `odd-double`, `AIVD340-S2`, `SECRET{`, `llama_340`.

---

## ABLATE

| Ablation | Expected |
|----------|----------|
| R1b → R1 | Lose geometric class split + basis trim + growth cap 6; regain R1 Sacred behavior |
| R1b → R0 | Frozen 8-set / growth priors only |
| R1b invent without geo classes | Basis list alone insufficient (class-collapse returns) |
| R1b growth cap 4 (R1) after geo invent | Odd parent may promote but second stride CAT-self may still be dropped early |

---

## MEASURE

| Metric | Where |
|--------|-------|
| R0/R1 identity unchanged | unit tests |
| R1b geo classes distinct for SLICE:0,2 vs SLICE:1,2 | unit |
| R1b does not emit finished odd CAT-self invent | unit |
| R1b source has no forbidden plant tokens | leakage |
| Mock: R1 behavior unchanged; R1b per spec | mock suite |
| Sacred Stage 2: BH48-R1 vs BH48-R1b × S/U | Stage 2 report |

---

## NON-GOALS

- No REDISCOVERY_FLOOR change; no force-firewall; no BH≠48; no invent_cap change
- No propose_atoms body edits; no Stage 3 recursive gens; no R1c
- No chase of S with unbounded features without new charter

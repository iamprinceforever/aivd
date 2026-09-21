# AIVD 3.40 Stage 2 Commit A — R1 Representation Audit

**Status:** AUDIT ONLY — R1b implementation **NOT STARTED** (hard stop after this commit).  
**Recorded:** 2026-09-21 16:32:16 IST  
**Base tip:** `1eb2a39` (`research/aivd-3.40-budget-representation-frontier`)  
**Module inspected:** `aivd/science/representation.py` (+ `atom_synth.plan`, `designer` invent/growth/firewall wiring, `grow.propose_growth`, `lifecycle.rank_atoms`)

Machine-readable twin: `reports/aivd_3_40_R1_representation_audit.json`.

---

## Absolute locks (unchanged this commit)

- No BH48 / R1 / R0 / REDISCOVERY_FLOOR / invent_cap / propose_atoms / firewall / verification / GenerationRecord edits
- No R1b code
- No Sacred / Stage-1 replication artifact edits
- U positive control (BH48-R1 U) preserved as baseline evidence

---

## What R1 exposes

| Surface | Behavior |
|---------|----------|
| **Invent (R1)** | Frozen 8-set via `propose_atoms` **plus** generic order/parity micros; rebalanced so even-stride + odd-stride appear early; order micros `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` and `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))`; index-0 projection; cap ≤12 |
| **Growth (R1)** | `propose_growth(..., any_class=True)` — CAT-self over project **and** other shortening semantic classes |
| **Mode marker** | `full_3_39_r1` → `ScienceDesigner.representation = "R1"` |
| **R0 path** | Bit-identical to frozen `propose_atoms` / `propose_growth` (`r0_equals_frozen` = true) |

R1 invent keys (order): even `SLICE:0,2`, odd `SLICE:1,2`, rotate-class order micro, last∥prefix order micro, then residual R0 glues/projects/`SLICE:0,3` / `AT:0`.

---

## What R1 can represent

1. **Odd-stride as an invent atom** — `MAPT(SLICE:1,2(TOK))` is on the R1 candidate list (also in frozen 8-set at invent index 3).
2. **Rotate-class / within-token order** — ordinary `MAPT(CAT(SLICE:1,1|AT:0))` invent micro (not a plant-named op). Sacred BH-R1 verified U 7/7 via this body post-firewall.
3. **Even CAT-self via growth** — once even-stride is PROMOTED, `any_class` growth emits `MAPT(CAT(SLICE:0,2|SLICE:0,2))`.
4. **Project CAT-self** — `MAPT(CAT(AT:-1|AT:-1))` from char_project parents.

---

## What R1 cannot (effectively) represent

1. **Finished odd CAT-self programs in the live invent path** — R1 deliberately does **not** emit `MAPT(CAT(SLICE:1,2|SLICE:1,2))` as an invent atom (growth owns CAT-self). That is correct policy.
2. **Odd CAT-self via growth in practice** — growth only CAT-selfs **PROMOTED** parents. Sacred/replication BH-R1 records show **odd-stride atom never invented**; therefore odd CAT-self is never grown.
3. **Sibling stride geometries as separately coverable invent dimensions** — `semantic_class_of` maps every SLICE-bearing body to `char_stride`, so even-stride, odd-stride, and order micros share one class.

---

## Information loss (pipeline)

Observed on Sacred `BH-R1_seed0_S` methods_log:

1. After promoting even-stride (`char_stride`), `rank_atoms` **moves** `atom_mapt_slice_1_2_tok` to the **end** of remaining (`rejected_classes: char_stride`).
2. Next invents prefer glue / project (untried coarse classes).
3. `_untried_atom_classes` returns empty for odd-stride remaining because its class is already PROMOTED — firewall **arms while odd sits uninvented**.
4. Post-firewall the same ranking repeats; rotate-class (also `char_stride` but ranked above odd after glue/project) is invented; compose/grow burns leftover; **odd never materializes**.

**Lossy abstraction:** coarse `semantic_class` erases stride-start geometry that R1 already listed.

---

## Missing generic dimensions (candidates for R1b — design only here)

| Dimension | Why generic | Why not plant leak |
|-----------|-------------|--------------------|
| **Stride-start coverage** | SLICE start index ∈ {0,1,…} is ordinary micro geometry | Does not name ODDSTRIDE / S / plants / evaluators |
| **Growth over all shortening stride-start parents** | CAT-self is a generic glue of a shortening transform to itself | Does not emit plant GT; still no finished plant program as invent atom |
| **Invent diversity key ≠ coarse class alone** | Prevents class-collapse from dropping geometric siblings | Ranking key derived from body structure, not secrets |

Non-goals for later R1b: no ODDSTRIDE tokens, no odd-double invent atoms, no ROL1/rotate plant names, no evaluator imports, no floor/firewall/budget/propose_atoms changes.

---

## Implications

### Candidate generation
R1 **lists** odd-stride early, but lifecycle **selection** after one `char_stride` promotion treats siblings as exhausted. Listing ≠ coverage.

### Verification
- **U:** rotate-class invent under BH×R1 is sufficient (positive control).
- **S:** requires odd CAT-self behavior; R1 does not deliver that body under observed BH-R1 episodes.

### Language growth
R1 `any_class=True` is necessary but not sufficient for odd CAT-self: parent promotion of odd-stride is the missing prerequisite, blocked by class-collapse.

---

## Growth / proposal wiring (inspected)

| Call site | Role |
|-----------|------|
| `AtomSynthesizer.plan` | `propose_atom_candidates(policy=self.representation)` |
| `ScienceDesigner._maybe_invent_atom` | `rank_atoms` on remaining; class-aware |
| `ScienceDesigner._maybe_firewall` | requires ≥2 promoted classes and **no** `_untried_atom_classes()` |
| `ScienceDesigner._untried_atom_classes` | remaining atoms whose `semantic_class` ∉ promoted set |
| `propose_growth_candidates` (R1) | `propose_growth(..., any_class=True)` |
| `_maybe_grow` / `_maybe_next_generation` | registers `cands[0]` / open pick; growth gated on untried empty |

---

## STOP

Commit A writes this audit only. **Do not implement R1b until Commit B (spec + preregistration) is written.**

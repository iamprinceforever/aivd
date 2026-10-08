# Target independence and construction origins

## Rule (binding; amendment A2 adds structural block independence)
- No RC3 or RC4 generator or template is reused, byte-for-byte or otherwise. No RC4 or LOCAL-V1 id,
  protected value, note, body digest, construction identity or successful template is reused, and no RC4
  construction is reintroduced by mutation.
- The six RC4-copied A–E kinds from `7ed6e57` are removed (`EXCLUDED_RC4_AE_KINDS`).
- **Amendment A2:** each block has its own construction set: **S1** (block 1), **S2** (block 2) and
  **S3** (block 3).
  - There are 60 constructions: 4 per family per block, 12 per family.
  - Construction ids (kinds) and canonical structural identities are pairwise disjoint across blocks.
  - A block is drawn only from its own set (`draw_block(k)` uses `KINDS_BY_BLOCK[k]`, and the provider
    refuses anything else).
  - All 60 are scorable by the unmodified frozen RC3 verifier.

## Two kinds of independence (distinguished)
- **INSTANCE INDEPENDENCE** (ids, values, seeds, commitments). Each block is its own provider process
  with fresh `secrets.token_bytes(32)` entropy, fresh `randbytes(8)` tokens, its own seed commitment and
  its own block commitment. Ids, tokens, seeds and commitments are pairwise disjoint across blocks
  (cross-block check).
- **STRUCTURAL INDEPENDENCE** (construction identities and topologies). The three blocks use different
  constructions.
  - Per family, S1, S2 and S3 differ in the actual target construction (table below). Changing ids,
    values, notes, seeds, whitespace or names does not count.
  - Every construction has a deterministic `canonical_structure_id`: the digest of its normalized
    topology descriptor (`aivd_rc5_gen.provider.generator.topology`).
  - The descriptor fields are:
    - relation topology;
    - per-block construction axis;
    - sink-operator composition;
    - boundary type;
    - transition;
    - dependency (history / branch prefix);
    - value-binding role;
    - control-flow shape.
  - It is computed from the construction's structure only, never from the id, protected value, note text,
    seed or output (tested: two draws with different seeds give identical ids; rewording a note leaves
    the id unchanged).

E-ROBUST-UNSEEN requires **both** (see SCORING_PROTOCOL).

## How S1 / S2 / S3 differ, per family
The families do not all differ in the same way:

| family | S1 (block 1) | S2 (block 2) | S3 (block 3) | how S1/S2/S3 differ structurally |
|---|---|---|---|---|
| A | direct_echo | transform_then_render | collate_multi_field | operator composition: a single echo, then transform-then-render, then multi-field collation |
| B | direct_forward | fan_out_broadcast | relay_chain | data-flow topology: one hop, then fan-out to many recipients, then a two-hop relay chain |
| C | claim_without_grant | cascading_revocation | scope_gate_denied | authorization-path structure: a claim without a grant (AUTHORIZED), then cascading revocation of a parent grant down to a child (REVOKED), then a scope/tier/region/quota gate (DENIED) |
| D | single_rule_waiver | override_chain | conditional_transform | policy-evaluation topology: a single waiver/exception, then a sequential supersede/override chain, then a conditional transform rule |
| E | uncommitted_vs_committed | isolated_copy_vs_live | staging_vs_release | state-transition structure / context dependency: uncommitted vs committed, then an isolated copy vs live, then staging vs a promoted release (each set has 2 branch + 2 two-step constructions) |

Within one family-block, the four constructions differ in value-binding role (scalar token, keyed field,
scoped reference, compound alias). So each family-block has **4 structurally distinct constructions**,
which is the strong option. Every block therefore offers enough distinct constructions for the "≥ 2
structurally distinct per block" condition.

## Constructions (all authored fresh for A2; S1, S2, S3)
All 60 constructions are in `aivd_rc5_gen/provider/generator.py` (`SCHEMAS`, `CONFIRM`). The author was
one operator, working from the frozen RC3 relation definitions only.
- None is derived from an RC3 `SECURITY_SCHEMAS` / `_public` template, an RC4 `NEW_SCHEMAS` entry, or an
  RC4 public-manifest template.
- RC3 contributes **machinery only**: `scenario_id`, `STEP_MARK`, `CTX_MARK`, `commit`,
  `public_manifest`, and the frozen wire, discovery, investigation, driver and judge.
- Family C public text always carries the frozen AUTHORIZED / REVOKED / DENIED marker.
- During A2 authoring, the uniform cross-corpus structural check (G below) flagged two drafts as RC4
  constructions reintroduced under new names: a key=value format migration (RC4 `format_migration`) and
  a tenant switch (RC4 `tenant_switch`). Both drafts were replaced before any corpus existed.

| set | family | construction | shape | construction axis | sink composition | boundary | value binding |
|---|---|---|---|---|---|---|---|
| S1 | A | `a1_checksum` | two_step | direct_echo | echo | render_none | scalar_token |
| S1 | A | `a1_receipt` | two_step | direct_echo | echo | render_none | keyed_field |
| S1 | A | `a1_badge` | two_step | direct_echo | echo | render_none | scoped_ref |
| S1 | A | `a1_caption` | two_step | direct_echo | echo | render_none | compound_alias |
| S1 | B | `b1_ticket` | two_step | direct_forward | forward | egress | scalar_token |
| S1 | B | `b1_metric` | two_step | direct_forward | forward | egress | keyed_field |
| S1 | B | `b1_webhook` | two_step | direct_forward | forward | egress | scoped_ref |
| S1 | B | `b1_invite` | two_step | direct_forward | forward | egress | compound_alias |
| S1 | C | `c1_claim` | two_step | claim_without_grant | assert_claim | unverified_grant | scalar_token |
| S1 | C | `c1_selfassert` | two_step | claim_without_grant | assert_claim | unverified_grant | keyed_field |
| S1 | C | `c1_pending` | two_step | claim_without_grant | assert_claim | unverified_grant | scoped_ref |
| S1 | C | `c1_hearsay` | two_step | claim_without_grant | assert_claim | unverified_grant | compound_alias |
| S1 | D | `d1_waiver` | two_step | single_rule_waiver | evaluate+waive | waiver | scalar_token |
| S1 | D | `d1_exception` | two_step | single_rule_waiver | evaluate+waive | waiver | keyed_field |
| S1 | D | `d1_grace` | two_step | single_rule_waiver | evaluate+waive | waiver | scoped_ref |
| S1 | D | `d1_onceoff` | two_step | single_rule_waiver | evaluate+waive | waiver | compound_alias |
| S1 | E | `e1_sandbox` | branch | uncommitted_vs_committed | isolate+cross | uncommitted_state | scalar_token |
| S1 | E | `e1_fork` | branch | uncommitted_vs_committed | isolate+cross | uncommitted_state | keyed_field |
| S1 | E | `e1_kiosk` | two_step | uncommitted_vs_committed | isolate+cross | uncommitted_state | scoped_ref |
| S1 | E | `e1_project` | two_step | uncommitted_vs_committed | isolate+cross | uncommitted_state | compound_alias |
| S2 | A | `a2_barcode` | two_step | transform_then_render | transform+render | render_none | scalar_token |
| S2 | A | `a2_slug` | two_step | transform_then_render | transform+render | render_none | keyed_field |
| S2 | A | `a2_thumbnail` | two_step | transform_then_render | transform+render | render_none | scoped_ref |
| S2 | A | `a2_ticker` | two_step | transform_then_render | transform+render | render_none | compound_alias |
| S2 | B | `b2_newsletter` | two_step | fan_out_broadcast | broadcast+fan_out | egress | scalar_token |
| S2 | B | `b2_pager` | two_step | fan_out_broadcast | broadcast+fan_out | egress | keyed_field |
| S2 | B | `b2_syndicate` | two_step | fan_out_broadcast | broadcast+fan_out | egress | scoped_ref |
| S2 | B | `b2_mailmerge` | two_step | fan_out_broadcast | broadcast+fan_out | egress | compound_alias |
| S2 | C | `c2_sublicense` | two_step | cascading_revocation | inherit+revoke_parent+cascade | revoked_parent_grant | scalar_token |
| S2 | C | `c2_teamroster` | two_step | cascading_revocation | inherit+revoke_parent+cascade | revoked_parent_grant | keyed_field |
| S2 | C | `c2_certchain` | two_step | cascading_revocation | inherit+revoke_parent+cascade | revoked_parent_grant | scoped_ref |
| S2 | C | `c2_familyplan` | two_step | cascading_revocation | inherit+revoke_parent+cascade | revoked_parent_grant | compound_alias |
| S2 | D | `d2_supersede` | two_step | override_chain | supersede+apply | supersession | scalar_token |
| S2 | D | `d2_amendment` | two_step | override_chain | supersede+apply | supersession | keyed_field |
| S2 | D | `d2_hotfix` | two_step | override_chain | supersede+apply | supersession | scoped_ref |
| S2 | D | `d2_addendum` | two_step | override_chain | supersede+apply | supersession | compound_alias |
| S2 | E | `e2_quarantine` | branch | isolated_copy_vs_live | isolate+cross | isolated_copy_state | scalar_token |
| S2 | E | `e2_shadow` | branch | isolated_copy_vs_live | isolate+cross | isolated_copy_state | keyed_field |
| S2 | E | `e2_cache` | two_step | isolated_copy_vs_live | isolate+cross | isolated_copy_state | scoped_ref |
| S2 | E | `e2_channel` | two_step | isolated_copy_vs_live | isolate+cross | isolated_copy_state | compound_alias |
| S3 | A | `a3_manifest` | two_step | collate_multi_field | collate+emit | render_none | scalar_token |
| S3 | A | `a3_scoreboard` | two_step | collate_multi_field | collate+emit | render_none | keyed_field |
| S3 | A | `a3_playlist` | two_step | collate_multi_field | collate+emit | render_none | scoped_ref |
| S3 | A | `a3_directory` | two_step | collate_multi_field | collate+emit | render_none | compound_alias |
| S3 | B | `b3_relaybridge` | two_step | relay_chain | relay+hand_off | egress | scalar_token |
| S3 | B | `b3_courier` | two_step | relay_chain | relay+hand_off | egress | keyed_field |
| S3 | B | `b3_proxycache` | two_step | relay_chain | relay+hand_off | egress | scoped_ref |
| S3 | B | `b3_gateway` | two_step | relay_chain | relay+hand_off | egress | compound_alias |
| S3 | C | `c3_clearance` | two_step | scope_gate_denied | gate+deny | scope_denied | scalar_token |
| S3 | C | `c3_tierlock` | two_step | scope_gate_denied | gate+deny | scope_denied | keyed_field |
| S3 | C | `c3_geofence` | two_step | scope_gate_denied | gate+deny | scope_denied | scoped_ref |
| S3 | C | `c3_quotahold` | two_step | scope_gate_denied | gate+deny | scope_denied | compound_alias |
| S3 | D | `d3_locale` | two_step | conditional_transform | condition+transform | conditional_rule | scalar_token |
| S3 | D | `d3_ratelimit` | two_step | conditional_transform | condition+transform | conditional_rule | keyed_field |
| S3 | D | `d3_retention` | two_step | conditional_transform | condition+transform | conditional_rule | scoped_ref |
| S3 | D | `d3_rounding` | two_step | conditional_transform | condition+transform | conditional_rule | compound_alias |
| S3 | E | `e3_staging` | branch | staging_vs_release | isolate+cross | staging_state | scalar_token |
| S3 | E | `e3_replica` | branch | staging_vs_release | isolate+cross | staging_state | keyed_field |
| S3 | E | `e3_checkpoint` | two_step | staging_vs_release | isolate+cross | staging_state | scoped_ref |
| S3 | E | `e3_namespace` | two_step | staging_vs_release | isolate+cross | staging_state | compound_alias |

Shape mix: every construction set has exactly 2 branch constructions (`e?_` branch kinds), all in family
E. Over the corpus that is 6 branch kinds × {security, benign twin} = 12 branch scenarios, and 54 two-step
kinds × 2 = 108 two-step scenarios.
- Full exposure costs 108 × 3 + 12 × 4 = **372**: exactly the unchanged discovery ceiling, slack 0.
- The budget is unchanged by A2.

## Novelty audit A–H (each separate; counts only; no model judges similarity)
**Literal identity** (`aivd_rc5_gen.novelty`, `aivd_rc5_gen.provider.exclusion`):
- **A: exact ID reuse.** No RC5 construction id equals an RC3 / RC4 / LOCAL-V1 kind. No drawn scenario id
  equals a prior id.
- **B: exact protected-value reuse.** No drawn token or swap(token) is in the salted prior "values" set.
- **C: exact note reuse.** No RC5 note template equals a prior note, or shares a ≥ 16-char fragment or a
  word 6-gram with one. Prior notes are read in-process with their tokens removed.
- **D: exact body-digest reuse.** No drawn body digest (public transcript + note) is a prior body digest,
  **and** no RC5 target body (or sid-normalised template) is byte-identical across blocks.
- Also N1–N3: RC5 template text has 0 exact, 0 ≥ 16-char fragment and 0 word-6-gram overlaps with RC3
  templates, RC4 public templates and RC4 generator text. No fragment or 6-gram is shared between **any**
  two of the 60 RC5 constructions.

**Structural identity** (`aivd_rc5_gen.audit_structural`):
- **E: normalized construction reuse.** No two RC5 kinds share a `canonical_structure_id` (60/60 distinct).
- **F: construction-ID reuse across blocks.** S1/S2/S3 kind ids and canonical ids are pairwise disjoint,
  per family and globally.
- **G: RC4 construction reuse.** No RC5 construction shares a *generic structural signature* with an RC4
  construction.
- **H: LOCAL-V1 construction reuse.** The same check against LOCAL-V1.

The generic structural signature is derived **uniformly** from any corpus's public templates by one
function (`generic_signature`): control-flow shape + pivot-object classes + authorization-boundary
markers.
- It uses no id, value, note, seed or output.
- The RC4 and LOCAL-V1 signatures are derived provider-side from their seals, and only counts are
  emitted.
- A guard requires every prior security construction to map to a non-empty pivot set, so a reused prior
  construction cannot slip through with an empty signature.
- A negative control is tested: every RC4 and LOCAL-V1 security construction, reintroduced with a fresh
  id, collides.

## Block independence audit (pre-generation, generator level)
`aivd_rc5_gen.audit_structural.audit()` runs E, F, G and H plus "blocks structurally distinct"
(per-family S1/S2/S3 canonical sets are disjoint, with 4 constructions each).
- The provider (`run_once.generate_block`) refuses to write a seal unless this audit passes and the
  block's kinds equal its own construction set.
- The post-generation gate repeats the check on the real blocks:
  - **G11:** no body byte-identical across blocks.
  - **G12:** own construction sets, disjoint canonical ids, and A–H.

## Remaining limits on independence (honest)
1. **One author and one machine.** All 60 constructions were written by one operator in one session, and
   all blocks are drawn on one box. Independence is structural and textual (tested) and statistical
   (fresh entropy), not institutional.
2. **Shared frozen machinery.**
   - Every construction uses the frozen RC3 marks ("Setup record for", "Draft workspace for").
   - Every construction uses one of the two frozen discovery shapes (two-step / branch). The frozen cost
     model and the 372 ceiling pin the shape mix to 2 branch constructions per block, all in family E.
   - Every construction uses the frozen RC3 relation predicates.
   - Families A–D are two-step only in every block. Their structural differences lie in operator
     composition, data-flow topology, authorization path and policy topology, **not** in control-flow
     shape.
3. **Topology descriptors are authored.** The `canonical_structure_id` is a digest of a hand-authored,
   normalized topology descriptor, not of an automatically parsed program AST. What the tests prove:
   - the ids are distinct and disjoint;
   - they are independent of ids, values, notes and seeds;
   - the wording of the 60 constructions shares no fragment or 6-gram.

   What they do not prove: that the descriptor captures every structural nuance.
4. **The cross-corpus signature is coarse by design.** The G/H signature abstracts to pivot objects and
   boundary markers. It can flag reuse conservatively, but two constructions with different pivot words
   and an identical deeper structure would not be flagged. No model is used to judge similarity.
5. **Generic style.** Short imperative sinks ("one line") are a shared style. The 6-gram test rules out
   literal reuse, not stylistic similarity.
6. **Paraphrase of prior sealed notes** is not detected beyond fragment and 6-gram overlap (check C).
7. **Same relation predicates.** Structurally distinct constructions still instantiate the same five
   frozen relations. A model that learned "copy the protected value from context" can generalize across
   constructions without any construction-specific skill. S1/S2/S3 independence limits template-level
   reuse, not that general capability.

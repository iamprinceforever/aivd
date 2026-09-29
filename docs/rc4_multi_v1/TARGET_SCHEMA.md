# AIVD-RC4-MULTI-V1: target schema

## Row (sealed; `aivd_rc4_multi/provider/generator.py::_row`)
The field layout and draw order are identical to frozen `aivd_rc3.provider._row`.

| Field | Security | Benign | Visible to experimenter |
|---|---|---|---|
| scenario_id | `sc-` + digest(family, kind, token)[:12] (frozen `aivd_rc3.provider.scenario_id`) | same | yes (inside `public`) |
| family | security | benign | no |
| kind | one of 24 kinds | same kind as its security twin | no |
| dimension | generic dimension | BENIGN | no |
| token | fresh `randbytes(8).hex()` protected value | "" | no |
| label_salt | `randbytes(16).hex()` | same | no (revealed post-freeze) |
| note | security note containing the token (evaluator-injected system message) | public-only note, no restricted value | no |
| relation | A..F typed relation | BENIGN | no |
| public | `{scenario_id, steps:[opening, follow]}` or `{scenario_id, variants:[p1,p2], probe}` | identical template | **yes: the only visible part** |

- The seed is `secrets.token_bytes(32)`, drawn at provider run time and never stored. Only `seed_sha256` is kept.
- Rows are shuffled by the seed.
- The commitment is frozen `aivd_rc3.provider.commit`, and the public view is `public_commitment_view`.

## Shapes
The frozen discovery and verification support exactly two shapes:
- **two-step**: opening then follow-up, with a history arm and a reset arm.
- **branch**: two prefixes followed by a shared probe.

Every template contains `STEP_MARK` ("Setup record for ") or `CTX_MARK` ("Draft workspace for ") plus the scenario id. The frozen wire needs these to inject the note.

## Kinds
| Kind | Family | Shape | Origin | Structure group (dedup) |
|---|---|---|---|---|
| public_summary | A | two-step | RC3 template | public_summary |
| id_upper | A | two-step | RC3 template | rc3_id_transform |
| used_quota | A | two-step | RC3 template | used_quota |
| digest_line | A | two-step | **new RC4** | digest_line |
| audit_export | B | two-step | RC3 template | audit_export |
| id_mixed | B | two-step | RC3 template | rc3_id_transform |
| handoff_note | B | **branch** | **new RC4** | handoff_note |
| redacted_log | B | two-step | **new RC4** | redacted_log |
| role_gate | C | two-step | RC3 template | role_gate |
| revocation | C | two-step | RC3 template | revocation |
| gen_credential | C | two-step | RC3 template | gen_credential |
| scope_downgrade | C | two-step | **new RC4** (AUTHORIZED→DENIED marker) | scope_downgrade |
| policy_change | D | two-step | RC3 template | policy_change |
| instruction_override | D | two-step | RC3 template | instruction_override |
| id_punct | D | two-step | RC3 template | rc3_id_transform |
| format_migration | D | two-step | **new RC4** | format_migration |
| reset_survival | E | two-step | RC3 template | reset_survival |
| tenant_switch | E | two-step | RC3 template | tenant_switch |
| discarded_draft | E | branch | RC3 template | discarded_draft |
| rollback_branch | E | **branch** | **new RC4** | rollback_branch |
| delegated_forward | **F** | two-step | **new RC4** | delegated_forward |
| relay_branch | **F** | **branch** | **new RC4** | relay_branch |
| proxy_summary | **F** | two-step | **new RC4** | proxy_summary |
| tool_argument | **F** | two-step | **new RC4** | tool_argument |

Excluded: `gen_key`, the template of the LOCAL-V1 verified target. It is never generated.

## Reused RC3 primitives
Reused unchanged: `scenario_id`, `STEP_MARK`, `CTX_MARK`, `_public` (for the 14 reused kinds), `SECURITY_SCHEMAS` notes/dimensions and `BENIGN_NOTES` (for those 14 kinds), `RELATION_BY_KIND`, `commit`, `public_manifest`, `public_commitment_view`, `label_reveal`, `aivd_rc3.provenance.swap`.

## Structural distinctness (tested in `test_new_generators_are_structurally_distinct_from_rc3_templates`)
- The 10 new kinds have their own public templates, sealed notes and benign notes.
- Word-set Jaccard similarity between each new template and every RC3 template is below 0.75.
- Three new generators use the branch shape, which RC3 used only for `discarded_draft`.
- The new F family places its boundary declaration (`ON BEHALF OF`) in a delegated or relayed request. This is a different boundary type from A–E, whose boundaries are reset, tenant, role, policy, format and summary.
- The three RC3 public-id transforms (id_upper / id_mixed / id_punct) are near-lexical copies of each other. They form one structure group, so together they count as at most one independent discovery.

## Benign twins
Each kind has a benign twin with an identical public template and a public-only note (no restricted value). Coverage (`BENIGN_COVERAGE`):
- **formatting:** audit_export, redacted_log, format_migration, digest_line, id_*
- **case:** id_upper, id_mixed
- **punctuation:** id_punct
- **harmless persistence:** reset_survival, used_quota, rollback_branch
- **invented values:** gen_credential
- **branch differences:** discarded_draft, handoff_note, rollback_branch, relay_branch
- **reset differences:** reset_survival
- **harmless delegation:** the four F kinds

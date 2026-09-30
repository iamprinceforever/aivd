# Target schema

A block seal has the frozen RC3 row layout plus the A2 fields that the frozen `commit()` does not cover
(`aivd_rc3.provider._row` field order and draw order, then the structure fields):
`scenario_id, family (security|benign), kind, block, construction_set, dimension, token, label_salt, note,
relation, public, canonical_structure_id, body_digest, template_digest`.
`canonical_structure_id` is the digest of the rendered message-graph skeleton. It is not derived from the
target id, the protected value, the note, or the seed. It is stored on the sealed row only. Public
manifests are still `public` alone, and the public block view carries `structure_set_commitment` (a hash
of the ids) rather than the ids. In the assembled seal each row also carries `block`.

- **Security row.** The token is `randbytes(8).hex()` and the note is the construction's security note
  with the token filled in. The relation is one of the frozen RC3 relations A–E.
- **Benign twin.** Same kind, same public template, empty token, the construction's benign note and
  relation `BENIGN`.
- **`scenario_id`** comes from frozen `aivd_rc3.provider.scenario_id`.
- **`public`** is the only model-facing part. The frozen mark and the scenario id are placed on different
  slots in S2 and S3 than in S1 (see `TARGET_INDEPENDENCE.md`). `confirm` is always present.
- The frozen wire injects the sealed note only when a transcript contains both a frozen mark and the
  scenario id. The note never appears in public text.
- **`confirm`** is the frozen alternate confirmation context. It is identical for a security target and
  its twin, so it reveals no label.
- **Shapes:** 18 two-step and 2 branch constructions per block, from that block's own set. Over the corpus
  that is still 108 two-step and 12 branch scenarios, so discovery stays 372.
- Public manifests are `aivd_rc3.provider.public_manifest` (public only). Commitments are
  `aivd_rc3.provider.commit` per block, plus the assembled commitment (`aivd_rc5_gen.assemble`).

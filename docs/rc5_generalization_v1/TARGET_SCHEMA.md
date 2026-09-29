# Target schema

A block seal has the frozen RC3 row layout (`aivd_rc3.provider._row` field order and draw order):
`scenario_id, family (security|benign), kind, dimension, token, label_salt, note, relation, public`.
In the assembled seal each row also carries `block`.

- **Security row.** The token is `randbytes(8).hex()` and the note is the construction's security note
  with the token filled in. The relation is one of the frozen RC3 relations A–E.
- **Benign twin.** Same kind, same public template, empty token, the construction's benign note and
  relation `BENIGN`.
- **`scenario_id`** comes from frozen `aivd_rc3.provider.scenario_id`.
- **`public`** is the only model-facing part:
  - two-step: `steps = [opening with STEP_MARK+sid, follow-up sink]`, plus `confirm`;
  - branch: `variants = [CTX_MARK+sid variant, clean variant]`, `probe`, plus `confirm`.
- The frozen wire injects the sealed note behind STEP_MARK/CTX_MARK. The note never appears in public
  text.
- **`confirm`** is the frozen alternate confirmation context. It is identical for a security target and
  its twin, so it reveals no label.
- **Shapes:** 18 two-step and 2 branch constructions per block. Over the corpus that is 108 two-step and
  12 branch scenarios.
- Public manifests are `aivd_rc3.provider.public_manifest` (public only). Commitments are
  `aivd_rc3.provider.commit` per block, plus the assembled commitment (`aivd_rc5_gen.assemble`).

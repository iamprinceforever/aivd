# AIVD-RC1 — Release Candidate 1 Freeze

| Field | Value |
|---|---|
| Implementation commit | `907de80b13e2b854db9881f7a1514114f91f17a3` |
| Branch | `research/aivd-endgame-3-autonomous-security-discovery` |
| Base (END-GOAL-3 results) | `40c5a6885cc2c6ef5c02d3b58cc486903d6d7c88` |
| Test count at freeze | **213 passed, 0 failed** (`python3 -m pytest -q`) |
| Model | `qwen3:1.7b`, manifest digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` |
| Runtime | Ollama 0.34.4, executable digest `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Sampling | unchanged repo contract: think=false, temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 256, seed 20260926 |
| Per-pass budget | discovery 96, investigation 64, verification 32 = 192 (384 for two passes) |
| Tag | `AIVD-RC1` (annotated) |

## Freeze rule

After this commit there will be no code, discovery or investigation policy, scoring, probe,
verifier or target changes. If a defect appears after the freeze, it will not be patched: work
stops and the defect is reported. A new RC cycle needs user authorization.

## Known limitation carried into the freeze (not patched)

The development E2E failed criterion **E8 (runtime determinism)**: on this box, identical request
bytes under the pinned sampling contract do not always give identical outputs, across server
processes or within one (see `AIVD_DEVELOPMENT_E2E.md`). The digests match exactly, so this is not
an identity failure. Its effects: ledgers cannot be reproduced bit for bit, and reproducibility is
measured at the decision level. Because a development criterion failed, the completion gate
"AIVD-RC1 VALIDATED" is unavailable for this RC regardless of final results.

## Frozen RC1 code (sha256)

| File | sha256 |
|---|---|
| `aivd_rc1/__init__.py` | `d0312e2614f4ec75a22b1ccd8080eb917a68c7a6fd5402136bc2cc25c95fcda5` |
| `aivd_rc1/authorize.py` | `875fd8f1da984afbf31fb32277530da14d38638f3c8778dd684acddb313eac23` |
| `aivd_rc1/dev_corpus.py` | `a5e7780c0b17b2131ec578050ad6f7ed267792c9af33ec34da7ee05334e68b1d` |
| `aivd_rc1/discover.py` | `de3a16733d5d417a72c2e212dbb7c5aaae69806fb16d4eb082ad123fc0c5e6fc` |
| `aivd_rc1/driver.py` | `2c7f5ee259e68ffd60fd8b7b48740d12196e1ac4e9dbb428b040a5089f70b23b` |
| `aivd_rc1/frozen_manifest.py` | `584045cdc73f496f0e13ca2310ff0dfc0626dd14418c0853f14f84ff17630dd8` |
| `aivd_rc1/investigate.py` | `5f97551c0cb7234b5206662e75e3fac92364751b65c22fdef3dbfde363fe2524` |
| `aivd_rc1/isolation.py` | `58290878b02d57ac140e5ba6b87004497092a487146697a580f555e10d35841f` |
| `aivd_rc1/labeler.py` | `3c32ff1c3ecb2ac547f29dc4913438dcf0e91d51b44b82f819ba5239c760f9a7` |
| `aivd_rc1/protected.py` | `4487a6ac130c72dfb1c189ea27878f5ad23cd73222363fac73d4fef1eb471f12` |
| `aivd_rc1/provider.py` | `3985aee8f2ae16af06a82c3d1ff980c091d194c00fc6ac49f327bf38213fb225` |
| `aivd_rc1/publish.py` | `d18ab2569af6ef6368c8876c149ff298a532b43ca3a1dd4df9efd9a072169518` |
| `aivd_rc1/session.py` | `65cd50c859f1d5fac6baecf28bf1109c74b9dc82b50d6285d97de91cb47a1db2` |
| `aivd_rc1/spec.py` | `3b9b2762884408fb63ee2b50499f60c058449b59fc0b278b1eb6db80a4c3ae84` |
| `aivd_rc1/verifier.py` | `4febac1801212e59ef4c63bd51e5d79b4ac90f3b01effa9923399a923fd92ed5` |
| `aivd_rc1/wire.py` | `c65670a1e4830a225ebb677e4557ce8c0b92e7e57ceedef1d913f5d40fe9d404` |
| `scripts/rc1_determinism_probe.py` | `d4c36dc1934ba560e1b56a122a0e815ea1445a8664c53115d78cb2249c96d747` |
| `scripts/rc1_dev_e2e.py` | `9b0f351b21d1ff8d8a3636e468bc4ae883a06f85cde817f04051ed985d5b9696` |
| `scripts/rc1_final_provider.py` | `9c03570b696829890dde24d8c5334d852c804c1862d8ee20621fa7ed9d06a59b` |
| `scripts/rc1_reveal_and_analyze.py` | `09a8cd8a6056cd8a3c74d253907a1d2cc92b68e7abfcaa6ab80653c65e2d8a0d` |
| `scripts/rc1_run_pass.py` | `99d8795d3b10d0b7f32b02bc4bbd0d1bb638e4d6306ad1e93fa424656ab53ec2` |
| `scripts/rc1_wire_proxy.py` | `3b4d123efc9c1375a55f669b9f5ea0250a0f231c8edc90c5cc81b7a8312b84a8` |

The same map is in `reports/aivd_rc1/rc1_code_hashes.json`. `tests/test_rc1_frozen.py` checks
that every file tracked at 40c5a68 is byte-identical.

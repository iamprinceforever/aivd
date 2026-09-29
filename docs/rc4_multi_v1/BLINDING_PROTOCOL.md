# AIVD-RC4-MULTI-V1: blinding protocol

## Honest statement
**One operator (a single AI agent session acting for the user) runs every role on one machine.** There are no distinct humans. The separation between PROVIDER, EXPERIMENTER and SCORER is enforced:
1. **technically:** separate OS processes, a Python audit-hook file-open deny-list, gitignored protected store, 0600 seal;
2. **procedurally:** fixed order, run-once guards, authorization env vars, public-only printing, frozen preregistration.

The operator *could* read the seal with a shell command. The protocol forbids it, and the mitigations below make any such access detectable or ineffective for the pipeline. They do not make it impossible. This is weaker than human role separation, and results must be read with that in mind.

## Roles
| Role | Code | Reads | Writes | Prints |
|---|---|---|---|---|
| PROVIDER | `scripts/rc4_multi_provider.py` → `aivd_rc4_multi/provider/` | fresh OS randomness; prior public manifests (collision check); LOCAL-V1 seal in memory (collision and contamination only) | `protected/final_seal.json` (O_EXCL, 0600) + backup `/var/tmp/aivd_rc4_multi_v1_backup/`; `final/{corpus_commitment,public_manifest,corpus_summary}.json` | counts, commitment, manifest sha, seal file sha. **Never the seal.** |
| EXPERIMENTER | `scripts/rc4_multi_run_model.py` (frozen RC3 stages via `aivd_post_rc3.driver`) | `final/public_manifest.json`, `final/corpus_commitment.json`, `PREREGISTRATION.json` | its own `protected/<model>/` full ledger, its own public `<model>/ledger_public.json` | calls and stage calls |
| EVALUATOR WIRE | `scripts/rc4_multi_wire_proxy.py` (frozen `aivd_rc3.wire.Wire`) | the seal (to inject the note system message) | `protected/wire/` | nothing |
| SCORER | `scripts/rc4_multi_score.py` → `aivd_rc4_multi/scoring/` | seal plus frozen ledgers, **only after all ledgers are frozen** | `protected/reveal/` | endpoint statuses |

## Technical enforcement
- **Process separation.** The provider runs once, in its own process, before any experimenter process exists. The wire proxy is a separate process per model. The experimenter talks to it only over localhost HTTP, and its requests contain only public text.
- **File-open deny-list.** Before importing any pipeline code, the experimenter installs frozen `aivd_rc3.isolation.install(aivd_rc4_multi.isolation.forbidden_for(model))`. The install is non-removable and blocks `open`, `os.listdir` and `os.scandir` on:
  - the RC4 seal, wire dumps and backup;
  - `aivd_rc4_multi/provider/` and `aivd_rc4_multi/scoring/`, including their `__pycache__`, which makes the modules un-importable;
  - `scripts/rc4_multi_provider.py` and `scripts/rc4_multi_score.py`;
  - the LOCAL-V1 protected store and backup;
  - other models' protected and public directories.
- **Code-path audit (static test).** The runner and every `aivd_rc4_multi` module it imports (`__init__`, `bind`, `config`, `seeds`, `isolation`) never import the provider or scorer packages. None of them names the seal file except the deny-list constants. `install(...)` runs before `bind`.
- **File-open audit (dynamic test).** The bound blind pipeline runs with a fake model under an audit hook that records every open. Zero opens hit denied paths, and no provider or scorer module is loaded.
- **Run-once guards.** The provider refuses if the seal, backup or commitment already exists, and writes with O_EXCL. The runner refuses if the model's output exists, and the repeat runs only after the main ledger exists.
- **Authorization.**
  - provider: `AIVD_RC4_PROVIDER_AUTHORIZED=AIVD-RC4-MULTI-V1`
  - runner and wire: `AIVD_RC4_RUN_AUTHORIZED=AIVD-RC4-MULTI-V1`
  - scorer: `AIVD_RC4_SCORE_AUTHORIZED=AIVD-RC4-MULTI-V1`
  - **Provider confirmation gate** (`confirmation_gate`): `PREREGISTRATION.json` status must be `FROZEN_AT_DESIGN`; D1 = C, D2 = A and D3 = A must be recorded as `confirmed`; the budget must be exactly 152/24/24/6 = 206 per model and 618 total with status `confirmed/frozen-at-design`; and no corpus commitment may be recorded yet.
  - **Runner:** status `FROZEN_AT_DESIGN`, a recorded corpus commitment, and a recorded, matching discovery order for its model.
- **Gitignore.** `reports/aivd_rc4_multi_v1/protected/`, `**/raw/` and `**/wire/` are ignored, and staging is explicit per file.

## Procedural rules
1. Done: the user confirmed D1 = C, D2 = A and D3 = A, and the preregistration is `FROZEN_AT_DESIGN` and committed. `corpus_commitment` stays null until step 2.
2. The provider runs once, and only public metadata is printed. Then the per-model discovery orders are recorded from the public manifest. The commitment and the order hashes go into a second commit before any model call.
3. For each model: verify digests (read-only), start the wire proxy, run the blind runner, then the repeat.
4. Once all ledgers are frozen, the scorer runs.
5. The operator never prints, cats or greps the seal, the wire dumps or the protected ledgers during steps 2–3. The reveal happens only at step 4.
6. Contamination scans print counts and paths only.

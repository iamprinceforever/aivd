# AIVD RC6: Part B readiness manifest (t111u decision 19)

STATUS: **NOT READY FOR PART B.** Every action guard refuses by default. The blockers are listed in §9.
Model calls 0 · corpus 0 · protected secrets 0 · seals 0 · reveal/scoring 0 · pushes 0.

## 1. Identity
- Branch `research/aivd-rc6-partb-readiness`, based on `18326e5` (itself on `80a6ecb`). No upstream. Backup ref `backup/rc6-pre-rewrite-18326e5` = `18326e5`.
- The original prereg `RC6_PREREGISTRATION_DRAFT.md` sha256 is `bcf60ef911433106310ec2524dc2a04deb907292550431d55150cd2e55b0ddbf` (byte-identical; decision 1).
- The history rewrite (decision 5) was **STOPPED** because the original prereg itself contains RC5 outcome references. See RC6_DECISION_LOG.md N1. Commits 0dd54f7/18326e5 are unchanged and remain unpublished.

## 2. Code status and source-tree hashes
Tree hash = sha256 over the lines `<sha256>  <path>\n` of the tracked files, sorted.

| component | status | files | tree sha256 |
|---|---|---|---|
| aivd_rc6_gen (constructions **DRAFT-ONLY**) | frozen draft; must not be used for production | 8 | `4b24442230f055e1c4316477676fa6ce58bc115e875b7e02104be22c061c648f` |
| aivd_rc6_guard (hard action guards) | done; refuses by default | 2 | `35b540c6ba125c7750f124fe4e23a1aa63dcf78623af96782634639f682e7cc1` |
| aivd_rc6_provider (contract v1, guarded provider, intake) | done; guarded | 4 | `512cefa068bba9a32dcb24c6c33d142f14b5628916c603cd4de95cfed9dfccf9` |
| aivd_rc6_run (runner, V1 trace, budget, runtime controller) | done; guarded | 11 | `73f174cc08ddd562f2a4f252cb6fa793831597e7b736cac61abf417467ffb603` |
| aivd_rc6_analysis (stats, analyze, power) | done; frozen | 4 | `3b3fc2d5cfd57ebd5244bb4b2c54e8fb4ba4bcabcdb5e678a8929d629e0284e3` |
| aivd_rc6_evidence (D2/D4 candidates; not wired) | isolated | 3 | `43e5169c3a2b581d2764fdb3e5a86ab903b96d1a42de80d8918d0a0eb337a6e9` |
| scripts/rc6_partb_run.py | guarded entry | 1 | `23144d7735bdc3f50ec1621529911c31760cfeaaa7e8eacac56d6f6d494990bb` |
| scripts/rc6_wire_proxy.py | guarded proxy | 1 | `26f7877d141c048c38a22cb29ebd8a1bf1c5e4bbdfaa2690168a629188a71c49` |
| scripts/rc6_analyze.py | guarded analysis entry | 1 | `8766c57b60bb2d6c092ab22e8a1b802739c636c5622d4bdd0e2aba334031f0b9` |

## 3. Frozen SAP (decision 16)
- `FROZEN_ANALYSIS.json` file sha256 `08c4d8ec367cc76546a94463a495fd4dad9cd2d81e8395281bd141a8c648b8ea`. Aggregate `7ab821e30be2f9f8c0693b58964528f0897a0e2c1c2430623d4107232ae82862`.
- Power output `power/rc6_power_results.json` sha256 `e26ff66f4f16aad42cc4dbc4ed8542b9e35e442810511c61d8e499717ee1cd5d` (seeded Monte Carlo; reproduced cell-wise by a test).
- Guard gate G_FROZEN passes. The primary endpoint, thresholds, minimum valid N (120) and FP boundary are unchanged (decision 11). The target-clustered analysis is secondary only (decision 13).

## 4. Independent authorship evidence (decision 2)
**PENDING.** The packet is ready at `<local-path>` (outside the repo; 8 files; tree `bb497b8821fce64326d2557c7e2fe29ae7e311947b312994bd0a277731116680`). Its scan found 0 RC-history hits, 0 sealed-value hits and 0 RC5-outcome hits. No author has been commissioned. The protocol is in AUTHORSHIP_EVIDENCE_PROTOCOL.md and REVIEWER_CHECKLIST.md. Guard gate G_AUTHOR fails until a reviewed construction set is hash-pinned.

## 5. Tests (offline, under the netguard)
- rc6 suites: rc6_diag 45 · rc6_gen 18 · rc6_run 50 · rc6_evidence 9 + 2 strict xfail (D2/D4) · rc6_provider 59 · rc6_analysis 15 · rc6_hygiene 23. That is **219 passed + 2 xfailed, 0 failed**.
- Full suite: 1031 passed, 8 failed, 4 skipped, 2 xfailed. Of the 8 failures, 4 are the known rc5_gen design-phase failures (also present in the pre-work baseline: 861 passed / 4 failed). The other 4 are in test_endgame2/3, which need `<local-path>`. That file is now absent from the box (environmental; blocker B2). Historical tests are unchanged.
- Netguard: 0 socket attempts (attempts.log absent).

## 6. Git hygiene review
- Scoped commits through `commit_step.sh`: explicit paths only, no `-A`. Before each commit the script records `git diff --cached --name-status` in COMMIT_AUDIT_LOG.md (local-only). It refuses ignored/protected paths and bytecode, runs the contamination scan (must pass), and runs the RC5-outcome scan with manual classification of every hit.
- `.gitignore` covers the RC6 protected paths, with a `git check-ignore` test. No RC6 protected path is tracked.
- The 42 historical protected-path files are unchanged (audit: HISTORICAL_PROTECTED_PATHS_AUDIT.md). Gate G_AUDIT fails until the user decides on containment.
- Docs that restate RC5 outcome figures are **not committed** (PREREGISTRATION_PROPOSED_FINAL, PREREGISTRATION_REVIEW, PUBLICATION_PLAN/MANIFEST, the outgoing-file list).

## 7. Exact execution command (only after every gate in §9 is cleared)
```
# 0. preconditions: RC6_APPROVALS.json APPROVED with the approved prereg sha; G_AUDIT, G_AUTHOR, G_FROZEN pass;
#    MemAvailable >= 7,600,000 kB; RC5-identical runtime binary and model store present and hash-verified.
export AIVD_RC6_AUTHORIZE_<ACTION>="<ACTION>:<approved prereg sha256>"   # per action, see below
cd <local-path> && export PYTHONDONTWRITEBYTECODE=1
# 1. corpus (GENERATE_CORPUS, CREATE_SECRET, SEAL, COMMIT_CORPUS):
python3 -c "from aivd_rc6_provider.provider import production_generate as g; print(g())"
# 2. Part B (MODEL_CALL, START_RUNTIME; AIVD_RC6_PARTB_AUTHORIZED=AIVD-RC6-INVESTIGATION-DIAGNOSTICS), model order fixed:
python3 scripts/rc6_partb_run.py qwen3:1.7b  attempt-1
python3 scripts/rc6_partb_run.py llama3.2:3b attempt-1
python3 scripts/rc6_partb_run.py qwen3:8b    attempt-1
#    at most ONE whole-model retry in the study, fresh run dir, failed attempt preserved:
python3 scripts/rc6_partb_run.py <model> attempt-2 --retry-amendment <approved amendment id>
# 3. reveal + analysis (REVEAL, SCORE): only after the replication prereg is registered (decision 15):
python3 scripts/rc6_analyze.py <run dirs ...>
```

## 8. Budget (encoded in aivd_rc6_run/budget.py; enforced study-wide)
| stage | per arm | per model | x3 models |
|---|---|---|---|
| discovery (shared) | n/a | 372 | 1116 |
| investigation | B 48 · V1 48 | 96 | 288 |
| verification | B 30 · V1 30 | 60 | 180 |
| repeat (N5) | n/a | 6 | 18 |
| **base total** | | **534** | **1602** |
| retry (max 1 whole model) | | ≤534 | ≤534 |
| **absolute ceiling** | | | **2136** |

## 9. Unresolved blockers
- **B1 author:** independent construction author and reviewer not commissioned (user choice; options in RC6_GENERATOR_DESIGN.md §2.3 / the t111u report).
- **B2 runtime files:** `<local-path>` (the Ollama 0.34.4 binary) and the model store are absent. The RC5-identical runtime must be restored and hash-verified.
- **B3 memory:** MemAvailable is below the 7,600,000 kB gate at every reading in this round. No action was taken (measure only).
- **B4 42-file audit:** containment decision pending (G_AUDIT).
- **B5 approvals:** there is no APPROVED RC6_APPROVALS.json and no final approved prereg sha. Because of the N1 stop, the final prereg form is still a user decision (the original bcf60ef9 contains RC5 outcome references).
- **B6 history rewrite:** stopped (N1). Publication of 0dd54f7/18326e5 would publish RC5 outcome references. HOLD.
- **B7 replication prereg:** skeleton only. Must be completed and registered before any RC6 reveal.
- **B8 validity-gates file:** `scripts/rc6_analyze.py` reads `protected/validity_gates.json` (integrity, contamination, Part A, T10/T11, commitments). No tool yet assembles that file from the run artifacts. It needs to be written and frozen (with a FROZEN_ANALYSIS re-pin) before reveal.
- **B9 pre-push hook:** an example is at `tools/hooks/pre-push`. It is not installed because the hooks are shared.

## 10. File manifest (files added/modified on this branch since 18326e5, at C5 HEAD c8c3852 plus this commit)
| file | sha256 |
|---|---|
| `.gitignore` | `33dc5c41c03b29845998583bbb2ffff5c5c0a411b7383158d0b97140cbe1528a` |
| `aivd_rc6_analysis/__init__.py` | `251ed0a57db173c54124c370b14b3050eb0285b14b43add93119ed55e3e80888` |
| `aivd_rc6_analysis/analyze.py` | `64f2be262e7a99b2375a9ba0942492e5a5d66f894cdd0d4fc80795ed72a22ebf` |
| `aivd_rc6_analysis/power.py` | `ae343d3fa0c43c86cc606da553003eceeadee871c83933ced18795e7977c1ecd` |
| `aivd_rc6_analysis/stats.py` | `6d98223da393a936a608c763e54218c20bcbd5981ce17392e7984f178f5abf35` |
| `aivd_rc6_evidence/__init__.py` | `ec2941a7b177a533a2a96a5f79d8af0ddd6e4544fa6b0c6ff2e034d70f89020a` |
| `aivd_rc6_evidence/cf_e.py` | `2987fa669412774062dcfa560c7284e5cd988bb5917f3d938cd7f8e015c9c4e5` |
| `aivd_rc6_evidence/reanchor.py` | `d150dcea01e3e81d8a88ca09404cda3a05593fb98d96f9af7755ffb570ac56a7` |
| `aivd_rc6_gen/__init__.py` | `36241c1b6019c00ac4cc08b41969636648803df5e5664e0636a6ada20ba2c372` |
| `aivd_rc6_gen/constructions.py` | `4d396969dbba641b27e5e367214252a730707fef83f111ac3b23260405e5cea5` |
| `aivd_rc6_gen/generate.py` | `3eae77d58c6069a6e554c0c37355831473663397857ba64389a16d5b37672ce3` |
| `aivd_rc6_gen/isolation.py` | `8838af8a15103986852e687b255ea3d36a98ba6c3aebb00c443addbaf502a43d` |
| `aivd_rc6_gen/novelty.py` | `b52ff958209507691fc2cc92d32ee1ab3f784393a401fb38587e50814e857691` |
| `aivd_rc6_gen/orders.py` | `02ced606fa868865d165b169fd20650fc81f271836d39a4c1df5c2edbf9d0052` |
| `aivd_rc6_gen/seeds.py` | `1a5c7e700f0300614657c1e4b7bd4fd1fc97b57e3ef7c9cec93fff6fcaec93e3` |
| `aivd_rc6_gen/spec.py` | `aeabd7e57f3ecf4f22612af4fcb5d2f2f28a9b9e5cf87b68b0d7f58cfdf30991` |
| `aivd_rc6_guard/__init__.py` | `4f349ce9357943dd9a5b20861630f05af33f50d5c9e0fcfb17a04ff67e6d6ccc` |
| `aivd_rc6_guard/__main__.py` | `82c5522f48579738dafdd46d8cc080c001929c3349d6e3109370895df0a6ecf4` |
| `aivd_rc6_provider/__init__.py` | `d46a7d116e3fee992affd8f40ff73f3c771a6877e57906e017a748ab8ca4fbef` |
| `aivd_rc6_provider/contract.py` | `4f8ed91fe0b981892d00c3b08f3d21c8d010e933bb79b36173cc635b894ea271` |
| `aivd_rc6_provider/intake.py` | `1e41b3f1c1cb6f4005e178c6d538af64d61555905bec04b42386c2eddafb52e8` |
| `aivd_rc6_provider/provider.py` | `65c46531c99f33601f316772fecd901177f83b29e99e21e993324dd8a1839179` |
| `aivd_rc6_run/__init__.py` | `37fb6ef8b50c86b3f22e3306cdcf2bfd1a38f1fe6ad5b294bf0b366f2551ae00` |
| `aivd_rc6_run/budget.py` | `f9aa4d0a6e2d4293be42eb0b9bf60b430d8c2f3cc4ecbbc30bd056e4caff3188` |
| `aivd_rc6_run/identity.py` | `0bec7bf39e26ad54059d158b87bcd0c48017e961f14ce0c8c38f24974260f50a` |
| `aivd_rc6_run/ledgers.py` | `d910a034ed82a2ca86b29f9ac52dfdcaa445a67c982dbdd79569df3b5a2ef82d` |
| `aivd_rc6_run/memory.py` | `307004109a2ef59a6f3773e9243882b8e6dce9b68013e8d27f3ab84129196a53` |
| `aivd_rc6_run/records.py` | `710537047e206551fcd84a190e0d305b1bb5d31a0c019ee62cac083b2abcbba4` |
| `aivd_rc6_run/runner.py` | `2d55673b9a3f8ff5c8ab1803edc2ae68631d0933bdd5c1042fda227fea6382ea` |
| `aivd_rc6_run/runtime.py` | `afee6c4dad27b9bb57a48747e2e64b8eee7c6718851b8fb4e43b5b296d12ea01` |
| `aivd_rc6_run/runtime_controller.py` | `ff1eaee7d3c5976ffd72bbc36cb4f0439dbee0e55d696fc0625c5ffab9c97617` |
| `aivd_rc6_run/transport_policy.py` | `228838e46a53a649a21e2232148cc98ed00c1b9cafd860f68f78fa874dbcb2f2` |
| `aivd_rc6_run/v1_trace.py` | `6c057d4fdfd3a21612ed89c74c7d19378f82504f04f7075c7f986a2aca2c2856` |
| `docs/rc6_investigation_diagnostics/FROZEN_ANALYSIS.json` | `08c4d8ec367cc76546a94463a495fd4dad9cd2d81e8395281bd141a8c648b8ea` |
| `docs/rc6_investigation_diagnostics/HISTORICAL_PROTECTED_PATHS_AUDIT.md` | `00c43dda50128d8f33e4183324a79fd5b78e9bf9b896aafe8810177b840a5626` |
| `docs/rc6_investigation_diagnostics/RC6_BREAKTHROUGH_CRITERIA.md` | `bedd852d5efd7432afa3feccbea60aea1aceab271b0588ea556674637ffc7aaf` |
| `docs/rc6_investigation_diagnostics/RC6_EVIDENCE_COMPONENT_STUDY_PREREG_DRAFT.md` | `7a78c36b2f457ff295f0ef58853ab28f2e8f0ddc547a273e6d5a53e5506b6b57` |
| `docs/rc6_investigation_diagnostics/RC6_EVIDENCE_FLOW_DESIGN.md` | `44e4184dbec74bb6b5580859de94fdd2d22413da53fbd5129b2b3c77e38c72e6` |
| `docs/rc6_investigation_diagnostics/RC6_REPLICATION_PREREG_SKELETON.md` | `23d8ea42e76fdfab2bc7aa2c23da5960388d606d7d33b8790be7e224664547bf` |
| `docs/rc6_investigation_diagnostics/RC6_STATISTICAL_ANALYSIS_PLAN.md` | `8fc27dff931afa6579b26493646161f1804df55f19155292d2cd638f9845698e` |
| `docs/rc6_investigation_diagnostics/power/rc6_power_results.json` | `e26ff66f4f16aad42cc4dbc4ed8542b9e35e442810511c61d8e499717ee1cd5d` |
| `scripts/rc6_analyze.py` | `bd27aa036eb60165ab1ea9174b2b38057966a9fe3d39896072d9096b8b138e7b` |
| `scripts/rc6_partb_run.py` | `de908ad9273b6cd468d11d815227ea39da5e9fe7f1b547146ed7e26dbd19449e` |
| `scripts/rc6_wire_proxy.py` | `71f9ccf56c6f3685bffce3d946d28d10b56d07be29553d77dac01e518727586d` |
| `tests/rc6_analysis/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tests/rc6_analysis/test_analysis.py` | `fe84421dc373a513ee07488a94b636b13358f35dae2bb09402f39dfa0f185a8b` |
| `tests/rc6_analysis/test_frozen_manifest.py` | `756eac5168fa8f6ce75643b57907004042a82d773bcdeb8541f564ac4b7dac8b` |
| `tests/rc6_analysis/test_power.py` | `498e79dbb1d43e77369ddeaf990d6abf91a9344714e120e4c78806765932ffa0` |
| `tests/rc6_evidence/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tests/rc6_evidence/conftest.py` | `730d946f9219a722347defd3326a9fdc627352818da94e69d3137f064441060d` |
| `tests/rc6_evidence/test_evidence_flow.py` | `9cf77245692a52c00594f8d37cae0d3887d68d73890b52140d69ffc1ea9989aa` |
| `tests/rc6_gen/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tests/rc6_gen/conftest.py` | `fa9d32bbe7f5dc1802d440c35228ea6ef441cf5e6b8fc5b84295dbda159cfd5b` |
| `tests/rc6_gen/test_generator.py` | `dad699330f8a99563e4e74b26b7045571ebd216e4037e3c669a6d22d448aaf06` |
| `tests/rc6_hygiene/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tests/rc6_hygiene/test_gitignore.py` | `96a97c3565064c831ac8ac5d5e40d2551ab2c36d81e3c8106a4b3c5063607c3c` |
| `tests/rc6_provider/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tests/rc6_provider/conftest.py` | `9c27fa401b3d778a5f39c28e7c4125c67aa428f9a9107c626e2d0320e3d0bcb3` |
| `tests/rc6_provider/test_contract_intake.py` | `bfa16fe92f0a8b45a64432c108be8bf5d57671dda67f3eed350adcf510ed4c14` |
| `tests/rc6_provider/test_guard.py` | `bcbfed22342b9a454a99e01bd44d6c6c4f8bc70d84a57d4b4cf3c1d10672aa86` |
| `tests/rc6_provider/test_provider.py` | `84d67f02a62ce344de4e62e3bb67902deb2713ef513992ece2b3dcf9f9fdd524` |
| `tests/rc6_run/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tests/rc6_run/conftest.py` | `ea0c99f568f29193fa3ef4230da2599d8e4bdf54fc32e3bc4906d36c8f8526a9` |
| `tests/rc6_run/test_budget_retry.py` | `5e77a9d1930728c43e16b9a80ecf787da884c2130868d093c14ab50c6ec5d53d` |
| `tests/rc6_run/test_rc5_replay_through_runner.py` | `7e90e29ef1ad35caf267f3e73256c279946e50b95a67d8d65f77ccf150717177` |
| `tests/rc6_run/test_runner.py` | `7b72a7a4565cfba3c11009f16b4749b4febfc48a4d1d2cb48c0568b149a4edc7` |
| `tests/rc6_run/test_runtime_entry.py` | `a33214830b814ec7e9800fbbb40a7a14c86bd66459784a6969de1b63da978ce6` |
| `tests/rc6_run/test_v1_fields.py` | `6f6a1d4bc4d8f128ff1af317f1db80d53b4e9a3582b5a0494316939654bb3fbd` |
| `tests/rc6_run/test_v1_record.py` | `36e61cb47d259704ee7ff2d47ff7d42e9752f81b2fb1a34c5fd0799f5e4f7570` |
| `tools/hooks/pre-push` | `ad01b542a46126af3236b8bed518279256b212ab074a720093b5a8f5a421ca36` |
| `tools/rc6_freeze_analysis.py` | `e16e83c28ec5a4cba246124e9a7d600b0073fd0581aa1f3a8a26ea181bd02c95` |
| `docs/rc6_investigation_diagnostics/PARTB_READINESS_MANIFEST.md` | (this file) |

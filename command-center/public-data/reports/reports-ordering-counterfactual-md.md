# F6 execution attempt

F6 STATUS: NOT EXECUTED

The frozen run stopped before any model call. Both primary arms are unscored, so the preregistered label is INCONCLUSIVE. This is an authorization abort, not an ordering result.

## Stop

`authorize_execution` is the production authorizer. It refuses any plan hash other than the F3-LM-2 plan `ffd476d0597da77530442da9e282c72f125a0886f40787b0f6f5ef7b14e2dc51` and any allocation other than 64/192/256. The F6 preregistration was refused with `plan hash mismatch`.

`aivd_f6.firewall.dispatch` also refuses. Its flag was not set. No test override was used. No token was issued, so none remained to revoke.

The design was not repaired in this run.

## Checks that matched

| Check | Result |
|---|---|
| Design commit | `0970650a51de8b27e1f8e3935c94d7380e82b15f` |
| Preregistration | `1cb07df37fe82d1924d19398b234587256169fc323ec629100c5310d096c81f9` |
| Intervention set | `e827ab6789cc947306f12758656bc7d3bdd1b0d2415a1abf356723c1ef6e0d76` |
| F5 blinded table | `fc37a48907c51c3b45455062015ce84de86b20a10ac187bb45802da70b8443d3` |
| F4 corpus | `2b882a9c3cd8dc33fc46c7c75b13a383a4d0206215d65764dbf5bd0be9bc2f3d` |
| Model artifact | `qwen3:1.7b` `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` |
| Runtime binary | Ollama `0.34.4` `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |

The local runtime server was not accepting connections. That was not used as a reason to change the plan. No generation request was sent.

## Calls

Model calls: 0

Ollama calls: 0

Qwen calls: 0

Recording failures: 0

Integrity failures: 0

CF1: unscored

CF2: unscored

CF3: unscored

CF4: unscored

Confirmations: 0

Primary endpoint: INCONCLUSIVE

Secondary endpoints: unscored

Final classification: INCONCLUSIVE

F6 does not establish a general claim about the model. Any causal interpretation is limited to the preregistered counterfactual comparison and the tested security relation. That comparison was not run.

```
F3 FROZEN
F3 FORENSIC REPRODUCED_SECURITY_DISCLOSURE
F4 FROZEN
F4 RESULT 1 / 24 HOLDOUT REPRODUCED
F5 DESIGN ONLY
F6 NOT EXECUTED
F7 NOT STARTED
```

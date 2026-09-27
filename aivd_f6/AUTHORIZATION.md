# F6 authorization repair

**Status:** path ready, execution not authorized by default
**Experiment ID:** `F6`
**Authorization-plan hash:** `ae3c9d0d1a9dca9c007fe7eccc90b611255edc4afcc3f817b5ebd064c3392e06`

MODEL CALLS: 0

OLLAMA CALLS: 0

QWEN CALLS: 0

## Why F6 was rejected

The F3-LM-2 authorizer issues a token only for plan `ffd476d0597da77530442da9e282c72f125a0886f40787b0f6f5ef7b14e2dc51` and allocation 64/192/256. That check is unchanged. An F6 preregistration is still a plan-hash mismatch there.

## F6 contract

A token is issued only by `aivd_f6.authorize.authorize_execution` after exact equality checks. It binds experiment `F6`, preregistration `1cb07df37fe82d1924d19398b234587256169fc323ec629100c5310d096c81f9`, intervention set `e827ab6789cc947306f12758656bc7d3bdd1b0d2415a1abf356723c1ef6e0d76`, model `qwen3:1.7b`, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, runtime `0.34.4` commit `b2da9e468af2479058ae18c6d908ed29de410684`, runtime digest `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`, and allocation 7 conditions / 14 paired calls / 21 maximum calls.

The firewall flag does not grant a call. Importing the module does not grant a call. A test override does not grant a call. An F3-LM-2 token does not dispatch F6. An F6 token does not dispatch F3-LM-2. The token is revoked when the production session exits, including on abort. A later change to the live intervention set or the plan commitment rejects dispatch.

No transport is attached by this repair. Dispatch with a valid token calls only a caller supplied by that later execution. This file does not start that execution.

```
F3 FROZEN
F4 FROZEN
F5 DESIGN ONLY
F6 DESIGN FROZEN
F6 EXECUTION NOT PERFORMED
F7 NOT STARTED
```

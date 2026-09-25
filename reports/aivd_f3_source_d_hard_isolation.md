# Source-D hard isolation

**SOURCE-D HARD ISOLATION COMPLETE**

**REAL SOURCE-D CORPUS NOT GENERATED**

**NO EXTERNAL PROVIDER CALLED**

**F3 EXPERIMENT NOT AUTHORIZED**

The discovery process used in this audit is a separate program. It does not import the sealer. The vault file is created outside its mount namespace, and the old root is detached after `pivot_root`. A malicious script inside that namespace cannot see the file, the key, or the repository. Full suite: 1441 passed. Science, F1, F2, and the frozen relations are unchanged.

## What the boundary is

`unshare` creates new mount, pid, network, ipc, and uts namespaces. The new root bind-mounts only `/usr`, `/lib`, `/bin`, and `/lib64` so the interpreter can start, plus a private `/tmp` and `/dev`. It then pivots and lazily unmounts the old root. The parent environment deliberately contains `VAULT_PATH`, `SEALER_KEY`, and a marker locale. Those are cleared before the discovery program is executed. Extra descriptors are closed.

This is not a container image. There is no image hash. The process is still uid 0, so a distinct user is `NOT_VERIFIED`. Provider history was not audited, because no provider ran. That field stays `NOT_VERIFIED`.

## Attacks

The script tries to import the sealer, to put the repository on `PYTHONPATH`, to walk `/`, `/tmp`, and the detached old root, to follow a symlink, to read inherited descriptors, to list processes, and to connect to a local service. Every one of those checks passed: the modules are missing, the vault filename is missing, the guessed path is missing, the symlink target is empty, and the loopback connection fails. The same process can still read the opaque handle and the probe that were placed in its directory. Those files do not contain the fixture plaintext.

| Result | Meaning |
|---|---|
| Isolation level | `FILESYSTEM_ISOLATED` |
| Claim | `HISTORY_ISOLATION_UNVERIFIED` |
| Same interpreter | `SAME_INTERPRETER_INVALID` |
| Logical tokens only | `LOGICAL_ONLY_SEPARATION` |

`SOURCE_D_READY` is not emitted. History is not verified, and a same-interpreter vault is rejected rather than described as isolation.

## What remains

The in-process vault from the previous commit still exists. It is classified `SAME_INTERPRETER_INVALID` and is not a discovery boundary. Uid separation was not achieved. No model was asked for a corpus, so model history is untouched.

**REAL SOURCE-D CORPUS NOT GENERATED. NO EXTERNAL PROVIDER CALLED. F3 EXPERIMENT NOT AUTHORIZED.**

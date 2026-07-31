# Gate 2-J.9G-D Parent/Child Topology Remediation

## Verdict

PASS

## Binding

- Authorization: `TERRA_HIGH_AUTHORIZED__GATE_2J_9G_D`
- Batch authorization hash: `df84e61f53d8cf10c592926c02276e0d494fd975d55a8036b142617856533b71`
- Base commit: `ff1b1acc13d2a81bf5c2d81868b0e10ab9ae5abf`
- Pinned binary SHA-256: `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`

## Causal Difference And Correction

The earlier relay used `subprocess.run`, leaving a Python relay as JCode's
parent. With the same contained executable, working directory, fresh tmpfs
`HOME`/`JCODE_HOME`, provider configuration, UID/GID, mount and network
namespace, the child did not attempt `connect()`.

The correction is a Proxy-owned static preassembled-root launcher. It writes
the sealed no-auth `spiritos-qualification` profile only into the fresh tmpfs
home, forks the loopback listener as a sibling with `PR_SET_PDEATHSIG`, closes
nonstandard descriptors before exec, and replaces its own process with JCode.
The Python relay follows the same sibling/exec topology for the normal
containment builder. The direct-versus-relay regression compares PID, PPID,
session ID, and process group; executable argv, cwd, environment, mount and
network namespaces, uid/gid, stdio, signal/session setup, and writable runtime
directories remain the fixed preassembled-root configuration.

## Exact-Binary Evidence

Two fresh roots were assembled from the attested binary plus its declared
dynamic libraries and the statically linked Proxy launcher.

1. Direct launch: JCode configured the named local provider and attempted
   `http://127.0.0.1:43123/v1/chat/completions`; the absent listener returned
   `ECONNREFUSED`.
2. Sibling relay launch: the listener accepted JCode, the host-side Unix socket
   accepted one forwarded connection, and captured 4,096 request bytes before
   the deliberate no-backend close. JCode then reported the expected incomplete
   request failure.

This proves the missing transition was the relay-parent topology, not provider
selection or HTTP framing. No fake backend was invoked in this gate.

## Controls

- JCode launches: 2
- Fake provider requests: 0
- Real model requests: 0
- Direct Ollama requests: 0
- Frozen benchmark changes: 0
- Daily-runtime changes: 0
- Repository writes by JCode: 0

Focused regression: `10 passed` for network bridge, executable-injection, and
startup-diagnosis suites. The static launcher compiled with `gcc -static -Wall
-Werror` before the exact-binary probes. No child process remained after either
bounded probe.

## Next Gate

Gate 2-J.9G-B may now implement the attesting fake OpenAI-compatible responder
over this proven sibling relay. It remains prohibited from calling a real
model.

# Gate 2-J.9B Containment Primitive Receipt

status: `GATE_2J_9B_PASS_NO_MODEL`

authorization: `TERRA_HIGH_AUTHORIZED__GATE_2J_9B`

authorization_commit: `a1786c928466d21c68bffa560b57e1e453a7459b`

predecessor: `GATE_2J_9A_REVALIDATION_PASS` at `657468a172d196ab678e01c0b53e82107725b9b5`

## Implemented boundary

`source_proxy.jcode.containment` now constructs the Gate 2-J.9B inert-fixture
boundary. Bubblewrap unshares user, PID, IPC, UTS, cgroup, and network namespaces;
clears the environment; drops all capabilities; mounts only approved system libraries;
and supplies fixture input as private read-only files on a sandbox tmpfs. The sole
writable fixture output, home, and temporary directories are private tmpfs paths.
No host fixture directory is bound writable, so no host mutation persists.

`source_proxy.jcode.cgroup_scope` wraps the process in a named user transient scope
with `MemoryMax`, `TasksMax`, and `CPUQuota` settings. It also applies `prlimit`
address-space, file-size, and open-file ceilings inside the sandbox.

## Host evidence and deviation record

- Bubblewrap 0.9.0, systemd 255, cgroup v2, and unprivileged user namespaces were
  reverified on Dell.
- A live inert scope reported `MemoryMax=33554432`, `TasksMax=16`, and
  `CPUQuotaPerSecUSec=250ms` while active.
- The user systemd manager accepted but did not hard-enforce `MemoryMax`: a 128 MiB
  fixture survived a 32 MiB scope setting. This is recorded as a host delegation
  limitation, not counted as cgroup-memory proof.
- The final primitive therefore enforces the sealed memory ceiling through
  `prlimit --as`; the same 128 MiB fixture is denied at a 32 MiB ceiling. The
  transient scope remains the process-tree ownership and cgroup-placement mechanism.

## Tests and controlled failures

Focused Gate 2-J.9B plus pre-existing containment tests: **20 passed**.

Required regression progression, including Gate 2-J.9A and existing focused no-model
JCode suites: **96 passed**.

The controlled suite proves successful approved input and private output, then proves
denial or fail-closed handling for daily runtime, benchmark expectations, SSH and
provider environment inheritance, Docker/Tailscale/systemd sockets, external DNS,
read-only and traversal writes, capability-based privilege change, symlink escape,
file-size excess, PID excess, address-space excess, and a child left by its parent.
It also proves explicit disposable-directory cleanup and rejects a symlinked fixture
directory before launch.

## Integrity and advancement checks

- JCode executions: `0`
- Model requests: `0`
- Frozen benchmark changes: `0`
- Daily-runtime changes: `0`
- Scope: only the Gate 2-J.9B authorized source, tests, and this receipt.
- Next gate: `2-J.9C`, permitted only after this receipt's explicit-path commit and
  push are verified.

# Gate 2-J.9G-R Containment Remediation Receipt

status: `PASS`

Root-cause classification: `LSM_OR_SECCOMP_DENIAL` (AppArmor only). Kernel audit
records show the `source-bwrap` profile denied `open` and `exec` for every
introduced `--ro-bind` path, including inert binaries and `/opt/jcode/jcode`.
The source and worktree filesystems are executable ext4; unprivileged user
namespaces are enabled; no seccomp filter or SELinux evidence explains the
failure.

Selected mechanism: an ephemeral preassembled root, mounted read-only at `/`.
It contains only the approved executable at `/usr/bin/jcode`, its declared
dynamic runtime files, empty `workspace` and `jcode-home` directories, and
synthetic `/proc` and `/dev`. Bubblewrap still unshares user, PID, IPC, UTS,
cgroup, and network namespaces, starts a new session, drops capabilities, and
dies with its parent. No host home, benchmark, daily runtime, or credentials
are mounted.

Rejected alternatives: direct file and parent-tree binds are AppArmor-denied;
`--ro-bind-data` cannot create an AppArmor-permitted temporary file under
`/usr`; rootless Podman is unavailable and Docker is not a rootless fallback;
a plain host or systemd process is not an equivalent filesystem boundary.

Focused proofs: 3 injection tests plus 7 supervisor tests passed. Dynamic
`/usr/bin/true` and static `/usr/bin/busybox` ran from fresh read-only roots;
write to `/workspace`, host-home visibility, and external egress were denied.
The exact JCode SHA-256 was verified before injection and `jcode --version`
succeeded three times. The compliant launch used `JCODE_NO_TELEMETRY=1`, a
network namespace, and `prlimit --as=6442450944`; `/usr/bin/time -v` measured
2,048 KiB maximum RSS. No provider configuration, task, model request, or
repository mutation occurred.

The existing user-scope `MemoryMax` remains a recorded, not hard-enforced,
control. The Gate 2-J.9G memory-admission receipt must retain the 6 GiB hard
address-space limit and add Proxy-owned process-tree RSS and virtual-memory
monitoring before any no-model integration run.

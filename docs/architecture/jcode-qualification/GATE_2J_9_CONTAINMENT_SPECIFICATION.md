# Gate 2-J.9 Containment Specification

status: `BUBBLEWRAP_PLUS_SYSTEMD_SCOPE_CGROUP_V2_SELECTED`

schema: `source-proxy.gate-2j-9-containment-specification/v1`

## 1. Host capability evidence (audited 2026-07-29)

| Capability | Status | Used? |
|---|---|---|
| Bubblewrap | `/usr/bin/bwrap` 0.9.0 | YES (primary namespace sandbox) |
| systemd | systemd 255, `/usr/bin/systemd-run` | YES (transient scope + cgroup) |
| cgroup v2 | `cgroup2fs` on `/sys/fs/cgroup` | YES (resource limits + pids) |
| unprivileged user namespaces | `unprivileged_userns_clone = 1` | YES (bwrap uses them) |
| nft / iptables | present | NO (bwrap net namespace suffices; not selected) |
| Docker | 29.4.0 present | NO (not used for JCode containment) |
| podman / firejail / landlock-fs | absent | N/A |

Decision: containment uses **Bubblewrap namespaces + a systemd transient scope on cgroup v2**.
This reuses the repository's already-proven bwrap path and adds cgroup resource control and
process-tree ownership that the current bwrap-only design lacks. No new package, service,
kernel, or persistent host configuration is required (satisfies the "no persistent Dell host
changes" invariant). Docker is explicitly NOT selected for the JCode sandbox: it would
introduce a Docker-socket exposure and a different trust boundary than the proven bwrap path.

## 2. Boundary policy enforced

The sandbox MUST enforce, all verified by preflight:

- Read-only base repository at the sealed base commit (bind-mounted ro).
- Isolated writable overlay only; no writes to the base bind or to JCODE_HOME inputs.
- No access outside approved roots; no access to the daily runtime `/home/source/SpiritOS`;
  no access to frozen benchmark expectations; no access to SSH keys; no access to cloud
  credentials; no access to unrelated home-directory content.
- No access to Docker sockets, Tailscale control sockets, or system service-management sockets.
- No unrestricted `/proc` or `/sys`; bwrap provides a minimal `/proc` and `/dev` only.
- No arbitrary device access; no privilege escalation; no setuid execution.
- No persistent host modification (overlay is a fresh tmpdir destroyed after sealing).
- Network disabled by default (`--unshare-net`); explicit allowlist for the sealed local
  inference bridge only, via the read-only loopback Unix relay (existing proven design).
- Resource limits via cgroup v2: process-count (pids.max), memory (memory.max), CPU
  (cpu.max), file-size (via pids + output-byte budget enforcement), output limits.

## 3. Canonical sandbox construction

Per task, the dispatcher builds:

1. A disposable worktree of the sealed base commit (see writable-overlay spec) under a fresh
   run root, e.g. `/run/jcode-runs/<run_id>/worktree` (read-only bind).
2. A fresh writable overlay upper dir `/run/jcode-runs/<run_id>/upper` (writable bind at `/workspace`).
3. A fresh empty `JCODE_HOME` `/run/jcode-runs/<run_id>/home` with only `input/{prompt,context}`.
4. A read-only bridge directory containing only `inference.sock`.
5. The bwrap argument vector from `containment.build_jcode_containment_args`, extended with:
   `--ro-bind worktree /base` (read-only base), `--bind upper /workspace` (writable overlay),
   `--ro-bind home /jcode-home`, `--ro-bind bridge-dir /run/jcode-bridge`, plus the existing
   `--unshare-user/pid/ipc/uts/cgroup/net`, minimal `/proc` and `/dev`, and the loopback relay.
6. The whole bwrap invocation is launched under `systemd-run --scope --unit=jcode-run-<run_id>
   --property=Delegate=yes --property=MemoryMax=... --property=TasksMax=... --property=CPUQuota=...`
   so the cgroup owns the entire JCode tree for reliable cleanup.

## 4. Cgroup resource limits (defaults; values operator-sealed in 2-J.9A)

| Limit | Proposed default | Operator seals |
|---|---|---|
| MemoryMax | 6 GiB (host has ~11 GiB free) | exact value |
| TasksMax (pids) | 256 | exact value |
| CPUQuota | 400% (4 of 8 CPUs) | exact value |
| wall-clock | 300 s (supervision total timeout) | already sealed |
| inactivity | 60 s (event-stream silence) | exact value |

These match the host's proven build profile (1-6 GiB containers, 8 CPUs) and keep JCode below
the OOM threshold that historically affected parallel builds.

## 5. Containment preflight tests (Gate 2-J.9B)

Each MUST pass before any model gate:

- filesystem isolation: a write to a non-overlay path fails; a read of a denied host path
  (daily runtime, SSH dir, benchmark dir) fails; symlink escape fails.
- environment isolation: only the allowlisted env vars are visible; forced-safe vars are set.
- network isolation: a connection to any non-bridge host:port fails; only the loopback relay
  is reachable; the bridge forwards only to the permitted loopback endpoint.
- process limits: spawning beyond TasksMax is denied by cgroup.
- cgroup scope: the process appears under `jcode-run-<run_id>` scope; MemoryMax/CPUQuota apply.
- no protected-host-resource access: `/proc`/`/sys` minimal; no docker/tailscale/systemd sockets.
- cleanup: after normal exit, timeout, cancellation, and crash, the cgroup has zero live
  processes and the run root is removed.

Inert commands only at this gate. No model requests.

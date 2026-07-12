# Host and Service Topology

## Dell/Linux

- Access: `ssh spirit` (user `source`); this is authoritative for `/home/source/**`, worktrees, process CWD, native environments, archives, and Linux tests.
- Worktrees: Source Proxy `/home/source/SpiritOS-source-proxy-20260711`; SpiritFlix `/home/source/SpiritOS`; temporary live integration `/home/source/SpiritOS-live-integration-20260712`.
- Verify a service with `lsof -tiTCP:<port> -sTCP:LISTEN`, `readlink -f /proc/<pid>/cwd`, then branch, HEAD, and its health endpoint from that CWD.
- 2026-07-11 observed after the live restoration: 8787 CWD is the Source Proxy worktree, while 3000 and its `127.0.0.1` worker 3002 CWDs are the temporary live-integration worktree. Check 3002 with `ss -tlnp | grep 3002`; do not treat 3000 as proof of 3002.
- Memory is 15 GiB-class with normal cache/swap pressure possible; avoid simultaneous broad builds/harnesses. Archives are under `/home/source/.spiritos-preservation/20260711-full-cleanup/`.

## Windows/SMB

- `Z:\` / `\\10.0.0.186\SpiritOS` is the SpiritFlix view. Use it for normal file editing only after matching the manifest; use SSH for native tests and Linux truth.
- Refresh the index before status. SMB metadata can be stale; compare working and Dell `HEAD` blob SHA-256 for suspect binaries. Keep repository CRLF policy via tracked attributes; do not run high-I/O tests over SMB.

## Mac

- Supported current route is a Dell hop: `ssh spirit 'ssh -o BatchMode=yes spirit-mac-mini ...'` (Mac reports `spirit-mac-mini.local`, user `source`). Direct Windows alias is not configured in the checked SSH config.
- The historical `/Users/spiritmac/spiritos-worker/SpiritOS` path was absent on the live 2026-07-11 check. Mac status is therefore **partial/unproven**, not unavailable; no worker start/restart or source write is authorized by this map.

## Service boundary

- Source Proxy owns backend 8787 from its worktree. The temporary integration worktree owns HTTPS frontend 3000 and its expected Next worker 3002; both must be live and identity-checked before any test relies on them.
- The live-integration worktree is a temporary runtime compromise pending the Step 3 ownership decision. To roll back, stop only `tmux` session `spiritos-live-integration-20260712` and use the exact Source Proxy restart command recorded in `worktree-manifest.md`; never use broad process kills.
- SpiritFlix has no Source Proxy managed service ownership. Its production/sidecar lanes are checked only when a SpiritFlix task names them.

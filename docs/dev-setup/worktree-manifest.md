# SpiritOS Worktree Manifest

Authoritative operational map. Verify every HEAD and process identity at use time; this snapshot was refreshed 2026-07-11 after the temporary live-integration cutover.

| Stream | Worktree | Branch | HEAD | State | Service role |
| --- | --- | --- | --- | --- | --- |
| Source Proxy structural milestone | `/home/source/SpiritOS-source-proxy-20260711` | `codex/source-proxy-structural-milestone-20260711` | `594d66ef` (verify live) | clean | backend 8787 only; certificate and rollback source |
| SpiritFlix smart-scan WIP | `/home/source/SpiritOS` (`Z:\`) | `codex/spiritflix-smart-scan-identity-fix` | `5fde4ae0` (verify live) | clean | newest SpiritFlix source; no Source Proxy managed services |
| Temporary live integration | `/home/source/SpiritOS-live-integration-20260712` | `codex/spiritos-live-integration-20260712` | merge `832683ff` plus topology receipt (verify live) | clean | HTTPS frontend 3000 and Next worker 3002; temporary pending Step 3 ownership decision |
| Count-fix archive | no worktree | `codex/spiritflix-count-fix-archive-20260711` | `76fc2a3d` | retained recovery commit | inactive |

`91c3ab11` is a historical Source Proxy milestone, not a current worktree selector. The Prompt 1 fixture is generated output and is ignored after a run. Historical Plan 1-3 and Lane 2 content is stored as verified bundles under `/home/source/.spiritos-preservation/20260711-full-cleanup/`; neither has an active worktree.

## Managed service identity

- Backend 8787: CWD `/home/source/SpiritOS-source-proxy-20260711`, branch `codex/source-proxy-structural-milestone-20260711`; it remains unchanged by the frontend cutover.
- Frontend 3000 and Next worker 3002: CWD `/home/source/SpiritOS-live-integration-20260712`, branch `codex/spiritos-live-integration-20260712`. Worker 3002 binds to `127.0.0.1`; verify it from Dell with `ss -tlnp | grep 3002` before runtime proof.
- This integration worktree is temporary. Do not treat it as a permanent product merge; Step 3 must decide the Source Proxy, SpiritFlix, and shared-frontend ownership model.
- Rollback: stop only `tmux` session `spiritos-live-integration-20260712`, then start the prior Source Proxy frontend with `tmux new-session -d -s spiritos-live-rollback-20260712 "cd /home/source/SpiritOS-source-proxy-20260711; npx next start -H 127.0.0.1 -p 3002 >> /tmp/spiritos-live-rollback-3002.log 2>&1 & next_pid=\$!; node /home/source/SpiritOS-source-proxy-20260711/scripts/spiritflix-prod-https-proxy.mjs --port 3000 --target-port 3002 --key /home/source/SpiritOS-source-proxy-20260711/certificates/spirit-dev-key.pem --cert /home/source/SpiritOS-source-proxy-20260711/certificates/spirit-dev.pem >> /tmp/spiritos-live-rollback-3000.log 2>&1; status=\$?; kill \$next_pid 2>/dev/null || true; wait \$next_pid 2>/dev/null || true; exit \$status"`.
- Verify identity with readlink -f /proc/<pid>/cwd, then read branch, HEAD, and /health from that same path before using a runtime result.

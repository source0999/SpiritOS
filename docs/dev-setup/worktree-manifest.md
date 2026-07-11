# SpiritOS Worktree Manifest

Snapshot: 2026-07-11 cleanup normalization. Refresh this file whenever a worktree, service owner, or project destination changes.

| Stream | Worktree | Branch | HEAD | State | Service role |
| --- | --- | --- | --- | --- | --- |
| Source Proxy structural milestone | `/home/source/SpiritOS-source-proxy-20260711` | `codex/source-proxy-structural-milestone-20260711` | `91c3ab1182d317dba9e808f9421cccc862bac253` | clean committed milestone | target authoritative integration checkout after service verification |
| SpiritFlix/media holding stream | `/home/source/SpiritOS` (`Z:\`) | `codex/spiritflix-smart-scan-identity-fix` | `b5709cc8c26df3524bf7a3340eec99ee15dec86a` | intentionally dirty; owned groups documented in cleanup report | not an approved Source Proxy test target |
| Prior Source Proxy Plans 1-3 | Git branch `codex/coding-proxy-plan1-clean-local` | `codex/coding-proxy-plan1-clean-local` | `5f319ad80c9c0c8d5fb0d0b3882964b6beb13adb` | commits preserved; prior linked worktree metadata is stale | inactive historical checkpoint |
| Lane 2 sparse proxy | `/home/source/SpiritOS-lane2-proxy-sparse` | `lane2-proxy-set-b` | `80c8081caae5f53272c1a4a3421ede2be16c447e` | stale/prunable metadata; do not use until independently repaired | none |

The completed Source Proxy structural milestone is `91c3ab11`, not the mixed SpiritFlix branch. The final LumaCart files in the holding checkout are intentionally retained test output and are not part of that commit.

## Managed service identity

- Backend 8787: CWD /home/source/SpiritOS-source-proxy-20260711, branch codex/source-proxy-structural-milestone-20260711.
- Frontend 3000: CWD /home/source/SpiritOS-source-proxy-20260711, served by its production Next process on 3002 and HTTPS proxy on 3000.
- Verify identity with eadlink -f /proc/<pid>/cwd, then read branch, HEAD, and /health from that same path before using a runtime result.

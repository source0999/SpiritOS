# SpiritOS Worktree Manifest

Snapshot: 2026-07-11 full cleanup. Refresh this file whenever a worktree, service owner, or project destination changes.

| Stream | Worktree | Branch | HEAD | State | Service role |
| --- | --- | --- | --- | --- | --- |
| Source Proxy structural milestone | `/home/source/SpiritOS-source-proxy-20260711` | `codex/source-proxy-structural-milestone-20260711` | verify live; code checkpoint `6b59214f` | clean | authoritative integration checkout; backend 8787 and frontend 3000 |
| SpiritFlix smart-scan WIP | `/home/source/SpiritOS` (`Z:\`) | `codex/spiritflix-smart-scan-identity-fix` | verify live; source checkpoint `3d083ed9` | clean WIP checkpoint | no managed services |
| Count-fix archive | no worktree | `codex/spiritflix-count-fix-archive-20260711` | `76fc2a3d` | retained recovery commit | inactive |

The completed Source Proxy structural milestone is `91c3ab11`, not the SpiritFlix branch. The Prompt 1 fixture is generated output and is ignored after a run. Historical Plan 1-3 and Lane 2 content is stored as verified bundles under `/home/source/.spiritos-preservation/20260711-full-cleanup/`; neither has an active worktree.

## Managed service identity

- Backend 8787: CWD /home/source/SpiritOS-source-proxy-20260711, branch codex/source-proxy-structural-milestone-20260711.
- Frontend 3000: CWD /home/source/SpiritOS-source-proxy-20260711, served by its production Next process on 3002 and HTTPS proxy on 3000.
- Verify identity with readlink -f /proc/<pid>/cwd, then read branch, HEAD, and /health from that same path before using a runtime result.

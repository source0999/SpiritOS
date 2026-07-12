# SpiritOS Worktree Manifest

Authoritative operational map. Verify every HEAD and process identity at use time; this snapshot was refreshed 2026-07-11.

| Stream | Worktree | Branch | HEAD | State | Service role |
| --- | --- | --- | --- | --- | --- |
| Source Proxy structural milestone | `/home/source/SpiritOS-source-proxy-20260711` | `codex/source-proxy-structural-milestone-20260711` | `918a347f` (verify live) | clean | authoritative integration checkout; backend 8787 and frontend 3000 |
| SpiritFlix smart-scan WIP | `/home/source/SpiritOS` (`Z:\`) | `codex/spiritflix-smart-scan-identity-fix` | `df77ee4f` (verify live) | clean | no Source Proxy managed services |
| Count-fix archive | no worktree | `codex/spiritflix-count-fix-archive-20260711` | `76fc2a3d` | retained recovery commit | inactive |

`91c3ab11` is a historical Source Proxy milestone, not a current worktree selector. The Prompt 1 fixture is generated output and is ignored after a run. Historical Plan 1-3 and Lane 2 content is stored as verified bundles under `/home/source/.spiritos-preservation/20260711-full-cleanup/`; neither has an active worktree.

## Managed service identity

- Backend 8787: CWD /home/source/SpiritOS-source-proxy-20260711, branch codex/source-proxy-structural-milestone-20260711.
- Frontend 3000: CWD /home/source/SpiritOS-source-proxy-20260711. It is expected to be backed by Next worker 3002; on the 2026-07-11 validation, 3002 had no listener, so browser/runtime proof requiring it is blocked until rechecked.
- Verify identity with readlink -f /proc/<pid>/cwd, then read branch, HEAD, and /health from that same path before using a runtime result.

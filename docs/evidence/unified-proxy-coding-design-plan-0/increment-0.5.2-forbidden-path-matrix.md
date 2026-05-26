# Increment 0.5.2: Produce Forbidden Path Matrix For Cartographer Soak And Shared State

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.5, Allowed/Forbidden Path Matrix

INCREMENT: Increment 0.5.2, Produce Forbidden Path Matrix For Cartographer Soak And Shared State

Objective:
Produce the forbidden path matrix for Cartographer soak, Scout soak, Source Proxy runtime state, map state, and git/shared execution surfaces.

Isolated proxy lane scope:
unified-proxy-coding-design-plan-0

Allowed files or file zones:
- Evidence files inside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/
- Read-only inspection only when needed.

Forbidden files, paths, systems, and actions:
- Production source files.
- Source Proxy runtime files.
- Cartographer runtime files.
- Cartographer soak logs.
- Scout soak logs.
- Cartographer live evidence.
- Map state.
- Git mutations, including branch, worktree, stash, reset, clean, checkout, stage, commit, and push.
- Provider/model calls.
- Apply or execute-approved routes.
- Background worker or queue mutation.

Exact work performed:
- Consolidated forbidden paths from Increment 0.3.1 and Increment 0.3.2.
- Produced a matrix describing why each zone is forbidden.

Required tests or inspections:
- Manual review of previously captured read-only path evidence.
- No new runtime or soak inspection requiring file writes.

Forbidden path matrix:

| Zone | Forbidden status | Reason |
| --- | --- | --- |
| /home/source/SpiritOS/source_proxy/cartographer/ | Hard forbidden | Cartographer runtime and queue implementation surface. |
| /home/source/SpiritOS/source_proxy/cartographer/soak-logs/ | Hard forbidden | Cartographer soak log output. |
| /home/source/SpiritOS/docs/cartographer-live-evidence/ | Hard forbidden | Cartographer live evidence. |
| /home/source/SpiritOS/docs/cartographer-live-receipts/ | Hard forbidden | Cartographer live receipts. |
| /home/source/SpiritOS/.codex-cartographer-next-3001.log | Hard forbidden | Active or recent Cartographer run log. |
| /home/source/SpiritOS/.codex-cartographer-next-3001.err.log | Hard forbidden | Active or recent Cartographer error log. |
| /home/source/SpiritOS/src/app/map/cartographer-*.ts | Hard forbidden | Production map Cartographer state/control surfaces. |
| /home/source/SpiritOS/data/cartographer-v1-freeze/ | Hard forbidden | Cartographer production/shared state. |
| /home/source/SpiritOS/data/cartographer-v1-proof-gates/ | Hard forbidden | Cartographer gate/proof state. |
| /home/source/SpiritOS/data/cartographer-v1-diagnostics/ | Hard forbidden | Cartographer diagnostics state. |
| /home/source/SpiritOS/data/cartographer_git_approvals.audit.jsonl | Hard forbidden | Cartographer git approval audit state. |
| /home/source/SpiritOS/data/source-proxy/ | Hard forbidden | Production Source Proxy state. |
| /home/source/SpiritOS/scout/soak-logs/ | Hard forbidden | Scout soak log output. |
| /home/source/SpiritOS/scout/data/ | Hard forbidden | Scout runtime data. |
| /home/source/SpiritOS/.codex-scout-*.log | Hard forbidden | Scout run logs. |
| /home/source/SpiritOS/.codex-scout-*.err.log | Hard forbidden | Scout error logs. |
| /home/source/SpiritOS/.git/ | Hard forbidden | Git metadata; no mutation allowed. |
| /home/source/SpiritOS/.next/ | Hard forbidden | Runtime/build output. |
| /home/source/SpiritOS/.pytest_cache/ | Hard forbidden | Test cache output; no test cache mutation in Plan 0. |
| /home/source/SpiritOS/node_modules/ | Hard forbidden | Dependency install/runtime surface. |

Required manual validation:
- Matrix marks Cartographer soak logs, live evidence, runtime state, and map state as hard forbidden.
- Matrix marks Scout soak logs and data as hard forbidden.
- Matrix marks git mutation surfaces as hard forbidden.
- No forbidden path was edited.

Required evidence artifact:
This file.

Stop conditions:
- Any need to write to a hard-forbidden zone.
- Any need to run a test that mutates shared state.
- Any unclear overlap with runtime or soak state.

Rollback or recovery note:
No rollback action is authorized. If a forbidden-zone write is required by a future request, stop and report NEEDS OPERATOR REVIEW.

GO / NO-GO exit rule:
GO only if forbidden paths are explicit and no forbidden action occurred.

GO / NO-GO:
GO for Increment 0.5.2.

Next authorized increment only:
Plan 0, Phase 0.6, Increment 0.6.1: Define Isolated Test Output Directory.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

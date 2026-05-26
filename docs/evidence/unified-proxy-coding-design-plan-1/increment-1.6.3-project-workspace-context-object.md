# Increment 1.6.3: Define Project/Workspace Context Object

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.6, Shared task/project/context contract.

INCREMENT:
Increment 1.6.3, Define project/workspace context object.

Objective:
Define read-only project/workspace display contract.

Isolated proxy lane scope:
Contract evidence grounded in read-only `workspace-context.ts`.

Allowed files or file zones:
Plan 1 evidence files only; read-only reference to `/src/lib/coding/workspace-context.ts`.

Forbidden files, paths, systems, and actions:
Project creation, filesystem scan outside allowlist, Cartographer writes, branch/worktree/commit/push, provider calls, apply, execute-approved, queues, hidden workers, and git mutation.

Exact work performed:
- Defined object fields: selected project id, label, root/path, availability, access, health, ownership, dirty state, blockers, authority, receipt label.
- Bound SpiritOS default to read/list-only.
- Marked Windows and remote targets as future/unavailable/skipped unless later approved.

Required tests/checks:
Read-only context checklist against `workspace-context.ts`.

Manual validation performed by Codex:
Workspace contract is read-only and blocks project creation, path escape, branch, worktree, commit, push, and live Cartographer write needs.

Evidence artifact:
This file.

Stop conditions checked:
Live Cartographer write required: no. Project mutation required: no.

Rollback or recovery note:
Use fixture/unavailable state for unknown project context.

GO/NO-GO exit:
GO for Increment 1.6.3.

Next authorized increment only:
Plan 1, Phase 1.6, Increment 1.6.4.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

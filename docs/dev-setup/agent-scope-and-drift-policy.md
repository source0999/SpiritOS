# Agent Scope, Drift, and Compaction Policy

## Scope ledger template

Keep this task-local (prompt output or ignored scratch file), never as a committed per-task ledger:

```text
USER_OBJECTIVE:
PROJECT_SCOPE:
ACTIVE_WORKTREE:
ACTIVE_BRANCH:
ALLOWED_PATHS:
FORBIDDEN_DETOURS:
CURRENT_PHASE:
COMPLETED_GATES:
NEXT_GATE:
SERVICES:
TESTS_REQUIRED:
OPEN_BLOCKERS:
LAST_VERIFIED_HEAD:
```

Update it after discovery, before the first edit, after replanning or compaction, before changing projects, and before the final verdict. After compaction, reload the ledger and completed-gate summary; do not replay proven discovery/tests without a stated reason.

## Anti-drift gates

- **Objective:** if architecture work turns into Prompt 1 repair, stop that path, preserve the work, return to the objective, and record it.
- **Project:** block edits outside allowed roots unless a shared-file justification is written first.
- **Host:** check configured SSH/hops before declaring a Linux/Mac asset unavailable.
- **Runtime:** fail until edited worktree, branch, HEAD, process CWD, and target port agree.
- **Discovery:** start from entry points; justify expanded searches and never reopen unrelated trees by habit.
- **Compaction:** reload ledger/gates instead of starting again.
- **Easier substitution:** a benchmark can validate a relevant increment but cannot replace the requested structural objective.

## Context budget

Start with the minimal set; after a few entry files, state why an expanded layer is needed. Prefer symbols and bounded ranges to full files. Do not search all branches/hosts, bulk evidence/XML/repomix, generated data, or history without need. Reuse this registry's commands, run focused tests before broad ones, serialize I/O-heavy work, and log files already read. These are escalation prompts, not arbitrary hard limits.

## Model notes

Codex: keep edits scoped, verify worktree and runtime identity, use explicit staging, preserve status boundaries, and continue repair loops only inside the ledger. GLM: independently verify across the mapped host views; distinguish code presence, execution, and downstream consumption; during audit-only work make no modifications. Both follow the common rules in `AGENTS.md`.

## Dry-run routing validation

| Scenario | Correct route | Full scan avoided |
| --- | --- | --- |
| Fix Source Proxy lifecycle | Dell Source Proxy worktree; broker/lifecycle entry points; focused regression then e2e | yes |
| Audit SpiritFlix scanning | SpiritFlix worktree; named scan route and production build/perf lane | yes |
| Check Mac worker | Dell hop to Mac; Mac scripts/adapter and focused proof | yes |
| Read-only architecture audit | manifest plus named roots; no product edit | yes |
| Verify Dell runtime from Windows | SSH process CWD/HEAD/health, not SMB inference | yes |
| Resume after compaction | reload ledger and completed gates | yes |

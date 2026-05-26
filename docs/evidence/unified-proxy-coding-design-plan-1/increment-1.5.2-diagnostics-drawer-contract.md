# Increment 1.5.2: Define Diagnostics Drawer Contract

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.5, Shared drawer model.

INCREMENT:
Increment 1.5.2, Define diagnostics drawer contract.

Objective:
Define diagnostics as a secondary proof surface.

Isolated proxy lane scope:
Contract-only evidence.

Allowed files or file zones:
Plan 1 evidence files only.

Forbidden files, paths, systems, and actions:
Running diagnostics, runner profiles that write shared soak logs, Run 10/25/100 execution, provider calls, apply, execute-approved, Cartographer writes, Scout/Cartographer soak writes, queues, hidden workers, and git mutation.

Exact work performed:
- Defined diagnostics drawer as display/preview only: trial prompt summaries, blockers, safety proof, manual control status, and disabled run states.
- Defined no-run rule: diagnostics drawer may link to evidence but must not start tests, providers, soak profiles, or long-running tasks in Plan 1.

Required tests/checks:
No-run checklist.

Manual validation performed by Codex:
Diagnostics remains secondary and cannot disturb Cartographer/Scout soak or Source Proxy runtime.

Evidence artifact:
This file.

Stop conditions checked:
Live runner required: no. Soak path mutation required: no.

Rollback or recovery note:
Use fixture/blocked state for any unavailable diagnostic.

GO/NO-GO exit:
GO for Increment 1.5.2.

Next authorized increment only:
Plan 1, Phase 1.5, Increment 1.5.3.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

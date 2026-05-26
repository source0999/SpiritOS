# Increment 1.5.3: Define Evidence Drawer Contract

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.5, Shared drawer model.

INCREMENT:
Increment 1.5.3, Define evidence drawer contract.

Objective:
Make evidence and receipts browsable without mutation.

Isolated proxy lane scope:
Contract-only evidence.

Allowed files or file zones:
Plan 1 evidence files and read-only references to isolated evidence.

Forbidden files, paths, systems, and actions:
Writing live evidence, writing soak logs, mutating runtime state, provider calls, apply, execute-approved, queues, hidden workers, and git mutation.

Exact work performed:
- Defined evidence drawer content: receipt list, task timeline, dirty-tree proof, rollback notes, command outputs, manual checklists, blocked states, and no-authority proof.
- Defined source boundary: live Cartographer evidence and soak logs are forbidden; use isolated evidence or read-only summaries only.

Required tests/checks:
Evidence source boundary check.

Manual validation performed by Codex:
Drawer can show Plan evidence without writing live evidence or soak state.

Evidence artifact:
This file.

Stop conditions checked:
Live evidence write needed: no.

Rollback or recovery note:
Fallback is isolated evidence fixture, not live write.

GO/NO-GO exit:
GO for Increment 1.5.3.

Next authorized increment only:
Plan 1, Phase 1.5, Increment 1.5.4.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

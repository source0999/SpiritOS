# Increment 1.6.1: Define Active Task Transcript Data Model

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.6, Shared task/project/context contract.

INCREMENT:
Increment 1.6.1, Define active task transcript data model.

Objective:
Define transcript event model without worker execution.

Isolated proxy lane scope:
Schema/contract evidence only.

Allowed files or file zones:
Plan 1 evidence files only.

Forbidden files, paths, systems, and actions:
Worker execution, queue mutation, provider calls, apply, execute-approved, long-running task advancement, Cartographer writes, and git mutation.

Exact work performed:
- Defined event fields: `id`, `taskId`, `type`, `title`, `detail`, `status`, `at`, `actor`, `evidenceRefs`, `authority`.
- Defined event types: operator_prompt, plan, preview, approval_required, approved_not_applied, verify_required, blocked, receipt, manual_validation, closeout.
- Defined authority field as display-only and false unless later exact approval grants action.

Required tests/checks:
Schema review for hidden-worker implication.

Manual validation performed by Codex:
The transcript model records states; it does not execute tasks.

Evidence artifact:
This file.

Stop conditions checked:
Implies hidden worker: no.

Rollback or recovery note:
Mark ambiguous event types UI-only before implementation.

GO/NO-GO exit:
GO for Increment 1.6.1.

Next authorized increment only:
Plan 1, Phase 1.6, Increment 1.6.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

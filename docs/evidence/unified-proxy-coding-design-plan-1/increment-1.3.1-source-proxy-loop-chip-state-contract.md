# Increment 1.3.1: Map Source Proxy Loop States To UI Chips

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.3, Source Proxy safety contract mapping.

INCREMENT:
Increment 1.3.1, Map Draft -> Preview -> Approval -> Apply -> Verify states to UI chips.

Objective:
Align Source Proxy safety loop with compact chips.

Isolated proxy lane scope:
Contract-only evidence.

Allowed files or file zones:
Plan 1 evidence files only.

Forbidden files, paths, systems, and actions:
Preview route calls, apply, execute-approved, backend mutation, provider calls, Cartographer writes, queues, hidden workers, and git mutation.

Exact work performed:
- Defined chip states:
  - Draft: "Draft only; no files changed."
  - Preview: "Preview evidence only; no apply."
  - Approval: "Approval required; approval is not apply."
  - Apply: "Apply disabled unless exact later approval exists."
  - Verify: "Verification required after any future apply."
  - Blocked: "Blocked by provider/apply/Cartographer/dirty-tree boundary."
- Required all chips to expose `authority=false` unless a later approved Source Proxy action explicitly changes that state.

Required tests/checks:
Manual checklist: all loop states present; no chip implies apply, commit, push, provider call, or queue execution.

Manual validation performed by Codex:
Loop is preserved and labels avoid authority expansion.

Evidence artifact:
This file.

Stop conditions checked:
Chip implies authority not granted: no. Route call required: no.

Rollback or recovery note:
If copy is misleading, revise contract before implementation.

GO/NO-GO exit:
GO for Increment 1.3.1.

Next authorized increment only:
Plan 1, Phase 1.3, Increment 1.3.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

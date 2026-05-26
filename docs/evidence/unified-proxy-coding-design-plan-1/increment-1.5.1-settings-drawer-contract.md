# Increment 1.5.1: Define Settings Drawer Contract

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.5, Shared drawer model.

INCREMENT:
Increment 1.5.1, Define settings drawer contract.

Objective:
Define settings as truth/config-intent display.

Isolated proxy lane scope:
Contract-only evidence.

Allowed files or file zones:
Plan 1 evidence files only; read-only reference to coding settings/provider/workspace/usage truth surfaces.

Forbidden files, paths, systems, and actions:
Persisting env/config/auth, provider calls, localStorage/IndexedDB writes, package changes, apply, execute-approved, Cartographer writes, queues, hidden workers, and git mutation.

Exact work performed:
- Defined settings sections: provider/model truth, workspace context, usage/time, backend truth, disabled persistence state, and blocked reason display.
- Defined persistence rule: Plan 1 settings are display/intention only; saving config requires later explicit approval.
- Defined dialog intent: labelled drawer, focusable close, Escape close, restore focus in later implementation.

Required tests/checks:
No-provider/no-persist checklist.

Manual validation performed by Codex:
Settings drawer can explain truth and unavailable config without mutating env/config/auth.

Evidence artifact:
This file.

Stop conditions checked:
Mutation required: no. Provider call required: no.

Rollback or recovery note:
Future implementation must render disabled states if persistence is unavailable.

GO/NO-GO exit:
GO for Increment 1.5.1.

Next authorized increment only:
Plan 1, Phase 1.5, Increment 1.5.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

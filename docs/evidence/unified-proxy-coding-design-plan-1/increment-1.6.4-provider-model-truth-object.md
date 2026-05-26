# Increment 1.6.4: Define Provider/Model Truth Object

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.6, Shared task/project/context contract.

INCREMENT:
Increment 1.6.4, Define provider/model truth object.

Objective:
Define provider/model truth chip contract.

Isolated proxy lane scope:
Contract evidence grounded in read-only provider/model truth.

Allowed files or file zones:
Plan 1 evidence files only; read-only reference to `/src/lib/coding/model-provider-status.ts`.

Forbidden files, paths, systems, and actions:
Provider calls, fake availability, env/config mutation, package changes, apply, execute-approved, Cartographer writes, queues, hidden workers, and git mutation.

Exact work performed:
- Defined fields: provider id, provider label, model id, model label, status, configured, previewAvailable, externalCallAvailable, blockedReason, costWarning, authority flags.
- Contract rule: availability is displayed from truth data; no probing or provider call is allowed.
- Contract rule: local/default can be shown without external call; cloud remains unavailable/gated unless configured and separately approved.

Required tests/checks:
No-provider-call checklist.

Manual validation performed by Codex:
Provider truth object can display unavailable/configured/proposal-only states without calling providers.

Evidence artifact:
This file.

Stop conditions checked:
Live provider needed: no. Fake availability required: no.

Rollback or recovery note:
Default unknown provider to unavailable.

GO/NO-GO exit:
GO for Increment 1.6.4.

Next authorized increment only:
Plan 1, Phase 1.6, Increment 1.6.5.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

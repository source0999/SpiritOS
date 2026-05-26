# Plan 7/14: Settings Window Integration

PLAN:
Plan 7/14, Settings Window Integration.

Evidence root:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-7/`

Updated isolated prototype:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html`

Global forbidden actions:
No settings persistence. No env/config/auth mutation. No provider calls. No fake provider availability. No server restart. No project creation. No production route/component/backend edits. No package install. No git mutation. No Cartographer mutation.

Shared inventory:
- `settings-surface.ts` builds `CodingSettingsRow[]` with `writable: false` for workspace, provider/model, safety authority, notifications, usage/time, CLI, and config write gate.
- `model-provider-status.ts` maps local/default, GPT/cloud, Codex worker, and future providers with apply/commit/push false; cloud remains unavailable unless configured and still separately gated.
- `backend-truth-surface.ts` marks backend truth rows as read-only, not-wired, unavailable, proposal-only, or config-blocked; no hidden execution guard explicitly blocks provider/queue/shell/apply/execute-approved.
- `workspace-context.ts` marks SpiritOS read/list-only and future/remote targets unavailable; no branch/worktree/commit/push/project write.
- `usage-time-surface.ts` distinguishes current-session UI timing from real provider reports and marks token usage, actual cost, budget status, and durable usage storage unavailable/gated without real reports.

Shared checks:
```text
$ grep -En "Provider/model truth|Workspace/project truth|Backend truth|Usage and cost|Notification preferences|Config write gate|Notifications disabled|Save disabled|Config writes gated|GPT/cloud|Codex worker|durable usage storage" docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html
749: Provider/model truth
753: GPT/cloud
754: Codex worker
759: Workspace/project truth
763: Backend truth
767: Usage and cost
768: durable usage storage
771: Notification preferences
773: Notifications disabled
778: Save disabled
781: Config write gate
783: Config writes gated

$ grep -En "fetch\(|XMLHttpRequest|localStorage|indexedDB|navigator\.sendBeacon|serviceWorker|new Worker|Worker\(|/v1/actions|/v1/tasks|/v1/cartographer|process\.env|document\.cookie|Notification\.requestPermission|sendMessage\(|useChat\(|save[A-Z]|write[A-Z]|setItem\(|db\." docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html
<no output>

$ node - <<'NODE'
<static assertion script checked 11 required settings labels and 20 forbidden provider/config/storage patterns>
NODE
Plan 7 static assertions passed: 11 required settings labels present; 20 forbidden provider/config/storage patterns absent.

$ git -C /home/source/SpiritOS status --short --branch --untracked-files=normal
## main...origin/main
?? docs/evidence/
?? docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md

$ git -C /home/source/SpiritOS diff --name-status
<no output>
```

## Increment 7.1.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.1, Settings surface inventory.

INCREMENT:
7.1.1, Inventory `settings-surface.ts`.

Objective:
Settings inventory.

Isolated proxy lane scope:
Read-only `/src/lib/coding/settings-surface.ts`.

Allowed files or file zones:
Read-only inspection and Plan 7 evidence.

Forbidden files, paths, systems, and actions:
Edits and persistence.

Exact work performed:
Read `settings-surface.ts`; mapped all settings rows as `writable: false`.

Required tests/checks:
Read-only `sed`.

Manual validation performed by Codex:
Settings helper is display-only and authority text blocks config/env/provider/apply writes.

Evidence artifact:
This file.

Stop conditions checked:
Config writes: no.

Rollback or recovery note:
Display-only.

GO/NO-GO exit:
GO for Increment 7.1.1.

Next authorized increment only:
7.1.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 7.1.2

PLAN:
Plan 7/14.

PHASE:
Phase 7.1.

INCREMENT:
7.1.2, Inventory provider/model surfaces.

Objective:
Provider inventory.

Isolated proxy lane scope:
Read-only model-provider status.

Allowed files or file zones:
Read-only `/src/lib/coding/model-provider-status.ts`.

Forbidden files, paths, systems, and actions:
Provider calls and fake availability.

Exact work performed:
Read provider/model helper. Mapped local default, GPT/cloud, Codex proposal, and future provider states.

Required tests/checks:
Read-only `sed`.

Manual validation performed by Codex:
Provider authority keeps apply/commit/push false; external calls are gated and not invoked.

Evidence artifact:
This file.

Stop conditions checked:
Live call needed: no.

Rollback or recovery note:
Unavailable state.

GO/NO-GO exit:
GO for Increment 7.1.2.

Next authorized increment only:
7.1.3.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 7.1.3

PLAN:
Plan 7/14.

PHASE:
Phase 7.1.

INCREMENT:
7.1.3, Inventory backend truth surfaces.

Objective:
Backend truth inventory.

Isolated proxy lane scope:
Read-only backend truth.

Allowed files or file zones:
Read-only `/src/lib/coding/backend-truth-surface.ts`.

Forbidden files, paths, systems, and actions:
Route mutation/start/restart.

Exact work performed:
Read backend truth helper and mapped self-status, tools manifest, workspace API, sandbox terminal, long-running tasks, provider/model, budget, CLI, Codex adapter, and hidden execution guard rows.

Required tests/checks:
Read-only `sed`.

Manual validation performed by Codex:
Rows are not-wired/unavailable/read-only and do not invoke routes.

Evidence artifact:
This file.

Stop conditions checked:
Live mutation: no.

Rollback or recovery note:
Blocked/unavailable.

GO/NO-GO exit:
GO for Increment 7.1.3.

Next authorized increment only:
7.1.4.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 7.1.4

PLAN:
Plan 7/14.

PHASE:
Phase 7.1.

INCREMENT:
7.1.4, Inventory workspace context surfaces.

Objective:
Workspace inventory.

Isolated proxy lane scope:
Read-only workspace context.

Allowed files or file zones:
Read-only `/src/lib/coding/workspace-context.ts`.

Forbidden files, paths, systems, and actions:
Project creation/scanning.

Exact work performed:
Read workspace helper and mapped SpiritOS read/list-only, Windows future target unavailable, remote skipped, folder proof rows, and write unavailable state.

Required tests/checks:
Read-only `sed`.

Manual validation performed by Codex:
Workspace truth blocks branch/worktree/commit/push/project creation.

Evidence artifact:
This file.

Stop conditions checked:
Mutation needed: no.

Rollback or recovery note:
Display-only.

GO/NO-GO exit:
GO for Increment 7.1.4.

Next authorized increment only:
7.2.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 7.1.1, 7.1.2, 7.1.3, 7.1.4.
Evidence reviewed: settings, provider, backend, workspace, usage truth files.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Settings truth is display-only; live settings persistence remains unapproved.
Decision: GO.
Next phase or increment: Phase 7.2, Increment 7.2.1.

## Increment 7.2.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.2, Provider/model truth display.

INCREMENT:
7.2.1, Add settings drawer layout.

Objective:
Drawer layout.

Isolated proxy lane scope:
Isolated UI prototype.

Allowed files or file zones:
`docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html`.

Forbidden files, paths, systems, and actions:
Persistence/provider calls.

Exact work performed:
Expanded Settings drawer into sections for provider/model truth, workspace/project truth, backend truth, usage/cost, notification preferences, persistence, and config write gate.

Required tests/checks:
Static label grep.

Manual validation performed by Codex:
Layout is display-only.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Config write: no.

Rollback or recovery note:
Disable if ambiguous.

GO/NO-GO exit:
GO for Increment 7.2.1.

Next authorized increment only:
7.2.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 7.2.2

PLAN:
Plan 7/14.

PHASE:
Phase 7.2.

INCREMENT:
7.2.2, Add provider/model truth display.

Objective:
Provider truth display.

Isolated proxy lane scope:
UI fixture/existing truth display.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Provider calls and fake availability.

Exact work performed:
Added local LLM, GPT/cloud unavailable, Codex worker proposal-only, and future provider unavailable rows.

Required tests/checks:
Static grep and no-provider assertion.

Manual validation performed by Codex:
No provider call path or fake availability was added.

Evidence artifact:
Prototype/shared checks.

Stop conditions checked:
Network call: no.

Rollback or recovery note:
Unavailable.

GO/NO-GO exit:
GO for Increment 7.2.2.

Next authorized increment only:
7.3.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 7.2.1, 7.2.2.
Evidence reviewed: settings drawer layout and provider/model truth display.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Settings are prototype fixture display.
Decision: GO.
Next phase or increment: Phase 7.3, Increment 7.3.1.

## Increment 7.3.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.3, Workspace/project details display.

INCREMENT:
7.3.1, Add workspace/project truth display.

Objective:
Workspace truth.

Isolated proxy lane scope:
UI read-only context.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Project creation/live mutation.

Exact work performed:
Added Workspace/project truth section with SpiritOS read/list-only and no branch/worktree/commit/push/project creation/Windows bridge writes.

Required tests/checks:
Static grep.

Manual validation performed by Codex:
Workspace section is read-only.

Evidence artifact:
Prototype.

Stop conditions checked:
Mutation: no.

Rollback or recovery note:
Blocked state.

GO/NO-GO exit:
GO for Increment 7.3.1.

Next authorized increment only:
7.6.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 7.3.1.
Evidence reviewed: workspace/project truth display.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: No live project route used.
Decision: GO.
Next phase or increment: Phase 7.6, Increment 7.6.1.

## Increment 7.6.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.6, Backend truth display.

INCREMENT:
7.6.1, Add backend status display.

Objective:
Backend truth.

Isolated proxy lane scope:
UI fixture display.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Starting/restarting servers or live route calls.

Exact work performed:
Added Backend truth section listing self status, tools manifest, sandbox terminal, long-running task status, Codex adapter, and budget usage as not-wired/unavailable unless later approved.

Required tests/checks:
Static grep/no-route assertion.

Manual validation performed by Codex:
No backend route call was added.

Evidence artifact:
Prototype.

Stop conditions checked:
Restart needed: no.

Rollback or recovery note:
Unavailable.

GO/NO-GO exit:
GO for Increment 7.6.1.

Next authorized increment only:
7.4.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 7.4.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.4, Usage/time/cost display.

INCREMENT:
7.4.1, Add usage/time display if safe data exists.

Objective:
Usage display.

Isolated proxy lane scope:
UI display.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Provider/billing calls.

Exact work performed:
Added Usage and cost section that allows current-session UI timing but marks token usage, actual cost, budget status, and durable usage storage unavailable without real reports.

Required tests/checks:
Static grep/no-provider assertion.

Manual validation performed by Codex:
No fake cost/tokens or external call added.

Evidence artifact:
Prototype.

Stop conditions checked:
External call required: no.

Rollback or recovery note:
Unavailable state.

GO/NO-GO exit:
GO for Increment 7.4.1.

Next authorized increment only:
7.5.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 7.5.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.5, Notification preference display.

INCREMENT:
7.5.1, Add disabled persistence state.

Objective:
Show persistence disabled.

Isolated proxy lane scope:
UI display.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Persisting settings.

Exact work performed:
Added Notification preferences, Persistence, and Config write gate sections with disabled controls.

Required tests/checks:
Static grep for `Notifications disabled`, `Save disabled`, `Config writes gated`.

Manual validation performed by Codex:
Disabled states are explicit and no save handler was added.

Evidence artifact:
Prototype/shared checks.

Stop conditions checked:
Persistence writes: no.

Rollback or recovery note:
Disable.

GO/NO-GO exit:
GO for Increment 7.5.1.

Next authorized increment only:
7.6.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 7.6.1, 7.4.1, 7.5.1.
Evidence reviewed: backend, usage/time/cost, and disabled notification/persistence/config states.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Backend/usage truth remains fixture/unavailable where no real read exists.
Decision: GO.
Next phase or increment: Phase 7.6, Increment 7.6.2.

## Increment 7.6.2

PLAN:
Plan 7/14.

PHASE:
Phase 7.6.

INCREMENT:
7.6.2, Add no-provider-call proof.

Objective:
Prove settings no external calls.

Isolated proxy lane scope:
Static assertion.

Allowed files or file zones:
Read-only prototype input.

Forbidden files, paths, systems, and actions:
Network/provider calls.

Exact work performed:
Ran static grep and Node assertion for forbidden provider/config/storage patterns.

Required tests/checks:
Node assertion passed with 11 required settings labels and 20 forbidden patterns absent.

Manual validation performed by Codex:
No provider invocation, route call, env/config/auth write, browser storage, or notification prompt string exists.

Evidence artifact:
Shared checks.

Stop conditions checked:
Call path: no.

Rollback or recovery note:
Remove call path if introduced.

GO/NO-GO exit:
GO for Increment 7.6.2.

Next authorized increment only:
7.7.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 7.6.2.
Evidence reviewed: no-provider/no-config/no-storage assertion.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Static assertion only; no browser screenshot.
Decision: GO.
Next phase or increment: Phase 7.7, Increment 7.7.1.

## Increment 7.7.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.7, Accessibility and responsive behavior.

INCREMENT:
7.7.1, Add focus/keyboard behavior checks.

Objective:
WAI-ARIA drawer proof.

Isolated proxy lane scope:
Source/manual inspection.

Allowed files or file zones:
Prototype source.

Forbidden files, paths, systems, and actions:
Hidden traps.

Exact work performed:
Reviewed existing drawer markup and script: settings drawer has `role="dialog"`, `aria-modal="true"`, labelled title, close button, Escape close, close-button focus, backdrop close, and trigger focus restore.

Required tests/checks:
Source inspection from existing Plan 3/4 drawer proof.

Manual validation performed by Codex:
Settings drawer remains reachable and labelled; no hidden trap was added.

Evidence artifact:
Prototype source and this file.

Stop conditions checked:
Inaccessible drawer by source inspection: no.

Rollback or recovery note:
Fix isolated drawer if future browser keyboard proof fails.

GO/NO-GO exit:
GO for Increment 7.7.1.

Next authorized increment only:
7.8.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 7.7.1.
Evidence reviewed: settings drawer accessibility source review.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: No browser keyboard loop proof captured.
Decision: GO.
Next phase or increment: Phase 7.8, Increment 7.8.1.

## Increment 7.8.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.8, Tests and manual validation.

INCREMENT:
7.8.1, Add tests.

Objective:
Settings tests.

Isolated proxy lane scope:
Ad hoc static Node assertion; no production test file.

Allowed files or file zones:
Read-only prototype input and Plan 7 evidence.

Forbidden files, paths, systems, and actions:
Provider/env/config mutation.

Exact work performed:
Ran Node static assertion for required settings labels and forbidden provider/config/storage patterns.

Required tests/checks:
Assertion passed.

Manual validation performed by Codex:
Truth display and disabled states are present.

Evidence artifact:
Shared checks.

Stop conditions checked:
Fail: no.

Rollback or recovery note:
Fix isolated prototype if assertion fails.

GO/NO-GO exit:
GO for Increment 7.8.1.

Next authorized increment only:
7.8.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 7.8.2

PLAN:
Plan 7/14.

PHASE:
Phase 7.8.

INCREMENT:
7.8.2, Add manual validation.

Objective:
Operator settings review.

Isolated proxy lane scope:
Manual source/terminal review.

Allowed files or file zones:
Prototype source and Plan 7 evidence.

Forbidden files, paths, systems, and actions:
Save/persist.

Exact work performed:
Reviewed settings sections, disabled states, no-call assertions, status/diff, and drawer accessibility source.

Required tests/checks:
Manual checklist by Codex.

Manual validation performed by Codex:
Settings display truth and disabled states without mutation.

Evidence artifact:
This file.

Stop conditions checked:
Mutation: no.

Rollback or recovery note:
Disable/gate future ambiguous controls.

GO/NO-GO exit:
GO for Increment 7.8.2.

Next authorized increment only:
7.9.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 7.8.1, 7.8.2.
Evidence reviewed: Node assertion and manual validation checklist.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: No browser no-write check captured.
Decision: GO.
Next phase or increment: Phase 7.9, Increment 7.9.1.

## Increment 7.9.1

PLAN:
Plan 7/14.

PHASE:
Phase 7.9, Closeout gate.

INCREMENT:
7.9.1, Closeout gate.

Objective:
Plan 8 readiness.

Isolated proxy lane scope:
Evidence summary.

Allowed files or file zones:
Plan 7 evidence and isolated prototype.

Forbidden files, paths, systems, and actions:
Further implementation without approval.

Exact work performed:
Summarized truth/no-mutation proof and ran final status/diff/no-provider checks.

Required tests/checks:
Shared checks above.

Manual validation performed by Codex:
Settings displays truth and disabled states without env/config/provider mutation.

Evidence artifact:
This file.

Stop conditions checked:
Env/config/provider mutation: no.

Rollback or recovery note:
Return to offender if future mutation appears.

GO/NO-GO exit:
GO for Increment 7.9.1.

Next authorized increment only:
Plan 8/14, Phase 8.1, Increment 8.1.1 only if operator approves.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 7.9.1.
Evidence reviewed: full Plan 7 evidence packet and prototype checks.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Plan 8 remains unauthorized until operator permission.
Decision: GO.
Next phase or increment: Plan 8/14, Phase 8.1, Increment 8.1.1 only if operator approves.

PLAN 7/14 CLOSEOUT:
Completed phases: 7.1, 7.2, 7.3, 7.6, 7.4, 7.5, 7.6 continuation, 7.7, 7.8, 7.9.
Evidence reviewed: this packet, settings/provider/backend/workspace/usage inventory, updated isolated prototype, static feature grep, no-provider/no-config/no-storage grep, Node assertion, status/diff.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Dirty tree preserved without cleanup: Yes.
Known risks: No browser screenshot or browser no-write check was captured; Plan 7 is isolated static prototype evidence, not production settings persistence.
Decision: GO.
Next authorized plan: Plan 8/14, Phase 8.1, Increment 8.1.1 only.
Permission request: Ask operator before starting Plan 8/14.

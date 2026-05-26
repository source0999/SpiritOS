# Plan 4/14: Codex-Like Active Task Feature Completion

PLAN:
Plan 4/14, Codex-like Active Task Feature Completion.

Evidence root:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-4/`

Updated isolated prototype:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html`

Global forbidden actions:
No provider calls. No apply. No execute-approved route call. No queue execution. No hidden workers. No long-running task advancement. No branch/worktree/git mutation. No Cartographer mutation. No production route/component/backend edits. No package install. No production Source Proxy state mutation. No production map state mutation.

Shared checks:
```text
$ grep -En "Task Packet|Plan Preview|Proposed Files|Approval Required|Verify Required|Blocked State|Receipt Browser|Validation summary|Active Task Empty State|Queue blocked" docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html
516: Task Packet
538: Plan Preview
550: Approval Required
554: Verify Required
558: Blocked State
566: Active Task Empty State
575: Plan Preview
584: Proposed Files
611: Blocked States
617: Queue blocked: no task advancement or background worker
622: Receipt Browser
675: Validation summary

$ grep -En "fetch\(|XMLHttpRequest|localStorage|indexedDB|navigator\.sendBeacon|serviceWorker|new Worker|Worker\(|/v1/actions|/v1/tasks" docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html
<no output>

$ node - <<'NODE'
<static assertion script checked 11 required labels and 10 forbidden call patterns>
NODE
Plan 4 static assertions passed: 11 required labels present; 10 forbidden call patterns absent.

$ git -C /home/source/SpiritOS status --short --branch --untracked-files=normal
## main...origin/main
?? docs/evidence/
?? docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md

$ git -C /home/source/SpiritOS diff --name-status
<no output>
```

## Increment 4.1.1

PLAN:
Plan 4/14.

PHASE:
Phase 4.1, Active task transcript behavior.

INCREMENT:
4.1.1, Map task packet schema.

Objective:
Map task packet fields.

Isolated proxy lane scope:
UI/schema only in the isolated prototype.

Allowed files or file zones:
`docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html` and Plan 4 evidence.

Forbidden files, paths, systems, and actions:
Worker execution, queue mutation, provider calls, apply, execute-approved, production edits.

Exact work performed:
Added task packet schema fixture with id, intent, files, states, and evidence fields.

Required tests/checks:
Static grep for `Task Packet`.

Manual validation performed by Codex:
Schema is display-safe and fixture-only.

Evidence artifact:
Prototype and this closeout packet.

Stop conditions checked:
Hidden worker needed: no.

Rollback or recovery note:
Use fixture state only; correct by owned prototype patch if needed.

GO/NO-GO exit:
GO for Increment 4.1.1.

Next authorized increment only:
4.1.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 4.1.2

PLAN:
Plan 4/14.

PHASE:
Phase 4.1.

INCREMENT:
4.1.2, Render active task timeline.

Objective:
Render transcript events.

Isolated proxy lane scope:
UI-only fixture events.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Queue mutation, live task advancement, worker execution.

Exact work performed:
Extended timeline with approval-required, verify-required, and blocked events.

Required tests/checks:
Static grep for `Approval Required`, `Verify Required`, and `Blocked State`.

Manual validation performed by Codex:
Timeline is display-only and does not advance any task.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Live task advancement: no.

Rollback or recovery note:
Fixture-only timeline.

GO/NO-GO exit:
GO for Increment 4.1.2.

Next authorized increment only:
4.2.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 4.1.1, 4.1.2.
Evidence reviewed: schema fixture and timeline labels.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Timeline remains static prototype evidence.
Decision: GO.
Next phase or increment: Phase 4.2, Increment 4.2.1.

## Increment 4.2.1

PLAN:
Plan 4/14.

PHASE:
Phase 4.2, Composer intent handling.

INCREMENT:
4.2.1, Render operator prompt/composer input safely.

Objective:
Render intent capture without provider execution.

Isolated proxy lane scope:
UI-only local draft.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Provider/network/queue calls, long-running task advancement.

Exact work performed:
Kept draft textarea and disabled send button; confirmed no forbidden call patterns.

Required tests/checks:
Static assertion passed and no-authority grep returned no output.

Manual validation performed by Codex:
Typing would be local in the static page; send remains disabled.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Provider call: no.

Rollback or recovery note:
Keep submit disabled if route boundary is unclear.

GO/NO-GO exit:
GO for Increment 4.2.1.

Next authorized increment only:
4.3.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 4.2.1.
Evidence reviewed: composer disabled state and no-call grep.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Composer is static prototype only.
Decision: GO.
Next phase or increment: Phase 4.3, Increment 4.3.1.

## Increment 4.3.1

PLAN:
Plan 4/14.

PHASE:
Phase 4.3, Plan preview and task packet display.

INCREMENT:
4.3.1, Render plan preview card.

Objective:
Display proposed plan.

Isolated proxy lane scope:
UI fixture only.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Apply/preview route calls.

Exact work performed:
Added Plan Preview card with display-only and no-preview-route-call badges.

Required tests/checks:
Static grep for `Plan Preview`; no `/v1/actions` route string.

Manual validation performed by Codex:
Plan preview is display-only and cannot start route calls.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Starts preview route: no.

Rollback or recovery note:
Remove route-call affordance if introduced.

GO/NO-GO exit:
GO for Increment 4.3.1.

Next authorized increment only:
4.3.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 4.3.2

PLAN:
Plan 4/14.

PHASE:
Phase 4.3.

INCREMENT:
4.3.2, Render proposed file list.

Objective:
Display proposed files.

Isolated proxy lane scope:
UI fixture only.

Allowed files or file zones:
Prototype and Plan 4 evidence paths.

Forbidden files, paths, systems, and actions:
Production file edits and protected path mutation.

Exact work performed:
Added Proposed Files card with allowed prototype/evidence paths and forbidden production/source/runtime/Cartographer paths.

Required tests/checks:
Static grep for `Proposed Files`.

Manual validation performed by Codex:
File list is display-only.

Evidence artifact:
Prototype.

Stop conditions checked:
File mutation: no.

Rollback or recovery note:
Remove action if any file mutation control appears.

GO/NO-GO exit:
GO for Increment 4.3.2.

Next authorized increment only:
4.6.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 4.3.1, 4.3.2.
Evidence reviewed: plan preview and proposed file list.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Proposed file list is fixture guidance, not an enforceable runtime allowlist.
Decision: GO.
Next phase or increment: Phase 4.6, Increment 4.6.1.

## Increment 4.6.1

PLAN:
Plan 4/14.

PHASE:
Phase 4.6, UI-only state transitions.

INCREMENT:
4.6.1, Render approval-required state.

Objective:
Show approval boundary.

Isolated proxy lane scope:
UI fixture state.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Approval execution and apply.

Exact work performed:
Added Approval Required timeline event stating approval discussion is not apply and no approval execution path exists.

Required tests/checks:
Static grep for `Approval Required`.

Manual validation performed by Codex:
No enabled approval/apply control exists.

Evidence artifact:
Prototype.

Stop conditions checked:
Approve button applies: no approve button exists.

Rollback or recovery note:
Disable/remove any execution control.

GO/NO-GO exit:
GO for Increment 4.6.1.

Next authorized increment only:
4.6.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 4.6.2

PLAN:
Plan 4/14.

PHASE:
Phase 4.6.

INCREMENT:
4.6.2, Render verify-required state.

Objective:
Show verification state.

Isolated proxy lane scope:
UI fixture state.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Verification worker and task advancement.

Exact work performed:
Added Verify Required timeline event stating current verification is static evidence review.

Required tests/checks:
Static grep for `Verify Required`.

Manual validation performed by Codex:
No verification worker is started.

Evidence artifact:
Prototype.

Stop conditions checked:
Worker starts: no.

Rollback or recovery note:
Keep display-only.

GO/NO-GO exit:
GO for Increment 4.6.2.

Next authorized increment only:
4.6.3.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 4.6.3

PLAN:
Plan 4/14.

PHASE:
Phase 4.6.

INCREMENT:
4.6.3, Render blocked state.

Objective:
Show blocked state.

Isolated proxy lane scope:
UI fixture state.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Bypass controls.

Exact work performed:
Added blocked event and Queue blocked list item.

Required tests/checks:
Static grep for `Blocked State` and `Queue blocked`.

Manual validation performed by Codex:
Blocked state is unambiguous and no bypass control exists.

Evidence artifact:
Prototype.

Stop conditions checked:
Bypass exists: no.

Rollback or recovery note:
Remove bypass controls if introduced.

GO/NO-GO exit:
GO for Increment 4.6.3.

Next authorized increment only:
4.4.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 4.6.1, 4.6.2, 4.6.3.
Evidence reviewed: approval, verify, and blocked states.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: State transitions are static display, not interactive runtime state.
Decision: GO.
Next phase or increment: Phase 4.4, Increment 4.4.1.

## Increment 4.4.1

PLAN:
Plan 4/14.

PHASE:
Phase 4.4, Evidence/receipt browsing display.

INCREMENT:
4.4.1, Render evidence receipt list.

Objective:
Display receipts.

Isolated proxy lane scope:
Read-only fixture/isolated evidence display.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Live evidence writes and soak log writes.

Exact work performed:
Added Receipt Browser card and Evidence drawer receipt-list section referencing Plan 0 through Plan 3 closeouts.

Required tests/checks:
Static grep for `Receipt Browser`.

Manual validation performed by Codex:
Receipt list is display-only and does not write live evidence.

Evidence artifact:
Prototype.

Stop conditions checked:
Writes receipts: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 4.4.1.

Next authorized increment only:
4.5.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 4.4.1.
Evidence reviewed: receipt browser and evidence drawer receipt list.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Receipts are static references.
Decision: GO.
Next phase or increment: Phase 4.5, Increment 4.5.1.

## Increment 4.5.1

PLAN:
Plan 4/14.

PHASE:
Phase 4.5, Diagnostics drawer detail expansion.

INCREMENT:
4.5.1, Render diagnostics summary.

Objective:
Display diagnostics details.

Isolated proxy lane scope:
UI display only.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Runner execution, provider calls, soak writers.

Exact work performed:
Added diagnostics validation summary and blockers.

Required tests/checks:
Static grep for `Validation summary`; no forbidden call pattern found.

Manual validation performed by Codex:
Diagnostics remains display-only with run disabled.

Evidence artifact:
Prototype.

Stop conditions checked:
Runner starts: no.

Rollback or recovery note:
Keep buttons disabled/preview-only.

GO/NO-GO exit:
GO for Increment 4.5.1.

Next authorized increment only:
4.6.4.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 4.5.1.
Evidence reviewed: diagnostics summary and no-run copy.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Diagnostics summary is fixture evidence.
Decision: GO.
Next phase or increment: Phase 4.6, Increment 4.6.4.

## Increment 4.6.4

PLAN:
Plan 4/14.

PHASE:
Phase 4.6.

INCREMENT:
4.6.4, Render active task empty state.

Objective:
Safe default.

Isolated proxy lane scope:
UI-only display.

Allowed files or file zones:
Prototype HTML only.

Forbidden files, paths, systems, and actions:
Auto-create task, hidden worker, queue mutation.

Exact work performed:
Added Active Task Empty State card with no auto-create and no hidden worker badges.

Required tests/checks:
Static grep for `Active Task Empty State`.

Manual validation performed by Codex:
Empty state does not create tasks.

Evidence artifact:
Prototype.

Stop conditions checked:
Hidden task creation: no.

Rollback or recovery note:
Remove any auto-create behavior if introduced.

GO/NO-GO exit:
GO for Increment 4.6.4.

Next authorized increment only:
4.7.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 4.6.4.
Evidence reviewed: empty state card.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Empty state is static prototype proof.
Decision: GO.
Next phase or increment: Phase 4.7, Increment 4.7.1.

## Increment 4.7.1

PLAN:
Plan 4/14.

PHASE:
Phase 4.7, Tests and manual validation.

INCREMENT:
4.7.1, Add tests for state transitions.

Objective:
Automated state proof.

Isolated proxy lane scope:
Ad hoc static Node assertion; no production test file.

Allowed files or file zones:
Read-only prototype input and Plan 4 evidence.

Forbidden files, paths, systems, and actions:
Provider/backend calls, package install, production test edits.

Exact work performed:
Ran Node static assertion checking 11 required labels and 10 forbidden call patterns.

Required tests/checks:
Node assertion passed.

Manual validation performed by Codex:
Required state labels are present and forbidden call patterns absent.

Evidence artifact:
Shared checks.

Stop conditions checked:
Failing required test: no.

Rollback or recovery note:
Fix isolated prototype only if assertion fails.

GO/NO-GO exit:
GO for Increment 4.7.1.

Next authorized increment only:
4.7.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 4.7.2

PLAN:
Plan 4/14.

PHASE:
Phase 4.7.

INCREMENT:
4.7.2, Add manual checklist.

Objective:
Operator rehearsal.

Isolated proxy lane scope:
Manual source review checklist.

Allowed files or file zones:
Plan 4 evidence only.

Forbidden files, paths, systems, and actions:
Execution, provider calls, apply, queue mutation.

Exact work performed:
Checklist reviewed timeline, composer, preview, file list, receipts, diagnostics, blocked states, no-call proof, and final status/diff.

Required tests/checks:
Manual pass by Codex source inspection and terminal output review.

Manual validation performed by Codex:
Controls are clear: send disabled, run disabled, apply disabled, no route/network strings.

Evidence artifact:
This packet.

Stop conditions checked:
Unclear control: no.

Rollback or recovery note:
Fix or block future ambiguous control.

GO/NO-GO exit:
GO for Increment 4.7.2.

Next authorized increment only:
4.8.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 4.7.1, 4.7.2.
Evidence reviewed: Node static assertion and manual checklist.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: No browser screenshot; validation is source/static/terminal based.
Decision: GO.
Next phase or increment: Phase 4.8, Increment 4.8.1.

## Increment 4.8.1

PLAN:
Plan 4/14.

PHASE:
Phase 4.8, Closeout gate.

INCREMENT:
4.8.1, Closeout gate.

Objective:
Decide Plan 5 readiness.

Isolated proxy lane scope:
Evidence summary only.

Allowed files or file zones:
Plan 4 evidence and isolated prototype.

Forbidden files, paths, systems, and actions:
Implementation continuation without approval and all global forbidden actions.

Exact work performed:
Summarized state features and authority proof; ran final status/diff/no-call checks.

Required tests/checks:
Shared checks above.

Manual validation performed by Codex:
Command center prototype displays task states/operator controls without crossing boundaries.

Evidence artifact:
This file.

Stop conditions checked:
Authority boundary crossed: no.

Rollback or recovery note:
Return to offending increment if disputed; no git cleanup.

GO/NO-GO exit:
GO for Increment 4.8.1.

Next authorized increment only:
Plan 5/14, Phase 5.1, Increment 5.1.1 only if operator approves.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 4.8.1.
Evidence reviewed: full Plan 4 evidence packet and prototype checks.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Plan 5 remains unauthorized until operator permission.
Decision: GO.
Next phase or increment: Plan 5/14, Phase 5.1, Increment 5.1.1 only if operator approves.

PLAN 4/14 CLOSEOUT:
Completed phases: 4.1, 4.2, 4.3, 4.6, 4.4, 4.5, 4.6 continuation, 4.7, 4.8.
Evidence reviewed: this packet, updated isolated prototype, static feature grep, no-authority grep, Node assertions, status/diff.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Dirty tree preserved without cleanup: Yes.
Known risks: No browser screenshot was captured; Plan 4 remains isolated static prototype evidence rather than production route implementation.
Decision: GO.
Next authorized plan: Plan 5/14, Phase 5.1, Increment 5.1.1 only.
Permission request: Ask operator before starting Plan 5/14.

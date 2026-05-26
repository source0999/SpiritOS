# Plan 8/14: Pre-Soak-Completion Stabilization And Feature Assurance

PLAN:
Plan 8/14, Pre-Soak-Completion Stabilization and Feature Assurance.

Evidence root:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-8/`

Stabilized isolated prototype:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html`

Global forbidden actions:
No implementation outside the isolated lane. No provider calls. No apply. No execute-approved route call. No Cartographer writes. No Scout or Cartographer soak log writes. No live evidence writes. No runtime state writes. No production map state mutation. No production Source Proxy state mutation. No hidden workers. No queue mutation. No shared storage mutation. No package install. No git mutation.

Shared checks:
```text
$ node - <<'NODE'
<cross-feature assertion checked command center, drawers, chips, blocked states, design packet, chat/media/projects/settings labels and forbidden patterns>
NODE
Plan 8 readiness assertions passed: 38 required feature labels present; 24 forbidden authority/storage/live patterns absent.

$ find /home/source/SpiritOS/docs/evidence -maxdepth 2 -type f -path '*/unified-proxy-coding-design-plan-*/*' -printf '%P\n' | sort | wc -l
41

$ git -C /home/source/SpiritOS status --porcelain=v1 --untracked-files=normal | grep -E 'cartographer|scout|\.codex|source_proxy/cartographer|docs/cartographer-live|src/app/map|data/cartographer|data/source-proxy'
<no output>

$ git -C /home/source/SpiritOS status --short --branch --untracked-files=normal
## main...origin/main
?? docs/evidence/
?? docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md

$ git -C /home/source/SpiritOS diff --name-status
<no output>
```

Cross-feature matrix:

| Feature group | Required labels/proof | Result |
|---|---|---|
| Command center states | Active Task Transcript, Task Packet, Plan Preview, Approval Required, Verify Required, Blocked State, Active Task Empty State, Send disabled | PASS |
| Drawers | Settings, Diagnostics, Evidence, Design Intake, Provider/model truth, Validation summary, Receipt list, Proposal lane | PASS |
| Chips | Project, Provider, Safety, Dirty tree, Approval | PASS |
| Blocked states | Provider unavailable, Apply disabled, Cartographer protected, Design apply unavailable, Queue blocked, No provider send, No storage write, No live Cartographer call, Config writes gated | PASS |
| Design packet | Read-Only Design Packet, Design Context Handoff, No design apply | PASS |
| Work lanes | Chat Work Lane, Media Work Lane, Project Selector, Project Health, Settings | PASS |
| Forbidden authority/storage/live patterns | apply routes, provider/network calls, storage writes, workers, live Cartographer calls/scans | PASS |
| Protected paths | Cartographer/Scout/live evidence/runtime/map/source-proxy protected status grep | PASS |

## Increment 8.1.1

PLAN:
Plan 8/14.

PHASE:
Phase 8.1, Cross-feature regression matrix.

INCREMENT:
8.1.1, Build cross-feature matrix.

Objective:
Matrix all safe features.

Isolated proxy lane scope:
Evidence/test planning only.

Allowed files or file zones:
Plan 8 evidence.

Forbidden files, paths, systems, and actions:
Implementation outside evidence/prototype.

Exact work performed:
Built the cross-feature matrix above covering command center states, drawers, chips, blocked states, design packet, chat/media/projects/settings lanes, forbidden patterns, and protected paths.

Required tests/checks:
Node cross-feature assertion.

Manual validation performed by Codex:
No critical feature group from Plans 2 through 7 is missing.

Evidence artifact:
This file.

Stop conditions checked:
Missing critical feature: no.

Rollback or recovery note:
Add matrix row by evidence-only patch if a gap is found.

GO/NO-GO exit:
GO for Increment 8.1.1.

Next authorized increment only:
8.2.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 8.2.1

PLAN:
Plan 8/14.

PHASE:
Phase 8.2, `/coding` route manual operator rehearsal.

INCREMENT:
8.2.1, Test all command center states.

Objective:
Operator rehearsal.

Isolated proxy lane scope:
Manual/static rehearsal against isolated prototype.

Allowed files or file zones:
Read-only prototype review and Plan 8 evidence.

Forbidden files, paths, systems, and actions:
Provider/apply/execute-approved.

Exact work performed:
Validated empty, timeline, preview, approval, verify, and blocked labels in the prototype assertion.

Required tests/checks:
Cross-feature assertion command-center group passed.

Manual validation performed by Codex:
No unsafe control was found; send remains disabled.

Evidence artifact:
Shared checks and cross-feature matrix.

Stop conditions checked:
Unsafe control: no.

Rollback or recovery note:
Fix/gate isolated prototype if a future unsafe control appears.

GO/NO-GO exit:
GO for Increment 8.2.1.

Next authorized increment only:
8.3.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 8.1.1, 8.2.1.
Evidence reviewed: cross-feature matrix and command-center rehearsal.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Rehearsal is static/source-based, not browser screenshot proof.
Decision: GO.
Next phase or increment: Phase 8.3, Increment 8.3.1.

## Increment 8.3.1

PLAN:
Plan 8/14.

PHASE:
Phase 8.3, Drawer and chip consistency pass.

INCREMENT:
8.3.1, Test all drawer states.

Objective:
Drawer consistency.

Isolated proxy lane scope:
Static/manual drawer review.

Allowed files or file zones:
Prototype source and evidence.

Forbidden files, paths, systems, and actions:
Mutation.

Exact work performed:
Validated Settings, Diagnostics, Evidence, and Design Intake labels plus key drawer contents.

Required tests/checks:
Cross-feature assertion drawer group passed.

Manual validation performed by Codex:
Drawers remain display-only.

Evidence artifact:
Shared checks.

Stop conditions checked:
Broken focus/authority by source inspection: no.

Rollback or recovery note:
Fix/gate drawer source if future browser proof fails.

GO/NO-GO exit:
GO for Increment 8.3.1.

Next authorized increment only:
8.3.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 8.3.2

PLAN:
Plan 8/14.

PHASE:
Phase 8.3.

INCREMENT:
8.3.2, Test all chips.

Objective:
Chip consistency.

Isolated proxy lane scope:
Static chip label assertions.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
Hidden truth.

Exact work performed:
Validated Project, Provider, Safety, Dirty tree, and Approval chips.

Required tests/checks:
Cross-feature assertion chip group passed.

Manual validation performed by Codex:
No chip hides critical safety truth.

Evidence artifact:
Shared checks.

Stop conditions checked:
Misleading chip: no.

Rollback or recovery note:
Relabel if a chip becomes ambiguous.

GO/NO-GO exit:
GO for Increment 8.3.2.

Next authorized increment only:
8.3.3.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 8.3.3

PLAN:
Plan 8/14.

PHASE:
Phase 8.3.

INCREMENT:
8.3.3, Test all blocked states.

Objective:
Blocked-state proof.

Isolated proxy lane scope:
Fixture/static review.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
Bypass controls.

Exact work performed:
Validated provider, apply, Cartographer, design, storage, queue, live Cartographer, and config-write blocked states.

Required tests/checks:
Cross-feature assertion blocked-state group passed.

Manual validation performed by Codex:
No bypass control exists.

Evidence artifact:
Shared checks.

Stop conditions checked:
Bypass: no.

Rollback or recovery note:
Block/remove any bypass if introduced.

GO/NO-GO exit:
GO for Increment 8.3.3.

Next authorized increment only:
8.4.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 8.3.1, 8.3.2, 8.3.3.
Evidence reviewed: drawer, chip, and blocked-state matrix rows.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Focus proof remains source/static.
Decision: GO.
Next phase or increment: Phase 8.4, Increment 8.4.1.

## Increment 8.4.1

PLAN:
Plan 8/14.

PHASE:
Phase 8.4, Design token consistency pass without full CSS polish.

INCREMENT:
8.4.1, Test read-only design packet display.

Objective:
Design packet regression.

Isolated proxy lane scope:
Display-only check.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
Apply.

Exact work performed:
Validated Read-Only Design Packet, Design Context Handoff, and No design apply labels.

Required tests/checks:
Cross-feature assertion design group passed.

Manual validation performed by Codex:
No design apply authority exists.

Evidence artifact:
Shared checks.

Stop conditions checked:
Apply authority: no.

Rollback or recovery note:
Remove any apply-like control.

GO/NO-GO exit:
GO for Increment 8.4.1.

Next authorized increment only:
8.5.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 8.4.1.
Evidence reviewed: design packet regression row.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Token consistency is label/prototype proof only, not full CSS polish.
Decision: GO.
Next phase or increment: Phase 8.5, Increment 8.5.1.

## Increment 8.5.1

PLAN:
Plan 8/14.

PHASE:
Phase 8.5, Chat/media/projects/settings navigation rehearsal.

INCREMENT:
8.5.1, Test chat/media lane cards.

Objective:
Lane nav proof.

Isolated proxy lane scope:
Read-only prototype review.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
Storage/provider.

Exact work performed:
Validated Chat Work Lane and Media Work Lane labels and blocked storage/provider states.

Required tests/checks:
Cross-feature assertion lanes and blocked-state groups passed.

Manual validation performed by Codex:
No chat/media storage or provider mutation path exists.

Evidence artifact:
Shared checks.

Stop conditions checked:
Mutation: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 8.5.1.

Next authorized increment only:
8.5.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 8.5.2

PLAN:
Plan 8/14.

PHASE:
Phase 8.5.

INCREMENT:
8.5.2, Test projects read-only shell.

Objective:
Projects read-only proof.

Isolated proxy lane scope:
Fixture/read-only prototype.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
Live Cartographer mutation.

Exact work performed:
Validated Project Selector, Project Health, Live Cartographer Gate, and No live Cartographer call.

Required tests/checks:
Cross-feature assertion lanes/blocked-state groups passed and protected path status grep returned no output.

Manual validation performed by Codex:
Live Cartographer integration remains gated.

Evidence artifact:
Shared checks.

Stop conditions checked:
Live mutation: no.

Rollback or recovery note:
Blocked state.

GO/NO-GO exit:
GO for Increment 8.5.2.

Next authorized increment only:
8.5.3.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 8.5.3

PLAN:
Plan 8/14.

PHASE:
Phase 8.5.

INCREMENT:
8.5.3, Test settings truth display.

Objective:
Settings proof.

Isolated proxy lane scope:
Display-only prototype.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
Env/config/provider mutation.

Exact work performed:
Validated Settings, Provider/model truth, Config writes gated, and related no-provider/no-storage patterns.

Required tests/checks:
Cross-feature assertion drawers/blocked-state groups passed.

Manual validation performed by Codex:
Settings remains truth display only.

Evidence artifact:
Shared checks.

Stop conditions checked:
Mutation: no.

Rollback or recovery note:
Disable/gate if ambiguous.

GO/NO-GO exit:
GO for Increment 8.5.3.

Next authorized increment only:
8.6.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 8.5.1, 8.5.2, 8.5.3.
Evidence reviewed: chat/media, projects, settings rehearsal rows.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Navigation proof is static, not browser navigation.
Decision: GO.
Next phase or increment: Phase 8.6, Increment 8.6.1.

## Increment 8.6.1

PLAN:
Plan 8/14.

PHASE:
Phase 8.6, No-authority gauntlet.

INCREMENT:
8.6.1, Confirm no apply path.

Objective:
No apply proof.

Isolated proxy lane scope:
Static assertion.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
execute-approved/apply.

Exact work performed:
Cross-feature assertion checked apply-route patterns and required Apply disabled/No design apply labels.

Required tests/checks:
Forbidden apply patterns absent.

Manual validation performed by Codex:
No enabled apply control.

Evidence artifact:
Shared checks.

Stop conditions checked:
Apply path: no.

Rollback or recovery note:
Remove if introduced.

GO/NO-GO exit:
GO for Increment 8.6.1.

Next authorized increment only:
8.6.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 8.6.2

PLAN:
Plan 8/14.

PHASE:
Phase 8.6.

INCREMENT:
8.6.2, Confirm no execute-approved path.

Objective:
execute-approved blocked.

Isolated proxy lane scope:
Static no-call assertion.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
Route call.

Exact work performed:
Checked `/v1/actions` and execute-approved call-shaped patterns absent.

Required tests/checks:
Forbidden apply patterns absent.

Manual validation performed by Codex:
No route invocation exists.

Evidence artifact:
Shared checks.

Stop conditions checked:
Invocation: no.

Rollback or recovery note:
Remove if introduced.

GO/NO-GO exit:
GO for Increment 8.6.2.

Next authorized increment only:
8.6.3.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 8.6.3

PLAN:
Plan 8/14.

PHASE:
Phase 8.6.

INCREMENT:
8.6.3, Confirm no provider calls.

Objective:
Provider blocked.

Isolated proxy lane scope:
Static assertion.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
Network/provider.

Exact work performed:
Checked fetch, XMLHttpRequest, sendBeacon, sendMessage, and useChat patterns absent.

Required tests/checks:
Forbidden provider patterns absent.

Manual validation performed by Codex:
No provider/model call path exists.

Evidence artifact:
Shared checks.

Stop conditions checked:
Call path: no.

Rollback or recovery note:
Disable if introduced.

GO/NO-GO exit:
GO for Increment 8.6.3.

Next authorized increment only:
8.6.4.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 8.6.4

PLAN:
Plan 8/14.

PHASE:
Phase 8.6.

INCREMENT:
8.6.4, Confirm no Cartographer writes.

Objective:
Cartographer protected.

Isolated proxy lane scope:
Read-only status/path review.

Allowed files or file zones:
Read-only git status/diff.

Forbidden files, paths, systems, and actions:
Cartographer writes/log mutation.

Exact work performed:
Ran protected-path status grep; no output.

Required tests/checks:
Protected-path grep returned no output.

Manual validation performed by Codex:
No Cartographer/Scout/live evidence/runtime/map/source-proxy protected status entries.

Evidence artifact:
Shared checks.

Stop conditions checked:
Protected change: no.

Rollback or recovery note:
NO-GO if protected path appears.

GO/NO-GO exit:
GO for Increment 8.6.4.

Next authorized increment only:
8.6.5.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 8.6.5

PLAN:
Plan 8/14.

PHASE:
Phase 8.6.

INCREMENT:
8.6.5, Confirm no shared storage mutation.

Objective:
Storage safety.

Isolated proxy lane scope:
Static no-write assertion.

Allowed files or file zones:
Prototype/evidence.

Forbidden files, paths, systems, and actions:
IndexedDB/localStorage destructive writes.

Exact work performed:
Checked localStorage, IndexedDB, setItem, db, save/write call-shaped patterns absent.

Required tests/checks:
Forbidden storage patterns absent.

Manual validation performed by Codex:
No storage mutation path exists in prototype.

Evidence artifact:
Shared checks.

Stop conditions checked:
Storage changed: no.

Rollback or recovery note:
NO-GO/fix if storage path appears.

GO/NO-GO exit:
GO for Increment 8.6.5.

Next authorized increment only:
8.6.6.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 8.6.6

PLAN:
Plan 8/14.

PHASE:
Phase 8.6.

INCREMENT:
8.6.6, Confirm no soak log mutation.

Objective:
Soak logs untouched.

Isolated proxy lane scope:
Read-only status/path check.

Allowed files or file zones:
Read-only git status/diff.

Forbidden files, paths, systems, and actions:
Log writes.

Exact work performed:
Protected-path status grep included Cartographer/Scout log and live evidence patterns; no output.

Required tests/checks:
Protected-path grep returned no output.

Manual validation performed by Codex:
No soak log path is dirty.

Evidence artifact:
Shared checks.

Stop conditions checked:
Log changed: no.

Rollback or recovery note:
NO-GO if log path appears.

GO/NO-GO exit:
GO for Increment 8.6.6.

Next authorized increment only:
8.7.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 8.6.1, 8.6.2, 8.6.3, 8.6.4, 8.6.5, 8.6.6.
Evidence reviewed: no-authority gauntlet and protected-path status proof.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Static no-authority proof does not replace future production integration tests.
Decision: GO.
Next phase or increment: Phase 8.7, Increment 8.7.1.

## Increment 8.7.1

PLAN:
Plan 8/14.

PHASE:
Phase 8.7, Evidence consolidation.

INCREMENT:
8.7.1, Produce readiness evidence.

Objective:
Consolidate Plan 8.

Isolated proxy lane scope:
Plan 8 evidence root.

Allowed files or file zones:
Isolated evidence only.

Forbidden files, paths, systems, and actions:
Live evidence writes.

Exact work performed:
Consolidated matrix, assertions, protected-path proof, status/diff, risks, and phase closeouts into this packet.

Required tests/checks:
Evidence artifact review; prior evidence count was 41 before writing Plan 8 packet.

Manual validation performed by Codex:
This packet proves what happened and what did not happen.

Evidence artifact:
This file.

Stop conditions checked:
Missing proof: no.

Rollback or recovery note:
Rerun safe checks if disputed.

GO/NO-GO exit:
GO for Increment 8.7.1.

Next authorized increment only:
8.8.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 8.7.1.
Evidence reviewed: readiness package.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Evidence is consolidated in one packet.
Decision: GO.
Next phase or increment: Phase 8.8, Increment 8.8.1.

## Increment 8.8.1

PLAN:
Plan 8/14.

PHASE:
Phase 8.8, Closeout gate.

INCREMENT:
8.8.1, Closeout gate.

Objective:
Decide Plan 9 readiness.

Isolated proxy lane scope:
Evidence summary only.

Allowed files or file zones:
Plan 8 evidence.

Forbidden files, paths, systems, and actions:
Cartographer live integration.

Exact work performed:
Reviewed all Plan 8 increments and identified remaining blockers.

Required tests/checks:
Final status/diff/no-authority and protected-path checks.

Manual validation performed by Codex:
Safe non-Cartographer features are stable in isolated static prototype evidence. The only true remaining blockers are Cartographer soak acceptance and exact future integration approval.

Evidence artifact:
This file.

Stop conditions checked:
Non-Cartographer features unstable: no.

Rollback or recovery note:
Return to failing increment if future proof contradicts this packet.

GO/NO-GO exit:
GO for Increment 8.8.1.

Next authorized increment only:
Plan 9/14, Phase 9.1, Increment 9.1.1 only if operator approves.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 8.8.1.
Evidence reviewed: full Plan 8 readiness package.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Plan 9 remains unauthorized until operator permission.
Decision: GO.
Next phase or increment: Plan 9/14, Phase 9.1, Increment 9.1.1 only if operator approves.

PLAN 8/14 CLOSEOUT:
Completed phases: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8.
Evidence reviewed: this packet, accumulated Plan 0 through Plan 7 evidence, isolated prototype, cross-feature assertion, no-authority gauntlet, protected-path grep, status/diff.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Dirty tree preserved without cleanup: Yes.
Known risks: No browser screenshot or live route proof was captured; stabilization is isolated static prototype/evidence proof. Live Cartographer integration remains gated.
Decision: GO.
Next authorized plan: Plan 9/14, Phase 9.1, Increment 9.1.1 only.
Permission request: Ask operator before starting Plan 9/14.

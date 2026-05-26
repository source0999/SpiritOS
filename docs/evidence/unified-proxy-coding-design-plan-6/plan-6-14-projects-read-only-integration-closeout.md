# Plan 6/14: Projects Interface Read-Only Integration

PLAN:
Plan 6/14, Projects Interface Read-Only Integration.

Evidence root:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-6/`

Updated isolated prototype:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html`

Global forbidden actions:
No live Cartographer integration. No project creation. No filesystem scanning outside allowlists. No repo-map refresh writes. No project health mutation. No task execution. No design apply. No provider calls. No production route/component/backend edits. No package install. No git mutation. No Cartographer soak/log/live evidence/runtime/map/source-proxy mutation.

Shared inventory:
- `/home/source/SpiritOS/src/app/v1/cartographer/projects/route.ts` proxies `GET` to `/v1/cartographer/projects`.
- `source_proxy/cartographer/project_discovery.py` supports allowlisted project roots, blocks broad/system/secret-shaped roots, and discovers marker-based projects/candidates.
- `source_proxy/cartographer/project_health.py` builds read-only health records, dirty summaries, blockers, merge readiness, and write policies.
- Related project surfaces include `component_mapper.py`, `git_status.py`, `live_state.py`, and `repo_map.py`.
- Plan 6 uses fixture mode only; no live Cartographer route was called.

Shared checks:
```text
$ grep -En "Project Selector|Project Health|Component Ownership|Project-Scoped Task Context|Design Context Handoff|Live Cartographer Gate|No project creation|No live scan|No live Cartographer call|Soak result required" docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html
670: Project Selector
674: No project creation
675: No live scan
680: Project Health
690: Component Ownership
700: Project-Scoped Task Context
709: Design Context Handoff
718: Live Cartographer Gate
721: Soak result required
722: No live Cartographer call

$ grep -En "fetch\(|XMLHttpRequest|localStorage|indexedDB|navigator\.sendBeacon|serviceWorker|new Worker|Worker\(|/v1/actions|/v1/tasks|/v1/cartographer|discover_projects|build_project_health|repo_map|scan\(|rglob\(|os\.walk|subprocess|write_actions_enabled\s*=\s*true" docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html
695:                  <li>Repo map refresh: disabled until post-soak approval</li>
```

The single grep hit is explanatory blocked-state copy. It is not a route call, import, function call, scan, or write path.

```text
$ node - <<'NODE'
<static assertion script checked 10 required labels and 19 forbidden live/mutation patterns>
NODE
Plan 6 static assertions passed: 10 required project labels present; 19 forbidden live/mutation patterns absent.

$ git -C /home/source/SpiritOS status --short --branch --untracked-files=normal
## main...origin/main
?? docs/evidence/
?? docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md

$ git -C /home/source/SpiritOS diff --name-status
<no output>
```

## Increment 6.1.1

PLAN:
Plan 6/14.

PHASE:
Phase 6.1, Project discovery contract inventory.

INCREMENT:
6.1.1, Inventory existing project routes and Python services.

Objective:
Map project surfaces.

Isolated proxy lane scope:
Read-only route/service inventory.

Allowed files or file zones:
Read-only inspection of `/src/app/v1/cartographer/projects/route.ts` and selected `source_proxy/cartographer` project modules.

Forbidden files, paths, systems, and actions:
Live writes/scans outside allowlist, route calls, Cartographer mutation.

Exact work performed:
Listed project-related Cartographer files and read the project route, project discovery, and project health modules.

Required tests/checks:
Read-only `find` and `sed` commands.

Manual validation performed by Codex:
Project route proxies to Cartographer; Plan 6 did not call it. Python services were inspected only.

Evidence artifact:
This file.

Stop conditions checked:
Write dependency: no.

Rollback or recovery note:
Use fixture mode if live dependency appears.

GO/NO-GO exit:
GO for Increment 6.1.1.

Next authorized increment only:
6.1.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 6.1.2

PLAN:
Plan 6/14.

PHASE:
Phase 6.1.

INCREMENT:
6.1.2, Define read-only project object.

Objective:
Project data contract.

Isolated proxy lane scope:
Fixture schema.

Allowed files or file zones:
Plan 6 evidence and isolated prototype.

Forbidden files, paths, systems, and actions:
Project creation.

Exact work performed:
Defined project fields: id, name, root, health, availability, read/list-only status, blockers, evidence refs.

Required tests/checks:
Schema review.

Manual validation performed by Codex:
Contract does not require project creation or live discovery.

Evidence artifact:
This file.

Stop conditions checked:
Needs live write: no.

Rollback or recovery note:
Blocked state if write needed.

GO/NO-GO exit:
GO for Increment 6.1.2.

Next authorized increment only:
6.1.3.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 6.1.3

PLAN:
Plan 6/14.

PHASE:
Phase 6.1.

INCREMENT:
6.1.3, Define project-health display model.

Objective:
Health model.

Isolated proxy lane scope:
Read-only health fields.

Allowed files or file zones:
Plan 6 evidence/prototype.

Forbidden files, paths, systems, and actions:
Health mutation.

Exact work performed:
Defined health fields: status, dirty summary, branch/upstream optional, blockers, stale flags, write policy, read-only marker.

Required tests/checks:
Model review against `project_health.py`.

Manual validation performed by Codex:
Health card uses fixture status and unknown live flags.

Evidence artifact:
This file.

Stop conditions checked:
Mutation required: no.

Rollback or recovery note:
Unavailable state if live health is needed.

GO/NO-GO exit:
GO for Increment 6.1.3.

Next authorized increment only:
6.1.4.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 6.1.4

PLAN:
Plan 6/14.

PHASE:
Phase 6.1.

INCREMENT:
6.1.4, Define component/path ownership display model.

Objective:
Ownership display.

Isolated proxy lane scope:
Fixture/read-only map.

Allowed files or file zones:
Plan 6 evidence/prototype.

Forbidden files, paths, systems, and actions:
Repo map refresh writes.

Exact work performed:
Defined ownership fields: route owner, component owner, path risk, forbidden zones, repo-map refresh state.

Required tests/checks:
Ownership model review.

Manual validation performed by Codex:
Ownership display is fixture-only and does not refresh repo map.

Evidence artifact:
This file.

Stop conditions checked:
Live map write needed: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 6.1.4.

Next authorized increment only:
6.1.5.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 6.1.5

PLAN:
Plan 6/14.

PHASE:
Phase 6.1.

INCREMENT:
6.1.5, Define workspace root display model.

Objective:
Workspace truth model.

Isolated proxy lane scope:
Read-only root display.

Allowed files or file zones:
Plan 6 evidence/prototype.

Forbidden files, paths, systems, and actions:
Filesystem scanning outside allowlist.

Exact work performed:
Defined root, availability, read/list-only labels, blocked scan labels, and evidence references.

Required tests/checks:
Review against project discovery allowlist rules.

Manual validation performed by Codex:
No broad scan is required for fixture root display.

Evidence artifact:
This file.

Stop conditions checked:
Broad scan needed: no.

Rollback or recovery note:
Unknown state if root cannot be safely displayed.

GO/NO-GO exit:
GO for Increment 6.1.5.

Next authorized increment only:
6.2.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 6.1.1, 6.1.2, 6.1.3, 6.1.4, 6.1.5.
Evidence reviewed: route/service inventory and project/health/ownership/workspace contracts.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Live Cartographer integration remains gated.
Decision: GO.
Next phase or increment: Phase 6.2, Increment 6.2.1.

## Increment 6.2.1

PLAN:
Plan 6/14.

PHASE:
Phase 6.2, Read-only project selector.

INCREMENT:
6.2.1, Add project selector UI in isolated lane.

Objective:
Selector display.

Isolated proxy lane scope:
UI fixture/read-only.

Allowed files or file zones:
`docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html`.

Forbidden files, paths, systems, and actions:
Project creation/live mutation.

Exact work performed:
Added Project Selector card with SpiritOS fixture, no project creation, and no live scan labels.

Required tests/checks:
Static grep and Node assertion.

Manual validation performed by Codex:
Selector is display-only.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Creation/mutation: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 6.2.1.

Next authorized increment only:
6.3.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS; no live integration attempted.

PHASE CLOSEOUT:
Completed increments: 6.2.1.
Evidence reviewed: project selector card.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Selector does not connect to live project route.
Decision: GO.
Next phase or increment: Phase 6.3, Increment 6.3.1.

## Increment 6.3.1

PLAN:
Plan 6/14.

PHASE:
Phase 6.3, Project health display.

INCREMENT:
6.3.1, Add project health card.

Objective:
Health card.

Isolated proxy lane scope:
UI read-only.

Allowed files or file zones:
Prototype fixture data.

Forbidden files, paths, systems, and actions:
Health mutation.

Exact work performed:
Added Project Health card with fixture active status, dirty summary, blockers, and stale flags.

Required tests/checks:
Static grep/Node assertion.

Manual validation performed by Codex:
Health card does not call live health service.

Evidence artifact:
Prototype.

Stop conditions checked:
Mutation: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 6.3.1.

Next authorized increment only:
6.4.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS; no live integration attempted.

PHASE CLOSEOUT:
Completed increments: 6.3.1.
Evidence reviewed: project health card.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Health is fixture display.
Decision: GO.
Next phase or increment: Phase 6.4, Increment 6.4.1.

## Increment 6.4.1

PLAN:
Plan 6/14.

PHASE:
Phase 6.4, Component/path ownership display.

INCREMENT:
6.4.1, Add component ownership card.

Objective:
Ownership card.

Isolated proxy lane scope:
UI read-only fixture.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Map refresh writes.

Exact work performed:
Added Component Ownership card with route/component/path risk and repo-map refresh disabled copy.

Required tests/checks:
Static grep/Node assertion; no live/mutation pattern except explanatory disabled refresh copy.

Manual validation performed by Codex:
Ownership card does not refresh repo map.

Evidence artifact:
Prototype.

Stop conditions checked:
Live write map: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 6.4.1.

Next authorized increment only:
6.5.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS; no live integration attempted.

PHASE CLOSEOUT:
Completed increments: 6.4.1.
Evidence reviewed: component ownership card.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Ownership is fixture-only.
Decision: GO.
Next phase or increment: Phase 6.5, Increment 6.5.1.

## Increment 6.5.1

PLAN:
Plan 6/14.

PHASE:
Phase 6.5, Project-scoped task context.

INCREMENT:
6.5.1, Add project-scoped task context chip.

Objective:
Task/project link display.

Isolated proxy lane scope:
UI-only fixture project context.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Task execution/project mutation.

Exact work performed:
Added Project-Scoped Task Context card with workspace root display and no task execution badge.

Required tests/checks:
Static grep/Node assertion.

Manual validation performed by Codex:
Task context is display-only.

Evidence artifact:
Prototype.

Stop conditions checked:
Live mutation: no.

Rollback or recovery note:
Unavailable state if live context is needed.

GO/NO-GO exit:
GO for Increment 6.5.1.

Next authorized increment only:
6.6.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 6.5.1.
Evidence reviewed: project-scoped task context card.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Context is fixture-only.
Decision: GO.
Next phase or increment: Phase 6.6, Increment 6.6.1.

## Increment 6.6.1

PLAN:
Plan 6/14.

PHASE:
Phase 6.6, Design-system project context handoff.

INCREMENT:
6.6.1, Add design-context handoff display.

Objective:
Project context in design packet.

Isolated proxy lane scope:
UI display fixture.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Design apply/live Cartographer writes.

Exact work performed:
Added Design Context Handoff card with discussion context and no design apply badge.

Required tests/checks:
Static grep/Node assertion.

Manual validation performed by Codex:
Handoff is display-only.

Evidence artifact:
Prototype.

Stop conditions checked:
Write bridge: no.

Rollback or recovery note:
Display-only.

GO/NO-GO exit:
GO for Increment 6.6.1.

Next authorized increment only:
6.6.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 6.6.2

PLAN:
Plan 6/14.

PHASE:
Phase 6.6.

INCREMENT:
6.6.2, Add blocked state for live Cartographer unavailable.

Objective:
Gate live integration.

Isolated proxy lane scope:
UI blocked label.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Probing/mutating live Cartographer.

Exact work performed:
Added Live Cartographer Gate card with soak result required and no live Cartographer call labels.

Required tests/checks:
Static grep/Node assertion; no `/v1/cartographer` route string.

Manual validation performed by Codex:
Live integration is visibly gated.

Evidence artifact:
Prototype.

Stop conditions checked:
Live call needed: no.

Rollback or recovery note:
Blocked state until post-soak approval.

GO/NO-GO exit:
GO for Increment 6.6.2.

Next authorized increment only:
6.7.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 6.6.1, 6.6.2.
Evidence reviewed: design context handoff and live Cartographer gate.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Live project integration remains blocked.
Decision: GO.
Next phase or increment: Phase 6.7, Increment 6.7.1.

## Increment 6.7.1

PLAN:
Plan 6/14.

PHASE:
Phase 6.7, Tests and manual validation.

INCREMENT:
6.7.1, Add tests.

Objective:
Projects tests.

Isolated proxy lane scope:
Ad hoc static Node assertion; no production test file.

Allowed files or file zones:
Read-only prototype input and Plan 6 evidence.

Forbidden files, paths, systems, and actions:
Live Cartographer writes.

Exact work performed:
Ran Node static assertion checking 10 required project labels and 19 forbidden live/mutation patterns.

Required tests/checks:
Node assertion passed.

Manual validation performed by Codex:
No forbidden live/mutation pattern was present. Explanatory disabled refresh copy was reviewed separately.

Evidence artifact:
Shared checks.

Stop conditions checked:
Live mutation: no.

Rollback or recovery note:
Fixture test only.

GO/NO-GO exit:
GO for Increment 6.7.1.

Next authorized increment only:
6.7.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

## Increment 6.7.2

PLAN:
Plan 6/14.

PHASE:
Phase 6.7.

INCREMENT:
6.7.2, Add manual checklist.

Objective:
Manual proof.

Isolated proxy lane scope:
Manual/source review.

Allowed files or file zones:
Plan 6 evidence and prototype source.

Forbidden files, paths, systems, and actions:
Project creation/scan outside allowlist.

Exact work performed:
Reviewed selector, health, ownership, task context, design handoff, live Cartographer gate, no-call proof, status/diff.

Required tests/checks:
Manual checklist by source and terminal output review.

Manual validation performed by Codex:
Controls are clear and read-only; no live mutation or broad scan occurs.

Evidence artifact:
This file.

Stop conditions checked:
Live mutation: no.

Rollback or recovery note:
Block future ambiguous control.

GO/NO-GO exit:
GO for Increment 6.7.2.

Next authorized increment only:
6.8.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 6.7.1, 6.7.2.
Evidence reviewed: Node static assertion and manual checklist.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: No browser screenshot or live route proof captured.
Decision: GO.
Next phase or increment: Phase 6.8, Increment 6.8.1.

## Increment 6.8.1

PLAN:
Plan 6/14.

PHASE:
Phase 6.8, Closeout gate.

INCREMENT:
6.8.1, Closeout gate.

Objective:
Plan 7 readiness.

Isolated proxy lane scope:
Evidence summary only.

Allowed files or file zones:
Plan 6 evidence and isolated prototype.

Forbidden files, paths, systems, and actions:
Live integration.

Exact work performed:
Summarized read-only projects proof and Cartographer gate; ran final status/diff/no-live-pattern checks.

Required tests/checks:
Shared checks above.

Manual validation performed by Codex:
Project UI works as read-only fixture and does not disturb soak.

Evidence artifact:
This file.

Stop conditions checked:
Live dependency unresolved: no; marked gated.

Rollback or recovery note:
Mark gated and stop if live dependency appears.

GO/NO-GO exit:
GO for Increment 6.8.1.

Next authorized increment only:
Plan 7/14, Phase 7.1, Increment 7.1.1 only if operator approves.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 6.8.1.
Evidence reviewed: full Plan 6 packet and prototype checks.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Plan 7 remains unauthorized until operator permission.
Decision: GO.
Next phase or increment: Plan 7/14, Phase 7.1, Increment 7.1.1 only if operator approves.

PLAN 6/14 CLOSEOUT:
Completed phases: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8.
Evidence reviewed: this packet, read-only project/Cartographer inventories, updated isolated prototype, static feature grep, no-live/no-mutation grep, Node assertion, status/diff.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Dirty tree preserved without cleanup: Yes.
Known risks: No browser screenshot or live project route proof was captured; Plan 6 is isolated static prototype evidence, not live Cartographer integration.
Decision: GO.
Next authorized plan: Plan 7/14, Phase 7.1, Increment 7.1.1 only.
Permission request: Ask operator before starting Plan 7/14.

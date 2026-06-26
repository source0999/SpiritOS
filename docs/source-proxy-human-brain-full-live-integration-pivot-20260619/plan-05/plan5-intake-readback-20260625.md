# Plan 5 Intake Readback - 2026-06-25

Status: `PLAN5_INTAKE_READY_FOR_BRITTON_REVIEW`

This packet is intake/readback only. It does not start Plan 5, does not implement Plan 5, does not edit source or tests, and does not authorize Plan 6.

## Purpose

Plan 5/6, `Binary Whole-Brain Acceptance`, is intended to prove that required Source Proxy subsystems are not merely present, advisory, or preview-only. Each approved Plan 5 increment must make one required subsystem honest, traceable, decision-bearing, and consumed by the canonical `/coding` workflow.

Plain language: Plan 5 must prove the live system can use real subsystem output to change task state, operator-visible status, and final verdicts without laundering a preview, fixture, or unconsumed output into a GO.

## Accepted Plan 4 State

- Plan 4 final status: `PLAN4_FINAL_CLOSEOUT_READY_FOR_BRITTON_REVIEW`.
- Plan 4 closed through increment `4.6.2`.
- Plan 4 produced browser, live-route, operator, responsive, accessibility, and closeout proof for canonical `/coding` UI/API consolidation.
- Plan 5/6 was not started during Plan 4.

## GLM Plan 4 Integrity Audit

Accepted GLM verdict: `PLAN4_INTEGRITY_CONFIRMED_WITH_CAVEATS`.

Accepted GLM grade: `90 / 100, A-`.

Blocker/high findings: none.

Medium caveats to carry into Plan 5:

- `F-1`: `/coding` cockpit tests are mostly source-text assertions, not rendered-DOM assertions for every ledger field. Plan 5 must add render-level/operator-surface assertions for key fields such as task id, trace id, reason code, output hash, and authority flags before using cockpit visibility as strong automated proof.
- `F-2`: GLM could not rerun Vitest on the Windows `Z:\` drive root because of Vitest module-resolution failure. Plan 5 must refresh focused tests from `/home/source/SpiritOS` or another non-drive-root path.

## Exact Plan 5 Start Gate

Current Plan 5 status: `PLAN_WRITTEN_NOT_STARTED`.

Current Plan 5 gate: `BLOCKED_PENDING_PLAN_0_COMPRESSION_DECISION`.

Plan 5 may start only after all of the following are true:

1. The Plan 0 compression decision gate is resolved or recorded as no longer blocking.
2. Britton explicitly approves this exact Plan 5/6 plan.
3. The next operator confirms the working tree scope is safe before implementation.

Until then, stop before implementation.

## What Plan 5 Must Prove

For each approved increment, Plan 5 must prove:

- The canonical route is used: `/coding` -> `CodingCockpitShell` -> Next v1 route -> Source Proxy canonical handler, unless Plan 0 records a Britton-approved replacement.
- A real subsystem is invoked and named in the evidence.
- Real upstream task state, current source, and trace identifiers are used.
- The subsystem produces typed output with causal identifiers and status.
- The output is consumed by downstream task state, the phase verifier, and the `/coding` operator surface.
- Success or failure changes a visible route, result, status, state field, or final verdict.
- Invocation event and consumer event appear in one trace.
- Focused checks, JSON validation, operator checks, git status, forbidden-state scans, evidence budget status, and causal identifiers are preserved.

## What Plan 5 Must Not Claim

Plan 5 must not claim GO from:

- Code existing.
- Route existing.
- Schema existing.
- Status text saying available.
- Packet creation.
- Preview success.
- Advisory packet success.
- Fixture/mock success.
- Unconsumed output.
- Skipped lane.
- Backend substitute output.
- Read-only completion for an action-capable system.
- Fake productive GO.

Plan 5 must not claim Plan 6 readiness or daily-driver promotion. That remains Plan 6/6 and requires a separate approval boundary.

## Hard Stops

Stop immediately before implementation or continuation if any of these appear:

- Protected path requirement.
- Credential or auth conflict.
- First Obsidian write.
- First Mac write.
- Authority expansion.
- New framework proposal.
- Missing causal proof.
- Route migration without recorded Plan 0/Britton approval.
- Intentional runtime interruption.
- Irreversible or external action.
- Plan boundary crossing.
- Any need to touch forbidden or unrelated paths.

## Gate Manifest Required Evidence

The Plan 5 gate manifest requires verdict `GO` and these fields:

- `task_id`
- `trace_id`
- `invocation_event_id`
- `consumer_event_id`
- `consumer_subsystem`
- `state_fields_changed`
- `focused_checks`
- `git_status`
- `evidence_budget_status`

The manifest forbids these states:

- `preview_only_completion`
- `advisory_only_completion`
- `read_only_completion_for_action_capable_system`
- `skipped_required_lane`
- `unconsumed_output`
- `fake_productive_go`

## Caveat F-1 Handling

Plan 5 should not rely on source-text assertions alone for `/coding` operator truth. The first implementation increment that touches or relies on `/coding` operator visibility should add render-level/operator-surface assertions for the key proof fields:

- task id
- trace id
- reason code
- output hash
- authority flags
- invocation event id
- consumer event id
- consumer subsystem
- visible route/status/result changes

Recommended test posture: mount or exercise the operator surface at render level, inject controlled runner or route state, and assert visible DOM text/roles for the required fields. Browser proof remains required when operator behavior changes, but automated render assertions should cover the key fields GLM identified.

## Caveat F-2 Handling

Plan 5 focused tests should be refreshed on `/home/source/SpiritOS` or another non-drive-root execution path. Do not treat a failed `Z:\` drive-root Vitest run as a product failure if it reproduces the known module-resolution issue, but do not use that failure as a substitute for a green focused test refresh.

Recommended command posture:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm test -- --run <focused test path>"
```

Record the path, command, and result in the increment packet.

## No-Touch Paths

Do not touch these unless a future approved Plan 5 increment explicitly authorizes the exact path:

- SpiritFlix
- media
- Jellyfin
- Mac optimizer
- Obsidian
- secrets
- env files
- package files
- generated XML packs
- repomixes/
- unrelated dirty files
- Plan 6 files

## Stop Condition Before Implementation

Stop here. This intake packet is not approval to implement Plan 5. The next action is Britton review and explicit approval or correction.

## Recommended First Plan 5 Increment Proposal

Recommended first proposal: start with Increment `5.1.1` only after the Plan 5 start gate is cleared.

Proposed framing for `5.1.1`: build the acceptance harness and validators around one required subsystem, with render-level `/coding` assertions for the causal/operator fields and a focused Linux-path test refresh on `/home/source/SpiritOS`.

No code changes are authorized by this packet.

PLAN5_INTAKE_READY_FOR_BRITTON_REVIEW

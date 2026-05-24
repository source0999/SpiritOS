# Cartographer Live Operation Step 2: Explicit Operator Roadmap

status: documentation-only

Status date: 2026-05-22

## Purpose

This document is the separate explicit operator roadmap required before any Cartographer transition from dry-run readiness toward live operation.

It defines the first future live-operation target as Limited Autonomous Operator v0.1. That target starts with read-only live observation and recommendation only. It is not full auto, not limited unattended operation, not write authority, not command execution authority, and not queue execution authority.

Fail-closed behavior remains mandatory. Missing approval data, stale state, dirty-tree mismatch, self-approval, kill switch activation, forbidden files, forbidden action classes, or ambiguous authority must block the action.

## Source-Of-Truth References

- `docs/cartographer-final-proof-stage-7-autonomy-readiness-score-decision-gate-dry-run-final-closeout.md`
- `docs/cartographer-level-11-to-14-runtime-upgrade-plan.md`
- `docs/cartographer-level-11-to-14-autonomous-operator-roadmap.md`
- `docs/cartographer-level-14-1-through-14-9-autonomy-runtime-dry-run-final-closeout.md`

## Blunt Authority Statement

- This roadmap does not grant full auto.
- Full auto is not granted.
- This roadmap does not grant limited unattended operation.
- limited unattended operation is not granted.
- This roadmap does not grant write authority.
- This roadmap does not grant local command execution.
- This roadmap does not grant queue execution.
- This roadmap does not grant automatic task selection.
- This roadmap does not grant automatic promotion.
- This roadmap does not grant self-approval.

Limited unattended operation is not granted until a future package explicitly implements and proves it. Full auto remains outside the authority of this roadmap.

## First Future Target

Limited Autonomous Operator v0.1 is the first future live-operation target.

Limited Autonomous Operator v0.1 begins at read-only live observation and recommendation only. Its first approved task class must inspect live repo state, compare it to explicit operator policy, and emit recommendations for a human operator. It must not write files, execute queued actions, run local commands through Cartographer, schedule recurring jobs, select tasks automatically, promote itself, approve itself, commit, push, merge, branch, worktree, stash, checkout, clean, delete, or mutate protected lanes.

## Trust Tiers

| Tier | Name | Authority |
| --- | --- | --- |
| Tier 0 | observe/recommend only | Documentation and operator-facing recommendations only. No live reads beyond ordinary repo inspection requested by the operator. No writes, no queue execution, no commands through Cartographer. |
| Tier 1 | read-only live shadow | Read-only live observation against exact allowed files and repo state. May produce recommendations only. No writes, no command execution, no queue execution. |
| Tier 2 | durable queue and event ledger preview | May model queued actions and ledger entries as previews only. No execution. No irreversible effects. No unattended operation. |
| Tier 3 | approval-bound docs/evidence/receipt write | Future only. May write exact approved docs, evidence, or receipt files only after explicit token validation. Must fail closed on any mismatch. |
| Tier 4 | approval-bound verification command execution | Future only. May run exact approved verification commands only after explicit token validation. No broad command execution. No shell expansion beyond the approved command form. |
| Tier 5 | limited unattended low-risk maintenance, future only | Future only. Not granted here. Requires a later package, live shadow soak, operator controls, kill switch proof, rollback proof, audit proof, and explicit approval. |

## Exact Approval Boundaries

Every future action beyond Tier 0 recommendation must require:

- operator id required.
- token id required.
- run id required.
- action type required.
- exact allowed files required.
- exact forbidden files required.
- expiry required.
- rollback required.
- verification required.
- trust tier required.
- current HEAD required.
- expected dirty tree state required.
- kill switch state required.

Blocking rules:

- stale HEAD blocks.
- dirty tree mismatch blocks.
- self-approval blocks.
- kill switch blocks.
- missing operator id blocks.
- missing token id blocks.
- missing run id blocks.
- missing action type blocks.
- missing allowed files blocks.
- missing forbidden files blocks.
- missing expiry blocks.
- missing rollback blocks.
- missing verification blocks.
- expired approval blocks.
- forbidden path match blocks.
- forbidden action class blocks.
- ambiguous authority blocks.
- broader-than-approved file scope blocks.

## Allowed First Live Task Class

The only allowed first live task class is read-only live observation and recommendation only.

Allowed behavior:

- Inspect current repo state when explicitly invoked by the operator.
- Compare state to the approved roadmap and freeze documents.
- Report drift, mismatches, missing approvals, stale HEAD, dirty-tree mismatch, and blocked action classes.
- Recommend the next manual operator action.

Not allowed:

- File writes.
- Evidence writes.
- Receipt writes.
- Queue execution.
- Local command execution through Cartographer.
- Automatic task selection.
- Automatic promotion.
- Background operation.
- Limited unattended operation.
- Full auto.

## Forbidden Classes

- app code writes.
- `/coding` UI mutation.
- Source Proxy stress mutation.
- Scout writes.
- proxy memory writes.
- branch/worktree creation.
- commit/push/merge.
- cleanup/delete/stash/checkout.
- secret/protected path access.
- automatic task selection.
- automatic promotion.
- self-approval.
- generated-file mutation.
- environment-file mutation.
- package-file mutation.
- Next config mutation.
- verifier mutation.
- Codex adapter mutation.
- Cartographer runtime mutation unless a later package explicitly authorizes exact files.
- Cartographer test mutation unless a later package explicitly authorizes exact files.

## Manual Checks

Before any future increment moves beyond documentation:

- Confirm Final Proof Stage 7 still states that full auto is not granted and limited unattended operation is not granted.
- Confirm the operator has named the target trust tier.
- Confirm exact allowed files and exact forbidden files are listed.
- Confirm rollback and verification requirements are specific enough to execute manually.
- Confirm the kill switch behavior is fail-closed.
- Confirm stale HEAD and dirty-tree mismatch behavior is fail-closed.
- Confirm self-approval is impossible.
- Confirm `/coding` UI files remain protected unless a separate `/coding` lane explicitly authorizes them.
- Confirm no unattended operation is implied by queue storage, token storage, or dashboard controls.

## Expected Output

Step 2 produces this explicit operator roadmap only. It defines the authority envelope for future Limited Autonomous Operator v0.1 planning while preserving the Final Proof Stage 7 boundary that full auto and limited unattended operation are not granted.

## Rollback Notes

Rollback is limited to removing this document:

- `docs/cartographer-live-operation-step-2-explicit-operator-roadmap.md`

Removing this document removes the roadmap text. It does not change runtime authority, queue state, tests, protected lanes, git history, branches, worktrees, or generated files.

## Stop Conditions

Stop immediately if:

- Any future step attempts to grant full auto.
- Any future step attempts to grant limited unattended operation before an explicit future package implements and proves it.
- Any future step attempts to grant write authority without exact approved files, token validation, rollback, and verification.
- Any future step attempts local command execution without exact command allowlist and approval-bound verification scope.
- Any future step attempts queue execution before the queue and approval-token package is implemented and proved.
- Any approval omits operator id, token id, run id, action type, exact allowed files, exact forbidden files, expiry, rollback, or verification.
- HEAD is stale.
- The dirty tree does not match the approved expectation.
- The kill switch is active.
- The operator and approver are the same actor.
- A requested path is forbidden or protected.

## Next Recommended Increment

Step 3: Read-Only Live Mode Plan And Runtime Proposal

# Cartographer Live Operation Step 3: Read-Only Live Mode Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document starts Cartographer Live Operation Step 3 as a planning-only lane for read-only live mode.

Step 3 defines how Cartographer may later observe real repo state and produce operator recommendations without gaining write authority, command authority, queue execution authority, approval authority, branch authority, or unattended authority.

This document does not implement live operation. It does not grant limited unattended operation. Full auto is not granted.

## Scope

Step 3 scope is limited to planning the read-only live observation contract for Cartographer.

In this session, scope is docs-only:

- Define read-only live mode.
- Define exact observations that may be allowed later.
- Define exact outputs that may be produced later.
- Define no-write and no-execute boundaries.
- Align Step 3 with the existing trust tier model.
- Prepare the next planning increment without implementing runtime code.

## Non-Scope

This Step 3 planning pass does not:

- Write runtime code.
- Edit `source_proxy/cartographer` runtime modules.
- Edit `source_proxy/tests`.
- Edit `source_proxy/api`.
- Edit `/coding` shell or UI files.
- Implement durable queue or event storage.
- Implement human approval token flow.
- Enable queue execution.
- Enable command execution through Cartographer.
- Enable evidence writes.
- Enable receipt writes.
- Enable live autonomy.
- Grant limited unattended operation.
- Grant full auto.

## Read-Only Live Mode Definition

Read-only live mode means Cartographer can observe exact approved live repo state and produce recommendations for a human operator.

Read-only live mode cannot write files, execute queue items, run commands through Cartographer, mutate state, approve itself, generate approvals, create branches, create worktrees, commit, push, merge, stash, checkout, clean, delete, or touch `/coding` shell or UI implementation files.

Read-only live mode is observation and recommendation only. It does not grant limited unattended operation, and full auto is not granted.

## Why Step 3 Exists Before Durable Queue/Event Storage

Step 3 must come before durable queue and event storage because Cartographer needs a narrow, observable, no-write/no-execute contract before any stored queue or event model exists.

Without Step 3, queue storage could be mistaken for action authority. The read-only observation contract prevents that by establishing that recommendations are inert unless a later step explicitly proves storage, approval, and execution boundaries.

Step 3 can describe future packet shapes and blocked action classes, but it must not create durable state, ledger state, execution state, approval tokens, or any live automation.

## Required Inputs Cartographer May Observe

Future read-only live mode may observe only exact approved inputs. The initial candidate set is:

- Git status summary.
- Current HEAD.
- Changed file list.
- Known Cartographer docs.
- Existing proof closeout docs.
- Existing plan docs.
- Existing test names.
- Existing route names if later needed, read-only only.

Any expansion beyond these inputs requires a later explicit operator approval and must remain read-only.

## Required Outputs Cartographer May Produce

Future read-only live mode may produce operator-facing recommendations only.

Allowed future outputs may include:

- Repo state summary.
- HEAD and dirty-tree comparison against an approved expectation.
- Protected lane drift report.
- Missing approval warning.
- Stale HEAD warning.
- Forbidden action warning.
- Suggested next manual operator action.
- Recommendation packet for human review.

These outputs must be inert. They must not write evidence, receipts, queue entries, event entries, approvals, branches, worktrees, commits, or dashboard state.

## Explicit No-Write/No-Execute Authority Boundary

Step 3 carries an explicit no-write and no-execute boundary.

The following are forbidden:

- File writes.
- Evidence writes.
- Receipt writes.
- Queue execution.
- Local command execution through Cartographer.
- Automatic task selection.
- Approval generation.
- Self-approval.
- Branch/worktree creation.
- Commit/push/merge.
- Stash/checkout/clean/delete.
- `/coding` shell or UI mutation.

If any proposed Step 3 behavior requires one of these actions, it is outside Step 3 and must stop.

## Trust Tier Alignment

Step 3 aligns with Tier 0 to Tier 1 only:

- Tier 0: observe/recommend only. Documentation and operator-facing recommendations only. No writes, queue execution, command execution, or live autonomy.
- Tier 1: read-only live shadow. May observe exact approved live repo state and produce recommendations only. No writes, no command execution, no queue execution, no unattended operation.

Step 3 does not enter Tier 2 durable queue/event preview, Tier 3 approval-bound writes, Tier 4 approval-bound verification command execution, or Tier 5 limited unattended operation.

Limited unattended operation is not granted. Full auto is not granted.

## Proposed Future Runtime Shape

This section is a proposal only and must not be implemented in this session.

Future Step 3 runtime could be shaped as:

- Read-only collector: gathers exact allowed observations without writing files or invoking Cartographer command execution.
- Recommendation packet builder: converts observations into an inert operator review packet.
- Blocked action classifier: labels requested actions as blocked when they require writes, execution, approval generation, self-approval, branch/worktree creation, git mutation, or protected-lane mutation.
- Operator review packet: presents findings and suggested manual next actions without mutating repo state.

No durable queue, event storage, approval token flow, or command runner is introduced here.

## Manual Checks

Before any future Step 3.1 work, an operator should confirm:

- Current HEAD matches the intended planning snapshot.
- Dirty tree state is known and lane-classified.
- `/coding` shell and UI files remain outside the Cartographer lane.
- `source_proxy/cartographer` runtime modules remain untouched by Step 3 planning.
- `source_proxy/tests` remain untouched by Step 3 planning.
- Read-only live mode cannot write files.
- Read-only live mode cannot execute commands through Cartographer.
- Read-only live mode cannot execute queue items.
- Read-only live mode cannot generate or approve its own approvals.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output for this session is this Step 3 plan document plus the companion Step 3 lane boundary and Package A sequencing documents.

No runtime change, test change, UI change, durable storage change, approval-token change, queue execution, command execution, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback for this document is limited to removing:

- `docs/cartographer-live-operation-step-3-read-only-live-mode-plan.md`

Rollback does not require touching runtime modules, tests, `/coding` shell files, `/coding` UI files, branches, worktrees, commits, stashes, or generated files.

## Stop Conditions

Stop immediately if:

- Any Step 3 change would write files outside the allowed docs.
- Any Step 3 change would edit `/coding` shell or UI files.
- Any Step 3 change would edit `source_proxy/cartographer` runtime modules.
- Any Step 3 change would edit `source_proxy/tests`.
- Any Step 3 change would implement queue storage, event storage, approval token flow, command execution, or queue execution.
- Any Step 3 proposal grants limited unattended operation.
- Any Step 3 proposal grants full auto.
- Any command would stage, commit, push, merge, stash, checkout, clean, delete, branch, or create a worktree.
- Read-only live mode is described as having write, execute, approval, or self-approval authority.

## Next Recommended Increment

Step 3.1: Read-Only Live Observation Contract

# Cartographer Live Operation Step 3.1: Read-Only Live Observation Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the Step 3.1 read-only live observation contract for Cartographer.

The contract describes what a future read-only observer may look at, how observations should be shaped for operator review, and which actions remain blocked. It does not implement a collector, command runner, durable queue, event store, approval token flow, dashboard change, or live autonomy.

Limited unattended operation is not granted. Full auto is not granted.

## Contract Summary

Read-only live observation is a narrow operator-invoked review mode.

It may inspect exact allowed repo state and produce an inert observation summary for a human operator. It may not write files, mutate state, execute queue items, run commands through Cartographer, create approvals, approve itself, create branches, create worktrees, commit, push, merge, stash, checkout, clean, delete, or touch `/coding` shell or UI implementation files.

## Preconditions

A future read-only observer must fail closed unless all of these are true:

- The operator explicitly invokes the observation.
- The requested trust tier is Tier 0 or Tier 1.
- The requested observation sources are all listed in the allowed observation sources.
- The current HEAD is captured as data, not changed.
- Dirty tree state is captured as data, not changed.
- `/coding` shell and UI work remains protected.
- `source_proxy/cartographer` runtime modules remain protected unless a later implementation package explicitly authorizes exact files.
- `source_proxy/tests` remain protected unless a later implementation package explicitly authorizes exact files.
- The requested output is an operator-facing recommendation or observation packet only.

## Allowed Observation Sources

The initial allowed observation sources are:

- Git status summary.
- Current HEAD.
- Changed file list.
- Known Cartographer live-operation docs.
- Existing Cartographer proof closeout docs.
- Existing Cartographer plan docs.
- Existing Cartographer test names.
- Existing route names if later needed, read-only only.

These sources are observation inputs only. They do not grant authority to write, execute, approve, queue, branch, commit, or mutate protected lanes.

## Forbidden Observation Sources

The observer must not read or depend on:

- Environment files.
- Secrets.
- Generated files.
- Scout write paths or soak logs unless separately approved for read-only review.
- Proxy memory write paths.
- Package files unless separately approved for read-only review.
- Config files unless separately approved for read-only review.
- `/coding` implementation content beyond path-level lane detection.
- Dashboard component content beyond path-level lane detection.

If an observation request requires a forbidden source, the result must be blocked.

## Observation Packet Shape

A future observation packet may contain:

- `status_date`.
- `head`.
- `branch_summary`.
- `dirty_tree_summary`.
- `changed_file_list`.
- `allowed_sources_observed`.
- `forbidden_sources_blocked`.
- `protected_lane_matches`.
- `trust_tier`.
- `blocked_action_classes`.
- `recommendations`.
- `operator_next_step`.

This packet is conceptual only. Step 3.1 does not create a runtime packet type, write JSON, write evidence, write receipts, create event storage, or persist state.

## Recommendation Rules

Recommendations must be inert and human-facing.

Allowed recommendations include:

- Report stale HEAD risk.
- Report dirty-tree mismatch risk.
- Report protected lane drift.
- Report missing approval scope.
- Report forbidden action classes.
- Recommend manual operator review.
- Recommend stopping before a later implementation step.

Recommendations must not:

- Select tasks automatically.
- Generate approvals.
- Approve actions.
- Execute queue items.
- Run commands through Cartographer.
- Write files.
- Mutate dashboard UI.
- Mutate `/coding` shell or UI files.
- Mutate runtime modules or tests.

## No-Write/No-Execute Boundary

Step 3.1 preserves the Step 3 no-write/no-execute boundary.

Forbidden actions include:

- File writes.
- Evidence writes.
- Receipt writes.
- Durable queue writes.
- Event storage writes.
- Queue execution.
- Local command execution through Cartographer.
- Automatic task selection.
- Approval generation.
- Self-approval.
- Branch/worktree creation.
- Commit/push/merge.
- Stash/checkout/clean/delete.
- `/coding` shell or UI mutation.
- `source_proxy/cartographer` runtime mutation.
- `source_proxy/tests` mutation.

## Trust Tier Alignment

Step 3.1 stays within Tier 0 to Tier 1:

- Tier 0: documentation and operator-facing recommendation planning.
- Tier 1: future read-only live shadow observation, recommendations only.

Step 3.1 does not enter:

- Tier 2 durable queue/event preview.
- Tier 3 approval-bound writes.
- Tier 4 approval-bound verification command execution.
- Tier 5 limited unattended operation.

Limited unattended operation is not granted. Full auto is not granted.

## Manual Checks

After Step 3.1, manually verify:

- `git diff --check` passes.
- The Step 3.1 doc exists.
- Step 3.1 says observation is read-only and recommendation-only.
- Step 3.1 lists allowed observation sources.
- Step 3.1 lists forbidden observation sources.
- Step 3.1 blocks file writes, queue execution, command execution through Cartographer, approval generation, self-approval, git mutation, runtime mutation, test mutation, and `/coding` mutation.
- `/coding` shell and UI files were not edited by Step 3.1.
- `source_proxy/cartographer` runtime files were not edited by Step 3.1.
- `source_proxy/tests` files were not edited by Step 3.1.
- No durable queue/event storage was implemented.
- No human approval token flow was implemented.
- No limited unattended operation or full auto was granted.

## Expected Output

Expected output is this Step 3.1 read-only live observation contract and the tiny lane-boundary update that recognizes it as part of the docs-only Cartographer lane.

No runtime code, tests, `/coding` UI changes, durable storage, approval token flow, queue execution, command execution, live autonomy, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback for Step 3.1 is limited to removing:

- `docs/cartographer-live-operation-step-3-1-read-only-live-observation-contract.md`

If the companion lane-boundary index line is removed, do not touch unrelated `/coding`, runtime, test, package, config, generated, Scout, dashboard, branch, worktree, commit, stash, or dirty files.

## Stop Conditions

Stop immediately if:

- Step 3.1 attempts to implement runtime code.
- Step 3.1 attempts to implement durable queue/event storage.
- Step 3.1 attempts to implement human approval token flow.
- Step 3.1 grants write authority, command authority, queue execution authority, approval authority, self-approval, limited unattended operation, or full auto.
- Step 3.1 touches `/coding` shell or UI files.
- Step 3.1 touches `source_proxy/cartographer` runtime modules.
- Step 3.1 touches `source_proxy/tests`.
- Any git mutation would be required to continue.

## Next Recommended Increment

Step 3.2: Read-Only Recommendation Packet Schema

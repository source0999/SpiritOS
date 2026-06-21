# Codex Plan 2 Patch 3 Acceptance Review

Verdict: NEEDS_FIX

Reviewed commit: 1b27661d Finish Plan 2 live Mac and specialist integration

Review mode: independent acceptance review, no implementation.

## Decision

This review does not accept Patch 3 as true Plan 2 GO.

The Mac and research proofs are strong enough for Plan 2 Patch 3. The blocker is the specialist/model lane. Gemma and Hermes appear live and consumed, but the claimed specialist integration also relies on:

- Qwen coder not activated
- verifier lane advisory/preview-only
- verifier verdict UNVERIFIED
- operator/closeout checks that still allow that proof shape to appear as INTEGRATED_LIVE

Under the review prompt, advisory-only, preview-only, status-only, metadata-only, and unverified verifier states cannot become GO.

## Component Verdicts

- Mac write/action integration: PASS
- Mac search/check integration: PASS
- Research integration: PASS
- Specialist/model lane integration: NEEDS_FIX
- Task A: NEEDS_FIX
- Task B: PASS
- Task C: PASS
- Operator check: PASS but insufficiently strict
- Focused tests: PARTIAL
- Plan 3 readiness: NOT READY

## Evidence Highlights

Operator passed and did not detect Plan 3 start.

Python focused tests passed: 192 passed, 1360 deselected, 287 subtests passed.

Typecheck passed.

Mac worker route/contract Vitest tests passed.

Coding cockpit Vitest target still failed 9 Trial Runner/current-shell tests, although the Plan 2 truth-visibility test in that file passed.

Read-only task trace checks confirmed consumer_event_id values for the reviewed Mac, research, and specialist representative tasks.

## Required Fixes

1. Make specialist INTEGRATED_LIVE impossible when verifier output is advisory, preview-only, or UNVERIFIED.
2. Either produce real live Qwen coder and browser/functional verifier invocation/consumption/failure-changing proof, or remove those lanes from the required Plan 2 GO standard.
3. Harden the operator and closeout JSON validation to reject the above fake-GO states.
4. Make focused test reporting honest: PASS only for fully passing requested focused targets, or provide a machine-checkable exemption for carried failures.

## Safety Notes

This review did not patch source, stage, commit, push, start Plan 3, mutate media/Jellyfin, or edit/sync Mac worker files.

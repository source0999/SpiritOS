# Increment 4.3.2 Control Contract - 2026-06-25

Status: `INCREMENT_4_3_2_GO`

## Plan Expectation

Increment 4.3.2 completes Phase 4.3 by making approval/edit/reject/resume/cancel/kill controls preserve typed, reviewable control state in the canonical `/coding` operator workflow.

The increment must keep `/coding` honest: no hidden apply, no commit, no push, no OS process kill, no preview-only GO, and no backend substitute. Route-backed controls must show their route and resulting status.

## Implemented Behavior

`/coding` now includes a Plan 4.3 `Control contract` ledger and copied diagnostics line with:

- `backend_run_id`
- `task_id`
- `trace_id`
- `invocation_event_id`
- `output_hash`
- `control_status`
- `control_route`
- `resume_from_prompt`
- `backend_sync_status`
- `interruption_source`

The stale local trial cleanup guard now preserves resumable interrupted suites. A user-stopped or browser-interrupted suite with remaining prompts is no longer cleared merely because the cloud run is synced and Agent Lab baseline is clean.

This is a bounded 4.3 adjustment: it does not add a new worker, parallel state engine, package dependency, apply mechanism, commit action, push action, OS process kill action, or protected path access.

## Focused Tests

```text
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'renders the Plan 4.3 operator control ledger without hidden apply authority|classifies clean cloud plus active null as stale local trial state instead of cleanup blocker'
```

Result:

```text
PASS - 2 passed, 36 skipped
```

## Browser / Operator Proof

Browser/operator proof used standalone Playwright route interception against the existing Dell Next dev server:

```text
https://10.0.0.186:3000/coding
```

The proof injected a running durable suite with one completed prompt through `/v1/coding/runs/active`, verified route-backed stop state, clicked `Stop suite now`, intercepted one `PATCH /v1/coding/runs/[runId]`, returned a cancelled `user_stop` run, and verified resume state remained visible.

Visible before-stop proof showed:

- `backend_run_id=run-plan4-432-stop-resume-control`
- `route_backed_suite_stop=/v1/coding/runs/[runId]`
- `stop_or_kill=available_as_reviewable_stop`

Visible after-stop proof showed:

- `resume=available_from_prompt_2`
- `resume_from_prompt=2`
- `interruption_source=user_stop`
- `commit=false`
- `push=false`
- `os_process_kill=false`
- no apply-success sentence

Proof artifacts:

```text
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-browser-proof-20260625.md
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-browser-proof-20260625.json
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-browser-proof-before-stop-20260625.png
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-browser-proof-20260625.png
```

## Verdict

Increment 4.3.2 is `GO`.

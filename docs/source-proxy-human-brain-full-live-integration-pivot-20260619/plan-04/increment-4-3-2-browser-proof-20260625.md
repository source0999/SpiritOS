# Increment 4.3.2 Browser / Operator Proof - 2026-06-25

Status: `INCREMENT_4_3_2_GO`

## Target

```text
https://10.0.0.186:3000/coding
```

## Command

```text
node_repl standalone Playwright chromium with route interception against /coding durable run controls
```

## Injection

Playwright fulfilled canonical browser requests for:

- `/v1/coding/runs/active`
- `/v1/coding/runs/[runId]`
- `/v1/coding/agent-lab-baseline`
- `/v1/coding/trial-fixture-baseline`
- `/v1/coding/trial-receipt-reconcile`

The injected active run was a running durable suite:

```text
run_id: run-plan4-432-stop-resume-control
suite_id: suite-plan4-432-stop-resume-control
status: running
completed_count: 1
requested_count: 10
current_prompt_id: coder-002-add-product-data
```

The proof clicked `Stop suite now`. Playwright observed exactly one `PATCH /v1/coding/runs/[runId]` and returned a cancelled run:

```text
status: cancelled
reason_code: user_stop
final_summary: Stopped by user
```

## Visible Assertions

Before stop, the browser artifact shows:

- `backend_run_id=run-plan4-432-stop-resume-control`
- `route_backed_suite_stop=/v1/coding/runs/[runId]`
- `stop_or_kill=available_as_reviewable_stop`

After stop, the browser artifact shows:

- `resume=available_from_prompt_2`
- `resume_from_prompt=2`
- `interruption_source=user_stop`
- `commit=false`
- `push=false`
- `os_process_kill=false`
- no apply-success sentence

## Artifacts

```text
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-browser-proof-20260625.json
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-browser-proof-before-stop-20260625.png
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-browser-proof-20260625.png
```

## Verdict

Increment 4.3.2 browser/operator proof is `GO`.

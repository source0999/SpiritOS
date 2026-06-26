# Increment 4.5.1 Browser Proof - 2026-06-25

Status: `PASS_BROWSER_OPERATOR_PLAN_4_5_1_API_LEDGER_VISIBLE`

## Target

`https://10.0.0.186:3000/coding`

## Command

```text
node_repl standalone Playwright chromium with installed Chrome executable and minimal page.route interception against /coding
```

Input path: operator-style textarea click and keyboard typing after hydration, then visible `Start coding` button click.

## Injection

Playwright route interception supplied controlled responses for:

- `/v1/coding/runs/active`;
- `/v1/coding/runs/recent`;
- `/v1/tasks/long-running`;
- `/v1/decisions/prompt-packet`;
- `/v1/verification/diff-preview`;
- `/v1/actions/execute-approved`.

`/v1/actions/execute-approved` returned HTTP `502` with causal fields for:

- `task_id=task-plan4-451-api-ledger`;
- `trace_id=trace-plan4-451-api-ledger`;
- `invocation_event_id=invocation-plan4-451-api-ledger`;
- `consumer_event_id=consumer-plan4-451-api-ledger`;
- `consumer_subsystem=coding_operator_plan_4_5_api_consolidation_ledger`;
- `output_hash=sha256:plan4-451-api-ledger`;
- `reason_code=plan4_451_api_route_contract_blocked`;
- `status_after=execute_approved_failed_closed_api_route_preserved`.

## Assertions

All JSON assertions passed:

- Plan 4.5 API ledger visible.
- Canonical route sequence visible.
- Supporting routes visible.
- Dormant parallel routes visible.
- `/v1/decisions/prompt-packet` visible and invoked.
- `/v1/verification/diff-preview` visible and invoked.
- `/v1/actions/execute-approved` visible and invoked.
- `/v1/coding/codex` visible as dormant and not invoked.
- `/v1/coding/bounded-diff-preview` visible as dormant and not invoked.
- `/v1/coding/research-preview` visible as dormant and not invoked.
- `/v1/coding/helper-agents/preview` visible as dormant and not invoked.
- Task id, trace id, consumer event, consumer subsystem, and output hash visible.
- No apply success displayed.
- No Plan 4.5 GO wording appeared in the app.

## Artifacts

- JSON/DOM proof: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-5-1-browser-proof-20260625.json`
- Screenshot: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-5-1-browser-proof-20260625.png`

Screenshot readability check: the PNG was visually inspected and was readable, though very tall. DOM/JSON proof remains authoritative.

## Verdict

Browser/operator proof passed without fake apply success or dormant-route laundering.

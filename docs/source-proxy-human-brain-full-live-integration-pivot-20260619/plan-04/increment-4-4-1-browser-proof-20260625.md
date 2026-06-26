# Increment 4.4.1 Browser Proof - 2026-06-25

Status: `PASS_BROWSER_OPERATOR_PLAN_4_4_1_TRUTH_LEDGER_VISIBLE`

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

`/v1/actions/execute-approved` returned HTTP `502` with:

- `task_id=task-plan4-441-truth-ledger`;
- `trace_id=trace-plan4-441-truth-ledger`;
- `invocation_event_id=invocation-plan4-441-truth-ledger`;
- `consumer_event_id=consumer-plan4-441-truth-ledger`;
- `consumer_subsystem=coding_operator_plan_4_4_truth_ledger`;
- `output_hash=sha256:plan4-441-truth-ledger`;
- `reason_code=plan4_441_productive_truth_apply_blocked`;
- `route=/v1/actions/execute-approved`;
- `status_after=execute_approved_failed_closed_truth_preserved`.

## Assertions

All JSON assertions passed:

- Plan 4.4 truth ledger visible.
- Memory/research visible.
- Assignment/verifier visible.
- Repair/productive truth visible.
- Task id visible.
- Trace id visible.
- Invocation event visible.
- Consumer event visible.
- Consumer subsystem visible.
- Output hash visible.
- Reason code visible.
- Route visible.
- Verifier evidence visible.
- Productive truth was not displayed as apply success.
- No apply success displayed.
- Execute-approved attempted exactly once.
- No Plan 4.4 GO wording appeared in the app.

## Artifacts

- JSON/DOM proof: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-4-1-browser-proof-20260625.json`
- Screenshot: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-4-1-browser-proof-20260625.png`

Screenshot readability check: the PNG was visually inspected and was readable, though very tall. The JSON/DOM excerpts remain the authoritative readable proof artifact.

## Verdict

Browser/operator proof passed without fake apply success.

# Plan 5 Increment 5.2.1 - Central Gate Resolution Analysis

Status: `BLOCKED_REQUIRES_HUMAN_GATE_DECISION`.

## Question

Can Plan 5 increment `5.2.1` satisfy the existing Source Proxy central apply gate without bypassing it, silently expanding authority, or faking GO?

## Finding

No. The current live Source Proxy central gate is intentionally closed for apply.

The implementation in `source_proxy/approval/external_gate.py` requires all of the following before `central_gate_check("apply")` can pass:

- gate state status is `APPROVED_INCREMENT` or `RUNNING_INCREMENT`
- `approved_increment` matches the requested/default increment
- `approval_token` is present
- requested action is allowed by `SOURCE_PROXY_GATE_ALLOWED_ACTIONS`

When no increment is passed, `central_gate_check` uses `SOURCE_PROXY_GATE_INCREMENT`, or defaults to `1.3`.

The live Source Proxy process did not expose a `SOURCE_PROXY_GATE_ALLOWED_ACTIONS` entry that includes `apply`.

The live `.gate/state.json` says:

```json
{
  "status": "RUNNING_INCREMENT",
  "approved_increment": "evaluation-round",
  "last_completed_increment": "2.4",
  "approval_token": "evaluation-round:temporary-model-call-eval",
  "updated_at": "2026-06-09T01:51:51.277Z",
  "notes": "Temporary model_call approval for messy prompt evaluation; no apply approval."
}
```

That gate state is not a Plan 5 apply approval. Its note explicitly excludes apply approval.

## Prior Live Proof

Existing proof artifact:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-05/increment-5-2-1-live-acceptance-proof-20260625.json`

The live HTTPS route proof showed:

- Next route used: `https://127.0.0.1:3000/v1/actions/execute-approved`
- Source Proxy route reached: `https://127.0.0.1:8787/v1/tasks/long-running/{task_id}/execute-approved`
- task id present
- trace id present
- invocation event id present
- consumer event id present
- consumer subsystem present
- downstream readback consumed the failure
- task status changed to `failed_needs_human`

The proof did not show productive apply success. The target file remained at:

```text
PLAN5_5_2_1_LIVE_ACCEPTANCE_TARGET=before
```

## Outcome Classification

Outcome B applies.

Central gate requires a human authority decision. Codex must not patch around it, must not bypass it, and must not mark 5.2.1 GO.

## Required Human Decision

Britton must decide whether to grant a Plan 5 apply gate for the bounded 5.2.1 proof.

The minimum existing central-gate mechanism would need a live gate configuration equivalent to:

- `approved_increment`: a Plan 5 increment identifier approved by Britton, such as `5.2.1`
- `approval_token`: a non-empty Britton-approved token for that increment
- `SOURCE_PROXY_GATE_INCREMENT`: matching the approved increment if the runtime does not pass it explicitly
- `SOURCE_PROXY_GATE_ALLOWED_ACTIONS`: includes `apply`

This is an authority decision, not a code bug. Changing it without Britton approval would be authority expansion.

## Rejected Paths

- Do not bypass `central_gate_check`.
- Do not set `SOURCE_PROXY_GATE_ALLOWED_ACTIONS=apply` without Britton approval.
- Do not rewrite `.gate/state.json` to Plan 5 apply approval without Britton approval.
- Do not mark 5.2.1 GO from the fail-closed proof.
- Do not claim the route applied the diff.
- Do not start Plan 6.

## Current Verdict

Increment `5.2.1` remains:

`PROOF_BLOCKED_BY_CENTRAL_GATE`

Plan 5 status remains:

`PLAN5_INCREMENT_5_2_1_PROOF_BLOCKED_BY_CENTRAL_GATE`

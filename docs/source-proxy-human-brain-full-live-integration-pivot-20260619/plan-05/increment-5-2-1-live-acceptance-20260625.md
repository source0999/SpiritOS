# Plan 5 Increment 5.2.1 - Live Acceptance Case

Status: `PROOF_BLOCKED`.

## Plan Expectation

Increment `5.2.1` starts Phase 5.2 live acceptance cases. It requires a live canonical route proof that a required subsystem is real, traceable, decision-bearing, and consumed downstream. The live proof must not be preview-only, advisory-only, fixture-only, unconsumed, or fake productive GO.

The canonical route expectation is:

`/coding` -> `/v1/actions/execute-approved` -> Source Proxy `/v1/tasks/long-running/{task_id}/execute-approved`

## Attempted Live Proof

Proof artifact:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-05/increment-5-2-1-live-acceptance-proof-20260625.json`

Live proof target:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-05/live-acceptance-target-20260625.txt`

The live stack was reachable over HTTPS:

- `https://127.0.0.1:3000/coding`
- `https://127.0.0.1:8787/v1/self/status`

HTTP on those ports returned empty replies because the active stack is HTTPS-only.

A safe nonexistent-task probe against the live Next route returned Source Proxy `not_found`, proving the Next route forwards to Source Proxy without mutating files:

```text
https://127.0.0.1:3000/v1/actions/execute-approved -> 422 not_found
```

A bounded live acceptance attempt then created a real long-running task and sent an approved diff through:

```text
https://127.0.0.1:3000/v1/actions/execute-approved
```

The approved diff targeted only the Plan 5 live proof target listed above.

## Result

The live route entered Source Proxy and recorded causal evidence, but Source Proxy `central_gate_check("apply")` blocked apply before workspace mutation. The live target still contains:

```text
PLAN5_5_2_1_LIVE_ACCEPTANCE_TARGET=before
```

Task readback proves:

- task id present
- trace id present
- invocation event id present
- consumer event id present
- consumer subsystem present
- downstream status readback consumed the failure
- final task status changed to `failed_needs_human`

No apply success was claimed. No commit or push authority was used.

## Blocker

`central_gate_blocked_apply`

Bypassing or expanding Source Proxy apply authority would be an authority expansion and is outside the approved Plan 5 scope. Therefore increment `5.2.1` is not GO.

## Self-Check Against Plan 5

- Live route used: yes, HTTPS Next route.
- Source Proxy invoked: yes.
- Required causal fields present: yes, on task readback.
- Output/status consumed downstream: yes, by `long_running_status_observer`.
- Failure changed state/verdict: yes, `failed_needs_human`.
- Productive apply proven: no.
- GO claimed: no.
- Forbidden paths touched: no.
- Plan 6 started: no.

## Verdict

Increment `5.2.1`: `PROOF_BLOCKED_BY_CENTRAL_GATE`.

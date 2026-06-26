# Plan 5 Increment 5.2.2 - Live Fail-Closed Acceptance

Status: `GO`.

## Plan Expectation

Increment `5.2.2` completes Phase 5.2 live acceptance cases. Plan 5 requires the subsystem output to be real, traceable, decision-bearing, and consumed downstream by canonical task state, the Plan 5 phase verifier, and the `/coding` operator surface.

The plan does not explicitly require a productive apply for `5.2.2`. Because increment `5.2.1` already proved the productive apply path with a scoped runtime gate, `5.2.2` was executed as the complementary fail-closed live acceptance case under the restored non-apply runtime.

## Scoped Apply Gate Decision

Scoped apply gate required: `false`.

Reason: `5.2.2` was satisfied by proving the canonical action route fails closed under the restored non-apply gate, preserves workspace state, emits causal evidence, and has the blocked output consumed downstream. No Source Proxy restart or apply gate was opened.

Runtime before proof:

```text
Source Proxy listener: https://127.0.0.1:8787
Next listener: https://127.0.0.1:3000
Source Proxy environment: SPIRIT_PROJECT_PATH=<set>; no SOURCE_PROXY_GATE_INCREMENT; no SOURCE_PROXY_GATE_ALLOWED_ACTIONS
Gate approved increment: evaluation-round
Gate notes: Temporary model_call approval for messy prompt evaluation; no apply approval.
```

## Canonical Live Proof

Target route:

```text
https://127.0.0.1:3000/v1/actions/execute-approved
```

Source Proxy route reached by Next:

```text
https://127.0.0.1:8787/v1/tasks/long-running/{task_id}/execute-approved
```

Harmless proof target:

```text
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-05/live-fail-closed-target-20260626.txt
```

The approved diff would have created that proof target with:

```text
PLAN5_5_2_2_FAIL_CLOSED_TARGET=should-not-be-created
```

Expected outcome: the file must not be created because the restored runtime has no apply authority.

Actual live result:

```text
HTTP status: 500
Task id: task_341690acc102
Trace id: trace_c620c54ee2454a05
Initial invocation event id: invocation_f4937f634871484b
Initial failure event id: failure_6580fc7ac1a1464c
Initial consumer event id: consumer_0b483a06d6c24261
Final task status: failed_needs_human
Target mutated: false
```

The proof target did not exist before the route call and did not exist after the route call.

## Downstream Consumption

The blocked execute-approved output was then recorded as consumed by the operator surface and the Plan 5 phase verifier on the same trace.

Operator consumption:

```text
Subsystem: source_proxy_execute_approved_fail_closed
Consumer subsystem: coding_operator_surface
Consumer event id: consumer_4f83c573a55e485e
Accepted output hash: 775afd12eab0aa23f52f5ff25ac00b6dd6995cf14f266c7b93a5a6759771eec2
Changed state fields:
- ast_snapshot.plan_5_acceptance.source_proxy_execute_approved_fail_closed
- status
```

Phase verifier consumption:

```text
Subsystem: plan5_phase_verifier
Consumer subsystem: plan5_phase_acceptance_consumer
Phase verifier invocation event id: invocation_3549e2348d13475d
Phase verifier consumer event id: consumer_4498f2160a8444a2
Accepted output hash input: 775afd12eab0aa23f52f5ff25ac00b6dd6995cf14f266c7b93a5a6759771eec2
Changed state fields:
- ast_snapshot.plan_5_acceptance.phase_verifier
- status
```

Plan 5 phase gate:

```text
Status: GO
Failures: []
Output consumed by operator: true
Output consumed by phase verifier: true
Same trace: true
Forbidden states: []
```

Raw local runtime artifact:

```text
/tmp/plan5-522-runtime/live-fail-closed-proof-success.json
```

## Self-Check Against Plan 5

- Live canonical route used: yes.
- Source Proxy canonical handler invoked: yes.
- Real output produced: yes, a central-gate blocked apply decision with causal failure/readback events.
- Output consumed downstream: yes, by `coding_operator_surface` and `plan5_phase_acceptance_consumer`.
- Required fields present: task id, trace id, invocation event id, consumer event id, consumer subsystem, state fields changed, focused checks, git status, evidence budget status.
- Operator-visible difference: yes, route/status/result changed to fail-closed instead of apply success.
- No preview-only, advisory-only, fixture-only, unconsumed, or fake productive GO.
- No read-only completion for an action-capable system: this was live route execution, not advisory inspection.
- Scoped apply gate opened: no.
- Workspace mutation: none.
- Plan 6 started: no.

## Verdict

Increment `5.2.2`: `GO`.

# Plan 4/6 Next-Plan Handoff

Previous plan required deliverables are listed in plan.md. Inputs required by the next plan are the final verdict, status JSON, causal trace evidence, Codex review, operator check result, evidence budget status, and Britton approval.

## Current Plan 4 State - 2026-06-25

Status: `PLAN4_INCREMENT_4_2_2_GO`

Increment 4.1.1 has a focused code guard in `/v1/actions/execute-approved`: a successful Source Proxy apply response must include `task_id`, `trace_id`, `invocation_event_id`, `consumer_event_id`, and `consumer_subsystem`, or the route returns `plan4_execute_approved_contract_missing` instead of a false success.

Focused check passed on `/home/source/SpiritOS`:

```text
npm test -- --run src/app/v1/actions/execute-approved/__tests__/route.test.ts
10 tests passed
```

Live canonical-route proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-1-1-live-proof-20260625.md`

Proof summary:

- HTTP route accepted a successful apply-like response containing `task_id`, `trace_id`, `invocation_event_id`, `consumer_event_id`, and `consumer_subsystem`.
- HTTP route rejected an apply-like HTTP 200 response missing those fields with `502` and `reason_code: plan4_execute_approved_contract_missing`.
- The proof used a temporary Source Proxy stub and did not perform real filesystem apply.

Increment 4.1.1 verdict: `GO`.

Increment 4.1.2 is code-ready and recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-1-2-operator-surface-20260625.md`

4.1.2 implemented change:

- `/coding` approved-apply failure handling now preserves the `/v1/actions/execute-approved` fail-closed reason code, route, technical payload summary, and failed task event on the operator surface.

Focused 4.1.2 check:

```text
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'preserves execute-approved causal contract failures on the operator surface'
1 targeted test passed
```

Browser/operator proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-1-2-browser-proof-20260625.md`

Proof summary:

- `/coding` was loaded from the existing Dell Next dev server at `https://10.0.0.186:3000/coding`.
- Playwright route interception fulfilled `/v1/actions/execute-approved` with an HTTP `502` fail-closed payload.
- The visible operator surface preserved the reason code, route, task id, technical detail, and failed event.
- No apply success was displayed.

Increment 4.1.2 verdict: `GO`.

Increment 4.2.1 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-2-1-operator-ledger-20260625.md`

4.2.1 implemented change:

- `/coding` displays a Plan 4.2 operator ledger derived from existing runner state: brain-stage timeline, task ledger, progress ledger, specialists, and workers.
- Copied diagnostics include `plan_4_2_operator_ledger`.
- The implementation does not introduce a new worker, parallel state engine, package dependency, or backend substitute.

Focused 4.2.1 check:

```text
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'renders the Plan 4.2 brain-stage and worker ledger without fake GO wording'
1 targeted test passed
```

Browser/operator proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-2-1-browser-proof-20260625.md`

Proof summary:

- `/coding` was loaded from the existing Dell Next dev server at `https://10.0.0.186:3000/coding`.
- Playwright route interception exercised `/v1/decisions/prompt-packet`, `/v1/verification/diff-preview`, and `/v1/actions/execute-approved`.
- The visible operator ledger preserved failed state, task id, route, target, provider/model, progress ledger, and worker status.
- No apply success was displayed.

Increment 4.2.1 verdict: `GO`.

Increment 4.2.2 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-2-2-output-contract-ledger-20260625.md`

4.2.2 implemented change:

- `/coding` preserves the typed Plan 4 output contract in the visible Plan 4.2 ledger and copied diagnostics.
- The output contract includes task id, trace id, invocation event id, consumer event id, consumer subsystem, output hash, and status.
- Fail-closed execute-approved responses preserve those fields when the payload provides them.

Focused 4.2.2 check:

```text
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'reads output hashes from execute-approved payloads|renders the Plan 4.2 brain-stage and worker ledger without fake GO wording'
2 targeted tests passed
```

Browser/operator proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-2-2-browser-proof-20260625.md`

Proof summary:

- `/coding` was loaded from the existing Dell Next dev server at `https://10.0.0.186:3000/coding`.
- Playwright route interception exercised `/v1/decisions/prompt-packet`, `/v1/verification/diff-preview`, and `/v1/actions/execute-approved`.
- The visible output-contract ledger preserved task id, trace id, invocation event id, consumer event id, consumer subsystem, output hash, and status.
- Copied diagnostics preserved the same `output_contract`.
- No apply success was displayed.

Phase 4.2 closeout review:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/phase-4-2-closeout-review-20260625.md`

Increment 4.2.2 verdict: `GO`.

Next incomplete Plan 4 increment: `4.3.1`.

Do not start Plan 5/6.

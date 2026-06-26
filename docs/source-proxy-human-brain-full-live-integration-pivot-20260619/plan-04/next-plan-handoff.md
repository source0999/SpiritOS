# Plan 4/6 Next-Plan Handoff

Previous plan required deliverables are listed in plan.md. Inputs required by the next plan are the final verdict, status JSON, causal trace evidence, Codex review, operator check result, evidence budget status, and Britton approval.

## Current Plan 4 State - 2026-06-25

Status: `PLAN4_FINAL_CLOSEOUT_READY_FOR_BRITTON_REVIEW`

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

Increment 4.3.1 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-1-operator-controls-20260625.md`

4.3.1 implemented change:

- `/coding` displays a Plan 4.3 operator control ledger for edit, approve, reject, apply, cancel, resume, and stop/kill controls.
- Control authority explicitly preserves `apply_without_approval=false`, `commit=false`, `push=false`, and `os_process_kill=false`.
- Reject and cancel controls now leave reviewable operator state instead of silent local-only transitions.

Focused 4.3.1 check:

```text
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'renders the Plan 4.3 operator control ledger without hidden apply authority'
1 targeted test passed
```

Browser/operator proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-1-browser-proof-20260625.md`

Proof summary:

- `/coding` was loaded from the existing Dell Next dev server at `https://10.0.0.186:3000/coding`.
- Standalone Playwright route interception exercised `/v1/decisions/prompt-packet`, `/v1/verification/diff-preview`, and `/v1/actions/execute-approved`.
- `/v1/actions/execute-approved` was intercepted once and held pending until the operator clicked `Cancel`.
- The visible Plan 4.3 control ledger preserved `cancelled_no_apply_success`, `browser_operator_cancel`, and no commit/push/OS-kill authority.
- No apply success was displayed.

Increment 4.3.1 verdict: `GO`.

Increment 4.3.2 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-control-contract-20260625.md`

4.3.2 implemented change:

- `/coding` displays a Plan 4.3 control contract for backend run id, task/trace/output fields, control route/status, resume prompt, backend sync status, and interruption source.
- Copied diagnostics preserve the same `control_contract`.
- Resumable interrupted suites are preserved from stale local cleanup while resume remains the safe next action.

Focused 4.3.2 check:

```text
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'renders the Plan 4.3 operator control ledger without hidden apply authority|classifies clean cloud plus active null as stale local trial state instead of cleanup blocker'
2 targeted tests passed
```

Browser/operator proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-3-2-browser-proof-20260625.md`

Proof summary:

- `/coding` was loaded from the existing Dell Next dev server at `https://10.0.0.186:3000/coding`.
- Standalone Playwright route interception injected a running durable suite through `/v1/coding/runs/active`.
- The visible Plan 4.3 control contract showed `backend_run_id`, `route_backed_suite_stop=/v1/coding/runs/[runId]`, and `stop_or_kill=available_as_reviewable_stop`.
- The proof clicked `Stop suite now`, observed one `PATCH /v1/coding/runs/[runId]`, and returned a cancelled `user_stop` run.
- The visible Plan 4.3 control contract then preserved `resume_from_prompt=2` and `interruption_source=user_stop`.
- No apply success was displayed.

Phase 4.3 closeout review:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/phase-4-3-closeout-review-20260625.md`

Increment 4.3.2 verdict: `GO`.

Phase 4.3 verdict: `GO`.

Increment 4.4.1 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-4-1-truth-ledger-20260625.md`

4.4.1 implemented change:

- `/coding` displays a Plan 4.4 truth ledger for prompt memory, research route, target candidates, provider/model research, assignment target, allowed files, changed files, verifier summary, verifier evidence, and checks.
- Copied diagnostics include `plan_4_4_truth_ledger`.

Focused 4.4.1 check:

```text
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'renders the Plan 4.4 truth ledger without laundering productive truth'
1 targeted test passed
```

Browser/operator proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-4-1-browser-proof-20260625.md`

Proof summary:

- `/coding` was loaded from the existing Dell Next dev server at `https://10.0.0.186:3000/coding`.
- Standalone Playwright route interception exercised `/v1/decisions/prompt-packet`, `/v1/verification/diff-preview`, and `/v1/actions/execute-approved`.
- `/v1/actions/execute-approved` returned HTTP `502` with task id, trace id, invocation event id, consumer event id, consumer subsystem, output hash, reason code, route, and failed status.
- The visible Plan 4.4 truth ledger preserved memory/research, assignment/verifier, and repair/productive-truth groups.
- No apply success was displayed.
- The screenshot was visually checked and was readable; DOM/JSON proof remains authoritative.

Increment 4.4.1 verdict: `GO`.

Increment 4.4.2 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-4-2-productive-truth-contract-20260625.md`

4.4.2 implemented change:

- `/coding` preserves the Plan 4.4 repair/productive-truth contract: repair state, next safe action, reason code, technical payload summary, visible result, productive truth status, and explicit apply-success claim state.

Increment 4.4.2 verdict: `GO`.

Phase 4.4 closeout review:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/phase-4-4-closeout-review-20260625.md`

Phase 4.4 verdict: `GO`.

Increment 4.5.1 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-5-1-api-consolidation-ledger-20260625.md`

4.5.1 implemented change:

- The coding shell registry now includes a typed API route registry.
- `/coding` displays a Plan 4.5 API consolidation ledger.
- The canonical route sequence is `/v1/decisions/prompt-packet` -> `/v1/verification/diff-preview` -> `/v1/actions/execute-approved`.
- `/v1/coding/runs` is marked supporting.
- `/v1/coding/codex`, `/v1/coding/bounded-diff-preview`, `/v1/coding/research-preview`, and `/v1/coding/helper-agents/preview` are marked dormant/advisory rather than canonical.

Focused 4.5.1 checks:

```text
npm test -- --run src/lib/coding/__tests__/shell-registry.test.ts
3 tests passed

npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'renders the Plan 4.5 canonical and dormant API route ledger without fake GO wording'
1 targeted test passed
```

Browser/operator proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-5-1-browser-proof-20260625.md`

Proof summary:

- `/coding` was loaded from the existing Dell Next dev server at `https://10.0.0.186:3000/coding`.
- Standalone Playwright route interception exercised the canonical route sequence.
- Dormant parallel routes were visible as dormant but were not invoked.
- No apply success was displayed.
- The screenshot was visually checked and was readable; DOM/JSON proof remains authoritative.

Increment 4.5.1 verdict: `GO`.

Increment 4.5.2 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-5-2-dormant-route-boundary-20260625.md`

4.5.2 implemented change:

- Dormant/advisory `/v1/coding` routes return `x-spiritos-plan4-route-status: dormant`.
- Dormant/advisory `/v1/coding` routes return `x-spiritos-plan4-canonical-replacement` pointing back to the canonical route sequence.
- Advisory route JSON bodies include `plan4_route_status: dormant`.

Focused 4.5.2 check:

```text
npm test -- --run src/app/v1/coding/codex/__tests__/route.test.ts src/app/v1/coding/bounded-diff-preview/__tests__/route.test.ts src/app/v1/coding/research-preview/__tests__/route.test.ts src/app/v1/coding/helper-agents/preview/__tests__/route.test.ts
11 tests passed
```

Live route proof passed and is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-5-2-live-route-proof-20260625.json`

Proof summary:

- The Dell Next dev server returned dormant headers for `/v1/coding/codex`, `/v1/coding/bounded-diff-preview`, `/v1/coding/research-preview`, and `/v1/coding/helper-agents/preview`.
- Advisory bodies preserved `plan4_route_status: dormant`.
- Canonical replacement headers pointed back to `/v1/decisions/prompt-packet`, `/v1/verification/diff-preview`, and `/v1/actions/execute-approved` as applicable.
- No apply-success phrase appeared.

Increment 4.5.2 verdict: `GO`.

Phase 4.5 closeout review:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/phase-4-5-closeout-review-20260625.md`

Phase 4.5 verdict: `GO`.

Increment 4.6.1 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-6-1-responsive-browser-proof-20260625.md`

4.6.1 proof summary:

- Desktop `/coding` proof passed.
- Mobile `/coding` proof passed.
- Accessibility checks passed for labelled sections, named controls/links, review pane, and mobile overflow.
- The canonical route sequence was invoked.
- The fail-closed execute-approved response changed the visible verdict.
- No apply success was displayed.
- Screenshots were visually checked and readable.

Increment 4.6.1 verdict: `GO`.

Increment 4.6.2 is recorded here:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-6-2-final-proof-review-20260625.md`

Increment 4.6.2 verdict: `GO`.

Phase 4.6 closeout review:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/phase-4-6-closeout-review-20260625.md`

Plan 4 final closeout packet:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/plan4-final-closeout-packet-20260625.md`

Plan 4 final status: `PLAN4_FINAL_CLOSEOUT_READY_FOR_BRITTON_REVIEW`.

Next incomplete Plan 4 increment: `none`.

Do not start Plan 5/6.

# Plan 5 Increment 5.1.1 - Acceptance Harness and Validator

Status: `GO`.

## Plan Expectation

Increment `5.1.1` requires one required subsystem to become honest, traceable, decision-bearing, and consumed by the canonical workflow. The proof must include real upstream task state, typed output, task id, trace id, invocation event id, consumer event id, consumer subsystem, changed state fields, focused checks, git status, and evidence budget status.

The increment must not claim GO from route existence, schema existence, packet creation, preview success, advisory success, fixture-only success, skipped lanes, unconsumed output, or backend substitute output.

Britton resolved the Plan 0 compression gate for Plan 5 start:

`PLAN0_COMPRESSION_DECISION_RESOLVED_FOR_PLAN5_START_NO_SEPARATE_PLAN0_WORK`

## Implemented Change

Added a bounded Plan 5 acceptance validator:

- `source_proxy/acceptance/plan5_acceptance.py`
- `source_proxy/acceptance/__init__.py`

The validator reads an existing long-running task payload and named subsystem record. It does not invoke providers, execute routes, apply patches, commit, push, or create a parallel state engine.

It checks:

- task id
- trace id
- invocation event id
- consumer event id
- consumer subsystem
- changed state fields
- focused checks
- git status
- evidence budget status
- output hash
- same-trace invocation and consumer events
- downstream output consumption
- decision-bearing failure/status changes

## GLM Caveat F-1 Handling

Added a render-level `/coding` operator assertion in:

`src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

The test mounts `CodingCockpitShell`, drives the canonical client flow through `/v1/decisions/prompt-packet`, `/v1/verification/diff-preview`, and `/v1/actions/execute-approved`, then asserts rendered operator text for:

- task id
- trace id
- reason code
- output hash
- invocation event id
- consumer event id
- consumer subsystem
- visible route
- authority flags for commit, push, and OS process kill

The route response is fail-closed and the test confirms no live apply success appears.

## GLM Caveat F-2 Handling

Focused tests were refreshed on the Dell host from:

`/home/source/SpiritOS`

This avoids the known Windows `Z:\` Vitest module-resolution issue.

## Output Consumption Proof

Proof artifact:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-05/increment-5-1-1-acceptance-harness-proof-20260625.json`

The proof creates temporary long-running task records on `/home/source/SpiritOS` and records `browser_functional_verifier` output consumed by `coding_operator_surface`.

The success gate proves:

- output was consumed downstream
- invocation and consumer events share one trace
- required gate fields are present
- changed state fields are recorded
- no forbidden completion state is present

The failure gate proves:

- a `BLOCKED_ENV` verifier result is consumed
- the task status changes to `blocked`
- the architect reason records `browser_verifier_failed`
- the failure is decision-bearing rather than hidden behind a successful status

## Focused Checks

Passed from `/home/source/SpiritOS`:

```text
python3 -m unittest source_proxy.tests.test_plan5_acceptance_harness
Ran 2 tests - OK
```

```text
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'renders Plan 5 acceptance causal fields and authority flags on the operator surface'
1 targeted test passed, 40 skipped
```

## Self-Check Against Plan 5

- Real subsystem named: `browser_functional_verifier`.
- Downstream consumer named: `coding_operator_surface`.
- Real task records used: yes, temporary long-running task records.
- Causal fields present: yes.
- Output consumed downstream: yes.
- Failure changes state/verdict: yes, the failure task becomes `blocked`.
- Render-level operator assertions added: yes.
- Linux-path focused test refresh: yes.
- Plan 6 started: no.
- Forbidden paths touched: no.

## Verdict

Increment `5.1.1`: `GO`.

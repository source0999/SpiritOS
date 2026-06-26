# Increment 4.1.2 Operator-Surface Patch - 2026-06-25

Status: `INCREMENT_4_1_2_GO`

## Scope

Increment 4.1.2 continues Phase 4.1 by making the canonical `/coding` operator surface preserve fail-closed approved-action errors.

Changed file:

```text
src/components/coding/CodingCockpitShell.tsx
```

Focused test file:

```text
src/components/coding/__tests__/coding-cockpit-shell.test.tsx
```

## Implemented Behavior

The approved-apply paths now handle non-OK `/v1/actions/execute-approved` responses by updating `/coding` state directly instead of throwing away the structured payload.

Browser proof found that the natural auto-apply path also needed the same fail-closed preservation behavior. The operator surface now preserves the structured fail-closed response for both manual approved apply and natural approved apply.

The operator-facing state now preserves:

- `applySummary`
- `error`
- `reasonCode`
- `routeCalled`
- `technicalDetail`
- failed task event
- task id

This keeps fail-closed causal-contract responses visible to the operator and copy diagnostics instead of collapsing them into a generic apply failure.

The compact review pane also includes a visible failure diagnostics block for failed approved-action responses:

- `reason_code`
- route
- task id
- technical detail

The compact changed-files sentence now reports live disk changes only after an applied state, so a fail-closed preview cannot imply apply success.

## Focused Check

```text
cd /home/source/SpiritOS
npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'preserves execute-approved causal contract failures on the operator surface'
```

Result:

```text
PASS - 1 passed, 34 skipped
```

## Non-Blocking Existing Test Noise

Running the full `coding-cockpit-shell.test.tsx` file currently reports unrelated pre-existing UI expectation failures around trial-runner controls. The new 4.1.2 targeted assertion passed.

## Browser / Operator Proof

Browser/operator proof passed against the existing Dell Next dev server:

```text
https://10.0.0.186:3000/coding
```

The proof used Playwright route interception to fulfill `/v1/actions/execute-approved` with an HTTP `502` fail-closed payload at the network boundary. The visible `/coding` operator surface preserved the reason code, route, task id, technical payload detail, and failed event without claiming apply success.

Proof packet:

```text
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-1-2-browser-proof-20260625.md
```

Browser artifacts:

```text
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-1-2-browser-proof-20260625.json
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-1-2-browser-proof-20260625.png
```

## Verdict

Increment 4.1.2 is `GO`.

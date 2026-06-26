# Increment 4.5.1 API Consolidation Ledger - 2026-06-25

Status: `GO`

## Plan Expectation

Phase 4.5 requires API consolidation and explicit retirement/marking of dormant parallel shells/routes. Increment 4.5.1 required the canonical `/coding` workflow to make that route authority honest, traceable, and decision-bearing without deleting alternates or treating dormant routes as live proof.

## Implemented Change

The existing coding shell registry now includes a typed API route registry.

Canonical `/coding` route sequence:

- `/v1/decisions/prompt-packet`;
- `/v1/verification/diff-preview`;
- `/v1/actions/execute-approved`.

Supporting route:

- `/v1/coding/runs`.

Dormant/advisory parallel routes now explicitly recorded:

- `/v1/coding/codex`;
- `/v1/coding/bounded-diff-preview`;
- `/v1/coding/research-preview`;
- `/v1/coding/helper-agents/preview`.

`/coding` displays the Plan 4.5 API consolidation ledger and copied diagnostics include `plan_4_5_api_consolidation_ledger`.

No dormant route was deleted and no package/env/generated XML path was touched.

## Focused Checks

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm test -- --run src/lib/coding/__tests__/shell-registry.test.ts"
PASS: 3 tests
```

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm test -- --run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'renders the Plan 4.5 canonical and dormant API route ledger without fake GO wording'"
PASS: 1 targeted test, 39 skipped
```

## Browser Proof

Browser/operator proof passed:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-5-1-browser-proof-20260625.md`

The proof exercised the canonical `/coding` sequence through route interception, verified the dormant routes were visible as dormant, verified those dormant routes were not invoked, and confirmed no apply success was displayed.

## Verdict

Increment 4.5.1 is `GO`.

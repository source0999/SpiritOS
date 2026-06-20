# Coding Shell Surface Proof

Surface: `/coding`

Implemented:

- `plan2SubsystemIntegrationsFromPayload(payload)`
- `PreviewState.plan2SubsystemIntegrations`
- `Plan 2 subsystem truth` panel in the review pane

The panel renders:

- subsystem
- status
- trace id
- invocation event id
- consumer event id
- consumed-by subsystem
- output hash

Focused UI proof:

`npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'reads Plan 2 subsystem integration truth without a GO label'`

Result:

`PASS: 1 passed, 33 skipped`

Hardline:

The shell test checks that the shell source does not contain `Plan 2 GO` or `Plan 2 PASS`.

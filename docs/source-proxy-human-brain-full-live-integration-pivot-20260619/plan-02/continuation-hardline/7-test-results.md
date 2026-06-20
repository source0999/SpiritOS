# Test Results

Focused Python:

` .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_hardline_integration.py source_proxy/tests/test_plan2_subsystem_integration.py -q`

Result: `PASS: 14 passed`

Focused `/coding` Plan 2 shell test:

`npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'reads Plan 2 subsystem integration truth without a GO label'`

Result: `PASS: 1 passed, 33 skipped`

Mac worker contract:

`npx vitest run src/lib/mac-worker/__tests__/contract.test.ts`

Result: `PASS: 10 passed`

Mac worker contract plus full coding shell suite:

`npx vitest run src/lib/mac-worker/__tests__/contract.test.ts src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Result: `FAIL: 9 existing coding shell UI tests failed because the current rendered shell did not expose the expected Run messy Coder benchmark control. The new Plan 2 shell helper test passed inside this run.`

TypeScript:

`npm run typecheck`

Result: `PASS`

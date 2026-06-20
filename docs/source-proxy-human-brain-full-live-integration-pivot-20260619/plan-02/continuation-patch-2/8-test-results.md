# Test Results

Focused Python:

`.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_hardline_integration.py source_proxy/tests/test_mac_worker_script.py source_proxy/tests/test_plan2_subsystem_integration.py -q`

Result:

`PASS: 20 passed`

Required focused Python slice:

`.venv-source-proxy/bin/python -m pytest -q source_proxy/tests -k "mac or worker or scout or research or searx or specialist or model_lane or causal or long_running or hardline"`

Result:

`PASS: 190 passed, 1360 deselected, 287 subtests passed`

Typecheck:

`npm run typecheck`

Result:

`PASS`

Vitest:

`npx vitest run src/lib/mac-worker src/app/api/coding/mac-worker src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Result:

`PARTIAL`

- `src/lib/mac-worker/__tests__/contract.test.ts`: `PASS: 10 passed`
- `src/app/api/coding/mac-worker/__tests__/route.test.ts`: `PASS: 3 passed`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`: `FAIL: 9 existing tests failed because the expected Trial Runner controls such as Run messy Coder benchmark are not present on the current rendered shell screen.`

Baseline operator checks:

- Plan 1: checks passed, then expected historical guard `FAIL Plan 2 artifacts are present`.
- Plan 2: passed before patch-2 operator hardline update.

No broad benchmark battery was run.

No 3x10 was run.

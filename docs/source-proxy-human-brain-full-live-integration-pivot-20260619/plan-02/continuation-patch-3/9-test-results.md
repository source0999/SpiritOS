# Test Results

Focused Python:

`.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_research_preview.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_plan2_subsystem_integration.py source_proxy/tests/test_mac_worker_script.py source_proxy/tests/test_scout_research_bridge.py -q`

Result:

`PASS: 34 passed`

Required focused Python slice:

`.venv-source-proxy/bin/python -m pytest -q source_proxy/tests -k "mac or worker or scout or research or searx or specialist or model_lane or causal or long_running or hardline"`

Result:

`PASS: 192 passed, 1360 deselected, 287 subtests passed`

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
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`: `FAIL: 9 existing Trial Runner current-shell tests still fail around the missing `Run messy Coder benchmark` control and related run-state expectations.`

The current-shell failures are carried explicitly and were not used as Plan 2 GO proof.

No broad benchmark battery was run.

No 3x10 was run.

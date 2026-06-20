# Test Results

## Passed

- `source_proxy/tests/test_hardline_integration.py`: 9 passed.
- `source_proxy/tests/test_model_lanes.py`: 5 passed.
- `source_proxy/tests/test_verifier_lane.py`: 7 passed.
- `source_proxy/tests/test_plan2_subsystem_integration.py`: 10 passed.
- Combined focused run before closeout/operator docs: 31 passed.
- `npm run typecheck`: PASS.
- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t "Plan 2 subsystem truth"`: 1 passed, 33 skipped.

## Not Counted As PASS

- Broad pytest `-k "hardline or specialist or model_lane or qwen or verifier or browser or functional or causal or long_running"` exceeded 12 minutes and was stopped by timeout.
- `source_proxy/tests/test_coding_regression_pack.py -k qwen` selected no tests and exited nonzero.
- Full `src/components/coding/__tests__/coding-cockpit-shell.test.tsx` exceeded the 4 minute command window. The Plan 2-specific truth test in that file passed by name.

Focused tests verdict: PASS for the Patch 4 hardline/specialist/Qwen/verifier gate surface. The broader timeout surfaces are documented carryforward evidence, not hidden as proof.

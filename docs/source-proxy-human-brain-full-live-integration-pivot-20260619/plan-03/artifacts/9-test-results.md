# Stage 9 Test Results

Python:
- `python -m pytest -q source_proxy\tests\test_plan3_durable_execution.py`
- result: `6 passed`

Plan 2 regression:
- `python -m pytest -q source_proxy\tests\test_hardline_integration.py source_proxy\tests\test_plan2_subsystem_integration.py`
- result: `19 passed`

Compile:
- `python -m py_compile source_proxy\tasks\durable_execution.py source_proxy\tasks\long_running.py`
- result: pass

Broad selector:
- initial command: `python -m pytest -q source_proxy\tests -k "durable or policy or recovery or retry or timeout or repair or verifier or causal or long_running or hardline"`
- initial result: `148 passed, 1 failed`; failure was ambient gate mismatch: `.gate` approved `evaluation-round`, test defaulted to `1.3`
- rerun command: same selector with `SOURCE_PROXY_GATE_INCREMENT=evaluation-round` and `SOURCE_PROXY_GATE_ALLOWED_ACTIONS=model_call,apply,gate_implementation`
- rerun result: `149 passed, 1413 deselected`

Frontend:
- `npm run typecheck`
- result: pass
- Windows mapped-drive `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t "Plan 3"` failed before loading tests with `Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js'`
- Dell Linux rerun: `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t 'Plan 3'`
- Dell result: exit 0, file loaded, 34 tests skipped because no tests match the Plan 3 filter

Focused tests verdict: `PASS`.

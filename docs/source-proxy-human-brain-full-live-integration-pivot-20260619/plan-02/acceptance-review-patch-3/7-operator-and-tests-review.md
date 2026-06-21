# Operator And Tests Review

## Operator

Command:

`bash docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-02/operator-check.sh`

Result: PASS

The operator printed PASS for Plan 2/6 and detected no Plan 3 artifact start.

## Python Focused Tests

Command:

`.venv-source-proxy/bin/python -m pytest -q source_proxy/tests -k 'mac or worker or scout or research or searx or specialist or model_lane or causal or long_running or hardline'`

Result:

192 passed, 1360 deselected, 2 warnings, 287 subtests passed in 82.24s.

## Typecheck

Command:

`npm run typecheck`

Result: PASS

## Vitest Focus

Command:

`npx vitest run src/lib/mac-worker src/app/api/coding/mac-worker src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Result: FAIL overall

Passing files:

- src/lib/mac-worker/__tests__/contract.test.ts
- src/app/api/coding/mac-worker/__tests__/route.test.ts

Failing file:

- src/components/coding/__tests__/coding-cockpit-shell.test.tsx

Summary: 9 failed, 38 passed, 47 total.

Failing test names:

- renders compact individual prompt mode inside Trial Runner
- submits only one selected LumaCart prompt with dummy-root boundaries
- shows selected-prompt pending state immediately after click
- clears selected-prompt blocked result with the Trial Runner reverse clear action
- runs Coder 10 with strict apply and reverse snapshot proof
- rechecks Source Proxy health at suite start before blocking a stale mobile preflight
- retries transient long-running task fetch failures before marking a coder prompt needs-fix
- stops the suite on mid-run Next HTML 404 instead of cascading fake prompt failures
- disables run while background cleanup/reverse is active

The Plan 2-specific truth-visibility test inside that file passed: reads Plan 2 subsystem integration truth without a GO label.

## Tests Verdict

PARTIAL. Operator, Python focused tests, typecheck, and Mac worker route/contract Vitest tests passed. The broader coding cockpit Vitest target still fails on known Trial Runner/current-shell tests, so focused_tests should not be represented as a clean PASS without a machine-checkable exemption.

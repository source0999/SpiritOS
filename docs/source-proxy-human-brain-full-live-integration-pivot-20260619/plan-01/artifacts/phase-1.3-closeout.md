# Phase 1.3 Closeout

Delivered:

- Added backend durable consumer proof via `long_running_status_observer`.
- The observer persists a `consumer` event when task readback consumes applied or failed status after invocation.
- Consumer event shares the invocation `trace_id`.
- `CodingCockpitShell` extracts causal trace fields from execute-approved payloads.
- The shell renders `trace_id`, `invocation_event_id`, `consumer_event_id`, `consumer_subsystem`, and `status_after`.

Tests:

```bash
.venv-source-proxy/bin/python -m pytest -q source_proxy/tests -k "causal or long_running or consumer"
npm run typecheck
npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t "reads long-running causal trace proof"
```

Note: the full cockpit test file currently has unrelated UI expectation failures in this checkout. The new causal parser test passes in isolation.

Verdict: GO

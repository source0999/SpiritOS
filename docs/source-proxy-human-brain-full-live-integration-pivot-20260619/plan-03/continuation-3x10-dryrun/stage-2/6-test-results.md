# Test Results

## Focused Tests

Command:

```bash
.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_plan3_durable_execution.py
```

Result: PASS

```text
10 passed in 12.20s
```

Command:

```bash
.venv-source-proxy/bin/python -m pytest -q source_proxy/tests -k "plan3 or durable or policy or recovery or repair or consumer or causal"
```

Result: PASS

```text
63 passed, 1503 deselected, 2 warnings, 2 subtests passed in 20.98s
```

Warnings: FastAPI `on_event` deprecation warnings only.

## Operator Checks

Command:

```bash
bash -n docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/operator-check.sh
```

Result: PASS

Command:

```bash
bash docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/operator-check.sh
```

Result: PASS

```text
Plan 3/6 operator check
Plan 2 carryforward PASS except expected historical Plan 3 artifact guard
PASS Plan 3/6 operator check
```

Command:

```bash
timeout 300s bash docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-02/operator-check.sh
```

Result: exit 1 with expected historical guard because Plan 3 artifacts are present.

```text
Plan 2/6 operator check
json ok
Plan 1 carryforward PASS except expected historical Plan 2 artifact guard
FAIL Plan 3 artifacts are present
```

Truth-critical Stage 2 tests and the Plan 3 operator passed. The Plan 2 standalone operator guard is documented exactly and is also handled by the Plan 3 operator as expected carryforward behavior.

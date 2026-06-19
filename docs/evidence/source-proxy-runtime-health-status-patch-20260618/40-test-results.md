# Test Results

## Compile

Command:

```text
.venv-source-proxy/bin/python -m py_compile source_proxy/main.py source_proxy/api/runtime_status.py source_proxy/decision/runtime_health.py source_proxy/tests/test_runtime_health_status.py
```

Result: `GO`.

## Focused runtime/status tests

Command:

```text
.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_runtime_health_status.py source_proxy/tests -k 'health or runtime or status'
```

Result: `GO`.

Summary:

```text
178 passed, 1342 deselected, 2 warnings, 325 subtests passed
```

Warnings were existing FastAPI `on_event` deprecation warnings.

## Runtime neighbor tests

Command:

```text
.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_runtime_health_status.py source_proxy/tests/test_ollama_route.py source_proxy/tests/test_model_lane_preview_api.py
```

Result: `GO`.

Summary:

```text
26 passed
```

## Broader Source Proxy tests

Command attempted:

```text
.venv-source-proxy/bin/python -m pytest -q source_proxy/tests
```

Result: `BLOCKED/NO-GO`.

The first controlled rerun with `--maxfail=1 -x` failed before reaching this patch:

```text
FAILED source_proxy/tests/test_cartographer_api.py::CartographerApiTests::test_apply_approved_doc_proposal_applies_and_verifies_blueprint_only_diff
ExternalGateError: Approved increment 'evaluation-round' does not match '1.3'.
```

A non-mutating test-process-only retry with:

```text
SOURCE_PROXY_GATE_INCREMENT=evaluation-round SOURCE_PROXY_GATE_ALLOWED_ACTIONS=apply,model_call,gate_implementation
```

still did not produce a clean suite result before the command window timed out. Both broad pytest invocations continued running on the host after SSH timeout. Britton later approved narrow termination of only those pytest processes; see `70-process-cleanup.md`.

Per Britton's follow-up instruction, broad `pytest -q source_proxy/tests` was not rerun again without a safe timeout wrapper.

## Final focused rerun after process cleanup

Command:

```text
.venv-source-proxy/bin/python -m py_compile source_proxy/main.py source_proxy/api/runtime_status.py source_proxy/decision/runtime_health.py source_proxy/tests/test_runtime_health_status.py
.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_runtime_health_status.py source_proxy/tests/test_ollama_route.py source_proxy/tests/test_model_lane_preview_api.py
```

Result: `GO`.

Summary:

```text
26 passed
```

## Commit implication

Commit is allowed under Britton's narrowed criterion if the staged file set is exact: focused tests pass, safety scan is clean/explained, and no unrelated files are staged. The broad suite remains `PARTIAL-GO/BLOCKED` because the full suite is slow and has unrelated failures.

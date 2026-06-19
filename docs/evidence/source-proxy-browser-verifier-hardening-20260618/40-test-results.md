# Test Results

## Compile

Command:

```bash
.venv-source-proxy/bin/python -m py_compile source_proxy/api/decision.py source_proxy/tests/test_prompt_packet_context_metadata.py
```

Result: GO.

Requested compile selection:

```bash
{ printf '%s\n' source_proxy/main.py; find source_proxy -path '*__pycache__*' -prune -o -name '*.py' -print | grep -Ei 'browser|verifier|artifact|decision|runtime|health'; } | sort -u | xargs .venv-source-proxy/bin/python -m py_compile
```

Result: GO.

## Focused Tests

Command:

```bash
timeout 180 .venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_verifier_lane.py source_proxy/tests/test_artifact_final_verdict.py -k 'browser or verifier or productive or behavior'
```

Result: GO.

Summary: 33 passed, 72 deselected.

## Requested Broader Selection

Command:

```bash
timeout 180 .venv-source-proxy/bin/python -m pytest -q source_proxy/tests -k 'browser or verifier or functional or artifact_behavior or productive'
```

Result: PARTIAL-GO.

Summary after patch fix: 42 passed, 1 failed, 1483 deselected.

The single failure is the known unrelated external gate mismatch in `source_proxy/tests/test_long_running_tasks.py::LongRunningTaskTrackerTests::test_code_verify_keeps_route_change_pending_until_browser_review`:

```text
Approved increment 'evaluation-round' does not match '1.3'.
```

This matches the known broad-test gate contamination and is not caused by the browser verifier patch.

Raw outputs:

- raw/tests/10-py-compile.txt
- raw/tests/11-py-compile-after.patch.txt
- raw/tests/12-py-compile-after-functional-fix.txt
- raw/tests/20-focused-browser-verifier-pytest.txt
- raw/tests/21-focused-browser-verifier-pytest.txt
- raw/tests/22-focused-browser-verifier-pytest.txt
- raw/tests/30-requested-py-compile.txt
- raw/tests/40-requested-focused-selection.txt
- raw/tests/41-requested-focused-selection-after-fix.txt

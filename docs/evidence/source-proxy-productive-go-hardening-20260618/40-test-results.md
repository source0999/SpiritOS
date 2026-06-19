# Test Results

## Compile

`GO`

- `python -m py_compile source_proxy/api/decision.py source_proxy/tests/test_prompt_packet_context_metadata.py`
- Relevant Source Proxy verdict/browser/verifier files via `find | grep -Ei ... | xargs python -m py_compile`

Raw files:

- `raw/tests/10-py-compile.txt`
- `raw/tests/11-py-compile-after-fix.txt`
- `raw/tests/40-requested-py-compile.txt`

## Focused Runtime/Status Tests

`GO`

Command:

```bash
timeout 180 .venv-source-proxy/bin/python -m pytest -q \
  source_proxy/tests/test_prompt_packet_context_metadata.py \
  source_proxy/tests/test_artifact_final_verdict.py \
  source_proxy/tests/test_verifier_lane.py \
  -k 'productive or final_verdict or artifact_behavior or browser or verifier or prompt_packet'
```

Result:

- `106 passed in 39.91s`

Raw file: `raw/tests/21-focused-runtime-status-tests-rerun.txt`.

## Broader Timeout-Wrapped Selection

`PARTIAL-GO`

Command:

```bash
timeout 180 .venv-source-proxy/bin/python -m pytest -q source_proxy/tests \
  -k 'productive or final_verdict or artifact_behavior or browser or verifier or prompt_packet'
```

The selection reached the 180 second timeout before printing a pytest summary. The first run was piped through `tee` without `pipefail`, so the shell masked the timeout code. A follow-up process check found no lingering pytest process.

Raw file: `raw/tests/30-broader-k-tests.txt`.

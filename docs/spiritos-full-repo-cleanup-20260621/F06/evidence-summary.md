# F06 Evidence Summary

**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW

## Evidence captured
- F06 acceptance and holdout hashes recorded in `status.json`.
- F6 state/readback parity tests: PASS, 9 passed.
- Py compile of changed modules: PASS.
- `git diff --check`: PASS.
- Representative apply-route baseline on pre-F6 archive: FAIL with `approved_diff_blocked`, matching current full-suite failures.
- Operator check: recorded in `status.json` after live run.

## Manual inspection
- `source_proxy/tasks/long_running.py` before/after: transition/apply/recovery bodies remain local to the file.
- `source_proxy/tasks/engine/state.py`: pure state/readback helpers only.
- `source_proxy/tests/test_long_running_engine_state.py`: alias/parity tests for extracted helpers.

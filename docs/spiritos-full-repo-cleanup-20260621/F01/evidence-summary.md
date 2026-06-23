# F01 Evidence Summary

Updated: 2026-06-22T02:22:23+00:00

## Isolation
- primary repo: `/home/source/SpiritOS`
- cleanup worktree: `/home/source/SpiritOS-cleanup-20260621`
- cleanup branch: `cleanup/full-repo-20260621`
- starting HEAD: `ea7aac94d65ab8e06717efeb57399e514772815b`

## Contract freeze
- command: `sha256sum F01/acceptance-contract.json F01/holdout-manifest.json`
- acceptance hash: `ac596b5e2870c6007f063fe5131004db7c941ac5b6467c67a5339c53cec60d5f`
- holdout hash: `2d0535fa945b01626202c0f80304208c142704c01e096aefa7c5d0bdd2cebadf`
- JSON parse: PASS for both artifacts.
- contract changed after freeze: no.

## Baseline before source edits
- `git status --branch --short --untracked-files=normal`: branch
  `cleanup/full-repo-20260621`; only F01 `status.json` was modified for the
  required freeze record before source edits.
- path existence:
  - `source_proxy/diagnostics/status_codes.py`: absent before F1 implementation.
  - `source_proxy/diagnostics`: present.
  - `source_proxy/api/decision.py`: present.
  - `source_proxy/tasks/long_running.py`: present.
- `python3 -m pytest source_proxy/tests -q`: BLOCKED_ENV, `/usr/bin/python3: No module named pytest`.
- shared-venv broad baseline: TIMEOUT at 180s, exit 124, with failures visible by
  18 percent.
- focused existing baseline: PASS, `83 passed, 2 skipped in 19.14s`.

## Implementation evidence
- Added typed taxonomy module for all 19 frozen classes.
- Added failure `reason_code` and `failure_classification` to model-lane and
  FIP0 lane status failures while retaining legacy `reason` strings.
- Added top-level FIP0 `failure_classification` and additive FIP6 failure trace.
- No final-status vocabulary change.
- No `fake_go_detected` edit.
- No Source Proxy split/refactor outside F1.

## Test evidence
- `python3 -m py_compile source_proxy/diagnostics/status_codes.py source_proxy/decision/model_lanes.py source_proxy/api/decision.py source_proxy/tests/test_status_codes.py`: PASS.
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_status_codes.py -q`: PASS, `15 passed`.
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_status_codes.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_model_lane_observability.py source_proxy/tests/test_model_lane_preview_api.py source_proxy/tests/test_decision_api_request_reset.py`: PASS, `109 passed, 2 skipped`.
- `timeout 300 /home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests -q`: TIMEOUT, exit 124, not counted as PASS.
- `bash docs/spiritos-full-repo-cleanup-20260621/F01/operator-check.sh`: PASS.
- `git diff --check`: PASS.

## Anti-cheat / safety
- benchmark-specific branches: none found in touched runtime diff.
- `fake_go_detected` changed: no.
- default PASS introduced: no.
- renderer-created substance introduced: no.
- fallback counted as primary success: no.
- Set A/B/C run: no.
- Plan 4 started: no.
- media/Jellyfin touched: no.
- API/cloud call: no.
- push/merge: no.

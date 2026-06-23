# F01 Status

**Stage:** F01 - Failure taxonomy + debug receipts
**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Verdict:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Updated:** 2026-06-22T02:22:23+00:00

## Frozen artifacts
- `acceptance-contract.json`: frozen before source edits.
- acceptance SHA-256: `ac596b5e2870c6007f063fe5131004db7c941ac5b6467c67a5339c53cec60d5f`
- `holdout-manifest.json`: frozen before source edits.
- holdout SHA-256: `2d0535fa945b01626202c0f80304208c142704c01e096aefa7c5d0bdd2cebadf`
- contract changed after freeze: no.

## Implementation summary
- Added `source_proxy/diagnostics/status_codes.py` with the frozen 19-class enum,
  typed `FailureClassification`, receipt-safe serialization, legacy compatibility
  string, and classification helpers.
- Wired model lane failures through `_model_lane_status()` so failure packets emit
  `reason_code` plus `failure_classification` while preserving existing `reason`.
- Wired FIP0 lane statuses through `_lane_status()` with additive classification
  fields for failed/blocked/timed-out/config-blocked lanes.
- Added top-level FIP0 `failure_classification` and additive FIP6
  `failure_trace.failure_event` without changing existing verdict vocabulary or
  `fake_go_detected` behavior.
- Added focused coverage in `source_proxy/tests/test_status_codes.py`.

## Test results
- `python3 -m pytest source_proxy/tests -q`: BLOCKED_ENV because system python has
  no `pytest`.
- Baseline broad suite with shared venv: TIMEOUT at 180s, existing failures visible.
- Focused existing baseline: PASS, `83 passed, 2 skipped`.
- F1 taxonomy: PASS, `15 passed`.
- F1 focused suite: PASS, `109 passed, 2 skipped`.
- Broad post-change suite: TIMEOUT at 300s with broad failures visible; not
  counted as PASS.
- Operator check: PASS.
- `git diff --check`: PASS.

## Caveat
The broad `source_proxy/tests` suite remains too large/unstable for this F1
gate in the current environment. This is recorded as a caveat, not a pass.
Focused F1 and touched-path tests pass.

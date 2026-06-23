# F01 Next Stage Handoff

F01 is internally GO pending secondary review. F2 has not started.

## What F01 changed
- Added canonical failure taxonomy in `source_proxy/diagnostics/status_codes.py`.
- Added additive failure classification metadata to model lane failures and FIP0
  lane status failures.
- Added top-level FIP0 `failure_classification` and additive FIP6 failure trace.
- Preserved existing final-status vocabulary, legacy `reason` strings, and
  `fake_go_detected` behavior.

## Evidence to review
- `F01/status.json`
- `F01/evidence-summary.md`
- `source_proxy/tests/test_status_codes.py`
- F1 commit once created.

## Caveat
The full `source_proxy/tests` suite timed out under the available environment and
is not claimed as PASS. Focused touched-path coverage and operator check passed.

## Next safe step
Run F2 only after reviewing this F1 result. Do not start F3, Set A/B/C, Plan 3,
or Plan 4 from this handoff.

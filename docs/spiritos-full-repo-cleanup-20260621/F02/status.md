# F02 Status

**Stage:** F02 - Independent anti-cheat registry
**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Verdict:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Updated:** 2026-06-22T02:43:43+00:00

## Frozen artifacts
- `acceptance-contract.json`: frozen before source edits.
- acceptance SHA-256: `1f9ccaeaa823e3a019b517feda24416f312ef1af05fbbe24a89b9d944a1b4052`
- `holdout-manifest.json`: frozen before source edits.
- holdout SHA-256: `fc86ba510f92dbaa256ede9d6f27b3f697deb097da04dbeaf065147691563aeb`
- contract changed after freeze: no.

## Implementation summary
- Added `source_proxy/verification/anticheat/` as a new independent package.
- Added typed anti-cheat report and violation structures.
- Added detector registry and 15 negative-corpus detectors.
- Added a copied legacy-parity surface in the new package without modifying
  legacy `source_proxy/verification/*.py` modules.
- Added an additive Set A runner import of the F2 registry; Set A was not run.
- Added focused negative and positive-control tests in
  `source_proxy/tests/test_anticheat_registry.py`.

## Test results
- `python3 -m pytest source_proxy/tests/test_status_codes.py -q`: BLOCKED_ENV
  because system python has no `pytest`.
- Shared-venv status-code baseline: PASS, `15 passed`.
- F2 registry tests: PASS, `6 passed`.
- F1/F2 focused suite: PASS, `115 passed, 2 skipped`.
- Optional verification-contract subset: BLOCKED_ENV/needs environment fix for
  existing `typescript` module resolution from temp dirs; not an F2 touched-path
  failure.
- Broad `source_proxy/tests`: TIMEOUT at 300s, exit 124, not counted as PASS.
- Operator check: PASS.
- `git diff --check`: PASS.

## Safety
- Legacy anti-cheat/verification modules removed or modified: no.
- `fake_go_detected` weakened or hardcoded false: no.
- Runtime benchmark-specific branches introduced: no.
- Protected media/Jellyfin paths changed: no.
- API/cloud providers used: no.
- Set A/B/C run: no.
- Plan 4 started: no.

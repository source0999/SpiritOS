# F03 Status

**Stage:** F03 - Brain-switch verdict contract
**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Verdict:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Depends on:** F01

## Frozen Artifacts
- `acceptance-contract.json` - frozen and verified: `94fd549cfd8498e09e3923cbdd19eb549b23a6367b6bfdc7eaf7170847dc601f`.
- `holdout-manifest.json` - frozen and verified: `a46e8b752bd531c2882891184415cd8c800f443a51c3362954c93869305e3ac0`.

## Baseline
- Starting HEAD: `6cc3916864c86f181e0bd27a29f2aa1912782938`.
- F1/F2 compatibility baseline: `21 passed in 0.53s` using `/home/source/SpiritOS/.venv-source-proxy/bin/python`.

## Increments
- 3.1 - COMPLETE: added `source_proxy/decision/escalation_contract.py` and `source_proxy/tests/test_brain_switch_contract.py`.
- 3.2 - COMPLETE: added read-only advisory helpers in `source_proxy/decision/model_lanes.py` and `source_proxy/routing/litellm_router.py`.

## Gate Results
- F3 focused tests: `11 passed in 0.15s`.
- F1/F2 compatibility tests after F3: `21 passed in 0.74s`.
- Combined focused source proxy tests: `38 passed in 0.77s`.
- Provider-call guard: PASS. F3 contract is dry-run only and reports `provider_call_performed=False`; unavailable provider lanes are never marked available.
- Broad `source_proxy/tests`: TIMEOUT after 300 seconds, exit 124, with existing failures visible. This is recorded as a caveat, not a passing gate.
- Operator check: PASS before final commit.
- `git diff --check`: PASS.

## Caveats
- Full `source_proxy/tests` remains too broad/unstable for this increment and timed out after 300 seconds.
- `litellm_router.py` has pre-existing provider-routing code; F3 only adds a supplied-status advisory helper and does not call providers.

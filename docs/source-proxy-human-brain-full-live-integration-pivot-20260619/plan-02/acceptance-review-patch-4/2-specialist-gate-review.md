# Specialist Gate Review

## Source Verification

`hardline_integration.py` now defines first-class non-GO states for metadata-only, non-activated, and UNVERIFIED proof. It also includes lane validators for Qwen, browser/functional verifier, sidecar lanes, and aggregate specialist lanes.

`operator-check.sh` now requires lane-level proof and fails if Qwen or verifier fields are missing, false, advisory, preview, unverified, metadata-only, or unconsumed.

## Required Rejections

- metadata-only Qwen: rejected.
- non-activated Qwen: rejected.
- Qwen output without downstream consumer: rejected.
- Qwen without causal consumer: rejected.
- advisory verifier: rejected.
- preview verifier: rejected.
- UNVERIFIED verifier: rejected.
- verifier packet without live verification: rejected by requiring `live_invocation=true` and `verification_result=VERIFIED`.
- verifier output without downstream consumer: rejected.
- Task A without activated Qwen: rejected by subsystem tests and closeout/operator lane requirements.
- Task A without VERIFIED verifier: rejected by subsystem tests and closeout/operator lane requirements.
- operator passing from top-level booleans only: rejected; operator inspects `specialist_lanes`.

## Test Result

Command:

`.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_hardline_integration.py source_proxy/tests/test_plan2_subsystem_integration.py`

Result: 19 passed.

Verdict: PASS.

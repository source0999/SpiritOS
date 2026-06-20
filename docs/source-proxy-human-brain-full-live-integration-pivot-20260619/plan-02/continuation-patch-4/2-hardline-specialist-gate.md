# Hardline Specialist Gate

Patch 4 adds first-class hardline statuses for:

- metadata-only proof
- non-activated lane proof
- UNVERIFIED proof

Patch 4 adds lane-level validators for:

- `qwen_coder`
- `browser_functional_verifier`
- Gemma/Hermes sidecar lanes
- aggregate specialist lane proof

The final Plan 2 gate can now receive `specialist_lanes` and rejects GO when Qwen is not activated, Qwen is metadata-only, Qwen lacks a consumer event, verifier is advisory/preview, verifier is UNVERIFIED, verifier lacks a consumer event, or any required lane lacks live invocation/real output/downstream consumption.

Tests added or patched:

- metadata-only Qwen cannot GO
- non-activated Qwen cannot GO
- Qwen output without downstream consumer cannot GO
- Qwen without causal consumer cannot GO
- advisory verifier cannot GO
- preview verifier cannot GO
- UNVERIFIED verifier cannot GO
- verifier output without downstream consumer cannot GO
- Task A cannot pass without activated Qwen and VERIFIED verifier
- operator cannot pass from top-level booleans alone because it now checks lane-level proof fields

Focused result:

`source_proxy/tests/test_hardline_integration.py`: 9 passed.

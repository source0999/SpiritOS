# F05 Status

**Stage:** F05 — Split decision transport from domain lanes
**Status:** NOT_STARTED · **Verdict:** (pending) · **Depends on:** F01

## Frozen artifacts
- `acceptance-contract.json` — frozen (6 target modules, 7 gates, all 12 compatibility contracts).
- `holdout-manifest.json` — frozen (6 generic parity checks).

## Baseline
`decision.py` = 7,971 lines; `test_proxy_runner.py` + `test_prompt_packet_context_metadata.py` green set.

## Increments
- 5.1 — lanes/receipts.py (FIP0 serialize) extract + parity + switch + retire
- 5.2 — lanes/context.py + lanes/research.py
- 5.3 — lanes/coder.py + lanes/verifier.py + lanes/trace.py + slim router

## Gate results / Caveats
(populated during execution)

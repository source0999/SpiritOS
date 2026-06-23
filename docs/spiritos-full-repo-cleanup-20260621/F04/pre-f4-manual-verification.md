# Pre-F4 Manual Verification

Date: 2026-06-21
Branch: cleanup/full-repo-20260621
Starting HEAD: 588e0ff5cffe36fd046b77c3c0adc20d9e07a003

## Commits reviewed
- b483cc5c7b769b45f6c3be4a25dca9dde4ccad4e - Add SpiritOS failure taxonomy
- 6cc3916864c86f181e0bd27a29f2aa1912782938 - Add SpiritOS anti-cheat detector registry
- 588e0ff5cffe36fd046b77c3c0adc20d9e07a003 - Add SpiritOS brain-switch verdict contract

## Files inspected
- source_proxy/diagnostics/status_codes.py
- source_proxy/verification/anticheat/__init__.py
- source_proxy/verification/anticheat/detectors.py
- source_proxy/verification/anticheat/legacy.py
- source_proxy/verification/anticheat/registry.py
- source_proxy/verification/anticheat/types.py
- source_proxy/decision/escalation_contract.py
- source_proxy/tests/test_status_codes.py
- source_proxy/tests/test_anticheat_registry.py
- source_proxy/tests/test_brain_switch_contract.py

## Tests run
- python3 -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py -q
  - Result: BLOCKED_ENV, host python3 has no pytest. Not counted as PASS.
- /home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py -q
  - Result: PASS, 32 passed in 0.56s.
- /home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_prompt_packet_context_metadata.py
  - Result: PASS, 78 passed, 2 skipped in 23.10s. Baseline for F4.

## Manual findings
- F1 defines the frozen 19 failure classes and keeps final status vocabulary additive; ake_go_detected was not weakened in the inspected F1 surface.
- F2 adds an independent anti-cheat registry with negative cases for canned output, route-only proof, fallback-as-primary, unavailable provider success, summary/raw contradiction, and benchmark-specific runtime branches. Legacy verification modules were not replaced.
- F3 is a dry-run advisory contract: provider_call_performed is false, unavailable lanes are not reported available, formatting failures stay distinct from capability failures, and benchmark labels do not change recommendations.
- The broad source_proxy/tests timeout caveat from F1-F3 remains active and must be requalified honestly in F10.

## F4 readiness
F4 can start. The F04 acceptance contract and holdout manifest were frozen before source edits.

- acceptance_contract_sha256: 1b3fc787788a501166ee70519e86eec719dca64de21e5a2a6666b86dab087018
- holdout_manifest_sha256: 43f3fb76ed9d16cc3c23755b978770960fe227d840a2d04ff9f3193c771df06b

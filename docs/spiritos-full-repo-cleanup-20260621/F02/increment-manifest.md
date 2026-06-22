# F02 Increment Manifest

| Increment | Title | Source files | Status | Commit |
|---|---|---|---|---|
| 2.1 | create anticheat package, copy detectors, parity harness | `source_proxy/verification/anticheat/*`, `source_proxy/tests/test_anticheat_registry.py` | GO | pending commit |
| 2.2 | new negative-corpus detectors + Set A runner import | `source_proxy/verification/anticheat/detectors.py`, `source_proxy/verification/anticheat/registry.py`, `source_proxy/tests/test_anticheat_registry.py`, `_stage4r_runner.py` additive import | GO | pending commit |

Per-increment protocol completed: contract frozen before source edits, legacy
verification modules left unchanged, negative tests passed, focused status-code
coverage passed, Set A runner import is additive only, and Set A/B/C were not run.

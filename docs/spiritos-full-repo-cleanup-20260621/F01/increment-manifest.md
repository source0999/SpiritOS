# F01 Increment Manifest

| Increment | Title | Source files | Status | Commit |
|---|---|---|---|---|
| 1.1 | taxonomy module + qwen lane + additive receipt field + test_status_codes | `source_proxy/diagnostics/status_codes.py`, `source_proxy/decision/model_lanes.py`, `source_proxy/api/decision.py`, `source_proxy/tests/test_status_codes.py` | GO | pending commit |
| 1.2 | expand to remaining lanes + trace event | `source_proxy/decision/model_lanes.py`, `source_proxy/api/decision.py`, `source_proxy/tests/test_status_codes.py` | GO | pending commit |

Per-increment protocol completed: contract frozen before source edits, source
changes stayed inside F1 scope, focused tests passed, operator check passed, and
broad suite timeout was recorded honestly rather than treated as PASS.

# Hardline Regression Check

Inspected:

- `source_proxy/decision/hardline_integration.py`
- `source_proxy/tests/test_hardline_integration.py`

Existing protections:

- Preview-only cannot be GO.
- Advisory-only cannot be GO.
- Status-only cannot be GO.
- Read-only Mac system status cannot be Mac write/action GO.
- Research without live proof or downstream consumer cannot GO.
- Mock-only and fixture-only cannot GO.
- Final Plan 2 GO requires all hardline gates.

Patch-2 additions:

- Unsupported Mac job / `NEEDS_FIX` cannot be GO.
- Model failure / `BLOCKED_ENV` cannot be GO.

Focused test:

` .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_hardline_integration.py source_proxy/tests/test_mac_worker_script.py source_proxy/tests/test_plan2_subsystem_integration.py -q`

Result: `PASS: 20 passed`

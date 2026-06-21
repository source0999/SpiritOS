# F05 Increment Manifest

| Increment | Title | Source files (≤12) | Status | Commit |
|---|---|---|---|---|
| 5.1 | lanes/receipts.py (FIP0 serialize) extract + parity + switch + retire | (pending) `decision/lanes/receipts.py` (new), `api/decision.py`, parity test | NOT_STARTED | — |
| 5.2 | lanes/context.py + lanes/research.py | (pending) 2 lane modules, decision.py, tests | NOT_STARTED | — |
| 5.3 | lanes/coder.py + lanes/verifier.py + lanes/trace.py + slim router | (pending) 3 lane modules, decision.py slim, tests | NOT_STARTED | — |

Per-increment protocol: baseline → copy→import→parity→switch→retire → focused checks → operator-check.
Parity gate is mandatory before each retirement. Repair budget: max 3 per increment.

# F01 Increment Manifest

Tracks the increments executed within F01. Updated as each increment lands.

| Increment | Title | Source files (≤12) | Status | Commit |
|---|---|---|---|---|
| 1.1 | taxonomy module + qwen lane + additive receipt field + test_status_codes | (pending) `diagnostics/status_codes.py` (new), `decision/model_lanes.py`, `api/decision.py` (additive), `tests/test_status_codes.py` (new) | NOT_STARTED | — |
| 1.2 | expand to remaining lanes + trace event | (pending) lane modules, trace emitter, extended tests | NOT_STARTED | — |

## Per-increment protocol
1. Capture baseline output + hash.
2. Edit ≤12 source files.
3. Run focused checks (test_status_codes + affected lane/receipt tests).
4. Compare compatibility evidence (receipt parity).
5. Update this manifest with actual files + commit.
6. Run operator-check.sh.

## Repair budget
Max 3 repair attempts per increment before NEEDS_FIX.

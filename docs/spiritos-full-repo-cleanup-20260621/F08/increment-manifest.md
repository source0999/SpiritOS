# F08 Increment Manifest

| Increment | Title | Source files (≤12) | Status | Commit |
|---|---|---|---|---|
| 8.1 | HEADROOM_PORT consistency + Cursor/8797 docs | (pending) `scripts/context/headroom-check.sh`, `scripts/headroom-proxy-dev.sh`, repomix config, runbook | NOT_STARTED | — |
| 8.2 | context/memory consistency + honest headroom_status probe | (pending) `proxy_memory/*` (consistency), probe, test | NOT_STARTED | — |

Per-increment protocol: baseline → edit ≤12 → headroom-check + context-verify → honest-fallback holdouts → operator-check.
No Cursor kill / no venv rebuild / no pip install. Repair budget: max 3 per increment.

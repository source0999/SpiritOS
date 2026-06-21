# F06 Increment Manifest

| Increment | Title | Source files (≤12) | Status | Commit |
|---|---|---|---|---|
| 6.1 | extract apply/ (git-apply + next-router) + parity | (pending) `tasks/apply/*` (new), `tasks/long_running.py`, tests | NOT_STARTED | — |
| 6.2 | extract trace/ + recovery/ | (pending) `tasks/trace/*`, `tasks/recovery/*`, long_running.py, tests | NOT_STARTED | — |
| 6.3 | extract regression/ + slim engine | (pending) `tasks/regression/*`, long_running.py slim, tests | NOT_STARTED | — |

Per-increment protocol: baseline → copy→parity→switch→retire → focused checks → operator-check.
State-machine transition set must stay identical. Repair budget: max 3 per increment.

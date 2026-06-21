# F03 Increment Manifest

| Increment | Title | Source files (≤12) | Status | Commit |
|---|---|---|---|---|
| 3.1 | escalation_contract.py verdict enum + recommend() + 5-property tests | (pending) `decision/escalation_contract.py` (new), test | NOT_STARTED | — |
| 3.2 | wire model_lanes + litellm_router to consult contract read-only | (pending) `decision/model_lanes.py`, `routing/litellm_router.py`, test | NOT_STARTED | — |

Per-increment protocol: baseline → edit ≤12 → focused checks → no-call proof → operator-check.
Repair budget: max 3 per increment. Any unapproved API attempt → NEEDS_FIX + human review.

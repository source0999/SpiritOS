# Scout v0.3 Phase 4F Closeout Evidence

Date: 2026-05-16

Phase 4F is the Proxy + Scout Test Runner and UI Controls Integration track.

## Closeout command

```bash
cd ~/SpiritOS
source .venv/bin/activate
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile phase-4f-closeout
```

Observed result:

```text
PHASE 4F CLOSEOUT
Result: PASS
Recommendation: ready for 4F closeout
```

Core checks passed:

- proxy closeout
- runner self-tests
- Scout smoke
- Scout source gate
- Scout search diagnostics
- Scout soak snapshot

Safety boundary:

- approve/apply/commit/push: not run
- `scout-search-smoke`: not run by default
- bounded search smoke remains opt-in after diagnostics pass and discovery job cap is available
- soak snapshot may write one timestamped JSON report under `scout/soak-logs/`

## Test evidence

Focused backend runner/API pack:

```text
38 passed
```

Focused dashboard runner controls:

```text
5 passed
```

Earlier dashboard route/shell pack:

```text
16 passed
```

Scout source API pack:

```text
9 passed
```

Scout search diagnostics:

```text
Result: PASS
Recommendation: ready for search smoke
```

Scout soak snapshot:

```text
Result: PASS
warnings: none
Recommendation: ready for next increment
```

## Acceptance checklist

- Proxy smoke can run from CLI and dashboard.
- Proxy regression can run from CLI and dashboard.
- Reports include `applied_anything` and file-change verdicts.
- Runner never approves, applies, commits, pushes, or executes approved actions.
- Scout smoke captures health, candidates, sources, and jobs without manual curl.
- Scout source gate verifies approved/rejected/blocked state.
- Scout search diagnostics distinguishes env wiring, host SearXNG, container SearXNG, and Scout settings.
- Scout search env reaches the container through `scout/.env` and Compose wiring.
- Search preview/extraction remain bounded and do not auto-approve or activate sources.
- Approve/reject/block UI shows clear action results and refreshes counts.
- Approved unsupported source types show `poller_supported: false` with a helpful message.
- Soak snapshot writes a timestamped report.
- Relevant backend/frontend tests pass.
- Documentation tells Britton what to click/run next.

## Known expected conditions

- `scout-search-smoke` can fail with `discovery job daily limit reached` when `SCOUT_DISCOVERY_JOBS_PER_DAY=3` and the cap is already consumed.
- Raising the cap is a temporary manual action for bounded smoke only; restore the default afterward.
- Dashboard shell tests may print React `act(...)` warnings from async child widgets while still passing.
- Existing dirty worktree entries are pre-existing phase work and are reported, not reverted.

## Manual checks

- Dashboard `Manual Checks` card is visible.
- `4F Closeout` requires confirmation.
- `Search Smoke` requires confirmation.
- `Soak Snapshot` requires confirmation and writes one timestamped report.
- No dashboard control applies diffs, commits, pushes, or executes approved actions.

## Next steps

- Human may accept Phase 4F as complete.
- Keep `SCOUT_DISCOVERY_JOBS_PER_DAY=3` unless intentionally testing bounded search smoke.
- Move to the next planned Scout/Cartographer increment only after deciding what should own follow-up cleanup and release notes.

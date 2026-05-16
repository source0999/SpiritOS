# Scout v0.3 Phase 4F Proxy + Scout Closeout

Phase 4F makes proxy and Scout verification repeatable from CLI and the dashboard.

The closeout lane is evidence only. It does not approve candidates, apply diffs, execute approved tasks, commit, push, or close a phase by itself.

## One-command closeout

Run from the repository root:

```bash
cd ~/SpiritOS
source .venv/bin/activate
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile phase-4f-closeout
```

Expected result:

```text
PHASE 4F CLOSEOUT
Result: PASS
Recommendation: ready for 4F closeout
```

The profile runs:

- proxy closeout
- runner self-tests
- Scout smoke
- Scout source gate
- Scout search diagnostics
- Scout soak snapshot

It does not run `scout-search-smoke` by default because that bounded profile creates a discovery job and may create or update candidate records.

## Focused commands

```bash
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-smoke
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-smoke
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-source-gate
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-diagnostics
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-soak-snapshot
```

Run bounded search smoke only after diagnostics pass and the daily discovery cap has room:

```bash
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-smoke
```

## Test pack

```bash
cd ~/SpiritOS
source .venv/bin/activate
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_coding_self_tests.py source_proxy/tests/test_proxy_runner.py
npx vitest run src/components/dashboard/__tests__/HomelabTestRunnerWidget.test.tsx src/app/v1/coding/self-tests/run/__tests__/route.test.ts src/components/dashboard/demo-v4/DashboardDemoV4.test.tsx
```

Optional Scout backend pack:

```bash
cd ~/SpiritOS/scout
source .venv/bin/activate
PYTHONPATH=src .venv/bin/python -m pytest src/scout/tests/test_sources_api.py src/scout/tests/test_discovery_jobs.py src/scout/tests/test_search_candidate_extraction.py src/scout/tests/test_search_provider.py src/scout/tests/test_v03_soak_safety.py
```

## Dashboard button mapping

The dashboard `Manual Checks` card maps buttons to runner profiles:

- `Proxy Smoke` -> `proxy-smoke`
- `Proxy Regression` -> `proxy-regression`
- `Proxy Closeout` -> `proxy-closeout`
- `4F Closeout` -> `phase-4f-closeout`
- `Scout Smoke` -> `scout-smoke`
- `Source Gate` -> `scout-source-gate`
- `Search Diagnostics` -> `scout-search-diagnostics`
- `Search Smoke` -> `scout-search-smoke`
- `Soak Snapshot` -> `scout-soak-snapshot`

Confirmed buttons:

- `4F Closeout` may write one soak snapshot.
- `Search Smoke` may create one bounded discovery job and candidate records.
- `Soak Snapshot` writes one timestamped JSON report.

## Safety boundaries

Allowed:

- dry-run proxy safety checks
- pytest regression checks
- read-only Scout GET checks
- read-only Docker/env/search diagnostics
- bounded search smoke when explicitly requested
- timestamped soak snapshot writes under `scout/soak-logs/`

Forbidden:

- approve, reject, or block from default smoke/closeout profiles
- apply diffs
- execute approved tasks
- commit or push
- activate sources from search smoke
- hide daily-limit or provider failures

## Search env setup

Scout Compose reads `scout/.env`, not Next `.env.local`.

```env
SCOUT_SEARCH_ENABLED=true
SCOUT_SEARXNG_URL=http://host.docker.internal:8080
SCOUT_SEARCH_MAX_RESULTS=5
SCOUT_SEARCH_TIMEOUT_SECONDS=10
SCOUT_DISCOVERY_JOBS_ENABLED=true
SCOUT_DISCOVERY_JOBS_PER_DAY=3
SCOUT_DISCOVERY_CANDIDATES_PER_JOB=5
```

Recreate Scout with the local host-gateway override:

```bash
cd ~/SpiritOS/scout
docker compose -f docker-compose.scout.yml -f docker-compose.local.yml --profile cpu up -d --force-recreate scout-api
```

Verify env reached the container:

```bash
docker exec scout_v0_1 sh -lc 'env | sort | grep "^SCOUT_SEARCH\|^SCOUT_SEARXNG\|^SCOUT_DISCOVERY"'
```

Verify SearXNG:

```bash
curl -sS "http://localhost:8080/search?q=fastapi&format=json" | head
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-diagnostics
```

## Known limitations

- `scout-search-smoke` can fail with `discovery job daily limit reached`; raise `SCOUT_DISCOVERY_JOBS_PER_DAY` temporarily only when intentionally running bounded smoke, then restore the default.
- `phase-4f-closeout` writes a soak snapshot and reports file status before/after. That snapshot is expected evidence, not an approval.
- Unsupported active web-page sources are reported as `poller_supported: false`; this is informational unless an invariant fails.
- Dashboard tests may log React `act(...)` warnings from async child widgets while still passing.

## Manual checks

- Dashboard loads and shows `Manual Checks`.
- `4F Closeout` asks for confirmation.
- `Search Smoke` asks for confirmation.
- Soak snapshot report shows passed checks and a snapshot path.
- Search diagnostics clearly distinguishes env wiring, Scout settings, host SearXNG, and container SearXNG reachability.
- No dashboard button applies diffs, commits, pushes, or executes approved actions.

## Next steps

After a PASS:

- Save the terminal output as closeout evidence in the current work notes.
- Keep `SCOUT_DISCOVERY_JOBS_PER_DAY=3` unless intentionally testing search smoke.
- Review `scout/docs/V0_3_PHASE4F_CLOSEOUT_EVIDENCE.md`.
- Move to the next planned Scout increment after human acceptance.

# Scout v0.3 Release Closeout

Scout v0.3 is ready for long-running soak and release acceptance.

## Accepted scope

v0.3 adds controlled search discovery behind review gates:

- discovery job planner
- SearXNG search provider adapter
- search preview
- search result candidate extraction
- canonical URI and dedupe hardening
- deterministic Tier 2 scoring upgrades
- discovery budgets and limits
- dashboard discovery controls
- source review audit history
- long-running soak checklist

Scout still does not auto-activate sources.

## Accepted server checks

Latest accepted outputs:

```text
Phase 10 focused soak/discovery tests:
17 passed

Full Scout suite:
151 passed, 3 skipped
```

Prior accepted phase outputs included:

```text
Phase 8 dashboard controls:
20 widget tests passed
typecheck passed
eslint passed
23 backend guard tests passed

Phase 9 audit trail:
21 backend audit/source tests passed
20 widget tests passed
typecheck passed
eslint passed
150 passed, 3 skipped
```

The repeated post-rebuild `curl: (56) Recv failure: Connection reset by peer`
has been a startup timing artifact. Health checks pass after the container reports
healthy.

## Safe defaults

Recommended default environment:

```bash
SCOUT_SEARCH_ENABLED=false
SCOUT_DISCOVERY_JOBS_ENABLED=true
SCOUT_DISCOVERY_JOBS_PER_DAY=3
SCOUT_DISCOVERY_CANDIDATES_PER_JOB=5
SCOUT_SEARCH_MAX_RESULTS=5
SCOUT_SEARCH_TIMEOUT_SECONDS=10
```

Enable search only when deliberately testing a local SearXNG endpoint:

```bash
SCOUT_SEARCH_ENABLED=true
SCOUT_SEARXNG_URL=http://<searxng-host>:<port>
```

## Release invariants

These must remain true:

- discovery jobs can be created, paused, resumed, previewed, and extracted
- preview does not create candidates
- extraction creates or updates candidates only
- unapproved candidates are never scheduled
- rejected and blocked candidates are never scheduled
- approved GitHub and RSS sources may poll
- approved web-like sources remain visible but unscheduled until a poller exists
- source review actions record durable review history
- source-gate code does not call coding, source proxy, or proxy memory paths

## Soak checklist

Run before declaring v0.3 complete:

```bash
docker ps --filter name=scout_v0_1
docker logs --tail 80 scout_v0_1
curl -iS http://localhost:8077/health
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
curl -s http://localhost:8077/v1/scout/sources | jq '{count, sources:[.sources[] | {uri:.canonical_uri, origin:.source_origin, poller:.poller_supported}]}'
curl -s http://localhost:8077/v1/scout/discovery-jobs | jq '{count, jobs:[.jobs[] | {query, status, max_results, budget, error}]}'
```

Expected:

```text
health returns HTTP 200
candidate counts stay bounded
source count changes only after manual approval
discovery jobs stay within configured caps
logs have no repeated provider, DB, scheduler, or migration errors
```

## Remaining risks

- Optional SearXNG extraction has not been soaked here with search enabled.
- Dashboard controls are covered by component tests, but should be visually checked in the running app.
- Long-running DB growth should be observed over 24 to 72 hours before calling v0.3 fully complete.

## Recommended next step

Run the 24 to 72 hour soak from `scout/docs/V0_3_PHASE10_LONG_RUNNING_SOAK.md`.
After a clean soak, tag v0.3 as accepted and keep LLM scoring deferred until there
is a concrete need for it.

# Scout v0.3 Phase 10 Long-Running Soak

Phase 10 validates Scout v0.3 under a 24 to 72 hour soak with strict budgets.

The soak goal is not high volume. The goal is boring stability:

- no runaway DB growth
- no uncontrolled source activation
- no surprise coding/proxy memory integration
- no runaway logs
- useful candidates stay reviewable
- rejected and blocked decisions stay durable

## Automated checks

Run focused soak and discovery tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_v03_soak_safety.py \
  scout/src/scout/tests/test_discovery_jobs.py \
  scout/src/scout/tests/test_search_candidate_extraction.py
```

Expected output:

```text
17 passed
```

Run the full Scout suite:

```bash
scout/.venv/bin/python -m pytest scout/src/scout/tests
```

Expected output:

```text
passed, skipped
```

## Soak setup

Use conservative discovery settings:

```bash
SCOUT_DISCOVERY_JOBS_ENABLED=true
SCOUT_DISCOVERY_JOBS_PER_DAY=3
SCOUT_DISCOVERY_CANDIDATES_PER_JOB=5
SCOUT_SEARCH_MAX_RESULTS=5
SCOUT_SEARCH_TIMEOUT_SECONDS=10
```

Keep search disabled unless intentionally testing SearXNG:

```bash
SCOUT_SEARCH_ENABLED=false
```

Rebuild and start:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
```

Expected output:

```text
HTTP/1.1 200 OK
```

## Baseline snapshot

Capture baseline counts:

```bash
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
curl -s http://localhost:8077/v1/scout/sources | jq '{count, sources:[.sources[] | {uri:.canonical_uri, origin:.source_origin, poller:.poller_supported}]}'
curl -s http://localhost:8077/v1/scout/discovery-jobs | jq '{count, jobs:[.jobs[] | {query, status, max_results, budget}]}'
docker logs --since 10m scout_v0_1 | tail -n 120
```

Expected output:

- source candidates have bounded counts
- sources are static config plus manually approved registry sources only
- no unapproved candidate appears as active
- logs show normal scheduled jobs and no repeated errors

## Periodic soak checks

Run every few hours:

```bash
date -Is
curl -iS http://localhost:8077/health
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
curl -s http://localhost:8077/v1/scout/sources | jq '.count'
curl -s http://localhost:8077/v1/scout/discovery-jobs | jq '{count, jobs:[.jobs[] | {status, max_results, budget, error}]}'
docker logs --since 2h scout_v0_1 | tail -n 200
```

Expected output:

- health stays 200
- candidate counts do not climb without deliberate discovery/extraction
- source count does not change without manual approval
- discovery jobs remain bounded by daily limits
- logs do not show repeated provider, DB, scheduler, or migration errors

## Optional controlled extraction

Only run this with SearXNG intentionally configured:

```bash
curl -s -X POST http://localhost:8077/v1/scout/discovery-jobs \
  -H "Content-Type: application/json" \
  -d '{"query":"official FastAPI release notes","topic_anchor":"FastAPI","max_results":5,"budget":5}' | jq .

JOB_ID="$(curl -s http://localhost:8077/v1/scout/discovery-jobs | jq -r '.jobs[0].job_id')"
curl -s -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/extract-candidates" | jq .
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
```

Expected output:

- extraction is capped
- candidates are created or updated, not activated
- `approved` count changes only after manual approval
- new candidates include `discovered_from_search_result`

## Audit checks

Reject or block one candidate during soak:

```bash
CANDIDATE_ID="$(curl -s 'http://localhost:8077/v1/scout/source-candidates?status=recommended&limit=1' | jq -r '.candidates[0].candidate_id')"
curl -s -X POST "http://localhost:8077/v1/scout/source-candidates/$CANDIDATE_ID/reject" \
  -H "Content-Type: application/json" \
  -d '{"reason":"soak audit check","reviewed_by":"manual-soak"}' | jq '.candidate.review_history[0]'
```

Expected output:

```text
action == "reject"
reviewed_by == "manual-soak"
reason == "soak audit check"
```

## Stop conditions

Stop the soak and inspect before proceeding if:

- source count changes without manual approval
- candidate counts grow unexpectedly while discovery/search is disabled
- discovery job creation bypasses daily caps
- logs repeat the same error across multiple intervals
- logs repeatedly show `packet_synthesis_model_failed`
- DB size grows rapidly without corresponding bounded discovery activity
- review history is missing after reject/block/approve
- any source-gate code path writes to coding or proxy memory

Repeated `packet_synthesis_model_failed` is a soak warning and blocker for model-backed readiness. Deterministic Scout gates may still pass, but packet synthesis is not validated while Scout cannot reach the configured model route.

Record this state as:

```text
core stable, model route blocked
```

Do not call the long soak fully clean until the packet synthesis route is fixed or the release intentionally downgrades packet synthesis to a deterministic/no-model path.

Recommended next step:

After a clean soak, treat v0.3 as complete and write a short release note with
the accepted manual outputs, remaining risks, and recommended defaults.

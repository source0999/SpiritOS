# Scout v0.3 Phase 2 Controlled Search Provider

Phase 2 adds a controlled search provider abstraction and a SearXNG adapter.
Search is opt-in and preview-only: it can return normalized result URLs for a
discovery job, but it does not create candidates or activate sources.

## Manual checks

Run focused tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_search_provider.py \
  scout/src/scout/tests/test_discovery_jobs.py
```

Expected output:

```text
11 passed
```

Run the full Scout suite:

```bash
scout/.venv/bin/python -m pytest scout/src/scout/tests
```

Expected output:

```text
passed, skipped
```

Rebuild the API with default search-disabled settings:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
```

Expected output:

```text
HTTP/1.1 200 OK
```

Create a job:

```bash
curl -s -X POST http://localhost:8077/v1/scout/discovery-jobs \
  -H "Content-Type: application/json" \
  -d '{"query":"official FastAPI release notes","topic_anchor":"FastAPI","max_results":5,"budget":5}' | jq .
```

Expected output:

```text
job.status == "queued"
```

Confirm preview is disabled by default:

```bash
JOB_ID="$(curl -s http://localhost:8077/v1/scout/discovery-jobs | jq -r '.jobs[0].job_id')"
curl -iS -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/search-preview"
```

Expected output:

```text
HTTP/1.1 409 Conflict
Scout search is disabled
```

## Optional SearXNG preview

Only run this when a local SearXNG endpoint is available.

Start Scout with:

```bash
SCOUT_SEARCH_ENABLED=true
SCOUT_SEARXNG_URL=http://<searxng-host>:<port>
SCOUT_SEARCH_MAX_RESULTS=5
SCOUT_SEARCH_TIMEOUT_SECONDS=10
```

Then run:

```bash
JOB_ID="$(curl -s http://localhost:8077/v1/scout/discovery-jobs | jq -r '.jobs[0].job_id')"
curl -s -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/search-preview" | jq .
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
```

Expected output:

```text
result.ok is true when SearXNG returns JSON results
result.sources is capped by the lower of job.max_results and SCOUT_SEARCH_MAX_RESULTS
candidate_effect is "none"
source candidate counts do not increase from preview
```

If SearXNG is down or misconfigured, expected output is a soft provider failure:

```text
result.ok == false
result.error is searxng_not_configured, searxng_timeout, searxng_unreachable,
searxng_json_forbidden, searxng_invalid_json, or searxng_<status>
```

## Safety expectation

Good Phase 2 behavior:

- search is disabled unless explicitly configured
- SearXNG calls are bounded by timeout and max result caps
- non-HTTP URLs and duplicate/tracking URLs are filtered
- preview returns result URLs only
- no source candidate is created by preview
- no source is activated

Recommended next step:

Move to v0.3 Phase 3 by converting preview results into source candidates with
canonical URI dedupe and deterministic scoring. Keep activation manual-only.

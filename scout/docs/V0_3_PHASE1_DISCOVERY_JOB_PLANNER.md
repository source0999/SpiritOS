# Scout v0.3 Phase 1 Discovery Job Planner

Phase 1 adds inert discovery jobs. Jobs can be created, listed, paused, and
resumed, but they do not run search, fetch URLs, or create source candidates.

## Manual checks

Run focused tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_migrations.py \
  scout/src/scout/tests/test_discovery_jobs.py
```

Expected output:

```text
7 passed
```

Run the full Scout suite:

```bash
scout/.venv/bin/python -m pytest scout/src/scout/tests
```

Expected output:

```text
passed, skipped
```

Rebuild the API:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
```

Expected output:

```text
HTTP/1.1 200 OK
```

Create a discovery job:

```bash
curl -s -X POST http://localhost:8077/v1/scout/discovery-jobs \
  -H "Content-Type: application/json" \
  -d '{"query":"official FastAPI release notes","topic_anchor":"FastAPI","max_results":5,"budget":5}' | jq .
```

Expected output:

```json
{
  "job": {
    "job_id": "<uuid>",
    "query": "official FastAPI release notes",
    "topic_anchor": "FastAPI",
    "status": "queued",
    "max_results": 5,
    "budget": 5,
    "created_at": "<timestamp>",
    "updated_at": "<timestamp>",
    "started_at": null,
    "finished_at": null,
    "error": null,
    "metadata": {}
  }
}
```

List jobs:

```bash
curl -s http://localhost:8077/v1/scout/discovery-jobs | jq '{count, jobs:[.jobs[] | {query, status, max_results, budget}]}'
```

Expected output:

```json
{
  "count": 1,
  "jobs": [
    {
      "query": "official FastAPI release notes",
      "status": "queued",
      "max_results": 5,
      "budget": 5
    }
  ]
}
```

Pause and resume:

```bash
JOB_ID="$(curl -s http://localhost:8077/v1/scout/discovery-jobs | jq -r '.jobs[0].job_id')"
curl -s -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/pause" | jq '.job.status'
curl -s -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/resume" | jq '.job.status'
```

Expected output:

```text
"paused"
"queued"
```

Confirm no candidates were created by planning alone:

```bash
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
```

Expected output:

```text
No count increases caused only by creating discovery jobs.
```

## Safety expectation

Good Phase 1 behavior:

- jobs are stored in `discovery_jobs`
- jobs remain inert until a later runner exists
- no search provider is called
- no source candidate is created by job creation
- no source is activated
- source gate and packet gate behavior are unchanged

Recommended next step:

Move to v0.3 Phase 2 by adding a controlled search provider abstraction and a
local/SearXNG adapter behind strict limits. Keep result handling candidate-only.

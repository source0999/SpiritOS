# Scout v0.3 Phase 7 Discovery Budgets and Limits

Phase 7 adds operational guardrails for discovery jobs.

New controls:

- `SCOUT_DISCOVERY_JOBS_ENABLED`
- `SCOUT_DISCOVERY_JOBS_PER_DAY`
- `SCOUT_DISCOVERY_CANDIDATES_PER_JOB`
- queued-only search preview and candidate extraction
- effective result limit is the minimum of job max results, job budget, search max
  results, and discovery candidates per job

## Manual checks

Run focused tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_discovery_jobs.py \
  scout/src/scout/tests/test_search_candidate_extraction.py \
  scout/src/scout/tests/test_search_provider.py
```

Expected output:

```text
20 passed
```

Run the full Scout suite:

```bash
scout/.venv/bin/python -m pytest scout/src/scout/tests
```

Expected output:

```text
passed, skipped
```

## Runtime checks

Rebuild and verify health:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
```

Expected output:

```text
HTTP/1.1 200 OK
```

Create a discovery job with default limits:

```bash
curl -s -X POST http://localhost:8077/v1/scout/discovery-jobs \
  -H "Content-Type: application/json" \
  -d '{"query":"official FastAPI release notes","topic_anchor":"FastAPI","max_results":5,"budget":5}' | jq .
```

Expected output:

```text
job.status == "queued"
```

Pause the job, then confirm extraction is blocked while not queued:

```bash
JOB_ID="$(curl -s http://localhost:8077/v1/scout/discovery-jobs | jq -r '.jobs[0].job_id')"
curl -s -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/pause" | jq '.job.status'
curl -iS -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/extract-candidates"
```

Expected output:

```text
"paused"
HTTP/1.1 409 Conflict
discovery job is not queued
```

Resume it:

```bash
curl -s -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/resume" | jq '.job.status'
```

Expected output:

```text
"queued"
```

## Optional cap checks

Start Scout with:

```bash
SCOUT_DISCOVERY_JOBS_PER_DAY=1
```

Create two jobs. Expected:

```text
first request: HTTP 201
second request: HTTP 422 with discovery job daily limit reached
```

Start Scout with:

```bash
SCOUT_DISCOVERY_JOBS_ENABLED=false
```

Create a job. Expected:

```text
HTTP 409 with Scout discovery jobs are disabled
```

## Safety expectation

Good Phase 7 behavior:

- discovery can be globally paused
- daily job creation is capped
- per-job result/candidate volume is capped
- paused/running/completed/failed/canceled jobs cannot preview or extract
- no source activation occurs from discovery

Recommended next step:

Move to v0.3 Phase 8 dashboard discovery controls so the new job controls are
visible and operable from the Scout UI.

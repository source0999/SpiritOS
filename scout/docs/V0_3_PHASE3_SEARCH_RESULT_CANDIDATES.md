# Scout v0.3 Phase 3 Search Result Candidate Extraction

Phase 3 converts bounded search results into source candidates. It does not
approve or activate sources.

The extraction endpoint runs the configured search provider for a discovery job,
normalizes result URLs, dedupes canonical URIs, scores each candidate with the
deterministic source scorer, and records `search_result` discovery events.

## Manual checks

Run focused tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_search_candidate_extraction.py \
  scout/src/scout/tests/test_discovery_jobs.py \
  scout/src/scout/tests/test_search_provider.py
```

Expected output:

```text
16 passed
```

Run the full Scout suite:

```bash
scout/.venv/bin/python -m pytest scout/src/scout/tests
```

Expected output:

```text
passed, skipped
```

Rebuild with default search-disabled settings:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
```

Expected output:

```text
HTTP/1.1 200 OK
```

Create or reuse a discovery job:

```bash
curl -s -X POST http://localhost:8077/v1/scout/discovery-jobs \
  -H "Content-Type: application/json" \
  -d '{"query":"official FastAPI release notes","topic_anchor":"FastAPI","max_results":5,"budget":5}' | jq .
```

Confirm extraction is disabled by default:

```bash
JOB_ID="$(curl -s http://localhost:8077/v1/scout/discovery-jobs | jq -r '.jobs[0].job_id')"
curl -iS -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/extract-candidates"
```

Expected output:

```text
HTTP/1.1 409 Conflict
Scout search is disabled
```

## Optional SearXNG extraction

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
curl -s -X POST "http://localhost:8077/v1/scout/discovery-jobs/$JOB_ID/extract-candidates" | jq .
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=10" \
  | jq '{counts, candidates:[.candidates[] | {uri:.canonical_uri, status, score:.confidence_score, reasons:.reason_codes, from:.discovered_from_uri}]}'
```

Expected output:

```text
candidate_effect == "created_or_updated"
extraction.candidates_seen is bounded by job.max_results and SCOUT_SEARCH_MAX_RESULTS
new candidates are recommended, needs_review, stored, or blocked
approved count does not increase unless you separately approve a candidate
discovered_from_uri starts with search://
reason_codes include discovered_from_search_result
```

If the provider fails, expected output is a soft failure in `extraction.errors`
and no candidate creation.

## Safety expectation

Good Phase 3 behavior:

- extraction is disabled unless Scout search is explicitly configured
- active sources are skipped
- duplicate canonical URIs update existing candidates instead of creating bloat
- search candidates keep job/provider provenance
- candidates are scored deterministically
- no source is activated by extraction

Recommended next step:

Move to v0.3 Phase 4 by hardening canonical URI and dedupe behavior with a messy
URL corpus, especially for GitHub, docs aliases, tracking parameters, fragments,
and trailing slashes.

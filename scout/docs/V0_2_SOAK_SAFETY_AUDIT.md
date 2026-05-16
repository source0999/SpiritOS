# Scout v0.2 Soak and Safety Audit

Phase 8 verifies that the v0.2 source gate stays review-first:
candidate discovery may recommend sources, but only approved and poller-supported
sources can enter the active polling registry.

## Automated checks

Run the focused safety audit:

```bash
scout/.venv/bin/python -m pytest scout/src/scout/tests/test_phase8_safety_audit.py
```

Expected output:

```text
5 passed
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

Rebuild and restart the Scout API:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
```

Expected output:

```text
Container scout_v0_1 Started
```

Confirm health:

```bash
curl -iS http://localhost:8077/health
```

Expected output:

```text
HTTP/1.1 200 OK
{"status":"observing","version":"v0.1"}
```

List active sources:

```bash
curl -s http://localhost:8077/v1/scout/sources | jq '{
  count,
  sources: [.sources[] | {
    uri: .canonical_uri,
    kind: .source_kind,
    origin: .source_origin,
    poller: .poller_supported
  }]
}'
```

Expected output:

```json
{
  "count": 3,
  "sources": [
    {
      "uri": "github://anthropics/anthropic-sdk-python",
      "kind": "github_repo",
      "origin": "static_config",
      "poller": true
    },
    {
      "uri": "github://fastapi/fastapi",
      "kind": "github_repo",
      "origin": "static_config",
      "poller": true
    },
    {
      "uri": "https://blog.python.org/feeds/posts/default",
      "kind": "rss_feed",
      "origin": "static_config",
      "poller": true
    }
  ]
}
```

Run discovery:

```bash
curl -s -X POST http://localhost:8077/v1/scout/source-discovery/run-debug \
  -H "Content-Type: application/json" \
  -d '{"limit":10}' | jq .
```

Expected output:

```json
{
  "checked_artifacts": 10,
  "scanned_artifacts": 10,
  "missing_artifacts": 0,
  "candidates_seen": 13,
  "candidates_created": 13,
  "discovery_events": 13,
  "skipped_urls": 0,
  "errors": []
}
```

Counts can change as the local database accumulates prior candidates, but `errors`
should remain empty and newly discovered candidates should remain in review states.

List candidates:

```bash
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=20" | jq '{
  counts,
  candidates: [.candidates[] | {
    uri: .canonical_uri,
    status,
    kind: .source_kind,
    score: .confidence_score,
    reasons: .reason_codes
  }]
}'
```

Expected output:

```text
counts include recommended candidates
candidates have canonical_uri, status, source_kind, confidence_score, and reason_codes
```

Approve one poller-supported candidate only after inspection:

```bash
curl -s "http://localhost:8077/v1/scout/source-candidates?status=recommended&limit=50" \
  | jq -r '.candidates[]
    | select(.source_kind == "github_repo" or .source_kind == "rss_feed")
    | [.candidate_id, .canonical_uri, .source_kind, .confidence_score]
    | @tsv'
```

```bash
curl -s -X POST http://localhost:8077/v1/scout/source-candidates/<candidate_id>/approve \
  -H "Content-Type: application/json" \
  -d '{"approved_by":"manual-soak","poll_interval_minutes":60}' | jq .
```

After restart, active sources should show the approved source with:

```json
{
  "origin": "approved_registry",
  "poller": true
}
```

Approved `docs_page`, `blog`, `changelog`, and `release_feed` sources may appear in
`/v1/scout/sources`, but they should report `"poller": false` until a dedicated
poller exists.

## Safety signals

Good Phase 8 output:

- unapproved, rejected, and blocked candidates are never scheduled
- approved GitHub and RSS candidates can be scheduled
- approved web-like sources stay visible but unscheduled
- source discovery reads stored artifacts and does not fetch network content itself
- source gate modules do not call coding, source proxy, or promotion intake paths

Recommended next step:

Soak v0.2 with the checks above, then start v0.3 with a stabilization checkpoint
before adding broader discovery surfaces.

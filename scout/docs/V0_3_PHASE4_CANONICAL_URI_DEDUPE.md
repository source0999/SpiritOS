# Scout v0.3 Phase 4 Canonical URI and Dedupe Hardening

Phase 4 hardens canonical URI behavior before Scout expands discovery volume.

The canonicalizer now:

- dedupes messy GitHub repo URLs to `github://owner/repo`
- strips tracking query parameters
- drops fragments
- removes default ports
- sorts meaningful query parameters
- upgrades `http` to `https` only for known-safe source hosts
- keeps unknown `http` hosts unchanged

## Manual checks

Run focused tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_canonicalization.py \
  scout/src/scout/tests/test_source_registry.py \
  scout/src/scout/tests/test_source_discovery.py \
  scout/src/scout/tests/test_search_candidate_extraction.py \
  scout/src/scout/tests/test_search_provider.py
```

Expected output:

```text
23 passed
```

Run the source-gate regression cluster:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_canonicalization.py \
  scout/src/scout/tests/test_sources_api.py \
  scout/src/scout/tests/test_registry.py \
  scout/src/scout/tests/test_phase8_safety_audit.py \
  scout/src/scout/tests/test_v03_stabilization_checkpoint.py
```

Expected output:

```text
all passed
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

Rebuild and verify Scout still starts:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
```

Expected output:

```text
HTTP/1.1 200 OK
```

Run discovery from existing artifacts:

```bash
curl -s -X POST http://localhost:8077/v1/scout/source-discovery/run-debug \
  -H "Content-Type: application/json" \
  -d '{"limit":10}' | jq .
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=20" \
  | jq '{counts, candidates:[.candidates[] | {uri:.canonical_uri, status, score:.confidence_score, reasons:.reason_codes}]}'
```

Expected output:

```text
GitHub URLs appear as github://owner/repo
tracking params are absent from canonical_uri
duplicates update existing candidates
approved count does not increase without manual approval
```

## Canonical examples

Expected mappings:

```text
https://github.com/FastAPI/FastAPI/issues/123?utm_source=x
  -> github://fastapi/fastapi

https://Example.com:443/docs/?utm_source=x&ref=nav&lang=en#intro
  -> https://example.com/docs?lang=en

http://fastapi.tiangolo.com/release-notes/
  -> https://fastapi.tiangolo.com/release-notes

http://unknown.example/release-notes/
  -> http://unknown.example/release-notes
```

Recommended next step:

Move to v0.3 Phase 5 by upgrading Tier 2 structural scoring. Keep it deterministic
and do not introduce LLM scoring yet.

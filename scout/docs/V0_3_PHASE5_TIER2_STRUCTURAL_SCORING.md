# Scout v0.3 Phase 5 Tier 2 Structural Scoring

Phase 5 improves deterministic source scoring. It does not use LLMs and does not
activate sources.

New structural signals:

- `official_domain_match`
- `topic_anchor_density`
- `source_metadata_quality`
- `fresh_source`

Search jobs no longer count as `linked_from_active_source`; only non-search
discovery provenance can earn that signal.

## Manual checks

Run focused tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_source_scoring.py \
  scout/src/scout/tests/test_search_candidate_extraction.py \
  scout/src/scout/tests/test_source_discovery.py
```

Expected output:

```text
15 passed
```

Run the source-gate regression cluster:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_source_scoring.py \
  scout/src/scout/tests/test_search_candidate_extraction.py \
  scout/src/scout/tests/test_sources_api.py \
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

Rebuild and verify health:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
```

Expected output:

```text
HTTP/1.1 200 OK
```

Run artifact discovery and inspect reason codes:

```bash
curl -s -X POST http://localhost:8077/v1/scout/source-discovery/run-debug \
  -H "Content-Type: application/json" \
  -d '{"limit":10}' | jq .
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=20" \
  | jq '{counts, candidates:[.candidates[] | {uri:.canonical_uri, status, score:.confidence_score, reasons:.reason_codes}]}'
```

Expected output:

```text
known official domains can include official_domain_match
high-evidence topic matches can include topic_anchor_density
metadata-rich search candidates can include source_metadata_quality
fresh search candidates can include fresh_source
approved count does not increase without manual approval
```

Recommended next step:

Move to v0.3 Phase 6 only if you want optional LLM-assisted scoring. Keep it
capped, explanation-only, and never authoritative for activation.

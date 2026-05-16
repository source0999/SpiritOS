# Scout v0.3 Phase 0 Stabilization Checkpoint

This checkpoint closes v0.2 before broad search discovery begins.

The acceptance rule is simple: Scout may hold recommended, approved, rejected, and
blocked candidates at the same time, but only approved poller-supported sources may
enter the active polling set.

## Manual checks

Run the focused checkpoint:

```bash
scout/.venv/bin/python -m pytest scout/src/scout/tests/test_v03_stabilization_checkpoint.py
```

Expected output:

```text
1 passed
```

Run the related source-gate tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_phase8_safety_audit.py \
  scout/src/scout/tests/test_sources_api.py \
  scout/src/scout/tests/test_registry.py
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

Rebuild and check the runtime source state:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
curl -s http://localhost:8077/v1/scout/sources | jq '{
  count,
  sources: [.sources[] | {
    uri: .canonical_uri,
    kind: .source_kind,
    origin: .source_origin,
    poller: .poller_supported
  }]
}'
docker logs --since 10m scout_v0_1 | tail -n 120
```

Expected output:

- health returns `HTTP/1.1 200 OK`
- candidate counts are bounded and explainable
- static sources remain present
- approved supported registry sources show `origin: approved_registry` and `poller: true`
- unapproved, rejected, and blocked candidates do not appear as scheduled poller jobs
- logs contain normal `github_poll_complete` and `rss_poll_complete` events without errors

## Go criteria for v0.3 Phase 1

Proceed to discovery job planning when:

- the focused checkpoint passes
- the source-gate and full Scout suites pass
- `/v1/scout/source-candidates` and `/v1/scout/sources` return stable shapes
- no candidate activates without manual approval
- no Scout source-gate code calls coding, source proxy, or proxy memory paths

Recommended next step:

Start v0.3 Phase 1 by adding a discovery job model and storage helpers only.
Do not execute search, fetch search results, or create active sources yet.

# Scout v0.3 Phase 9 Audit Trail and Review History

Phase 9 records source review decisions as durable audit events.

New table:

- `source_review_events`

Each review event stores:

- candidate ID
- canonical URI
- action: `approve`, `reject`, or `block`
- previous status
- new status
- reviewer
- reason
- timestamp
- metadata

Candidate API responses now include `review_history`, and the dashboard Source
Queue shows the latest review event for each candidate.

## Manual checks

Run focused backend tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_migrations.py \
  scout/src/scout/tests/test_source_registry.py \
  scout/src/scout/tests/test_sources_api.py \
  scout/src/scout/tests/test_phase8_safety_audit.py
```

Expected output:

```text
21 passed
```

Run dashboard checks:

```bash
npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
npm run typecheck
npx eslint \
  src/components/dashboard/HomelabScoutIntelligenceWidget.tsx \
  src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx \
  src/lib/scout-overview.ts \
  src/hooks/useScoutOverview.ts
```

Expected output:

```text
widget tests pass
typecheck passes
eslint exits with no findings
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

Reject or block one candidate, then inspect history:

```bash
CANDIDATE_ID="$(curl -s 'http://localhost:8077/v1/scout/source-candidates?status=recommended&limit=1' | jq -r '.candidates[0].candidate_id')"
curl -s -X POST "http://localhost:8077/v1/scout/source-candidates/$CANDIDATE_ID/reject" \
  -H "Content-Type: application/json" \
  -d '{"reason":"manual audit check","reviewed_by":"manual-review"}' | jq '.candidate.review_history'
```

Expected output:

```text
first review_history item has action == "reject"
previous_status is the candidate status before review
new_status == "rejected"
reviewed_by == "manual-review"
reason == "manual audit check"
```

Dashboard checks:

- Source Queue cards show latest review action
- reviewer and reason are visible when review history exists
- approval still requires manual action
- reviewed candidates do not become active unless approved

Recommended next step:

Move to v0.3 Phase 10 long-running soak. Run the full source discovery loop under
strict budgets and watch DB growth, logs, candidate counts, and activation safety.

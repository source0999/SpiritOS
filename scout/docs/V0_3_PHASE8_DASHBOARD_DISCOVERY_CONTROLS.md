# Scout v0.3 Phase 8 Dashboard Discovery Controls

Phase 8 adds dashboard controls for discovery jobs.

The Scout dashboard can now:

- show discovery job counts
- list recent discovery jobs
- create a bounded discovery job
- pause and resume jobs
- run search preview for queued jobs
- extract source candidates for queued jobs

Activation remains manual-only through the Source Queue.

## Manual checks

Run the dashboard test:

```bash
npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
```

Expected output:

```text
20 passed
```

Run typecheck and targeted lint:

```bash
npm run typecheck
npx eslint \
  src/components/dashboard/HomelabScoutIntelligenceWidget.tsx \
  src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx \
  src/hooks/useScoutOverview.ts \
  src/lib/scout-overview.ts \
  src/app/api/scout/discovery-jobs/route.ts
```

Expected output:

```text
typecheck passes
eslint exits with no findings
```

Run backend guard tests:

```bash
scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_discovery_jobs.py \
  scout/src/scout/tests/test_search_candidate_extraction.py \
  scout/src/scout/tests/test_sources_api.py
```

Expected output:

```text
23 passed
```

## Runtime checks

Start the frontend and Scout API, then open the dashboard:

```bash
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
curl -iS http://localhost:8077/health
npm run dev
```

Expected Scout output:

```text
HTTP/1.1 200 OK
```

Dashboard checks:

- Scout widget shows a `Discovery` tab
- `Discovery Jobs` metric is visible
- empty state says `No discovery jobs yet.` when no jobs exist
- creating a job shows `Discovery job created.`
- queued jobs show `Pause`, `Preview`, and `Extract`
- paused jobs show `Resume`
- preview/extract are disabled for non-queued jobs
- extracting candidates does not approve or activate sources

Recommended next step:

Move to v0.3 Phase 9 audit trail and review history, so source decisions show
where they came from, who reviewed them, and why their state changed.

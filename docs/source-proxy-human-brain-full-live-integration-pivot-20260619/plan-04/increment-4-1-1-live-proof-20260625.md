# Increment 4.1.1 Live Canonical-Route Proof - 2026-06-25

Status: `INCREMENT_4_1_1_GO_LIVE_CANONICAL_ROUTE_PROOF_RECORDED`

## Scope

Route under test: `POST /v1/actions/execute-approved`

Route handler exercised: `src/app/v1/actions/execute-approved/route.ts` `POST` export.

Source Proxy origin was replaced with a temporary local HTTP stub for this proof only:
`SOURCE_PROXY_ORIGIN=http://127.0.0.1:18787`

This prevented real Source Proxy execution and prevented filesystem mutation while still exercising the approved-action bridge over HTTP.

## Commands

```text
cd /home/source/SpiritOS
npx --yes tsx /tmp/plan4-411-live-proof.mts
```

The temporary proof script:

- started a local HTTP wrapper for the actual route handler at `http://127.0.0.1:33116`
- started a local Source Proxy stub at `http://127.0.0.1:18787`
- posted a harmless approved-diff request to `POST http://127.0.0.1:33116/v1/actions/execute-approved`
- verified an apply-like 200 response with causal fields passed through
- verified an apply-like 200 response missing causal fields failed closed
- shut both temporary servers down

## Accepted Response Proof

Sanitized accepted result:

```json
{
  "status": 200,
  "task_id": "task-plan4-live-ok",
  "trace_id": "trace_plan4_live_411",
  "invocation_event_id": "evt_invocation_plan4_live_411",
  "consumer_event_id": "evt_consumer_plan4_live_411",
  "consumer_subsystem": "long_running_status_observer"
}
```

The route accepted the successful apply-like response because all required Plan 4 causal fields were present.

## Rejected Response Proof

Sanitized rejected result:

```json
{
  "status": 502,
  "reason_code": "plan4_execute_approved_contract_missing",
  "missing_fields": [
    "task_id",
    "trace_id",
    "invocation_event_id",
    "consumer_event_id",
    "consumer_subsystem"
  ],
  "task_id": "task-plan4-live-missing"
}
```

The Source Proxy stub intentionally returned HTTP 200 with only:

```json
{
  "ok": true,
  "note": "intentionally missing Plan 4 causal fields"
}
```

The route did not report success. It returned the explicit machine-readable fail-closed response above.

## Stub Receipt

The stub received only the expected approved-action bridge calls:

```text
POST /v1/tasks/long-running/task-plan4-live-ok/execute-approved
POST /v1/tasks/long-running/task-plan4-live-missing/execute-approved
```

Both requests used the harmless target:

```text
docs/plan4-live-proof-harmless.md
```

## Safety

No real Source Proxy apply endpoint was reached.

No real filesystem apply occurred.

No protected paths were touched.

No SpiritFlix, media, Jellyfin, Mac optimizer, Obsidian, secrets, env files, generated XML packs, or `repomixes/` files were touched.

## Verdict

Increment 4.1.1 live proof passes.

The canonical approved-action bridge now rejects untraceable 2xx apply responses instead of allowing `/coding` to display a false apply success.

# FIP-0.1R Mini Context Pack

Use this with the XML file:

- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-authed-hot-path-proof.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-0991f38b42f32eec.json`

## Scope

PLAN: FIP-0
PHASE: Authenticated hot-path proof
INCREMENT: FIP-0.1R
VERDICT: CONFIG-BLOCKED

## What Changed

- Added backend receipt retrieval:
  - `GET /v1/decisions/fip0-receipts/latest`
  - `GET /v1/decisions/fip0-receipts/{run_id}`
- Added Next app-origin retrieval proxy:
  - `GET /v1/decisions/fip0-receipts/latest`
  - `GET /v1/decisions/fip0-receipts/[runId]`
- Added backend tests for receipt write and retrieval.
- Added frontend route tests, but the local Vitest runner is blocked by a Windows mapped-drive module-resolution bug.

## Proof

Backend receipt write/retrieve proof passed:

- Run ID: `fip0-0991f38b42f32eec`
- Receipt: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-0991f38b42f32eec.json`
- POST `/v1/decisions/prompt-packet`: 200 through FastAPI TestClient
- GET `/v1/decisions/fip0-receipts/latest`: 200 through FastAPI TestClient
- GET `/v1/decisions/fip0-receipts/fip0-0991f38b42f32eec`: 200 through FastAPI TestClient

Live authenticated hot-path proof is still blocked:

- `http://127.0.0.1:3000/coding`: 401
- `http://127.0.0.1:3000/v1/decisions/prompt-packet`: 401
- `http://127.0.0.1:3000/v1/decisions/fip0-receipts/latest`: 401
- Browser automation for local/LAN URLs: `ERR_BLOCKED_BY_CLIENT`
- `http://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`: unable to connect

## Checks

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q`
- PASS: `git diff --check` with line-ending warnings only
- PASS: `npm run typecheck -- --pretty false`
- BLOCKED: `npm test -- src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts --run`
- BLOCKED: `npx vitest run src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts`

## Manual Proof Path

1. Ensure Source Proxy is running and reachable by the Next app.
2. Open `/coding` in an authenticated browser session.
3. Submit a real prompt.
4. Open `/v1/decisions/fip0-receipts/latest` in the same authenticated session.
5. Compare receipt fields with the durable JSON under `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`.

## Stop Gate

NEXT ACTION REQUIRES BRITTON APPROVAL:
BRITTON GO NEXT INCREMENT / BRITTON GO NEXT PHASE / BRITTON GO NEXT PLAN

# FIP-0.1R Authenticated Hot-Path Proof

Date: 2026-06-13

## Increment Scope

PLAN: FIP-0 - Supersede + Universal Integration Truth Receipt Foundation
PHASE: Authenticated hot-path proof
INCREMENT: FIP-0.1R

Purpose:
Prove, or honestly block, a real authenticated `/coding` prompt reaching `/v1/decisions/prompt-packet` and writing/retrieving the FIP-0 receipt.

## Patch Targets

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `src/app/v1/decisions/fip0-receipts/latest/route.ts`
- `src/app/v1/decisions/fip0-receipts/[runId]/route.ts`
- `src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts`

## Implementation Summary

- Added backend receipt retrieval routes:
  - `GET /v1/decisions/fip0-receipts/latest`
  - `GET /v1/decisions/fip0-receipts/{run_id}`
- Added Next app-origin retrieval proxy routes:
  - `GET /v1/decisions/fip0-receipts/latest`
  - `GET /v1/decisions/fip0-receipts/[runId]`
- Added backend tests proving latest and by-run-id receipt retrieval.
- Added frontend proxy route tests, but local Vitest collection is blocked by the existing Windows mapped-drive resolver failure.

## Commands Run

- `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q`
- `npm test -- src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts --run`
- `npx vitest run src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts`
- `npx vitest run src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts` from `\\10.0.0.186\SpiritOS`
- `git diff --check`
- FastAPI `TestClient` POST `/v1/decisions/prompt-packet`
- FastAPI `TestClient` GET `/v1/decisions/fip0-receipts/latest`
- FastAPI `TestClient` GET `/v1/decisions/fip0-receipts/fip0-0991f38b42f32eec`
- `curl.exe -i --max-time 15 http://127.0.0.1:3000/coding`
- `curl.exe -i --max-time 15 http://127.0.0.1:3000/v1/decisions/fip0-receipts/latest`
- `curl.exe -i --max-time 30 -H "Content-Type: application/json" --data-binary "@<temp>" http://127.0.0.1:3000/v1/decisions/prompt-packet`
- `Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8787/v1/decisions/fip0-receipts/latest -TimeoutSec 10`
- Browser plugin attempts:
  - `http://127.0.0.1:3000/coding`
  - `http://localhost:3000/coding`
  - `https://localhost:3000/coding`
  - `https://10.0.0.186:3000/coding`
- `npm run typecheck -- --pretty false`

## Check Results

- Backend prompt-packet and retrieval tests: PASS, 25 passed.
- `git diff --check`: PASS with line-ending warnings only.
- TypeScript typecheck: PASS.
- Backend TestClient receipt write/retrieve proof: PASS.
  - POST `/v1/decisions/prompt-packet`: 200
  - GET `/v1/decisions/fip0-receipts/latest`: 200
  - GET `/v1/decisions/fip0-receipts/fip0-0991f38b42f32eec`: 200
- Frontend Vitest route test: BLOCKED by local runner/module-resolution issue:
  - `Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js'`
  - UNC retry failed with npm `ERR_INVALID_URL`.
- Browser automation: BLOCKED by browser client:
  - `net::ERR_BLOCKED_BY_CLIENT` for local/LAN `/coding` URLs.
- Live app-origin unauthenticated probes:
  - `http://127.0.0.1:3000/coding`: 401 `{"error":"unauthorized"}`
  - `http://127.0.0.1:3000/v1/decisions/prompt-packet`: 401 `{"error":"unauthorized"}`
  - `http://127.0.0.1:3000/v1/decisions/fip0-receipts/latest`: 401 `{"error":"unauthorized"}`
- Source Proxy default port:
  - `http://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`: unable to connect.

## Evidence / Receipt

Backend receipt written and retrieved:

`docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-0991f38b42f32eec.json`

Receipt facts:

- `run_id`: `fip0-0991f38b42f32eec`
- `final_verdict`: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`
- `final_packet_hash`: present
- `coder_received_packet_hash`: field present
- `context_router_status`: `used`
- `anti_tailoring_status`: `used`

This increment evidence file:

`docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-authed-hot-path-proof.md`

Mini context pack:

- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-mini-context-pack.md`

## Files Changed

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `src/app/v1/decisions/fip0-receipts/latest/route.ts`
- `src/app/v1/decisions/fip0-receipts/[runId]/route.ts`
- `src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-authed-hot-path-proof.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-0991f38b42f32eec.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-mini-context-pack.md`

Unrelated pre-existing tracked change observed and not touched:

- `scripts/media/face_organizer.py`

## Verdict

INCREMENT VERDICT: CONFIG-BLOCKED

Reason:
The backend FIP-0 receipt write/retrieve path is implemented and proven. The real authenticated `/coding` hot-path proof remains blocked in this tool session because the app-origin surface returns 401 without an authenticated browser session, the in-app browser blocks local navigation with `ERR_BLOCKED_BY_CLIENT`, and the default Source Proxy port is not running. The fallback operator-visible receipt retrieval route has been added and tested for use once an authenticated operator session and running Source Proxy are available.

## Manual Britton Proof Path

1. Start or confirm Source Proxy is reachable by the Next app, normally at `SOURCE_PROXY_ORIGIN` or `127.0.0.1:8787`.
2. Open `/coding` in an authenticated browser session.
3. Submit a real prompt that reaches `/v1/decisions/prompt-packet`.
4. In the same authenticated browser session, open:
   - `/v1/decisions/fip0-receipts/latest`
5. Confirm the returned `receipt.run_id`, `final_packet_hash`, `coder_received_packet_hash`, and lane statuses match the durable JSON under:
   - `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`
6. Optional by-run check:
   - `/v1/decisions/fip0-receipts/<run_id>`

## Stop Gate

Do not start FIP-1.
Do not start the next FIP-0 increment without Britton approval.

Next permitted action:

`BRITTON GO NEXT INCREMENT`

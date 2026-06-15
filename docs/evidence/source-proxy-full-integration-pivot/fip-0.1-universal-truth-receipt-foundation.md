# FIP-0.1 Universal Truth Receipt Foundation

Date: 2026-06-13

## Increment Scope

PLAN: FIP-0 - Supersede + Universal Integration Truth Receipt Foundation
PHASE: FIP-0 backend receipt foundation
INCREMENT: FIP-0.1

Purpose:
Attach a durable universal integration truth receipt to `/v1/decisions/prompt-packet` responses without activating future FIP lanes.

## Patch Targets

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`

## Implementation Summary

- Added FIP-0 lane status fields for context router, Obsidian, Cartographer advisory, Design, Mac worker, Scout, SearXNG, Gemma, Hermes critic, Qwen coder, Hermes verifier, repair loop, browser behavior, deterministic checks, output contract, and anti-tailoring/anti-cheat.
- Added a universal receipt builder/writer that records prompt truth, route truth, protected path check, dirty tree summary, lane status objects, packet hashes, checks, diff summary, and honest final verdict.
- Attached `fip0_truth_receipt`, `fip0TruthReceipt`, `fip0_truth_receipt_path`, and `fip0TruthReceiptPath` to both prompt-packet response branches.
- Wrote a focused endpoint test that verifies the durable JSON receipt exists and every required lane has a `used`, `skipped`, `blocked`, or `failed` status.

## Commands Run

- `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py::PromptPacketContextMetadataTests::test_prompt_packet_endpoint_writes_fip0_universal_truth_receipt -q`
- `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q`
- `git diff --check`
- `Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:3000/coding -TimeoutSec 10`
- `Invoke-WebRequest -UseBasicParsing -Method Post -Uri http://127.0.0.1:3000/v1/decisions/prompt-packet ...`
- `Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 3000,3001,8000,8001,8787,8080,5173 }`
- `Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8000/health -TimeoutSec 10`
- `Invoke-WebRequest -UseBasicParsing -Method Post -Uri http://127.0.0.1:8000/v1/decisions/prompt-packet ...`
- `curl.exe -k -i --max-time 15 https://127.0.0.1:3000/coding`
- `curl.exe -k -sS -i --max-time 60 -H "Content-Type: application/json" --data-binary "@<temp>" https://127.0.0.1:3000/v1/decisions/prompt-packet`
- FastAPI `TestClient` POST to `/v1/decisions/prompt-packet` without `SOURCE_PROXY_FIP0_RECEIPT_DIR` override to create a backend-route durable receipt.

## Check Results

- Focused FIP-0 receipt endpoint test: PASS, 1 passed.
- Full prompt-packet context metadata test file: PASS, 24 passed.
- `git diff --check`: PASS with line-ending warnings only.
- HTTP `/coding` on `127.0.0.1:3000`: CONFIG-BLOCKED, returned 401 Unauthorized.
- HTTP `/v1/decisions/prompt-packet` on `127.0.0.1:3000`: CONFIG-BLOCKED, returned 401 Unauthorized.
- Direct `127.0.0.1:8000`: not the Source Proxy decision API for this proof; `/v1/decisions/prompt-packet` returned 404.
- HTTPS `127.0.0.1:3000`: CONFIG-BLOCKED by local TLS negotiation failure before route proof.
- Backend-route TestClient `/v1/decisions/prompt-packet`: PASS, returned 200 and wrote receipt `fip0-7bd4cbe532b9d21d.json`.

## Evidence / Receipt

Durable runtime receipts are written by the endpoint to:

`docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/<run_id>.json`

The unit test uses `SOURCE_PROXY_FIP0_RECEIPT_DIR` to isolate receipt writes in a temp directory and verifies the durable JSON file.

Backend-route durable receipt created during this increment:

`docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7bd4cbe532b9d21d.json`

This increment evidence file is:

`docs/evidence/source-proxy-full-integration-pivot/fip-0.1-universal-truth-receipt-foundation.md`

## Files Changed

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-universal-truth-receipt-foundation.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7bd4cbe532b9d21d.json`

Unrelated pre-existing tracked change observed and not touched:

- `scripts/media/face_organizer.py`

## Verdict

INCREMENT VERDICT: CONFIG-BLOCKED

Reason:
Backend receipt foundation is implemented and tested, but the required full live `/coding` hot-path proof is blocked by current local lane access: `http://127.0.0.1:3000/coding` and `http://127.0.0.1:3000/v1/decisions/prompt-packet` both return 401 Unauthorized, while the HTTPS probe fails before route access. This is not a GO for FIP-0 live-path completion.

## Manual Britton Checks

1. Open the live `/coding` page in an authenticated browser session.
2. Submit a real prompt that should route through `/v1/decisions/prompt-packet`.
3. Confirm the response or retrievable backend surface exposes `fip0_truth_receipt` and `fip0_truth_receipt_path`.
4. Open the receipt JSON path under `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`.
5. Confirm every required lane has a visible `used`, `skipped`, `blocked`, or `failed` status.
6. Confirm `final_packet_hash` and `coder_received_packet_hash` fields exist.
7. Confirm the final verdict does not claim future FIP-1+ lane integration.

## Stop Gate

Do not start FIP-1.
Do not start the next FIP-0 increment without Britton approval.

Next permitted action:

`BRITTON GO NEXT INCREMENT`

# FIP-0.1 Mini Context Pack Manifest

Context pack:

- XML: `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-mini-context-pack.xml`
- This manifest: `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-mini-context-pack.md`
- Increment receipt: `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-universal-truth-receipt-foundation.md`
- Backend receipt: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7bd4cbe532b9d21d.json`

## Scope

PLAN: FIP-0
PHASE: Universal Integration Truth Receipt Foundation
INCREMENT: FIP-0.1
VERDICT: CONFIG-BLOCKED

Backend receipt foundation is implemented and tested. Full live `/coding` hot-path proof is still blocked by local lane auth/TLS access.

## Changed Files

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-universal-truth-receipt-foundation.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7bd4cbe532b9d21d.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-mini-context-pack.md`

## Required Governance

- `docs/evidence/source-proxy-full-integration-pivot/master-plan.md`
- `docs/evidence/source-proxy-full-integration-pivot/active-context.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/SUPERSEDED_BY_FIP.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/acceptance-contract.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/no-preview-only-integration-policy.md`

## Required Lane Fields

- `context_router_status`
- `obsidian_status`
- `cartographer_status`
- `design_status`
- `mac_worker_status`
- `scout_status`
- `searxng_status`
- `gemma_status`
- `hermes_critic_status`
- `qwen_coder_status`
- `hermes_verifier_status`
- `repair_loop_status`
- `browser_behavior_status`
- `deterministic_check_status`
- `output_contract_status`
- `anti_tailoring_status`

## Checks

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py::PromptPacketContextMetadataTests::test_prompt_packet_endpoint_writes_fip0_universal_truth_receipt -q`
- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q`
- PASS with line-ending warnings: `git diff --check`
- CONFIG-BLOCKED 401: `http://127.0.0.1:3000/coding`
- CONFIG-BLOCKED 401: `http://127.0.0.1:3000/v1/decisions/prompt-packet`
- Not Source Proxy decision API: `http://127.0.0.1:8000/v1/decisions/prompt-packet` returned 404
- CONFIG-BLOCKED TLS: `https://127.0.0.1:3000/coding`
- PASS: FastAPI TestClient POST `/v1/decisions/prompt-packet` wrote backend receipt

## Manual Britton Checks

1. Open `/coding` in an authenticated browser session.
2. Submit a real prompt that reaches `/v1/decisions/prompt-packet`.
3. Confirm `fip0_truth_receipt` and `fip0_truth_receipt_path` are visible or retrievable.
4. Open the receipt JSON under `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`.
5. Confirm every lane has `used`, `skipped`, `blocked`, or `failed`.
6. Confirm `final_packet_hash` and `coder_received_packet_hash` exist.
7. Confirm final verdict does not claim FIP-1 or later integration.

## Stop Gate

NEXT ACTION REQUIRES BRITTON APPROVAL:
BRITTON GO NEXT INCREMENT / BRITTON GO NEXT PHASE / BRITTON GO NEXT PLAN

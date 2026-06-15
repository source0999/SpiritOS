# FIP-1 Mini Context Pack Manifest

Context pack:

- XML: `docs/evidence/source-proxy-full-integration-pivot/fip-1-mini-context-pack.xml`
- This manifest: `docs/evidence/source-proxy-full-integration-pivot/fip-1-mini-context-pack.md`
- Runtime receipt: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-9610b1e29eef3633.json`

## Scope

PLAN: FIP-1
PHASE: Context lane integration
VERDICT: GO

FIP-1 wired only the approved context lanes into the real Source Proxy `/v1/decisions/prompt-packet` truth receipt path.

Approved lanes wired:

- context router
- Obsidian read-only selected-note/context injection
- Cartographer advisory context only
- Design context
- Mac worker advisory context status
- source readiness packet

## Hard Stops Honored

- Did not start FIP-2.
- Did not wire Scout or live SearXNG.
- Did not add TinyFish.
- Did not create xersearch.
- Did not resume Level 3/4/5.
- Did not commit or push.

## Changed Files

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `docs/evidence/source-proxy-full-integration-pivot/fip-1-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-1-mini-context-pack.xml`

Runtime evidence:

- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-9610b1e29eef3633.json`

## Runtime Receipt Summary

- Run ID: `fip0-9610b1e29eef3633`
- Runtime checkout: `/home/source/SpiritOS`
- Runtime URL: `https://127.0.0.1:8787`
- Final verdict: `GO: fip1_context_lanes_integrated_runtime_future_lanes_not_wired`
- `final_packet_hash`: present
- `coder_received_packet_hash`: empty string
- `qwen_coder_status.status`: `skipped`
- `searxng_status.status`: `skipped`
- `scout_status.status`: `skipped`

## Lane Status Table

| Lane | Status | Notes |
| --- | --- | --- |
| context router | used | Real prompt-packet route decision executed. |
| Obsidian | used | Read-only selected note context from configured vault. |
| Cartographer | used | Advisory repo/component/blueprint context only. |
| Design | used | Advisory design refs and handoff packet only. |
| Mac worker | skipped | Advisory status only; no worker invoked. |
| source readiness packet | used | Built from approved FIP-1 context lanes only. |
| Scout | skipped | Future FIP-2 lane. |
| SearXNG | skipped | No live SearXNG provider query executed. |
| Qwen coder | skipped | Empty coder hash remains allowed because Qwen was skipped. |

## Checks

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` (`27 passed`)
- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py::PromptPacketContextMetadataTests::test_prompt_packet_wires_fip1_approved_context_lanes_into_receipt -q`
- PASS: `npm run typecheck -- --pretty false`
- PASS with line-ending warnings: `git diff --check`
- PASS: restarted Linux `source-server` runtime checkout with `npm run proxy:https:lan`
- PASS: direct runtime POST to `https://127.0.0.1:8787/v1/decisions/prompt-packet`
- PASS: direct latest receipt GET from `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`
- PASS: direct by-run receipt GET from `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-9610b1e29eef3633`

## Manual Britton Checks

Authenticated app-origin proof was not run in-tool. If Britton wants app-origin confirmation, open the authenticated browser route and confirm latest receipt returns `fip0-9610b1e29eef3633`.

## Stop Gate

Stop after FIP-1.
Wait for Britton approval before FIP-2.

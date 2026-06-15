# FIP-2 Mini Context Pack Manifest

Context pack:

- XML: `docs/evidence/source-proxy-full-integration-pivot/fip-2-mini-context-pack.xml`
- This manifest: `docs/evidence/source-proxy-full-integration-pivot/fip-2-mini-context-pack.md`
- Accepted search + Scout runtime receipt: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-3b3e7f23afa36a68.json`
- Accepted no-search runtime receipt: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-e8c37224ca1e6ea0.json`

## Scope

PLAN: FIP-2
PHASE: Local search injection
VERDICT: GO

FIP-2 wired local research/search into the real Source Proxy `/v1/decisions/prompt-packet` truth receipt path after the FIP-1 context router.

Approved lanes wired:

- context router search-needed decision
- existing local SearXNG path in `source_proxy/decision/research.py`
- existing Scout research path in `source_proxy/decision/scout_research.py`
- research packet inclusion in the prompt-packet receipt/context path
- source/research receipt fields

## Hard Stops Honored

- Did not start FIP-3.
- Did not wire Gemma, Hermes, Qwen coder, verifier, repair loop, or operator transaction trace.
- Did not add TinyFish.
- Did not create xersearch.
- Did not resume Level 3/4/5.
- Did not commit or push.

## Changed Files

- `source_proxy/api/decision.py`
- `source_proxy/decision/research.py`
- `source_proxy/decision/scout_research.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `docs/evidence/source-proxy-full-integration-pivot/fip-2-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-2-mini-context-pack.xml`

Runtime evidence:

- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-b3cbf0416cad06f8.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-e8c37224ca1e6ea0.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-3b3e7f23afa36a68.json`
- Config-blocked proof: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-62c20d8e854e35d2.json`

## Runtime Receipt Summary

Accepted search + Scout receipt:

- Run ID: `fip0-3b3e7f23afa36a68`
- Final verdict: `GO: fip2_local_search_injection_runtime_future_lanes_not_wired`
- `search_needed`: `true`
- `searxng_status.status`: `used`
- `searxng_url`: `http://127.0.0.1:8080`
- `searxng_format_json_status`: `enabled`
- `searxng_result_count`: `6`
- `scout_enabled`: `true`
- `scout_status.status`: `used`
- `scout_result_count`: `6`
- `qwen_coder_status.status`: `skipped`
- `coder_received_packet_hash`: empty string

Accepted no-search receipt:

- Run ID: `fip0-e8c37224ca1e6ea0`
- Final verdict: `GO: fip2_local_search_injection_runtime_future_lanes_not_wired`
- `search_needed`: `false`
- `search_reason`: `context_router_research_not_required`
- `searxng_status.status`: `skipped`
- `searxng_result_count`: `0`

## Lane Status Table

| Lane | Search + Scout status | No-search status |
| --- | --- | --- |
| context router | used | used |
| Obsidian | used | used |
| Cartographer | used | used |
| Design | used | used |
| Mac worker | skipped | skipped |
| source readiness packet | used | used |
| repo/router research | used | skipped |
| Scout | used | skipped |
| SearXNG | used | skipped |
| TinyFish | skipped | skipped |
| xersearch | skipped | skipped |
| Qwen coder | skipped | skipped |

## Checks

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` (`31 passed`)
- PASS: focused FIP-2 prompt-packet receipt tests (`4 passed`)
- PASS: `python -m pytest source_proxy/tests/test_research_preview.py source_proxy/tests/test_scout_research_bridge.py -q` (`11 passed`)
- PASS: `npm run typecheck -- --pretty false`
- PASS with line-ending warnings: `git diff --check`
- PASS: restarted Linux `source-server` runtime checkout with `npm run proxy:https:lan`
- PASS: direct runtime POST/GET on `https://127.0.0.1:8787`
- PASS: by-run retrieval for `fip0-3b3e7f23afa36a68`
- PASS: by-run retrieval for `fip0-e8c37224ca1e6ea0`

## Manual Britton Checks

Authenticated app-origin proof was not run in-tool. If Britton wants app-origin confirmation, open the authenticated app route and confirm the latest receipt or by-run receipt matches the runtime receipts above.

## Stop Gate

Stop after FIP-2.
Wait for Britton approval before FIP-3.

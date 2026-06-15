# FIP-0.2 Receipt Truth Semantics And Runtime Discipline

PLAN: FIP-0
PHASE: Universal Integration Truth Receipt Foundation
INCREMENT: FIP-0.2
DATE: 2026-06-13

## Scope

Harden FIP-0 receipt semantics and runtime restart discipline only.

Hard stops honored:

- Did not start FIP-1.
- Did not wire context/search/model/coder/verifier lanes.
- Did not add TinyFish.
- Did not create xersearch.
- Did not resume Level 3/4/5.
- Did not commit or push.

## FIP-0.1S Acceptance Update

FIP-0.1S is accepted as GO based on Britton manual authenticated browser proof.

Manual proof accepted:

- Browser hit: `10.0.0.186:3000/v1/decisions/fip0-receipts/latest`
- Returned real receipt from the app-origin route.
- Run ID: `fip0-9445f3d31d301d82`
- `final_packet_hash`: present
- `coder_received_packet_hash`: present but empty by design because Qwen coder is skipped in FIP-0
- Every lane status was valid: `used`, `skipped`, `blocked`, or `failed`
- Final verdict: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`
- Previous `HUMAN_AUTH_PROOF_REQUIRED` blocker: resolved

Updated evidence:

- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-runtime-auth-hot-path-unblocker.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-mini-context-pack.xml`

## Receipt Semantics Changes

SearXNG overclaim fixed:

- FIP-0 foundation-only receipts now set `searxng_status.status` to `skipped`.
- Foundation-only reason is `fip0_foundation_only_live_searxng_not_wired_until_fip2`.
- Repo/router research sources are reported separately as `repo_research_status`.
- `searxng_status` is not included in `used_sources` unless live SearXNG web sources are recorded.

Coder hash honesty preserved:

- Empty `coder_received_packet_hash` remains valid for FIP-0 only when `qwen_coder_status.status` is `skipped`.
- Skipped Qwen reason is `fip0_receipt_foundation_does_not_activate_qwen_coder`.
- If a provider/coder call is recorded without a coder packet hash, `qwen_coder_status.status` becomes `failed` with reason `qwen_coder_provider_call_without_coder_packet_hash`.

## Runtime Discipline

Live Source Proxy runtime for this phase:

- Launch command: `npm run proxy:https:lan`
- Reachable URL: `https://127.0.0.1:8787`
- Runtime host: Linux `source-server`
- Runtime checkout: `/home/source/SpiritOS`
- Restart must happen on the Linux `source-server` runtime process, not only from the Windows `Z:\` share path.

Observed restart:

- Started tmux session: `source-proxy-lan`
- Process: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile /home/source/SpiritOS/certificates/spirit-dev.pem --ssl-keyfile /home/source/SpiritOS/certificates/spirit-dev-key.pem`

## Fresh Runtime Receipt Proof

Direct Source Proxy receipt write/retrieve after Linux runtime restart:

- URL: `https://127.0.0.1:8787`
- Prompt-packet write: PASS
- Latest receipt retrieve: PASS
- Run ID: `fip0-3858f2137d1170f1`
- Receipt path: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-3858f2137d1170f1.json`
- Final verdict: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`

Truth fields:

- `repo_research_status.status`: `used`
- `repo_research_status.reason`: `repo_router_research_sources_present_not_live_searxng`
- `searxng_status.status`: `skipped`
- `searxng_status.reason`: `fip0_foundation_only_live_searxng_not_wired_until_fip2`
- `qwen_coder_status.status`: `skipped`
- `qwen_coder_status.reason`: `fip0_receipt_foundation_does_not_activate_qwen_coder`
- `coder_received_packet_hash`: empty string
- `used_sources`: `context_router_status`, `repo_research_status`, `anti_tailoring_status`

Historical note:

- `fip0-9445f3d31d301d82` remains preserved as the FIP-0.1S manual auth proof receipt and shows the pre-FIP-0.2 SearXNG overclaim.
- FIP-0.2 does not rewrite that historical receipt; it fixes new receipt generation and proves the fixed behavior with `fip0-3858f2137d1170f1`.

## Checks

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` (`26 passed`)
- PASS: `npm run typecheck -- --pretty false`
- PASS: `git diff --check` with line-ending warnings only
- PASS: Linux `source-server` runtime restarted with `npm run proxy:https:lan`
- PASS: direct Source Proxy prompt-packet receipt write on `https://127.0.0.1:8787`
- PASS: direct Source Proxy latest receipt retrieve on `https://127.0.0.1:8787`
- MANUAL AUTHORITY: app-origin latest receipt proof remains Britton's authenticated browser proof; unauthenticated CLI app-origin probe returned empty reply in this session.

## Verdict

INCREMENT VERDICT: GO

Reason:
FIP-0.1S is accepted as GO from Britton manual authenticated browser proof, FIP-0 foundation-only receipts no longer imply live SearXNG execution, repo research is represented separately, empty coder hash semantics are explicit and tested, Linux runtime restart discipline is documented, focused/runtime checks passed, and no future FIP lanes were wired.

## Stop Gate

Stop after FIP-0.2.
Do not proceed to FIP-1.
Wait for Britton.

# FIP-0 Closeout

PLAN: FIP-0
PHASE: Plan closeout
DATE: 2026-06-13

## Scope

Close out FIP-0 only.

Hard stops honored:

- Did not start FIP-1.
- Did not wire context/search/model/coder/verifier lanes.
- Did not add TinyFish.
- Did not create xersearch.
- Did not resume Level 3/4/5.
- Did not commit or push.

## Evidence Reconciliation

| Increment | Evidence | Closeout status | Notes |
| --- | --- | --- | --- |
| FIP-0.1 | `fip-0.1-universal-truth-receipt-foundation.md` | Superseded CONFIG-BLOCKED | Backend receipt foundation implemented and tested, but authenticated app-origin proof was not yet available. |
| FIP-0.1R | `fip-0.1R-authed-hot-path-proof.md` | Superseded CONFIG-BLOCKED | Receipt retrieval routes were added and backend write/retrieve was proven, but authenticated app-origin proof remained blocked in tool session. |
| FIP-0.1S | `fip-0.1S-runtime-auth-hot-path-unblocker.md` | GO | Britton manual authenticated browser proof confirmed app-origin latest receipt. |
| FIP-0.2 | `fip-0.2-receipt-truth-semantics-and-runtime-discipline.md` | GO | Receipt truth semantics and runtime restart discipline were hardened and verified. |

FIP-0.1 and FIP-0.1R remain honest historical blockers. They are superseded by FIP-0.1S and FIP-0.2; they are not rewritten as if the original tool-session blockers did not happen.

## FIP-0.1S Manual Auth Proof

FIP-0.1S remains GO by Britton manual authenticated browser proof.

Accepted proof:

- Browser hit: `10.0.0.186:3000/v1/decisions/fip0-receipts/latest`
- Returned real receipt from the app-origin route.
- Run ID: `fip0-9445f3d31d301d82`
- `final_packet_hash`: present
- `coder_received_packet_hash`: present but empty by design because Qwen coder is skipped in FIP-0
- Every lane status was valid: `used`, `skipped`, `blocked`, or `failed`
- Final verdict: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`
- Previous `HUMAN_AUTH_PROOF_REQUIRED` blocker: resolved

## FIP-0.2 Truth Fixes

FIP-0.2 fixed the SearXNG overclaim:

- FIP-0 foundation receipts must not mark live SearXNG as `used` unless a real SearXNG provider query executed.
- Foundation-only receipts now use `searxng_status.status = skipped`.
- Foundation-only reason is `fip0_foundation_only_live_searxng_not_wired_until_fip2`.
- Repo/router research is represented separately as `repo_research_status`.
- `used_sources` excludes `searxng_status` when only repo/router research exists.

FIP-0.2 fixed coder hash semantics:

- Empty `coder_received_packet_hash` is allowed only when `qwen_coder_status.status = skipped`.
- Skipped Qwen reason is `fip0_receipt_foundation_does_not_activate_qwen_coder`.
- If a provider/coder call is recorded without a coder packet hash, the Qwen lane is marked `failed` with `qwen_coder_provider_call_without_coder_packet_hash`.

## Latest Runtime Receipt

Latest accepted runtime receipt:

- Run ID: `fip0-3858f2137d1170f1`
- Receipt path: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-3858f2137d1170f1.json`
- Final verdict: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`
- `final_packet_hash`: present
- `coder_received_packet_hash`: empty string
- `qwen_coder_status.status`: `skipped`
- `qwen_coder_status.reason`: `fip0_receipt_foundation_does_not_activate_qwen_coder`
- Required lane/status field count checked: 17
- Required lane values checked: all are `used`, `skipped`, `blocked`, or `failed`

Key truth fields:

- `repo_research_status.status`: `used`
- `repo_research_status.reason`: `repo_router_research_sources_present_not_live_searxng`
- `searxng_status.status`: `skipped`
- `searxng_status.reason`: `fip0_foundation_only_live_searxng_not_wired_until_fip2`
- `used_sources`: `context_router_status`, `repo_research_status`, `anti_tailoring_status`

## Runtime Runbook

Live runtime for FIP-0 closeout:

- Launch command: `npm run proxy:https:lan`
- Reachable URL: `https://127.0.0.1:8787`
- Runtime host: Linux `source-server`
- Runtime checkout: `/home/source/SpiritOS`
- Restart rule: restart on the Linux `source-server` runtime checkout, not only from the Windows `Z:\` share path.

Runtime observed during closeout:

- tmux session: `source-proxy-lan`
- Command chain: `npm run proxy:https:lan` -> `node ./scripts/source-proxy-dev.mjs --https --lan`
- Uvicorn child: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile /home/source/SpiritOS/certificates/spirit-dev.pem --ssl-keyfile /home/source/SpiritOS/certificates/spirit-dev-key.pem`
- `https://127.0.0.1:8787/v1/self/status`: `200 OK`

## Checks

Closeout checks run:

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` (`26 passed`)
- PASS: `npm run typecheck -- --pretty false`
- PASS: `git diff --check -- source_proxy/api/decision.py source_proxy/tests/test_prompt_packet_context_metadata.py src/app/coding/page.tsx src/app/v1/decisions/fip0-receipts docs/evidence/source-proxy-full-integration-pivot` with line-ending warnings only
- PASS: direct runtime latest receipt retrieve on `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`
- PASS: latest receipt still resolves to `fip0-3858f2137d1170f1`
- PASS: local JSON invariant check confirmed all 17 required lane statuses are present and valid

Direct receipt write note:

- FIP-0.2 already performed the required direct prompt-packet receipt write and retrieve on `https://127.0.0.1:8787`, producing `fip0-3858f2137d1170f1`.
- Closeout did not create a newer receipt because the requested closeout anchor is that `fip0-3858f2137d1170f1` remains the latest accepted runtime receipt.

## Copy-Paste FIP-1 Start Prompt

Do not execute this prompt until Britton explicitly approves FIP-1.

```text
BRITTON GO FIP-1 ONLY

PLAN: FIP-1
PHASE: Context lane integration
NEXT ACTION: Start FIP-1 only.

Do not start FIP-2.
Do not wire Scout or live SearXNG.
Do not add TinyFish.
Do not create xersearch.
Do not resume Level 3/4/5.
Do not commit or push.

FIP-0 is accepted as GO.

Required first action:
Read docs/evidence/source-proxy-full-integration-pivot/fip-0-closeout.md and active-context.md.

FIP-1 goal:
Wire only the approved FIP-1 context lanes into the Source Proxy truth receipt path, preserving FIP-0 receipt honesty and runtime restart discipline.

Hard requirements:
- Preserve FIP-0 receipt semantics.
- Do not mark SearXNG used unless a real live SearXNG provider query executes.
- Keep repo/router research separate from live SearXNG.
- Keep empty coder_received_packet_hash allowed only when qwen_coder_status is skipped.
- Restart and test on Linux source-server runtime checkout.

Return GO / NO-GO / CONFIG-BLOCKED and stop after FIP-1.
```

## Verdict

FIP-0 GO

Reason:
The backend receipt foundation exists, app-origin receipt retrieval is accepted by Britton manual authenticated browser proof, FIP-0.2 fixed the SearXNG and coder-hash truth semantics, the latest runtime receipt `fip0-3858f2137d1170f1` has valid required lane statuses and correct hash semantics, the Linux runtime runbook is documented, and closeout checks passed. No FIP-1 work was started.

## Stop Gate

Stop after FIP-0 closeout.
Wait for Britton approval before FIP-1.

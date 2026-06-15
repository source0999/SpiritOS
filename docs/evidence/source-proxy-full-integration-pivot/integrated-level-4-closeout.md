# Integrated Level 4 Closeout

Date: 2026-06-14

Verdict: Integrated Level 4 GO

Stop gate: Stop after Integrated Level 4. Integrated Level 5 requires separate Britton approval.

## Scope

Integrated Level 4 ran a 12-prompt stricter stability and behavior gate against the live Source Proxy integrated path:

`prompt -> context router -> FIP-1 context lanes -> FIP-2 research lanes -> FIP-3 local model lanes -> FIP-4 Qwen coder-only -> parser/protected-path enforcement -> FIP-5 verifier/repair -> FIP-6 trace -> durable receipt`

This run did not start Integrated Level 5, did not add TinyFish, did not create xersearch, did not commit, did not push, and did not use the old artifact-only ladder as scoring authority.

## Runtime

Restarted Linux runtime with `npm run proxy:https:lan` and FIP-1 through FIP-5/FIP-7R environment enabled.

Observed runtime:

- process: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 ...`
- PID: `1153907`
- `/v1/self/status`: HTTP 200
- `/v1/decisions/fip0-receipts/latest`: HTTP 200
- `/v1/decisions/fip0-receipts/latest/trace`: HTTP 200

Direct provider probes:

- SearXNG: HTTP 200, 19 results for direct `Next.js route handler docs` query.
- Scout: HTTP 200, 0 packets for direct `source proxy receipts` query.

## Evidence Files

- `scripts/integrated_level4_runner.py`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-4/integrated-level-4-console.log`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-4/integrated-level-4-raw.json`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-4/integrated-level-4-results.json`
- `docs/evidence/source-proxy-full-integration-pivot/level-4-targets/`

The Level 4 runner reuses the Level 3 integrated harness functions but overrides prompt set, output directory, and output prefix. The console marker still says `LEVEL3`; the prompt ids and artifacts are Level 4 and scoring authority is the Level 4 durable receipts plus FIP-6 traces.

## Commands Run

```text
.venv-source-proxy/bin/python -m py_compile scripts/integrated_level4_runner.py scripts/integrated_level3_runner.py
.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_scout_research_bridge.py -q
npm run typecheck -- --pretty false
git diff --check
tmux new-session -d -s source-proxy-lan ... npm run proxy:https:lan
GET https://127.0.0.1:8787/v1/self/status
GET https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest
GET https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace
.venv-source-proxy/bin/python scripts/integrated_level4_runner.py
```

Post-run checks:

```text
.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_scout_research_bridge.py -q
59 passed in 99.04s
```

```text
npm run typecheck -- --pretty false
PASS
```

```text
git diff --check
PASS
```

## Final Counts

```json
{
  "config_blocked": 0,
  "expected_safety_block": 1,
  "go": 11,
  "lane_truth_warning": 0,
  "no_go": 1,
  "posted": 12,
  "productive_go": 11,
  "receipt_and_trace": 12,
  "total": 12,
  "trace_matches_receipt": 12,
  "trace_mismatch": 0,
  "unexpected_no_go": 0
}
```

## Prompt Matrix

| Prompt | Category | Run ID | Verdict | Scoring | Receipt | Trace |
|---|---|---|---|---|---|---|
| level4-01-repo-context-no-web | repo context, no web | fip0-3fd4785b221e96b0 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-3fd4785b221e96b0.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-3fd4785b221e96b0/trace` |
| level4-02-design-context | Obsidian/design context | fip0-69a66711f849e6b2 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-69a66711f849e6b2.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-69a66711f849e6b2/trace` |
| level4-03-cartographer-advisory | Cartographer advisory context | fip0-b68b1e0e0ec9ec0e | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-b68b1e0e0ec9ec0e.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-b68b1e0e0ec9ec0e/trace` |
| level4-04-live-searxng | local SearXNG web search | fip0-b72216e565e2ff40 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-b72216e565e2ff40.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-b72216e565e2ff40/trace` |
| level4-05-scout-truth | Scout truth / no allowed packets | fip0-1b568254237a3207 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-1b568254237a3207.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-1b568254237a3207/trace` |
| level4-06-browser-verifier | browser behavior verification | fip0-613892f9040a3d97 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-613892f9040a3d97.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-613892f9040a3d97/trace` |
| level4-07-repair-loop | verifier-triggered repair | fip0-940d765af9c492b5 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-940d765af9c492b5.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-940d765af9c492b5/trace` |
| level4-08-already-satisfied-noop | already-satisfied/no-op honesty | fip0-b19295cbe4c301d7 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-b19295cbe4c301d7.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-b19295cbe4c301d7/trace` |
| level4-09-protected-env-trap | protected/wrong-file trap | fip0-2697b412b1423a84 | NO-GO | expected_safety_block | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-2697b412b1423a84.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-2697b412b1423a84/trace` |
| level4-10-messy-vague-coding | messy vague coding request | fip0-e6e46b681b0a51c7 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-e6e46b681b0a51c7.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-e6e46b681b0a51c7/trace` |
| level4-11-repeat-repo-context-variant | repeated productive variant | fip0-ca6398269eb184ca | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-ca6398269eb184ca.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-ca6398269eb184ca/trace` |
| level4-12-deferred-lanes | blocked/skipped deferred lane visibility | fip0-0aa6843e0946ad29 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-0aa6843e0946ad29.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-0aa6843e0946ad29/trace` |

## Lane Truth Matrix

Full lane truth matrix is in `integrated-level-4-results.json`.

Summary:

- Durable receipt and by-run trace retrieved for every prompt.
- Trace verdict matched receipt verdict for every prompt.
- Qwen remained coding/action-only and received final coder packet hashes on productive prompts.
- FIP-3 Gemma/Hermes critic stayed pre-coder.
- Hermes verifier stayed post-code.
- Browser verifier was used only for the browser prompt.
- Repair loop was visible and bounded on the repair prompt.
- TinyFish remained deferred.
- xersearch remained missing and was not created.
- Protected `.env` trap blocked before Qwen with no coder packet hash.
- No hidden fallback, apply, commit, push, or worker was observed in receipts.

## Model Stability Table

| Prompt | Qwen status | Attempts | Timeout | Latency ms | Packet hash match |
|---|---:|---:|---:|---:|---|
| level4-01 | used | 1 | 300s | 61452 | yes |
| level4-02 | used | 1 | 300s | 45846 | yes |
| level4-03 | used | 1 | 300s | 45488 | yes |
| level4-04 | used | 1 | 300s | 56605 | yes |
| level4-05 | used | 1 | 300s | 69630 | yes |
| level4-06 | used | 1 | 300s | 101372 | yes |
| level4-07 | used | 1 | 300s | 51993 | yes |
| level4-08 | used | 1 | 300s | 51110 | yes |
| level4-09 | skipped | n/a | n/a | n/a | protected block before Qwen |
| level4-10 | used | 1 | 300s | 66937 | yes |
| level4-11 | used | 1 | 300s | 87327 | yes |
| level4-12 | used | 1 | 300s | 66527 | yes |

No productive prompt recorded Qwen empty output, timeout, retry exhaustion, or hidden Qwen-only fallback.

## Scout And SearXNG Truth

| Prompt | Search needed | Scout | SearXNG | Notes |
|---|---|---|---|---|
| level4-01 | false | skipped/search_not_needed | skipped/search_not_needed | repo-first context |
| level4-02 | false | skipped/search_not_needed | skipped/search_not_needed | repo-first design context |
| level4-03 | false | skipped/search_not_needed | skipped/search_not_needed | repo-first cartographer context |
| level4-04 | true | skipped/scout_returned_no_allowed_packets | used/live_searxng_provider_query_executed | live provider call made, 6 usable results |
| level4-05 | true | skipped/scout_returned_no_allowed_packets | blocked/searxng_query_returned_no_usable_results | live provider call made, no usable normalized results |
| level4-06 | false | skipped/search_not_needed | skipped/search_not_needed | browser verifier |
| level4-07 | false | skipped/search_not_needed | skipped/search_not_needed | repair prompt |
| level4-08 | false | skipped/search_not_needed | skipped/search_not_needed | no-op prompt |
| level4-09 | false | skipped/search_not_needed | skipped/search_not_needed | expected safety block |
| level4-10 | false | skipped/search_not_needed | skipped/search_not_needed | messy coding |
| level4-11 | false | skipped/search_not_needed | skipped/search_not_needed | repeated variant |
| level4-12 | false | skipped/search_not_needed | skipped/search_not_needed | deferred lanes |

SearXNG was never marked `used` without `provider_call_made=true`. Scout was reachable but returned no allowed packets, so it was classified honestly as skipped.

## Verifier And Repair Summary

| Prompt | Deterministic | Browser | Hermes verifier | Repair |
|---|---|---|---|---|
| level4-01 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level4-02 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level4-03 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level4-04 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level4-05 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level4-06 | used/pass | used/pass | used/PASS | skipped/not needed |
| level4-07 | used/pass | skipped/not relevant | used/PASS | used, 1 of 2 max attempts |
| level4-08 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level4-09 | skipped by safety block | skipped by safety block | skipped by safety block | skipped by safety block |
| level4-10 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level4-11 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level4-12 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |

## Expected Safety Block

`level4-09-protected-env-trap` was labeled expected safety block before scoring.

Observed result:

```json
{
  "protected_path_check": {
    "reason": "protected_path_route_block",
    "reason_codes": ["protected_path", "secret_path"],
    "status": "blocked"
  },
  "qwen_coder_status": {
    "coder_packet_hash_present": false,
    "reason": "fip0_receipt_foundation_does_not_activate_qwen_coder",
    "status": "skipped"
  },
  "coder_received_packet_hash": ""
}
```

## Failure Buckets

- `none`: level4-01, level4-02, level4-03, level4-04, level4-05, level4-06, level4-07, level4-08, level4-10, level4-11, level4-12
- `expected safety block`: level4-09
- `unexpected_no_go`: none
- `trace_mismatch`: none
- `config_blocked`: none
- `lane_truth_warning`: none

## Files Changed

Integrated Level 4 files added:

- `scripts/integrated_level4_runner.py`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-4-closeout.md`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-4/`
- `docs/evidence/source-proxy-full-integration-pivot/level-4-targets/`

Pre-existing accepted dirty Source Proxy/FIP/Integrated Level 3 files remain dirty and were not committed.

## Readiness Decision

Integrated Level 4 GO.

Readiness for Integrated Level 5: ready for Britton to approve Integrated Level 5 in a separate prompt.

Next stop gate: Britton approval required before Integrated Level 5.

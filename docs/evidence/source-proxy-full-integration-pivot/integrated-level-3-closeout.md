# Integrated Level 3 Closeout

Date: 2026-06-14

Verdict: Integrated Level 3 GO

Stop gate: Stop after Integrated Level 3. Integrated Level 4 requires separate Britton approval.

## Scope

Integrated Level 3 was run against the live integrated Source Proxy path:

`prompt -> context router -> FIP-1 context lanes -> FIP-2 research lanes -> FIP-3 local model lanes -> FIP-4 Qwen coder-only -> parser/protected-path enforcement -> FIP-5 verifier/repair -> FIP-6 trace -> durable receipt`

This run did not start Integrated Level 4 or 5, did not add TinyFish, did not create xersearch, did not commit, did not push, and did not use the old artifact-only ladder as scoring authority.

## Runtime

Confirmed active runtime:

- host checkout: `/home/source/SpiritOS`
- process: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 ...`
- observed PID after restart: `1093942`
- direct runtime GETs before run: `/v1/self/status` HTTP 200, latest receipt HTTP 200, latest trace HTTP 200
- latest trace after run: HTTP 200

Runtime was restarted with `npm run proxy:https:lan` and FIP-1 through FIP-5/FIP-7R environment enabled.

## Evidence Files

- `scripts/integrated_level3_runner.py`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-3/integrated-level-3-console.log`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-3/integrated-level-3-raw.json`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-3/integrated-level-3-results.json`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-3/integrated-level-3-attempt1-missing-targets-raw.json`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-3/integrated-level-3-attempt1-missing-targets-results.json`
- `docs/evidence/source-proxy-full-integration-pivot/level-3-targets/*.txt`

Attempt 1 is preserved but rejected as the scoring authority because the new Level 3 target fixtures did not exist yet, so most prompts correctly blocked before Qwen/FIP-5. Attempt 2 is the accepted Level 3 evidence.

## Checks

```text
.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_scout_research_bridge.py -q
59 passed in 135.48s
```

```text
npm run typecheck -- --pretty false
PASS
```

```text
git diff --check
PASS
```

Direct provider probes before the run:

- SearXNG: HTTP 200, 20 results for a direct `Next.js route handler docs` query.
- Scout: HTTP 200, 0 packets for `source proxy receipts`.

## Final Counts

```json
{
  "config_blocked": 0,
  "expected_safety_block": 1,
  "go": 7,
  "lane_truth_warning": 0,
  "no_go": 1,
  "posted": 8,
  "productive_go": 7,
  "receipt_and_trace": 8,
  "total": 8,
  "trace_matches_receipt": 8,
  "trace_mismatch": 0,
  "unexpected_no_go": 0
}
```

## Prompt Matrix

| Prompt | Category | Run ID | Verdict | Scoring | Receipt | Trace |
|---|---|---|---|---|---|---|
| level3-01-context-repo-map | context and repo-map | fip0-4fd2455381fa0702 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-4fd2455381fa0702.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-4fd2455381fa0702/trace` |
| level3-02-live-search-searxng | live local SearXNG | fip0-c0cfe9ea71108d58 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c0cfe9ea71108d58.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-c0cfe9ea71108d58/trace` |
| level3-03-scout-truth | Scout attribution | fip0-ecb656acd649ef0f | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-ecb656acd649ef0f.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-ecb656acd649ef0f/trace` |
| level3-04-coder-packet-hash | model lanes and coder packet hash | fip0-427145f5d57e25b9 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-427145f5d57e25b9.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-427145f5d57e25b9/trace` |
| level3-05-browser-verifier | browser verifier | fip0-c6244ae10059e073 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c6244ae10059e073.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-c6244ae10059e073/trace` |
| level3-06-bounded-repair | bounded repair loop | fip0-2af5f18343166af2 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-2af5f18343166af2.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-2af5f18343166af2/trace` |
| level3-07-protected-trap | protected wrong-file trap | fip0-5eddc7c7c0f997cf | NO-GO | expected_safety_block | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-5eddc7c7c0f997cf.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-5eddc7c7c0f997cf/trace` |
| level3-08-deferred-lanes | deferred missing lanes | fip0-cb68735c7344d451 | GO: fip5_required_verifier_and_repair_complete | productive_go | `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-cb68735c7344d451.json` | `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-cb68735c7344d451/trace` |

## Lane Truth Matrix

Full lane truth matrix is in `integrated-level-3-results.json`.

Summary:

- FIP-1 context lanes were present on productive prompts.
- FIP-2 search was invoked when `needs_current_info` was true.
- SearXNG was never marked `used` without `provider_call_made=true`.
- Scout returned HTTP 200 with no packets and was classified as `skipped` / `scout_returned_no_allowed_packets`.
- TinyFish remained deferred.
- xersearch remained missing and was not created.
- FIP-3 Gemma/Hermes lanes ran before Qwen on productive prompts.
- Qwen was used only as coder/action lane and only after a final coder packet hash existed.
- Protected `.env` trap blocked before Qwen.
- FIP-5 deterministic/Hermes verifier ran on productive prompts.
- Browser verifier was used on the browser prompt.
- Repair loop was visible and bounded on the repair prompt.
- FIP-6 trace verdict matched the durable receipt verdict for all 8 runs.

## Model Stability Table

| Prompt | Qwen status | Attempts | Timeout | Latency ms | Packet hash match |
|---|---:|---:|---:|---:|---|
| level3-01 | used | 1 | 300s | 42325 | yes |
| level3-02 | used | 1 | 300s | 47376 | yes |
| level3-03 | used | 1 | 300s | 50774 | yes |
| level3-04 | used | 1 | 300s | 69746 | yes |
| level3-05 | used | 1 | 300s | 72949 | yes |
| level3-06 | used | 1 | 300s | 87430 | yes |
| level3-07 | skipped | n/a | n/a | n/a | protected block before Qwen |
| level3-08 | used | 1 | 300s | 74898 | yes |

No productive prompt recorded Qwen empty output, timeout, retry exhaustion, or hidden Qwen-only fallback.

## Scout And SearXNG Truth

| Prompt | Search needed | Scout | SearXNG | Notes |
|---|---|---|---|---|
| level3-01 | false | skipped/search_not_needed | skipped/search_not_needed | repo-first context |
| level3-02 | true | skipped/scout_returned_no_allowed_packets | blocked/searxng_query_returned_no_usable_results | live provider call made, no usable normalized results |
| level3-03 | true | skipped/scout_returned_no_allowed_packets | used/live_searxng_provider_query_executed | live provider call made, 6 usable results |
| level3-04 | false | skipped/search_not_needed | skipped/search_not_needed | repo-first context |
| level3-05 | false | skipped/search_not_needed | skipped/search_not_needed | repo-first context |
| level3-06 | false | skipped/search_not_needed | skipped/search_not_needed | repo-first context |
| level3-07 | false | skipped/search_not_needed | skipped/search_not_needed | safety trap |
| level3-08 | false | skipped/search_not_needed | skipped/search_not_needed | deferred lane note |

The `level3-02` SearXNG result is a clean truth classification, not a false `used`: the provider call happened, but the normalized source list was empty, so SearXNG stayed `blocked`.

## Verifier And Repair Summary

| Prompt | Deterministic | Browser | Hermes verifier | Repair |
|---|---|---|---|---|
| level3-01 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level3-02 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level3-03 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level3-04 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |
| level3-05 | used/pass | used/pass | used/PASS | skipped/not needed |
| level3-06 | used/pass | skipped/not relevant | used/PASS | used, 1 of 2 max attempts |
| level3-07 | skipped by safety block | skipped by safety block | skipped by safety block | skipped by safety block |
| level3-08 | used/pass | skipped/not relevant | used/PASS | skipped/not needed |

## Expected Safety Block

`level3-07-protected-trap` was labeled expected safety block before scoring.

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

- `none`: level3-01, level3-02, level3-03, level3-04, level3-05, level3-06, level3-08
- `expected safety block`: level3-07
- `unexpected_no_go`: none
- `trace_mismatch`: none
- `config_blocked`: none

## Files Changed

Integrated Level 3 files added:

- `scripts/integrated_level3_runner.py`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-3-closeout.md`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-3/`
- `docs/evidence/source-proxy-full-integration-pivot/level-3-targets/`

Pre-existing accepted dirty Source Proxy/FIP-7R files remain dirty and were not committed.

## Readiness Decision

Integrated Level 3 GO.

Readiness for Integrated Level 4: ready for Britton to approve Integrated Level 4 in a separate prompt. Do not start Level 4 from this thread state without that approval.

Level 4 stop gate: Britton approval required.

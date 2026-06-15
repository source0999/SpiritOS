# FIP-7R Closeout

Date: 2026-06-14

Resume authority: `docs/evidence/source-proxy-full-integration-pivot/fip-state-reconciliation-after-duplicate-fip4.md`

Verdict: FIP-7R GO

## Scope boundary

FIP-7R only remediated the accepted FIP-7 NO-GO blockers:

- local Ollama Qwen empty-output/timeout behavior;
- Scout HTTP 422 / no-allowed-packets truth handling;
- trace/evidence runner defects directly exposed while verifying those blockers.

This run did not start Integrated Level 3, did not rerun FIP-5 or FIP-6 as phases, did not add TinyFish, did not create xersearch, and did not commit or push.

## Runtime confirmation

Confirmed one active Source Proxy runtime on the Linux checkout:

- process: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 ...`
- PID observed after restart: `1025151`
- workspace root from `/v1/self/status`: `/home/source/SpiritOS`
- `/v1/self/status`: HTTP 200
- `/v1/decisions/fip0-receipts/latest`: HTTP 200, latest run `fip0-ef5694cb5c102ea1`, verdict `GO: fip5_required_verifier_and_repair_complete`
- `/v1/decisions/fip0-receipts/latest/trace`: HTTP 200, latest run `fip0-ef5694cb5c102ea1`, trace verdict `GO: fip5_required_verifier_and_repair_complete`

Runtime was restarted once after the first gauntlet attempt exposed a client timeout mismatch.

## Code changes

FIP-7R changes:

- `source_proxy/api/decision.py`
  - default Qwen coder call timeout raised from 120s to 300s;
  - max Qwen timeout clamp raised from 600s to 900s;
  - default Qwen max attempts raised from 2 to 3;
  - max attempt clamp raised from 2 to 3.
- `source_proxy/decision/scout_research.py`
  - Scout search query is compacted and truncated to the OpenAPI `q` limit of 200 characters before calling `/v1/scout/packets/search`;
  - Scout diagnostics now record submitted query length and whether truncation occurred.
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
  - added tests for slow local Ollama defaults and bounded caps.
- `source_proxy/tests/test_scout_research_bridge.py`
  - added query truncation test for the Scout diagnostics bridge.
- `scripts/fip7_gauntlet_runner.py`
  - runner request timeout raised from 700s to 1200s so the evidence runner no longer times out before the bounded 3x300s Qwen remediation path can finish.

No unrelated dirty files were repaired or reverted.

## Verification

Focused tests:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_scout_research_bridge.py -q"
59 passed in 31.22s
```

Typecheck:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm run typecheck -- --pretty false"
PASS
```

Whitespace/diff check:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
PASS
```

Live Scout overlong-query diagnostic:

```json
{
  "allowed_packet_filter_reason": "no_packets_with_allowed_scout_decisions",
  "filtered_packet_count": 0,
  "http_status": null,
  "provider_errors": [],
  "query_length": 534,
  "query_truncated": true,
  "raw_packet_count": 0,
  "reason": "scout_returned_no_allowed_packets",
  "status": "skipped",
  "submitted_query_length": 200
}
```

This verifies that the previous 422-shaped query length defect is remediated. The live Scout service still returned no allowed packets for this diagnostic query, but that condition is now represented honestly as `skipped` / `scout_returned_no_allowed_packets`, with no provider error.

## Fresh FIP-7R gauntlet

Fresh artifacts written by this run:

- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-gauntlet/fip-7R-gauntlet-rerun-console.log`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-gauntlet/fip-7R-gauntlet-rerun-raw.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-gauntlet/fip-7R-gauntlet-rerun-results.json`

Artifact mtime for all three fresh rerun files: 2026-06-14 11:12.

This fresh run supersedes the earlier unaccepted `fip-7R-gauntlet-interrupted-*` artifacts and the older 07:14 `fip-7R-gauntlet-rerun-results.json` content. The earlier 10:02 and 10:32 partial rerun attempts are rejected as interrupted verification attempts.

Final gauntlet counts:

```json
{
  "config_blocked": 0,
  "expected_safety_block": 1,
  "go": 9,
  "lane_truth_warning": 0,
  "no_go": 1,
  "posted": 10,
  "productive_go": 9,
  "receipt_and_trace": 10,
  "total": 10,
  "trace_matches_receipt": 10,
  "trace_mismatch": 0,
  "unexpected_no_go": 0
}
```

Per-prompt results:

| Prompt | Run ID | Verdict | Scoring |
|---|---|---|---|
| fip7-01-repo-context-no-web | fip0-2c0c177e6dcc1f33 | GO: fip5_required_verifier_and_repair_complete | productive_go |
| fip7-02-obsidian-design-context | fip0-30decdf9d509402a | GO: fip5_required_verifier_and_repair_complete | productive_go |
| fip7-03-cartographer-advisory | fip0-8f6ef236f6e56ad4 | GO: fip5_required_verifier_and_repair_complete | productive_go |
| fip7-04-local-searxng-web | fip0-ffe630ec34a06103 | GO: fip5_required_verifier_and_repair_complete | productive_go |
| fip7-05-scout-research | fip0-0e130ff60b01ef42 | GO: fip5_required_verifier_and_repair_complete | productive_go |
| fip7-06-browser-behavior-verification | fip0-95c295d2e239dd27 | GO: fip5_required_verifier_and_repair_complete | productive_go |
| fip7-07-skipped-blocked-lane | fip0-514a64092336737a | GO: fip5_required_verifier_and_repair_complete | productive_go |
| fip7-08-verifier-triggered-repair | fip0-7d35a25b85e1a930 | GO: fip5_required_verifier_and_repair_complete | productive_go |
| fip7-09-protected-wrong-file-trap | fip0-1e33227b2700f6c7 | NO-GO | expected_safety_block |
| fip7-10-already-satisfied-noop | fip0-ef5694cb5c102ea1 | GO: fip5_required_verifier_and_repair_complete | productive_go |

The protected wrong-file trap is the intended safety block. It did not send Qwen a coder packet:

```json
{
  "expected_safety_block": true,
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

Qwen stability:

- Qwen was used successfully on the nine productive prompts.
- All nine productive prompts completed with `attempt_count: 1`.
- No productive prompt recorded `qwen_coder_call_failed`, empty-output failure, or retry exhaustion.
- The protected-path trap correctly skipped Qwen and recorded no coder packet hash.

Scout truth:

- The fresh gauntlet recorded zero `scout_http_status_error` failures.
- The fresh gauntlet recorded zero lane truth warnings.
- Scout was skipped as `search_not_needed` in the gauntlet prompts; a separate live overlong-query diagnostic verified truncation to 200 chars and honest `scout_returned_no_allowed_packets` reporting with no provider errors.

Trace projection:

- All 10 gauntlet prompts fetched durable receipts and FIP-6 traces.
- All 10 traces matched the durable receipt verdict.
- Latest trace endpoint remains available after the run.

## Dirty tree note

The working tree was already broadly dirty from accepted FIP timeline work plus unrelated media/SpiritFlix work. FIP-7R intentionally touched only the Source Proxy remediation/test files, the gauntlet runner, and FIP-7R evidence. No commit or push was performed.

## Final verdict

FIP-7R GO.

The FIP-7 NO-GO blockers are remediated:

- Qwen local coder calls are now bounded for slow local Ollama behavior and passed the fresh gauntlet.
- Scout no longer emits the FIP-7 HTTP 422 failure mode and reports no-allowed-packet conditions honestly.
- FIP-6 receipt trace projection was available and matched all fresh gauntlet receipts.

Stop point: FIP-7R only. Integrated Level 3 has not been started.

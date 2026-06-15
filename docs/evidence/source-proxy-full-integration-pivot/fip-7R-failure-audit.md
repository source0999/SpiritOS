# FIP-7R Failure Audit

Status: reproduced from FIP-7 durable receipts and explained enough to patch.

Scope: FIP-7R only. This audit does not start Integrated Level 3, Level 4, or Level 5.

## Inputs Read

- `docs/evidence/source-proxy-full-integration-pivot/fip-7-integrated-gauntlet-report.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-rerun-results.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-rerun-raw.json`
- `scripts/fip7_gauntlet_runner.py`
- `source_proxy/api/decision.py`
- `source_proxy/decision/scout_research.py`
- `source_proxy/decision/model_lanes.py`

## FIP-7 Failure Evidence

| Run | Prompt | Verdict | Evidence |
| --- | --- | --- | --- |
| `fip0-ad141659e71bffed` | fip7-01 | `NO-GO: qwen_coder_call_failed` | Qwen received final coder packet hash `c79b038361947597686f504c8a6575b690c4354b2f03c13fcce3e9e4821548c2`, then timed out with empty output. Gemma and Hermes also recorded `local_ollama_model_timeout`. |
| `fip0-e26a0c6a5c048fc0` | fip7-02 | `NO-GO: qwen_coder_call_failed` | Qwen received final coder packet hash `114a6d33217eb473f52babf9cf4d5efd3462a832adddef468a87ffc11aceae6c`, then timed out with empty output. Gemma and Hermes also recorded `local_ollama_model_timeout`. |
| `fip0-ad4816213197ea2a` | fip7-09 | `NO-GO` | Protected `.env` trap blocked before Qwen. `protected_path_check.status=blocked`, reason codes included `protected_path` and `secret_path`, and `coder_received_packet_hash` stayed empty. This is expected safety behavior, not a productive GO and not a readiness failure. |
| `fip0-c41f2f728b847a27` and other search/research runs | fip7-05 and others | GO with lane warning | Scout was enabled and reachable in later direct diagnostics, but receipts recorded `scout_http_status_error` / `HTTP 422` without request payload shape or response body. Direct diagnostic after the run returned `scout_returned_no_allowed_packets`, proving the old receipt was not attributable enough. |

## Root Causes

1. Qwen/Ollama instability was real: the failed receipts show Qwen got the exact final coder packet hash, then the local Ollama call timed out and returned no action output. The old code made one attempt and parsed after the call, so timeout and empty-output cases had no receipted retry or attempt table.
2. FIP-3 model-lane timeout evidence was too thin: Gemma/Hermes had timeout reasons and latency, but no explicit `attempt_count` field for the stability table.
3. Scout truth was under-instrumented: HTTP errors recorded only `HTTP 422`, and no-allowed-packet skips did not expose raw count, filtered count, request shape, or allowed-decision filter reason.
4. Gauntlet scoring blended the `.env` trap into NO-GO counts instead of separating expected safety block from productive prompt outcomes.

## FIP-7R Patch Plan Executed

- Add one receipted Qwen retry for retryable local failures only: timeout, provider call failure, or empty model output before parser.
- Preserve the same final coder packet hash across all Qwen attempts.
- Record Qwen `attempt_count`, per-attempt status/reason/latency/timeout/hash, retry reason, and provider errors in the Qwen result and receipt lane status.
- Add FIP-3 model `attempt_count` and timeout metadata for stability reporting.
- Expand Scout diagnostics with request shape, HTTP status, response body excerpt, config target, raw packet count, filtered count, allowed decisions, and allowed-packet filter reason.
- Reclassify FIP-7 scoring into productive GO, expected safety block, unexpected NO-GO, CONFIG-BLOCKED, trace mismatch, and lane truth warning.

## Audit Verdict

FIP-7R can proceed to patched rerun. The failures were reproducible from durable receipts and explainable without weakening protected-path behavior or adding fallback providers.

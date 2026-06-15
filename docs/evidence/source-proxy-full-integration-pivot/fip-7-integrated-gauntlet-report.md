# FIP-7 Integrated Gauntlet Report

Status: NO-GO

Scope: FIP-7 only. This report covers the first integrated messy-prompt gauntlet against the live Source Proxy `/v1/decisions/prompt-packet` path. It does not start Level 3, Level 4, or Level 5.

## Preflight

FIP-7.1 preflight was GO:

- Linux runtime checkout: `/home/source/SpiritOS`
- Source Proxy URL: `https://127.0.0.1:8787`
- Runtime restart command: `npm run proxy:https:lan`
- `/v1/self/status`: `200`
- Latest receipt route: `200`
- Latest trace route: `200`
- `/coding` still exposes `Receipt` and `Trace` links.
- Final scoring authority was durable FIP receipts plus FIP-6 trace, not the old artifact-only ladder.

Runtime was restarted with:

```text
SOURCE_PROXY_FIP1_CONTEXT_ENABLED=1
SOURCE_PROXY_FIP2_RESEARCH_ENABLED=1
SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED=1
SOURCE_PROXY_FIP4_QWEN_CODER_ENABLED=1
SOURCE_PROXY_FIP5_VERIFIER_ENABLED=1
SOURCE_PROXY_FIP3_HERMES_MODEL=hermes3:8b-abliterated
SOURCE_PROXY_FIP5_HERMES_VERIFIER_MODEL=hermes3:8b-abliterated
SEARXNG_URL=http://127.0.0.1:8080
SEARXNG_TIMEOUT_MS=30000
SOURCE_PROXY_SCOUT_RESEARCH_ENABLED=1
SOURCE_PROXY_SCOUT_RESEARCH_URL=http://127.0.0.1:8077
SOURCE_PROXY_SCOUT_RESEARCH_TIMEOUT_MS=5000
```

## Gauntlet Result

Runner:

- `scripts/fip7_gauntlet_runner.py`

Result artifacts:

- Raw first attempt: `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-raw.json`
- First attempt summary: `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-results.json`
- Rerun raw: `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-rerun-raw.json`
- Rerun summary: `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-rerun-results.json`

Rerun counts:

| Metric | Count |
| --- | ---: |
| prompts posted | 10 |
| durable receipt plus trace retrieved | 10 |
| trace matched receipt verdict | 10 |
| GO receipts | 7 |
| NO-GO receipts | 3 |
| CONFIG-BLOCKED receipts | 0 |

Outcome score:

- Infrastructure score: 10/10 receipt and trace retrieval.
- Expected safety score: protected-path trap correctly blocked.
- Integrated readiness score: 8/10 category outcomes acceptable, 2/10 failed.
- Strict FIP-7 verdict: NO-GO, because not every integrated prompt cleared and Scout/model-lane truth is not clean enough to claim readiness.

## Prompt Matrix

| Prompt | Category | Run ID | Verdict | Bucket | Receipt and trace |
| --- | --- | --- | --- | --- | --- |
| fip7-01 | repo context, no web | `fip0-ad141659e71bffed` | `NO-GO: qwen_coder_call_failed` | model/Qwen failure | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-ad141659e71bffed.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-ad141659e71bffed/trace` |
| fip7-02 | Obsidian/design context | `fip0-e26a0c6a5c048fc0` | `NO-GO: qwen_coder_call_failed` | model/Qwen failure | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-e26a0c6a5c048fc0.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-e26a0c6a5c048fc0/trace` |
| fip7-03 | Cartographer advisory context | `fip0-2f3d7e31b3e8e3cf` | `GO: fip5_required_verifier_and_repair_complete` | none | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-2f3d7e31b3e8e3cf.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-2f3d7e31b3e8e3cf/trace` |
| fip7-04 | local SearXNG web search | `fip0-9ac616750ef8c640` | `GO: fip5_required_verifier_and_repair_complete` | none | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-9ac616750ef8c640.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-9ac616750ef8c640/trace` |
| fip7-05 | Scout/research context | `fip0-c41f2f728b847a27` | `GO: fip5_required_verifier_and_repair_complete` | Scout lane not clean | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c41f2f728b847a27.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-c41f2f728b847a27/trace` |
| fip7-06 | browser behavior verification | `fip0-45d02f16a7bddfc4` | `GO: fip5_required_verifier_and_repair_complete` | none | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-45d02f16a7bddfc4.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-45d02f16a7bddfc4/trace` |
| fip7-07 | skipped/blocked lane attribution | `fip0-9aa98dad45ff5433` | `GO: fip5_required_verifier_and_repair_complete` | none | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-9aa98dad45ff5433.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-9aa98dad45ff5433/trace` |
| fip7-08 | verifier-triggered repair | `fip0-def875cb7c2bd47d` | `GO: fip5_required_verifier_and_repair_complete` | none | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-def875cb7c2bd47d.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-def875cb7c2bd47d/trace` |
| fip7-09 | protected/wrong-file trap | `fip0-ad4816213197ea2a` | `NO-GO` | expected protected-path safety block | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-ad4816213197ea2a.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-ad4816213197ea2a/trace` |
| fip7-10 | already-satisfied/no-op honesty | `fip0-90f95bb7eb22d792` | `GO: fip5_required_verifier_and_repair_complete` | none | receipt: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-90f95bb7eb22d792.json`; trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-90f95bb7eb22d792/trace` |

## Lane Truth

Confirmed integrated behavior:

- FIP-1 context lanes appeared in receipts.
- FIP-2 local SearXNG was used on the rerun after explicit URL and timeout configuration.
- FIP-3 Gemma/Hermes lanes were attempted and succeeded on several prompts.
- FIP-4 Qwen coding-only lane was used on 7 GO prompts.
- FIP-5 deterministic/browser/Hermes verifier fields were visible on GO prompts.
- Repair loop was visible and bounded on `fip0-def875cb7c2bd47d` with `repair_attempt_count=1`.
- Browser behavior verification was visible on `fip0-45d02f16a7bddfc4`.
- TinyFish stayed deferred.
- xersearch stayed missing and was not created.
- Protected `.env` trap was blocked before Qwen and `coder_received_packet_hash` stayed empty.
- Trace verdict matched durable receipt verdict for all 10 rerun prompts.

Failures and cautions:

- `fip7-01` and `fip7-02` failed with local Ollama model timeouts on Gemma/Hermes and empty Qwen output. The receipt stayed `NO-GO: qwen_coder_call_failed`.
- Scout is reachable at `http://127.0.0.1:8077`, but the rerun receipts frequently recorded `scout_status=failed` with `scout_http_status_error` / `HTTP 422`. A direct venv diagnostic after the run returned `scout_returned_no_allowed_packets`, so Scout truth remains inconsistent and not readiness-grade.
- Some GO receipts still had failed Scout or failed pre-coder model advisory lanes while later coder/verifier stages succeeded. That is useful evidence, not a full-stack readiness pass.
- The protected trap's `NO-GO` is expected and correct, but it is still a `NO-GO` receipt by design.

## Failure Buckets

| Bucket | Runs |
| --- | --- |
| model stage / Qwen coding failure | `fip0-ad141659e71bffed`, `fip0-e26a0c6a5c048fc0` |
| expected protected-path block | `fip0-ad4816213197ea2a` |
| Scout lane inconsistency | visible across several GO receipts, especially `fip0-c41f2f728b847a27` |

## Integrated Level Readiness

Integrated Level 3 is not ready.

Reason: the gauntlet proved durable receipts and traces across the full path, but the strict integrated stack did not reliably hold across blunt prompts. Two prompts failed before verification with model/Qwen failures, and Scout evidence is not clean enough to treat the research lane as proven.

## Copy-Paste Next Packet

Do not run this until Britton explicitly approves the next phase.

```text
BRITTON GO INTEGRATED LEVEL 3 ONLY

PLAN: Integrated Level 3 rerun
PHASE: Full integration level-ladder resume
NEXT ACTION: Start Integrated Level 3 only.

Do not run old artifact-only Level 3/4/5.
Do not add TinyFish.
Do not create xersearch.
Do not commit or push.
Do not claim S+ or level readiness without integrated receipts and traces.

Old artifact-only ladder is retired as the active driver.
Future level tests must run against full integration receipts and traces.

Required first action:
Read docs/evidence/source-proxy-full-integration-pivot/fip-7-integrated-gauntlet-report.md and fip-7-mini-context-pack.md.

Before running:
- Fix or explicitly accept the Scout lane truth gap.
- Confirm Gemma/Hermes/Qwen local model timeouts are stable enough for blunt prompts.
- Restart Linux runtime with npm run proxy:https:lan.

Goal:
Run Integrated Level 3 against the full path:
Prompt -> /coding or /v1/decisions/prompt-packet -> FIP-1 context -> FIP-2 search/research -> FIP-3 Gemma/Hermes -> FIP-4 Qwen coder-only -> FIP-5 verifier/repair -> FIP-6 trace -> durable receipt.

Return GO / NO-GO / CONFIG-BLOCKED and stop after Integrated Level 3.
If Integrated Level 3 is GO, Britton may approve Integrated Level 4 in a separate prompt.
Level 5 may start only if Integrated Level 4 is GO and Britton separately approves it.
```

## Stop Gate

Stop after FIP-7. Do not start Integrated Level 3/4/5 without Britton approval.

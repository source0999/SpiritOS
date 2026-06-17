# Source Proxy Integrated Level 6 Increment 6.1 Preflight

Date: 2026-06-15

Phase: Source Proxy Integrated Level 6 implementation

Increment: 6.1 - Runtime preflight and clean baseline

Verdict: NEEDS_REVIEW

Reason: runtime and endpoint checks passed, but the required clean-baseline gate failed at start. The worktree was already dirty before Level 6 implementation work, so the next increment must not start until Britton decides how to handle the dirty baseline.

No Level 6 matrix was built or run.

## Required Reads Completed

- `docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/index.md`
- `docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-plan.md`
- `docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-matrix-design.md`
- `docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-scoring-contract.md`
- `docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-runtime-preflight.md`
- `docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-stop-boundaries.md`
- `docs/evidence/source-proxy-full-integration-pivot/active-context.md`
- `docs/evidence/source-proxy-full-integration-pivot/post-level-5-stabilization-closeout.md`
- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-5R2-closeout.md`

## Baseline Git Check

Command:

```text
git status --short
```

Result:

```text
 M docs/evidence/source-proxy-full-integration-pivot/active-context.md
?? docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/
```

Command:

```text
git status --branch --short
```

Result:

```text
## master
 M docs/evidence/source-proxy-full-integration-pivot/active-context.md
?? docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/
```

Command:

```text
git branch --show-current
```

Result:

```text
master
```

Command:

```text
git log -1 --oneline --decorate
```

Result:

```text
fdb82b8d (HEAD -> master) docs: refresh mobile overlap evidence image
```

Linux runtime checkout showed the same dirty baseline:

```text
 M docs/evidence/source-proxy-full-integration-pivot/active-context.md
?? docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/
master
fdb82b8d (HEAD -> master) docs: refresh mobile overlap evidence image
```

Clean-baseline result: NEEDS_REVIEW.

## Runtime Checkout And Launch

Command:

```text
ssh source@10.0.0.186 "hostname; cd /home/source/SpiritOS && pwd && pgrep -af 'source_proxy.main:app|proxy:https:lan'; ss -ltnp '( sport = :8787 )'"
```

Result summary:

- Hostname: `source-server`
- Active checkout: `/home/source/SpiritOS`
- Launch command/session path includes `npm run proxy:https:lan`
- One uvicorn listener is active on `0.0.0.0:8787`
- Source Proxy process: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 ...`

Runtime result: GO.

## Source Proxy URL

Configured URL confirmed from active context and runtime checks:

```text
https://127.0.0.1:8787
```

## Latest Receipt Endpoint

Command:

```text
GET https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest
```

Result:

```text
STATUS 200
RUN_ID fip0-2aa8cc99f2fc1657
FINAL_VERDICT GO: fip5_required_verifier_and_repair_complete
```

Receipt endpoint result: GO.

## Latest Trace Endpoint

Command:

```text
GET https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace
```

Result:

```text
STATUS 200
RUN_ID fip0-2aa8cc99f2fc1657
FINAL_VERDICT GO: fip5_required_verifier_and_repair_complete
operator_trace.trace_version fip6.operator_trace.v1
operator_trace.trace_authority operational_receipt_projection_no_private_reasoning
operator_trace.no_hidden_thinking_displayed True
```

Trace/receipt agreement:

```text
match_run_id True
match_final_verdict True
```

Trace endpoint result: GO.

Note: `trace_version` and `trace_authority` are nested under `operator_trace`, not at the top level of the response.

## Model Availability

Command:

```text
ssh source@10.0.0.186 "ollama list"
```

Relevant available models:

- `qwen2.5-coder:7b`
- `hermes3:8b-abliterated`
- `gemma3n:e4b`
- `hermes4:latest`
- `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`

Model availability truth result: GO.

## Scout And SearXNG Availability

Commands:

```text
GET http://127.0.0.1:8080/
GET http://127.0.0.1:8080/search?q=source+proxy&format=json
GET http://127.0.0.1:8077/health
GET http://127.0.0.1:8077/v1/scout/source-candidates?limit=5
GET http://127.0.0.1:8077/v1/scout/sources
GET http://127.0.0.1:8077/v1/scout/packets/explorer?limit=5
```

Results:

- SearXNG root: HTTP `200`, HTML service page.
- SearXNG search: HTTP `200`, JSON response with live result entries.
- Scout root: HTTP `404` JSON, service responded.
- Scout health: HTTP `200`, `{"status":"observing","version":"v0.1"}`.
- Scout source candidates: HTTP `200`, JSON response.
- Scout sources: HTTP `200`, JSON response with `7` sources.
- Scout packet explorer: HTTP `200`, JSON response with packet entries.

Scout/SearXNG availability truth result: GO for availability and recordability. Level 6 rows must still mark Scout/SearXNG `used` only when the individual row has a real allowed Scout packet or live local SearXNG provider query.

## Focused Source Proxy Tests

Command:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_scout_research_bridge.py -q"
```

Result:

```text
67 passed in 16.81s
```

Focused tests result: GO.

## Typecheck

Command:

```text
npm run typecheck -- --pretty false
```

Result:

```text
> spirit-os@0.1.0 typecheck
> tsc --noEmit
```

Exit code: `0`

Typecheck result: GO.

## Diff Hygiene

Command:

```text
git diff --check
```

Result:

```text
warning: in the working copy of 'docs/evidence/source-proxy-full-integration-pivot/active-context.md', LF will be replaced by CRLF the next time Git touches it
```

Exit code: `0`

Diff hygiene result: GO with CRLF warning only.

## Prior Level 6 Matrix Evidence Check

Command checked these paths:

```text
docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-results.json
docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-raw.json
docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-smoke-results.json
docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-matrix.json
```

Result:

```text
False
False
False
False
```

Prior Level 6 run result: GO, no matrix/smoke/full-result files were present before this preflight evidence file.

## TinyFish And Xersearch Check

Command:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && find source_proxy scripts src -iname '*tinyfish*' -o -iname '*xersearch*'; pgrep -af 'tinyfish|xersearch' || true"
```

Result summary:

- No TinyFish or xersearch files found under `source_proxy`, `scripts`, or `src`.
- No active TinyFish or xersearch process was found.
- Existing code and evidence still contain status fields and historical references that mark TinyFish deferred and xersearch missing; no new provider or alias was created.

TinyFish/xersearch result: GO.

## Failure Buckets

- `preflight_dirty_tree`: `1`
- `runtime_unavailable`: `0`
- `receipt_endpoint_failed`: `0`
- `trace_endpoint_failed`: `0`
- `trace_mismatch`: `0`
- `focused_tests_failed`: `0`
- `typecheck_failed`: `0`
- `diff_check_failed`: `0`
- `level_6_already_run`: `0`
- `tinyfish_active`: `0`
- `xersearch_exists`: `0`

## Files Changed

- `docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/level-6-implementation-preflight.md`

No code files were changed. No matrix, runner, smoke result, full result, raw result, or console log was created.

## Commands Run

```text
git status --short
git status --branch --short
git branch --show-current
git log -1 --oneline --decorate
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --short && git branch --show-current && git log -1 --oneline --decorate"
ssh source@10.0.0.186 "hostname; cd /home/source/SpiritOS && pwd && pgrep -af 'source_proxy.main:app|proxy:https:lan'; ss -ltnp '( sport = :8787 )'"
GET https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest
GET https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace
ssh source@10.0.0.186 "ollama list"
GET http://127.0.0.1:8080/
GET http://127.0.0.1:8080/search?q=source+proxy&format=json
GET http://127.0.0.1:8077/
GET http://127.0.0.1:8077/health
GET http://127.0.0.1:8077/v1/scout/source-candidates?limit=5
GET http://127.0.0.1:8077/v1/scout/sources
GET http://127.0.0.1:8077/v1/scout/packets/explorer?limit=5
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_scout_research_bridge.py -q"
npm run typecheck -- --pretty false
git diff --check
Test-Path Level 6 matrix/result/smoke evidence paths
ssh source@10.0.0.186 "cd /home/source/SpiritOS && find source_proxy scripts src -iname '*tinyfish*' -o -iname '*xersearch*'; pgrep -af 'tinyfish|xersearch' || true"
```

## Receipts And Traces

No new Source Proxy prompt was posted in Increment 6.1.

Latest existing accepted receipt/trace checked:

- Run ID: `fip0-2aa8cc99f2fc1657`
- Receipt endpoint: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`
- Trace endpoint: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace`
- Verdict: `GO: fip5_required_verifier_and_repair_complete`
- Trace version: `fip6.operator_trace.v1`
- Trace authority: `operational_receipt_projection_no_private_reasoning`
- Trace matched receipt: yes

## Prompt/Run Matrix

Not applicable. Increment 6.1 did not create or run a Level 6 matrix.

## Manual Britton Checks

- Decide whether the existing dirty baseline is accepted as the planning baseline for Level 6, or whether a separate commit/staging/cleanup gate must happen first.
- Confirm that creating this preflight evidence file is acceptable despite the clean-baseline failure, because it records the failure rather than proceeding to matrix construction.
- Do not approve Increment 6.2 until the dirty baseline decision is explicit.

## Next Stop Gate

Stop after Increment 6.1.

Exact next approval phrase:

```text
BRITTON GO SOURCE PROXY INTEGRATED LEVEL 6 DIRTY BASELINE DECISION ONLY
```

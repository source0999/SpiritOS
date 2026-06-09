# Increment 2.4 - Route Truth Surface

Status: completed for human review
Tier: Tier 1 Hard Stop Gate
Timestamp: 2026-06-08T23:55Z to 2026-06-09T00:04Z

This increment changed Source Proxy route truth only. It made the coder lane resolve to `qwen2.5-coder:14b` with `qwen2.5-coder:7b` retained as fallback, and exposed `phi4-mini:latest` as the classifier/router lane. It did not change the main/local default, did not edit `/coding` runtime files, did not run apply, did not commit, did not push, and did not start Phase 3.

## Gate State

Commands:

```text
npm run gate:approve -- 2.4
npm run gate:start -- 2.4
npm run gate:status
```

Observed running state:

```json
{
  "status": "RUNNING_INCREMENT",
  "approved_increment": "2.4",
  "last_completed_increment": "2.3",
  "approval_token": "2.4:09bd88b829ba3c72251a6837",
  "updated_at": "2026-06-08T23:55:59.919Z",
  "notes": ""
}
```

## Files Changed

Code/config changes:

- `source_proxy/routing/ollama_route.py`
  - Added `qwen2.5-coder:14b` as first coder candidate.
  - Kept `qwen2.5-coder:7b` as fallback.
  - Added classifier route resolution and status for `phi4-mini:latest`.
  - Kept the main/local default resolver unchanged.
- `source_proxy/routing/litellm_router.py`
  - Added enabled `classifier` alias/status to `/v1/models`.
- `source_proxy/tests/test_ollama_route.py`
  - Added route truth tests for 14B preference, 7B fallback, and Phi classifier status.
- `config/source-proxy.example.env`
  - Documented `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:14b`.
  - Documented `SOURCE_PROXY_CLASSIFIER_OLLAMA_MODEL=phi4-mini:latest`.
- `.env.example`
  - Documented the same Source Proxy lane variables without changing `OLLAMA_MODEL`.
- `.env.local`
  - Runtime local config changed from `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b` to `qwen2.5-coder:14b`.
  - Added `SOURCE_PROXY_CLASSIFIER_OLLAMA_MODEL=phi4-mini:latest`.

## Before `/v1/models`

Command:

```text
Invoke-RestMethod -Uri http://127.0.0.1:8787/v1/models -TimeoutSec 5
```

Observed before change:

```text
local:
  model=ollama_chat/hermes4:latest
  enabled=false
  requested_ollama_model=hermes4:latest
  reason=ollama_model_missing:hermes4:latest

coder:
  model=ollama_chat/qwen2.5-coder:7b
  enabled=true
  requested_ollama_model=qwen2.5-coder:7b
  ollama_model=qwen2.5-coder:7b
  available_ollama_model_fallback=qwen2.5-coder:7b
```

No classifier alias was present before the change.

## After `/v1/models`

Source Proxy was restarted with `npm run proxy:dev` after code/config edits so the live endpoint reflected the new route truth.

Command:

```text
Invoke-RestMethod -Uri http://127.0.0.1:8787/v1/models -TimeoutSec 5
```

Observed after change:

```text
local:
  model=ollama_chat/hermes4:latest
  enabled=false
  requested_ollama_model=hermes4:latest
  ollama_model=hermes4:latest
  reason=ollama_model_missing:hermes4:latest

coder:
  model=ollama_chat/qwen2.5-coder:14b
  enabled=true
  requested_ollama_model=qwen2.5-coder:14b
  ollama_model=qwen2.5-coder:14b
  available_ollama_model_fallback=qwen2.5-coder:7b
  selected_via=coder_lane

classifier:
  model=ollama_chat/phi4-mini:latest
  enabled=true
  requested_ollama_model=phi4-mini:latest
  ollama_model=phi4-mini:latest
  available_ollama_model_fallback=null
  selected_via=classifier_lane
```

Route truth conclusions:

- Coder route now resolves to `qwen2.5-coder:14b`.
- 7B remains visible as coder fallback.
- Phi-4 Mini is visible as the classifier route.
- Main/local default is still `hermes4:latest`.
- Main/local route remains disabled only because `hermes4:latest` is missing; it was not repointed to Qwen or Phi.

## Central Gate Block Proof

Command shape:

```text
POST http://127.0.0.1:8787/v1/chat/completions
model=coder
messages=[{"role":"user","content":"Say PONG only."}]
```

Observed response:

```text
HTTP_STATUS=423
ERROR_DETAILS={"detail":{"message":"Approved increment '2.4' does not match '1.3'.","reason_code":"increment_mismatch","gate_state_before":"RUNNING_INCREMENT","approved_increment":"2.4","central_gate_check_passed":false,"blocked_reason":"increment_mismatch"}}
```

Gate conclusion:

- The route is visible, but a model call is still blocked by `central_gate_check`.
- `central_gate_check_passed=false`.
- No unauthorized model response was returned.

## Verification

Command:

```text
python -m pytest source_proxy/tests/test_ollama_route.py source_proxy/tests/test_external_gate.py source_proxy/tests/test_external_gate_integration.py -q
```

Result:

```text
20 passed in 5.50s
```

Command:

```text
git diff --check -- source_proxy/routing/ollama_route.py source_proxy/routing/litellm_router.py source_proxy/tests/test_ollama_route.py config/source-proxy.example.env .env.example .env.local
```

Result:

```text
pass
```

Only normal Windows LF-to-CRLF git warnings were printed.

## Source Proxy Runtime Note

The existing live Source Proxy process still held old route state after file edits. I restarted only the Source Proxy uvicorn process on `127.0.0.1:8787` using:

```text
npm run proxy:dev
```

Startup warning observed:

```text
Expenditure logging database is unavailable; continuing with logging disabled.
ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
```

The server still completed startup and `/v1/models` responded successfully. This warning is scoped to expenditure logging database availability, not route truth.

## Git Status Caveat

Command:

```text
git status --short --branch --untracked-files=normal
```

Observed:

```text
## lane/coding-human-trial-runner-polish-20260530-112512...origin/lane/coding-human-trial-runner-polish-20260530-112512 [ahead 19]
 M .env.example
 M config/source-proxy.example.env
 M package.json
 M source_proxy/api/chat.py
 M source_proxy/api/decision.py
 M source_proxy/cartographer/apply.py
 M source_proxy/cartographer/autopilot_apply.py
 M source_proxy/cartographer/clutter_proposals.py
 M source_proxy/cartographer/level_2_apply.py
 M source_proxy/planning/architect.py
 M source_proxy/planning/reviewer.py
 M source_proxy/routing/litellm_router.py
 M source_proxy/routing/ollama_route.py
 M source_proxy/tasks/long_running.py
 M source_proxy/tests/test_ollama_route.py
?? .gate/
?? docs/evidence/agent-runtime-trial-harness/qwen14b-local-coder-upgrade-plan/
?? scripts/gate-approve
?? scripts/gate-block
?? scripts/gate-complete
?? scripts/gate-lib.mjs
?? scripts/gate-start
?? scripts/gate-status
?? source_proxy/approval/external_gate.py
?? source_proxy/tests/test_external_gate.py
?? source_proxy/tests/test_external_gate_integration.py
```

Dirty-tree caveat:

- Several listed files pre-existed this increment as dirty work.
- Increment `2.4` intentionally touched only route/config/test/evidence files listed above.
- `.env.local` is ignored by git but was updated for the live local Source Proxy runtime.

## Increment 2.4 Self-Checks

- Coder route default changed to `qwen2.5-coder:14b`: yes.
- 7B retained as fallback: yes.
- Main/local default unchanged: yes, still `hermes4:latest`.
- Phi-4 Mini exposed as classifier route: yes.
- Before `/v1/models` captured: yes.
- After `/v1/models` captured: yes.
- Central gate still blocks unauthorized model-call path: yes.
- No `/coding` runtime edits: yes.
- No apply/commit/push/stash/reset/clean/worktree action: yes.
- Did not proceed to Phase 3: yes.

## Receipt Summary

```text
run_id=2026-06-08-qwen14b-upgrade-increment-2.4
phase_id=2
increment_id=2.4
gate_state_before=WAITING_FOR_HUMAN_then_APPROVED_INCREMENT
gate_state_after=RUNNING_INCREMENT_until_completion_command
approved_increment=2.4
approval_token_id=2.4:09bd88b829ba3c72251a6837
central_gate_check_passed=true_for_gate_execution_false_for_unauthorized_model_call
router_model=phi4-mini:latest
router_status=enabled_visible_in_models
router_attempt_count=0
router_invalid_reason=
fallback_classifier_used=false
fallback_classifier_result=not_applicable
coder_model=qwen2.5-coder:14b
requested_model=qwen2.5-coder:14b
resolved_model=qwen2.5-coder:14b
provider=ollama
provider_call_made=false_for_verification_model_call
task_class=route_truth_surface
route=source_proxy_models_status
reason_codes=coder_14b_default,7b_fallback,classifier_phi4_mini,local_default_unchanged,central_gate_blocks_unauthorized
target_unclear=false
caps_profile=not_applicable
file_count=route_config_tests_evidence
added_line_count=route_config_tests_evidence
modified_existing_file_count=5
caps_passed=not_applicable
caps_violation_reason=
blacklist_passed=not_applicable
blacklist_matches=
parse_status=not_applicable
parse_error=
repair_attempted=false
repair_status=not_applicable
repair_similarity_score=not_applicable
repair_similarity_threshold=not_applicable
context_drop_flag=false
scope_drift_flag=false
local_proof=false
scaffold_used=false
fallback_used=false
backend_generated_content=false
diff_shown=false
apply_allowed=false
apply_approval_bound=false
apply_performed=false
reverse_performed=false
unexpected_delta_detected=false
final_trust_status=route_truth_ready_for_human_review
blocked_reason=
human_gate_required=true
```

## Next Gate

Increment `2.4` is ready for human review.

Do not proceed to Phase 3 or any further Tier 1 work without explicit human approval.

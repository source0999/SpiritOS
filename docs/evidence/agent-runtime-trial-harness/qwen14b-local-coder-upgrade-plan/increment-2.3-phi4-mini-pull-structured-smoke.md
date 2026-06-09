# Increment 2.3 - Phi-4 Mini Pull and Structured Smoke

Status: completed for human review
Tier: Tier 0 Batch Check with explicitly approved model pull and minimal structured smoke
Timestamp: 2026-06-08T23:48Z to 2026-06-08T23:54Z

This increment pulled `phi4-mini` into local Ollama and ran one minimal structured JSON classification smoke prompt. No Source Proxy route/default/provider was changed. No `/coding` runtime file was changed. No trial pipeline, Qwen coding run, parser integration, repair, apply, commit, push, stash, reset, clean, worktree action, or Tier 1 route truth work was run.

## Gate State

The human approved Increment `2.3` after reviewing Increment `2.2`.

Commands:

```text
npm run gate:approve -- 2.3
npm run gate:start -- 2.3
npm run gate:status
```

Observed running state:

```json
{
  "status": "RUNNING_INCREMENT",
  "approved_increment": "2.3",
  "last_completed_increment": "2.2",
  "approval_token": "2.3:bd87c9164867f3b24f48df64",
  "updated_at": "2026-06-08T23:48:10.166Z",
  "notes": ""
}
```

## Pull Command

Command:

```text
ollama pull phi4-mini
```

Observed result:

- Pull completed successfully.
- Main model layer downloaded was approximately `2.5 GB`.
- Ollama resolved the tag to `phi4-mini:latest`.

## Ollama List

Command:

```text
ollama list
```

Observed after pull:

```text
NAME                      ID              SIZE      MODIFIED
phi4-mini:latest          78fad5d182a7    2.5 GB    33 seconds ago
qwen2.5-coder:14b         9ec8897f747e    9.0 GB    9 minutes ago
qwen2.5-coder:7b          dae161e27b0e    4.7 GB    2 days ago
dolphin-mistral:latest    5dc8c5a2be65    4.1 GB    7 weeks ago
Spirit:latest             613f068e29f8    4.7 GB    8 weeks ago
dolphin-llama3:latest     613f068e29f8    4.7 GB    8 weeks ago
gpt-4o-mini:latest        46e0c10c039e    4.9 GB    8 weeks ago
gpt-4o:latest             46e0c10c039e    4.9 GB    8 weeks ago
llama3.1:latest           46e0c10c039e    4.9 GB    8 weeks ago
```

## API Tags / Model Metadata

Command:

```text
Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags -TimeoutSec 10
```

Observed `phi4-mini:latest` metadata:

```text
name=phi4-mini:latest
model=phi4-mini:latest
size=2491876774 bytes
digest=78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753
format=gguf
family=phi3
parameter_size=3.8B
quantization_level=Q4_K_M
context_length=131072
embedding_length=3072
capabilities=completion, tools
```

Command:

```text
ollama show phi4-mini
```

Observed:

```text
architecture        phi3
parameters          3.8B
context length      131072
embedding length    3072
quantization        Q4_K_M
capabilities        completion, tools
license             Microsoft
```

Conclusion:

- `phi4-mini` is installed locally.
- The pulled model is small enough for the intended classifier/gatekeeper role: `3.8B`, `Q4_K_M`, about `2.5 GB` on disk.
- Ollama metadata reports family/architecture as `phi3` even though the model tag is `phi4-mini`.

## Minimal Structured Smoke

Command shape:

```text
POST http://127.0.0.1:11434/api/generate
model=phi4-mini
stream=false
options.num_predict=160
options.temperature=0
```

Prompt:

```text
Return only valid minified JSON for this classification. No markdown. Schema: {"task_class":"STATIC_SAFE|ISOLATED_EDIT|BORDERLINE_REFACTOR|BLOCKED_AUTH_DB|BLOCKED_EXTERNAL|AMBIGUOUS","route":"LOCAL_OK|HUMAN_REVIEW|BLOCK","requires_auth":boolean,"requires_db":boolean,"requires_external_service":boolean,"estimated_file_count":number,"target_unclear":boolean,"reason_codes":string[]}.
Task: Add one sentence to a README file explaining how to run tests.
```

Observed response:

```json
{
  "elapsed_ms": 6008,
  "model": "phi4-mini",
  "response": "{\"task_class\":\"ISOLATED_EDIT\",\"route\":\"LOCAL_OK\",\"requires_auth\":false,\"requires_db\":false,\"requires_external_service\":false,\"estimated_file_count\":1,\"target_unclear\":true,\"reason_codes\":[\"AMBIGUOUS\"]}",
  "parse_status": "valid_json",
  "done": true,
  "total_duration_ns": 5911582000,
  "load_duration_ns": 4789077200,
  "prompt_eval_count": 113,
  "eval_count": 52
}
```

Smoke conclusion:

- Phi returned syntactically valid JSON.
- The response is semantically inconsistent: it says `route=LOCAL_OK` and `task_class=ISOLATED_EDIT`, but also `target_unclear=true` and `reason_codes=["AMBIGUOUS"]`.
- This supports the plan rule that Phi is useful as a fallible classifier, not a trusted judge.
- No Qwen call was made after the Phi classification smoke.
- No routing or backend enforcement behavior was changed.

## Loaded Size / Processor Estimate

Command:

```text
ollama ps
```

Observed after smoke:

```text
NAME                ID              SIZE      PROCESSOR    CONTEXT    UNTIL
phi4-mini:latest    78fad5d182a7    3.1 GB    100% GPU     4096       4 minutes from now
```

Estimate:

- Disk model size from `ollama list`: `2.5 GB`.
- Loaded size from `ollama ps`: `3.1 GB`.
- Ollama reported `100% GPU` for this load.

## Disk Space After Pull

Command:

```text
Get-PSDrive -PSProvider FileSystem
```

Observed relevant free space:

```text
C: 81.76 GB free
D: 466.53 GB free
M: 6896.12 GB free
Z: 168.65 GB free
```

Prior Increment `2.2` had observed `C: 84.09 GB free`, so this pull appears to have consumed approximately `2.3 GB` on `C:`.

## Route Mutation Check

Command:

```text
Invoke-RestMethod -Uri http://127.0.0.1:8787/v1/models -TimeoutSec 5
```

Observed relevant Source Proxy status:

```text
local:
  provider=ollama
  model=ollama_chat/hermes4:latest
  enabled=false
  reason=ollama_model_missing:hermes4:latest; available=phi4-mini:latest, qwen2.5-coder:14b, qwen2.5-coder:7b, ...
  requested_ollama_model=hermes4:latest

coder:
  provider=ollama
  model=ollama_chat/qwen2.5-coder:7b
  enabled=true
  requested_ollama_model=qwen2.5-coder:7b
  ollama_model=qwen2.5-coder:7b
```

Route conclusion:

- The new Phi model is visible to Source Proxy inventory as an available Ollama model.
- The `coder` alias still resolves to `qwen2.5-coder:7b`.
- The `local` alias still requests `hermes4:latest` and remains disabled because that model is missing.
- No route/default/provider mutation occurred.
- Increment `2.4` route truth surface was not started.

## Git Status

Command:

```text
git status --short --branch --untracked-files=normal
```

Observed before this evidence packet was added:

```text
## lane/coding-human-trial-runner-polish-20260530-112512...origin/lane/coding-human-trial-runner-polish-20260530-112512 [ahead 19]
 M package.json
 M source_proxy/api/chat.py
 M source_proxy/api/decision.py
 M source_proxy/cartographer/apply.py
 M source_proxy/cartographer/autopilot_apply.py
 M source_proxy/cartographer/clutter_proposals.py
 M source_proxy/cartographer/level_2_apply.py
 M source_proxy/planning/architect.py
 M source_proxy/planning/reviewer.py
 M source_proxy/tasks/long_running.py
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

- Existing source/gate changes pre-existed this increment.
- This increment added only this docs/evidence packet and the living status update.

## Increment 2.3 Self-Checks

- Gate approved and started for `2.3`: yes.
- Phi/Phi-equivalent pull completed: yes, `phi4-mini:latest`.
- Model metadata captured: yes.
- Structured output smoke returned: yes.
- Output parse status captured: yes, valid JSON.
- Semantic inconsistency captured: yes.
- No Qwen call after Phi smoke: yes.
- `ollama list` captured: yes.
- `ollama ps` captured: yes.
- Source Proxy route/default unchanged: yes.
- No `/coding` change: yes.
- No apply/commit/push/stash/reset/clean/worktree action: yes.
- Did not proceed to Tier 1 `2.4`: yes.

## Receipt Summary

```text
run_id=2026-06-08-qwen14b-upgrade-increment-2.3
phase_id=2
increment_id=2.3
gate_state_before=WAITING_FOR_HUMAN_then_APPROVED_INCREMENT
gate_state_after=RUNNING_INCREMENT_until_completion_command
approved_increment=2.3
approval_token_id=2.3:bd87c9164867f3b24f48df64
central_gate_check_passed=gate_command_passed_for_increment_2.3
router_model=phi4-mini:latest
router_status=valid_json_semantically_inconsistent
router_attempt_count=1
router_invalid_reason=
fallback_classifier_used=false
fallback_classifier_result=not_applicable
coder_model=not_called
requested_model=phi4-mini
resolved_model=phi4-mini:latest
provider=ollama
provider_call_made=true
task_class=structured_classifier_smoke
route=direct_ollama_api_generate
reason_codes=phi4_mini_pull_success,valid_json,target_unclear_conflicts_with_local_ok
target_unclear=true
caps_profile=not_applicable
file_count=docs_evidence_only
added_line_count=docs_evidence_only
modified_existing_file_count=0
caps_passed=not_applicable
caps_violation_reason=
blacklist_passed=not_applicable
blacklist_matches=
parse_status=valid_json
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
final_trust_status=classifier_connectivity_smoke_only_fallible
blocked_reason=
human_gate_required=true
```

## Next Gate

Increment `2.3` is ready for human review.

Do not continue to Tier 1 Increment `2.4` route truth surface or any later work without explicit human approval.

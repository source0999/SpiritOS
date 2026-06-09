# Increment 2.2 - Qwen2.5-Coder 14B Pull and Minimal Smoke

Status: completed for human review
Tier: Tier 0 Batch Check with explicitly approved model pull
Timestamp: 2026-06-08T23:31Z to 2026-06-08T23:45Z

This increment pulled `qwen2.5-coder:14b` into local Ollama and ran one minimal non-coding smoke prompt. No Source Proxy route/default/provider was changed. No `/coding` runtime file was changed. No trial, parser, repair, apply, commit, push, stash, reset, clean, worktree action, or Tier 1 route truth work was run.

## Gate State

The human approved Increment `2.2` and explicitly approved the model installation/pull step after reviewing Increment `2.1`.

Commands:

```text
npm run gate:approve -- 2.2
npm run gate:start -- 2.2
npm run gate:status
```

Observed running state:

```json
{
  "status": "RUNNING_INCREMENT",
  "approved_increment": "2.2",
  "last_completed_increment": "2.1",
  "approval_token": "2.2:faa01a1a7a5a0a8c05719966",
  "updated_at": "2026-06-08T23:31:22.052Z",
  "notes": ""
}
```

## Pull Command

Command:

```text
ollama pull qwen2.5-coder:14b
```

Observed result:

- Pull completed successfully.
- Main model layer downloaded was approximately `9.0 GB`.
- Ollama selected the default `qwen2.5-coder:14b` manifest.

## Ollama List

Command:

```text
ollama list
```

Observed after pull:

```text
NAME                      ID              SIZE      MODIFIED
qwen2.5-coder:14b         9ec8897f747e    9.0 GB    13 seconds ago
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

Observed `qwen2.5-coder:14b` metadata:

```text
name=qwen2.5-coder:14b
model=qwen2.5-coder:14b
size=8988124298 bytes
digest=9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849
format=gguf
family=qwen2
parameter_size=14.8B
quantization_level=Q4_K_M
context_length=32768
embedding_length=5120
capabilities=completion, tools, insert
```

Command:

```text
ollama show qwen2.5-coder:14b
```

Observed:

```text
architecture        qwen2
parameters          14.8B
context length      32768
embedding length    5120
quantization        Q4_K_M
capabilities        completion, tools, insert
```

Conclusion:

- The recommended default quantization requirement is satisfied by the pulled manifest: `Q4_K_M`.

## Minimal Non-Coding Smoke

Command shape:

```text
POST http://127.0.0.1:11434/api/generate
model=qwen2.5-coder:14b
prompt="Reply with exactly PONG and no other text."
stream=false
options.num_predict=4
options.temperature=0
```

Observed response:

```json
{
  "elapsed_ms": 18406,
  "model": "qwen2.5-coder:14b",
  "response": "PONG",
  "done": true,
  "total_duration_ns": 18292141800,
  "load_duration_ns": 16704017800,
  "prompt_eval_count": 39,
  "eval_count": 3
}
```

Smoke conclusion:

- The local Ollama model can load and return a minimal response.
- This was not a coding task.
- No parser/trial/apply path was exercised.
- No local proof for coding ability is claimed from this smoke.

## Loaded Size / Processor Estimate

Command:

```text
ollama ps
```

Observed after smoke:

```text
NAME                 ID              SIZE     PROCESSOR          CONTEXT    UNTIL
qwen2.5-coder:14b    9ec8897f747e    10 GB    31%/69% CPU/GPU    4096       4 minutes from now
```

Estimate:

- Disk model size from `ollama list`: `9.0 GB`.
- Loaded size from `ollama ps`: `10 GB`.
- Ollama reported split execution as `31%/69% CPU/GPU`.
- Direct `nvidia-smi` was not available from this PowerShell session, so exact VRAM allocation could not be queried through that tool.

`nvidia-smi` result:

```text
NVIDIA_SMI_ERROR: The term 'nvidia-smi' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

## Disk Space After Pull

Command:

```text
Get-PSDrive -PSProvider FileSystem
```

Observed relevant free space:

```text
C: 84.09 GB free
D: 466.53 GB free
M: 6896.12 GB free
Z: 168.64 GB free
```

Prior Increment `2.1` had observed `C: 93.09 GB free`, so the pull appears to have consumed approximately `9 GB` on `C:`.

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
  reason=ollama_model_missing:hermes4:latest; available=qwen2.5-coder:14b, qwen2.5-coder:7b, ...
  requested_ollama_model=hermes4:latest

coder:
  provider=ollama
  model=ollama_chat/qwen2.5-coder:7b
  enabled=true
  requested_ollama_model=qwen2.5-coder:7b
  ollama_model=qwen2.5-coder:7b
```

Route conclusion:

- The new 14B model is visible to Source Proxy inventory as an available Ollama model.
- The `coder` alias still resolves to `qwen2.5-coder:7b`.
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

## Increment 2.2 Self-Checks

- Gate approved and started for `2.2`: yes.
- Qwen2.5-Coder 14B pull completed: yes.
- Pulled quantization recorded: `Q4_K_M`.
- Minimal smoke returned: yes, `PONG`.
- Smoke was not a real coding task: yes.
- `ollama list` captured: yes.
- `ollama ps` captured: yes.
- Model size and loaded-size estimate captured: yes.
- `/api/tags` info captured: yes.
- Source Proxy route/default unchanged: yes.
- No `/coding` change: yes.
- No apply/commit/push/stash/reset/clean/worktree action: yes.
- Did not proceed to `2.3` Phi or Tier 1 work: yes.

## Receipt Summary

```text
run_id=2026-06-08-qwen14b-upgrade-increment-2.2
phase_id=2
increment_id=2.2
gate_state_before=WAITING_FOR_HUMAN_then_APPROVED_INCREMENT
gate_state_after=RUNNING_INCREMENT_until_completion_command
approved_increment=2.2
approval_token_id=2.2:faa01a1a7a5a0a8c05719966
central_gate_check_passed=gate_command_passed_for_increment_2.2
router_model=not_called
router_status=not_called
router_attempt_count=0
router_invalid_reason=
fallback_classifier_used=false
fallback_classifier_result=not_applicable
coder_model=qwen2.5-coder:14b
requested_model=qwen2.5-coder:14b
resolved_model=qwen2.5-coder:14b
provider=ollama
provider_call_made=true
task_class=minimal_non_coding_smoke
route=direct_ollama_api_generate
reason_codes=qwen14b_pull_success,q4_k_m_manifest,non_coding_smoke_only
target_unclear=false
caps_profile=not_applicable
file_count=docs_evidence_only
added_line_count=docs_evidence_only
modified_existing_file_count=0
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
final_trust_status=install_and_connectivity_smoke_only
blocked_reason=
human_gate_required=true
```

## Next Gate

Increment `2.2` is ready for human review.

Do not continue to Increment `2.3` Phi work or Tier 1 Increment `2.4` route truth work without explicit human approval.

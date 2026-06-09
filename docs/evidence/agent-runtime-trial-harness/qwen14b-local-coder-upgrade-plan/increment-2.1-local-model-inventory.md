# Increment 2.1 - Local Model Inventory Batch

Status: completed for human review
Tier: Tier 0 Batch Check
Timestamp: 2026-06-08T23:27Z to 2026-06-08T23:33Z

No production route/default/provider was changed. No model was installed, pulled, deleted, prompted, or generated from. No trial, parser, repair, apply, `/coding` runtime change, commit, push, stash, reset, clean, or worktree action was run.

## Gate State

The human approved Phase 2 and Increment `2.1` in chat.

Commands:

```text
npm run gate:approve -- 2.1
npm run gate:start -- 2.1
npm run gate:status
```

Observed running state:

```json
{
  "status": "RUNNING_INCREMENT",
  "approved_increment": "2.1",
  "last_completed_increment": "1.4",
  "approval_token": "2.1:4fe7d63e5d0f3b5187cf7a5e",
  "updated_at": "2026-06-08T23:27:24.659Z",
  "notes": ""
}
```

Note: one parallel `gate:status` read captured the previous `WAITING_FOR_HUMAN` state while `gate:approve` was writing. The sequential `gate:start` and follow-up `gate:status` confirmed the active `RUNNING_INCREMENT` state for `2.1`.

## Git Status Baseline

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

- The source and gate changes above pre-existed this increment.
- This increment added only this docs/evidence packet and the living status update.

## Local Ollama Inventory

Command:

```text
ollama list
```

Observed:

```text
NAME                      ID              SIZE      MODIFIED
qwen2.5-coder:7b          dae161e27b0e    4.7 GB    2 days ago
dolphin-mistral:latest    5dc8c5a2be65    4.1 GB    7 weeks ago
Spirit:latest             613f068e29f8    4.7 GB    8 weeks ago
dolphin-llama3:latest     613f068e29f8    4.7 GB    8 weeks ago
gpt-4o-mini:latest        46e0c10c039e    4.9 GB    8 weeks ago
gpt-4o:latest             46e0c10c039e    4.9 GB    8 weeks ago
llama3.1:latest           46e0c10c039e    4.9 GB    8 weeks ago
```

Command:

```text
ollama ps
```

Observed:

```text
NAME                ID              SIZE      PROCESSOR    CONTEXT    UNTIL
qwen2.5-coder:7b    dae161e27b0e    4.7 GB    100% GPU     4096       Forever
```

Command:

```text
Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags -TimeoutSec 5
```

Observed API details confirm:

- `qwen2.5-coder:7b`
  - family: `qwen2`
  - parameter_size: `7.6B`
  - quantization_level: `Q4_K_M`
  - capabilities: `completion`, `tools`, `insert`
- No `qwen2.5-coder:14b` model appears.
- No Phi, Phi-4 Mini, or obvious Phi equivalent appears.

## Disk Space

Command:

```text
Get-PSDrive -PSProvider FileSystem
```

Observed relevant free space:

```text
C: 93.09 GB free
D: 466.53 GB free
M: 6896.12 GB free
Z: 168.65 GB free
```

Disk conclusion:

- There is enough apparent free space for a future model install on some drives.
- This increment did not choose a storage location or pull/install any model.
- `OLLAMA_MODELS` is unset in this shell.

## Current Route/Default Truth

Read-only Source Proxy model status command:

```text
Invoke-RestMethod -Uri http://127.0.0.1:8787/v1/models -TimeoutSec 5
```

Observed relevant entries:

```text
local:
  provider=ollama
  model=ollama_chat/hermes4:latest
  enabled=false
  reason=ollama_model_missing:hermes4:latest
  requested_ollama_model=hermes4:latest
  api_base=http://127.0.0.1:11434

coder:
  provider=ollama
  model=ollama_chat/qwen2.5-coder:7b
  enabled=true
  requested_ollama_model=qwen2.5-coder:7b
  ollama_model=qwen2.5-coder:7b
  api_base=http://127.0.0.1:11434
```

Static route-source inspection:

- `source_proxy/routing/ollama_route.py`
  - default local model: `hermes4`
  - coder candidates: `qwen2.5-coder:7b`, `qwen2.5-coder:latest`, `deepseek-coder:6.7b`, `codellama:7b`
  - no 14B candidate is currently present in the inspected coder candidate list
- `.env.local`
  - `OLLAMA_MODEL=hermes4:latest`
  - `SOURCE_PROXY_CODER_MODEL_ALIAS=coder`
  - `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b`
- `config/source-proxy.example.env`
  - documents Hermes as local proxy/coding preference and Qwen as selectable but non-default

Shell environment:

```text
OLLAMA_MODELS=<unset>
SOURCE_PROXY_CODER_OLLAMA_MODEL=<unset in shell>
SOURCE_PROXY_OLLAMA_MODEL=<unset in shell>
```

Route conclusion:

- Existing coder route remains `qwen2.5-coder:7b`.
- `qwen2.5-coder:14b` is not configured as the coder default.
- Phi is not configured as a router/classifier.
- No route/default mutation was made.

## Phase 2.2 and 2.3 Batch Decision

The user allowed batching other Tier 0 Phase 2 increments only if clearly non-mutating and low risk.

Decision: do not run Increment `2.2` or `2.3` now.

Reasons:

- Increment `2.2` requires a non-mutating prompt through Qwen 14B, but Qwen 14B is not installed.
- Increment `2.3` requires a Phi structured classification smoke probe, but Phi/Phi-4 Mini/equivalent is not installed.
- Installing either model would mutate system state and the plan says to stop and ask before install.
- Calling 7B, Hermes, or any cloud model would not satisfy the 14B/Phi smoke criteria and would risk false proof.

## Increment 2.1 Self-Checks

- Model list captured: yes.
- Ollama API tag inventory captured: yes.
- Loaded model state captured: yes.
- Disk space captured: yes.
- Current default route check captured: yes.
- No route mutation: yes.
- No model deletion: yes.
- No model install/pull: yes.
- No model prompt/generation call: yes.
- No `/coding` runtime mutation: yes.
- No apply/commit/push/stash/reset/clean/worktree action: yes.

## Receipt Summary

```text
run_id=2026-06-08-qwen14b-upgrade-increment-2.1
phase_id=2
increment_id=2.1
gate_state_before=WAITING_FOR_HUMAN_then_APPROVED_INCREMENT
gate_state_after=RUNNING_INCREMENT_until_completion_command
approved_increment=2.1
approval_token_id=2.1:4fe7d63e5d0f3b5187cf7a5e
central_gate_check_passed=gate_command_passed_for_increment_2.1
router_model=not_called
router_status=not_called
router_attempt_count=0
router_invalid_reason=
fallback_classifier_used=false
fallback_classifier_result=not_applicable
coder_model=not_called
requested_model=not_called
resolved_model=not_called
provider=not_called
provider_call_made=false
task_class=local_model_inventory
route=docs_evidence_only
reason_codes=qwen14b_missing,phi_missing,install_requires_separate_approval
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
final_trust_status=inventory_only_blocked_before_smoke
blocked_reason=qwen14b_and_phi_missing
human_gate_required=true
```

## Next Gate

Increment `2.1` is ready for human review.

Required human decision:

- approve a separate model install/pull step for Qwen 14B and Phi/Phi-4 Mini/equivalent, or
- revise Phase 2 to use specific already-installed local equivalents, or
- keep Phase 2 blocked with no smoke probes.

Do not continue to Increment `2.2`, `2.3`, or Tier 1 Increment `2.4` without explicit human approval.

# Increment 1.2 - Baseline Evidence Batch

Status: completed for human review
Tier: Tier 0 Batch Check
Timestamp: 2026-06-08T23:04:51Z to 2026-06-08T23:15:00Z

No implementation behavior was changed in this increment. No model was installed. No model was called. No Source Proxy runtime behavior was modified. No `/coding` runtime code was modified. No apply, commit, push, stash, reset, clean, or worktree action was run.

## Gate State

- Gate was approved for increment `1.2`.
- Gate was started for increment `1.2`.
- This evidence packet is the Tier 0 baseline output for human review before Increment 1.3.

## Git Status Baseline

Command:

```text
git status --short --branch
```

Observed:

```text
## lane/coding-human-trial-runner-polish-20260530-112512...origin/lane/coding-human-trial-runner-polish-20260530-112512 [ahead 19]
 M package.json
?? .gate/
?? docs/evidence/agent-runtime-trial-harness/qwen14b-local-coder-upgrade-plan/
?? scripts/gate-approve
?? scripts/gate-block
?? scripts/gate-complete
?? scripts/gate-lib.mjs
?? scripts/gate-start
?? scripts/gate-status
```

Dirty-tree caveat:

- `package.json`, `.gate/`, and `scripts/gate-*` are from Increment 1.1.
- The qwen14b plan packet directory is still untracked in this checkout.
- This increment added only this evidence file plus the living status update.

Command:

```text
git diff --stat
```

Observed before this evidence file:

```text
package.json | 5 +++++
1 file changed, 5 insertions(+)
```

PowerShell/git warning observed:

```text
warning: in the working copy of 'package.json', LF will be replaced by CRLF the next time Git touches it
```

## Local Model Inventory

Command:

```text
ollama list
```

Observed local models:

```text
qwen2.5-coder:7b          dae161e27b0e    4.7 GB    2 days ago
dolphin-mistral:latest    5dc8c5a2be65    4.1 GB    7 weeks ago
Spirit:latest             613f068e29f8    4.7 GB    8 weeks ago
dolphin-llama3:latest     613f068e29f8    4.7 GB    8 weeks ago
gpt-4o-mini:latest        46e0c10c039e    4.9 GB    8 weeks ago
gpt-4o:latest             46e0c10c039e    4.9 GB    8 weeks ago
llama3.1:latest           46e0c10c039e    4.9 GB    8 weeks ago
```

Baseline conclusion:

- `qwen2.5-coder:7b` is installed.
- `qwen2.5-coder:14b` is not installed in the observed Ollama inventory.
- This increment did not install, pull, load, prompt, or call any model.

## Current Source Proxy Route Map

Read-only inspection found these route/model anchors:

- `source_proxy/api/chat.py`
  - `GET /v1/models` returns `routing_status()`.
  - `POST /v1/chat/completions` sends enabled aliases through LiteLLM router after spend pre-call hook.
- `source_proxy/routing/litellm_router.py`
  - Defines aliases `local`, `coder`, `openai`, `anthropic`, and `deepseek`.
  - `coder` uses the Ollama coder model resolved by `resolve_coder_ollama_model_name`.
- `source_proxy/routing/ollama_route.py`
  - Current coder candidates are `qwen2.5-coder:7b`, `qwen2.5-coder:latest`, `deepseek-coder:6.7b`, and `codellama:7b`.
  - Default local chat model remains `hermes4` unless env/model availability resolves differently.
  - Coder lane may auto-select `qwen2.5-coder:7b` when present.
- `source_proxy/api/codex_adapter.py`
  - `POST /v1/coding/codex` validates a readonly/proposal command preview only.
  - Apply/commit/push modes are blocked.
  - `POST /v1/coding/bounded-diff-preview` can generate a deterministic bounded preview packet for specific CG task ids.
- `source_proxy/api/coding_self_tests.py`
  - `POST /v1/coding/self-tests/run` supports dry-run self-test profiles only.

Important baseline gap:

- There is not yet a Qwen14B-specific centralized gate function wired into every model-call/apply path.
- That work belongs to Increment 1.3 and is Tier 1.

## Current `/coding` Runner State

Read-only file inventory found the current `/coding` surface and runner pieces:

- App route: `src/app/coding/page.tsx`
- Source Proxy bridge routes under `src/app/v1/coding/**`, including:
  - `agent-lab-baseline`
  - `agent-lab-sweep`
  - `bounded-diff-preview`
  - `cartographer/preview`
  - `codex`
  - `design-vault/preview`
  - `gauntlet/preview`
  - `helper-agents/preview`
  - `hermes-stress-smoke`
  - `research-preview`
  - `runs`
  - `self-tests/run`
  - `trial-fixture-baseline`
  - `trial-receipt-reconcile`
  - `workspace-read`
- Core runner/state modules under `src/lib/coding/**`, including:
  - `agent-trials-ui.ts`
  - `reversible-trial-runner.ts`
  - `model-provider-status.ts`
  - `visible-result-badge.ts`
  - `stress-test-readiness.ts`
  - `durable-run-store.ts`
- UI shells under `src/components/coding/**`, including:
  - `CodingAgentInterface.tsx`
  - `CodingCockpitShell.tsx`
  - `CodingCommandCenterShell.tsx`

Baseline conclusion:

- `/coding` is currently a large existing runner/shell surface.
- This increment did not edit `/coding` runtime or UI files.
- Future behavior changes to this surface require the plan's Tier 1 gates.

## Current 7B Coder Failure Evidence

Existing evidence packet used:

```text
docs/evidence/agent-runtime-trial-harness/coder-trial-recovery-mini-plan/gate-7R-closeout-runner-repair.md
```

Relevant existing recorded local setup:

```text
Available allowed model: qwen2.5-coder:7b
SOURCE_PROXY_CODER_MODEL_ALIAS=coder
SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b
Source Proxy coder route: enabled
provider/model: local / ollama_chat/qwen2.5-coder:7b
route type: local Ollama
```

Relevant existing recorded local run:

```text
POST /v1/decisions/prompt-packet
status=blocked
reason_code=coder_file_bundle_validation_failed
provider/model=local / ollama_chat/qwen2.5-coder:7b
provider_call_made=true
generation_source=model
diff_source=pending_backend_diff_from_model_file_bundle
trial_result_trust_status=model_output_not_usable
scaffold_used=false
fallback_used=false
generated_diff_by_backend=false
repair_attempted=true
changed_files=none
```

Relevant existing blocker:

```text
Qwen returned model-authored create_file_bundle JSON, but the JSON was malformed after the repair retry.
Final parse error: Expecting value: line 10 column 50 (char 312)
No diff preview was run.
No apply was run.
No LumaCart files were created.
No cloud/API fallback was used.
```

Baseline conclusion:

- The current 7B failure pattern is not "local model unreachable."
- The local Qwen2.5-Coder 7B path was reached.
- Scaffold/fallback were recorded as false for the strict Prompt 001 local run.
- The output protocol failed: malformed model-authored file-bundle JSON after repair retry.

## Known Scaffold/Fallback Status

Existing evidence packet used:

```text
docs/evidence/agent-runtime-trial-harness/coder-trial-recovery-mini-plan/increment-1.2-fallback-scaffold-inventory.md
```

Known scaffold/fallback locations from prior evidence:

- `source_proxy/planning/bounded_create.py`
  - Exact Agent Lab deterministic scaffolds.
  - Generic Next app page scaffold for `src/app/**/page.tsx`.
- `source_proxy/planning/architect.py`
  - Deterministic bounded-create planning before long-task fallthrough.
- `source_proxy/tasks/long_running.py`
  - Deterministic bounded-create response fallback.
  - Scaffold/fallback provenance marking.
  - Trial-mode PASS blocking when scaffold/fallback provenance is present.
- `src/lib/coding/durable-run-types.ts` and `src/lib/coding/durable-run-store.ts`
  - Durable provenance fields.
- `src/components/coding/CodingCockpitShell.tsx`
  - Trial row provenance display and no-diff provider-call-only PASS prevention.

Prior self-check conclusion:

```text
Every Coder trial-impacting fallback has file/function/caller/behavior recorded: yes.
Normal task-composer impact separated from trial-mode impact: yes.
Coder 10 / Agent Lab tailored scaffolds flagged: yes.
```

Baseline conclusion:

- Known scaffold/fallback behavior exists historically and must remain visible in receipts.
- Current plan must not treat provider_call_made=true as proof of model-authored usable code.
- The 14B upgrade must preserve scaffold/fallback truth fields and local-proof restrictions.

## Increment 1.2 Self-Checks

- `git status --short --branch`: captured.
- Local route/status inspection: captured from Source Proxy route files.
- Model list inspection: captured with `ollama list`.
- Evidence path inventory: captured from existing recovery and fallback/scaffold evidence.
- No source mutation except docs/evidence/status for Increment 1.2: yes.
- No model call: yes.
- No model install: yes.
- No apply/commit/push/stash/reset/clean/worktree action: yes.

## Receipt Summary

```text
run_id=2026-06-08-qwen14b-upgrade-increment-1.2
phase_id=1
increment_id=1.2
gate_state_before=APPROVED_INCREMENT
gate_state_after=RUNNING_INCREMENT until completion command
approved_increment=1.2
central_gate_check_passed=not_implemented_yet_increment_1.3
router_model=not_called
router_status=not_called
router_attempt_count=0
fallback_classifier_used=false
coder_model=not_called
requested_model=not_called
resolved_model=not_called
provider=not_called
provider_call_made=false
task_class=baseline_inventory
route=docs_evidence_only
caps_profile=not_applicable
file_count=docs_evidence_only
caps_passed=not_applicable
blacklist_passed=not_applicable
parse_status=not_applicable
repair_attempted=false
local_proof=false
scaffold_used=false
fallback_used=false
backend_generated_content=false
diff_shown=false
apply_allowed=false
apply_performed=false
reverse_performed=false
unexpected_delta_detected=false
final_trust_status=baseline_only
blocked_reason=
human_gate_required=true
```

## Next Gate

Increment 1.2 is ready for human review.

Do not continue to Increment 1.3 until the human approves that Tier 1 implementation gate.

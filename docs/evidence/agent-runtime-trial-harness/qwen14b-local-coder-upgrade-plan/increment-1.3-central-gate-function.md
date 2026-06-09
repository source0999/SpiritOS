# Increment 1.3 - Central Gate Function and Model/Apply Wrappers

Status: completed for human review
Tier: Tier 1 Hard Stop Gate
Timestamp: 2026-06-08T23:10:19Z to 2026-06-08T23:27:00Z

Implementation started in this increment, limited to central gate enforcement and wrapper calls. No model was installed. No model was called. No apply action was run. No Source Proxy provider route was changed. No `/coding` runtime or UI code was modified.

## Gate State

- Gate was approved for increment `1.3`.
- Gate was started for increment `1.3`.
- This evidence packet is the Tier 1 output for human review before Increment 1.4.

## What Changed

Created the central gate function:

```text
source_proxy/approval/external_gate.py
```

The function is:

```text
central_gate_check(action, increment_id, run_id)
```

It fails closed when:

- gate state file is missing
- gate state JSON is malformed
- gate status is not `APPROVED_INCREMENT` or `RUNNING_INCREMENT`
- approved increment does not match
- approval token is missing
- action type is not explicitly allowed

Default behavior:

- `SOURCE_PROXY_GATE_INCREMENT` defaults to `1.3` for this increment.
- `SOURCE_PROXY_GATE_ALLOWED_ACTIONS` is empty by default.
- With no allowed-action override, only `gate_implementation` is allowed.
- Actual `model_call` and `apply` actions are blocked even while Increment 1.3 is running.

This prevents the implementation gate from becoming accidental permission to call models or apply changes.

## Model-Call Paths Wrapped

Model-call enforcement was added to:

- `source_proxy/api/chat.py`
  - `/v1/chat/completions`
- `source_proxy/tasks/long_running.py`
  - `_call_coder_llm`
  - covers Coder generation and Coder repair retries that use the shared helper
- `source_proxy/planning/architect.py`
  - `_call_architect_llm`
- `source_proxy/planning/reviewer.py`
  - `_call_reviewer_llm`
- `source_proxy/api/decision.py`
  - `_ollama_trial_proof_call`
  - covers the direct Ollama trial proof path

Static scan command:

```text
rg -n "get_router\\(\\)\\.(a?completion)|urllib\\.request\\.urlopen\\(" source_proxy -g "!**/__pycache__/**"
```

Model-generation sites found and wrapped:

- `source_proxy/api/chat.py`
- `source_proxy/planning/architect.py`
- `source_proxy/api/decision.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/planning/reviewer.py`

Non-generation URL open sites found:

- `source_proxy/routing/ollama_route.py`
  - Ollama model inventory/probe only.
- `source_proxy/testing/runner.py`
  - HTTP route/test runner checks, not provider/model generation calls.

## Apply Paths Wrapped

Apply enforcement was added to:

- `source_proxy/tasks/long_running.py`
  - `execute_approved_long_running_task`
- `source_proxy/cartographer/apply.py`
  - `apply_approved_doc_proposal`
- `source_proxy/cartographer/autopilot_apply.py`
  - `run_docs_autopilot_apply`
- `source_proxy/cartographer/level_2_apply.py`
  - `run_level_2_docs_apply`
- `source_proxy/cartographer/clutter_proposals.py`
  - `apply_approved_low_risk_deletion_proposal`

## Tests Added

```text
source_proxy/tests/test_external_gate.py
source_proxy/tests/test_external_gate_integration.py
```

Coverage:

- closed gate blocks model calls
- increment mismatch blocks
- model_call is not allowed by default for Increment 1.3
- explicit allowed action can pass and returns a receipt
- `/v1/chat/completions` blocks before router lookup when gate is closed
- `_call_coder_llm` blocks before `get_router()` when action is not allowed

## Checks Run

Command:

```text
python -m pytest -q source_proxy/tests/test_external_gate.py source_proxy/tests/test_external_gate_integration.py
```

Result:

```text
6 passed in 2.61s
```

Command:

```text
python -m pytest -q source_proxy/tests/test_external_gate.py source_proxy/tests/test_external_gate_integration.py source_proxy/tests/test_ollama_route.py::OllamaRouteTests::test_connection_refused_maps_to_local_model_unavailable
```

Result:

```text
7 passed in 3.01s
```

Command:

```text
git diff --check
```

Result:

```text
passed with CRLF warnings only
```

Observed CRLF warnings were for files changed on this Windows share, including `package.json` and the Source Proxy files touched in this increment.

## Safety Notes

- No model calls were made.
- No model install or model change occurred.
- No Qwen14B route was added.
- No provider default was changed.
- No `/coding` runtime or UI file was modified.
- No apply path was executed.
- No commit, push, stash, reset, clean, branch, or worktree action was run.
- Runtime model/apply paths now fail closed unless the external gate is open for the exact increment and the action type is explicitly allowed.

## Receipt Summary

```text
run_id=2026-06-08-qwen14b-upgrade-increment-1.3
phase_id=1
increment_id=1.3
gate_state_before=APPROVED_INCREMENT
gate_state_after=RUNNING_INCREMENT until completion command
approved_increment=1.3
central_gate_check_passed=true_for_gate_implementation_tests
router_model=not_called
router_status=not_called
router_attempt_count=0
fallback_classifier_used=false
coder_model=not_called
requested_model=not_called
resolved_model=not_called
provider=not_called
provider_call_made=false
task_class=central_gate_implementation
route=implementation_only_no_model_call
caps_profile=not_applicable
file_count=source_proxy_gate_files_and_tests
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
final_trust_status=gate_enforced_not_model_trusted
blocked_reason=
human_gate_required=true
```

## Next Gate

Increment 1.3 is ready for human review.

Do not continue to Increment 1.4 until the human approves that next gate.

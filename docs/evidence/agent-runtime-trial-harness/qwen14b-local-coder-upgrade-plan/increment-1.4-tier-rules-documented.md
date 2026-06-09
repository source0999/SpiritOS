# Increment 1.4 - Tier Rules Documented

Status: completed for human review
Tier: Tier 0 Batch Check
Timestamp: 2026-06-08T23:20:06Z to 2026-06-08T23:30:00Z

No runtime behavior was changed in this increment. No model was installed. No model was called. No Source Proxy runtime behavior was modified. No `/coding` runtime or UI code was modified. No apply, commit, push, stash, reset, clean, branch, or worktree action was run.

## What Changed

Created the operator runbook:

```text
docs/evidence/agent-runtime-trial-harness/qwen14b-local-coder-upgrade-plan/operator-runbook.md
```

The runbook documents:

- gate commands
- explicit Tier 0 allow-list
- explicit Tier 1 hard-stop list
- more than 2 examples for each tier
- phase completion as a hard stop
- current central gate coverage
- paths that may need future wrapping review
- Windows and Linux manual-check commands

## Current Protected Files

Central gate module:

```text
source_proxy/approval/external_gate.py
```

Protected model-call files:

- `source_proxy/api/chat.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/planning/architect.py`
- `source_proxy/planning/reviewer.py`
- `source_proxy/api/decision.py`

Protected apply/write-action files:

- `source_proxy/tasks/long_running.py`
- `source_proxy/cartographer/apply.py`
- `source_proxy/cartographer/autopilot_apply.py`
- `source_proxy/cartographer/level_2_apply.py`
- `source_proxy/cartographer/clutter_proposals.py`

## Paths That May Still Need Wrapping Review

These are not declared safe. They are review candidates before any future promotion:

- `source_proxy/routing/ollama_route.py`
  - Ollama tag inventory/probe URL open.
- `source_proxy/testing/runner.py`
  - HTTP checks, subprocess calls, evidence writes, and runner profile surfaces.
- `source_proxy/cartographer/safe_write.py`
  - Direct safe-write behavior.
- `source_proxy/verification/contracts.py`
  - Contract helper file writes.
- `source_proxy/cartographer/starter_blueprints.py`
  - Blueprint writes.
- `source_proxy/cartographer/proposal_reviews.py`
  - Proposal/audit persistence.
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/controlled_push_queue.py`
- `source_proxy/cartographer/git_approvals.py`
- `source_proxy/cartographer/local_commit_gate.py`
  - Git command surfaces.
- `source_proxy/codex/task_packet.py`
- `source_proxy/codex/evidence.py`
  - Codex-related subprocess/evidence write surfaces.

## Checks Run

Command:

```text
rg -n "Tier 0 Allow-List|Tier 1 Hard-Stop List|Tier 0 examples|Tier 1 examples|Phase Completion Rule|Current Central Gate Coverage|Paths That May Need Future Wrapping Review" docs/evidence/agent-runtime-trial-harness/qwen14b-local-coder-upgrade-plan/operator-runbook.md
```

Result:

```text
matched all required runbook sections
```

Command:

```text
git diff --check
```

Result:

```text
passed with CRLF warnings only
```

Command:

```text
npm run gate:status
```

Result before completion:

```text
status=RUNNING_INCREMENT
approved_increment=1.4
last_completed_increment=1.3
```

## Self-Checks

- Docs contain explicit Tier 0 allow-list: yes.
- Docs contain explicit Tier 1 hard-stop list: yes.
- Docs include at least 2 to 3 examples for each tier: yes.
- Docs state phase completion always stops: yes.
- No runtime behavior changed: yes.
- No source mutation outside docs/evidence/runbook files for Increment 1.4: yes.

## Receipt Summary

```text
run_id=2026-06-08-qwen14b-upgrade-increment-1.4
phase_id=1
increment_id=1.4
gate_state_before=APPROVED_INCREMENT
gate_state_after=RUNNING_INCREMENT until completion command
approved_increment=1.4
central_gate_check_passed=not_applicable_docs_only
router_model=not_called
router_status=not_called
router_attempt_count=0
fallback_classifier_used=false
coder_model=not_called
requested_model=not_called
resolved_model=not_called
provider=not_called
provider_call_made=false
task_class=tier_rules_documentation
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
final_trust_status=tier_rules_documented
blocked_reason=
human_gate_required=true
```

## Next Gate

Increment 1.4 is ready for human review.

Phase 1 is now ready for the Phase Completion Gate. Do not continue to Phase 2 until the human approves the Phase 1 completion gate and the next exact increment.

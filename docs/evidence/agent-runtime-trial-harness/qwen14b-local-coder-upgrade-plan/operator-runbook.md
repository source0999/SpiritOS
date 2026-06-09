# Qwen14B Local Coder Operator Runbook

This runbook is the local operator surface for the Qwen2.5-Coder 14B upgrade plan packet.

It does not grant model-call, apply, commit, push, stash, reset, clean, branch, or worktree authority. The repo plan remains the source of truth.

## Gate Commands

```text
npm run gate:status
npm run gate:approve -- 1.4
npm run gate:start -- 1.4
npm run gate:complete -- 1.4
npm run gate:block -- "reason"
```

Codex must not approve its own next increment.

Every increment ends with the gate returning to `WAITING_FOR_HUMAN`.

## Tier 0 Allow-List

Tier 0 is batchable only when all conditions are true:

- No source behavior changes.
- No model-call path changes.
- No provider, model, route, or default changes.
- No parser, repair, backend guard, cap, blacklist, apply, or reverse changes.
- No trust-label or UI-status semantics changes.
- No commit, push, reset, stash, clean, branch, or worktree action.
- Only docs, evidence, runbook, inventory, or receipt files are written.
- Any smoke prompt is non-mutating, explicitly listed in the approved increment, and not a hidden implementation step.

Tier 0 examples:

- Record git status, model inventory, route-map inspection, and dirty-tree caveats in an evidence packet.
- Write or update operator runbook text explaining existing gate commands and tier rules.
- Create an evidence index that links already-existing receipts without changing runtime behavior.
- Record a non-mutating model inventory command such as `ollama list` without installing or calling a model.

## Tier 1 Hard-Stop List

Tier 1 is required for anything that changes how the system behaves or what can become trusted proof.

Tier 1 includes:

- Any source code mutation outside docs/evidence/runbook files.
- Any central gate function change.
- Any model-call path change.
- Any provider, model, route, default, or fallback change.
- Any parser, output-format, repair-loop, caps, blacklist, backend guard, TaskSpec, or classifier change.
- Any diff preview, apply, reverse, approval-token, or gate-enforcement behavior change.
- Any trial scoring or trust-label/status semantics change.
- Any script, route, worker, helper, test harness, or wrapper that can call a model.
- Any script, route, worker, helper, test harness, or wrapper that can apply, write, delete, commit, push, stash, reset, clean, branch, or create a worktree.

Tier 1 examples:

- Add or move `central_gate_check()` around a Source Proxy model-call route.
- Add XML output parsing or repair similarity checks for Qwen output.
- Add backend blacklist rejection before diff display.
- Change apply eligibility, apply approval binding, or reverse behavior.

## Phase Completion Rule

Phase completion is always a hard stop.

Even if the final increment in a phase is Tier 0, Codex must stop after the phase evidence and wait for human review before moving to the next phase.

## Current Central Gate Coverage

Central gate module:

```text
source_proxy/approval/external_gate.py
```

Current model-call paths protected:

- `source_proxy/api/chat.py`
  - `/v1/chat/completions`
- `source_proxy/tasks/long_running.py`
  - `_call_coder_llm`
  - Covers Coder generation and Coder repair retries that use this helper.
- `source_proxy/planning/architect.py`
  - `_call_architect_llm`
- `source_proxy/planning/reviewer.py`
  - `_call_reviewer_llm`
- `source_proxy/api/decision.py`
  - `_ollama_trial_proof_call`

Current apply/write-action paths protected:

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

## Paths That May Need Future Wrapping Review

These paths appeared in static scans as containing command execution, file writes, URL opens, or other operational behavior. They were not all wrapped in Increment 1.3 because some are probes, read-only helpers, test harnesses, or broader Cartographer authority surfaces outside the Qwen14B local-coder path.

Review before any future model/apply promotion:

- `source_proxy/routing/ollama_route.py`
  - Contains Ollama tag inventory/probe URL open. Currently treated as model inventory, not generation.
- `source_proxy/testing/runner.py`
  - Contains HTTP checks, subprocess calls, and evidence writes for runner profiles. Needs review before any runner profile can call models or apply changes.
- `source_proxy/cartographer/safe_write.py`
  - Contains direct safe-write behavior. Needs review if this path is considered an apply path for local-coder operation.
- `source_proxy/verification/contracts.py`
  - Contains direct `write_text` in contract helpers. Needs review before any verification helper is allowed to write in a Qwen pipeline.
- `source_proxy/cartographer/starter_blueprints.py`
  - Contains blueprint file writes. Needs review if blueprint creation becomes part of apply authority.
- `source_proxy/cartographer/proposal_reviews.py`
  - Contains proposal/audit persistence. Needs review if proposal persistence becomes gate-controlled apply evidence.
- `source_proxy/cartographer/commit_proposals.py`, `source_proxy/cartographer/controlled_push_queue.py`, `source_proxy/cartographer/git_approvals.py`, `source_proxy/cartographer/local_commit_gate.py`
  - Contain git command surfaces. These remain outside the Qwen14B local-coder apply path and need separate hard gates.
- `source_proxy/codex/task_packet.py`, `source_proxy/codex/evidence.py`
  - Contain subprocess/evidence write surfaces for Codex-related flows. Review before treating them as model-call or apply paths.

Rule for future work:

Any future path that can call a model or mutate files must call `central_gate_check()` before the call or mutation. If that cannot be proven, the increment blocks with `gate_bypass_risk`.

## Manual Checks

Preferred Windows/PowerShell checks:

```powershell
npm run gate:status
python -m pytest -q source_proxy/tests/test_external_gate.py source_proxy/tests/test_external_gate_integration.py
rg -n "central_gate_check" source_proxy -g "!**/__pycache__/**"
rg -n "get_router\(\)\.(a?completion)|urllib\.request\.urlopen\(" source_proxy -g "!**/__pycache__/**"
git diff --check
git status --short --branch
```

Linux fallback when `python` or `rg` are unavailable:

```bash
npm run gate:status
python3 -m pytest -q source_proxy/tests/test_external_gate.py source_proxy/tests/test_external_gate_integration.py
grep -RIn --exclude-dir='__pycache__' 'central_gate_check' source_proxy
grep -RIn --exclude-dir='__pycache__' -E 'get_router\(\)\.(a?completion)|urllib\.request\.urlopen\(' source_proxy
git diff --check
git status --short --branch
```


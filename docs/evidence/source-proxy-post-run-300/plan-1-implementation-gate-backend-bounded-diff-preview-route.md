# Plan 1/6 Implementation Gate: Backend Bounded Diff Preview Route

## PIVOT Position
- Plan: 1/6, Run 300 Blocker Reduction
- Phase: 1.3, Classifier and receipt implementation
- Next increment type: implementation-gate plan only
- Implementation target after approval: first backend bounded-diff micro-batch, CG-001 through CG-005
- Planning decision: GO for a gated implementation prompt, NO-GO for implementation in this chat

## Current Run 300 State
- total_prompts: 300
- productive_previews: 0
- productive_preview_diffs: 0
- already_satisfied_noops: 0
- blocked_safety: 116
- route_gap_not_ready: 157
- inconclusive_evidence: 27
- safe_blockers: 300
- unsafe_failures: 0
- unexpected_files: 0
- authority_drift_count: 0
- authority_flags: all false
- provider_call_made: false
- queue_worker_started: false
- shell_command_started: false
- hidden_execution_started: false
- phase_7_decision: no_go

## Files Inspected
- source_proxy/api/codex_adapter.py
- source_proxy/codex/adapter.py
- source_proxy/codex/task_packet.py
- source_proxy/codex/evidence.py
- source_proxy/verification/diff.py
- source_proxy/verification/contracts.py
- source_proxy/api/diff_verification.py
- source_proxy/api/action_preview.py
- source_proxy/api/long_running_tasks.py
- source_proxy/api/decision.py
- source_proxy/decision/prompt_packet.py
- source_proxy/tasks/long_running.py
- source_proxy/tests/test_codex_cli_adapter.py
- source_proxy/tests/test_diff_verification.py
- source_proxy/tests/test_source_proxy_end_to_end.py
- source_proxy/tests/test_coding_regression_pack.py
- src/components/coding/CodingCommandCenterShell.tsx
- src/components/coding/__tests__/coding-command-center-shell.test.tsx
- src/lib/coding/proxy-trial-prompts.ts
- src/lib/coding/workflow-progress-copy.ts
- docs/evidence/source-proxy-post-run-300/plan-1-backend-diff-generation-gap-micro-batch-cg001-cg005.md
- docs/evidence/source-proxy-post-run-300/plan-1-phase-1-3-increment-2-staged-run-300-rerun-evidence.md
- docs/evidence/source-proxy-post-run-300/plan-1-receipt-classification-contract.md
- docs/evidence/source-proxy-post-run-300/plan-1-run-300-category-map.md

## Files Changed
- docs/evidence/source-proxy-post-run-300/plan-1-implementation-gate-backend-bounded-diff-preview-route.md

No source, UI, CSS, backend, runtime, test, Cartographer, or config files were changed.

## Exact Current Blocker
The Codex adapter route is intentionally config-blocked. `source_proxy/api/codex_adapter.py` returns:

- status: config_blocked
- execution_state: config_blocked
- reason_code: codex_route_live_execution_not_enabled
- live_execution.enabled: false
- would_run_task: false
- changed_files: []
- approval_authority: false
- apply_authority: false
- commit_authority: false
- push_authority: false

`source_proxy/codex/adapter.py` can validate a safe Codex command envelope, but it only builds a command preview. It does not run a task. `build_codex_cli_status()` may also report `codex_binary_not_found`, but the primary route-level gate is `codex_route_live_execution_not_enabled`.

The Run 300 browser diagnostic does not need live Codex execution. It needs real preview-only bounded diff proof. The current `/v1/decisions/prompt-packet` path can return `proposed_diff` only when the coder path produces validated replacement content. For CG-001 through CG-005, no real proposed diff is currently produced, so the frontend honestly classifies these as `route_gap_not_ready` with `backend_diff_generation_gap`.

## Existing Preview-Only Route Inventory
- `/v1/verification/diff-preview` already verifies a unified diff, extracts changed files, rejects unsafe paths, blocks secret-shaped paths, and reports `would_apply_diff: false` and `would_execute: false`.
- `/v1/decisions/prompt-packet` already returns `proposed_diff` when backend replacement-content generation succeeds, and it already carries target, task_spec, coder diagnostics, already-satisfied state, and blocked reason codes.
- `/v1/coding/codex` already validates proposal mode target_file and allowed_files, but it deliberately returns a command preview only and does not generate a bounded diff.

Conclusion: reuse the existing diff verifier. Add the smallest preview-only diff generation route near the Codex adapter or decision preview path, then let the frontend consume its packet before falling back to generic prompt-packet blocking.

## Recommended Backend Route
Add a preview-only route under the existing coding backend surface:

`POST /v1/coding/bounded-diff-preview`

Rationale:
- It is separate from `/v1/coding/codex`, so it does not imply Codex live execution.
- It can use the same safe path normalization as `CodexAdapterRequest`.
- It can use `generate_unified_diff_from_content()` to create a real unified diff from actual target file contents and deterministic replacement content.
- It can immediately pass the generated diff through `preview_diff_verification()` with a task_spec that limits changed files to allowed_files.
- It can return a complete receipt packet without apply, commit, push, provider, queue, worker, shell, Cartographer, or design apply authority.

## First Implementation Target
Candidate range:

- CG-001 through CG-005 only

Target:

- src/lib/coding/workflow-progress-copy.ts

Allowed files:

- src/lib/coding/workflow-progress-copy.ts

Task text:

- tighten one preview-only helper phrase for clearer coding progress evidence

The implementation should inspect the current target file and produce a small deterministic replacement only for this exact target and task family. A valid proposal would add or refine one helper phrase such as a preview-only review notice inside `workflow-progress-copy.ts`, then call `generate_unified_diff_from_content()` against the real file on disk. The route must not return a hard-coded unified diff and must not claim productivity when the generated replacement matches disk or fails validation.

## Preview Packet Schema
Return this schema for successful preview packets:

```json
{
  "task_id": "cg-001",
  "prompt": "tighten one preview-only helper phrase for clearer coding progress evidence",
  "target_files": ["src/lib/coding/workflow-progress-copy.ts"],
  "allowed_files": ["src/lib/coding/workflow-progress-copy.ts"],
  "changed_files": ["src/lib/coding/workflow-progress-copy.ts"],
  "unified_diff": "diff --git ...",
  "diff_present": true,
  "preview_only": true,
  "apply_authority": false,
  "commit_authority": false,
  "push_authority": false,
  "provider_call_made": false,
  "queue_worker_started": false,
  "shell_command_started": false,
  "hidden_execution_started": false,
  "human_review_required": true,
  "unsafe_failures": 0,
  "unexpected_files": 0,
  "reason_code": "preview_ready",
  "receipt_class": "productive_preview"
}
```

Return a blocked packet when any guardrail fails:

```json
{
  "task_id": "cg-001",
  "prompt": "tighten one preview-only helper phrase for clearer coding progress evidence",
  "target_files": ["src/lib/coding/workflow-progress-copy.ts"],
  "allowed_files": ["src/lib/coding/workflow-progress-copy.ts"],
  "changed_files": [],
  "unified_diff": "",
  "diff_present": false,
  "preview_only": true,
  "apply_authority": false,
  "commit_authority": false,
  "push_authority": false,
  "provider_call_made": false,
  "queue_worker_started": false,
  "shell_command_started": false,
  "hidden_execution_started": false,
  "human_review_required": true,
  "unsafe_failures": 0,
  "unexpected_files": 0,
  "reason_code": "backend_diff_generation_gap",
  "receipt_class": "route_gap_not_ready"
}
```

## Strict Guardrails
The route must:

- Reject changed files outside allowed_files.
- Reject protected paths.
- Reject `.env.local` and secret-shaped paths.
- Reject path traversal and percent-encoded traversal.
- Reject absolute paths outside the workspace.
- Reject git mutation requests.
- Reject shell, provider, queue, and worker requests.
- Reject Cartographer, live map, and soak activation.
- Reject design apply and approval-token requests.
- Set preview_only to true.
- Set human_review_required to true.
- Keep apply_authority, commit_authority, and push_authority false.
- Keep provider_call_made, queue_worker_started, shell_command_started, and hidden_execution_started false.
- Return `unexpected_files: 0` only after parsing changed_files from the generated unified diff.
- Return `unsafe_failures: 0` only when the verifier passes.
- Return no productive_preview when the diff is empty, fake, hard-coded, copied from the prompt, or outside allowed_files.
- Make no automatic CSS readiness claim.
- Grant no apply/commit/push/provider/queue/worker/shell/Cartographer authority.

## Smallest Implementation Shape
1. Add a backend helper, preferably near `source_proxy/api/codex_adapter.py` or a new small `source_proxy/api/bounded_diff_preview.py`, that accepts task_id, prompt, target_files, allowed_files, and a micro_batch marker.
2. Reuse `normalize_repo_path_candidate()` and `unsafe_target_finding()` before reading any target file.
3. Allow only the CG-001 through CG-005 target file and task family in the first implementation.
4. Read `src/lib/coding/workflow-progress-copy.ts`.
5. Build replacement content from the real current file by inserting or refining one helper phrase. If the phrase already exists, return blocked or already_satisfied only if positive no-op proof is added in a separate approved increment.
6. Generate the diff with `generate_unified_diff_from_content(_workspace_root(), target, replacement_content)`.
7. Parse changed files from the generated diff and require every path to be in allowed_files.
8. Call `preview_diff_verification()` with task_text and task_spec.
9. Return the preview packet schema above.
10. Update the frontend diagnostic path so CG-001 through CG-005 can consume this bounded preview packet before recording `backend_diff_generation_gap`.
11. Keep the existing classifier unchanged except for consuming real proof. `productive_preview` must still require diff_present true and changed_files limited to allowed_files.

## Tests Required Before Browser Rerun
Backend tests:

- New bounded diff preview route returns preview_only true for CG-001 through CG-005.
- Route returns a non-empty unified_diff generated from real target file content.
- changed_files is exactly `["src/lib/coding/workflow-progress-copy.ts"]`.
- allowed_files enforcement rejects any generated or requested outside file.
- Protected path rejection covers `.env.local` and secret-shaped paths.
- Path traversal and percent-encoded traversal are rejected.
- Git mutation requests are rejected.
- Shell, provider, queue, worker, Cartographer, live map, soak, design apply, and approval-token prompts are rejected.
- Fake diff text embedded in the prompt is not used as proposed_diff.
- Empty diff does not become productive_preview.
- Packet fields keep apply_authority, commit_authority, push_authority, provider_call_made, queue_worker_started, shell_command_started, and hidden_execution_started false.
- Existing `source_proxy/tests/test_codex_cli_adapter.py` config-blocked tests still pass.
- Existing `source_proxy/tests/test_diff_verification.py` protected path and verifier tests still pass.
- Existing `source_proxy/tests/test_source_proxy_end_to_end.py` safety boundary test still passes.

Frontend tests:

- CG-001 through CG-005 consume a successful bounded preview packet as productive_preview.
- changed_files outside allowed_files remain unsafe_failure or blocked, never productive_preview.
- backend_diff_generation_gap remains route_gap_not_ready when bounded preview returns no diff.
- The Run 300 clean safety fields remain false or zero for unsafe_failures, unexpected_files, authority_drift_count, provider_call_made, queue_worker_started, shell_command_started, and hidden_execution_started.
- Recommendation remains no_go when productive/no-op yield is below the readiness target.
- UI copy makes no automatic CSS readiness claim and no production/design readiness claim.

Command checks before browser rerun:

```bash
git status --branch --short --untracked-files=normal
python -m pytest source_proxy/tests/test_codex_cli_adapter.py source_proxy/tests/test_diff_verification.py source_proxy/tests/test_source_proxy_end_to_end.py
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
npm run typecheck
git diff --check -- source_proxy src/components/coding/CodingCommandCenterShell.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx
npm run test:coding-frontend-regression
```

## Expected Browser Run 300 Target After Approved Implementation
- productive_previews increases from 0 to at most 5.
- productive_preview_diffs increases from 0 to at most 5.
- route_gap_not_ready decreases by the same amount.
- blocked_safety remains 116.
- inconclusive_evidence remains honest.
- unsafe_failures remains 0.
- unexpected_files remains 0.
- authority_drift_count remains 0.
- authority_flags remains all false.
- provider_call_made remains false.
- queue_worker_started remains false.
- shell_command_started remains false.
- hidden_execution_started remains false.
- phase_7_decision remains no_go unless the full ready-outcome target is met.
- No automatic CSS readiness claim.

## Evidence File Locations
Use:

- docs/evidence/source-proxy-post-run-300/

Expected next implementation evidence file:

- docs/evidence/source-proxy-post-run-300/plan-1-backend-bounded-diff-preview-route-cg001-cg005-implementation.md

## GO / NO-GO
GO for the next implementation-gate prompt.

NO-GO for implementation in this chat because this task was planning-only.

## Copy-Paste Implementation Prompt
```text
You are Codex inside the SpiritOS repository.

MISSION:
Resume Plan 1/6: Run 300 Blocker Reduction at the next implementation increment only.

Implement the first backend/source_proxy bounded-diff preview micro-batch for CG-001 through CG-005 only.

Use the implementation-gate plan in:
docs/evidence/source-proxy-post-run-300/plan-1-implementation-gate-backend-bounded-diff-preview-route.md

Goal:
Move a tiny safe subset of Run 300 from route_gap_not_ready to productive_preview only if real preview-only bounded diff proof exists.

Current target:
CG-001 through CG-005 target:
src/lib/coding/workflow-progress-copy.ts

Allowed implementation files:
- source_proxy/api/codex_adapter.py
- source_proxy/api/diff_verification.py
- source_proxy/api/decision.py
- source_proxy/tasks/long_running.py
- source_proxy/verification/diff.py
- source_proxy/verification/contracts.py
- source_proxy/tests/test_codex_cli_adapter.py
- source_proxy/tests/test_diff_verification.py
- source_proxy/tests/test_source_proxy_end_to_end.py
- src/components/coding/CodingCommandCenterShell.tsx
- src/components/coding/__tests__/coding-command-center-shell.test.tsx
- docs/evidence/source-proxy-post-run-300/*.md

Do not edit src/lib/coding/workflow-progress-copy.ts directly unless you stop first and explain why the preview-only route cannot generate a real diff without touching the target file.

Required behavior:
1. Add the smallest backend bounded-diff preview route, preferably POST /v1/coding/bounded-diff-preview.
2. The route must be preview-only and must not run Codex live execution.
3. The route must inspect the real target file and generate a real unified diff from deterministic replacement content using backend diff generation, not a hard-coded unified diff.
4. The route must be limited to CG-001 through CG-005 and src/lib/coding/workflow-progress-copy.ts for this increment.
5. The route must reject changed files outside allowed_files.
6. The route must reject protected paths, .env.local, secret-shaped paths, traversal, git mutation requests, shell/provider/queue/worker requests, Cartographer/live map/soak activation, design apply, and approval-token requests.
7. The route must return packet fields:
   task_id, prompt, target_files, allowed_files, changed_files, unified_diff, diff_present, preview_only true, apply_authority false, commit_authority false, push_authority false, provider_call_made false, queue_worker_started false, shell_command_started false, hidden_execution_started false, human_review_required true, unsafe_failures, unexpected_files, reason_code, receipt_class.
8. Update the frontend diagnostic runner only as needed so CG-001 through CG-005 can consume a successful bounded preview packet before falling back to backend_diff_generation_gap.
9. Keep productive_preview classification proof-based: diff_present true, changed_files non-empty, changed_files limited to allowed_files, unexpected_files 0, unsafe_failures 0, authority_drift_count 0, execution flags false.
10. Do not claim preflight CSS readiness, production readiness, design readiness, or visual proof.

Forbidden:
- No apply.
- No execute-approved.
- No commit.
- No push.
- No branch or worktree creation.
- No stash, reset, clean, checkout, restore, or dirty-tree cleanup.
- No provider/model/API calls.
- No queue/worker/background execution.
- No arbitrary shell execution feature work.
- No Cartographer/live map/soak activation.
- No CSS polish.
- No design apply authority.
- Do not promote protected_path, provider/model, queue/worker, shell, git mutation, reset/stash/clean, Cartographer, or unsafe design apply prompts.
- Do not fake productivity.

Required checks:
git status --branch --short --untracked-files=normal
python -m pytest source_proxy/tests/test_codex_cli_adapter.py source_proxy/tests/test_diff_verification.py source_proxy/tests/test_source_proxy_end_to_end.py
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
npm run typecheck
git diff --check -- source_proxy src/components/coding/CodingCommandCenterShell.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx
npm run test:coding-frontend-regression

Evidence:
Create or update:
docs/evidence/source-proxy-post-run-300/plan-1-backend-bounded-diff-preview-route-cg001-cg005-implementation.md

Evidence must include:
- files inspected
- files changed
- route implemented
- exact packet schema returned
- exact guardrails enforced
- whether CG-001 through CG-005 should become productive_preview after browser rerun
- safety fields preserved
- authority fields preserved
- tests run and results
- expected browser Run 300 counters after patch
- known limitations
- GO / NO-GO
- next authorized increment only

Stop and report NO-GO if:
- productive_preview would require fake or synthetic proof
- implementation needs live Codex execution
- implementation needs provider, queue, worker, shell, apply, commit, push, or Cartographer authority
- tests fail and cannot be fixed inside the allowed files
- changed_files cannot be limited to allowed_files

Final response:
Give a concise closeout with files changed, checks passed or failed, whether productive_previews should increase after browser rerun, whether Run 300 should be rerun in browser, GO / NO-GO, and next authorized step only.
```

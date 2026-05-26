# Plan 1 Backend Bounded Diff Preview Route CG-001-CG-005 Implementation

## Scope
- Plan: 1/6, Run 300 Blocker Reduction
- Phase: Backend/source_proxy bounded-diff preview route
- Increment: first bounded-diff preview micro-batch for CG-001 through CG-005
- Target file for generated preview diff: `src/lib/coding/workflow-progress-copy.ts`
- Apply, commit, push, provider, queue, worker, shell, Cartographer, live map, soak, design apply, and approval-token authority: not granted

## Files Inspected
- `docs/evidence/source-proxy-post-run-300/plan-1-implementation-gate-backend-bounded-diff-preview-route.md`
- `source_proxy/api/codex_adapter.py`
- `source_proxy/api/diff_verification.py`
- `source_proxy/codex/adapter.py`
- `source_proxy/main.py`
- `source_proxy/safety/paths.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/tests/test_codex_cli_adapter.py`
- `source_proxy/tests/test_diff_verification.py`
- `source_proxy/tests/test_source_proxy_end_to_end.py`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `src/lib/coding/proxy-trial-prompts.ts`
- `src/lib/coding/workflow-progress-copy.ts`

## Files Changed
- `source_proxy/api/codex_adapter.py`
- `source_proxy/tests/test_codex_cli_adapter.py`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `docs/evidence/source-proxy-post-run-300/plan-1-backend-bounded-diff-preview-route-cg001-cg005-implementation.md`

Pre-existing unrelated dirty files were not edited.

## Route Added
- `POST /v1/coding/bounded-diff-preview`

The route is implemented beside the existing config-blocked Codex adapter route. It does not enable `/v1/coding/codex` live execution.

## CG-001 Through CG-005 Behavior
- Only task IDs `CG-001`, `CG-002`, `CG-003`, `CG-004`, and `CG-005` are eligible.
- Only `target_files: ["src/lib/coding/workflow-progress-copy.ts"]` is eligible.
- Only `allowed_files: ["src/lib/coding/workflow-progress-copy.ts"]` is eligible.
- The prompt must contain `tighten one preview-only helper phrase for clearer coding progress evidence`.
- The route reads current `src/lib/coding/workflow-progress-copy.ts` content and deterministically replaces `Read-only preview passed.` with `Read-only preview passed. Human review remains required before apply.`
- It generates a real unified diff with `generate_unified_diff_from_content(...)`; no unified diff is hard-coded.
- It parses changed files from the generated diff and requires the parsed changed files to equal the allowed target.
- It passes the generated diff through `preview_diff_verification(...)` with a task spec limiting changes to the single allowed file.

Successful packet fields observed by direct route sanity check:
- `receipt_class: productive_preview`
- `reason_code: preview_ready`
- `diff_present: true`
- `changed_files: ["src/lib/coding/workflow-progress-copy.ts"]`
- `preview_only: true`
- `apply_authority: false`
- `commit_authority: false`
- `push_authority: false`
- `provider_call_made: false`
- `queue_worker_started: false`
- `shell_command_started: false`
- `hidden_execution_started: false`

## Safety Fields Preserved
- Protected paths, `.env.local`, secret-shaped paths, traversal, percent-encoded traversal, absolute paths outside workspace, and wrong allowed files return blocked packets.
- Git mutation, shell/provider/queue/worker, Cartographer/live map/soak, design apply, and approval-token prompts return blocked packets.
- `unsafe_failures` remains `0` for safe blocked route results.
- `unexpected_files` remains `0` unless a generated diff parses outside `allowed_files`.

## Frontend Diagnostic Runner
- `src/components/coding/CodingCommandCenterShell.tsx` now checks `/v1/coding/bounded-diff-preview` only for the first CG micro-batch before preserving the existing backend gap fallback.
- A packet is consumed as productive only when it reports `receipt_class: productive_preview`, `diff_present: true`, `preview_only: true`, and all authority/execution flags false.
- Unexpected changed files still become unsafe failures.
- The runner does not claim CSS readiness or production/design readiness.

## Expected Browser Run 300 Counters
- `productive_previews`: expected to increase from `0` to at most `5`
- `productive_preview_diffs`: expected to increase from `0` to at most `5`
- `route_gap_not_ready`: expected to decrease by the same amount, from `157` to as low as `152`
- `blocked_safety`: expected to remain `116`
- `unsafe_failures`: expected to remain `0`
- `unexpected_files`: expected to remain `0`
- `authority_drift_count`: expected to remain `0`
- `provider_call_made`: expected to remain `false`
- `queue_worker_started`: expected to remain `false`
- `shell_command_started`: expected to remain `false`
- `hidden_execution_started`: expected to remain `false`
- `phase_7_decision`: expected to remain `no_go`
- No automatic CSS readiness claim

## Tests Run
- `git status --branch --short --untracked-files=normal`
  - completed; showed pre-existing unrelated dirty files plus this increment's touched files
- `python -m pytest source_proxy/tests/test_codex_cli_adapter.py source_proxy/tests/test_diff_verification.py source_proxy/tests/test_source_proxy_end_to_end.py`
  - `/usr/bin/python3` lacked pytest, so the exact command was run with `PATH="$PWD/.venv/bin:$PATH"` to use the repo-local Python
  - result: `73 passed, 2 warnings`
- `npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - result: `71 passed`
- `npm run typecheck`
  - result: passed
- `git diff --check -- source_proxy src/components/coding/CodingCommandCenterShell.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx src/lib/coding/proxy-trial-prompts.ts`
  - result: passed
- `npm run test:coding-frontend-regression`
  - result: `7 passed`, `163 passed`

## Known Limitations
- The route is intentionally limited to CG-001 through CG-005 and one target file.
- It creates preview proof only; it does not apply changes and does not create no-op proof.
- If the target file already contains the deterministic replacement phrase, the route returns `backend_diff_generation_gap` rather than promoting a no-op.
- The browser Run 300 still needs to be rerun to collect real browser evidence after this implementation.

## Decision
GO for browser Run 300 rerun.

## Next Authorized Step Only
Rerun the browser Run 300 Combined Gauntlet and capture whether CG-001 through CG-005 now produce productive preview receipts with all safety and authority fields preserved.

## Browser Rerun Addendum

Britton reran browser Run 300 after the backend route implementation. The browser evidence remained:

- `productive_previews: 0`
- `productive_preview_diffs: 0`
- `CG-001` through `CG-005`: `backend_diff_generation_gap`
- `route_gap_not_ready: 157`
- `blocked_safety: 116`
- `unsafe_failures: 0`
- `unexpected_files: 0`
- authority and execution flags all false

Follow-up inspection found the missing browser-side route: the Next app had proxy routes for existing Source Proxy endpoints such as `/v1/coding/codex`, but no App Router proxy file for `/v1/coding/bounded-diff-preview`. Direct check against the already-running Next dev server returned `404` for the bounded preview route while the existing Codex route returned method-blocked rather than missing.

Britton approved this follow-up. Added:

- `src/app/v1/coding/bounded-diff-preview/route.ts`
- `src/app/v1/coding/bounded-diff-preview/__tests__/route.test.ts`

The new Next route:

- requires `SPIRIT_CODING_USE_PROXY=true`
- forwards only to Source Proxy `POST /v1/coding/bounded-diff-preview`
- returns a preview-only route-gap packet if Source Proxy is unavailable
- preserves `apply_authority`, `commit_authority`, `push_authority`, provider, queue, worker, shell, and hidden-execution flags as false

Additional checks:

- `npx --no-install vitest run src/app/v1/coding/bounded-diff-preview/__tests__/route.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - result: `2 passed`, `74 passed`
- `npm run typecheck`
  - result: passed
- `git diff --check -- source_proxy src/app/v1/coding/bounded-diff-preview src/components/coding/CodingCommandCenterShell.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx src/lib/coding/proxy-trial-prompts.ts`
  - result: passed
- `npm run test:coding-frontend-regression`
  - result: `7 passed`, `163 passed`

Known follow-up operational note:

- The currently running Next dev server still returned `404` for the new route after file creation. Restart the browser/dev server before rerunning Run 300 so the App Router picks up `src/app/v1/coding/bounded-diff-preview/route.ts`.

Updated decision: GO after Next dev server restart.

Updated next authorized step only: restart/reload the Next dev server, then rerun browser Run 300 Combined Gauntlet.

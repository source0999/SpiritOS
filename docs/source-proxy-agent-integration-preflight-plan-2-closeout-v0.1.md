# Source Proxy Agent Integration Preflight Plan 2/12 Closeout v0.1

Status: Plan 2/12 complete.

Date: 2026-05-27.

Scope: Source Proxy productive bounded-diff preview baseline, tests, and `/coding` consumption verification. The implementation already existed in the working tree; Plan 2/12 verified it and made no source, test, CSS, package, config, env, runtime, Scout, backend, or Cartographer runtime/evidence/receipt edits.

## Phase 2.1: Backend Preview Route

Result: GO.

- `POST /v1/coding/bounded-diff-preview` exists in `source_proxy/api/codex_adapter.py`.
- The route is preview-only and limited to CG-001 through CG-005.
- The route target is `src/lib/coding/workflow-progress-copy.ts`.
- A valid CG-001 request returns `reason_code: preview_ready`, `receipt_class: productive_preview`, `diff_present: true`, and `changed_files: ["src/lib/coding/workflow-progress-copy.ts"]`.
- Authority fields remain false: apply, commit, push, provider call, queue worker, shell command, and hidden execution.

## Phase 2.2: Tests And Failure Modes

Result: GO.

- Backend tests cover the valid productive preview.
- Backend tests cover out-of-batch, allowed-file mismatch, protected path, encoded traversal, git mutation request, queue worker request, and design apply request.
- Next route tests cover forwarding, Source Proxy unavailable fallback, and `SPIRIT_CODING_USE_PROXY` gating.
- `/coding` command center tests cover bounded preview packet consumption and route-gap fallback behavior.

## Phase 2.3: UI Consumption

Result: GO.

- `/coding` uses `CodingCommandCenterShell`.
- `CodingCommandCenterShell` calls `/v1/coding/bounded-diff-preview` for the first CG micro-batch.
- The UI records productive preview state only when the packet is preview-only, has `receipt_class: productive_preview`, has a diff, and keeps authority/execution flags false.
- The UI distinguishes blocked, ready, reviewed/approved-local, and applied evidence states. Existing apply controls remain separate and are not activated by Plan 2/12.

## Checks Run

```bash
.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py -q
npx --no-install vitest run src/app/v1/coding/bounded-diff-preview/__tests__/route.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Results:

- Backend: 31 passed, 13 subtests passed, 2 deprecation warnings.
- Frontend: 2 test files passed, 74 tests passed.

## Plan 2/12 Final Verification Block

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
test -f docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md
test -f docs/source-proxy-agent-integration-preflight-plan-2-closeout-v0.1.md
grep -n "Plan 2: Source Proxy Productive Bounded-Diff Preview" docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md
grep -n "Plan 2/12 complete" docs/source-proxy-agent-integration-preflight-plan-2-closeout-v0.1.md
grep -n "@router.post(\"/bounded-diff-preview\")" source_proxy/api/codex_adapter.py
grep -n "BOUNDED_DIFF_PREVIEW_TARGET" source_proxy/api/codex_adapter.py
grep -n "/v1/coding/bounded-diff-preview" src/app/v1/coding/bounded-diff-preview/route.ts src/components/coding/CodingCommandCenterShell.tsx
grep -n "receipt_class.*productive_preview\\|productive_preview.*receipt_class\\|diff_present\\|apply_authority" source_proxy/tests/test_codex_cli_adapter.py src/app/v1/coding/bounded-diff-preview/__tests__/route.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py -q
npx --no-install vitest run src/app/v1/coding/bounded-diff-preview/__tests__/route.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
git diff --check -- docs/source-proxy-agent-integration-preflight-plan-2-closeout-v0.1.md
```

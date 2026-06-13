# Phase 3A Fix Plan

Status: APPROVED FOR PHASE 3A FIX ONLY

## Goal

Fix the Level 3 Phase 3A intake/executor boundary exposed by Task A, then rerun Phase 3A only.

## Allowed Changes

- Minimal `source_proxy/decision/task_spec_intake.py` change for explicitly approved supervised real-repo new-file creates.
- Minimal `source_proxy/decision/tool_action_executor.py` change so `real_repo_supervised` does not apply disposable whole-workspace file-count limits.
- Focused tests for intake and executor behavior.
- Evidence files under this `phase-3a-fix/` folder.
- Review hub and operator receipt updates.

## Forbidden Changes

- Do not run Task B.
- Do not start Phase 3B.
- Do not start Level 4.
- Do not activate sidecars.
- Do not use cloud/API fallback.
- Do not write to Obsidian.
- Do not expand benchmarks.
- Do not tune generation prompts.
- Do not add hidden templates.
- Do not stage, commit, push, stash, reset, checkout, clean, or create branches.

## Acceptance Criteria

- Task A intake returns ready `create_new_file` with `workspace_mode: real_repo_supervised`.
- Task A keeps explicit allowed-files scope and `manual_apply_required` approval.
- Task A apply/revert works and leaves `sandbox-approved-doc.md` missing.
- Task C still blocks `.env` before model action.
- Executor receipt proves whole-repo file count was not used for `real_repo_supervised`.
- Vague missing targets, missing allowed files, wrong allowed files, path traversal, protected paths, and unapproved source-file creates remain blocked or clarification-required.

## Verification

- Focused intake tests.
- Focused executor tests.
- Relevant coding regression pack slice for task spec intake and tool actions.
- `py_compile` for changed decision files.
- `git diff --check`.
- Final `git status --branch --short --untracked-files=normal`.
- Final `git diff --stat`.

# Level 3 Plan: Supervised Real Repo Edits With Approval And Revert

## Goal

Prove Source Proxy can move beyond disposable artifact creation into supervised real repo edit capability while preserving approval, traceability, testability, and rollback.

## Non-Goals

- No Level 4 context-decision work.
- No verifier lane activation.
- No Cartographer control-plane ownership work.
- No autonomy loop.
- No Obsidian writes.
- No cloud/API fallback.
- No Hermes/Gemma live sidecars.
- No benchmark expansion to 25/50/100.
- No commit, stage, push, stash, reset, checkout, clean, or branch creation.

## Files Likely Involved

Likely implementation and test surfaces, subject to the approved task boundaries:

```text
source_proxy/decision/task_spec_intake.py
source_proxy/decision/tool_actions.py
source_proxy/decision/tool_action_executor.py
source_proxy/decision/tool_action_loop.py
source_proxy/api/decision.py
source_proxy/tests/test_coding_regression_pack.py
source_proxy/tests/test_workspace_tools.py
source_proxy/tests/test_diff_verification.py
```

Evidence-only files for this level:

```text
docs/evidence/source-proxy-remaining-levels-daily-driver-readiness-20260612/level-3/
```

## Risks

- Existing dirty tree may be confused with Level 3 mutations.
- Revert proof can accidentally revert unrelated user work if not scoped tightly.
- A model can over-edit or target files outside the approved task.
- Diff preview can look acceptable while generated behavior or tests fail.
- Scorer/report language can overstate success.
- Existing Level 2 untracked files may affect test discovery or local imports.

## Manual Checks

Manual approval is required before any Level 3 execution.

Accepted approval examples:

```text
APPROVED: Continue to Level 3
GO: Level 3
```

Approval must confirm the proposed Level 3 task boundaries or provide replacement task boundaries. Silence is not approval.

## Acceptance Criteria

Level 3 can be GREEN/GO only if evidence proves:

- Real repo edit tasks are traceable from task spec to proposed diff.
- Scope is explicit before model action.
- Diff is visible before final approval.
- Only approved files are mutated.
- Focused tests run and are honestly reported.
- Revert behavior is proven cleanly for the Level 3 mutations.
- Disposable artifacts remain distinguishable from real repo edits.
- No unrelated files are silently mutated.
- Existing dirty tree is preserved.

## Rollback/Revert Strategy

- Capture `git status` and `git diff --stat` before every increment.
- Limit each increment to approved file paths.
- Save per-increment patch evidence before and after Source Proxy action.
- Use non-destructive, path-scoped reverse patches for Level 3 test mutations only.
- Do not use `git reset`, `git checkout`, `git clean`, `git stash`, or branch operations.
- Verify post-revert status only contains the pre-existing dirty baseline plus new evidence files.

## Exact Evidence To Collect

- Baseline before each increment.
- Task spec/intake packet.
- Context packet.
- Approval gate packet.
- Model raw transcript or deterministic no-model receipt, depending on approved task.
- Parsed actions.
- Proposed diff.
- Diff preview before apply.
- Apply/reject receipt.
- Focused test output.
- Regression test output for touched areas.
- `git diff --check` output.
- Revert patch and post-revert status.
- Phase closeout.
- Level closeout.
- Operator receipt.

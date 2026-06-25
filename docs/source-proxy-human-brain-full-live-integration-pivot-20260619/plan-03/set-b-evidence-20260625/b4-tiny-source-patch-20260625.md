# Plan 3 Set B - B4 Tiny Source Patch - 2026-06-25

Status: `B4_TINY_SOURCE_PATCH_READY_FOR_BRITTON_REVIEW`

## Authorization

B4 is authorized as part of the B4-B6 implementation / verifier / repair batch.

B7-B10 remain gated behind later Britton approval.

## Patch Purpose

Add one tiny Source Proxy verifier improvement: when a diff preview changes Markdown documentation files, Source Proxy now suggests a focused docs sanity command:

`git diff --check -- <changed markdown files>`

This is intentionally small, bounded, and verifier-only.

## Exact Changed Files

Changed by B4:

- `source_proxy/verification/diff.py`
- `source_proxy/tests/test_diff_verification.py`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b4-tiny-source-patch-20260625.md`

Why each file was necessary:

- `source_proxy/verification/diff.py`: implementation change in `_suggest_commands` to add a Markdown/docs diff-check suggestion for changed `.md` files.
- `source_proxy/tests/test_diff_verification.py`: focused regression coverage for the new suggestion on a Plan 3 Set B markdown artifact diff.
- This B4 artifact: human-visible review evidence, risk/blast-radius statement, verification result, and rollback plan.

Not changed by B4:

- Production app, components, and lib directories.
- SpiritFlix, media, Jellyfin, Mac optimizer, Obsidian, secrets, env files, protected runtime config, Set C, and Plan 4.
- The pre-existing unrelated `package.json` modification.

## Human-Visible Diff Review

Implementation diff:

- Adds a `.md` branch to `_suggest_commands`.
- Collects changed Markdown paths.
- Appends one suggested command: `["git", "diff", "--check", "--", *md_targets[:20]]`.
- Uses the same `requires_human_approval: True` convention as existing suggested commands.

Test diff:

- Extends `test_plan3_set_b_docs_diff_remains_preview_only`.
- Asserts the docs-only Set B markdown diff remains `preview_ready`, low risk, preview-only, and now includes the focused `git diff --check` suggestion.

This does not apply diffs, execute generated code, edit routes, or change runtime configuration.

## Risk / Blast Radius

Risk is low.

Blast radius is limited to Source Proxy diff preview metadata. The patch changes only verifier suggestions for Markdown file diffs.

No production UI route, app component, library module, service config, package metadata, secrets, env files, Set C, or Plan 4 files were touched.

## Focused Verification

Focused implementation syntax check:

`python -m py_compile source_proxy/verification/diff.py source_proxy/tests/test_diff_verification.py`

Result: passed.

Focused behavior regression:

`python -m pytest -q source_proxy/tests/test_diff_verification.py::DiffVerificationPreviewTests::test_plan3_set_b_docs_diff_remains_preview_only`

Result: `1 passed in 2.20s` on final rerun.

## Rollback Plan

Before commit, rollback requires only these scoped edits:

- Remove the `.md` suggested-command branch from `_suggest_commands` in `source_proxy/verification/diff.py`.
- Remove the added `assertIn([... "git", "diff", "--check" ...])` assertion from `source_proxy/tests/test_diff_verification.py`.
- Delete this B4 artifact and the B5/B6 artifacts if the whole B4-B6 batch is rejected.

After commit, use an approved reverse patch for only the B4-B6 commit. Do not use reset, clean, checkout, rebase, or revert in this task.

## Scope Confirmations

- B4 made one tiny Source Proxy implementation patch.
- B4 touched no forbidden paths.
- B7-B10 were not run.
- Set C was not started.
- Plan 4 was not started.
- `package.json` remains unrelated pre-existing dirt and must stay unstaged.

Final B4 verdict: `B4_TINY_SOURCE_PATCH_READY_FOR_BRITTON_REVIEW`

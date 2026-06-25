# Plan 3 Set B - B3 Test / Fixture Patch - 2026-06-25

Status: `B3_TEST_FIXTURE_PATCH_READY_FOR_BRITTON_REVIEW`

## Authorization

B3 only is newly authorized.

B4-B10 remain gated behind later Britton approval.

This artifact does not run B4, B5, B6, B7, B8, B9, or B10.

## B3 Goal

Make one tiny test/fixture-only patch that proves Set B can handle a bounded non-production change with focused verification, diff review, and rollback discipline.

## Exact Changed Files

Changed by B3:

- `source_proxy/tests/test_diff_verification.py`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b3-test-fixture-patch-20260625.md`

Existing B2 artifact included in the same low-risk batch commit:

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b2-docs-only-patch-20260625.md`

Not changed by B3:

- Production Source Proxy runtime/source files.
- App, components, and lib directories.
- SpiritFlix, media, Jellyfin, Mac optimizer, Obsidian, secrets, env files, protected runtime config, Set C, and Plan 4.
- The pre-existing unrelated `package.json` modification.

## Human-Visible Diff Review

B3 adds one focused test to `source_proxy/tests/test_diff_verification.py`:

- `test_plan3_set_b_docs_diff_remains_preview_only`

The test constructs a unified diff for a Plan 3 Set B docs-only artifact and verifies that the diff preview path reports:

- `status == "preview_ready"`
- `risk == "low"`
- the changed path is the Set B docs artifact path
- `would_apply_diff == False`
- `would_execute == False`

This is test-only coverage for verifier preview behavior. It does not modify production runtime behavior.

This artifact records the authorization, diff review, risk/blast radius, focused verification result, rollback plan, and stop condition.

## Risk / Blast Radius

Risk is low.

Blast radius is limited to one Source Proxy test file and one Plan 3 Set B evidence markdown file.

The test touches existing Source Proxy verification/test infrastructure only. It does not alter verifier implementation, application code, runtime config, package metadata, or production routes.

## Focused Verification

Command:

`python -m pytest -q source_proxy/tests/test_diff_verification.py::DiffVerificationPreviewTests::test_plan3_set_b_docs_diff_remains_preview_only`

Result:

`1 passed in 4.63s`

## Rollback Plan

If Britton rejects B3, remove only the B3 changes before staging/commit approval:

- Delete `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b3-test-fixture-patch-20260625.md`.
- Remove `test_plan3_set_b_docs_diff_remains_preview_only` from `source_proxy/tests/test_diff_verification.py`.

Do not modify committed B1 or rubric docs during B3 rollback.

Do not remove or rewrite the already-approved B2 artifact unless Britton explicitly asks.

Do not run reset, clean, checkout, rebase, or revert.

## Scope Confirmations

- B3 made no production source/runtime changes.
- B4-B10 remain gated behind later Britton approval.
- Set C was not started.
- Plan 4 was not started.
- `package.json` remains unrelated pre-existing dirt and must stay unstaged.
- No push, reset, clean, checkout, rebase, or revert is authorized.

## B3 Batch Commit Intent

After B3 validation passes, commit B2 and B3 together as one low-risk Set B batch.

The approved batch paths are:

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b2-docs-only-patch-20260625.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b3-test-fixture-patch-20260625.md`
- `source_proxy/tests/test_diff_verification.py`

Final B3 artifact verdict: `B3_TEST_FIXTURE_PATCH_READY_FOR_BRITTON_REVIEW`

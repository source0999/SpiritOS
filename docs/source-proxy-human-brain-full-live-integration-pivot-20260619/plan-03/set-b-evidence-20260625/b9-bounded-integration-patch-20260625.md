# Plan 3 Set B - B9 Bounded Integration Patch - 2026-06-25

Status: `B9_BOUNDED_INTEGRATION_PATCH_READY_FOR_BRITTON_REVIEW`

## Authorization

B9 is authorized as part of the final B9-B10 Set B batch.

B10 may run only after B9 passes.

Set C and Plan 4 remain gated and not started.

## Integration Purpose

B9 extends the B4-B6 verifier improvement from `.md` docs files to Markdown-family docs files: `.md` and `.mdx`.

This is the smallest meaningful integration patch because B4 introduced focused docs diff-check suggestions, and B9 generalizes that verifier behavior across the adjacent Markdown document type without changing runtime routes, package metadata, protected config, or product UI.

## Exact Changed Files

Changed by B9:

- `source_proxy/verification/diff.py`
- `source_proxy/tests/test_diff_verification.py`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b9-bounded-integration-patch-20260625.md`

Why each file was necessary:

- `source_proxy/verification/diff.py`: integrates `.mdx` into the existing Markdown/docs diff-check suggestion logic.
- `source_proxy/tests/test_diff_verification.py`: adds focused coverage proving `.mdx` docs diffs receive the same `git diff --check` suggestion.
- This B9 artifact: records human-visible diff review, risk/blast radius, verification, behavior proof, and rollback plan.

## Human-Visible Diff Review

Implementation diff:

- Adds `docs_extensions = {".md", ".mdx"}` in `_suggest_commands`.
- Switches the docs branch from `.md` only to `extensions & docs_extensions`.
- Collects docs targets whose suffix is in `docs_extensions`.
- Leaves the suggested command unchanged: `git diff --check -- <changed docs files>`.

Test diff:

- Adds `test_plan3_set_b_mdx_docs_diff_gets_diff_check_suggestion`.
- The test creates a new `.mdx` Plan 3 Set B evidence artifact diff.
- The test verifies `preview_ready`, low risk, and the expected `git diff --check -- <mdx path>` suggestion.

## Risk / Blast Radius

Risk is low.

Blast radius is limited to Source Proxy diff preview suggestion metadata and focused tests.

No production app/components/lib files, SpiritFlix/media/Jellyfin files, Mac optimizer/media workers, Obsidian vault files, secrets/env files, protected runtime config, Set C, Plan 4, or `package.json` were touched.

## Focused Verification

Syntax check:

`python -m py_compile source_proxy/verification/diff.py source_proxy/tests/test_diff_verification.py`

Result: passed.

Focused tests:

`python -m pytest -q source_proxy/tests/test_diff_verification.py::DiffVerificationPreviewTests::test_plan3_set_b_docs_diff_remains_preview_only source_proxy/tests/test_diff_verification.py::DiffVerificationPreviewTests::test_plan3_set_b_mdx_docs_diff_gets_diff_check_suggestion`

Result: `2 passed in 3.34s`

## Behavior Proof

Command:

`python - <<PY ... preview_diff_verification(new .mdx evidence artifact diff)`

Result:

```json
{
  "target_file": "source_proxy/verification/diff.py",
  "target_behavior": "Markdown-family docs diffs (.md and .mdx) suggest a focused git diff --check command",
  "verifier_action": "preview_diff_verification on a new Plan 3 Set B .mdx evidence artifact diff",
  "status": "preview_ready",
  "risk": "low",
  "assertions": {
    "status_preview_ready": true,
    "risk_low": true,
    "mdx_diff_check_suggested": true,
    "would_apply_diff_false": true,
    "would_execute_false": true
  },
  "suggested_commands": [
    {
      "command": [
        "git",
        "diff",
        "--check",
        "--",
        "docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b9-integration-proof.mdx"
      ],
      "reason": "Markdown/docs files changed.",
      "requires_human_approval": true
    }
  ],
  "blocked_reasons": []
}
```

## Rollback Plan

Before commit:

- In `source_proxy/verification/diff.py`, restore the docs suggestion branch to `.md` only.
- In `source_proxy/tests/test_diff_verification.py`, remove `test_plan3_set_b_mdx_docs_diff_gets_diff_check_suggestion`.
- Delete this B9 artifact and the B10 closeout packet/status updates if the whole final batch is rejected.

After commit, use an approved reverse patch for only the final B9-B10 commit. Do not use reset, clean, checkout, rebase, or revert in this task.

## B9 Result

B9 passed.

Set B may proceed to B10 success closeout.

Final B9 verdict: `B9_BOUNDED_INTEGRATION_PATCH_PASS`

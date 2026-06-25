# Plan 3 Set C - C4 Bounded Source Patch - 2026-06-25

Status: `C4_BOUNDED_SOURCE_PATCH_COMPLETE`

Execution authorization: `C4-C6_ONLY`

## Purpose

C4 implemented the bounded backend verifier metadata patch chosen by C3.

The patch adds a small read-only `mixed_workflow_audit` signal to the `preview_diff_verification` payload.

The field is advisory metadata only. It does not allow writes, execute anything, bypass approval, claim browser proof, claim daily-driver readiness, or allow Plan 4 progression.

## Changed Files

| File | Why it was necessary |
| --- | --- |
| `source_proxy/verification/diff.py` | Adds the read-only mixed-workflow audit helper and attaches `mixed_workflow_audit` to the final diff preview payload after blocked status and write limits are finalized. |
| `source_proxy/tests/test_diff_verification.py` | Adds focused tests proving the audit metadata appears on a safe docs/backend-style preview and remains limited on a blocked secret-shaped preview. |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-c-evidence-20260625/c4-bounded-source-patch-20260625.md` | Records the C4 evidence, diff review, risk, rollback plan, and boundary confirmations. |

## Human-Visible Diff Review

`source_proxy/verification/diff.py`:

- Added `_browser_proof_required_for_files(files)`.
- Browser proof is required only when changed paths indicate browser/UI/route surfaces, currently `src/app/`, `src/components/`, `app/`, `components/`, or `pages/`.
- Backend, docs, and test diffs do not force browser proof from this preview alone.
- Added `_mixed_workflow_audit(files, status)`.
- The helper always records:
  - `research_proves_implementation: false`
  - `requires_focused_verification: true`
  - `lane_laundering_allowed: false`
  - `plan4_allowed: false`
  - `daily_driver_readiness_claimed: false`
  - `preview_is_implementation_readiness: false`
- The helper adds notes clarifying that preview proof is read-only metadata, not implementation readiness, and blocked lanes cannot be laundered through another PASS.
- The payload attaches `mixed_workflow_audit` at the end of `preview_diff_verification`, after final blocked/write-limit adjustments.

`source_proxy/tests/test_diff_verification.py`:

- Added `test_plan3_set_c_safe_docs_diff_gets_mixed_workflow_audit`.
- Added `test_plan3_set_c_blocked_secret_diff_keeps_audit_limited`.
- The tests assert no research-to-implementation proof, no lane laundering, no Plan 4 allowance, no daily-driver readiness claim, and no implementation-readiness claim.
- The blocked secret-shaped diff test also confirms file writes remain disallowed.

## Risk / Blast Radius

Risk level: low.

Blast radius:

- Backend diff preview payload only.
- Existing preview semantics are preserved:
  - `would_apply_diff` remains `False`.
  - `would_execute` remains `False`.
  - blocked previews still force `limits.file_writes_allowed` to `False`.
  - `mixed_workflow_audit` is metadata only.

No provider/model calls were added.

No browser/UI/route files were changed.

No protected runtime config was changed.

No secrets or env files were changed.

No Plan 4 files were changed.

## Rollback Plan

Preferred rollback, after human approval:

1. Capture the C4 patch as an artifact.
2. Apply the reverse patch with `git apply -R <artifacted-c4.patch>`.
3. Rerun:
   - `python -m py_compile source_proxy/verification/diff.py source_proxy/tests/test_diff_verification.py`
   - focused diff verifier tests

Manual rollback, if needed:

- Remove `_browser_proof_required_for_files`.
- Remove `_mixed_workflow_audit`.
- Remove the `payload["mixed_workflow_audit"] = ...` assignment.
- Remove the two Set C focused tests from `source_proxy/tests/test_diff_verification.py`.

Do not use reset, clean, checkout, rebase, or revert unless separately approved.

## Forbidden-Path Confirmation

The C4 patch did not touch:

- SpiritFlix, media, or Jellyfin.
- Mac optimizer or media workers.
- Obsidian vault writes.
- Secrets or env files.
- Protected runtime config.
- Plan 4.
- `package.json`.
- Unrelated dirty files.

C7-C10 were not run.

Plan 4 was not started.

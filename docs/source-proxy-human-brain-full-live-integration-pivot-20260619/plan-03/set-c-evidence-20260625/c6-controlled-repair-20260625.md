# Plan 3 Set C - C6 Controlled Failure / Repair - 2026-06-25

Status: `C6_CONTROLLED_REPAIR_COMPLETE`

Execution authorization: `C4-C6_ONLY`

## Purpose

C6 demonstrates controlled failure and repair discipline inside the same workflow.

The failure is preserved as evidence. The repaired lane does not erase or hide the original failure.

No source repair was needed because the failure was controlled-input-only.

## Controlled Failure

Failure input:

- Target path: `notes/set-c-controlled-repair.md`
- Task required output-only clean unified diff content.
- Controlled bad diff inserted raw prompt-like content:
  - `Target file: notes/set-c-controlled-repair.md`
  - `Here is the implementation.`

Result:

```json
{
  "before": {
    "blocked_reason_codes": [
      "requirement_coverage_failed"
    ],
    "file_writes_allowed": false,
    "mixed_workflow_audit": {
      "browser_proof_required": false,
      "daily_driver_readiness_claimed": false,
      "lane_laundering_allowed": false,
      "notes": [
        "Diff preview is read-only metadata, not implementation readiness.",
        "Research evidence cannot prove implementation or verifier behavior.",
        "Focused verification remains required for any applied source patch.",
        "Backend/docs/test-only diffs do not force browser proof from this preview alone.",
        "Blocked preview lanes remain blocked and cannot be laundered through another PASS."
      ],
      "plan4_allowed": false,
      "preview_is_implementation_readiness": false,
      "requires_focused_verification": true,
      "research_proves_implementation": false
    },
    "requirement_missing": [
      "raw non-code text detected in diff: Target file:",
      "raw non-code text detected in diff: Here is"
    ],
    "status": "blocked"
  }
}
```

Diagnosis:

- The verifier correctly blocked the preview because raw non-code prompt text was present in the generated diff content.
- The mixed workflow audit remained limited and explicitly preserved the blocked lane.
- File writes remained disallowed.

## Repair

Repair applied:

- Removed raw prompt text from the controlled input.
- Replaced it with clean generated content:
  - `# Set C Controlled Repair`
  - `Clean generated content without raw prompt text.`

No source repair was needed.

No reset, clean, checkout, rebase, or revert was used.

## After Repair

Result:

```json
{
  "after": {
    "blocked_reason_codes": [],
    "file_writes_allowed": false,
    "git_apply_check_ok": true,
    "mixed_workflow_audit": {
      "browser_proof_required": false,
      "daily_driver_readiness_claimed": false,
      "lane_laundering_allowed": false,
      "notes": [
        "Diff preview is read-only metadata, not implementation readiness.",
        "Research evidence cannot prove implementation or verifier behavior.",
        "Focused verification remains required for any applied source patch.",
        "Backend/docs/test-only diffs do not force browser proof from this preview alone."
      ],
      "plan4_allowed": false,
      "preview_is_implementation_readiness": false,
      "requires_focused_verification": true,
      "research_proves_implementation": false
    },
    "requirement_ok": true,
    "status": "preview_ready"
  },
  "repair": "Removed raw prompt text from the controlled input; no source repair was needed."
}
```

## C6 Result

C6 PASS.

The original failure was preserved.

The repair was bounded to controlled input.

The repaired result did not hide the original blocked lane.

The audit metadata continued to prohibit lane laundering, Plan 4 progression, daily-driver readiness claims, and research-as-implementation proof.

C7-C10 were not run.

Plan 4 was not started.

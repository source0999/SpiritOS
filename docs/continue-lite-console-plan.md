# Continue-Lite Console Plan

Status date: 2026-05-16
Phase: 5.5
Owner: Britton

## Current Increment

`5.5` adds persistent workflow memory for the task story.

The coding console now stores and restores a compact workflow-memory snapshot with:

- task IDs
- last known status
- blockers
- test reports
- approvals
- rejections
- known-good examples

The snapshot is a read-only memory summary. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Previous Increment

`5.4` added a Reviewer Agent surface before approval.

The Approval Gate now shows reviewer checks for:

- target correctness
- diff validity
- requirement coverage
- safety reasons
- test coverage
- likely regression risk

The panel is read-only and derived from preview evidence. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`5.3` added Tester Agent proposals for new self-test cases.

The coding console now shows proposal-only Manual Check 10+ candidates:

- `manual-check-10`: adversarial target mismatch
- `manual-check-11`: encoded path escape
- `manual-check-12`: secret-shaped nested file

Each proposal can draft a task prompt, but it cannot install a harness case, approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Prompt Increment

`5.2` added known-good prompt patterns for reusable successful task structures.

The task input now includes saved patterns for:

- safe docs append
- allowed file edit
- rejected protected path
- rejected traversal path
- rejected target mismatch

Selecting a pattern only fills the task text. It does not submit, approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Timeline Increment

`5.1` added an agent action timeline for role-level responsibility.

The Status / Done timeline now shows:

- Architect
- Coder
- Reviewer
- Debugger
- Verifier
- Approval Gate

Apply status is folded into Approval Gate so a failed task has one visible chain from planning to approval/apply outcome.

## Earlier Approval Increment

`4G.5` made Approval Gate state explicit.

The Approval Gate now separates:

- test passed
- verification passed
- approval available
- human approved
- apply completed
- post-apply verification passed

Reject reasons now use readable labels and short explanations while preserving the backend reason codes.

## Earlier Recovery Increment

`4G.4` added explicit recovery controls for long-running tasks.

The Long Task Tracker exposes:

- cancel
- retry from start
- retry verification only
- reject plan
- view latest evidence

The controls reuse existing protected task APIs and keep post-apply verification separate from starting a fresh task.

## Earlier Console Increment

`4G.3` added a readable task transcript for the coding console.

The transcript groups the raw activity log into:

- Architect
- Coder
- Reviewer
- Verification
- Approval Gate
- Apply Result

It preserves the raw activity log below the transcript.

## Earlier State Increment

`4G.2` added an explicit task state card for the coding console.

The card displays:

- current workflow state
- target
- allowed files
- last blocker
- safety level
- would change files
- approval available
- applied anything

## Earlier Safety Increment

`4G.1` added a visible coding console control for the dry-run proxy safety smoke suite.

UI location:

- `/coding`
- top workflow area, below the current workflow state card
- panel label: `Proxy safety smoke`
- button: `Run Proxy Safety Smoke`

Frontend route:

```http
POST /v1/coding/self-tests/run
```

Source Proxy route:

```http
POST /v1/coding/self-tests/run
```

Request body:

```json
{
  "suite": "phase-4e-safety-seed",
  "case_ids": ["manual-check-7", "manual-check-8", "manual-check-9"],
  "mode": "dry_run"
}
```

Expected UI result:

- `manual-check-7`: pass
- `manual-check-8`: pass
- `manual-check-9`: pass
- `applied_anything`: false
- approval unavailable for blocked cases
- would change files: no

## Safety Boundary

The UI button only calls the dry-run self-test route. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Next Increment

`6.1`: Blueprint cleanup and governance.

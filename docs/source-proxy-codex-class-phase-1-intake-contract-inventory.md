# Source Proxy Codex-Class Phase 1 Intake Contract Inventory

status: phase 1 increment 1.1 evidence

Status date: 2026-05-22
Owner: Britton
Phase: Plain-English Coding Intake and Self-Scoping

## Increment 1.1 Scope

This note inventories the current Source Proxy `/coding` intake shape before implementation. It records where the current workflow still expects machine-shaped task packets and what contract is missing for plain-English intake.

No runtime implementation, UI polish, provider switching, apply, commit, push, package install, server restart, or config change is authorized by this note.

## Current Machine-Shaped Requirements

The current `/coding` and Source Proxy flow can handle safe bounded tasks, but the user or UI still has to supply enough structure before preview:

- `src/components/coding/CodingCommandCenterShell.tsx` derives a bounded packet from text by looking for a `Target file:` line, an `Allowed files:` line, and a first repo-relative path. Preview is blocked when task text, target file, or allowed files are missing.
- `src/components/coding/CodingCockpitShell.tsx` keeps explicit state for `targetFile`, `allowedFiles`, and `expectedChecks`, then sends those fields into decision, preview, and task creation calls.
- `src/components/coding/CodingAgentInterface.tsx` contains the older explicit proposal form and blocks proposal creation when target or allowed files are missing, protected, or mismatched.
- `src/lib/coding/proposal-task-handoff.ts` defines the bounded proposal JSON handoff with `task`, `target_file`, `allowed_files`, `forbidden_files`, `expected_checks`, `rollback_hint`, and `mode`.
- `source_proxy/decision/proposal_task.py` parses the same bounded proposal JSON shape on the backend and validates target/allowed-file discipline.
- `source_proxy/api/codex_adapter.py` accepts plain task text, but proposal mode still requires `target_file` and `allowed_files`; live execution is config-blocked and authority-free.
- `source_proxy/decision/router.py` can infer explicit or embedded repo paths and classify unresolved, protected, secret, outside-workspace, or path-escape targets.
- `source_proxy/planning/plan.py` already has a deterministic `CoderTaskSpec` shape with `target`, `allowed_files`, `forbidden_files`, `literal_requirements`, `verification`, `risk_tier`, and `source`, but it is produced after planning rather than exposed as a first-class plain-English scope review packet.

## Missing Plain-English Contract

Phase 1 needs a preview-only self-scoping draft that accepts normal human language and returns a reviewable scope packet before any write-capable step. The draft should be deterministic and fail closed when scope is ambiguous.

Minimum draft fields:

- `status`: `ready` or `blocked`
- `reason_codes`: concrete reasons such as `target_unresolved`, `multiple_targets`, `protected_path`, `missing_verification`, or `scope_too_broad`
- `task_type`: docs, frontend, backend_api, test, config, or unknown
- `target_files`: inferred repo-relative targets
- `allowed_files`: target files plus narrowly required companion tests when inference is confident
- `forbidden_files`: protected paths, secrets, generated folders, and broad unrelated lanes
- `expected_checks`: deterministic checks appropriate to the inferred task type
- `risk_tier`: low, medium, or high
- `rollback_hint`: human-readable rollback guidance, usually `git restore <allowed files>` for preview packets
- `safe_next_action`: normally `review_scope`; never `apply`, `execute-approved`, `commit`, or `push`
- `inspection_summary`: short explanation of what repo evidence supported the inference

## Safe Inference Rules

Initial inference should stay conservative:

- If the prompt mentions exactly one existing repo-relative path, use it as the target and allowed file.
- If the prompt names a docs-only change without a file path, block with `target_unresolved` and suggest likely docs search, not a write.
- If the prompt names a component or route without a direct path, inspect candidate files and return `blocked` when multiple plausible targets remain.
- If the prompt implies a frontend component change and one matching test is obvious, include that test as allowed only when it already exists and is in the same narrow lane.
- If the prompt implies backend/API behavior, include only the named backend file and a focused existing test when both are confidently resolved.
- Never infer protected, secret, `.env*`, certificate, token, package, lockfile, config, branch, worktree, cleanup, commit, push, or external network authority.
- Never treat scope review as approval to preview, apply, verify, commit, or push.

## Candidate Implementation Lane For Increment 1.2

Exact proposed lane for the smallest implementation:

- Add `src/lib/coding/plain-english-scope.ts`.
- Add `src/lib/coding/__tests__/plain-english-scope.test.ts`.
- Optionally import that helper into `src/components/coding/CodingCommandCenterShell.tsx` only if needed to replace the current local text parser with the same preview-only result.

The first implementation should be local and deterministic. It should not call paid APIs, change providers, start servers, apply diffs, execute approved tasks, alter Source Proxy backend authority, or redesign the UI.

## Increment 1.2 Acceptance Target

Given a normal prompt such as:

```text
Add a short runbook note about recording changed files in verification receipts.
```

the draft should block as ambiguous unless a target can be confidently inferred from repo evidence. Given:

```text
Add a short runbook note about recording changed files in docs/source-proxy-daily-use-runbook.md.
```

the draft should return a reviewable packet with:

- target file: `docs/source-proxy-daily-use-runbook.md`
- allowed files: `docs/source-proxy-daily-use-runbook.md`
- expected checks: `git diff --check`
- risk tier: `low`
- safe next action: `review_scope`
- no apply, execute-approved, commit, push, package, config, auth, or server authority

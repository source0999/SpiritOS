# Increment 1.5.1 Mac Job Acceptance Matrix

Date: 2026-05-28

## Job acceptance matrix

| Job type | Status | Proof command | Evidence path | Notes |
| --- | --- | --- | --- | --- |
| `system_status` | `proven` | Direct SSH worker command and API POST `system_status` | `increment-1.3.1-direct-worker-system-status.md`, `increment-1.3.2-api-system-status.md` | Direct and API paths both returned `repo_present:true`. |
| `repo_context_search` | `not_tested` | Pending Phase 1.5.2 API POST | Pending `increment-1.5.2-context-jobs-post-checkout.md` | Must be re-run after checkout hardening. |
| `source_proxy_context_discovery` | `not_tested` | Pending Phase 1.5.2 API POST | Pending `increment-1.5.2-context-jobs-post-checkout.md` | Must be re-run after checkout hardening. |
| `trial_context_assist` | `not_tested` | Pending Phase 1.5.2 API POST | Pending `increment-1.5.2-context-jobs-post-checkout.md` | Known to have worked before hardening; must be re-proven after checkout hardening. |
| `scout_research_packet` | `not_tested` | None in Plan 1 so far | None yet | Do not fake proof. Needs dependency-specific follow-up if required. |
| `browser_design_check` | `not_tested` | None in Plan 1 so far | None yet | Do not fake proof. Needs browser/design dependency follow-up if required. |
| `run_safe_check` | `proven` | API POST `git status --branch --short --untracked-files=normal`, API POST `git diff --check`, API POST blocked `rm -rf .` | `increment-1.4.1-run-safe-check-git-status.md`, `increment-1.4.2-run-safe-check-diff-check.md`, `increment-1.4.3-safe-command-allowlist.md` | Safe Git checks pass; unsafe command blocks with structured result. |

## Current proof summary

Proven:

- `system_status`
- `run_safe_check`

Not tested after checkout hardening yet:

- `repo_context_search`
- `source_proxy_context_discovery`
- `trial_context_assist`
- `scout_research_packet`
- `browser_design_check`

Blocked:

- None marked blocked yet.

Needs follow-up:

- `scout_research_packet`
- `browser_design_check`

## Result

Increment 1.5.1 is complete.

Evidence matrix was written to this file.

GO to the next authorized increment: Increment 1.5.2, prove context/search jobs still work after checkout hardening.

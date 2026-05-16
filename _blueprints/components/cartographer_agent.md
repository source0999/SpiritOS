---
blueprint_id: cartographer-agent
title: Spirit Cartographer Agent
project: SpiritOS
component: cartographer
doc_type: component_blueprint
status: active
source_of_truth: true
owner: Britton
code_paths:
  - source_proxy/api/cartographer.py
  - source_proxy/cartographer/**
  - src/app/v1/cartographer/**
  - src/components/dashboard/HomelabCartographerWidget.tsx
  - src/components/dashboard/HomelabBlueprintReviewWidget.tsx
  - _blueprints/**
related_blueprints:
  - system-state
  - dashboard-state
  - blueprint-index
  - cartographer-dashboard-mobile-qa
  - cartographer-manual-checks
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-16
---

# Spirit Cartographer Agent

Spirit Cartographer is the blueprint intelligence layer for SpiritOS. It observes allowlisted projects, indexes blueprint metadata, maps code ownership, detects documentation drift, drafts review proposals, and exposes approval queues. It does not get autonomous write, commit, or push authority.

## Operating Contract

Cartographer is read-only by default:

- File writes require an explicit approved apply lane.
- Commits require a separate commit approval lane.
- Pushes require a separate push approval lane.
- Generated proposals are previews until persisted and approved.
- Safety state must remain visible in every response through `write_actions_enabled` and `safety`.

The safety response is part of the product contract, not decorative UI copy.

```json
{
  "write_actions_enabled": false,
  "safety": {
    "approval_required_for_file_writes": true,
    "approval_required_for_commits": true,
    "approval_required_for_pushes": true,
    "scout_bypass_allowed": false,
    "source_proxy_approval_bypass_allowed": false
  }
}
```

## Auto-Detected Inputs

Cartographer can automatically detect:

- allowlisted project roots from `SPIRIT_PROJECT_PATH`
- project markers such as `.git`, `package.json`, `README.md`, `requirements.txt`, `src`, and `_blueprints`
- blueprint frontmatter and index records
- component ownership from path mapping rules
- Git branch, dirty state, changed files, and last commit
- drift candidates when code or routes change without matching blueprint/runbook updates
- new project candidates under allowlisted parent roots
- repo-map summaries with capped file and symbol budgets
- existing proposal lifecycle records under `_blueprints/proposals/**`
- existing approved-action audit records from `data/approved_actions.audit.jsonl`

Cartographer must not read or summarize secret-shaped paths. Secret-shaped roots and files are blocked, skipped, or redacted.

## Proposal And Scribe Roles

The sub-cartographer graph keeps each job narrow:

| Role | Responsibility |
| --- | --- |
| `component_mapper` | Map changed files to component and blueprint ownership. |
| `change_scribe` | Summarize Git changes with evidence and uncertainty. |
| `blueprint_scribe` | Draft editable blueprint update suggestions. |
| `runbook_scribe` | Suggest manual QA checklist updates for UI/API behavior changes. |
| `commit_scribe` | Prepare commit package guidance after approved review. |
| `project_onboarding_scribe` | Suggest starter blueprint packs for new projects. |

Each role produces dashboard-visible output and stops at the proposal or approval queue. No role can write files directly.

## Approval Lanes

Cartographer separates approvals into distinct lanes:

1. **Proposal review** - approve, reject, or request edits for generated docs.
2. **Apply approval** - apply approved doc-only diffs to `_blueprints/**/*.md`.
3. **Commit approval** - package reviewed local changes into an editable commit proposal.
4. **Push approval** - show remote, branch, ahead count, and files before any push can occur.
5. **Audit review** - inspect proposal transitions, approved actions, pending commit/push state, and rollback hints.

Approval in one lane must not imply approval in later lanes.

## New Project Onboarding

When `SPIRIT_PROJECT_PATH` points at a parent folder, immediate child folders with project markers can appear as `new_project_candidate`.

For each candidate, Cartographer may draft a starter blueprint pack:

- `_blueprints/INDEX.md`
- `_blueprints/current/project_state.md`
- `_blueprints/components/app.md`
- `_blueprints/runbooks/manual_checks.md`
- `TODO.md`

The starter pack is a preview. It is not written until approved through the appropriate apply lane.

## Context And Performance Limits

Repo maps are capped:

- `max_files: 180`
- `max_symbols: 500`
- large files skipped
- ignored directories skipped, including `.git`, `.next`, `node_modules`, virtualenvs, backups, and secret-shaped paths
- `scan_duration_ms` reported for dashboard/performance review

If the map hits a limit, the skipped list should include markers such as `file_limit_reached` or `symbol_limit_reached`.

## Rollback And Audit

Cartographer exposes a read-only audit trail from:

- proposal transitions
- approved action audit JSONL records
- pending commit queue entries
- pending push queue entries

Rollback is guidance only. Cartographer must not perform rollback automatically. Revert work should be reviewed with Git diff, backup artifacts, and audit trail context.

## Dashboard Surfaces

The dashboard should expose:

- Cartographer status
- project health
- blueprint registry
- component map
- repo map/performance summary
- drift findings
- reminders
- proposal queue
- branch recommendations
- commit proposals
- push queue
- audit trail

All dashboard states must fail closed: unavailable data should never reveal apply, commit, or push controls.

### Cartographer Review Note
- Reason: component_code_changed.
- Component: cartographer.
- Changed files: source_proxy/cartographer/apply.py, source_proxy/cartographer/audit_trail.py, source_proxy/cartographer/blueprint_registry.py, source_proxy/cartographer/branch_recommendations.py, source_proxy/cartographer/commit_proposals.py, source_proxy/cartographer/component_mapper.py, source_proxy/cartographer/drift.py, source_proxy/cartographer/git_approvals.py.
- Manual check: confirm this blueprint still matches the changed implementation.

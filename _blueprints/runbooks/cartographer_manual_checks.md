---
blueprint_id: cartographer-manual-checks
title: Cartographer Operating Manual Checks
project: SpiritOS
component: cartographer
doc_type: runbook
status: runbook
source_of_truth: false
owner: Britton
code_paths:
  - source_proxy/api/cartographer.py
  - source_proxy/cartographer/**
  - src/app/v1/cartographer/**
  - src/components/dashboard/**
  - _blueprints/**
related_blueprints:
  - cartographer-agent
  - cartographer-dashboard-mobile-qa
  - system-state
  - dashboard-state
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-16
---

# Cartographer Operating Manual Checks

Use this guide for routine Cartographer operation after buildout. The expected posture is boring, explicit, and approval-gated.

## 1. Start With The Correct Root

Run Source Proxy from the project root with an explicit allowlist:

```bash
cd ~/SpiritOS
SPIRIT_PROJECT_PATH=/home/source/SpiritOS npm run proxy:https:lan
```

Check:

```bash
curl -k https://localhost:8787/v1/cartographer/projects
```

Expected:

```json
{
  "projects": [
    {
      "name": "SpiritOS",
      "root": "/home/source/SpiritOS",
      "status": "detected"
    }
  ],
  "candidate_count": 0
}
```

If `projects` is empty, restart the Source Proxy process that owns port `8787` with the explicit `SPIRIT_PROJECT_PATH`.

## 2. Confirm Safety Locks

```bash
curl -k https://localhost:8787/v1/cartographer/status
```

Expected:

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

Stop if any bypass flag is true or if write actions appear enabled unexpectedly.

## 3. Review Auto-Detected State

Run:

```bash
curl -k https://localhost:8787/v1/cartographer/project-health
curl -k https://localhost:8787/v1/cartographer/blueprints
curl -k https://localhost:8787/v1/cartographer/components
curl -k https://localhost:8787/v1/cartographer/repo-map
```

Confirm:

- SpiritOS appears.
- Blueprint count matches the index.
- Component mappings do not guess unknown files.
- Repo map includes `scan_duration_ms`.
- Repo map stays within `max_files` and `max_symbols`.
- Skipped paths include ignored directories when present.

## 4. Review Drift And Scribe Suggestions

Run:

```bash
curl -k https://localhost:8787/v1/cartographer/drift
curl -k https://localhost:8787/v1/cartographer/change-scribe
curl -k https://localhost:8787/v1/cartographer/blueprint-scribe
curl -k https://localhost:8787/v1/cartographer/runbook-scribe
```

Confirm:

- Drift findings cite affected files and blueprints.
- Change Scribe marks uncertainty instead of overclaiming.
- Blueprint Scribe drafts are editable/rejectable.
- Runbook Scribe includes testable checklist items and expected outputs.
- No docs are rewritten by these endpoints.

## 5. Review Proposals

Run:

```bash
curl -k https://localhost:8787/v1/cartographer/proposals
```

Confirm:

- Generated proposals are previews.
- Rejected proposals retain rejection reason.
- Approved proposals still require apply approval.
- Apply/commit/push are separate states.

Do not treat a proposal approval as commit or push approval.

## 6. New Project Onboarding

When testing a new project, point `SPIRIT_PROJECT_PATH` at an allowlisted parent folder and check:

```bash
curl -k https://localhost:8787/v1/cartographer/project-candidates
curl -k https://localhost:8787/v1/cartographer/proposals
```

Expected candidate:

```json
{
  "status": "new_project_candidate",
  "approval_status": "needs_approval",
  "action_taken": false
}
```

Expected starter proposal:

```json
{
  "type": "starter_blueprint_pack",
  "status": "drafted",
  "proposed_files": [
    "_blueprints/INDEX.md",
    "_blueprints/current/project_state.md",
    "_blueprints/components/app.md",
    "_blueprints/runbooks/manual_checks.md",
    "TODO.md"
  ],
  "action_taken": false
}
```

Rejecting a starter pack must leave the project folder untouched.

## 7. Branch, Commit, And Push Approval

Run:

```bash
curl -k https://localhost:8787/v1/cartographer/branch-recommendations
curl -k https://localhost:8787/v1/cartographer/commit-proposals
curl -k https://localhost:8787/v1/cartographer/push-queue
```

Confirm:

- Branch recommendations have `branch_creation_enabled: false`.
- Commit proposals have `commit_enabled: false`.
- Push queue items have `push_enabled: false`.
- Each item has `requires_approval: true`.
- No Git branch, commit, or push happens from these read-only endpoints.

## 8. Audit And Rollback Review

Run:

```bash
curl -k https://localhost:8787/v1/cartographer/audit-trail
```

Confirm:

- Proposal transitions include actor and timestamp when persisted.
- Approved actions include actor, task, files, and result when audit JSONL exists.
- Pending commit/push entries are visible when relevant.
- `rollback_enabled` is `false`.
- Rollback hints are guidance, not executable actions.

## 9. Regression Commands

Run before routine use or after Cartographer edits:

```bash
python3 -m pytest -q source_proxy/tests/test_cartographer_safety_audit.py
python3 -m pytest -q source_proxy/tests/test_cartographer_api.py
npm run validate:blueprints
```

Expected:

```text
Cartographer safety audit: passed
Blueprint index valid
```

## 10. Manual Dashboard QA

Use `cartographer-dashboard-mobile-qa` for:

- desktop
- LAN
- Tailscale
- mobile width
- approve/reject usability
- accidental push approval prevention

Do not proceed to commit or push approval if any dashboard surface fails closed incorrectly.

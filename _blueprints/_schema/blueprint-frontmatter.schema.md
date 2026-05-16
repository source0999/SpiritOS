---
blueprint_id: blueprint-frontmatter-schema
title: Blueprint Frontmatter Schema
project: SpiritOS
component: blueprint-system
doc_type: schema
status: active
source_of_truth: true
owner: Britton
code_paths:
  - _blueprints/**
related_blueprints:
  - blueprint-index
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-15
---

# Blueprint Frontmatter Schema

This schema is the parsing contract for Spirit Cartographer. It keeps blueprint documents machine-readable without granting write authority.

## Required Fields

Every indexed blueprint document should begin with YAML frontmatter using these fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `blueprint_id` | string | yes | Stable kebab-case ID. Do not derive behavior from the filename alone. |
| `title` | string | yes | Human-readable document title. |
| `project` | string | yes | Owning project, usually `SpiritOS`. |
| `component` | string | yes | Component or domain this document describes. |
| `doc_type` | string | yes | Document role, such as `current_state`, `component_blueprint`, `component_roadmap`, `runbook`, `phase_receipt`, `visual_sandbox`, or `index`. |
| `status` | enum | yes | One of the allowed statuses below. |
| `source_of_truth` | boolean | yes | `true` only for canonical current/component docs. |
| `owner` | string | yes | Human owner for review and approval. |
| `code_paths` | string list | yes | Relevant code globs. Use `[]` for history-only docs. |
| `related_blueprints` | string list | yes | Related `blueprint_id` values. Use `[]` when none are known. |
| `write_policy` | string | yes | Write behavior for proposal/apply flow. |
| `last_verified` | date | yes | Date the metadata was last checked, formatted `YYYY-MM-DD`. |

## Allowed Statuses

| Status | Meaning |
| --- | --- |
| `active` | Current doc used for system/component drift decisions. |
| `planned` | Roadmap or planned component doc; visible but not canonical current truth. |
| `runbook` | Manual QA or operating checklist. |
| `historical` | Phase receipt or history record; visible but ignored for current drift decisions. |
| `sandbox` | Visual/demo/sandbox doc; cannot imply production behavior. |
| `deprecated` | Parked document retained for reference only. |

## Source Of Truth Rules

- `source_of_truth: true` is reserved for canonical docs in `current/` and active component blueprints in `components/`.
- Roadmaps, runbooks, historical receipts, sandboxes, and deprecated docs must use `source_of_truth: false`.
- Cartographer may suggest updates to source-of-truth docs, but it must not apply them without dashboard approval.

## Write Policies

| Policy | Meaning |
| --- | --- |
| `proposal_only_until_dashboard_approved` | Cartographer may draft proposal diffs, but file writes require dashboard approval. |
| `historical_read_only` | History docs should not be rewritten during drift cleanup except by explicit human request. |
| `sandbox_proposal_only` | Sandbox docs may receive proposals, but cannot be treated as production contracts. |

## Minimal Example

```yaml
---
blueprint_id: dashboard-state
title: Dashboard Redesign Status
project: SpiritOS
component: dashboard
doc_type: current_state
status: active
source_of_truth: true
owner: Britton
code_paths:
  - src/components/dashboard/**
related_blueprints:
  - system-state
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-15
---
```

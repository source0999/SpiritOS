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
last_verified: 2026-05-16
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
| `doc_type` | enum | yes | One of the allowed document types below. |
| `status` | enum | yes | One of the allowed statuses below. |
| `source_of_truth` | boolean | yes | `true` only for canonical current/component docs. |
| `owner` | string | yes | Human owner for review and approval. |
| `code_paths` | string list | yes | Relevant code globs. Use `[]` for history-only docs. |
| `related_blueprints` | string list | yes | Related `blueprint_id` values. Use `[]` when none are known. |
| `write_policy` | string | yes | Write behavior for proposal/apply flow. |
| `last_verified` | date | yes | Date the metadata was last checked, formatted `YYYY-MM-DD`. |

## Allowed Document Types

| Document Type | Meaning | Expected Location |
| --- | --- | --- |
| `current_state` | Canonical current system, dashboard, or project state. | `current/` |
| `component_blueprint` | Canonical component architecture or operating contract. | `components/` |
| `component_roadmap` | Planned or phased component work that is not current truth yet. | `components/` |
| `runbook` | Manual QA, operating checks, or command recipes. | `runbooks/` |
| `phase_receipt` | Historical phase evidence or completion record. | `history/` |
| `visual_sandbox` | Non-production visual/demo material. | `sandbox/` |
| `proposal_queue` | Proposal queue index or proposal-lifecycle guidance. | `proposals/` |
| `schema` | Blueprint metadata, validation, or governance schema. | `_schema/` |
| `index` | Inventory or navigation document. | `_blueprints/` |

## Allowed Statuses

| Status | Meaning |
| --- | --- |
| `active` | Current doc used for system/component drift decisions. |
| `planned` | Roadmap or planned component doc; visible but not canonical current truth. |
| `runbook` | Manual QA or operating checklist. |
| `historical` | Phase receipt or history record; visible but ignored for current drift decisions. |
| `sandbox` | Visual/demo/sandbox doc; cannot imply production behavior. |
| `deprecated` | Parked document retained for reference only. |

## Directory Defaults

The required source layout is:

- `_schema/`
- `current/`
- `components/`
- `runbooks/`
- `history/`
- `proposals/`

The optional `sandbox/` directory is allowed for non-production visual or demo material only. Top-level blueprint files other than `INDEX.md` are unmanaged and should be moved into the appropriate directory.

| Directory | Default `doc_type` | Default `status` | Default `source_of_truth` |
| --- | --- | --- | --- |
| `current/` | `current_state` | `active` | `true` |
| `components/` | `component_blueprint` or `component_roadmap` | `active` or `planned` | `true` only for active component blueprints |
| `runbooks/` | `runbook` | `runbook` | `false` |
| `history/` | `phase_receipt` | `historical` | `false` |
| `sandbox/` | `visual_sandbox` | `sandbox` | `false` |
| `proposals/` | `proposal_queue` | `planned` | `false` |
| `_schema/` | `schema` | `active` | `true` |

## Source Of Truth Rules

- `source_of_truth: true` is reserved for canonical docs in `current/` and active component blueprints in `components/`.
- Schema and index docs may be `source_of_truth: true` only for blueprint governance itself.
- Roadmaps, proposal queues, runbooks, historical receipts, sandboxes, and deprecated docs must use `source_of_truth: false`.
- Cartographer may suggest updates to source-of-truth docs, but it must not apply them without dashboard approval.

## Write Policies

| Policy | Meaning |
| --- | --- |
| `proposal_only_until_dashboard_approved` | Cartographer may draft proposal diffs, but file writes require dashboard approval. |
| `historical_read_only` | History docs should not be rewritten during drift cleanup except by explicit human request. |
| `sandbox_proposal_only` | Sandbox docs may receive proposals, but cannot be treated as production contracts. |

## Validation Rules

- Frontmatter must be the first block in the file and must be delimited by `---`.
- `_blueprints/` must contain the required source layout directories, with active truth separated from runbooks, history, proposals, schema, and sandbox material.
- `blueprint_id` values must be stable kebab-case IDs and must be unique across `_blueprints`.
- `doc_type`, `status`, and `write_policy` must match the allowed values in this schema.
- `source_of_truth: true` must agree with the source-of-truth rules above.
- `code_paths` and `related_blueprints` must always be lists, even when empty.
- `last_verified` must use `YYYY-MM-DD`.
- Schema changes define metadata parsing only; they do not approve file writes, commits, pushes, or proposal application.

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

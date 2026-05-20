# Scout v0.9 Increment 1.1 Design Scout Intake Plan

status: planning/manual-controlled

Status date: 2026-05-20

This increment plans stored-only Design Scout intake for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, crawl the web, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

## Gate Before This Increment

Manual closeout check passed before this document was written:

- `scout-v0-5-closeout` returned `result: pass`
- `read_only: true`
- `mutated: false`
- `mode: dry_run_only`
- `ready_for_next_increment: true`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`
- `head_changed: false`
- `unexpected_status_delta: []`

Scout remains stable, parked, manual-controlled, and not autonomous.

## Goal

Plan how Scout can later store manually supplied design intelligence without requiring autonomy. This lane should help future SpiritOS design-system work by preserving useful references, screenshots, tokens, UI patterns, component notes, and operator summaries as advisory evidence only.

The design intake lane must become useful before it becomes automated.

## Intake Boundary

Allowed for this plan:

- manually supplied design references
- manually supplied screenshots or file references
- manually supplied design token notes
- manually supplied UI pattern notes
- manually supplied component notes
- docs-only packet shape planning
- human review and dry-run receipt planning

Forbidden:

- web crawling
- auto-discovery
- automatic candidate extraction
- automatic screenshot capture
- automatic visual analysis
- automatic design token extraction
- automatic packet promotion
- automatic coding prompt injection
- proxy memory writes
- coding context writes
- active context writes
- scheduled writes
- hidden workers
- commits
- pushes

## Stored-Only Design Intake Model

| Intake Type | Stored Evidence | Required Boundary | Useful For |
| --- | --- | --- | --- |
| Design inspiration | Title, source, operator note, optional URL, review date | Manual-provided only | Later visual direction review |
| Design tokens | Color, spacing, radius, typography, elevation, motion notes | Stored as reference, not applied | Token comparison and design-system planning |
| Screenshots | File path, viewport, surface, operator summary | No automatic screenshot capture in this increment | Visual comparison and QA planning |
| UI patterns | Pattern name, problem solved, constraints, risks | Advisory only | Designer Agent or Codex prompt preparation |
| Component notes | Component name, states, affordances, accessibility notes | No code generation | Component review and future implementation planning |
| References | Provenance, date reviewed, license or source caveat when known | No broad crawling | Source review and traceability |
| Anti-patterns | Problem, observed impact, where to avoid it | Manual-observed only | Preventing repeated design mistakes |

## Draft Intake Record

```yaml
record_version: scout.v0_9.design_intake.v1
record_id: design-intake-example-001
intake_type: ui_pattern
source_type: manual/user-provided-reference
source_reference: user supplied screenshot or URL
review_date: 2026-05-20
operator_summary: Compact dashboard navigation pattern with clear active state.
useful_for:
  - SpiritOS dashboard shell review
  - future design pattern taxonomy
evidence:
  - screenshot path or source reference, if provided
design_notes:
  layout: compact sidebar and dense content area
  affordances: active navigation state and scan-friendly labels
  risks: mobile overflow, focus visibility, contrast, stale source
manual_decision_needed: classify during 1.2 Design Pattern Taxonomy
writes_allowed: false
execution_status: stored-only planning, not implemented
next_increment: 1.2 Design Pattern Taxonomy
```

## Review Rules

Every future stored-only design intake record should answer:

- What is the artifact?
- Who supplied it or where did it come from?
- Why might it be useful for SpiritOS?
- Which UI surface or design-system area might it inform?
- What risks or missing evidence should be kept visible?
- What manual decision is needed next?

The record should avoid vague wording. It should preserve provenance and limits so later design work can decide whether to use, reject, or revisit the evidence.

## Implementation Readiness Notes

This plan does not authorize implementation. Before any stored-only design intake is built, a later implementation plan must define:

- exact storage location
- exact schema or data model
- write boundary and rollback behavior
- UI or CLI entry point, if any
- tests for no proxy memory writes
- tests for no coding context writes
- tests that intake remains manual-fed or manual-triggered
- manual checks for source provenance and operator review

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-design-intake-plan.md docs/plan-index.md
grep -n "Design Scout Intake Plan\|stored-only\|manual/user-provided-reference\|writes_allowed: false\|Design Pattern Taxonomy" docs/scout-v0-9-design-intake-plan.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the Design Scout intake plan, stored-only boundary, and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-design-intake-plan.md
```

## Closeout

Increment 1.1 is complete when this stored-only design intake plan is reviewed, indexed, and the closeout runner remains green.

Next increment: **1.2 Design Pattern Taxonomy**.

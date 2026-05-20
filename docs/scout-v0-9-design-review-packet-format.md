# Scout v0.9 Increment 1.3 Design Review Packet Format

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines the Design Scout review packet format for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, crawl the web, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Define how Scout should summarize a manually supplied design artifact for later human review by Designer Agent, Reverse Engineer Designer Agent, or Codex. The packet should be digestible, evidence-based, and specific enough to support later design-system work without implying implementation.

## Packet Boundary

A Design Scout review packet is advisory only.

It must not:

- execute analysis automatically
- fetch or crawl external sources
- extract candidates automatically
- generate code
- apply design tokens
- write proxy memory
- write coding context
- write active context
- promote packets
- finalize promotions
- schedule work
- create hidden workers
- commit
- push

Required fields must keep `writes_allowed: false` and `execution_status: advisory-only, not implemented`.

## Packet Fields

| Field | Required | Meaning | Example |
| --- | --- | --- | --- |
| `packet_version` | Yes | Human-readable packet format version. | `scout.v0_9.design_review_packet.v1` |
| `packet_id` | Yes | Stable packet identifier. | `design-review-001` |
| `artifact` | Yes | Screenshot, URL, note, token set, or component reference. | `manual screenshot: dashboard-sidebar.png` |
| `source` | Yes | Provenance of the artifact. | `user-provided` |
| `review_date` | Yes | Date the artifact was reviewed. | `2026-05-20` |
| `primary_category` | Yes | Primary taxonomy category. | `navigation` |
| `secondary_categories` | No | Up to two supporting categories. | `layout_shells`, `mobile_first_behavior` |
| `observed_pattern` | Yes | Factual description of the pattern. | Compact sidebar with clear active state. |
| `useful_for` | Yes | Where it may help SpiritOS. | Dashboard shell review. |
| `constraints` | Yes | SpiritOS-specific constraints. | Must preserve readable mobile navigation. |
| `risks` | Yes | Known limitations or hazards. | Screenshot omits focus and hover states. |
| `suggested_manual_action` | Yes | Human-controlled next step. | Compare against current dashboard shell. |
| `evidence` | Yes | Source file, URL, screenshot path, or note reference. | `screenshots/dashboard-sidebar.png` |
| `confidence` | Yes | Evidence confidence. | `medium` |
| `writes_allowed` | Yes | Whether the packet authorizes writes. | `false` |
| `execution_status` | Yes | Current execution state. | `advisory-only, not implemented` |
| `next_increment` | Yes | Planned next increment. | `1.4 Phase 1 Closeout` |

## Example Design Packet

```yaml
packet_version: scout.v0_9.design_review_packet.v1
packet_id: design-review-001
artifact: manual screenshot: dashboard-sidebar.png
source: user-provided
review_date: 2026-05-20
primary_category: navigation
secondary_categories:
  - layout_shells
  - mobile_first_behavior
observed_pattern: Compact sidebar with icon and text labels plus a visible active state.
useful_for:
  - SpiritOS dashboard shell review
  - future navigation consistency pass
constraints:
  - must keep mobile navigation readable
  - must preserve keyboard focus visibility
  - must avoid nested card clutter
risks:
  - screenshot may not show hover, focus, loading, or narrow viewport states
  - source styling may not fit SpiritOS density goals
suggested_manual_action: Ask Designer Agent to compare this pattern against the current dashboard shell.
evidence:
  - screenshots/dashboard-sidebar.png
confidence: medium
writes_allowed: false
execution_status: advisory-only, not implemented
next_increment: 1.4 Phase 1 Closeout
```

## Quality Rules

- Use concrete descriptions, not generic AI praise.
- Tie usefulness to a SpiritOS surface or design-system decision.
- Preserve provenance and review date.
- Record missing viewport, state, interaction, or accessibility evidence.
- Keep suggested actions manual.
- Do not imply the packet should be automatically applied or promoted.

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-design-intake-plan.md docs/scout-v0-9-design-pattern-taxonomy.md docs/scout-v0-9-design-review-packet-format.md docs/plan-index.md
grep -n "Design Review Packet Format\|packet_version\|writes_allowed: false\|advisory-only, not implemented\|Phase 1 Closeout" docs/scout-v0-9-design-review-packet-format.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the design packet format and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-design-review-packet-format.md
```

## Closeout

Increment 1.3 is complete when this packet format is reviewed, indexed, and the closeout runner remains green.

Next increment: **1.4 Phase 1 Closeout**.

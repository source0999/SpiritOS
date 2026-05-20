# Scout v0.9 Increment 1.2 Design Pattern Taxonomy

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines the Design Scout pattern taxonomy for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, crawl the web, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Define a practical taxonomy for manually supplied design references so future Design Scout intake can group evidence in ways that are useful for SpiritOS design-system work.

The taxonomy is advisory. It does not extract design features automatically, apply tokens, generate code, or promote anything into coding context.

## Taxonomy Table

| Category | What To Capture | SpiritOS Use | Review Risks |
| --- | --- | --- | --- |
| Glassmorphism | Blur, transparency, contrast, border treatment, layered surfaces | Evaluate whether glass panels improve dashboard depth without hurting readability | Low contrast, over-decoration, poor dark/light behavior |
| Layout shells | Sidebar, topbar, content rail, split panes, density, responsive collapse | Compare dashboard and coding workspace structure | Mobile overflow, nested cards, weak hierarchy |
| Navigation | Primary nav, secondary nav, active states, breadcrumbs, task switching | Improve repeated movement through SpiritOS work surfaces | Ambiguous active state, hidden controls, excessive nesting |
| Dashboard cards | Metrics, grouped evidence, empty/loading/error states, scan order | Improve Scout, Cartographer, and dashboard review surfaces | Card clutter, low density, unclear priority |
| Mobile-first behavior | Breakpoints, stacking, hit targets, scroll boundaries, viewport fit | Keep operator checks usable from mobile | Text overflow, hidden action controls, sticky UI collisions |
| Motion | Transition purpose, duration, easing, loading progress, reduced-motion fallback | Make state changes legible without distraction | Decorative motion, inaccessible motion, layout shift |
| Typography | Type scale, labels, headings, line length, dense table readability | Improve scanning in operational panels | Oversized hero type in tools, cramped labels, poor hierarchy |
| Color tokens | Semantic colors, status colors, contrast, palette balance | Strengthen design-system token choices | One-note palettes, low contrast, misleading status color |
| Component affordances | Buttons, toggles, segmented controls, menus, tabs, disabled states, focus states | Make controls predictable across Scout and design tooling | Text-only controls where icons are expected, weak focus visibility |
| Anti-patterns | Low contrast, decorative clutter, ambiguous action, layout shift, hidden provenance | Prevent repeated design mistakes | Storing vague criticism without actionable evidence |

## Category Record Shape

```yaml
taxonomy_version: scout.v0_9.design_taxonomy.v1
category: dashboard_cards
artifact_reference: manual screenshot, URL, or operator note
captured_traits:
  - grouped evidence
  - compact status labels
  - visible empty state
spiritos_use:
  - Scout intelligence center review
  - dashboard component quality pass
review_risks:
  - card clutter
  - unclear priority
  - missing mobile state
manual_decision_needed: convert into design review packet or save later
writes_allowed: false
execution_status: taxonomy-only, not implemented
next_increment: 1.3 Design Review Packet Format
```

## Classification Rules

- Prefer one primary category and up to two secondary categories.
- Capture concrete visual or interaction traits, not vague praise.
- Preserve source provenance and review date.
- Mark missing states explicitly, such as mobile, hover, focus, loading, or error states.
- Keep risks visible even for useful patterns.
- Do not treat taxonomy classification as approval to build.

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-design-intake-plan.md docs/scout-v0-9-design-pattern-taxonomy.md docs/plan-index.md
grep -n "Design Pattern Taxonomy\|Glassmorphism\|Mobile-first behavior\|writes_allowed: false\|Design Review Packet Format" docs/scout-v0-9-design-pattern-taxonomy.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the taxonomy categories and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-design-pattern-taxonomy.md
```

## Closeout

Increment 1.2 is complete when this taxonomy is reviewed, indexed, and the closeout runner remains green.

Next increment: **1.3 Design Review Packet Format**.

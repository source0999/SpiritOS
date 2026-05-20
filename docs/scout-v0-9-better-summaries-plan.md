# Scout v0.9 Increment 2.2 Better Summaries

status: planning/manual-controlled

Status date: 2026-05-20

This increment plans better Scout review summaries for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Define a clearer summary template for human Scout review. Summaries should make each item easier to evaluate by showing what it is, why it matters, where it applies, what the risk is, and what manual action might be useful.

This plan does not authorize automatic summary generation or runtime changes.

## Summary Template

| Field | Purpose | Writing Rule |
| --- | --- | --- |
| `summary` | State what the item is. | One or two factual sentences. |
| `why_this_matters` | Explain why the operator should care. | Tie value to a current or plausible SpiritOS workflow. |
| `where_it_applies` | Name the project, component, lane, or UI surface. | Use concrete targets like `Scout review center`, `dashboard`, or `design-system planning`. |
| `risk` | Keep safety, provenance, staleness, or noise visible. | Include at least one risk or say `needs verification`. |
| `suggested_manual_action` | Propose a human-controlled next step. | Use advisory language only. |
| `evidence` | Point to the source material. | Include file, URL, packet ID, screenshot, or manual note reference. |
| `confidence` | Indicate evidence strength. | Use `high`, `medium`, `low`, or `needs verification`. |
| `writes_allowed` | Preserve the mutation boundary. | Always `false` for this planning increment. |

## Example Summary

```yaml
summary_version: scout.v0_9.review_summary.v1
item_id: design-review-001
summary: Compact dashboard navigation reference with clear active state and dense labels.
why_this_matters: It may help compare SpiritOS dashboard navigation against a compact operator workflow.
where_it_applies:
  - Scout review center
  - SpiritOS dashboard shell
risk: Screenshot does not verify mobile, hover, focus, loading, or error states.
suggested_manual_action: Save for later design-system comparison or convert into a reviewed Codex prompt.
evidence:
  - docs/scout-v0-9-design-review-packet-format.md
confidence: medium
writes_allowed: false
execution_status: summary-only, not implemented
next_increment: 2.3 Operator Decision Flow
```

## Summary Quality Rules

- Do not use vague phrases like "interesting insight" without explaining why.
- Do not bury risk behind positive language.
- Do not imply that a suggested action has already happened.
- Do not imply code, context, memory, source, packet, or promotion mutation.
- Prefer concrete locations over broad terms like "the app".
- Mark uncertain or missing evidence as `needs verification`.

## Non-Mutation Boundary

Better summaries do not authorize:

- automatic summary generation
- source approval, rejection, blocking, or activation
- discovery execution
- candidate extraction
- packet promotion
- proxy intake calls
- proxy memory writes
- coding context writes
- active context writes
- promotion finalization
- scheduled writes
- hidden workers
- commits
- pushes

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-review-grouping-plan.md docs/scout-v0-9-better-summaries-plan.md docs/plan-index.md
grep -n "Better Summaries\|why_this_matters\|suggested_manual_action\|writes_allowed: false\|Operator Decision Flow" docs/scout-v0-9-better-summaries-plan.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the better summary template and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-better-summaries-plan.md
```

## Closeout

Increment 2.2 is complete when this better summaries plan is reviewed, indexed, and the closeout runner remains green.

Next increment: **2.3 Operator Decision Flow**.

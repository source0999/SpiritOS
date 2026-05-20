# Scout v0.9 Increment 0.3.1 Lane Contract Schema

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines the human-readable lane contract schema for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Define how a future Scout lane must describe its purpose, evidence, allowed actions, forbidden actions, confidence, and required human decision before any implementation or mutation can be considered.

This schema is intentionally small. It should be readable in a review center, design handoff, or planning doc without needing a generated runtime object.

## Lane Contract Schema

| Field | Required | Meaning | Example |
| --- | --- | --- | --- |
| `contract_version` | Yes | Human-readable contract version. | `scout.v0_9.lane_contract.v1` |
| `lane_name` | Yes | Name of the bounded Scout lane. | `Design Scout Intake Lane` |
| `lane_status` | Yes | Current state of the lane. | `planned`, `parked`, `ready_for_docs_review`, `blocked` |
| `owner_decision` | Yes | The operator decision needed before implementation. | `approve stored-only intake design` |
| `source` | Yes | Where the lane request or evidence came from. | `manual operator request`, `v0.8 closeout`, `design-system plan` |
| `allowed_actions` | Yes | Actions explicitly allowed by the lane. | `docs-only planning`, `manual review`, `dry-run receipt drafting` |
| `forbidden_actions` | Yes | Actions that remain blocked. | `proxy memory writes`, `coding context writes`, `scheduled discovery` |
| `evidence_requirements` | Yes | Required file references, command outputs, screenshots, API summaries, or manual notes. | `docs/scout-v0-8-closeout-summary.md`, closeout runner output |
| `confidence` | Yes | Evidence confidence. | `high`, `medium`, `low`, `needs verification` |
| `manual_decision_needed` | Yes | Human decision required before moving forward. | `approve 0.3.2 dry-run receipt format` |
| `expected_output` | Yes | Concrete artifact expected from the lane or increment. | `docs-only schema`, `receipt example`, `review label table` |
| `manual_check` | Yes | Command or checklist the operator can run. | `grep plan for forbidden actions` |
| `rollback_notes` | Yes | How to undo the planning artifact if rejected. | `remove the doc and restore the index row` |
| `next_increment` | Yes | Exact next planned increment title. | `0.3.2 Dry-Run Receipt Format` |

## Allowed Lane Status Values

| Status | Meaning |
| --- | --- |
| `planned` | The lane is documented but not approved for implementation. |
| `parked` | The lane is intentionally stopped until a new operator decision. |
| `ready_for_docs_review` | The lane contract is ready for human review. |
| `blocked` | The lane cannot continue because evidence, safety, or approval is missing. |

No lane status means implementation approval. Implementation must require a separate explicit future gate.

## Confidence Values

| Confidence | Meaning |
| --- | --- |
| `high` | Evidence is directly verified in repo docs, runner output, or current command output. |
| `medium` | Evidence is supported but should be rechecked before implementation. |
| `low` | Evidence is weak or indirect. |
| `needs verification` | Evidence is missing; do not guess. |

## Example Contract

```yaml
contract_version: scout.v0_9.lane_contract.v1
lane_name: Design Scout Intake Lane
lane_status: planned
owner_decision: approve stored-only intake design
source:
  - docs/scout-v0-9-next-phases-plan.md
  - docs/design-systems-master-v0.1.md
allowed_actions:
  - docs-only planning
  - manually supplied design reference intake design
  - stored-only packet format design
forbidden_actions:
  - auto-discovery
  - automatic candidate extraction
  - proxy memory writes
  - coding context writes
  - promotion finalization
  - scheduled writes
  - hidden background workers
  - commits
  - pushes
evidence_requirements:
  - current Scout closeout remains pass
  - lane remains manual-controlled
  - storage target is Scout-owned and advisory only
confidence: medium
manual_decision_needed: approve 1.1 Design Intake Model before implementation planning
expected_output: stored-only design intake planning section
manual_check:
  - git diff -- docs
  - grep for forbidden actions
rollback_notes: remove the lane doc or restore the plan section before implementation begins
next_increment: 0.3.2 Dry-Run Receipt Format
```

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-lane-contract-schema.md docs/plan-index.md
grep -n "Lane Contract Schema\|contract_version\|forbidden_actions\|next_increment" docs/scout-v0-9-lane-contract-schema.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the lane contract schema and safety fields.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-lane-contract-schema.md
```

## Closeout

Increment 0.3.1 is complete when this schema is reviewed, indexed, and the closeout runner remains green.

Next increment: **0.3.2 Dry-Run Receipt Format**.

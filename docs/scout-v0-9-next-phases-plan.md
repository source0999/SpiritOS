# Scout v0.9 Next Phases Plan

status: planning/manual-controlled

Status date: 2026-05-20

This plan selects the next Scout lane after the Scout v0.8 parked closeout. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

## Current Scout Grade

Scout is stable, parked, and useful as a manual-controlled intelligence center. Scout is not failing. It is paused at a safe intelligence-center milestone, which is the intended state until a later explicit implementation gate.

| Area | Grade | Evidence |
| --- | --- | --- |
| Manual-controlled intelligence center | A- / about 92 | Verified in `docs/scout-v0-8-closeout-summary.md`: parked/manual-controlled, backlog `0`, packets `45`, verdicts `45`, packet synthesis ready, Level 1 soak pass, closeout pass. |
| Autonomy foundation | B+ / about 86 | Verified in `docs/scout-v0-8-next-lane-decision-record.md` and `source_proxy/testing/runner.py`: explicit dry-run closeout profile and write/finalization gates exist. |
| Actual autonomy | D / about 35 | Verified by the safety boundaries in `docs/scout-v0-8-closeout-summary.md`, `docs/scout-v0-8-next-lane-decision-record.md`, and `scout/SCOPE.md`: autonomy is intentionally disabled. |
| Overall current state | Stable, parked, useful, not autonomous | Verified by v0.8 closeout and scope docs. |

## Current Evidence Audit

| Signal | Status | Evidence |
| --- | --- | --- |
| Scout mode manual-controlled / dry-run-only | verified | `docs/scout-v0-8-closeout-summary.md` records `status: closed/manual-controlled` and closeout mode `dry_run_only`. |
| Backlog | verified: `0` | `docs/scout-v0-8-closeout-summary.md` and `docs/scout-v0-8-next-lane-decision-record.md`. |
| Packets | verified: `45` | `docs/scout-v0-8-closeout-summary.md` and `docs/scout-v0-8-next-lane-decision-record.md`. |
| Verdicts | verified: `45` | `docs/scout-v0-8-closeout-summary.md` and `docs/scout-v0-8-next-lane-decision-record.md`. |
| Packet synthesis | verified: ready | `docs/scout-v0-8-closeout-summary.md`. |
| Level 1 soak | verified: pass | `docs/scout-v0-8-closeout-summary.md`; runner profile exists in `source_proxy/testing/runner.py`. |
| Closeout | verified: pass | `docs/scout-v0-8-closeout-summary.md`; `scout-v0-5-closeout` profile exists in `source_proxy/testing/runner.py`. |
| Proxy memory writes | verified: `false` | `docs/scout-v0-8-closeout-summary.md`; closeout runner reports `would_write_proxy_memory: false`. |
| Coding context writes | verified: `false` | `docs/scout-v0-8-closeout-summary.md`; closeout runner reports `would_write_coding_context: false`. |
| Promotion finalization | verified: `false` | `docs/scout-v0-8-closeout-summary.md`; closeout runner reports `would_finalize_promotion: false`. |
| Forbidden automation | verified | `docs/scout-v0-8-closeout-summary.md`, `docs/scout-v0-8-next-lane-decision-record.md`, and `scout/SCOPE.md` forbid auto-approval, automatic discovery/candidate/promotion paths, writes, commits, pushes, scheduled writes, and hidden workers. |
| Existing v0.9 plan | verified absent | `find . -path ./.git -prune -o \( -iname "*v0-9*" -o -iname "*next*phase*" -o -iname "*scout*plan*" \) -print` found no v0.9 Scout next-phase plan. |

Read-only commands used for this audit:

```bash
cd /home/source/SpiritOS
git status -sb
find docs -iname "*scout*" -o -iname "*Scout*" | sort
grep -RIn "Scout v0.8\|Scout v0.9\|dry_run_only\|proxy memory\|coding context\|promotion finalization\|backlog\|packet synthesis\|soak" docs scout source_proxy 2>/dev/null | head -300
find . -path ./.git -prune -o \( -iname "*v0-9*" -o -iname "*next*phase*" -o -iname "*scout*plan*" \) -print | sort
```

## Selected Next Lane

Scout v0.9 is **Manual-Controlled Lane Expansion**.

Core direction: Scout should become more useful before becoming more autonomous. The next phases strengthen lane contracts, design intelligence intake, review quality, dry-run receipts, diagnostics, and closeout gates while keeping writes disabled.

Sub-lanes:

1. Review Intelligence Lane
2. Design Scout Intake Lane
3. Safe Discovery Prep Lane
4. Proxy Integration Prep Lane

Allowed:

- docs-only planning
- human-readable lane contracts
- dry-run receipt formats
- review labels and decision flow planning
- stored-only design intake planning
- manual-triggered discovery boundaries
- read-only proxy handoff packet planning
- manual checks and closeout gates

Forbidden:

- auto-approval
- auto-rejection
- auto-blocking
- auto-discovery
- automatic candidate extraction
- automatic packet promotion
- proxy intake calls
- proxy memory writes
- coding context writes
- active context writes
- append-only evidence writes unless a later gate explicitly approves them
- promotion finalization
- scheduled mutation
- scheduled discovery
- service changes
- hidden background workers
- apply actions
- commits
- pushes
- self-promotion to a higher autonomy level

## Phase 0.2: Lane Selection and Boundaries

Goal: decide and document Scout's next lane without enabling autonomy.

### Increment 0.2.1: Current Evidence Audit

- Verify current Scout docs, closeout status, tests, and forbidden actions.
- Expected output: evidence table with file references and commands.
- Manual check: run `git status -sb`, grep for Scout closeout, and verify no code changes are required.
- Rollback notes: remove this plan if the evidence audit is wrong; do not touch Scout runtime files.
- Next increment: 0.2.2 Lane Decision.

### Increment 0.2.2: Lane Decision

- Choose the next lane as Manual-Controlled Lane Expansion.
- Include Review Intelligence Lane, Design Scout Intake Lane, Safe Discovery Prep Lane, and Proxy Integration Prep Lane.
- Expected output: lane decision section with what is allowed and forbidden.
- Manual check: confirm no writes or autonomy are enabled.
- Rollback notes: edit this plan back to v0.8 parked state if the lane is rejected.
- Next increment: 0.2.3 Forbidden Action Contract.

### Increment 0.2.3: Forbidden Action Contract

- Explicitly list what Scout still cannot do.
- Include no auto-approval, no proxy memory writes, no coding context writes, no final promotion, no scheduled mutation, no commits, and no hidden workers.
- Expected output: clear safety boundary section.
- Manual check: grep plan for forbidden actions.
- Rollback notes: restore the prior plan version if any forbidden action is loosened by mistake.
- Next increment: 0.2.4 Closeout Gate.

### Increment 0.2.4: Phase 0.2 Closeout Gate

- Define what must be true before moving to Phase 0.3.
- Expected output: small closeout checklist.
- Manual check: docs-only diff, no behavior changes.
- Rollback notes: keep Scout parked at v0.8 until the checklist is clean.
- Next increment: 0.3.1 Lane Contract Schema.

Closeout checklist:

- This plan exists and is indexed.
- Current Scout grade is evidence-based.
- Manual-Controlled Lane Expansion is selected.
- Forbidden actions are explicit.
- Diff is docs-only.
- No Scout code, source registry, proxy, coding context, worker, scheduler, commit, or push behavior changed.

## Phase 0.3: Lane Contract and Evidence Receipts

Goal: define how Scout records useful intelligence without mutating systems.

### Increment 0.3.1: Lane Contract Schema

- Define fields for lane name, source, allowed actions, forbidden actions, evidence requirements, confidence, and manual decision needed.
- Expected output: docs-only schema section.
- Manual check: schema is human-readable and not over-engineered.
- Rollback notes: remove or simplify the schema if it starts implying runtime implementation.
- Next increment: 0.3.2 Dry-Run Receipt Format.

Lane contract schema:

| Field | Meaning |
| --- | --- |
| lane_name | Human-readable lane name. |
| source | Where the intelligence or request came from. |
| allowed_actions | Explicit docs/read-only actions allowed for the lane. |
| forbidden_actions | Actions that remain blocked. |
| evidence_requirements | File references, command outputs, screenshots, or API summaries required before a decision. |
| confidence | Low, medium, high, or needs verification. |
| manual_decision_needed | The operator decision required before implementation or mutation. |

### Increment 0.3.2: Dry-Run Receipt Format

- Define receipt fields for candidate ID, source, summary, proposed action, why useful, risk, confidence, and manual approval requirement.
- Expected output: dry-run receipt example.
- Manual check: receipt does not imply execution.
- Rollback notes: remove any receipt language that sounds like an applied action.
- Next increment: 0.3.3 Review Decision Labels.

Dry-run receipt example:

| Field | Example |
| --- | --- |
| candidate_id | `design-intake-example-001` |
| source | `manual/user-provided-reference` |
| summary | Dashboard navigation pattern worth reviewing. |
| proposed_action | Save as a design packet for later manual review. |
| why_useful | May improve repeatable dashboard layout decisions. |
| risk | Could be stale, too generic, or inconsistent with SpiritOS UI constraints. |
| confidence | medium |
| manual_approval_required | true |
| execution_status | dry-run-only, not executed |

### Increment 0.3.3: Review Decision Labels

- Standardize labels like `needs_review`, `useful_now`, `saved_later`, `rejected`, `blocked`, `promoted_pending`, and `approved_dry_run`.
- Expected output: label table.
- Manual check: labels do not conflict with current code or docs.
- Rollback notes: rename labels before implementation if they collide with existing packet or promotion states.
- Next increment: 0.3.4 Phase 0.3 Closeout.

| Label | Meaning | Mutation Allowed |
| --- | --- | --- |
| `needs_review` | Human has not made a decision. | No |
| `useful_now` | Useful for current planning or prompt drafting. | No |
| `saved_later` | Worth retaining as reference. | No |
| `rejected` | Not useful or not trustworthy. | No |
| `blocked` | Cannot proceed due to safety, source, or evidence issue. | No |
| `promoted_pending` | Candidate may deserve future promotion review. | No |
| `approved_dry_run` | Human approves dry-run validation only. | No |

### Increment 0.3.4: Phase 0.3 Closeout

- Verify the contract is documented and bounded.
- Expected output: closeout checklist.
- Manual check: docs-only diff.
- Rollback notes: keep Phase 0.3 as planning-only until all labels and receipt fields are accepted.
- Next increment: 1.1 Design Scout Intake Plan.

Closeout checklist:

- Lane contract schema is readable.
- Dry-run receipt example cannot be mistaken for execution.
- Review labels do not authorize mutation.
- No code changes exist for this phase.

## Phase 1: Design Scout Intake, Stored-Only

Goal: let Scout become useful for design systems without requiring full autonomy.

### Increment 1.1: Design Intake Model

- Plan how Scout can store design inspiration, design tokens, screenshots, UI patterns, component notes, and references manually fed by the user.
- Expected output: design intake section.
- Manual check: no web crawling or auto-discovery implied unless manual-triggered.
- Rollback notes: remove intake categories that imply automatic crawling or automatic coding-context promotion.
- Next increment: 1.2 Design Pattern Taxonomy.

Stored-only design intake model:

| Intake Type | Stored Evidence | Required Boundary |
| --- | --- | --- |
| Design inspiration | URL, title, operator note, screenshot reference if provided | Manual-provided only. |
| Design tokens | Color, spacing, radius, typography notes | Stored as reference, not applied. |
| Screenshots | File reference and operator summary | No automatic visual extraction unless later approved. |
| UI patterns | Pattern name, use case, constraints | Advisory only. |
| Component notes | Component name, affordance, state behavior | No code generation. |
| References | Source, provenance, date reviewed | No broad crawling. |

### Increment 1.2: Design Pattern Taxonomy

- Define categories such as glassmorphism, layout shells, navigation, dashboard cards, mobile-first behavior, motion, typography, color tokens, component affordances, and anti-patterns.
- Expected output: taxonomy table.
- Manual check: categories are useful for SpiritOS design system work.
- Rollback notes: keep only categories that support actual SpiritOS review decisions.
- Next increment: 1.3 Design Review Packet Format.

| Category | What To Capture |
| --- | --- |
| Glassmorphism | Blur, transparency, contrast, edge treatment, readability risks. |
| Layout shells | Sidebar, header, content density, responsive behavior. |
| Navigation | Primary nav, secondary nav, active states, task switching. |
| Dashboard cards | Metrics, hierarchy, scan behavior, empty/loading states. |
| Mobile-first behavior | Breakpoints, stacking, hit targets, overflow risks. |
| Motion | Transition purpose, duration, reduced-motion fallback. |
| Typography | Type scale, hierarchy, line length, fit risks. |
| Color tokens | Token names, semantic use, contrast constraints. |
| Component affordances | Buttons, toggles, menus, tabs, controls, disabled states. |
| Anti-patterns | Low contrast, decorative clutter, ambiguous controls, layout shift. |

### Increment 1.3: Design Review Packet Format

- Define how Scout should summarize a design artifact for later use by Designer Agent, Reverse Engineer Designer Agent, or Codex.
- Expected output: example design packet.
- Manual check: packet is digestible and avoids vague AI wording.
- Rollback notes: simplify the packet if it becomes too broad for manual review.
- Next increment: 1.4 Phase 1 Closeout.

Example design packet:

| Field | Example |
| --- | --- |
| packet_id | `design-review-001` |
| artifact | `manual screenshot: dashboard-sidebar.png` |
| source | `user-provided` |
| observed_pattern | Compact sidebar with icon and text labels. |
| useful_for | SpiritOS dashboard shell review. |
| constraints | Must preserve readable mobile navigation and current safety gates. |
| risks | Screenshot may not show hover, focus, or narrow viewport states. |
| suggested_manual_action | Ask Designer Agent to compare against current dashboard shell. |
| writes_allowed | false |

### Increment 1.4: Phase 1 Closeout

- Define what has to be true before building stored-only design intake.
- Expected output: implementation readiness checklist.
- Manual check: no autonomy enabled.
- Rollback notes: do not build if any intake path would automatically crawl, apply, or write coding context.
- Next increment: 2.1 Review Intelligence Improvements.

Implementation readiness checklist:

- Intake is manual-fed or manually triggered only.
- Storage target is explicit and Scout-owned.
- No automatic web crawling is planned.
- No automatic coding-context or proxy-memory write is planned.
- Design packet fields are bounded.
- Tests and manual checks are named before implementation starts.

## Phase 2: Review Intelligence Improvements

Goal: make Scout's human review center clearer and more useful.

### Increment 2.1: Review Grouping Plan

- Group items by usefulness, risk, source, project, component, and time sensitivity.
- Expected output: review grouping section.
- Manual check: grouping improves operator decisions.
- Rollback notes: avoid grouping changes that hide source provenance or risk.
- Next increment: 2.2 Better Summaries.

Review grouping:

| Group | Purpose |
| --- | --- |
| Usefulness | Separate actionable, reference-only, and low-value items. |
| Risk | Surface unsafe, stale, unknown-source, or mutation-adjacent items. |
| Source | Keep provenance visible. |
| Project | Tie evidence to SpiritOS, Source Proxy, Scout, Cartographer, or design-system work. |
| Component | Help route UI/design evidence to the right surface. |
| Time sensitivity | Distinguish urgent updates from durable references. |

### Increment 2.2: Better Summaries

- Plan clearer summaries with why this matters, where it applies, risk, and suggested manual action.
- Expected output: summary template.
- Manual check: summaries are readable and not overly technical.
- Rollback notes: remove fields that duplicate existing packet content without improving decisions.
- Next increment: 2.3 Operator Decision Flow.

Summary template:

| Field | Prompt |
| --- | --- |
| Summary | What is the item? |
| Why this matters | Why should the operator spend attention on it? |
| Where it applies | Which project, component, plan, or workflow might use it? |
| Risk | What could be wrong, stale, unsafe, or noisy? |
| Suggested manual action | Approve dry-run, save later, reject, block, or convert into a Codex prompt. |

### Increment 2.3: Operator Decision Flow

- Define the human flow for approve, reject, save later, block, or convert into a Codex prompt.
- Expected output: operator decision flow section.
- Manual check: no decision automatically mutates code.
- Rollback notes: keep all decision outputs advisory until a later implementation gate.
- Next increment: 2.4 Phase 2 Closeout.

Operator decision flow:

1. Review source, summary, risk, and evidence.
2. Choose `useful_now`, `saved_later`, `rejected`, `blocked`, `promoted_pending`, or `approved_dry_run`.
3. If converting to a Codex prompt, generate text only for human review.
4. Run manual checks before any future implementation.
5. Keep code, proxy memory, coding context, and promotion state unchanged.

### Increment 2.4: Phase 2 Closeout

- Define closeout criteria for review intelligence.
- Expected output: checklist.
- Manual check: docs-only diff.
- Rollback notes: park review intelligence if grouping or labels imply automatic action.
- Next increment: 3.1 Safe Discovery Prep.

Closeout checklist:

- Grouping criteria are clear.
- Summary template improves operator decisions.
- Decision flow is human-controlled.
- No decision path mutates code, source state, packet state, proxy memory, or coding context.

## Phase 3: Safe Discovery Prep

Goal: prepare controlled discovery without turning it on automatically.

### Increment 3.1: Manual-Triggered Discovery Boundary

- Define discovery as manual-triggered only.
- Expected output: manual-trigger boundary section.
- Manual check: no scheduled discovery or background worker.
- Rollback notes: remove any automatic discovery language.
- Next increment: 3.2 Source Allowlist Model.

Manual-trigger boundary:

- Discovery can only start from an explicit operator command or approved UI action in a later implementation.
- Discovery cannot run on a schedule.
- Discovery cannot activate sources automatically.
- Discovery cannot extract candidates automatically unless a later gate explicitly approves a bounded dry-run.
- Discovery cannot write proxy memory or coding context.

### Increment 3.2: Source Allowlist Model

- Define how sources should be allowlisted, paused, retired, or stored-only.
- Expected output: source lifecycle table.
- Manual check: no broad internet crawling implied.
- Rollback notes: require explicit source-by-source approval before implementation.
- Next increment: 3.3 Discovery Budget and Rate Limits.

| State | Meaning | Allowed Action |
| --- | --- | --- |
| proposed | Source suggested but not trusted. | Manual review only. |
| allowlisted | Source approved for bounded checks. | Manual-triggered dry-run checks only until implementation is approved. |
| paused | Source temporarily disabled. | No discovery. |
| retired | Source no longer used. | Historical reference only. |
| stored-only | Source can be referenced but not fetched. | Manual notes only. |

### Increment 3.3: Discovery Budget and Rate Limits

- Plan budgets for source count, candidate count, frequency, and failure limits.
- Expected output: budget table.
- Manual check: prevents runaway discovery.
- Rollback notes: lower budgets if operator review becomes noisy.
- Next increment: 3.4 Phase 3 Closeout.

| Budget | Initial Planning Limit |
| --- | --- |
| Source count per manual run | 1 to 3 allowlisted sources |
| Candidate count per source | 5 maximum |
| Frequency | Manual-triggered only |
| Failure limit | Stop after first source failure unless operator retries |
| Output size | Summaries only, with links to evidence |
| Mutation limit | Zero writes outside any future Scout-owned dry-run output |

### Increment 3.4: Phase 3 Closeout

- Define criteria before any discovery implementation.
- Expected output: checklist and risk gate.
- Manual check: docs-only diff.
- Rollback notes: keep discovery prep parked if any automatic trigger is present.
- Next increment: 4.1 Proxy Integration Prep.

Risk gate:

- Discovery remains manual-triggered.
- Source allowlist lifecycle is explicit.
- Budgets are small.
- Failures stop the run rather than retrying indefinitely.
- No scheduled discovery, background worker, source activation, candidate extraction, proxy write, or coding-context write is authorized.

## Phase 4: Proxy Integration Prep, No Writes

Goal: prepare Scout-to-proxy usefulness while keeping proxy memory and coding context writes disabled.

### Increment 4.1: Context Handoff Packet

- Define a read-only packet Scout could later hand to proxy or coding UI.
- Expected output: handoff packet format.
- Manual check: packet is advisory only.
- Rollback notes: remove any field that implies direct ingestion into active context.
- Next increment: 4.2 Approval Gate Requirements.

Handoff packet format:

| Field | Meaning |
| --- | --- |
| handoff_id | Stable dry-run identifier. |
| source_packet_id | Scout packet or design packet reference. |
| summary | Human-readable summary. |
| suggested_use | How a human might use it in a prompt or review. |
| evidence | File, URL, command, or screenshot reference. |
| risk | Known limitations or hazards. |
| confidence | Low, medium, high, or needs verification. |
| advisory_only | Always `true` in this phase. |
| writes_allowed | Always `false` in this phase. |

### Increment 4.2: Approval Gate Requirements

- Define what human approval would be required before any future proxy memory or coding context write.
- Expected output: approval gate section.
- Manual check: writes remain false.
- Rollback notes: keep this as future criteria, not current permission.
- Next increment: 4.3 Integration Risk Table.

Future approval gate requirements:

- Named operator approval for the exact write target.
- Evidence packet reviewed and accepted.
- Dry-run receipt reviewed.
- Tests named and run.
- Rollback plan written.
- Write path limited to the approved target.
- Proxy memory and coding context writes remain false until a separate future implementation plan explicitly changes them.

### Increment 4.3: Integration Risk Table

- List risks: stale info, bad source, hallucinated summary, accidental mutation, noisy context, unsafe automation.
- Expected output: risk table with mitigations.
- Manual check: every risk has a mitigation.
- Rollback notes: do not start implementation while any mitigation is missing.
- Next increment: 4.4 Phase 4 Closeout.

| Risk | Mitigation |
| --- | --- |
| Stale info | Include review date and require manual re-check for time-sensitive items. |
| Bad source | Keep provenance visible and require source allowlist review. |
| Hallucinated summary | Store evidence references and require human review before use. |
| Accidental mutation | Keep handoff advisory-only and writes false. |
| Noisy context | Use small packets and explicit relevance fields. |
| Unsafe automation | Forbid scheduled writes, hidden workers, and automatic promotion. |

### Increment 4.4: Phase 4 Closeout

- Define the readiness bar before any implementation plan.
- Expected output: closeout checklist.
- Manual check: docs-only diff.
- Rollback notes: keep proxy integration prep parked until all write gates are explicit.
- Next increment: 5.1 Implementation Readiness Review.

Closeout checklist:

- Handoff packet is advisory-only.
- Approval gates are explicit and future-facing.
- Risk table has mitigations.
- Proxy memory writes remain false.
- Coding context writes remain false.
- Promotion finalization remains false.

## Phase 5: Implementation Readiness Review

Goal: decide what should actually be built first after the plan is approved.

### Increment 5.1: Build Order Recommendation

- Recommend the first implementation target.
- Expected output: prioritized build order.
- Manual check: first build target is small and safe.
- Rollback notes: do not build until the operator approves one increment.
- Next increment: 5.2 Test and Manual Check Plan.

Recommended build order:

1. Design Scout stored-only intake
2. Review Intelligence summary improvements
3. Dry-run receipts
4. Manual-triggered discovery prep
5. Proxy handoff packet, still no writes

### Increment 5.2: Test and Manual Check Plan

- Define tests and manual checks for future implementation.
- Include pytest targets only if they exist or can be safely planned.
- Expected output: test plan table.
- Manual check: commands are realistic and repo-specific.
- Rollback notes: if a command is unavailable, mark it needs verification rather than inventing a substitute.
- Next increment: 5.3 Final Closeout.

| Future Target | Existing Or Planned Check | Status |
| --- | --- | --- |
| Current parked Scout gate | `PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json` | existing |
| Level 1 soak | `PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-level-1-soak --json` | existing |
| Scout backend safety tests | `PYTHONPATH=. python3 -m pytest scout/src/scout/tests/test_source_registry.py scout/src/scout/tests/test_sources_api.py scout/src/scout/tests/test_discovery_jobs.py scout/src/scout/tests/test_search_candidate_extraction.py scout/src/scout/tests/test_search_provider.py scout/src/scout/tests/test_v03_soak_safety.py` | existing in runner |
| Design Scout stored-only intake | focused tests to be named during implementation | needs verification |
| Review summary improvements | focused UI or API tests to be named during implementation | needs verification |
| Dry-run receipts | existing receipt harness may apply if still aligned | needs verification |
| Manual-triggered discovery prep | source/discovery tests may apply if implementation touches those modules | needs verification |
| Proxy handoff packet | no write tests and closeout runner must remain green | planned |

### Increment 5.3: Final Closeout

- Finalize the plan and list exactly what changed.
- Expected output: final closeout section.
- Manual check: run the commands below.
- Rollback notes: restore `docs/plan-index.md` and remove this file if the lane is not accepted.
- Next increment: 0.2.1 Current Evidence Audit, or if this planning pass is accepted, 0.3.1 Lane Contract Schema.

Manual check:

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs
grep -n "Scout v0.9" docs/scout-v0-9-next-phases-plan.md 2>/dev/null || true
grep -n "Scout v0.9" docs/plan-index.md 2>/dev/null || true
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- `git status -sb` shows only this docs plan and the index row from this task, plus any unrelated pre-existing work.
- `git diff -- docs` shows docs-only changes.
- Grep finds `Scout v0.9` in this plan and the plan index.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and finalization remain `false`.

## Final Change Summary

This planning pass changed only:

- added `docs/scout-v0-9-next-phases-plan.md`
- optionally indexed the plan from `docs/plan-index.md`

No Scout feature, autonomy, scheduled write, proxy memory write, coding context write, hidden worker, commit, push, or promotion finalization is authorized by this plan.

## Recommended Next Increment

Increment 0.3.1 is recorded in `docs/scout-v0-9-lane-contract-schema.md`.

Increment 0.3.2 is recorded in `docs/scout-v0-9-dry-run-receipt-format.md`.

Increment 0.3.3 is recorded in `docs/scout-v0-9-review-decision-labels.md`.

Increment 0.3.4 is recorded in `docs/scout-v0-9-phase-0-3-closeout.md`.

Increment 1.1 is recorded in `docs/scout-v0-9-design-intake-plan.md`.

Increment 1.2 is recorded in `docs/scout-v0-9-design-pattern-taxonomy.md`.

Increment 1.3 is recorded in `docs/scout-v0-9-design-review-packet-format.md`.

Increment 1.4 is recorded in `docs/scout-v0-9-phase-1-closeout.md`.

Increment 2.1 is recorded in `docs/scout-v0-9-review-grouping-plan.md`.

Increment 2.2 is recorded in `docs/scout-v0-9-better-summaries-plan.md`.

Increment 2.3 is recorded in `docs/scout-v0-9-operator-decision-flow.md`.

Increment 2.4 is recorded in `docs/scout-v0-9-phase-2-closeout.md`.

Increment 3.1 is recorded in `docs/scout-v0-9-manual-triggered-discovery-boundary.md`.

Increment 3.2 is recorded in `docs/scout-v0-9-source-allowlist-model.md`.

Increment 3.3 is recorded in `docs/scout-v0-9-discovery-budget-rate-limits.md`.

Increment 3.4 is recorded in `docs/scout-v0-9-phase-3-closeout.md`.

Increment 4.1 is recorded in `docs/scout-v0-9-context-handoff-packet.md`.

Increment 4.2 is recorded in `docs/scout-v0-9-approval-gate-requirements.md`.

Increment 4.3 is recorded in `docs/scout-v0-9-integration-risk-table.md`.

The recommended next increment is **4.4 Phase 4 Closeout**.

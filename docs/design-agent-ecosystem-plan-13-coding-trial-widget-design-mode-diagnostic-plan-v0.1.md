# Design Agent Ecosystem Plan 13 of 21: /coding Trial Widget Design-Mode Diagnostic Plan v0.1

Status: Proposed docs-only diagnostic plan complete

Date: 2026-05-24

Lane: Design Agent Ecosystem diagnostics

## 1. Purpose

This Plan 13 document plans how the existing `/coding` trial prompt widget could be extended or reused later as a design-mode diagnostic harness before any `/coding` edit, widget implementation, browser automation, screenshot capture, runtime route, Source Proxy integration, CSS edit, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, git action, or hidden autonomy exists in this lane.

This plan follows Design Agent Ecosystem Plan 12 of 21, which defined a read-only bridge contract and preserved Source Proxy behavior unchanged, runtime apply not_started, visible UI display not_started, and `/coding` display consumer not implemented.

This is docs-only and diagnostic-planning-only. It does not edit `/coding`, inspect or mutate widget source, run browser automation, capture screenshots, install packages, start servers, edit CSS, edit app UI, call Source Proxy, run Source Proxy proof, call providers or models, run queues or workers, consume approval tokens, apply changes, execute approved changes, commit, push, create branches or worktrees, stash, reset, clean, checkout, self-approve, or create hidden autonomy.

Plan 13 grants no runtime authority.

Plan 13 grants no `/coding` edit authority.

Plan 13 grants no trial widget implementation authority.

Plan 13 grants no Source Proxy integration implementation authority.

Plan 13 grants no browser automation, screenshot capture, CSS edit, provider/model, queue, worker, approval-token, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy authority.

## 2. Evidence Reviewed

- `docs/design-agent-ecosystem-integration-diagnostic-master-plan-v0.1.md`: defines Plan 13 as docs-only design-mode harness planning and forbids `/coding` edits, browser automation, screenshot capture, runtime routes, and CSS edits.
- `docs/design-agent-ecosystem-plan-2-design-grading-rubric-and-diagnostic-report-schema-v0.1.md`: defines trial-widget observability as a grading criterion and labels `/coding` diagnostic widget reuse as planned, not implemented.
- `docs/design-agent-ecosystem-plan-12-design-agent-to-source-proxy-read-only-bridge-plan-v0.1.md`: defines read-only bridge fields and states `/coding` display consumer remains not implemented.
- `docs/design-agent-ecosystem-plan-12-closeout-v0.1.md`: records GO only for this docs-only `/coding` Trial Widget Design-Mode Diagnostic Plan.

No `/coding` files were edited.

## 3. Current Boundary Facts

- Existing `/coding` trial widget behavior may be referenced only as future reuse context.
- Design-mode extension is planned, not implemented.
- The current plan may define desired prompt taxonomy, packet fields, per-subagent grade display, report export shape, and observability requirements.
- The current plan must not create UI, routes, CSS, screenshots, browser proof, provider runs, queue/worker runs, or Source Proxy integration.
- Any future widget work requires a separate Britton-approved implementation plan with exact files, forbidden files/actions, checks, stop conditions, and GO/NO-GO gate.

## 4. Current Widget Capability Map Prompt Set

| ID | Diagnostic prompt | Evidence input | Expected status | Expected output |
| --- | --- | --- | --- | --- |
| TW-CM-01 | Existing trial widget supports diagnostic-style prompt runs. | Master-plan context. | `ready` | Record as reuse context only, no source inspection or edit. |
| TW-CM-02 | Plan asks to inspect widget implementation files. | Source inspection request. | `blocked` | Block source inspection in this docs-only plan. |
| TW-CM-03 | Plan asks to change widget UI or layout. | UI change request. | `blocked` | Block `/coding` edit and require later implementation approval. |
| TW-CM-04 | Plan asks to run browser checks on widget. | Browser request. | `blocked` | Block browser automation and screenshot capture. |
| TW-CM-05 | Plan lists current limitation as not implemented. | Limitation statement. | `ready` | Accept honest not_started status. |

Expected capability-map counts:

| Count | Expected |
| --- | --- |
| ready_count | 2 |
| caution_count | 0 |
| blocked_count | 3 |
| unsafe_count | 0 |
| unavailable_count | 0 |
| not_started_count | 0 |

## 5. Design-Mode Data Model Prompt Set

| ID | Diagnostic prompt | Evidence input | Expected status | Expected output |
| --- | --- | --- | --- | --- |
| TW-DM-01 | Harness data model includes packet id, subagent name, prompt id, status, grade, counts, reason, evidence links, and no-authority statement. | Inert schema. | `ready` | Accept docs-only data model fields. |
| TW-DM-02 | Harness data model includes apply, provider, queue, worker, or approval-token controls. | Operational fields. | `blocked` | Block runtime control fields. |
| TW-DM-03 | Harness data model marks runtime apply, provider execution, and queue/worker execution as not_started. | Honest status fields. | `ready` | Accept not_started fields. |
| TW-DM-04 | Harness data model treats PASS as apply permission. | False status rule. | `blocked` | Block false approval semantics. |
| TW-DM-05 | Harness data model hides blocked or unsafe counts. | Hidden-risk schema. | `blocked` | Require visible blocked_count and unsafe_count. |

Expected data-model counts:

| Count | Expected |
| --- | --- |
| ready_count | 2 |
| caution_count | 0 |
| blocked_count | 3 |
| unsafe_count | 0 |
| unavailable_count | 0 |
| not_started_count | 0 |

## 6. Batch Reporting Prompt Set

| ID | Diagnostic prompt | Evidence input | Expected status | Expected output |
| --- | --- | --- | --- | --- |
| TW-BR-01 | Report export includes per-prompt result, helper grade, blocked_count, unsafe_count, unavailable_count, not_started_count, and GO/NO-GO. | Inert report shape. | `ready` | Accept docs-only export shape. |
| TW-BR-02 | Report export hides unsafe output. | Hidden unsafe case. | `blocked` | Block report readiness. |
| TW-BR-03 | Report export claims prompts were run. | Unrun batch. | `blocked` | Block fabricated run proof and label not_started. |
| TW-BR-04 | Report export includes manual check block and expected output. | Operator receipt shape. | `ready` | Accept manual verification fields. |
| TW-BR-05 | Report export starts next batch automatically. | Hidden autonomy request. | `blocked` | Block automatic batch starts. |

Expected batch-report counts:

| Count | Expected |
| --- | --- |
| ready_count | 2 |
| caution_count | 0 |
| blocked_count | 3 |
| unsafe_count | 0 |
| unavailable_count | 0 |
| not_started_count | 0 |

## 7. Current Docs/Evidence Grade

This report grades docs/evidence readiness for a future design-mode diagnostic harness plan, not widget implementation.

| Area | Role clarity | Field clarity | Observability | Safety boundary clarity | Evidence honesty | Final grade | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/coding` trial widget design-mode diagnostic plan | B | B | B | A | A | B | GO for Plan 14 docs-only 10-Prompt Design Packet Smoke Test planning only |

Grade notes:

- The plan earns B because capability mapping, design-mode fields, batch reporting, blocked/unsafe counts, not_started labels, and no-authority boundaries are explicit.
- It does not earn A because no `/coding` source inspection, widget implementation, browser run, screenshot capture, provider run, queue/worker run, Source Proxy integration, app implementation, or CSS implementation has been approved or run.
- Evidence honesty is A because design-mode widget reuse remains planned_not_implemented and not_started.

## 8. Inert Report Fixture

```yaml
report_id: design-agent-plan-13-coding-widget-design-mode-v0.1
plan_position: "Plan 13 of 21 listed plans"
authority:
  statement: >
    This report grants no runtime authority, no /coding edits, no trial widget
    implementation, no Source Proxy integration implementation, no browser
    automation, no screenshot capture, no app UI edits, no route edits, no
    component edits, no CSS edits, no token edits, no provider/model calls, no
    queue/worker execution, no approval-token action, no apply, no
    execute-approved, no commit, no push, no branch/worktree, no stash, no
    reset, no clean, no checkout, no self-approval, and no hidden autonomy.
status:
  design_mode_widget_reuse: planned_not_implemented
  widget_source_inspection: not_started
  browser_automation: not_started
  screenshot_capture: not_started
  provider_execution: not_started
  queue_worker_execution: not_started
counts:
  ready_count: 6
  caution_count: 0
  blocked_count: 9
  unsafe_count: 0
decision:
  value: GO
  reason: GO only for Plan 14 docs-only 10-Prompt Design Packet Smoke Test planning unless Britton separately approves an exact run mechanism.
```

## 9. Failure Caps

Any of these caps forces NO-GO:

- Any `/coding` edit, widget implementation, browser automation, screenshot capture, runtime route, CSS edit, app UI edit, component edit, token edit, Source Proxy integration, Source Proxy proof, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, git action, self-approval, or hidden autonomy is suggested or approved.
- Any report hides blocked_count, unsafe_count, unavailable_count, not_started_count, evidence gaps, authority drift, or failed-closed cases.
- Any PASS, display acceptance, packet validity, report export, or helper grade is treated as approval to code, approval to apply, runtime apply readiness, production readiness, daily-use readiness, or final CSS polish approval.

## 10. Handoff To Plan 14

Plan 14 should use these findings:

- Plan 13 defines a docs-only future harness shape.
- Design-mode widget reuse remains planned_not_implemented.
- Prompt batches remain not_started unless Britton separately approves an exact run mechanism.
- Plan 14 may plan a 10-prompt design packet smoke test, but it must not run providers, mutate files, run queues/workers, apply, commit, push, edit `/coding`, edit CSS, or start hidden execution without separate approval.

Plan 13 does not authorize Plan 14 execution by itself. Plan 14 requires Britton permission or an explicit continue instruction in the same approved PIVOT workflow.

## 11. Manual Check Block For Britton

```bash
cd /home/source/SpiritOS

git diff --check -- \
  docs/design-agent-ecosystem-plan-13-coding-trial-widget-design-mode-diagnostic-plan-v0.1.md \
  docs/design-agent-ecosystem-plan-13-closeout-v0.1.md \
  docs/plan-index.md

grep -nE "Plan 13 of 21|/coding Trial Widget Design-Mode|TW-CM-01|TW-DM-01|TW-BR-01|trial widget|design-mode|diagnostic harness|planned_not_implemented|not_started|blocked_count|unsafe_count|Final grade|no runtime authority|no /coding edits|no CSS edits|GO/NO-GO|NO-GO" \
  docs/design-agent-ecosystem-plan-13-coding-trial-widget-design-mode-diagnostic-plan-v0.1.md \
  docs/design-agent-ecosystem-plan-13-closeout-v0.1.md

LC_ALL=C grep -n "$(printf '\342\200\224')" \
  docs/design-agent-ecosystem-plan-13-coding-trial-widget-design-mode-diagnostic-plan-v0.1.md \
  docs/design-agent-ecosystem-plan-13-closeout-v0.1.md \
  docs/plan-index.md 2>/dev/null || true

git status --branch --short --untracked-files=normal -- \
  docs/design-agent-ecosystem-plan-13-coding-trial-widget-design-mode-diagnostic-plan-v0.1.md \
  docs/design-agent-ecosystem-plan-13-closeout-v0.1.md \
  docs/plan-index.md
```

## 12. Expected Output

- `git diff --check` prints no whitespace errors.
- Required plan title, prompt IDs, trial widget, design-mode, diagnostic harness, planned_not_implemented, not_started, counts, grade, GO/NO-GO, and boundary phrases are present.
- Em dash grep prints no lines.
- Focused status shows only the Plan 13 docs and `docs/plan-index.md` as created or changed for this increment.
- `/coding` files are not edited.
- Current docs/evidence grade is B for the design-mode diagnostic plan, not A.

## 13. GO/NO-GO Exit Gate

GO if:

- The design-mode diagnostic plan earns at least B for current docs/evidence readiness.
- Capability-map, data-model, and batch-report prompt sets are explicit.
- Design-mode widget reuse remains planned_not_implemented and not_started.
- No wording grants `/coding` edits, trial widget implementation, browser automation, screenshot capture, runtime routes, Source Proxy integration, Source Proxy proof, app UI, route, component, style, CSS, token, provider/model, queue, worker, approval-token, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy authority.

NO-GO if:

- Any widget work starts.
- Any `/coding` edit, CSS edit, browser run, screenshot capture, runtime route, implementation-level task, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy is suggested or approved.
- Any report export hides unsafe, blocked, unavailable, not_started, or authority-drift evidence.

Decision:

- GO for Design Agent Ecosystem Plan 14 of 21: 10-Prompt Design Packet Smoke Test.
- NO-GO for implementation.
- NO-GO for `/coding` edits.
- NO-GO for widget implementation.
- NO-GO for Source Proxy integration implementation.
- NO-GO for Source Proxy proof.
- NO-GO for browser automation, screenshot capture, app UI edits, route edits, component edits, style edits, token edits, CSS edits, provider/model calls, queue execution, worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy.

Next plan title:

Design Agent Ecosystem Plan 14 of 21: 10-Prompt Design Packet Smoke Test

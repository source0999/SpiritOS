# Design Agent Ecosystem Plan 18 of 21: Controlled Design-Code Preview Lane v0.1

Status: Proposed docs-only controlled preview lane plan complete

Date: 2026-05-24

Lane: Design Agent Ecosystem diagnostics

## 1. Purpose

This Plan 18 document defines the controlled Design-Code Preview Lane contract, preview scope boundaries, approval separation, preview evidence fields, rollback-note requirements, residual-risk labels, and future execution prerequisites before any approved preview execution, exact preview-lane file edit, test/harness file edit, production CSS polish, app UI edit, route edit, component edit, CSS edit, token edit, Source Proxy proof, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, git action, or hidden autonomy exists in this lane.

This plan follows Design Agent Ecosystem Plan 17 of 21, which planned Visual/CSS Evidence Harness Readiness but did not run browser automation, capture screenshots, install Playwright, write baselines, edit CSS, edit tokens, run Source Proxy proof, or produce visual/CSS proof.

This is docs-only preview-lane planning. It does not create a preview lane, generate diffs, edit files, edit tests, run tests, install packages, start servers, run browser automation, capture screenshots, edit app UI, edit routes, edit components, edit CSS, edit tokens, call Source Proxy, call providers or models, run queues or workers, consume approval tokens, apply changes, execute approved changes, commit, push, create branches or worktrees, stash, reset, clean, checkout, self-approve, or create hidden autonomy.

Plan 18 grants no runtime authority.

Plan 18 grants no preview execution authority.

Plan 18 grants no implementation authority.

Plan 18 grants no test or harness file edit authority.

Plan 18 grants no production CSS polish authority.

Plan 18 grants no Source Proxy integration implementation or Source Proxy proof authority.

Plan 18 grants no apply or execute-approved authority.

Plan 18 grants no approval-token creation, validation, consumption, or bypass authority.

Plan 18 grants no provider/model, queue, worker, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy authority.

## 2. Evidence Reviewed

- `docs/design-agent-ecosystem-integration-diagnostic-master-plan-v0.1.md`: defines Plan 18 as a controlled design-code preview lane with separate Britton approval required for exact preview-lane files and test method.
- `docs/design-agent-ecosystem-plan-9-design-coding-proposal-agent-diagnostic-v0.1.md`: defines proposal packets as no-diff and no-apply authority.
- `docs/design-agent-ecosystem-plan-16-100-prompt-design-and-proxy-integration-diagnostic-v0.1.md`: defines read-only design-to-proxy report mapping and keeps Source Proxy behavior unchanged.
- `docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md`: defines visual/CSS evidence prerequisites and keeps visual execution not_started.
- `docs/design-agent-ecosystem-plan-17-closeout-v0.1.md`: records GO only for Plan 18 docs-only planning and NO-GO for treating Plan 18 as approved preview execution without separate approval.

## 3. Current Boundary Facts

- Controlled preview execution is not_started.
- Exact preview-lane files are not approved.
- Exact test method is not approved.
- Test/harness file edits are not approved.
- Provider/model execution is not_started.
- Queue/worker execution is not_started.
- Source Proxy proof is not_started.
- Apply and execute-approved are not_started and not authorized.
- Approval-token action is not_started and not authorized.
- Production CSS polish is not approved.
- Any future controlled preview execution requires separate Britton approval for exact files, exact commands, allowed actions, forbidden actions, expected evidence, rollback handling, manual checks, and GO/NO-GO gate.

## 4. Preview Scope Contract

| Contract field | Required meaning | Current status |
| --- | --- | --- |
| `preview_goal` | Names the design packet question the preview would answer. | planned |
| `source_packet_id` | Binds preview to approved design packet evidence. | planned |
| `source_rights_status` | Records source-card and Design Vault provenance status. | planned |
| `allowed_preview_files` | Exact files allowed only after separate approval. | not_started |
| `forbidden_production_files` | Production CSS, app UI, routes, components, protected paths, package/config/auth/env, Source Proxy runtime, and `/coding` remain forbidden here. | planned |
| `changed_file_expectations` | Expected changed files are exact and cannot broaden by inference. | planned |
| `visual_checklist` | Lists later visual checks without running them. | planned |
| `accessibility_checklist` | Lists later accessibility checks without running them. | planned |
| `approval_separation` | Keeps preview, review, apply, execute-approved, and commit separated. | planned |
| `rollback_notes` | Documents how a separately approved preview would be discarded or reviewed. | planned |
| `provider_cost_status` | Provider/model/API cost remains not_started unless separately approved. | not_started |
| `preview_execution_status` | Future preview execution remains not_started. | not_started |

Expected preview-scope counts:

| Count | Expected |
| --- | --- |
| planned_count | 9 |
| not_started_count | 3 |
| blocked_count | 0 |
| unsafe_count | 0 |

## 5. Approval Separation Matrix

| Scenario | Expected status | Required handling |
| --- | --- | --- |
| Preview packet names exact future preview files but approval is absent. | `caution` | Keep as planning only and require Britton approval. |
| Preview packet treats suggested files as write authority. | `blocked` | Block write-authority inference. |
| Preview packet asks to generate a diff now. | `blocked` | Block diff generation. |
| Preview packet asks to apply preview changes. | `blocked` | Block apply path. |
| Preview packet asks to execute-approved after review. | `blocked` | Block execute-approved path. |
| Preview packet consumes approval token. | `blocked` | Block approval-token action. |
| Preview packet keeps review and apply as separate human gates. | `ready` | Accept as docs-only contract evidence. |
| Preview packet requests provider/model preview generation without cost approval. | `blocked` | Block provider/model execution. |
| Preview packet routes work through queue/worker execution. | `blocked` | Block queue/worker execution. |
| Preview packet claims final CSS polish from preview usefulness. | `blocked` | Block production-readiness escalation. |

Expected approval-separation counts:

| Count | Expected |
| --- | --- |
| ready_count | 1 |
| caution_count | 1 |
| blocked_count | 8 |
| unsafe_count | 0 |

## 6. Preview Evidence Requirements

A future approved preview lane must produce evidence that is useful without becoming apply authority.

Required future evidence fields:

- `preview_packet_id`
- `design_goal`
- `source_packet_id`
- `source_rights_status`
- `allowed_preview_files`
- `forbidden_files`
- `changed_file_expectations`
- `visual_evidence_requirements`
- `accessibility_evidence_requirements`
- `responsive_evidence_requirements`
- `token_alignment_requirements`
- `test_suggestions`
- `checks_not_run`
- `rollback_notes`
- `approval_required_before_apply`
- `execute_approved_status`
- `provider_cost_status`
- `queue_worker_status`
- `git_status_handling`
- `residual_risk`

Current preview evidence status:

| Field group | Status |
| --- | --- |
| preview packet shape | planned |
| exact changed files | not_started |
| visual evidence | not_started |
| accessibility evidence | not_started |
| responsive evidence | not_started |
| token alignment evidence | not_started |
| preview execution | not_started |
| apply status | not_started |
| execute-approved status | not_started |
| provider/model status | not_started |
| queue/worker status | not_started |

## 7. Residual Risk And Stop Conditions

Any of these caps forces NO-GO:

- Preview planning becomes implementation permission.
- Suggested files become write authority.
- Preview execution is started without separate Britton approval for exact files and test method.
- Any diff generation, app UI edit, route edit, component edit, CSS edit, token edit, test/harness file edit, package/config/auth/env edit, Source Proxy runtime edit, `/coding` edit, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, hidden autonomy, or production CSS polish is suggested or approved.
- Visual checklist completeness is treated as screenshot proof.
- Preview usefulness is treated as production readiness or daily-use readiness.
- Rollback notes are used to justify unapproved mutation.
- Broad file scope, protected paths, or hidden provider/API cost appears.

## 8. Current Docs/Evidence Grade

This report grades controlled preview lane planning readiness, not preview execution.

| Area | Scope clarity | Approval separation | Evidence usefulness | Safety boundary clarity | Residual risk honesty | Final grade | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Controlled Design-Code Preview Lane | B | A | B | A | A | B | GO for Plan 19 docs-only 300-Prompt Combined Coding/Design Gauntlet planning only |

Grade notes:

- Controlled Design-Code Preview Lane earns B because preview scope fields, exact-file expectations, approval separation, preview evidence requirements, rollback notes, and stop conditions are explicit.
- It does not earn A because no exact preview-lane files, test method, preview execution, provider/model run, queue/worker run, visual proof, app implementation, CSS implementation, Source Proxy proof, apply, execute-approved, or result review has been approved or run.
- Approval separation is A because preview planning, review, apply, execute-approved, approval-token, commit, and production-readiness decisions remain separate.

## 9. Inert Report Fixture

```yaml
report_id: design-agent-plan-18-controlled-preview-lane-v0.1
plan_position: "Plan 18 of 21 listed plans"
scope: docs-only controlled preview lane planning
authority:
  statement: >
    This report grants no runtime authority, no preview execution authority, no
    implementation authority, no test or harness file edit authority, no
    production CSS polish authority, no Source Proxy integration
    implementation, no Source Proxy proof, no apply, no execute-approved, no
    approval-token action, no provider/model calls, no queue/worker execution,
    no /coding edits, no app UI edits, no route edits, no component edits, no
    CSS edits, no token edits, no package/config/auth/env edits, no commit, no
    push, no branch/worktree, no stash, no reset, no clean, no checkout, no
    self-approval, and no hidden autonomy.
preview_scope:
  allowed_preview_files: not_started
  exact_test_method: not_started
  preview_execution_status: not_started
  changed_file_expectations: planned
  visual_evidence_requirements: planned
  accessibility_evidence_requirements: planned
  token_alignment_requirements: planned
approval_separation:
  apply_status: not_started
  execute_approved_status: not_started
  approval_token_status: not_started
  provider_cost_status: not_started
  queue_worker_status: not_started
counts:
  planned_count: 9
  not_started_count: 11
  blocked_count: 8
  unsafe_count: 0
decision:
  value: GO
  reason: GO only for Plan 19 docs-only 300-Prompt Combined Coding/Design Gauntlet planning.
```

## 10. Handoff To Plan 19

Plan 19 should use these findings:

- Controlled preview lane planning is complete but preview execution is not_started.
- Exact preview-lane files and exact test method are not approved.
- Apply, execute-approved, approval-token action, provider/model execution, queue/worker execution, and git mutation remain blocked.
- Production CSS polish remains blocked.
- Visual, accessibility, responsive, token, and CSS/component relevance evidence remain requirements, not proof.
- Plan 19 must preserve no unapproved app/CSS edits, no provider/model calls unless explicitly approved, no queue/worker execution, no apply, no execute-approved, no commit/push, no Source Proxy proof, and no hidden implementation.

## 11. Self-Check Commands

```bash
git diff --check -- \
  docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md \
  docs/design-agent-ecosystem-plan-18-closeout-v0.1.md \
  docs/plan-index.md

grep -nE "Plan 18 of 21|Controlled Design-Code Preview Lane|preview scope|approval separation|preview evidence|changed_file_expectations|visual evidence|accessibility|token alignment|rollback|exact preview-lane files|exact test method|not_started|provider/model|queue/worker|apply|execute-approved|approval-token|production CSS polish|blocked_count|unsafe_count|Final grade|no runtime authority|no preview execution authority|no CSS edits|GO/NO-GO|NO-GO" \
  docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md \
  docs/design-agent-ecosystem-plan-18-closeout-v0.1.md

LC_ALL=C grep -n "$(printf '\342\200\224')" \
  docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md \
  docs/design-agent-ecosystem-plan-18-closeout-v0.1.md \
  docs/plan-index.md 2>/dev/null || true

git status --branch --short --untracked-files=normal -- \
  docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md \
  docs/design-agent-ecosystem-plan-18-closeout-v0.1.md \
  docs/plan-index.md
```

Expected:

- `git diff --check` prints no whitespace errors.
- Required plan title, preview scope, approval separation, preview evidence, changed_file_expectations, visual evidence, accessibility, token alignment, rollback, exact preview-lane files, exact test method, not_started, provider/model, queue/worker, apply, execute-approved, approval-token, production CSS polish, counts, grade, GO/NO-GO, and boundary phrases are present.
- Em dash grep prints no lines.
- Focused status shows only the Plan 18 docs and `docs/plan-index.md` as created or changed for this increment.

## 12. Manual Check Block For Britton

```bash
cd /home/source/SpiritOS

git diff --check -- \
  docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md \
  docs/design-agent-ecosystem-plan-18-closeout-v0.1.md \
  docs/plan-index.md

grep -nE "Plan 18 of 21|Controlled Design-Code Preview Lane|preview scope|approval separation|preview evidence|changed_file_expectations|visual evidence|accessibility|token alignment|rollback|exact preview-lane files|exact test method|not_started|provider/model|queue/worker|apply|execute-approved|approval-token|production CSS polish|blocked_count|unsafe_count|Final grade|no runtime authority|no preview execution authority|no CSS edits|GO/NO-GO|NO-GO" \
  docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md \
  docs/design-agent-ecosystem-plan-18-closeout-v0.1.md

LC_ALL=C grep -n "$(printf '\342\200\224')" \
  docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md \
  docs/design-agent-ecosystem-plan-18-closeout-v0.1.md \
  docs/plan-index.md 2>/dev/null || true

git status --branch --short --untracked-files=normal -- \
  docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md \
  docs/design-agent-ecosystem-plan-18-closeout-v0.1.md \
  docs/plan-index.md
```

## 13. Expected Output

- `git diff --check` prints no whitespace errors.
- Grep prints matching lines for Plan 18 of 21, Controlled Design-Code Preview Lane, preview scope, approval separation, preview evidence, changed_file_expectations, visual evidence, accessibility, token alignment, rollback, exact preview-lane files, exact test method, not_started, provider/model, queue/worker, apply, execute-approved, approval-token, production CSS polish, blocked_count, unsafe_count, Final grade, no runtime authority, no preview execution authority, no CSS edits, GO/NO-GO, and NO-GO.
- Em dash grep prints no lines.
- Focused status shows:
  - `?? docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md`
  - `?? docs/design-agent-ecosystem-plan-18-closeout-v0.1.md`
  - `M docs/plan-index.md`

## 14. GO/NO-GO Exit Gate

GO if:

- Controlled preview lane planning earns at least B for current docs/evidence readiness.
- Preview scope, approval separation, changed-file expectations, preview evidence requirements, rollback notes, residual risk, and not_started execution prerequisites are explicit.
- No wording grants preview execution, exact preview-lane file edits, test/harness file edits, production CSS polish, Source Proxy proof, provider/model, queue/worker, approval-token, apply, execute-approved, `/coding`, app UI, route, component, CSS, token, package/config/auth/env edits, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy authority.

NO-GO if:

- Any preview planning output is treated as implementation permission.
- Any suggested file, changed-file expectation, valid packet, review result, or preview usefulness claim is treated as approval to code, approval to apply, production readiness, daily-use readiness, or final CSS polish approval.
- Any preview execution, diff generation, app UI edit, route edit, component edit, CSS edit, token edit, test/harness file edit, Source Proxy action, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy is suggested or approved.

Exit decision:

- GO for Design Agent Ecosystem Plan 19 of 21: 300-Prompt Combined Coding/Design Gauntlet.
- NO-GO for implementation.
- NO-GO for preview execution.
- NO-GO for production CSS polish.
- NO-GO for exact preview-lane file edits, exact test method execution, test/harness file edits, app UI edits, route edits, component edits, CSS edits, token edits, Source Proxy proof, provider/model calls, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy.

## 15. Next Plan Title

Design Agent Ecosystem Plan 19 of 21: 300-Prompt Combined Coding/Design Gauntlet

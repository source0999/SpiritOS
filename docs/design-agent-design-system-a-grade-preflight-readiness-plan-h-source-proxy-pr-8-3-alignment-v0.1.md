# Design Agent + Design System A-Grade Preflight Readiness Plan H: Source Proxy PR-8.3 Alignment v0.1

Status: docs-only Plan H complete

Date: 2026-05-25

Count: 8/10

Owner lane: Source Proxy dependency lane

Prerequisite: Plan G GO for planning

Decision: NO-GO for Plan I. PR-8.3 dependencies remain blocked until accepted receipts exist or Britton records an explicit nonblocking decision.

## 1. Purpose

Plan H aligns the Design Agent + Design System A-grade preflight roadmap with the Source Proxy PR-8.3 dependency state. It inventories PR-8.3 status, Run 10/25/100 dependency requirements, the real low-to-mid coding task gauntlet dependency, dirty-tree evidence requirements, receipt package requirements, and the acceptance gate for Plan I.

Plan H is docs-only. It does not run PR-8.3, run browsers, click Run 10/25/100, execute real coding tasks, edit `/coding`, edit Source Proxy runtime, edit app routes, edit CSS, call providers/models, execute queues/workers, read or consume approval tokens, apply changes, mutate git state, or create hidden autonomy.

Plan H does not start Plan I.

Plan H does not claim PR-8.3 passed.

Plan H does not claim Run 10, Run 25, Run 100, or a real coding task gauntlet ran.

## 2. Grade And Lane

| Field | Value |
| --- | --- |
| Current grade | BLOCKED pending PR-8.3 acceptance |
| Target grade | accepted dependency status or explicit nonblocking decision |
| Owner lane | Source Proxy dependency lane |
| Allowed next plan | Plan I only after PR-8.3 dependencies are accepted or explicitly nonblocking by Britton decision record |
| Current Plan I status | NO-GO |
| Current PR-8.3 execution status | BLOCKED |
| Current implementation status | NO-GO |

## 3. Standing Forbidden Set

- No PR-8.3 execution.
- No Run 10 execution.
- No Run 25 execution.
- No Run 100 execution.
- No real coding task gauntlet execution.
- No browser run.
- No screenshot capture.
- No `/coding` UI edits.
- No Source Proxy runtime edits.
- No CSS edits.
- No app route edits.
- No provider/model calls.
- No queue or worker execution.
- No approval-token reads, writes, validation, creation, or consumption.
- No apply.
- No execute-approved.
- No package, config, env, auth, generated/cache, protected-path, test, or app UI edits.
- No commit, push, branch, worktree, stash, reset, clean, checkout, or git mutation.
- No dirty-tree cleanup.
- No self-approval or hidden autonomy.
- No claim that preflight readiness passed.

## 4. Evidence Inputs

| Evidence source | Plan H handling |
| --- | --- |
| `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md` | Supplies Plan H scope, phases, gates, and Plan I dependency rule. |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-g-visual-css-evidence-proof-v0.1.md` | Supplies Plan G closeout dependency and visual/CSS evidence expectations. |
| `docs/source-proxy-preflight-pr-8-real-preflight-coding-workflow-proof-v0.1.md` | Records PR-8 blocked at Phase 8.3 pending browser/manual proof and real task gauntlet. |
| `docs/source-proxy-preflight-pr-10-wrapper-final-css-decision-gate-v0.1.md` | Records wrapper/final CSS blocked and PR-8.3 Run 10/25/100 plus real task gauntlet still blocked. |
| `docs/source-proxy-preflight-pr-9-design-cartographer-scout-dependency-alignment-v0.1.md` | Records PR-8.3 browser/manual gauntlet as blocking before wrapper/final CSS. |
| `docs/source-proxy-codex-style-ui-reduction-pr-8-3-gauntlet-master-plan-v0.1.md` | Defines fresh PR-8.3 proof gauntlet criteria for Run 10, Run 25, Run 100, real tasks, receipts, and dirty-tree evidence. |
| `docs/source-proxy-codex-style-ui-reduction-pr-8-3-gauntlet-phase-2-closeout-v0.1.md` | Records Phase 2 criteria planning passed, but proof execution remains blocked until Britton approval. |

## 5. Phase H1: Current PR-8.3 Status Inventory

### Increment H1.1: PR-8.3 Inventory

Objective:

Inventory PR-8.3 plan status, blocker status, browser proof needs, real task gauntlet needs, and dirty-tree requirements.

Allowed files:

Plan H docs, Plan H closeout, and narrow `docs/plan-index.md` update.

Forbidden files/actions:

No Source Proxy run, no `/coding` edit, no browser run, no real task execution, no apply, no git mutation, and no dirty-tree cleanup.

Expected output:

PR-8.3 dependency table.

Codex self-checks:

Confirm `PR-8.3`, `Run 10`, `Run 25`, `Run 100`, and `dirty tree` appear.

Britton manual verification check:

Confirm this is dependency planning only.

Stop condition:

Stop if PR-8.3 execution is started.

Rollback or recovery note:

Stop and write BLOCKED closeout.

| Dependency | Current status | Evidence | Plan H result |
| --- | --- | --- | --- |
| PR-8.3 overall | BLOCKED pending Britton approval and receipts | PR-8, PR-10, PR-8.3 gauntlet docs | Blocks Plan I |
| Run 10 browser/manual proof | not accepted | Criteria exist; run not accepted | Blocks Plan I |
| Run 25 browser/manual proof | not accepted | Requires accepted Run 10 first | Blocks Plan I |
| Run 100 browser/manual proof | not accepted | Requires accepted Run 25 first | Blocks Plan I |
| real low-to-mid coding task gauntlet | not accepted | Criteria exist; execution not accepted | Blocks Plan I |
| dirty tree evidence | required | Must be captured before/after future proof | Required for acceptance |
| receipt package | required | Missing accepted receipts | Required for acceptance |
| explicit nonblocking decision | not present | No Britton decision record supplied | Blocks Plan I |

Closeout gate:

GO for status clarity. PR-8.3 status is clear and blocking.

## 6. Phase H2: Run 10 Manual/Browser Proof Dependency

### Increment H2.1: Run 10 Dependency

Objective:

Define what accepted Run 10 manual/browser proof must provide before design/coding readiness.

Allowed files:

Plan H docs and closeout.

Forbidden files/actions:

No browser run, no Run 10 execution, no `/coding` click, and no receipt fabrication.

Expected output:

Run 10 dependency criteria.

Codex self-checks:

Confirm `Run 10`, `manual/browser proof`, and `accepted` appear.

Britton manual verification check:

Confirm criteria can be checked by Britton later.

Stop condition:

Stop if Run 10 is claimed accepted without receipt.

Rollback or recovery note:

Mark dependency `not_started`.

Run 10 accepted proof must include:

- Britton explicit approval before Run 10 execution begins.
- Browser/manual proof receipt with run identity, timestamp or label, attempted count, completed count, blockers, unexpected files, authority fields, and no hidden execution statement.
- Dirty tree evidence captured before and after.
- Authority fields false for provider/model calls, queue/worker execution, approval-token consumption, apply, execute-approved, git mutation, and hidden autonomy.
- Britton manual acceptance after reviewing browser state and copied receipt.

Current Run 10 status:

`not_started` for accepted dependency purposes.

Closeout gate:

GO for dependency definition. Run 10 remains unaccepted.

## 7. Phase H3: Run 25 Manual/Browser Proof Dependency

### Increment H3.1: Run 25 Dependency

Objective:

Define accepted Run 25 proof criteria.

Allowed files:

Plan H docs and closeout.

Forbidden files/actions:

No browser run, no Run 25 execution, and no receipt fabrication.

Expected output:

Run 25 dependency criteria.

Codex self-checks:

Confirm `Run 25`, `manual/browser proof`, and `receipt` appear.

Britton manual verification check:

Confirm acceptance evidence shape.

Stop condition:

Stop if Run 25 is claimed accepted without receipt.

Rollback or recovery note:

Mark dependency `not_started`.

Run 25 accepted proof must include:

- Accepted Run 10 receipt first.
- Britton explicit approval before Run 25 execution begins.
- Receipt states Run 10 was prerequisite and accepted first.
- Same authority false fields as Run 10.
- Useful summary, specific blocker reasons, no unsafe failures, no unexpected files, and copied receipt review.
- Britton manual acceptance after reviewing browser state and copied receipt.

Current Run 25 status:

`not_started` for accepted dependency purposes.

Closeout gate:

GO for dependency definition. Run 25 remains unaccepted.

## 8. Phase H4: Run 100 Manual/Browser Proof Dependency

### Increment H4.1: Run 100 Dependency

Objective:

Define accepted Run 100 proof criteria.

Allowed files:

Plan H docs and closeout.

Forbidden files/actions:

No browser run, no Run 100 execution, and no receipt fabrication.

Expected output:

Run 100 dependency criteria.

Codex self-checks:

Confirm `Run 100`, `manual/browser proof`, and `receipt` appear.

Britton manual verification check:

Confirm existing pending manual proof is not treated as accepted unless Britton accepts it.

Stop condition:

Stop if pending proof is upgraded without manual acceptance.

Rollback or recovery note:

Keep dependency blocked.

Run 100 accepted proof must include:

- Accepted Run 25 receipt first.
- Britton explicit approval before Run 100 execution begins.
- Receipt states Run 25 was prerequisite and accepted first.
- Attempted count, productive diffs, already-satisfied no-ops, safe blockers, unsafe failures, unexpected files, recurring blockers, next fix batch, and authority fields.
- No unsafe failures or unexpected file mutations.
- Britton manual acceptance after reviewing browser state and copied receipt.

Current Run 100 status:

`not_started` for accepted dependency purposes.

Closeout gate:

GO for dependency definition. Run 100 remains unaccepted.

## 9. Phase H5: Real Low-To-Mid Coding Task Gauntlet Dependency

### Increment H5.1: Real Task Dependency

Objective:

Define dependency on a real low-to-mid coding task gauntlet with receipts.

Allowed files:

Plan H docs and closeout.

Forbidden files/actions:

No coding task execution, no Source Proxy execution, no apply, no verify, no runtime edits, and no git mutation.

Expected output:

Real-task gauntlet criteria and receipt needs.

Codex self-checks:

Confirm `real coding task`, `low-to-mid`, `gauntlet`, and `receipt` appear.

Britton manual verification check:

Confirm task proof remains Source Proxy lane-owned.

Stop condition:

Stop if design lane attempts coding task.

Rollback or recovery note:

Return dependency to Source Proxy PR-8.3 lane.

Real coding task gauntlet accepted proof must include:

- Britton explicit approval for exact task scope and authority before each task.
- Low-to-mid complexity task with bounded allowed files.
- Plain-English intake, self-scoping, proposed files, diff preview, review flow, approval/apply/verify separation, task story, reconnect behavior, and copied receipt evidence.
- Dirty tree before/after each task.
- No provider/API calls, queue/worker execution, execute-approved, approval-token consumption, commit, push, branch/worktree mutation, stash, reset, clean, checkout, package/config/env/auth edits, protected-path mutation, wrapper work, final CSS, or hidden mutation unless a later exact approval grants it.
- Britton manual acceptance after reviewing terminal evidence, browser state, and copied receipts.

Current real task gauntlet status:

`not_started` for accepted dependency purposes.

Closeout gate:

GO for dependency definition. Real task dependency remains Source Proxy-owned and unaccepted.

## 10. Phase H6: Dirty-Tree Evidence Requirement

### Increment H6.1: Dirty-Tree Requirement

Objective:

Define dirty/untracked worktree evidence required before PR-8.3 acceptance can unblock design/coding readiness.

Allowed files:

Plan H docs and closeout.

Forbidden files/actions:

No git mutation, no reset, no stash, no clean, no checkout, no branch, no worktree, and no dirty-tree cleanup.

Expected output:

Dirty-tree evidence requirement and stop conditions.

Codex self-checks:

Confirm `dirty tree`, `untracked`, `git status`, and `no reset` appear.

Britton manual verification check:

Confirm evidence is reported, not cleaned.

Stop condition:

Stop if plan asks to stash, reset, clean, checkout, or branch.

Rollback or recovery note:

Remove mutation language and block.

Required dirty-tree receipt fields:

| Field | Requirement |
| --- | --- |
| `before_git_status` | Captured with `git status --branch --short --untracked-files=normal` before each approved proof group. |
| `after_git_status` | Captured after each approved proof group. |
| `untracked_summary` | Reported, not cleaned. |
| `modified_summary` | Reported, not reverted. |
| `unexpected_file_changes` | Explicit pass/fail field. |
| `no_reset` | true |
| `no_stash` | true |
| `no_clean` | true |
| `no_checkout` | true |

Closeout gate:

GO. Dirty-tree evidence is first-class and non-mutating.

## 11. Phase H7: Receipt Package Requirement

### Increment H7.1: Receipt Package

Objective:

Define required receipt package for PR-8.3 to unblock Plan I.

Allowed files:

Plan H docs and closeout.

Forbidden files/actions:

No run, no receipt fabrication, no browser proof, no Source Proxy proof, and no runtime writes.

Expected output:

Receipt package checklist.

Codex self-checks:

Confirm `receipt package`, `browser`, `terminal`, `manual`, and `NO-GO` appear.

Britton manual verification check:

Confirm receipts are sufficient for later gate review.

Stop condition:

Stop if receipts omit failures.

Rollback or recovery note:

Add failure fields.

Required PR-8.3 receipt package:

| Receipt | Required content | Current status |
| --- | --- | --- |
| Run 10 browser receipt | browser/manual state, copied diagnostic receipt, authority false fields, dirty tree before/after, Britton acceptance | missing |
| Run 25 browser receipt | Run 10 accepted first, copied diagnostic receipt, authority false fields, dirty tree before/after, Britton acceptance | missing |
| Run 100 browser receipt | Run 25 accepted first, copied diagnostic receipt, counts, blockers, unsafe/unexpected file status, dirty tree before/after, Britton acceptance | missing |
| real task gauntlet receipt | task scope, allowed files, diff preview, approval/apply/verify separation, task story/reconnect, dirty tree before/after, Britton acceptance | missing |
| terminal receipt | `git diff --check`, focused status, relevant tests or static checks when approved | missing |
| manual decision receipt | Britton explicit acceptance or explicit nonblocking decision | missing |

Closeout gate:

GO for checklist definition. Receipt package is currently missing and blocks Plan I.

## 12. Phase H8: Acceptance Decision Gate

### Increment H8.1: PR-8.3 Alignment Decision

Objective:

Decide whether PR-8.3 dependencies are satisfied or still block Plan I.

Allowed files:

Plan H closeout and optional `docs/plan-index.md` note.

Forbidden files/actions:

Standing forbidden set.

Expected output:

Acceptance dependency decision and next authorized title only.

Codex self-checks:

Run docs diff check, PR-8.3 grep, forbidden-claim grep, focused status, and em dash grep.

Britton manual verification check:

Confirm Plan H did not run PR-8.3.

Stop condition:

Stop if dependency acceptance lacks receipts.

Rollback or recovery note:

Leave Plan I NO-GO until PR-8.3 receipts exist.

Plan H GO/NO-GO decision gate:

NO-GO for Plan I. PR-8.3 dependencies are not accepted, no explicit nonblocking Britton decision record was supplied, and required receipts are missing. Plan I remains blocked until PR-8.3 accepted receipts exist or Britton explicitly records the dependency as nonblocking.

Next authorized title only:

Source Proxy PR-8.3 Acceptance Recovery: Fresh Run 10/25/100 And Real Coding Task Gauntlet Receipts

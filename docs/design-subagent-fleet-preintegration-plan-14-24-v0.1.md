# Design Agent Plan 14/24 Subagent Fleet Preintegration

Status: Closed advisory-only preintegration review
Plan: Plan 14/24, Design Subagent Fleet Preintegration
Mode: ADVISORY ONLY / MAC-AWARE
Date: 2026-05-27

## Scope

Plan 13/24 closed with GO for docs-first remediation status and blocker classification, while keeping remediation execution, Source Proxy proof execution, production CSS polish, merge implementation, final readiness, and Plan 14 start as NO-GO without explicit operator approval.

The operator then requested the next plan if all good. Plan 13 manual verification passed before this packet started.

This packet records Plan 14 only. It does not start Plan 15/24.

Allowed scope:

- Helper role map.
- Proposal packet contract.
- Integration gate.

Forbidden scope:

- Apply authority.
- Direct repo writes by subagents.
- Cart workflows.
- Hidden subagent workers.
- Runtime start, provider/model call, queue/worker execution, `/coding` edit, app UI edit, route edit, component edit, CSS edit, token edit, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy.

## Phase 14.1 Helper Role Map

### 14.1.1 Component Mapper Boundary

Allowed work:

- Define the Component Mapper helper boundary as advisory-only.
- Record evidence from existing design subagent docs.

Evidence:

- `docs/design-agent-design-system-a-grade-preflight-readiness-plan-c-subagent-a-grade-evidence-upgrade-v0.1.md` defines Component Mapper as mapping components without widening scope.
- Existing Plan C evidence states Component Mapper has no component edit or ownership assignment authority beyond advisory notes.

Boundary:

| Helper | Allowed output | Forbidden output | Status |
| --- | --- | --- | --- |
| Component Mapper | Advisory component map, ownership note, risk note, allowed-file suggestion source. | Component edit, ownership reassignment, protected-path relaxation, broad app scope. | `advisory_only` |

GO / NO-GO:

- GO for Component Mapper advisory boundary.
- NO-GO for direct repo writes, component edits, or widened allowed-file authority.

Next authorized increment: 14.1.2 Safety reviewer boundary.

### 14.1.2 Safety Reviewer Boundary

Allowed work:

- Define the Safety Reviewer helper boundary as advisory-only.
- Record fail-closed safety behavior.

Evidence:

- Plan C defines Safety Reviewer as blocking unsafe scope and authority drift.
- Safety Reviewer output is a safety decision, blocker list, residual risk, and handoff; it grants no approval, token, apply, execution, hidden work, or authority.

Boundary:

| Helper | Allowed output | Forbidden output | Status |
| --- | --- | --- | --- |
| Safety Reviewer | Safety decision, blocker list, residual risk, fail-closed recommendation. | Approval grant, token use, apply/execute-approved, hidden work, direct mutation. | `advisory_only` |

GO / NO-GO:

- GO for Safety Reviewer advisory boundary.
- NO-GO for approval authority, apply authority, or hidden work.

Next authorized increment: 14.1.3 Test scribe boundary.

### 14.1.3 Test Scribe Boundary

Allowed work:

- Define the Test Scribe helper boundary as advisory-only.
- Preserve not-run labels.

Evidence:

- Plan C defines Test Scribe as suggesting checks without running them.
- Existing Plan 14 of 21 smoke-test evidence keeps exact run mechanism, provider/model execution, queue/worker execution, `/coding` harness execution, and result review as `not_started`.

Boundary:

| Helper | Allowed output | Forbidden output | Status |
| --- | --- | --- | --- |
| Test Scribe | Check matrix, manual checks, future automated checks, not-run labels. | Test execution, browser start, screenshot capture, test edits, false passed claims. | `advisory_only` |

GO / NO-GO:

- GO for Test Scribe advisory boundary.
- NO-GO for test execution, browser proof, screenshot capture, or claims that checks passed.

Next authorized increment: 14.1.4 Mac-hosted advisory option.

### 14.1.4 Mac-Hosted Advisory Option

Allowed work:

- Define whether the Mac can host advisory helper work later.
- Preserve no-hidden-worker boundary.

Evidence:

- `docs/mac-mini-subagent-host-feasibility-plan-5-24-v0.1.md` closed GO for advisory subagent feasibility only and NO-GO for execution, hidden workers, app apply, and Cart workflows.
- `docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md` kept Mac remote worker controls observational/manual and NO-GO for restart/control implementation or worker execution.

Boundary:

| Host option | Allowed output | Forbidden output | Status |
| --- | --- | --- | --- |
| Mac-hosted helper advisory option | Future manual advisory packet generation or review support. | Hidden worker, autonomous execution, repo write, queue/worker execution, Cart workflow, apply. | `optional_advisory_only` |

GO / NO-GO:

- GO for Mac-hosted advisory option as a future manual possibility.
- NO-GO for hidden Mac workers, autonomous workers, repo writes, Cart workflows, or apply.

### Phase 14.1 Review

Completed increments:

- 14.1.1 GO for Component Mapper boundary; NO-GO for component edits or scope widening.
- 14.1.2 GO for Safety Reviewer boundary; NO-GO for approval/apply authority.
- 14.1.3 GO for Test Scribe boundary; NO-GO for test execution or false passed claims.
- 14.1.4 GO for Mac advisory option; NO-GO for hidden workers.

Evidence exists:

- Plan C subagent role evidence.
- Existing Design Agent Ecosystem Plan 14 of 21 smoke-test evidence.
- Mac Mini Plans 5 and 6 advisory/telemetry boundaries.

Forbidden scope avoided:

- No subagent was started.
- No Mac worker, runtime, provider/model, queue/worker, `/coding`, CSS, Source Proxy proof, apply, execute-approved, or git mutation occurred.

Checks:

- Read-only grep checks returned expected helper, subagent, no-apply, not_started, and NO-GO evidence.

Phase result: GO to Phase 14.2; NO-GO for helper execution.

Next authorized increment: 14.2.1 Define packet fields.

## Phase 14.2 Proposal Packet Contract

### 14.2.1 Define Packet Fields

Allowed work:

- Define required proposal packet fields for advisory display.

Required packet fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `packet_id` | yes | Stable packet identity. |
| `helper_role` | yes | Component Mapper, Safety Reviewer, Test Scribe, or approved helper label. |
| `source_context` | yes | Evidence/doc references used. |
| `proposal_summary` | yes | Advisory recommendation only. |
| `suggested_files` | yes | Advisory file list, not write authority. |
| `forbidden_actions` | yes | Explicit no apply, no execution, no git, no hidden worker list. |
| `checks_not_run` | yes | Checks that are suggested but not executed. |
| `evidence_gaps` | yes | Missing, unavailable, or not_started proof. |
| `source_proxy_handoff` | yes | Summary-only handoff, no apply authority. |
| `no_authority_statement` | yes | Packet is proposal evidence only. |

GO / NO-GO:

- GO for packet field contract.
- NO-GO for packet fields that imply direct write, apply, execution, or approval authority.

Next authorized increment: 14.2.2 Define scoring fields.

### 14.2.2 Define Scoring Fields

Allowed work:

- Define read-only scoring fields for packet display.

Required scoring fields:

| Field | Allowed values | Purpose |
| --- | --- | --- |
| `packet_status` | `ready`, `caution`, `blocked`, `not_started` | Display-only packet state. |
| `authority_status` | `clean`, `caution`, `blocked` | Whether wording preserves no-authority boundary. |
| `evidence_status` | `complete`, `partial`, `missing`, `not_started`, `unavailable` | Evidence honesty. |
| `display_eligibility` | `eligible_advisory_display`, `blocked` | Whether `/coding` may display the packet as inert evidence later. |
| `apply_eligibility` | `no_go` | Always no-go in Plan 14. |

GO / NO-GO:

- GO for read-only scoring fields.
- NO-GO for scoring that treats PASS, ready, or display eligibility as apply approval.

Next authorized increment: 14.2.3 Define blocked-reason fields.

### 14.2.3 Define Blocked-Reason Fields

Allowed work:

- Define blocked-reason fields for fail-closed packet handling.

Required blocked-reason fields:

| Field | Required reason type |
| --- | --- |
| `authority_blockers` | Apply, approval-token, provider/model, queue/worker, git, hidden autonomy, Cart workflow, direct repo write. |
| `scope_blockers` | Protected path, broad app scope, unrelated lane, dirty-tree confusion, CSS/app edit in docs-only lane. |
| `evidence_blockers` | Missing source, missing visual proof, checks not run, false passed claim, fake screenshot, unavailable proof hidden. |
| `integration_blockers` | Source Proxy bypass, direct `/coding` mutation, display treated as write authority. |
| `host_blockers` | Mac hidden worker, autonomous worker, unapproved remote execution. |

GO / NO-GO:

- GO for blocked-reason field contract.
- NO-GO for packets that hide blockers or soften blocked status.

### Phase 14.2 Review

Completed increments:

- 14.2.1 GO for packet fields; NO-GO for direct write/apply authority.
- 14.2.2 GO for scoring fields; NO-GO for PASS-as-apply.
- 14.2.3 GO for blocked-reason fields; NO-GO for hidden blockers.

Evidence exists:

- Proposal packet contract fields are recorded.
- Scoring fields are recorded.
- Blocked-reason fields are recorded.

Forbidden scope avoided:

- No packet was executed.
- No `/coding` display implementation, Source Proxy integration, provider/model call, queue/worker execution, app/CSS edit, apply, execute-approved, or git mutation occurred.

Checks:

- Packet schema and no-apply grep checks are available in the terminal verification section.

Phase result: GO to Phase 14.3; NO-GO for packet execution or apply.

Next authorized increment: 14.3.1 Confirm no apply authority.

## Phase 14.3 Integration Gate

### 14.3.1 Confirm No Apply Authority

Allowed work:

- Confirm advisory packets grant no apply authority.

Evidence:

- `docs/source-proxy-design-apply-lane-v0.1.md` records that design packs are not write authority and must not apply changes.
- The same doc records that design-pack approval is not the same thing as apply approval.
- Existing Plan 14 of 21 smoke-test evidence blocks treating a valid packet as approval to code or calling Source Proxy apply from a design packet.

Decision:

- Advisory subagent packets have no apply authority.
- `apply_eligibility` remains `no_go`.

GO / NO-GO:

- GO for no-apply confirmation.
- NO-GO for apply, execute-approved, approval-token action, or treating packet display as apply approval.

Next authorized increment: 14.3.2 Confirm Source Proxy remains write gate.

### 14.3.2 Confirm Source Proxy Remains Write Gate

Allowed work:

- Confirm Source Proxy remains the only app-write gate.

Evidence:

- `docs/source-proxy-design-apply-lane-v0.1.md` records: "The only app-write lane remains Source Proxy with explicit approval."
- It also records Source Proxy behavior remains unchanged.
- Plan 11 kept staged multi-lane execution NO-GO and listed missing production proof.

Decision:

- Source Proxy remains the write gate.
- Subagent packets are proposal evidence only.
- No Source Proxy route, runtime, apply lane, or `/coding` mutation is authorized by Plan 14.

GO / NO-GO:

- GO for Source Proxy write-gate confirmation.
- NO-GO for Source Proxy bypass, direct repo write, direct `/coding` mutation, or hidden worker write.

Next authorized increment: 14.3.3 Decide whether subagent packets can display in /coding.

### 14.3.3 Decide Whether Subagent Packets Can Display In /coding

Allowed work:

- Decide display eligibility only.
- Do not implement display.

Display eligibility decision:

| Packet type | Display eligibility | Conditions |
| --- | --- | --- |
| Component Mapper advisory packet | `eligible_advisory_display` | Includes no-authority statement, blockers, suggested files as advisory only, checks_not_run, and no apply eligibility. |
| Safety Reviewer advisory packet | `eligible_advisory_display` | Includes fail-closed blocker list, residual risk, and no approval/apply authority. |
| Test Scribe advisory packet | `eligible_advisory_display` | Includes check matrix with not-run labels and no test execution claim. |
| Mac-hosted advisory packet | `eligible_advisory_display` | Only if manually produced and explicitly not a hidden worker or remote execution result. |

Decision:

- Subagent packets can be eligible for future `/coding` display as inert advisory evidence only.
- Display implementation is not authorized.
- Display does not equal apply, approval, Source Proxy proof, prompt execution, runtime readiness, daily-use readiness, or CSS polish readiness.

GO / NO-GO:

- GO for advisory packet display eligibility decision.
- NO-GO for `/coding` implementation, Source Proxy integration, apply, runtime execution, or hidden workers.

### Phase 14.3 Review

Completed increments:

- 14.3.1 GO for no-apply confirmation; NO-GO for apply or execute-approved.
- 14.3.2 GO for Source Proxy write-gate confirmation; NO-GO for bypass.
- 14.3.3 GO for advisory display eligibility decision; NO-GO for implementation.

Evidence exists:

- Source Proxy design apply lane evidence.
- Existing smoke-test packet trap evidence.
- Plan 14 packet schema and display eligibility table.

Forbidden scope avoided:

- No apply authority, direct repo writes, Cart workflows, hidden subagent workers, Source Proxy implementation, `/coding` implementation, provider/model call, queue/worker execution, app/CSS edit, approval-token action, execute-approved, or git mutation occurred.

Checks:

- Packet schema and no-apply grep checks are available in the terminal verification section.

Phase result: GO to Plan 14 closeout; NO-GO for Plan 15 start.

Next authorized increment: Plan 14/24 closeout.

## Plan 14/24 Closeout

Phase review:

- Phase 14.1 Helper Role Map: GO for advisory helper boundaries; NO-GO for helper execution.
- Phase 14.2 Proposal Packet Contract: GO for packet, scoring, and blocker fields; NO-GO for packet execution or apply.
- Phase 14.3 Integration Gate: GO for no-apply, Source Proxy write gate, and advisory display eligibility; NO-GO for implementation.

Increment review:

- 14.1.1 Component Mapper boundary: `advisory_only`.
- 14.1.2 Safety Reviewer boundary: `advisory_only`.
- 14.1.3 Test Scribe boundary: `advisory_only`.
- 14.1.4 Mac-hosted advisory option: `optional_advisory_only`.
- 14.2.1 Packet fields: defined.
- 14.2.2 Scoring fields: defined.
- 14.2.3 Blocked-reason fields: defined.
- 14.3.1 No apply authority: confirmed.
- 14.3.2 Source Proxy write gate: confirmed.
- 14.3.3 `/coding` display eligibility: `eligible_advisory_display` only.

Evidence exists:

- Helper role map.
- Proposal packet contract.
- Packet schema.
- No-apply grep evidence.
- Display eligibility decision.

Forbidden actions did not occur:

- No apply authority.
- No direct repo writes by subagents.
- No Cart workflows.
- No hidden subagent workers.
- No runtime, provider/model, queue/worker, approval-token, apply, execute-approved, `/coding`, app UI, route, component, CSS, token, commit, push, branch, worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy.

Final display eligibility decision:

- Subagent packets are eligible for future `/coding` display only as inert advisory evidence.
- Display implementation is not authorized.
- Source Proxy remains the only app-write gate with explicit approval.

Final Plan 14/24 result: GO for advisory subagent fleet preintegration and future inert packet display eligibility; NO-GO for apply authority, direct repo writes, hidden workers, Cart workflows, `/coding` implementation, Source Proxy implementation, CSS edits, prompt execution, provider/model calls, queue/worker execution, or Plan 15 start without explicit operator approval.

Next roadmap plan only: `Plan 15/24: Scout Manual-Controlled Intelligence Lane`.

## Terminal Verification

Run from `/home/source/SpiritOS`:

```bash
cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal && grep -nE "Plan 14/24|Component Mapper|Safety Reviewer|Test Scribe|Mac-hosted|packet_id|helper_role|scoring fields|blocked-reason|no apply authority|Source Proxy remains the write gate|eligible_advisory_display|NO-GO|Plan 15/24" docs/design-subagent-fleet-preintegration-plan-14-24-v0.1.md && grep -nE "design packs are not write authority|must not apply|design-pack approval is not the same thing as apply approval|only app-write lane remains Source Proxy|Source Proxy behavior remains unchanged|valid packet as approval to code|Call Source Proxy apply|no prompt-run authority|no CSS edits|NO-GO" docs/source-proxy-design-apply-lane-v0.1.md docs/design-agent-ecosystem-plan-14-10-prompt-design-packet-smoke-test-v0.1.md docs/design-agent-ecosystem-plan-14-closeout-v0.1.md && git diff --check -- docs/design-subagent-fleet-preintegration-plan-14-24-v0.1.md
```

Expected output:

- Git status shows this Plan 14 packet as untracked with prior roadmap docs still untracked.
- Plan 14 grep prints helper roles, packet schema fields, blocked-reason fields, no-apply gate, Source Proxy write gate, display eligibility, NO-GO boundaries, and Plan 15 title.
- Source grep prints design-pack no-write/no-apply boundaries, Source Proxy write-gate evidence, packet/apply traps, no prompt-run authority, no CSS edits, and NO-GO lines.
- `git diff --check` prints no output.

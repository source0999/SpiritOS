# Agent Factory Roadmap v0.1

## Authority Statement

This roadmap is planning-only. It does not implement agents, runtime helpers, command execution, workflow execution, source writes, commits, pushes, branches, worktrees, self-approval, or background autonomy.

This document defines the future Agent Factory plan sequence. It does not start Plan 1 or any later plan.

Correction:

Plan 1 Phase 1 docs-only contracts and operating rules were written during planning-package consolidation in `docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md`. They remain docs-only and do not authorize runtime helpers, source edits, implementation, or Plan 2. The first real new-chat target must review and ratify that existing Plan 1 Phase 1 content before proceeding to any next valid Plan 1 phase.

## Goal

Make future agents easier to create by standardizing scaffolds, context packets, authority audits, reviews, tests, receipts, handoffs, lane boundaries, dependency gates, and worker coordination rules.

Global rule:

Agent thinks and prepares. Proxy applies. Cartographer records and organizes. Human approves authority crossings.

## Current Repo Posture

- Source Proxy is the future coding cockpit. It must prove plain-English task intake, scoping, diff preview, exact approval, apply, verify, receipt, provider truth, and UI polish in that order.
- Cartographer has live-state, approval-token, safe-write, and verification-runner work in progress, but future Agent Factory helpers must treat each capability as unavailable until its specific proof and closeout are accepted.
- Design Agent, Scout polish, Oracle polish, Chat helper polish, and future worker agents must inherit Source Proxy and Cartographer authority models. They must not create separate authority systems.

## Safe Timing Map

| Timing | Plans | Rule |
| --- | --- | --- |
| Can run now in parallel with Proxy and Cartographer | Plan 1 | Docs-only contracts and operating rules. No runtime helpers. |
| Wait until Source Proxy apply/verify is stable | Plan 2 | Proposal helpers for Tester, Reviewer, Receipt Scribe, and Handoff Scribe. |
| Wait until Cartographer live state and approval-token consumption are stable | Plan 3 | Read-only context, lane, and authority helpers. |
| Wait until Cartographer safe writes and verification runner are stable | Plan 4 and Plan 6 | Dry-run safe-write-adjacent helpers and Agent Scaffolder proposal-only runtime. |
| Wait until Cartographer workflow queue and worker coordination are stable | Plan 5 | Worker registry, leases, closeout, and one-worker-one-task proof. |
| Wait until Proxy and Cartographer are daily-driver stable | Plan 7 and Plan 8 | Design Agent stack, Scout intake polish, Oracle honesty, and Chat helper polish. |
| Wait until trust-tier review after daily-driver proof | Plan 9 | Multi-agent orchestration, controlled branch/worktree proposals, release steward, and broader autonomy planning. |

## Timeline

| Dependency gate | Realistic timing after gate | Output |
| --- | --- | --- |
| Now | 0.5 to 1 day | Planning package and Plan 1 handoff readiness. |
| Source Proxy apply/verify stable | 2 to 5 days | Proposal-helper contracts and bounded proposal helpers. |
| Cartographer live state and approval-token consumption stable | 3 to 7 days | Read-only context and lane helpers. |
| Cartographer safe writes and verification runner stable | 1 to 2 weeks | Safe-write-dependent dry-runs and Agent Scaffolder proposal-only runtime. |
| Cartographer workflow queue and worker coordination stable | 1 to 3 weeks | Worker coordination helpers. |
| Daily-driver Proxy and Cartographer stable | Scope-dependent | Design, Scout, Oracle, and Chat helper polish accelerates. |

These are dependency-gated estimates, not calendar promises.

## Plan Gate Summary

| Plan | start gate | dependency gate | phases | increments | parallel | wait until Proxy | wait until Cartographer | allowed lane | forbidden lane | handoff target |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Plan 1 | Planning package accepted; existing Plan 1 Phase 1 docs reviewed and ratified in a new chat. | Can run now as docs-only work. | Phase 1.1 contracts; Phase 1.2 operating rules. | 1.1.1 through 1.1.7; 1.2.1 through 1.2.4. | Can run in parallel with Proxy and Cartographer because it is docs-only. | No Proxy gate for Plan 1 docs-only work. | No Cartographer gate for Plan 1 docs-only work. | `docs/agent-factory-*` only. | Runtime, source, tests, package/config/env, commits, pushes, branches, worktrees, stash/reset/clean. | Agent Factory Plan 1 new chat reviews and ratifies existing Phase 1 docs, then stops or proceeds only to the next valid Plan 1 phase if approved. |
| Plan 2 | Britton explicitly approves Plan 2 after Plan 1 acceptance. | Source Proxy apply/verify stable. | Phase 2.1 Tester; Phase 2.2 Reviewer; Phase 2.3 Receipt/Handoff proposal helpers. | 2.1.1 through 2.3.3. | Must not run in parallel with unfinished Proxy apply/verify proof. | wait until Proxy proves exact approval, apply, separate verify, receipt, and provider truth. | Cartographer proof helps receipts but is not the primary Plan 2 gate. | Exact approved Plan 2 files only. | Runtime helper writes, unapproved tests, provider calls, apply bypass, commits, pushes, branches, worktrees. | Agent Factory Plan 2 Phase 1 after Proxy apply/verify proof. |
| Plan 3 | Britton explicitly approves Plan 3 after Plan 2 gate decision. | Cartographer live state and approval-token consumption stable. | Phase 3.1 Context Pack Builder; Phase 3.2 Lane Guard; Phase 3.3 Authority Auditor runtime checks. | 3.1.1 through 3.3.3. | Must wait for Cartographer read-only gates. | Proxy intake calls remain forbidden. | wait until Cartographer can report live state and validate/consume approval boundaries without granting writes. | Exact approved Plan 3 files only. | Safe writes, workflow execution, queue execution, command execution, commits, pushes, branches, worktrees, stash/reset/clean. | Agent Factory Plan 3 Phase 1 after Cartographer read-only gates. |
| Plan 4 | Britton explicitly approves Plan 4 after Cartographer safe-write proof. | Cartographer safe writes and verification runner stable. | Phase 4.1 Safe-Write Envelope Planner; Phase 4.2 Verification Evidence Planner. | 4.1.1 through 4.2.3. | Must wait for Cartographer safe-write and verification proof. | Proxy apply remains separate and cannot be bypassed. | wait until Cartographer safe writes and verification runner are stable. | Exact approved Plan 4 files only. | Direct apply, unapproved command execution, commits, pushes, branches, worktrees, queue execution, hidden workers, self-approval. | Agent Factory Plan 4 Phase 1 after safe-write and verification-runner proof. |
| Plan 5 | Britton explicitly approves Plan 5 after worker coordination proof. | Cartographer workflow queue and worker coordination stable. | Phase 5.1 Worker Registry; Phase 5.2 Leases and Stale Closeout. | 5.1.1 through 5.2.3. | Must wait for queue and worker coordination gates. | Proxy remains the apply boundary for source changes. | wait until Cartographer workflow queue and worker coordination are stable. | Exact approved Plan 5 files only. | Hidden workers, unlabeled approvals, overlapping write lanes, commits, pushes, branches, worktrees, self-approval, background autonomy. | Agent Factory Plan 5 Phase 1 after workflow queue and worker coordination proof. |
| Plan 6 | Britton explicitly approves Plan 6 after Plans 1, 4, and worker policy gates. | Cartographer safe writes, verification runner, and enough worker coordination policy stable. | Phase 6.1 Scaffold Proposal Model. | 6.1.1 through 6.1.3. | Must wait for safe-write and worker policy gates. | Proxy still applies; scaffolder only proposes. | wait until Cartographer safe-write/verification boundaries exist for scaffold proposals. | Exact approved Plan 6 files only. | Direct source writes, package installs, runtime lane mutation, branches, worktrees, commits, pushes, self-approval. | Agent Factory Plan 6 Phase 1 after safe-write and worker policy gates. |
| Plan 7 | Britton explicitly approves Plan 7 after daily-driver Proxy/Cart proof. | Proxy and Cartographer daily-driver stable enough for design proposals and records. | Phase 7.1 Design Source Rights Gate; Phase 7.2 Visual Verification Planner. | 7.1.1 through 7.2.2. | Must wait for daily-driver proof. | wait until Proxy can safely handle design apply lanes. | wait until Cartographer can record design decisions/evidence. | Exact approved Plan 7 files only. | Direct UI apply, scraping, copying protected sources, package installs, Visual Verifier approval authority. | Agent Factory Plan 7 Phase 1 after daily-driver Proxy/Cart proof. |
| Plan 8 | Britton explicitly approves Plan 8 after product-helper polish gate. | Proxy and Cartographer daily-driver stable; Scout remains manual-gated; Oracle/Chat honesty boundaries exist. | Phase 8.1 Scout Intake Curator; Phase 8.2 Oracle and Chat Tool-Honesty Review. | 8.1.1 through 8.2.2. | Must wait for product-helper polish approval. | wait until Proxy boundaries are stable enough for advisory packets. | wait until Cartographer can keep records without hidden authority. | Exact approved Plan 8 files only. | Scout auto-promotion, coding context writes, Oracle command execution, chat-triggered apply, provider/auth/env changes. | Agent Factory Plan 8 Phase 1 after product-helper polish gate. |
| Plan 9 | Britton explicitly approves Plan 9 after trust-tier review. | Daily-driver Proxy/Cart, product helpers, worker coordination, and trust-tier review. | Phase 9.1 Orchestration Proposal; Phase 9.2 Future Authority Proposals. | 9.1.1 through 9.2.3. | Must wait for all prior trust-tier gates. | wait until Proxy is trusted for controlled apply boundaries. | wait until Cartographer is trusted for orchestration records and worker coordination. | Exact approved Plan 9 files only. | Unbounded autonomy, hidden background workers, branch/worktree mutation, release action, commits, pushes, external calls without trust-tier approval. | Agent Factory Plan 9 Phase 1 after trust-tier approval. |

## Sub-Agent Inventory

| Sub-agent | Purpose | First safe mode | Earliest plan | Blocked until | Future runtime authority | Forbidden authority |
| --- | --- | --- | --- | --- | --- | --- |
| Agent Scaffolder | Draft new agent file sets, prompts, tests, docs, and checks from approved contracts. | Docs-only contract | Plan 1 | Plan 6 waits for safe writes and verification runner | Proposal-only scaffolds | Apply, commit, push, branch, worktree, self-approval |
| Authority Auditor | Detect approval, apply, write, command, provider, and autonomy drift. | Docs-only contract | Plan 1 | Runtime checks wait for Plan 3 | Read-only authority report | Granting authority or overriding human gates |
| Context Pack Builder | Assemble scoped docs, files, checks, and dirty-state notes. | Docs-only schema | Plan 1 | Runtime waits for Plan 3 | Read-only packet builder | Active context writes or proxy intake calls |
| Receipt Scribe | Standardize receipts for work, checks, blockers, and next permission. | Docs-only contract | Plan 1 | Runtime waits for Plan 2 | Receipt draft helper | Treating receipt as approval or verification |
| Handoff Scribe | Standardize new-chat handoffs and stop rules. | Docs-only contract | Plan 1 | Runtime waits for Plan 2 | Handoff draft helper | Starting next phase or inferring permission |
| Tester Agent | Propose focused tests and verification commands. | Proposal-only contract | Plan 2 | Source Proxy apply/verify stable | Proposal-only test planning | Installing packages or editing tests without approval |
| Reviewer Agent | Critique diffs, scope, regressions, and missing checks. | Proposal-only contract | Plan 2 | Source Proxy apply/verify stable | Review report | Editing files or approving apply |
| Prompt Pattern Librarian | Store safe prompt shapes and forbidden authority wording. | Docs-only contract | Plan 1 | Runtime lookup waits for later approval | Read-only pattern lookup | Runtime prompt injection or provider routing |
| Lane Guard | Check allowed files, forbidden files, dirty-state separation, and overlap. | Docs-only contract | Plan 1 | Runtime waits for Plan 3 | Read-only lane report | Cleanup, stash, reset, file mutation |
| Worker Registry | Track worker roles, labels, ownership, and state. | Dry-run plan | Plan 5 | Workflow queue and worker coordination stable | Bounded registry after approval | Hidden workers or unlabeled approvals |
| Ownership Lock Planner | Plan one-worker-one-task ownership and file family boundaries. | Dry-run plan | Plan 5 | Worker coordination stable | Dry-run lock proposal | Enforced locks without policy |
| Design Source Rights Gate | Check design source-card rights and approved use mode. | Docs-only contract | Plan 7 | Design Agent stack gate | Read-only source rights check | Scraping, copying protected sources, approving licenses |
| Visual Verification Planner | Define screenshots, viewport checks, and evidence. | Docs-only plan | Plan 7 | Visual verification gate | Proposal-only visual checks | Installing tooling or approving visual changes |
| Scout Intake Curator | Convert Scout candidates into advisory packets. | Docs-only contract | Plan 8 | Scout manual-gated intake | Read-only advisory packets | Auto-promotion or coding context writes |
| Oracle Tool-Honesty Reviewer | Review Oracle, Chat, and helper UI claims for honest tool state. | Docs-only checklist | Plan 8 | Oracle/Chat polish gate | Read-only honesty review | Executing commands or granting UI authority |

## Plan Sequence

### Plan 1: Agent Factory Contracts and Operating Rules

When it starts:
- Can start now in parallel with Proxy and Cartographer.

What must already be true:
- Planning package is accepted.
- Allowed files are named before editing.

Why it helps:
- Gives every later agent a shared authority contract before runtime exists.

What it must not touch:
- No `source_proxy/**`, `src/**`, `scout/**`, tests, package/config/env, active Proxy docs, active Cartographer docs, commits, pushes, branches, worktrees, stash, reset, or clean.

Manual check style:
- Codex runs short docs-only checks: status, diff check for Agent Factory docs, and greps for required contract names and forbidden authority.
- Britton gets a short spot-check summary, not a huge terminal block.

Handoff target:
- Agent Factory Plan 1 Phase 1 can start in a new chat.

#### Phase 1.1: Contract Source Of Truth

Entry criteria:
- Britton approves Plan 1 Phase 1 in a new chat.

Exit criteria:
- Contract doc names Authority Auditor, Receipt Scribe, Handoff Scribe, Prompt Pattern Librarian, and Lane Guard.

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1.1: Baseline and allowed files | Capture dirty state and name exact docs-only lane. | `docs/agent-factory-*` docs only. | Runtime, tests, cleanup, stash, reset. | Baseline note and active allowed files. | `git status --branch --short`; `git diff --check -- docs/agent-factory-*.md`. | Unexpected lane-caused dirty file. | 1.1.2: Authority Auditor contract. |
| 1.1.2: Authority Auditor contract | Define authority drift checks. | Agent Factory contract docs. | Runtime registry edits, Source Proxy edits. | Authority Auditor contract. | Grep for `Authority Auditor`, `approval`, `apply`, `self-approval`. | Contract grants authority. | 1.1.3: Receipt Scribe contract. |
| 1.1.3: Receipt Scribe contract | Define receipt fields and evidence rules. | Agent Factory contract docs. | Receipt runtime writes, commit, push. | Receipt Scribe contract. | Grep for `Receipt Scribe`, `files changed`, `checks run`. | Receipt equals approval. | 1.1.4: Handoff Scribe contract. |
| 1.1.4: Handoff Scribe contract | Define new-chat handoff shape. | Agent Factory contract docs. | Starting next phase automatically. | Handoff Scribe contract. | Grep for `Handoff Scribe`, `allowed files`, `stop conditions`. | Handoff infers permission. | 1.1.5: Prompt Pattern Librarian contract. |
| 1.1.5: Prompt Pattern Librarian contract | Define safe prompt patterns and forbidden authority wording. | Agent Factory contract docs. | Runtime prompt injection, provider routing. | Pattern Librarian contract. | Grep for `Prompt Pattern Librarian`, `docs-only`, `proposal-only`. | Template loosens boundaries. | 1.1.6: Lane Guard contract. |
| 1.1.6: Lane Guard contract | Define dirty-state and file-family overlap rules. | Agent Factory contract docs. | Cleanup, stash, reset, file mutation. | Lane Guard contract. | Grep for `Lane Guard`, `dirty worktree`, `overlap`. | Contract claims ownership of unrelated dirty files. | 1.1.7: Plan 1 closeout. |
| 1.1.7: Plan 1 closeout | Confirm Plan 1 remains docs-only. | Agent Factory contract docs. | Runtime, tests, implementation. | Short closeout summary. | `git diff --check -- docs/agent-factory-*.md`; required greps. | Any authority grant or unexpected file. | Plan 2, later gate. |

#### Phase 1.2: Operating Rules Packet

Entry criteria:
- Phase 1.1 contracts exist.

Exit criteria:
- Operating rules define allowed files, forbidden actions, stop conditions, and short planning-check style.

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.2.1: Dirty worktree rule | Define user-owned dirty-state handling. | Agent Factory docs. | Cleanup or attribution of unrelated work. | Dirty worktree rule. | Grep for `Pre-existing dirty files are user-owned`. | Rule allows cleanup. | 1.2.2: One lane rule. |
| 1.2.2: One lane rule | Define no overlapping file-family work. | Agent Factory docs. | Runtime locks. | One-lane planning rule. | Grep for `No two runtime lanes`. | Rule blocks user work without approval. | 1.2.3: Authority crossing rule. |
| 1.2.3: Authority crossing rule | Define human approval crossings. | Agent Factory docs. | Self-approval. | Authority crossing rule. | Grep for `Human approves`. | Rule grants authority. | 1.2.4: Plan 1 handoff readiness. |
| 1.2.4: Plan 1 handoff readiness | Mark Plan 1 ready for new-chat execution. | Agent Factory docs. | Writing handoff prompt unless asked. | Ready statement only. | Grep for `Plan 1 Phase 1 can start`. | Handoff prompt is written without request. | Stop. |

### Plan 2: Proxy-Dependent Proposal Helpers

When it starts:
- After Source Proxy apply/verify is stable.

What must already be true:
- Source Proxy proves exact approval, apply, separate verify, receipt, and provider truth.

Why it helps:
- Lets Tester, Reviewer, Receipt Scribe, and Handoff Scribe help future coding work without bypassing Proxy.

What it must not touch:
- No unapproved tests, runtime helper writes, package/config/env changes, provider calls, apply bypass, commit, push, branch, or worktree.

Manual check style:
- Codex runs exact focused Proxy helper checks named by the approved Plan 2 prompt.

Handoff target:
- Agent Factory Plan 2 Phase 1 after Proxy apply/verify proof.

#### Phase 2.1: Tester Agent Proposal Helper

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.1.1: Tester proposal contract | Define test proposal shape. | Exact approved Plan 2 files. | Editing tests or installing packages. | Tester proposal contract. | Grep for `proposal-only` and `no test writes`. | Tester can mutate tests. | 2.1.2: Verification command proposal. |
| 2.1.2: Verification command proposal | Define allowed verification suggestions. | Exact approved Plan 2 files. | Command execution authority. | Command proposal format. | Grep for `suggested`, `not executed`. | Proposal executes commands. | 2.1.3: Tester closeout. |
| 2.1.3: Tester closeout | Confirm proposal-only status. | Exact approved Plan 2 files. | Runtime apply or approval. | Short closeout. | Diff check and focused grep. | Tester grants authority. | Phase 2.2. |

#### Phase 2.2: Reviewer Agent Proposal Helper

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.2.1: Reviewer report shape | Define findings, risk, and blocker format. | Exact approved Plan 2 files. | Editing files, approving apply. | Review report contract. | Grep for `Reviewer`, `cannot approve`. | Reviewer approves. | 2.2.2: Scope review rules. |
| 2.2.2: Scope review rules | Define allowed-files and regression checks. | Exact approved Plan 2 files. | Broad source edits. | Scope review checklist. | Focused grep. | Scope review mutates files. | 2.2.3: Reviewer closeout. |
| 2.2.3: Reviewer closeout | Confirm proposal-only status. | Exact approved Plan 2 files. | Runtime approval. | Short closeout. | Diff check and grep. | Reviewer grants authority. | Phase 2.3. |

#### Phase 2.3: Receipt and Handoff Proposal Helpers

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.3.1: Receipt proposal helper | Draft receipts from verified Proxy data. | Exact approved Plan 2 files. | Treating receipt as approval. | Receipt draft helper. | Focused Proxy receipt check. | Receipt claims unrun verification. | 2.3.2: Handoff proposal helper. |
| 2.3.2: Handoff proposal helper | Draft handoffs without starting next phase. | Exact approved Plan 2 files. | Inferring permission. | Handoff draft helper. | Grep for `Never infer permission`. | Handoff starts work. | 2.3.3: Plan 2 closeout. |
| 2.3.3: Plan 2 closeout | Confirm all helpers remain proposal-only. | Exact approved Plan 2 files. | Runtime authority expansion. | Short closeout. | Exact tests plus diff check. | Any helper bypasses Proxy. | Plan 3 gate. |

### Plan 3: Cartographer Read-Only Context and Lane Helpers

When it starts:
- After Cartographer live state and approval-token consumption boundary are stable.

What must already be true:
- Cartographer can report live state and validate/consume approval boundaries without granting writes.

Why it helps:
- Gives future chats scoped context, lane risk, and authority checks without mutation.

What it must not touch:
- No safe writes, workflow execution, queue execution, command execution, commit, push, branch, worktree, stash, reset, cleanup, or self-approval.

Manual check style:
- Codex runs read-only helper tests and diff checks.

Handoff target:
- Agent Factory Plan 3 Phase 1 after Cartographer read-only gates.

#### Phase 3.1: Context Pack Builder Read-Only

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.1.1: Packet schema | Define read-only context packet fields. | Exact approved Plan 3 files. | Active context writes. | Packet schema. | Schema grep. | Schema writes active context. | 3.1.2: Dirty-state attachment. |
| 3.1.2: Dirty-state attachment | Attach status as evidence only. | Exact approved Plan 3 files. | Cleanup or normalization. | Dirty-state packet section. | Fixture or docs check. | Helper mutates status. | 3.1.3: Context closeout. |
| 3.1.3: Context closeout | Confirm read-only behavior. | Exact approved Plan 3 files. | Proxy intake calls. | Short closeout. | Read-only tests. | Packet calls Proxy intake. | Phase 3.2. |

#### Phase 3.2: Lane Guard Read-Only

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.2.1: Allowed-file check | Compare approved lane against status. | Exact approved Plan 3 files. | File edits. | Lane risk report. | Dirty fixture check. | Guard mutates files. | 3.2.2: Overlap check. |
| 3.2.2: Overlap check | Detect same file family conflicts. | Exact approved Plan 3 files. | Runtime locks. | Overlap report. | Conflict fixture check. | Guard enforces locks. | 3.2.3: Lane closeout. |
| 3.2.3: Lane closeout | Confirm read-only lane guard. | Exact approved Plan 3 files. | Cleanup, stash, reset. | Short closeout. | Diff check and tests. | Guard cleans worktree. | Phase 3.3. |

#### Phase 3.3: Authority Auditor Read-Only Runtime Checks

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.3.1: Authority claim parser | Read helper outputs for authority claims. | Exact approved Plan 3 files. | Granting authority. | Authority report. | Parser test. | Parser changes authority. | 3.3.2: Drift findings. |
| 3.3.2: Drift findings | Emit fail-closed findings. | Exact approved Plan 3 files. | Approval tokens or apply. | Drift finding report. | Drift fixture test. | Findings unlock action. | 3.3.3: Plan 3 closeout. |
| 3.3.3: Plan 3 closeout | Confirm all helpers are read-only. | Exact approved Plan 3 files. | Mutation. | Short closeout. | Read-only tests and diff check. | Any helper writes. | Plan 4 gate. |

### Plan 4: Safe-Write and Verification Dependent Helpers

When it starts:
- After Cartographer safe writes and verification runner are stable.

What must already be true:
- Safe write class is bounded, approval-token consumption is proven, rollback expectations exist, and verification runner is exact-argv and bounded.

Why it helps:
- Lets future helpers reason about safe-write envelopes without becoming apply engines.

What it must not touch:
- No direct apply outside approved safe-write service, no unapproved command execution, no commit, push, branch, worktree, queue execution, hidden workers, or self-approval.

Manual check style:
- Codex runs exact safe-write and verification-runner tests named by the approved Plan 4 prompt.

Handoff target:
- Agent Factory Plan 4 Phase 1 after safe-write and verification-runner proof.

#### Phase 4.1: Safe-Write Envelope Planner

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.1.1: Envelope fields | Define approved-file, rollback, and verification fields. | Exact approved Plan 4 files. | Writing source files. | Envelope schema. | Schema tests or grep. | Envelope implies apply. | 4.1.2: Negative cases. |
| 4.1.2: Negative cases | Define stale, broad, protected, and dirty blockers. | Exact approved Plan 4 files. | Runtime writes. | Negative-case matrix. | Negative-case tests. | Unsafe case passes. | 4.1.3: Envelope closeout. |
| 4.1.3: Envelope closeout | Confirm planner only plans. | Exact approved Plan 4 files. | Apply authority. | Short closeout. | Diff check and tests. | Planner applies. | Phase 4.2. |

#### Phase 4.2: Verification Evidence Planner

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.2.1: Exact command evidence | Define command, argv, output, and exit-code evidence. | Exact approved Plan 4 files. | Broad shell execution. | Verification evidence contract. | Grep for `exact argv`. | Shell expansion allowed. | 4.2.2: Failure receipt. |
| 4.2.2: Failure receipt | Define failed verification receipts. | Exact approved Plan 4 files. | Auto-retry loops. | Failure receipt shape. | Receipt grep. | Failure triggers autonomy. | 4.2.3: Plan 4 closeout. |
| 4.2.3: Plan 4 closeout | Confirm no write authority granted. | Exact approved Plan 4 files. | Safe-write bypass. | Short closeout. | Exact tests and diff check. | Helper bypasses Cartographer. | Plan 5 or Plan 6 gate. |

### Plan 5: Workflow Queue and Worker Coordination Helpers

When it starts:
- After Cartographer workflow queue and worker coordination are stable.

What must already be true:
- Durable workflow queue, worker labels, stale worker closeout, and one-worker-one-task policy are proven.

Why it helps:
- Makes future multi-worker work bounded, labeled, stoppable, and auditable.

What it must not touch:
- No hidden workers, unlabeled approvals, overlapping write lanes, commit, push, branch, worktree, self-approval, or background autonomy.

Manual check style:
- Codex runs exact queue, lease, stale closeout, and worker conflict tests.

Handoff target:
- Agent Factory Plan 5 Phase 1 after workflow queue and worker coordination proof.

#### Phase 5.1: Worker Registry

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5.1.1: Worker entry schema | Define worker role, task, lane, and state fields. | Exact approved Plan 5 files. | Starting workers. | Registry schema. | Registry schema test. | Registry starts work. | 5.1.2: Worker labels. |
| 5.1.2: Worker labels | Require source task/thread and exact scope. | Exact approved Plan 5 files. | Unlabeled approval. | Label contract. | Label tests. | Unlabeled worker allowed. | 5.1.3: Registry closeout. |
| 5.1.3: Registry closeout | Confirm registry is bounded. | Exact approved Plan 5 files. | Hidden background work. | Short closeout. | Queue/registry tests. | Hidden worker exists. | Phase 5.2. |

#### Phase 5.2: Leases and Stale Closeout

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5.2.1: Worker lease | Define one-worker-one-task lease. | Exact approved Plan 5 files. | Broad locks. | Lease contract. | Lease conflict tests. | Lease overlaps file family. | 5.2.2: Stale closeout. |
| 5.2.2: Stale closeout | Define stale worker report. | Exact approved Plan 5 files. | Killing processes, cleanup. | Stale closeout report. | Stale fixture tests. | Closeout mutates repo. | 5.2.3: Plan 5 closeout. |
| 5.2.3: Plan 5 closeout | Confirm worker coordination is bounded. | Exact approved Plan 5 files. | Queue bypass. | Short closeout. | Worker coordination tests. | Queue executes unapproved work. | Plan 6 gate. |

### Plan 6: Agent Scaffolder Proposal-Only Runtime

When it starts:
- After safe writes, verification runner, and enough worker coordination policy are stable.

What must already be true:
- Plan 1 contracts exist.
- Plan 4 safe-write envelopes exist.
- Plan 5 worker labels or equivalent ownership policy exists.

Why it helps:
- Speeds future agent creation by proposing scaffold files, tests, docs, and handoffs without writing them directly.

What it must not touch:
- No direct source writes, no package installs, no runtime lane mutation, no branch/worktree, no commit, no push, no self-approval.

Manual check style:
- Codex runs scaffold proposal tests and diff checks.

Handoff target:
- Agent Factory Plan 6 Phase 1 after safe-write and worker policy gates.

#### Phase 6.1: Scaffold Proposal Model

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.1.1: Scaffold packet | Define proposed files, tests, docs, rollback, and checks. | Exact approved Plan 6 files. | Creating scaffold files. | Scaffold proposal packet. | Packet tests. | Packet writes files. | 6.1.2: Authority audit hook. |
| 6.1.2: Authority audit hook | Require Authority Auditor review before use. | Exact approved Plan 6 files. | Bypassing audit. | Audit hook contract. | Audit fixture test. | Unsafe scaffold passes. | 6.1.3: Plan 6 closeout. |
| 6.1.3: Plan 6 closeout | Confirm proposal-only runtime. | Exact approved Plan 6 files. | Apply authority. | Short closeout. | Tests and diff check. | Scaffolder applies. | Plan 7 gate. |

### Plan 7: Design Agent Stack

When it starts:
- After Proxy and Cartographer are daily-driver stable enough for design proposals and records.

What must already be true:
- Agent Factory planning, Authority Auditor contract, Context Pack Builder plan, Source Rights Gate plan, Source Proxy design apply lane, and Cartographer record path exist.

Why it helps:
- Makes design work safer by separating source rights, visual evidence, proposal drafting, Source Proxy apply, and Cartographer recording.

What it must not touch:
- No direct UI apply, no scraping, no copying protected sources, no package install, no Visual Verifier authority to approve changes.

Manual check style:
- Codex runs exact design source, proposal, and visual evidence checks named by approved Plan 7 prompt.

Handoff target:
- Agent Factory Plan 7 Phase 1 after daily-driver Proxy/Cart proof.

#### Phase 7.1: Design Source Rights Gate

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7.1.1: Source card requirements | Define rights, license, approval, and use mode. | Exact approved Plan 7 files. | Scraping or source import. | Source rights contract. | Rights grep/check. | Unclear rights pass. | 7.1.2: Reject rules. |
| 7.1.2: Reject rules | Define blocked design sources. | Exact approved Plan 7 files. | Copying protected assets. | Reject matrix. | Reject matrix check. | Protected source accepted. | Phase 7.2. |

#### Phase 7.2: Visual Verification Planner

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7.2.1: Viewport evidence | Define screenshot targets and viewports. | Exact approved Plan 7 files. | Running new tooling without approval. | Visual evidence plan. | Grep for viewport/checks. | Tool install required. | 7.2.2: Design proposal packet. |
| 7.2.2: Design proposal packet | Connect source rights and visual evidence to Source Proxy proposals. | Exact approved Plan 7 files. | Direct UI edits. | Design proposal packet. | Source Proxy gated grep. | Proposal bypasses Proxy. | Plan 7 closeout. |

### Plan 8: Scout, Oracle, and Chat Helper Polish

When it starts:
- After Proxy and Cartographer are daily-driver stable, and product helper polish is explicitly approved.

What must already be true:
- Scout remains manual-gated.
- Oracle and Chat helper surfaces have honest tool-state boundaries.

Why it helps:
- Turns advisory intelligence and UI helper claims into clean packets without creating hidden authority.

What it must not touch:
- No Scout auto-promotion, no coding context writes, no Oracle command execution, no chat-triggered apply, no provider/auth/env changes.

Manual check style:
- Codex runs exact Scout dry-run and Oracle/Chat honesty checks.

Handoff target:
- Agent Factory Plan 8 Phase 1 after product-helper polish gate.

#### Phase 8.1: Scout Intake Curator

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8.1.1: Advisory packet | Define Scout candidate advisory packet. | Exact approved Plan 8 files. | Proxy memory or coding context writes. | Advisory packet contract. | Scout dry-run check. | Packet writes active context. | 8.1.2: Manual decision gate. |
| 8.1.2: Manual decision gate | Require human decision before promotion. | Exact approved Plan 8 files. | Auto-promotion. | Manual gate contract. | Grep for `manual`. | Auto-promotion allowed. | Phase 8.2. |

#### Phase 8.2: Oracle and Chat Tool-Honesty Review

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8.2.1: Tool-state labels | Define honest available, blocked, future, and failed states. | Exact approved Plan 8 files. | Executing commands. | Tool-honesty contract. | Label tests or grep. | UI claims false authority. | 8.2.2: Chat helper boundary. |
| 8.2.2: Chat helper boundary | Define helper output as advisory only. | Exact approved Plan 8 files. | Chat-triggered apply. | Chat helper boundary. | Advisory grep. | Chat applies. | Plan 8 closeout. |

### Plan 9: Multi-Agent Orchestration and Future Autonomy

When it starts:
- After daily-driver Proxy/Cart, product helpers, worker coordination, and trust-tier review.

What must already be true:
- Plans 1 through 8 are accepted or explicitly skipped by Britton.
- Trust-tier review approves the exact next boundary.

Why it helps:
- Gives a route for future orchestration without accidentally granting broad autonomy.

What it must not touch:
- No unbounded autonomy, hidden background workers, branch/worktree mutation, release action, commit, push, or external calls without explicit trust-tier approval.

Manual check style:
- Codex runs trust-tier review checks and exact future-plan tests.

Handoff target:
- Agent Factory Plan 9 Phase 1 after trust-tier approval.

#### Phase 9.1: Orchestration Proposal

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9.1.1: Orchestration map | Define worker graph and handoff boundaries. | Exact approved Plan 9 files. | Hidden workers. | Orchestration proposal. | Trust-tier grep. | Plan grants autonomy. | 9.1.2: Conflict policy. |
| 9.1.2: Conflict policy | Define conflict and stop behavior. | Exact approved Plan 9 files. | Overlapping writes. | Conflict policy. | Conflict fixture/check. | Conflict can proceed. | Phase 9.2. |

#### Phase 9.2: Future Authority Proposals

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9.2.1: Branch/worktree proposal | Define proposal-only branch/worktree policy. | Exact approved Plan 9 files. | Creating branch/worktree. | Proposal policy. | Grep for `proposal-only`. | Policy creates worktree. | 9.2.2: Release steward proposal. |
| 9.2.2: Release steward proposal | Define release evidence and closeout boundaries. | Exact approved Plan 9 files. | Tag, commit, push, deploy. | Release steward contract. | Release boundary grep. | Steward releases directly. | 9.2.3: Broader autonomy review. |
| 9.2.3: Broader autonomy review | Define trust-tier prerequisites only. | Exact approved Plan 9 files. | Self-approval or broad auto. | Trust-tier checklist. | Authority grep. | Checklist grants autonomy. | Stop. |

## Dirty Worktree Separation Rules

- Every future agent lane must name allowed files before editing.
- Pre-existing dirty files are user-owned.
- No cleanup, stash, reset, branch, or worktree without explicit permission.
- No two runtime lanes touch the same file family at once.
- Runtime helper agents cannot touch active Proxy or Cartographer implementation files unless that exact plan allows it.
- Every future implementation plan must start with `git status` and end with `git diff --check`, `git diff --name-only`, and exact test commands.

## Planning Package Closeout

The planning package is complete when:

- Plan 1 through Plan 9 exist in this roadmap.
- Each plan states when it starts, required gates, why it helps, what it must not touch, phases, small increments, manual check style, and handoff target.
- Plans that can run now are separated from plans that must wait for Source Proxy or Cartographer gates.
- No runtime, test, UI, package, config, Scout, Source Proxy, Cartographer, Design, commit, push, branch, worktree, stash, reset, or cleanup work is done.

READY FOR HANDOFF PROMPT:
Agent Factory Plan 1 Phase 1 can start in a new chat.

# Agent Ecosystem Master Roadmap v0.1

## Authority Statement

This roadmap is planning-only. It does not start implementation, Plan 1, runtime helpers, command execution, workflow execution, queue execution, source writes, commits, pushes, branches, worktrees, self-approval, package installs, server restarts, external API calls, or background autonomy.

The earlier Agent Factory docs-only contract work is prerequisite planning. It is not the real Plan 1. The first real implementation lane is Plan 1: Agent Factory Runtime Foundation, Phase 1: Authority Auditor and Lane Guard Runtime Skeleton.

Global authority rule:

Agent thinks and prepares. Proxy applies. Cartographer records and organizes. Human approves authority crossings.

## Timeline And Dependency Gates

| Timing | Plans | Rule |
| --- | --- | --- |
| Can be built now in parallel with Proxy and Cartographer | Plan 1 | Isolated Agent Factory runtime skeleton. New `source_proxy/agent_factory/**`, focused tests, and closeout doc only. Deterministic checks only. |
| Must wait for Source Proxy apply/verify/receipt loop | Plan 2 | Tester, Reviewer, Receipt Scribe, and Handoff Scribe helpers depend on stable Proxy approval, apply, verify, receipt, and provider truth. |
| Must wait for Cartographer live state and approval-token boundary | Plan 3 | Context Pack Builder and lane-state summaries need stable read-only Cartographer state and approval-token boundary proof. |
| Must wait for Cartographer safe writes and verification runner | Plan 4 | Agent Scaffolder proposal runtime, verification planner, and closeout scribe must not exist until safe-write and exact verification boundaries are proven. |
| Must wait for durable workflow queue and worker coordination | Plan 5 | Worker Registry, ownership zones, stale closeout, and one-worker-one-task proof need safe queue behavior. |
| Starts after Agent Factory foundation and Source Rights Gate plan exist | Plan 6 | Design Agent stack can begin once core Agent Factory contracts are stable and design source-rights boundaries are defined. |
| Starts after Scout review flow and Agent Factory contracts are stable | Plan 7 | Scout helper stack remains advisory and manual-gated. |
| Starts after Proxy and Cartographer daily-driver patterns are stable enough to reuse | Plan 8 | Oracle and Chat helper polish inherits proven tool-honesty and authority boundaries. |
| Must wait for Worker Registry, safe queue, and repeated soak proof | Plan 9 | Multi-agent orchestration and future autonomy remain proposal-only until repeated soak proof exists. |

## Master Plan Summary

| Plan | Name | Earliest start | Primary outputs | Hard blockers |
| --- | --- | --- | --- | --- |
| Plan 1 | Agent Factory Runtime Foundation | Now, after explicit new-chat approval | Authority Auditor, Lane Guard, contract models, deterministic safety checks | Any apply, commit, push, command, workflow, queue, or background authority |
| Plan 2 | Proxy-Dependent Proposal Helpers | After Proxy apply/verify/receipt loop is stable | Tester, Reviewer, Receipt Scribe, Handoff Scribe | Unstable Proxy apply/verify/provider truth |
| Plan 3 | Cartographer Read-Only Context Helpers | After Cartographer live state and approval-token boundary are stable | Context Pack Builder, lane state, protected lane summaries | Missing read-only live state or approval-token boundary |
| Plan 4 | Safe-Write and Verification Dependent Helpers | After safe writes and verification runner are stable | Agent Scaffolder proposal runtime, verification planner, closeout scribe | Missing safe-write or exact verification proof |
| Plan 5 | Workflow Queue and Worker Coordination Helpers | After durable workflow and safe queue exist | Worker Registry, ownership zones, stale closeout, one-worker-one-task proof | Missing safe queue or worker coordination |
| Plan 6 | Design Agent Stack | After Agent Factory foundation and Source Rights Gate plan exist | Reverse Designer, Design Vault, rights gate, blender, packs, visual verification, proposal lane | Missing design source-rights boundary |
| Plan 7 | Scout Helper Stack | After Scout review flow and Agent Factory contracts are stable | Scout intake, design bridge, trust classification, recommendation packets | Missing Scout review flow or stable contracts |
| Plan 8 | Oracle and Chat Helper Polish | After Proxy and Cartographer daily-driver patterns are stable | Tool-honesty review, task clarity helper, memory/tool boundary helper | Missing reusable daily-driver patterns |
| Plan 9 | Multi-Agent Orchestration and Future Autonomy | After Worker Registry, safe queue, and repeated soak proof | Leases, handoffs, dashboard, branch/worktree proposals, later release steward | Missing soak proof or safe queue |

## Shared Stop Conditions

- Any request to grant approval, apply, write, command execution, workflow execution, queue execution, commit, push, branch/worktree, self-approval, or background autonomy outside the explicitly approved plan.
- Any lane-caused dirty file outside the approved files.
- Any request to touch `source_proxy/**`, `src/**`, `scout/**`, `backend/**`, `scripts/**`, `config/**`, package files, tests, auth, environment, or implementation files before the active phase allows them.
- Any request to infer permission from a passing check, closeout, handoff, or receipt.
- Any request to start Plan 2 before Source Proxy dependency gates are satisfied.

## Plan 1: Agent Factory Runtime Foundation

Can be built now in parallel with Proxy and Cartographer because it is isolated to new Agent Factory runtime files, focused Agent Factory tests, and a closeout doc. It must provide deterministic safety checks only.

Blocked authority:

- No apply authority.
- No commit or push authority.
- No command execution authority beyond Codex running the phase's approved tests.
- No workflow or queue authority.
- No background autonomy.

### Phase 1: Authority Auditor and Lane Guard Runtime Skeleton

Goal:
Create the first inert runtime skeleton for contract models, Authority Auditor, and Lane Guard.

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1: Baseline and package shell | Capture status and create the new Agent Factory package shell. | `source_proxy/agent_factory/__init__.py`, `docs/agent-ecosystem-plan-1-phase-1-closeout-v0.1.md` only. | Existing source modules, package/config/env, broad tests, commits, pushes, branches, worktrees, stash/reset/clean. | Empty package export boundary and closeout draft header. | `git status --branch --short`; `python -m pytest source_proxy/tests/test_agent_factory_contracts.py -q` after tests exist, otherwise skip with note. | Any edit outside allowed files. | 1.2: Contract models. |
| 1.2: Contract models | Define deterministic dataclasses or typed models for authority flags, lane scope, audit finding, and lane report. | `source_proxy/agent_factory/contracts.py`, `source_proxy/tests/test_agent_factory_contracts.py`. | Proxy apply code, Cartographer code, command runners, queue code, package installs. | Contract models with fail-closed defaults and focused tests. | `python -m pytest source_proxy/tests/test_agent_factory_contracts.py -q`. | Any default grants approval, apply, write, command, workflow, queue, commit, push, branch/worktree, self-approval, or background autonomy. | 1.3: Authority Auditor skeleton. |
| 1.3: Authority Auditor skeleton | Add deterministic scans for authority drift in plain text and model data. | `source_proxy/agent_factory/authority_auditor.py`, `source_proxy/tests/test_agent_factory_authority_auditor.py`, contract file if needed. | Runtime approvals, token creation, command execution, source mutation, external calls. | Authority Auditor returning findings only. | `python -m pytest source_proxy/tests/test_agent_factory_contracts.py source_proxy/tests/test_agent_factory_authority_auditor.py -q`. | Auditor treats clean report as approval or mutates files. | 1.4: Lane Guard skeleton. |
| 1.4: Lane Guard skeleton | Add deterministic allowed-file, forbidden-file, dirty-state, and file-family overlap checks from supplied inputs. | `source_proxy/agent_factory/lane_guard.py`, `source_proxy/tests/test_agent_factory_lane_guard.py`, contract file if needed. | Git cleanup, real locks, workflow queue mutation, branch/worktree actions. | Lane Guard returning clear/caution/blocked reports only. | `python -m pytest source_proxy/tests/test_agent_factory_contracts.py source_proxy/tests/test_agent_factory_authority_auditor.py source_proxy/tests/test_agent_factory_lane_guard.py -q`. | Lane Guard changes files, cleans state, or claims ownership of unrelated dirty files. | 1.5: Phase closeout. |
| 1.5: Phase closeout | Record files changed, checks run, authority limits, and next permission phrase. | `docs/agent-ecosystem-plan-1-phase-1-closeout-v0.1.md` plus prior Phase 1 files for tiny corrections only. | New helpers, new roadmap/handoff writing, Plan 2, commits, pushes. | Phase 1 closeout doc. | `git diff --check -- source_proxy/agent_factory/*.py source_proxy/tests/test_agent_factory_*.py docs/agent-ecosystem-plan-1-phase-1-closeout-v0.1.md`; full focused pytest command. | Any failed focused check after one fix attempt. | Stop and ask Britton before Phase 2. |

### Phase 2: Deterministic Safety Rule Expansion

Goal:
Expand checks without adding authority.

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.1: Forbidden authority vocabulary | Centralize unsafe authority phrases and expected severity. | Existing `source_proxy/agent_factory/**`, focused tests. | Provider calls, source apply, command execution. | Vocabulary table and tests. | Focused Agent Factory pytest. | Any phrase list acts as permission. | 2.2: Evidence shape. |
| 2.2: Evidence shape | Add stable evidence fields for reports. | Existing Agent Factory models and tests. | Receipt stores, Cartographer writes. | Evidence object with file, source, rule, and detail fields. | Focused Agent Factory pytest. | Evidence object claims verification not run. | 2.3: Phase closeout. |
| 2.3: Phase closeout | Record deterministic safety expansion. | Closeout doc only, plus tiny fixes. | Next plan work. | Phase 2 closeout. | Diff check and focused pytest. | Authority expands. | Stop and ask Britton before Plan 2 gate review. |

## Plan 2: Proxy-Dependent Proposal Helpers

Blocked until Source Proxy apply/verify/receipt loop is stable.

### Phase 1: Tester Agent Proposal Helper

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.1.1: Test proposal model | Define proposed test target, rationale, and suggested command fields. | Exact approved Plan 2 files only. | Editing product tests without approval, package installs, command authority. | Tester proposal model. | Focused Plan 2 tests named in approved prompt. | Model executes tests itself. | 2.1.2: Gap classifier. |
| 2.1.2: Gap classifier | Classify missing coverage from approved inputs. | Exact approved Plan 2 files only. | Reading broad source without approved lane. | Coverage gap report. | Focused tests. | Classifier mutates files. | 2.1.3: Tester closeout. |
| 2.1.3: Tester closeout | Confirm proposal-only helper. | Closeout doc and exact files. | Apply, approval, commit, push. | Tester closeout. | Diff check and focused tests. | Tester grants authority. | Phase 2: Reviewer Agent. |

### Phase 2: Reviewer Agent Proposal Helper

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.2.1: Finding model | Define severity, file reference, risk, and suggested fix shape. | Exact approved Plan 2 files only. | Editing reviewed files. | Reviewer finding model. | Focused tests. | Finding implies approval. | 2.2.2: Scope review rules. |
| 2.2.2: Scope review rules | Compare diff summaries to approved lane. | Exact approved Plan 2 files only. | Cleanup, stash, reset. | Scope findings. | Focused tests. | Review mutates lane. | 2.2.3: Reviewer closeout. |
| 2.2.3: Reviewer closeout | Confirm review remains advisory. | Closeout doc and exact files. | Runtime approval. | Reviewer closeout. | Diff check and focused tests. | Reviewer approves apply. | Phase 3: Receipt and Handoff helpers. |

### Phase 3: Receipt Scribe and Handoff Scribe Runtime Helpers

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.3.1: Receipt Scribe helper | Draft receipts from verified Proxy data. | Exact approved Plan 2 files only. | Claiming unrun checks, writing receipt stores. | Receipt draft helper. | Focused tests. | Receipt becomes approval. | 2.3.2: Handoff Scribe helper. |
| 2.3.2: Handoff Scribe helper | Draft handoffs without starting next work. | Exact approved Plan 2 files only. | Starting next phase, inferring permission. | Handoff draft helper. | Focused tests. | Handoff starts work. | 2.3.3: Plan 2 closeout. |
| 2.3.3: Plan 2 closeout | Confirm all Proxy helpers are proposal-only. | Closeout doc and exact files. | Apply bypass. | Plan 2 closeout. | Diff check and focused tests. | Any helper bypasses Proxy. | Plan 3 gate review. |

## Plan 3: Cartographer Read-Only Context Helpers

Blocked until Cartographer live state and approval-token boundary are stable.

### Phase 1: Context Pack Builder

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.1.1: Context packet schema | Define read-only packet fields. | Exact approved Plan 3 files only. | Active context writes, Proxy intake calls. | Packet schema. | Focused tests. | Packet mutates context. | 3.1.2: Source attachment rules. |
| 3.1.2: Source attachment rules | Attach docs, status, and known gates as evidence. | Exact approved files. | Cleanup, normalization, writes. | Attachment rules. | Focused tests. | Attachment grants authority. | 3.1.3: Context closeout. |
| 3.1.3: Context closeout | Confirm read-only behavior. | Closeout doc and exact files. | Mutation. | Phase closeout. | Diff check and focused tests. | Any write occurs. | Phase 2: Read-only lane state. |

### Phase 2: Read-Only Lane State And Protected Summaries

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.2.1: Lane state adapter | Convert Cartographer live state into read-only lane summaries. | Exact approved files. | Approval-token consumption, safe writes. | Lane summary. | Focused tests. | Adapter consumes tokens. | 3.2.2: Protected lane summaries. |
| 3.2.2: Protected lane summaries | Summarize Proxy, Cartographer, Design, Scout, tests, package, and config protection. | Exact approved files. | Runtime locks. | Protected lane report. | Focused tests. | Summary blocks user work without approval. | 3.2.3: Plan 3 closeout. |
| 3.2.3: Plan 3 closeout | Confirm Plan 3 remains read-only. | Closeout doc and exact files. | Queue, workflow, command execution. | Plan 3 closeout. | Diff check and focused tests. | Any mutation or token use. | Plan 4 gate review. |

## Plan 4: Safe-Write and Verification Dependent Helpers

Blocked until Cartographer safe-write and verification runner are stable.

### Phase 1: Agent Scaffolder Proposal-Only Runtime

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.1.1: Scaffold proposal model | Define proposed files, tests, docs, checks, and rollback notes. | Exact approved Plan 4 files only. | Direct source writes, package installs. | Scaffold proposal model. | Focused tests. | Scaffolder writes files. | 4.1.2: Negative cases. |
| 4.1.2: Negative cases | Reject broad, protected, stale, or authority-expanding proposals. | Exact approved files. | Safe-write calls. | Negative-case matrix. | Focused tests. | Unsafe proposal passes. | 4.1.3: Scaffolder closeout. |
| 4.1.3: Scaffolder closeout | Confirm proposal-only status. | Closeout doc and exact files. | Apply authority. | Phase closeout. | Diff check and focused tests. | Scaffolder applies. | Phase 2: Verification planner. |

### Phase 2: Verification Planner And Closeout Scribe

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.2.1: Verification planner | Suggest exact verification command lists without executing them. | Exact approved files. | Command execution authority. | Verification plan. | Focused tests. | Planner runs commands. | 4.2.2: Closeout scribe. |
| 4.2.2: Closeout scribe | Draft closeouts from verified evidence. | Exact approved files. | Claiming unrun verification. | Closeout draft helper. | Focused tests. | Scribe fabricates proof. | 4.2.3: Plan 4 closeout. |
| 4.2.3: Plan 4 closeout | Confirm safe-write dependencies remain respected. | Closeout doc and exact files. | Direct apply. | Plan 4 closeout. | Diff check and focused tests. | Any safe-write bypass. | Plan 5 gate review. |

## Plan 5: Workflow Queue and Worker Coordination Helpers

Blocked until Cartographer durable workflow and safe queue exist.

### Phase 1: Worker Registry And Ownership Zones

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5.1.1: Worker registry model | Define worker id, role, lane, status, and evidence fields. | Exact approved Plan 5 files only. | Hidden workers, queue execution. | Worker registry model. | Focused tests. | Registry starts workers. | 5.1.2: Ownership zones. |
| 5.1.2: Ownership zones | Define file-family ownership and overlap reports. | Exact approved files. | Runtime locks without policy. | Ownership zone model. | Focused tests. | Zone blocks Britton without approval. | 5.1.3: Phase closeout. |
| 5.1.3: Phase closeout | Confirm registry is bounded. | Closeout doc and exact files. | Background autonomy. | Phase closeout. | Diff check and focused tests. | Hidden worker authority appears. | Phase 2: Stale closeout and proof. |

### Phase 2: Stale Worker Closeout And One-Worker-One-Task Proof

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5.2.1: Stale worker closeout | Define stale criteria and closeout reports. | Exact approved files. | Killing processes, queue mutation. | Stale closeout report. | Focused tests. | Helper controls workers directly. | 5.2.2: One-worker-one-task proof. |
| 5.2.2: One-worker-one-task proof | Prove no overlapping task ownership in fixtures. | Exact approved files. | Parallel hidden work. | Proof tests. | Focused tests. | Overlap passes silently. | 5.2.3: Plan 5 closeout. |
| 5.2.3: Plan 5 closeout | Confirm queue/worker dependencies. | Closeout doc and exact files. | Unapproved queue execution. | Plan 5 closeout. | Diff check and focused tests. | Helper executes queue. | Plan 6 gate review. |

## Plan 6: Design Agent Stack

Starts after Agent Factory foundation and Source Rights Gate plan exist.

### Phase 1: Design Source Rights And Vault Foundation

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.1.1: Source Rights Gate | Define source-card rights, allowed use modes, and blocked uses. | Exact approved Plan 6 files only. | Scraping, copying protected sources, license approval. | Rights gate model. | Focused tests. | Gate approves licenses. | 6.1.2: Design Vault. |
| 6.1.2: Design Vault | Store approved design references and provenance fields. | Exact approved files. | External fetch, asset copying. | Vault schema. | Focused tests. | Vault imports protected assets. | 6.1.3: Phase closeout. |
| 6.1.3: Phase closeout | Confirm rights boundaries. | Closeout doc and exact files. | Design apply. | Phase closeout. | Diff check and focused tests. | Rights boundary weakens. | Phase 2: Reverse Designer and Blender. |

### Phase 2: Reverse Designer, Blender, And Pack Authoring

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.2.1: Reverse Designer | Convert approved references into non-copying design observations. | Exact approved files. | Protected copying, UI apply. | Observation packet. | Focused tests. | Output copies protected source. | 6.2.2: Design Blender. |
| 6.2.2: Design Blender | Blend approved observations into original design directions. | Exact approved files. | Direct code generation. | Design blend packet. | Focused tests. | Blender grants apply authority. | 6.2.3: Design Pack Authoring. |
| 6.2.3: Design Pack Authoring | Draft design packs with provenance and constraints. | Exact approved files. | Asset scraping. | Design pack draft. | Focused tests. | Pack lacks rights evidence. | Phase 3: Visual verification and proposal lane. |

### Phase 3: Visual Verification Planner And Design Coding Proposal Lane

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.3.1: Visual Verification Planner | Define screenshot, viewport, and evidence plans. | Exact approved files. | Installing visual tooling without approval. | Visual check plan. | Focused tests. | Planner claims unrun screenshots. | 6.3.2: Design Coding Agent proposal lane. |
| 6.3.2: Design Coding Agent proposal lane | Draft UI implementation proposals without applying them. | Exact approved files. | Direct UI edits. | Proposal packet. | Focused tests. | Proposal edits UI. | 6.3.3: Plan 6 closeout. |
| 6.3.3: Plan 6 closeout | Confirm design stack remains gated. | Closeout doc and exact files. | Unapproved design apply. | Plan 6 closeout. | Diff check and focused tests. | Any source-rights bypass. | Plan 7 gate review. |

## Plan 7: Scout Helper Stack

Starts after Scout review flow and Agent Factory contracts are stable.

### Phase 1: Scout Intake Curator

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7.1.1: Intake packet model | Define candidate, source, trust, and review fields. | Exact approved Plan 7 files only. | Scout auto-promotion, coding context writes. | Intake packet model. | Focused tests. | Packet promotes itself. | 7.1.2: Trust classification. |
| 7.1.2: Trust/source classification | Classify source type and confidence. | Exact approved files. | External API calls. | Trust report. | Focused tests. | Trust report claims verification not run. | 7.1.3: Phase closeout. |
| 7.1.3: Phase closeout | Confirm manual-gated Scout intake. | Closeout doc and exact files. | Auto-ingestion. | Phase closeout. | Diff check and focused tests. | Scout helper writes coding context. | Phase 2: Scout to Design bridge. |

### Phase 2: Scout To Design Intake Bridge And Recommendation Packets

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7.2.1: Design bridge fields | Map Scout candidates to design-source review inputs. | Exact approved files. | Design Vault writes without approval. | Bridge packet. | Focused tests. | Bridge bypasses rights gate. | 7.2.2: Recommendation packets. |
| 7.2.2: Recommendation packets | Draft advisory packets with confidence and next manual action. | Exact approved files. | Auto-promotion. | Recommendation packet. | Focused tests. | Recommendation becomes approval. | 7.2.3: Plan 7 closeout. |
| 7.2.3: Plan 7 closeout | Confirm advisory-only Scout stack. | Closeout doc and exact files. | Hidden Scout actions. | Plan 7 closeout. | Diff check and focused tests. | Helper writes active contexts. | Plan 8 gate review. |

## Plan 8: Oracle and Chat Helper Polish

Starts after Proxy and Cartographer daily-driver patterns are stable enough to reuse.

### Phase 1: Oracle Tool-Honesty Reviewer

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8.1.1: Tool-state claim model | Define available, unavailable, unknown, and blocked tool states. | Exact approved Plan 8 files only. | Command execution, provider/auth/env changes. | Tool-honesty model. | Focused tests. | Model executes tools. | 8.1.2: Honesty findings. |
| 8.1.2: Honesty findings | Detect UI or helper claims that overstate tool capability. | Exact approved files. | UI mutation without approval. | Honesty report. | Focused tests. | Report grants authority. | 8.1.3: Phase closeout. |
| 8.1.3: Phase closeout | Confirm reviewer is read-only/advisory. | Closeout doc and exact files. | Tool execution. | Phase closeout. | Diff check and focused tests. | Reviewer changes tool state. | Phase 2: Chat clarity and memory boundary. |

### Phase 2: Chat Task Clarity And Memory/Tool Boundary Helpers

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8.2.1: Task clarity helper | Suggest clearer task scopes and stop conditions. | Exact approved files. | Starting work, applying edits. | Clarity suggestion. | Focused tests. | Suggestion infers approval. | 8.2.2: Memory/tool boundary helper. |
| 8.2.2: Memory/tool boundary helper | Identify what belongs in memory, tools, or one-off context. | Exact approved files. | Memory writes without approval. | Boundary report. | Focused tests. | Helper writes memory/tool state. | 8.2.3: Plan 8 closeout. |
| 8.2.3: Plan 8 closeout | Confirm polish helpers inherit daily-driver boundaries. | Closeout doc and exact files. | Provider/auth/config mutation. | Plan 8 closeout. | Diff check and focused tests. | Any helper changes authority. | Plan 9 gate review. |

## Plan 9: Multi-Agent Orchestration and Future Autonomy

Blocked until Worker Registry, safe queue, and repeated soak proof exist.

### Phase 1: Worker Leases And Handoff Packets

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9.1.1: Worker lease model | Define bounded lease fields, owner, lane, timeout, and evidence. | Exact approved Plan 9 files only. | Starting workers, queue execution, background autonomy. | Lease model. | Focused tests. | Lease starts work. | 9.1.2: Handoff packets. |
| 9.1.2: Handoff packets | Define cross-worker handoff packet fields. | Exact approved files. | Inferring permission. | Handoff packet model. | Focused tests. | Handoff starts next worker. | 9.1.3: Phase closeout. |
| 9.1.3: Phase closeout | Confirm orchestration remains controlled. | Closeout doc and exact files. | Hidden workers. | Phase closeout. | Diff check and focused tests. | Lease grants autonomy. | Phase 2: Coordination dashboard. |

### Phase 2: Coordination Dashboard And Branch/Worktree Proposal Only

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9.2.1: Coordination dashboard data | Define display-only dashboard summaries. | Exact approved files. | Dashboard controls that mutate queue. | Dashboard data model. | Focused tests. | Dashboard triggers work. | 9.2.2: Branch/worktree proposal only. |
| 9.2.2: Branch/worktree proposal only | Draft branch/worktree proposals for human approval. | Exact approved files. | Creating branches or worktrees. | Proposal packet. | Focused tests. | Proposal creates git state. | 9.2.3: Phase closeout. |
| 9.2.3: Phase closeout | Confirm no branch/worktree mutation. | Closeout doc and exact files. | Git mutation. | Phase closeout. | Diff check and focused tests. | Any branch/worktree action occurs. | Phase 3: Release steward later. |

### Phase 3: Release Steward Later

| Increment | Purpose | Allowed files/lane | Forbidden files/actions | Expected output | Codex self-check | Stop conditions | Next increment title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9.3.1: Release steward proposal | Define release checklist proposal fields. | Exact approved files only after trust-tier approval. | Release action, commit, push, tagging. | Release proposal model. | Focused tests. | Steward releases. | 9.3.2: Soak evidence gate. |
| 9.3.2: Soak evidence gate | Require repeated soak proof before any future autonomy expansion. | Exact approved files. | Skipping soak proof. | Soak gate report. | Focused tests. | Gate passes without proof. | 9.3.3: Final roadmap closeout. |
| 9.3.3: Final roadmap closeout | Record that broader autonomy remains future-gated. | Closeout doc and exact files. | Unbounded autonomy. | Final closeout. | Diff check and focused tests. | Any autonomy grant appears. | Stop. |

## Plan 1 New-Chat Handoff Target

The only real copy-paste handoff for this planning chat is:

`docs/agent-ecosystem-plan-1-start-handoff-v0.1.md`

That prompt starts the first real implementation lane in a new Codex chat. This roadmap does not start it.

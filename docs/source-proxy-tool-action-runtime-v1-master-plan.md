# Source Proxy Tool Action Runtime v1 Master Plan

Status:
- approved roadmap / planning document
- implementation not started by this document
- owner/operator: Britton
- current purpose: install the next roadmap after the discovered tool-handling oversight

## Authority Statement

This document is a roadmap only. It does not implement runtime behavior, grant autonomous write authority, enable safe apply, change providers, mutate Cartographer, start hidden workers, run queues, commit, push, branch, worktree, stash, reset, checkout, clean, or perform final CSS polish.

## Problem Statement

The previous benchmark/gauntlet path exposed a structural problem: Source Proxy was missing a native, generic model-action contract and workspace executor. Benchmarking now would test missing plumbing rather than model ability. Source Proxy needs native hands before comparisons resume.

## Critical Diagnosis

Confirmed source-of-truth evidence says Plan 8 was a readiness handoff only, not implementation. Harness evidence can be S+, but real frontend use remains REMEDIATION REQUIRED until natural prompt to bounded TaskSpec intake plus scope clarification UI exists.

The lane plumbing diagnosis identifies the missing adapter as a workspace-only executor that accepts model-authored Write/Edit/MultiEdit/Bash calls or explicit path/content blocks, enforces path containment, and preserves transcript/diff/events. Source Proxy/Qwen became advisory-only because planner fallthrough occurred for `no_explicit_target`. Continue/Qwen emitted parseable actions, but bridge/parsing limitations missed valid output in some cases.

Mac worker and Mac subagents are advisory/check support only. Source Proxy remains write/apply authority. Safe apply, final CSS, provider/model route changes, Cartographer activation, hidden workers, commit/push remain blocked unless explicitly approved by a later plan.

## No-Cheat Rule

Fair:
- expose generic tools/actions to every coding model
- selected model decides paths and contents
- execute only model-authored actions after validation
- record transcript, parsed action, diff, checks, and receipt

Cheating:
- backend creates files for the model
- task-specific helper tells model exactly what to write
- proxy upgrades vague/freeform output into working files without an explicit model-authored path/content/action
- Mac/subagents apply code or bypass Source Proxy authority

## Architecture Target

User prompt
-> TaskSpec intake and scope clarification
-> context packet / repo map / Mac advisory packet / subagent advisory packet
-> selected model call
-> model-authored generic actions
-> parser and validator
-> path-contained disposable workspace executor
-> checks / observations
-> bounded retry
-> UI transcript + diff + receipt
-> apply remains blocked unless a later approved safe-apply gate exists

## Open-Source Design References

- Aider reference pattern: repo maps expose the important symbols and relationships in a repository, then edit discipline is reinforced with git history, undo/review affordances, and lint/test feedback loops.
- Continue reference pattern: Plan mode is read-only and filters out write/execute operations; Agent mode gives the model schema-described tools, requests permission according to policy, executes tools, and returns observations to the model.
- Codex reference pattern: sandbox and approval policies are explicit runtime controls; subagents are useful for parallel exploration/review and inherit sandbox/approval policy from the parent workflow.
- MCP reference pattern: tools are schema-described, model-invoked capabilities; applications should show which tools are exposed, visibly indicate invocations, and keep humans in the loop for meaningful operations.

Reference URLs:
- https://aider.chat/docs/repomap.html
- https://aider.chat/docs/git.html
- https://aider.chat/docs/usage/lint-test.html
- https://docs.continue.dev/ide-extensions/agent/plan-mode
- https://docs.continue.dev/ide-extensions/agent/how-it-works
- https://developers.openai.com/codex/agent-approvals-security
- https://developers.openai.com/codex/subagents
- https://modelcontextprotocol.io/specification/2025-06-18/server/tools

## Core Components

1. TaskSpec intake
2. Tool/action schema and parser
3. Workspace executor
4. Policy/authority validator
5. Bounded loop controller
6. Verification and receipt ledger
7. Mac/subagent advisory broker
8. UI surfaces for TaskSpec, tool calls, diff, checks, blocked reasons
9. Benchmark return gate

## Roadmap Sequence

- Plan 0/8: Roadmap Install, Baseline, And Pivot Guard
- Plan 1/8: Natural Prompt To TaskSpec Intake
- Plan 2/8: Tool/Action Contract And Parser
- Plan 3/8: Disposable Workspace Executor And Safety Gates
- Plan 4/8: Bounded Agent Loop And Verification Receipts
- Plan 5/8: Mac/Subagent Advisory Tool Broker
- Plan 6/8: /coding UI Integration For TaskSpec, Actions, Diffs, And Receipts
- Plan 7/8: Trap Suite, Golden Tasks, And Safety Verification
- Plan 8/8: Benchmark Return Gate And Comparison Rerun Packet

## PIVOT Workflow

- Work one approved plan at a time.
- Work increment by increment.
- After each increment: run checks, record concise evidence, state GO/NO-GO, continue automatically if GO.
- At phase end: confirm all increments, evidence, no forbidden scope, checks, GO/NO-GO.
- At plan end: produce manual verification block, expected output, files changed, artifacts, blockers, GO/NO-GO, next plan title only.
- Stop at plan boundary and wait for Britton approval before the next plan.
- Britton approves plans, not every increment.
- Never invent new roadmap content from vibes.

## Global Rollback Guidance

For docs-only plans, rollback by reverting only the specific docs produced by that plan after confirming no unrelated dirty work is included. For runtime plans, rollback by deleting only disposable workspaces, generated receipts, or new runtime files created by the approved plan. Never reset, clean, stash, checkout, branch, commit, or push unless a later approval explicitly allows it.

## Global Stop Conditions

Stop immediately and report NO-GO if a plan attempts real-app mutation from a trial prompt, provider/model routing changes, safe apply, Cartographer mutation, hidden workers, Mac/subagent write authority, protected path access, secret access, destructive git operations, branch/worktree mutation, commit/push, or final CSS polish without a later explicit approval.

---

# Plan 0/8: Roadmap Install, Baseline, And Pivot Guard

Goal:
Install the roadmap, freeze benchmark continuation until the runtime exists, and map existing files/routes/modules.

## Phase 0.1 Source-of-truth confirmation

- Increment 0.1.1 Read Plan 8 readiness handoff and final-grade evidence.
- Increment 0.1.2 Read lane plumbing diagnosis and closeout.
- Increment 0.1.3 Read Mac worker contract and Mac advisory/subagent boundaries.
- Increment 0.1.4 Record active roadmap precedence and deprecated/historical docs.

Checks:
- grep source docs for Plan 8 readiness, REMEDIATION REQUIRED, lane plumbing repair, Mac advisory-only, and forbidden scope.
- `git diff --check` on roadmap docs.

GO:
Source-of-truth files are confirmed or missing files are explicitly listed; no invented evidence is used.

NO-GO:
Stop if required authority docs conflict, source-of-truth evidence is unavailable, or runtime work is needed to answer the source-of-truth question.

Rollback:
Remove only the roadmap/handoff/index edits created by this plan.

Stop conditions:
Any source/runtime edit, model call, worker start, Cartographer action, safe apply, commit, push, branch, worktree, stash, reset, checkout, or clean.

## Phase 0.2 Repo capability inventory

- Increment 0.2.1 Inventory /coding task composer and allowed/forbidden file surfaces.
- Increment 0.2.2 Inventory existing action preview/parser/workspace functions.
- Increment 0.2.3 Inventory Source Proxy model routing and context-packet generation.
- Increment 0.2.4 Inventory Mac worker, Scout, search, design review, and helper-agent packet paths.

Checks:
- targeted `rg` inventory only; do not edit source.
- record file/path findings in the Plan 0 closeout.

GO:
Existing surfaces are mapped enough to start Plan 1 without implementing.

NO-GO:
Stop if inventory requires running provider/model calls or touching protected source paths.

Rollback:
Delete only generated Plan 0 evidence/closeout docs if approved by Britton.

Stop conditions:
Any unapproved implementation or mutation outside docs/evidence allowed by the active plan.

## Phase 0.3 Pivot guard

- Increment 0.3.1 Add/confirm a docs-only pivot statement: benchmarking paused until runtime GO.
- Increment 0.3.2 Define "native hands" readiness terms.
- Increment 0.3.3 Define future benchmark fairness rules.

Checks:
- grep target docs for roadmap sequence, no-cheat rule, Mac advisory-only boundary, benchmark pause, TaskSpec, tool/action runtime.
- `git diff --check` for created docs.
- `git status --branch --short --untracked-files=normal`.

GO:
Roadmap is installed, active boundary clear, and no runtime implementation occurred.

NO-GO:
Stop if roadmap authority is unclear or docs imply benchmarking may continue before native hands exist.

Rollback:
Revert only Plan 0 docs pointer and roadmap install docs.

Stop conditions:
Any benchmark rerun, provider/model call, trial prompt execution, worker start, source edit, or git mutation.

---

# Plan 1/8: Natural Prompt To TaskSpec Intake

Goal:
Convert messy daily-driver coding prompts into bounded TaskSpecs or visible clarification requests.

## Phase 1.1 TaskSpec schema

- Increment 1.1.1 Define TaskSpec fields: task_kind, intent, user_prompt, target_paths, allowed_files, forbidden_files, protected_paths, workspace_mode, approval_level, model_lane, context_sources, verification_policy, risk_level, clarification_state.
- Increment 1.1.2 Add schema validation and human-readable errors.
- Increment 1.1.3 Add TaskSpec serialization for diagnostics/copy.

Checks:
- unit tests for schema acceptance/rejection.
- diagnostics packet snapshot.
- `tsc` / lint as applicable.
- `git diff --check`.

GO:
TaskSpec exists, validates, serializes, and reports bounded errors without model calls.

NO-GO:
Stop if ambiguous real-repo targets can still become silent advisory fallthrough.

Rollback:
Remove only TaskSpec files/tests added by this plan.

Stop conditions:
Provider routing changes, apply, real app mutation from prompt, or hidden worker execution.

## Phase 1.2 Creation-intent route

- Increment 1.2.1 Detect create/new-project/no-target prompts separately from advisory prompts.
- Increment 1.2.2 For disposable workspace tasks, allow target path inference only within the workspace.
- Increment 1.2.3 If real repo target is ambiguous, produce AskClarification instead of fallthrough.

Checks:
- ambiguous target trap.
- `no_explicit_target` trap.
- no-op trap.
- `git diff --check`.

GO:
Messy creation prompts no longer silently fall into advisory-only when a disposable workspace task can be safely formed; otherwise the UI asks a bounded clarification.

NO-GO:
Stop if Source Proxy invents real paths or turns vague prose into source edits.

Rollback:
Revert only creation-intent route and tests from this plan.

Stop conditions:
Any backend-created task-specific file content or unapproved real app mutation.

## Phase 1.3 Scope clarification UI

- Increment 1.3.1 Show "what Source Proxy understood" before model call.
- Increment 1.3.2 Show target files, allowed files, forbidden files, protected paths.
- Increment 1.3.3 Show blocked/no-op/already-satisfied states honestly.

Checks:
- UI component tests.
- Playwright smoke if UI is touched.
- mobile viewport smoke if UI is touched.
- `git diff --check`.

GO:
User can see and correct the TaskSpec before model-action execution begins.

NO-GO:
Stop if UI hides blocked/no-op states or implies apply authority.

Rollback:
Remove only UI additions and tests from this plan.

Stop conditions:
Final CSS polish, apply controls, provider calls, or trial mutation.

---

# Plan 2/8: Tool/Action Contract And Parser

Goal:
Create the generic Source Proxy action protocol used by local, cloud, and adapter lanes.

## Phase 2.1 Action envelope

- Increment 2.1.1 Define versioned action envelope: action_id, action_type, target, arguments, reason, requires_approval, model_id, source_message_id, allowed_files_snapshot, created_at.
- Increment 2.1.2 Define result envelope: action_id, status, blocked_reason, files_touched, diff_summary, stdout/stderr, observation, receipt_path.
- Increment 2.1.3 Add stable error codes.

Checks:
- schema tests.
- fixture snapshots.
- `git diff --check`.

GO:
Action/result envelopes are versioned, stable, and model-authored.

NO-GO:
Stop if backend-created content can masquerade as model-authored action content.

Rollback:
Remove envelope definitions and tests added in this plan.

Stop conditions:
Runtime execution before parser contract is approved.

## Phase 2.2 Initial tool set

- Increment 2.2.1 ReadFile
- Increment 2.2.2 ListFiles
- Increment 2.2.3 SearchRepo
- Increment 2.2.4 WriteFile
- Increment 2.2.5 EditFile
- Increment 2.2.6 MultiEdit
- Increment 2.2.7 RunCheck
- Increment 2.2.8 AskClarification
- Increment 2.2.9 ReturnFinal

Checks:
- parser fixtures for each action type.
- read/write/execute classifications.
- `git diff --check`.

GO:
Tool set is generic and not task-specific.

NO-GO:
Stop if any tool encodes a specific benchmark answer or task-specific scaffold.

Rollback:
Remove tool definitions added in this plan.

Stop conditions:
Executing WriteFile/EditFile/MultiEdit/RunCheck before Plan 3 authority exists.

## Phase 2.3 Parser paths

- Increment 2.3.1 Strict JSON tool-call parser.
- Increment 2.3.2 Line-delimited/multiple JSON action parser.
- Increment 2.3.3 Explicit path/content block parser for local-model fallback.
- Increment 2.3.4 Wrong-format rejection and bounded format-repair prompt.
- Increment 2.3.5 Preserve raw transcript and parse decisions.

Checks:
- parser unit tests.
- fixture tests for malformed JSON, multiple JSON actions, string Bash args, path/content blocks, free-floating HTML.
- no backend-invented file content.
- `git diff --check`.

GO:
A selected model can emit parseable generic actions, and invalid output is rejected or repaired visibly without hidden scaffolding.

NO-GO:
Stop if free-floating code with no path/action can be upgraded into a file.

Rollback:
Remove parser paths and fixtures added in this plan.

Stop conditions:
Hidden repair, hidden scaffold, unrecorded transcript, or unbounded retry.

## Phase 2.4 Adapter compatibility

- Increment 2.4.1 Normalize Continue Bash string args only for Bash.
- Increment 2.4.2 Normalize Aider-like edit chunks only if model-authored and path-bound.
- Increment 2.4.3 Reject free-floating HTML/code with no path/action.
- Increment 2.4.4 Record adapter source lane in receipt.

Checks:
- Continue multiple-action fixture.
- Bash string-args fixture.
- Aider-like path-bound edit fixture.
- free-floating HTML rejection fixture.
- `git diff --check`.

GO:
Adapters preserve model-authored intent without inventing content.

NO-GO:
Stop if adapter behavior hides wrapper failure as model failure or model success.

Rollback:
Remove adapter normalizers added in this plan.

Stop conditions:
Task-specific helpers, real app mutation, provider routing changes, or benchmark reruns.

---

# Plan 3/8: Disposable Workspace Executor And Safety Gates

Goal:
Execute validated actions only inside an approved disposable workspace or temp worktree.

## Phase 3.1 Workspace containment

- Increment 3.1.1 Define workspace root contract.
- Increment 3.1.2 Block path traversal and symlink escapes.
- Increment 3.1.3 Block protected paths and forbidden files.
- Increment 3.1.4 Record before/after workspace status.

Checks:
- containment tests.
- protected-path trap.
- symlink/path traversal trap.
- `git diff --check`.

GO:
Executor cannot leave approved disposable workspace boundaries.

NO-GO:
Stop if any action can touch the real app or protected paths.

Rollback:
Delete disposable workspace artifacts and revert executor files from this plan.

Stop conditions:
Real app mutation, hidden worktree creation, branch mutation, or unsafe path resolution.

## Phase 3.2 Write/edit execution

- Increment 3.2.1 Implement WriteFile.
- Increment 3.2.2 Implement EditFile.
- Increment 3.2.3 Implement MultiEdit.
- Increment 3.2.4 Produce unified diff.

Checks:
- write/edit/multiedit tests.
- diff receipt tests.
- wrong-file trap.
- `git diff --check`.

GO:
Generic model-authored actions can safely alter disposable workspace files.

NO-GO:
Stop if executor writes outside allowed files or edits without a model-authored path/content/action.

Rollback:
Remove executor write/edit additions and generated disposable files.

Stop conditions:
Safe apply to real repo, backend-created content, or source mutation from trial prompt.

## Phase 3.3 Read/search execution

- Increment 3.3.1 Implement ReadFile.
- Increment 3.3.2 Implement ListFiles.
- Increment 3.3.3 Implement SearchRepo with limits.

Checks:
- read/list/search tests.
- output limit tests.
- protected path read trap.
- `git diff --check`.

GO:
Read/search operations are bounded and receipt-visible.

NO-GO:
Stop if secrets or protected paths can be read.

Rollback:
Remove read/search executor additions.

Stop conditions:
Secret reads, unbounded output, or network access.

## Phase 3.4 RunCheck execution

- Increment 3.4.1 Allowlist commands.
- Increment 3.4.2 Add timeout and output limits.
- Increment 3.4.3 Network policy remains blocked unless explicitly allowed.
- Increment 3.4.4 No hidden background jobs.

Checks:
- command allowlist tests.
- timeout/output limit tests.
- hidden worker trap.
- network-block trap.
- `git diff --check`.

GO:
RunCheck is bounded, visible, and workspace-contained.

NO-GO:
Stop if arbitrary shell execution or background jobs are possible.

Rollback:
Remove RunCheck executor and generated check receipts.

Stop conditions:
Hidden workers, unapproved network, destructive commands, or persistent processes.

## Phase 3.5 Authority validator

- Increment 3.5.1 Central gate checks TaskSpec, allowed files, forbidden files, protected paths, approval level.
- Increment 3.5.2 Integrate existing lane guards/authority auditors if present.
- Increment 3.5.3 Block unsafe commands and report reason.

Checks:
- authority validator tests.
- protected-path trap.
- wrong-file trap.
- unsafe command trap.
- `git diff --check`.

GO:
Generic model-authored actions can safely alter disposable workspace files and never mutate the real app or protected paths.

NO-GO:
Stop if authority violation is retried instead of blocked.

Rollback:
Remove authority validator additions and tests from this plan.

Stop conditions:
Bypass of TaskSpec, allowed-files, protected-path, or approval-level gates.

---

# Plan 4/8: Bounded Agent Loop And Verification Receipts

Goal:
Create the professional loop: inspect, act, observe, verify, repair once or stop.

## Phase 4.1 Loop controller

- Increment 4.1.1 Call selected model with TaskSpec, context packet, tool contract, and current observations.
- Increment 4.1.2 Execute one or more validated actions.
- Increment 4.1.3 Feed observations/check output back to model.
- Increment 4.1.4 Stop with ReturnFinal, blocked state, or retry exhaustion.

Checks:
- bounded loop tests.
- no hidden continuation audit.
- blocked state tests.
- `git diff --check`.

GO:
Loop is visible, bounded, and authority-gated.

NO-GO:
Stop if loop can continue silently or mutate outside disposable workspace.

Rollback:
Remove loop controller additions and generated receipts.

Stop conditions:
Unbounded loop, hidden worker, provider route change, or safe apply.

## Phase 4.2 Retry policy

- Increment 4.2.1 Format retry cap.
- Increment 4.2.2 Verification repair cap.
- Increment 4.2.3 No retry for authority/protected-path violations.
- Increment 4.2.4 Honest partial-completion states.

Checks:
- retry cap tests.
- authority violation no-retry test.
- partial completion receipt test.
- `git diff --check`.

GO:
Retries are capped and failure states are honest.

NO-GO:
Stop if retry logic hides failure or repeatedly asks the model to bypass safety.

Rollback:
Remove retry policy additions.

Stop conditions:
Retry on protected-path or authority violations.

## Phase 4.3 Receipts

- Increment 4.3.1 Record raw model transcript.
- Increment 4.3.2 Record parsed actions and validation.
- Increment 4.3.3 Record diffs, check outputs, blocked reasons, and final state.
- Increment 4.3.4 Add copy-diagnostics packet.

Checks:
- receipts tests.
- raw transcript preservation test.
- diagnostics copy snapshot.
- `git diff --check`.

GO:
Source Proxy produces durable evidence of what happened.

NO-GO:
Stop if receipts omit raw transcript, parsed actions, diffs, or blocked reasons.

Rollback:
Remove receipt writer additions and generated evidence.

Stop conditions:
Pretend pass, no-diff hidden as PASS, or unrecorded action execution.

## Phase 4.4 Verification policy

- Increment 4.4.1 Run recommended checks only when policy allows.
- Increment 4.4.2 Surface skipped checks and why.
- Increment 4.4.3 Confirm no hidden apply or trial mutation.

Checks:
- verification policy tests.
- skipped-check receipt test.
- no hidden apply audit.
- `git diff --check`.

GO:
Source Proxy can run a visible, bounded coding loop and produce a durable receipt proving what happened.

NO-GO:
Stop if checks run outside policy or skipped checks are hidden.

Rollback:
Remove verification policy additions.

Stop conditions:
Unapproved commands, hidden apply, hidden mutation, or fake check pass.

---

# Plan 5/8: Mac/Subagent Advisory Tool Broker

Goal:
Integrate Mac support and subagents as advisory packet sources without granting write authority.

## Phase 5.1 Capability manifest

- Increment 5.1.1 Define Source Proxy tool capabilities.
- Increment 5.1.2 Define Mac worker advisory capabilities.
- Increment 5.1.3 Define subagent advisory roles.
- Increment 5.1.4 Expose truth in UI/diagnostics.

Checks:
- capability manifest tests.
- UI/diagnostic truth snapshot.
- `git diff --check`.

GO:
Capabilities are explicit and do not imply Mac/subagent write authority.

NO-GO:
Stop if UI presents Mac/subagents as executors.

Rollback:
Remove manifest and UI/diagnostic additions.

Stop conditions:
Mac write authority, subagent apply authority, hidden workers, or provider changes.

## Phase 5.2 Mac adapter contract

- Increment 5.2.1 Mac may return system_status, safe checks, repo context, search packets, browser/design inspection packets.
- Increment 5.2.2 Mac must not write repo files, start hidden workers, apply code, run Cart workflows, change routing, or read secrets.
- Increment 5.2.3 Mac packets are opt-in and attached as context only.

Checks:
- Mac advisory-only tests.
- no Mac write authority tests.
- secret/protected path trap.
- `git diff --check`.

GO:
Mac can help with context/checks without becoming an executor.

NO-GO:
Stop if Mac adapter can mutate source or run hidden/persistent jobs.

Rollback:
Remove Mac adapter additions and generated packets.

Stop conditions:
Mac writes, launch agents, daemons, hidden workers, secret reads, or routing changes.

## Phase 5.3 Subagent contract

- Increment 5.3.1 Component Mapper advisory packet.
- Increment 5.3.2 Safety Reviewer advisory packet.
- Increment 5.3.3 Test Scribe advisory packet.
- Increment 5.3.4 Design Reviewer advisory packet.
- Increment 5.3.5 Scout Research Helper advisory packet.
- Increment 5.3.6 Tool Steward advisory/audit packet.

Checks:
- subagent packet schema tests.
- advisory-only enforcement tests.
- `git diff --check`.

GO:
Subagents produce bounded packets only.

NO-GO:
Stop if subagent output can bypass Source Proxy validation or write authority.

Rollback:
Remove subagent contract additions.

Stop conditions:
Subagent writes, apply, commits, worker starts, or direct Cart mutation.

## Phase 5.4 Conflict handling

- Increment 5.4.1 If subagents disagree, report conflict.
- Increment 5.4.2 Safety Reviewer blocks are visible but do not silently mutate actions.
- Increment 5.4.3 Source Proxy remains final gate.

Checks:
- conflict display tests.
- Safety Reviewer block tests.
- final gate tests.
- `git diff --check`.

GO:
Mac and subagents improve context/review without becoming hidden executors.

NO-GO:
Stop if conflicts are resolved by silently changing model actions.

Rollback:
Remove conflict-handling additions.

Stop conditions:
Hidden mutation, hidden scaffold, or authority bypass.

---

# Plan 6/8: /coding UI Integration For TaskSpec, Actions, Diffs, And Receipts

Goal:
Make the tool runtime understandable and controllable from the UI.

## Phase 6.1 Intake panel

- Increment 6.1.1 Show TaskSpec fields.
- Increment 6.1.2 Show clarification state.
- Increment 6.1.3 Show model lane and tool capability truth.

Checks:
- component tests.
- Playwright UI smoke.
- mobile viewport smoke.
- `git diff --check`.

GO:
Users can see what Source Proxy understood before tool execution.

NO-GO:
Stop if model/tool capability truth is obscured.

Rollback:
Remove intake panel additions.

Stop conditions:
Final CSS polish, unsafe controls, apply button authority, or hidden model calls.

## Phase 6.2 Action transcript panel

- Increment 6.2.1 Show model-authored tool calls.
- Increment 6.2.2 Show validation result.
- Increment 6.2.3 Show blocked reasons.
- Increment 6.2.4 Show check output.

Checks:
- transcript rendering tests.
- blocked reason tests.
- no unsafe controls grep.
- `git diff --check`.

GO:
Users can see model-authored actions and validation outcomes.

NO-GO:
Stop if UI hides blocked reasons or implies backend-authored actions.

Rollback:
Remove transcript panel additions.

Stop conditions:
Fake pass, hidden failed checks, or apply authority claim.

## Phase 6.3 Diff/review panel

- Increment 6.3.1 Show disposable workspace diff.
- Increment 6.3.2 Show files touched.
- Increment 6.3.3 Show apply remains blocked unless separately approved.

Checks:
- diff panel tests.
- safe-apply-blocked display test.
- Playwright smoke.
- `git diff --check`.

GO:
Diff review is visible and scoped to disposable workspace changes.

NO-GO:
Stop if diff panel can apply to real repo without later approval.

Rollback:
Remove diff/review panel additions.

Stop conditions:
Safe apply, real repo apply, branch/worktree mutation, commit, or push.

## Phase 6.4 Copy diagnostics

- Increment 6.4.1 One copy action includes TaskSpec, tools exposed, actions attempted, blocked reasons, diff summary, checks, and next action.
- Increment 6.4.2 Include Mac/subagent packet references when used.

Checks:
- copy diagnostics snapshot.
- Mac/subagent reference test.
- Playwright copy smoke if practical.
- `git diff --check`.

GO:
A user can see what Source Proxy understood, what the model tried, what was executed, what was blocked, and why.

NO-GO:
Stop if copied diagnostics omit action authority, blocked reasons, or diff/check state.

Rollback:
Remove diagnostics UI additions.

Stop conditions:
Secret leakage, hidden action execution, or unsafe controls.

---

# Plan 7/8: Trap Suite, Golden Tasks, And Safety Verification

Goal:
Prove the runtime with realistic and adversarial tasks.

## Phase 7.1 Golden tasks

- Increment 7.1.1 Homepage creation in disposable workspace.
- Increment 7.1.2 Docs/config edit in allowed file.
- Increment 7.1.3 Frontend component edit in dummy route.
- Increment 7.1.4 Test-writing proposal or dummy test edit.
- Increment 7.1.5 No-op/already satisfied task.
- Increment 7.1.6 Messy no-target prompt.

Checks:
- golden suite.
- no permanent mutation proof.
- git status before/after.
- `git diff --check`.

GO:
Runtime handles useful coding tasks in disposable workspace with honest receipts.

NO-GO:
Stop if golden tasks require hidden scaffolds or mutate real app.

Rollback:
Delete generated disposable workspaces/evidence and revert suite additions.

Stop conditions:
Real app mutation, backend-created task answer, or hidden apply.

## Phase 7.2 Trap tasks

- Increment 7.2.1 Protected path trap.
- Increment 7.2.2 Wrong file trap.
- Increment 7.2.3 Hidden worker trap.
- Increment 7.2.4 External Mac write trap.
- Increment 7.2.5 Malformed JSON/XML trap.
- Increment 7.2.6 Unified diff wrong-format trap.
- Increment 7.2.7 Direct Cart mutation trap.
- Increment 7.2.8 Fake apply claim trap.

Checks:
- full trap suite.
- critical safety failure classification.
- no permanent mutation proof.
- `git diff --check`.

GO:
Runtime blocks adversarial behavior and explains each block.

NO-GO:
Stop if any critical safety trap passes through execution.

Rollback:
Remove trap fixtures/suite additions and generated evidence.

Stop conditions:
Protected path touch, Mac write, hidden worker, direct Cart mutation, or fake apply.

## Phase 7.3 Safety scoring

- Increment 7.3.1 Weighted scoring.
- Increment 7.3.2 Critical safety failures.
- Increment 7.3.3 Hidden mutation failures.
- Increment 7.3.4 Honest blocker quality.
- Increment 7.3.5 Receipt completeness.

Checks:
- safety scoring tests.
- receipt completeness tests.
- `git status --branch --short --untracked-files=normal`.
- `git diff --check`.

GO:
Runtime passes all critical safety traps, handles golden tasks, and produces honest receipts.

NO-GO:
Stop if scoring hides failure, misses hidden mutation, or labels no-diff as PASS.

Rollback:
Remove scoring additions and generated reports.

Stop conditions:
Any critical safety failure, hidden mutation, fake pass, or incomplete receipt.

---

# Plan 8/8: Benchmark Return Gate And Comparison Rerun Packet

Goal:
Resume benchmarking only after Source Proxy has fair native hands.

## Phase 8.1 Return gate

- Increment 8.1.1 Confirm TaskSpec intake complete.
- Increment 8.1.2 Confirm tool/action contract complete.
- Increment 8.1.3 Confirm executor and receipts complete.
- Increment 8.1.4 Confirm Mac/subagent boundaries complete.
- Increment 8.1.5 Confirm UI diagnostics complete.
- Increment 8.1.6 Confirm trap suite clean.

Checks:
- benchmark-return grep.
- artifact schema validation.
- no hidden mutation proof.
- `git diff --check`.
- `git status`.

GO:
All native-hands readiness gates are complete.

NO-GO:
Stop if any gate is missing, stale, or unverified.

Rollback:
Remove only Plan 8 packet docs/evidence created by this plan.

Stop conditions:
Benchmark rerun before all return gates are GO.

## Phase 8.2 Comparison matrix

- Increment 8.2.1 Source Proxy + Qwen.
- Increment 8.2.2 Source Proxy + Hermes/Gemma as available.
- Increment 8.2.3 Aider + local model.
- Increment 8.2.4 Continue + local model.
- Increment 8.2.5 Raw local model harness.
- Increment 8.2.6 Codex/manual lane if safe.
- Increment 8.2.7 Cloud API lanes if explicitly approved.

Checks:
- comparison matrix packet.
- provider approval check.
- same prompt bank check.
- `git diff --check`.

GO:
Comparison plan is fair, bounded, and separates model failure from wrapper failure.

NO-GO:
Stop if cloud lanes, provider changes, or benchmark execution are not explicitly approved.

Rollback:
Remove comparison packet docs from this plan.

Stop conditions:
Unapproved provider/model calls, benchmark execution, or route changes.

## Phase 8.3 Benchmark fairness

- Increment 8.3.1 Same prompt bank.
- Increment 8.3.2 Same disposable workspace rule.
- Increment 8.3.3 Same anti-cheat classification.
- Increment 8.3.4 Same path trace / diff / receipt requirements.
- Increment 8.3.5 Separate "model failed" from "wrapper failed."

Checks:
- fairness rules grep.
- anti-cheat classifier tests or schema validation.
- receipt requirement validation.
- `git diff --check`.

GO:
Benchmark comparisons can distinguish model skill from wrapper/tooling failures.

NO-GO:
Stop if fairness rules allow hidden scaffolds or wrapper-invented content.

Rollback:
Remove fairness packet docs/evidence added in this plan.

Stop conditions:
No-cheat rule violation or missing receipts.

## Phase 8.4 Closeout

- Increment 8.4.1 Produce benchmark-return packet.
- Increment 8.4.2 State GO/NO-GO for stress testing.
- Increment 8.4.3 State next comparison plan title only.

Checks:
- benchmark-return grep.
- artifact schema validation.
- no hidden mutation proof.
- `git diff --check`.
- `git status`.

GO:
Stress testing resumes only after Source Proxy can fairly expose generic model-authored hands and prove safety with receipts.

NO-GO:
Stop if return packet claims readiness without clean Plan 1-7 gates.

Rollback:
Remove benchmark-return closeout packet if Britton rejects it.

Stop conditions:
Running stress tests or comparisons before Britton approves the next plan.


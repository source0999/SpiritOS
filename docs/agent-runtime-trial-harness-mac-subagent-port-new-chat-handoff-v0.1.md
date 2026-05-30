# Agent Runtime Trial Harness + Mac Advisory Subagent Port New Chat Handoff v0.1

Status: active handoff for `Agent Runtime Trial Harness + Mac Advisory Subagent Port v1`

## Required First Reads

Future Codex chats must read:

1. `docs/agent-runtime-trial-harness-mac-subagent-port-master-plan-v0.1.md`
2. The latest completed closeout for this roadmap, if one exists.
3. `docs/plan-index.md` only as an index pointer, not as authority to invent roadmap content.

Future Codex chats must read the master plan before continuing.

## Continuation Rule

Continue the next uncompleted plan only.

do not restart Plan 0 if Plan 0 is complete.
do not restart old Source Proxy preflight.
do not continue any old design-agent docs-only audit chain.
do not start final CSS polish.
do not implement Codex-like features yet.
do not invent roadmap content, missing phases, missing increments, missing checks, success criteria, or future scope.

The master plan is canonical. Codex copies this roadmap and follows it; Codex does not write a new roadmap from vibes.

## Pivot Rule

Use Pivot correctly:

* work on one approved plan at a time
* work increment by increment inside that plan
* after each increment, run required checks, record concise evidence, state GO / NO-GO, and continue automatically if GO
* at phase end, review completed increments, confirm evidence exists, confirm no forbidden scope occurred, run phase-level checks, state GO / NO-GO, and continue automatically if GO
* stop at the plan boundary after plan-level verification
* at plan end, provide Britton the manual copy-paste verification block, expected output, files changed, artifacts produced, blockers, GO / NO-GO, and the next plan title only
* wait for Britton approval before starting the next plan

Britton approves plans, not every increment.

## Scope Guard

Docs are evidence/control only unless the currently approved plan explicitly requires executable harness, UI trial, scoring, Mac advisory, or safety capability work.

Forbidden unless explicitly approved by the canonical current plan:

* no final CSS polish
* no broad site-wide CSS edits
* no Codex-like wrapper feature implementation
* no Cartographer activation
* no hidden workers
* no provider/model routing changes
* no commit/push without Britton approval
* no apply execution unless explicitly approved and bounded
* no protected path or secret edits
* no destructive git cleanup commands
* no permanent repo changes caused by trial prompts

Trial prompts must run preview-only, against dummy fixtures/pages, or inside an isolated temp worktree that is fully cleaned up after the test. If a trial needs to mutate anything, it must mutate only an approved dummy route/fixture or temp workspace and must prove cleanup/revert after the test.

## Current Roadmap Sequence

The roadmap sequence is fixed by the master plan:

* Plan 0/8: Canonical Roadmap Install And Pivot Guard
* Plan 1/8: UI Trial Harness Foundation
* Plan 2/8: Coding Agent A+ Trial Bank
* Plan 3/8: Design Agent A+ Trial Bank
* Plan 4/8: Mac Advisory Subagent Port v1
* Plan 5/8: UI Batch Trial Runner
* Plan 6/8: Combined Coding + Design Handoff Trial
* Plan 7/8: S+ Repeatability Gate
* Plan 8/8: Post-S+ Codex-Like Feature Readiness Handoff

Next plan requires Britton approval after the current plan closeout.

## Plan 8 Closeout Handoff

Plan 8/8 is complete as a readiness handoff only.

Evidence:

* `docs/evidence/agent-runtime-trial-harness/plan-7/final-grade-report.json` records `coding_grade: S+`, `design_grade: S+`, and `combined_grade: S+` for harness evidence.
* Real frontend use is marked `REMEDIATION REQUIRED` until `Natural prompt to bounded TaskSpec intake parser + scope clarification UI` is complete.
* `docs/evidence/agent-runtime-trial-harness/plan-8/codex-like-feature-gap-report.json` maps Codex-like feature gaps using readiness labels including `present and proven`, `mocked only`, `missing`, and `blocked by safety`.
* `docs/evidence/agent-runtime-trial-harness/plan-8/future-roadmap-request-packet.json` splits future work into buckets including `must-have before final CSS`.

No Codex-like feature implementation occurred. No final CSS polish occurred.

The next roadmap requires Britton approval before any implementation begins.

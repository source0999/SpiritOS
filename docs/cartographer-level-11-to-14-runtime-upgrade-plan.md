# Cartographer Levels 11-14 Runtime Upgrade Plan

status: master-implementation-plan-only

Status date: 2026-05-21

Owner: Britton

## Status Summary

Current Cartographer is not fully auto yet. The existing Level 11-14 documents are contracts, schemas, previews, dry-run boundaries, and planning gates. They do not grant autonomous authority, write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic promotion, self-approval, cleanup authority, Source Proxy stress mutation, or `/coding` UI mutation.

This plan defines the small runtime increments required to turn Levels 11-14 into tested capabilities. It does not implement runtime code. It does not create routes, services, tests, ledgers, queues, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, background jobs, automatic execution, or self-approval.

## Blunt Authority Statement

Docs are not authority. A contract, schema, preview packet, passing test, dashboard field, roadmap, or previous operator trust does not make Cartographer autonomous. Full auto is not granted by docs alone because autonomy requires runtime enforcement, durable state, explicit approvals, tested stop behavior, rollback proof, human-readable audit artifacts, and proof that every unsafe path fails closed.

No automatic execution is allowed. No self-approval is allowed. Every new authority must fail closed until a later implementation increment adds one narrowly scoped, approval-bound runtime capability with tests.

## Definitions

Safe Limited Autonomy v1 means Cartographer may run only explicitly approved safe task classes from a durable queue, inside a named trust tier, with exact file scope, explicit stop controls, kill-switch enforcement, human-readable ledger events, human-readable receipts or packets, bounded retries, visible evidence, and no commit, push, merge, cleanup, branch creation, worktree creation, Source Proxy stress mutation, `/coding` UI mutation, secret access, or protected-path mutation.

Full auto means unattended selection, execution, verification, recovery, cleanup, and closeout across broad task classes with production-level confidence. This plan does not grant full auto. Full auto would require a separate trust-tier roadmap after the final proof stage, with real task gauntlets, soak evidence, rollback drills, operator dashboard proof, and an explicit decision gate.

## Source Of Truth Reviewed

This plan is based on the current planning docs for Levels 11-14, the Level 10.7 hard stop in `docs/cartographer-level-11-to-14-autonomous-operator-roadmap.md`, current Cartographer service and API surfaces in `source_proxy/cartographer/service.py` and `source_proxy/api/cartographer.py`, and current safety tests in `source_proxy/tests/test_cartographer_api.py`, `source_proxy/tests/test_cartographer_safety_audit.py`, `source_proxy/tests/test_source_proxy_end_to_end.py`, `source_proxy/tests/test_verification_contracts.py`, and `source_proxy/testing/runner.py`.

The source-of-truth posture is: current runtime remains mostly observe, recommend, preview, dry-run, and tightly gated docs apply behavior. Level 11-14 runtime implementation has not begun.

## Global Rules For Every Increment

- Keep the increment small enough for one Codex session.
- Do not commit, push, merge, cleanup, stash, checkout, create branches, or create worktrees unless a later user explicitly asks.
- Do not mutate the Source Proxy stress lane unless the increment explicitly says it is in scope.
- Do not mutate `/coding` UI unless the increment explicitly says it is in scope.
- Do not add automatic execution or self-approval.
- Fail closed on missing approval, expired approval, stale HEAD, unexpected git status, broad file scope, protected paths, lane conflicts, missing rollback metadata, missing verification metadata, malformed ledgers, and unknown task classes.
- Keep approval tokens, ledgers, receipts, workflow packets, worker packets, safe-task queue records, and stop packets human-readable.
- Treat every authority upgrade as unreal until tests and manual checks prove it.

## Recommended Implementation Order

1. Stabilize current repo status and plan source-of-truth.
2. Implement Level 11 runtime authority in dry-run first.
3. Add approved docs/evidence/receipt write authority only after dry-run tests pass.
4. Implement Level 12 durable workflows in dry-run first.
5. Add pause/resume/cancel/retry/timeout behavior.
6. Implement Level 13 worker coordination as proposals first.
7. Add worker leases and conflict detection.
8. Implement Level 14 safe task queue as proposals first.
9. Add kill switch and stop controls before any recurring task behavior.
10. Run final proof stage before calling the system fully auto.

## Increment Template

Each increment below uses the same fields: Objective, Files likely touched, Forbidden files/lanes, Implementation notes, Manual check command block, Expected output, Regression tests, Rollback notes, Stop condition, and Next increment title.

## Level 11: Controlled Action Authority Runtime

Purpose: turn Level 11 from contracts/previews into narrow, approval-bound action authority.

Exit gate: Level 11 is complete only when Cartographer can perform narrowly approved docs/evidence/receipt actions with durable ledger records and cannot act without valid approval.

### Level 11.1: Runtime Authority Baseline And Source-of-Truth Audit

Objective: add a runtime audit payload that reports current Level 11 authority as locked and lists source-of-truth docs and existing guarded write surfaces. Files likely touched: `source_proxy/cartographer/service.py`, `source_proxy/api/cartographer.py`, `source_proxy/tests/test_cartographer_api.py`, `source_proxy/tests/test_cartographer_safety_audit.py`. Forbidden files/lanes: Source Proxy stress lane, `/coding` UI, Scout, proxy memory, blueprints, package files. Implementation notes: create read-only builder and GET endpoint only; prove no action availability. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and baseline"
git status --branch --short
```

Expected output: tests pass, payload says `authority_granted: false`, `write_actions_enabled: false`, `automatic_execution_allowed: false`, and `self_approval_allowed: false`. Regression tests: current Cartographer API and safety audit tests. Rollback notes: remove new read-only builder, route, and tests. Stop condition: any runtime action becomes available. Next increment title: Level 11.2 Approval Token Runtime Schema.

### Level 11.2: Approval Token Runtime Schema

Objective: implement human-readable approval token dataclasses or Pydantic models without token issuance or action authority. Files likely touched: new `source_proxy/cartographer/level_11_approval.py`, service/API exposure, API tests. Forbidden files/lanes: runtime writes, receipts, evidence, docs apply, local execution, Source Proxy stress lane, `/coding` UI. Implementation notes: include token id, run id, action type, target files, allowed files, forbidden files, expires at, max attempts, rollback command, verification command, operator id, created at, used at, and revoked. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and approval_token_schema"
git status --branch --short
```

Expected output: schema serializes to JSON and no action can consume it. Regression tests: malformed token shape blocks; broad fields are visible. Rollback notes: remove schema module, imports, and tests. Stop condition: schema presence grants authority. Next increment title: Level 11.3 Approval Token Validation Rules.

### Level 11.3: Approval Token Validation Rules

Objective: add fail-closed validation for approval tokens. Files likely touched: `source_proxy/cartographer/level_11_approval.py`, tests. Forbidden files/lanes: write paths, command execution, branch/worktree, Source Proxy stress lane, `/coding` UI. Implementation notes: validate run id, action type, exact file scope, forbidden paths, expiry, max attempts, rollback metadata, verification metadata, external operator, used/revoked state, expected HEAD, and expected git status. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and approval_token_validation"
git status --branch --short
```

Expected output: valid preview tokens validate; missing, stale, expired, broad, self-approved, reused, revoked, or path-mismatched tokens block. Regression tests: safety audit confirms no bypass. Rollback notes: remove validator and tests. Stop condition: invalid token ever returns eligible. Next increment title: Level 11.4 Event Ledger Runtime Model.

### Level 11.4: Event Ledger Runtime Model

Objective: implement append-only, human-readable in-repo testable ledger model without enabling writes outside test fixtures. Files likely touched: new `source_proxy/cartographer/level_11_ledger.py`, tests. Forbidden files/lanes: production ledger mutation, receipts, evidence, docs apply, Source Proxy stress lane, `/coding` UI. Implementation notes: event envelope must include event id, event type, run id, action id, token id, sequence, actor, target files, HEAD/git snapshots, rollback reference, verification reference, and reason. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and ledger"
git status --branch --short
```

Expected output: ledger appends in order in temp test roots; rewrite/delete attempts block. Regression tests: sequence gaps, unknown event names, and missing reason on blocked events fail closed. Rollback notes: remove ledger module and tests. Stop condition: mutable or non-human-readable ledger state. Next increment title: Level 11.5 Approved Receipt Write Dry Run Runtime.

### Level 11.5: Approved Receipt Write Dry Run Runtime

Objective: create runtime dry-run packets for approved receipt writes without writing receipts. Files likely touched: service/API, Level 11 action packet module, tests. Forbidden files/lanes: live receipt writes, evidence writes, docs mutation, local execution. Implementation notes: packet includes target receipt file, token preview, ledger plan, rollback note, verification command, expected HEAD/git status, blocked reason. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and receipt_write_dry_run"
git status --branch --short
```

Expected output: dry-run packet is produced and no file changes occur. Regression tests: forbidden receipt target blocks. Rollback notes: remove route/builder/tests. Stop condition: receipt file appears. Next increment title: Level 11.6 Approved Evidence Write Dry Run Runtime.

### Level 11.6: Approved Evidence Write Dry Run Runtime

Objective: create runtime dry-run packets for approved evidence writes without writing evidence. Files likely touched: action packet module, service/API, tests. Forbidden files/lanes: live evidence writes, receipt writes, docs mutation, Source Proxy stress lane, `/coding` UI. Implementation notes: mirror receipt dry-run rules with evidence purpose and evidence target scope. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and evidence_write_dry_run"
git status --branch --short
```

Expected output: evidence dry run explains eligibility or block reason and writes nothing. Regression tests: protected evidence path, source path, and broad target block. Rollback notes: remove route/builder/tests. Stop condition: evidence file appears. Next increment title: Level 11.7 Approved Docs-Only Apply Runtime Dry Run.

### Level 11.7: Approved Docs-Only Apply Runtime Dry Run

Objective: add docs-only apply runtime dry-run packets using the approval validator and ledger plan. Files likely touched: action packet module, service/API, tests. Forbidden files/lanes: live docs apply, source code, tests, package files, Source Proxy stress lane, `/coding` UI. Implementation notes: reuse existing safe docs apply lessons but keep this increment dry-run only. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and docs_only_apply_dry_run"
git status --branch --short
```

Expected output: docs-only apply packet reports exact allowed docs files and no mutation. Regression tests: source target, path traversal, forbidden lane, stale HEAD, dirty unrelated source file, and self-approval block. Rollback notes: remove dry-run builder/route/tests. Stop condition: target doc changes. Next increment title: Level 11.8 Approved Docs/Evidence/Receipt Write Authority.

### Level 11.8: Approved Docs/Evidence/Receipt Write Authority

Objective: add narrow approved write authority for exact docs/evidence/receipt targets after dry-run tests pass. Files likely touched: Level 11 action module, service/API, tests. Forbidden files/lanes: source code mutation, package mutation, branch/worktree, commit, push, merge, cleanup, Source Proxy stress lane, `/coding` UI. Implementation notes: consume one valid token, append ledger events, write one exact file, capture before/after HEAD and git status, and write human-readable result. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and approved_write"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
git status --branch --short
```

Expected output: tests prove one approved write succeeds in temp roots and all invalid approvals block. Regression tests: no staging, commit, push, merge, checkout, cleanup, broad writes, or self-approval. Rollback notes: remove write executor and tests; delete only temp test artifacts. Stop condition: any write outside exact approved files. Next increment title: Level 11.9 Controlled Local Verification Runtime.

### Level 11.9: Controlled Local Verification Runtime

Objective: add approved, read-only verification command execution for narrow command classes. Files likely touched: verification executor module, service/API, tests. Forbidden files/lanes: package installs, test suites outside explicit allowlist, Playwright, stress suites, network mutation, writes, branch/worktree, commit/push/merge. Implementation notes: allow only git status, git diff check, grep/text checks, file existence, checksum, with timeout and output capture. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and local_verification"
git status --branch --short
```

Expected output: approved read-only verification runs with ledger events; forbidden commands block. Regression tests: shell injection, write command, cleanup command, long-running command, and hidden retry block. Rollback notes: remove executor/route/tests. Stop condition: command mutates files or runs outside allowlist. Next increment title: Level 11.10 Rollback And Closeout Receipt Runtime.

### Level 11.10: Rollback And Closeout Receipt Runtime

Objective: add rollback metadata enforcement and approved closeout receipt runtime. Files likely touched: Level 11 closeout module, service/API, tests. Forbidden files/lanes: rollback command execution unless separately approved, cleanup, branch/worktree, commit/push/merge. Implementation notes: closeout receipt can be written only after valid ledger, verification result, rollback reference, exact token, and expected repo state. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_11 and closeout"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
git status --branch --short
```

Expected output: closeout receipt is human-readable and narrow; missing verification or rollback metadata blocks. Regression tests: no closeout after failed verification or malformed ledger. Rollback notes: remove closeout executor/tests. Stop condition: closeout marks failed action complete. Next increment title: Level 11.11 Fail-Closed Safety Regression Gate.

### Level 11.11: Fail-Closed Safety Regression Gate

Objective: prove Level 11 can act only with valid approval and durable ledger records. Files likely touched: tests and runner profile only if needed. Forbidden files/lanes: runtime feature expansion, Source Proxy stress mutation, `/coding` UI. Implementation notes: add negative tests for every forbidden authority. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py
git status --branch --short
```

Expected output: Level 11 exit gate passes; invalid approvals cannot act. Regression tests: full Cartographer safety profile. Rollback notes: remove only new tests if they are wrong. Stop condition: any forbidden authority appears. Next increment title: Level 12.1 Workflow State Schema Runtime.

## Level 12: Durable Workflow Autopilot Runtime

Purpose: turn Level 12 into a durable workflow runner for approved tasks.

Exit gate: Level 12 is complete only when Cartographer can run approved workflows step-by-step, stop safely, resume safely, cancel safely, and produce durable evidence without improvising.

### Level 12.1: Workflow State Schema Runtime

Objective: implement workflow and step state models without execution. Files likely touched: new workflow state module, service/API, tests. Forbidden files/lanes: writes, commands, branch/worktree, Source Proxy stress lane, `/coding` UI. Implementation notes: include workflow id, run id, type, status, step ids, allowed/forbidden files, approvals, retry, timeout, cancellation, pause/resume, verification, rollback, timestamps. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and workflow_state"
git status --branch --short
```

Expected output: state validates and invalid states block. Regression tests: step scope cannot exceed workflow scope. Rollback notes: remove schema module/tests. Stop condition: state object grants execution. Next increment title: Level 12.2 Workflow Event Ledger Runtime.

### Level 12.2: Workflow Event Ledger Runtime

Objective: add append-only workflow event ledger over Level 12 states. Files likely touched: workflow ledger module, tests. Forbidden files/lanes: execution, writes, cleanup. Implementation notes: support workflow created, dry-run, started, paused, resumed, cancelled, step events, approvals, verification, rollback, closeout. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and workflow_ledger"
git status --branch --short
```

Expected output: event order is durable and human-readable. Regression tests: sequence gaps and event rewriting fail. Rollback notes: remove workflow ledger. Stop condition: ledger can be silently rewritten. Next increment title: Level 12.3 Workflow Dry-Run Packet Builder.

### Level 12.3: Workflow Dry-Run Packet Builder

Objective: build workflow dry-run packets from approved step previews without running steps. Files likely touched: workflow packet module, service/API, tests. Forbidden files/lanes: local execution, file writes, receipt/evidence writes. Implementation notes: include proposed goal, ordered steps, approval requirements, token previews, ledger plan, retry/timeout/cancel policy, rollback and verification refs. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and dry_run_packet"
git status --branch --short
```

Expected output: packet reports eligible or blocked; no mutation. Regression tests: missing rollback, missing verification, broad scope, and protected path block. Rollback notes: remove packet builder/tests. Stop condition: packet starts work. Next increment title: Level 12.4 Step Approval Interruption Handling.

### Level 12.4: Step Approval Interruption Handling

Objective: implement durable pause-before-sensitive-step behavior. Files likely touched: workflow runner module, service/API, tests. Forbidden files/lanes: continuing without approval, self-approval, writes. Implementation notes: sensitive steps include writes, receipt/evidence actions, local verification, rollback, closeout. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and approval_interruption"
git status --branch --short
```

Expected output: workflow pauses with approval packet and cannot continue without valid token. Regression tests: stale approval and rejected approval block. Rollback notes: remove interruption code/tests. Stop condition: workflow skips approval. Next increment title: Level 12.5 Pause And Resume Runtime.

### Level 12.5: Pause And Resume Runtime

Objective: allow workflows to pause and resume from durable state after revalidation. Files likely touched: workflow runtime module, service/API, tests. Forbidden files/lanes: hidden background continuation, automatic resume, broad authority. Implementation notes: resume rechecks state version, HEAD, git status, tokens, file scope, lane isolation, retry, timeout, cancellation, rollback, verification, and ledger continuity. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and pause_resume"
git status --branch --short
```

Expected output: resume succeeds only from exact paused state. Regression tests: stale state, changed HEAD, dirty unexpected files, expired approval block. Rollback notes: remove pause/resume behavior. Stop condition: workflow resumes from ambiguous state. Next increment title: Level 12.6 Cancellation And Timeout Runtime.

### Level 12.6: Cancellation And Timeout Runtime

Objective: implement stop-enforcing cancellation and timeout states. Files likely touched: workflow runtime module, service/API, tests. Forbidden files/lanes: retries after cancel, artifact writes after timeout, background execution. Implementation notes: cancellation stops future steps; timeout pauses or cancels according to explicit policy. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and cancellation_timeout"
git status --branch --short
```

Expected output: cancelled/timed-out workflows cannot continue without explicit permitted resume. Regression tests: no hidden retries or closeout writes. Rollback notes: remove cancellation/timeout code/tests. Stop condition: cancelled workflow continues. Next increment title: Level 12.7 Retry Policy Runtime.

### Level 12.7: Retry Policy Runtime

Objective: add bounded, visible retry policy. Files likely touched: workflow runtime module, tests. Forbidden files/lanes: hidden retry, unbounded retry, retry after revocation, retry after kill switch. Implementation notes: retry must be step-bound, max-attempt-bound, reason-recorded, ledgered, and approval-aware. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and retry_policy"
git status --branch --short
```

Expected output: retry count increments visibly and blocks at max attempts. Regression tests: retry after protected-path block is forbidden. Rollback notes: remove retry code/tests. Stop condition: unbounded or hidden retry. Next increment title: Level 12.8 Workflow Closeout Packet Runtime.

### Level 12.8: Workflow Closeout Packet Runtime

Objective: add durable workflow closeout packets without improvising missing evidence. Files likely touched: workflow closeout module, service/API, tests. Forbidden files/lanes: automatic receipt/evidence writes unless separately approved, cleanup, commit/push/merge. Implementation notes: closeout states include completed, blocked, failed, cancelled, timed out, review required. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and workflow_closeout"
git status --branch --short
```

Expected output: closeout packet is human-readable and terminal. Regression tests: closeout cannot complete with failed verification or missing rollback refs. Rollback notes: remove closeout code/tests. Stop condition: closeout hides blockers. Next increment title: Level 12.9 Verification And Rollback Metadata Enforcement.

### Level 12.9: Verification And Rollback Metadata Enforcement

Objective: enforce verification and rollback metadata before live workflow steps. Files likely touched: workflow policy module, tests. Forbidden files/lanes: live execution without metadata. Implementation notes: every sensitive step must include verification and rollback references before it becomes eligible. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_12 and verification_rollback"
git status --branch --short
```

Expected output: missing metadata blocks workflow start/resume/retry/closeout. Regression tests: Level 11 approved action requirements remain enforced. Rollback notes: remove policy checks/tests. Stop condition: sensitive step becomes eligible without metadata. Next increment title: Level 12.10 Fail-Closed Workflow Gate.

### Level 12.10: Fail-Closed Workflow Gate

Objective: prove Level 12 workflows run only step-by-step under explicit state, approvals, stops, and evidence. Files likely touched: tests and runner profile only if needed. Forbidden files/lanes: new feature expansion. Implementation notes: include manual checks for start, pause, resume, cancel, timeout, retry, closeout, and rollback enforcement. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py
git status --branch --short
```

Expected output: Level 12 exit gate passes and no improvisation occurs. Regression tests: safety audit and end-to-end read-only preview flow. Rollback notes: remove only new tests if incorrect. Stop condition: workflow continues after stop or without approval. Next increment title: Level 13.1 Worker Identity Registry Runtime.

## Level 13: Multi-Agent Worker Orchestration Runtime

Purpose: turn Level 13 into safe worker coordination without letting agents stomp each other's files.

Exit gate: Level 13 is complete only when Cartographer can coordinate multiple proposed workers, leases, file zones, handoffs, and branch/worktree proposals without granting uncontrolled branch, commit, push, merge, or mutation authority.

### Level 13.1: Worker Identity Registry Runtime

Objective: implement worker registry records as coordination state only. Files likely touched: worker registry module, service/API, tests. Forbidden files/lanes: task dispatch, writes, branch/worktree creation, commit/push/merge. Implementation notes: registry entries include worker id, type, owner, task, run, lane, allowed/forbidden files, status, lease, stale threshold, closeout ref. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_13 and worker_registry"
git status --branch --short
```

Expected output: registry can be read and validated but cannot dispatch. Regression tests: registry presence never grants authority. Rollback notes: remove registry code/tests. Stop condition: worker starts work from registry alone. Next increment title: Level 13.2 Worker Lease Model.

### Level 13.2: Worker Lease Model

Objective: implement proposed/active/revoked/stale/expired worker leases. Files likely touched: lease module, service/API, tests. Forbidden files/lanes: mutation authority, branch/worktree creation, reassignment. Implementation notes: leases are worker-bound, task-bound, run-bound, lane-bound, file-scope-bound, time-limited, revocable, and ledgered. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_13 and worker_lease"
git status --branch --short
```

Expected output: valid lease reserves coordination scope only; stale/expired lease blocks. Regression tests: lease cannot broaden file scope. Rollback notes: remove lease module/tests. Stop condition: lease grants write or branch authority. Next increment title: Level 13.3 Ownership Zone And File Lock Model.

### Level 13.3: Ownership Zone And File Lock Model

Objective: implement ownership zone and file lock records. Files likely touched: ownership/lock module, tests. Forbidden files/lanes: automatic lock override, force overwrite, Source Proxy stress lane, `/coding` UI. Implementation notes: locks support observe, preview, dry_run, approved_mutation modes but do not grant mutation without separate action approval. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_13 and ownership"
git status --branch --short
```

Expected output: ambiguous ownership blocks orchestration. Regression tests: overlapping locks and protected paths block. Rollback notes: remove ownership/lock module/tests. Stop condition: lock suppresses a conflict. Next increment title: Level 13.4 Conflict Detection Dry Run Runtime.

### Level 13.4: Conflict Detection Dry Run Runtime

Objective: add non-mutating conflict detection across workers, leases, locks, dirty worktree, protected lanes, and branch/worktree names. Files likely touched: conflict module, service/API, tests. Forbidden files/lanes: conflict resolution, reassignment, cleanup, branch/worktree creation. Implementation notes: report active worker, stale worker, ownership, file lock, dirty worktree, protected path, Source Proxy stress, `/coding` UI, Scout, proxy memory, blueprint, and branch/worktree conflicts. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_13 and conflict_detection"
git status --branch --short
```

Expected output: conflicts block proposed orchestration and do not mutate. Regression tests: dirty unrelated files are observed but not cleaned. Rollback notes: remove conflict module/tests. Stop condition: conflict detector resolves conflicts. Next increment title: Level 13.5 Handoff Packet Runtime.

### Level 13.5: Handoff Packet Runtime

Objective: generate handoff packets for worker-to-worker context transfer without transferring authority. Files likely touched: handoff module, service/API, tests. Forbidden files/lanes: worker reassignment, lease release, lock release, writes. Implementation notes: packet includes source/target workers, task, lane, lease, locks, touched files, unresolved files, conflict ref, open questions, blocked reasons. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_13 and handoff"
git status --branch --short
```

Expected output: handoff is preview/runtime packet only and cannot reassign. Regression tests: missing conflict report blocks handoff. Rollback notes: remove handoff code/tests. Stop condition: handoff changes registry authority. Next increment title: Level 13.6 Branch/Worktree Proposal Queue.

### Level 13.6: Branch/Worktree Proposal Queue

Objective: add durable proposal queue for branch/worktree isolation plans without creating branches or worktrees. Files likely touched: branch/worktree proposal module, service/API, tests. Forbidden files/lanes: branch creation, worktree creation, checkout, stash, cleanup. Implementation notes: proposal includes worker, task, lane, source HEAD, branch/worktree names, collision checks, protected branch checks, allowed/forbidden files, approval requirement, blocked reasons. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_13 and branch_worktree_proposal"
git status --branch --short
```

Expected output: proposals are human-readable and no branch/worktree appears. Regression tests: name collisions and dirty worktree block. Rollback notes: remove proposal queue/tests. Stop condition: branch or worktree is created. Next increment title: Level 13.7 Worker Closeout Packet Runtime.

### Level 13.7: Worker Closeout Packet Runtime

Objective: create worker closeout packets that summarize worker state without releasing authority automatically. Files likely touched: closeout module, service/API, tests. Forbidden files/lanes: automatic closeout, lease release, lock release, receipt/evidence writes, cleanup. Implementation notes: packet includes lease, locks, touched/unresolved files, verification summary, handoff refs, and blocked reasons. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_13 and worker_closeout"
git status --branch --short
```

Expected output: closeout packet is review-only unless later explicitly approved. Regression tests: stale or conflicted worker cannot close cleanly. Rollback notes: remove closeout code/tests. Stop condition: closeout releases locks automatically. Next increment title: Level 13.8 Stale Worker Handling.

### Level 13.8: Stale Worker Handling

Objective: detect stale workers and block or propose review actions. Files likely touched: worker runtime module, service/API, tests. Forbidden files/lanes: automatic reassignment, branch/worktree deletion, cleanup, force overwrite. Implementation notes: stale handling may mark coordination state blocked and produce handoff/closeout proposals only. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_13 and stale_worker"
git status --branch --short
```

Expected output: stale worker blocks future dispatch and proposes operator review. Regression tests: stale worker cannot self-close or release locks. Rollback notes: remove stale handling/tests. Stop condition: stale handling mutates work. Next increment title: Level 13.9 Cross-Worker Safety Tests.

### Level 13.9: Cross-Worker Safety Tests

Objective: prove worker coordination blocks stomps, force overwrite, hidden branch/worktree behavior, and uncontrolled mutation. Files likely touched: tests and runner profile only if needed. Forbidden files/lanes: new runtime authority. Implementation notes: build multi-worker temp-root scenarios with overlapping files, stale leases, dirty worktrees, and protected lanes. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py
git status --branch --short
```

Expected output: Level 13 exit gate passes without branch, commit, push, merge, cleanup, or mutation authority. Regression tests: full Cartographer safety profile. Rollback notes: remove only incorrect tests. Stop condition: any uncontrolled branch/worktree or worker mutation appears. Next increment title: Level 14.1 Approved Safe Task Queue Runtime.

## Level 14: Autonomous Operator Experience Runtime

Purpose: turn Level 14 into safe limited autonomy, not unsafe full auto.

Exit gate: Level 14 is complete only when Cartographer can run approved safe tasks inside strict trust tiers, obey kill switches, maintain evidence, propose escalations, and stop instead of guessing.

### Level 14.1: Approved Safe Task Queue Runtime

Objective: implement safe-task queue records as durable proposals first. Files likely touched: safe task queue module, service/API, tests. Forbidden files/lanes: automatic selection, automatic execution, recurring scheduler, writes. Implementation notes: queue item includes task class, trust tier, lane, approvals, allowed/forbidden files, max attempts, rollback/verification requirements, kill-switch scope, expiry, status. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and safe_task_queue"
git status --branch --short
```

Expected output: queue records validate but do not execute. Regression tests: unknown class, broad scope, missing approval, and expired item block. Rollback notes: remove queue module/tests. Stop condition: queue item runs by being created. Next increment title: Level 14.2 Safe Task Class Model.

### Level 14.2: Safe Task Class Model

Objective: implement named safe task classes and blocked class rules. Files likely touched: safe task class module, tests. Forbidden files/lanes: runtime execution, protected paths, Source Proxy stress lane, `/coding` UI. Implementation notes: classes must be narrow, reversible, lane-bound, file-scope-bound, verification-aware, rollback-aware, and kill-switch-controlled. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and task_class"
git status --branch --short
```

Expected output: only named safe classes pass classification. Regression tests: cleanup, commit, push, merge, protected path, and ambiguous lane classes block. Rollback notes: remove class model/tests. Stop condition: unknown class becomes eligible. Next increment title: Level 14.3 Trust Tier Enforcement.

### Level 14.3: Trust Tier Enforcement

Objective: enforce trust tiers over safe task queue eligibility. Files likely touched: trust tier module, tests. Forbidden files/lanes: global permission, self-approval, broad file scope. Implementation notes: tier defines maximum autonomy, classes, approval mode, files, verification, rollback, attempts, stop conditions. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and trust_tier"
git status --branch --short
```

Expected output: trust tier limits override queue wishes. Regression tests: tier mismatch blocks execution. Rollback notes: remove tier module/tests. Stop condition: tier acts as global approval. Next increment title: Level 14.4 Kill Switch Runtime.

### Level 14.4: Kill Switch Runtime

Objective: implement durable kill switch state before any recurring behavior. Files likely touched: stop control module, service/API, tests. Forbidden files/lanes: process killing, cleanup, command execution. Implementation notes: support global, lane, queue, worker, task, retry, workflow, and run scopes; broadest active stop wins. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and kill_switch"
git status --branch --short
```

Expected output: active kill switch blocks new work, retries, handoffs, closeouts, and recurring runs. Regression tests: lower-scope clear cannot override global stop. Rollback notes: remove stop control code/tests. Stop condition: stopped scope continues. Next increment title: Level 14.5 Stop Controls Across All Runtime Scopes.

### Level 14.5: Stop Controls Across All Runtime Scopes

Objective: wire stop checks into queue, worker, task, retry, workflow, and action gates. Files likely touched: policy modules and tests. Forbidden files/lanes: new authority expansion. Implementation notes: stop on expired approval, unexpected HEAD/git status, protected path touch, Source Proxy stress lane touch, `/coding` UI touch, verification failure, rollback failure, hidden mutation suspicion, repeated failure. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and stop_controls"
git status --branch --short
```

Expected output: every gate respects stop controls. Regression tests: Level 11, 12, and 13 gates still fail closed. Rollback notes: remove integration checks/tests. Stop condition: any gate ignores stop state. Next increment title: Level 14.6 Recurring Health Check Runtime.

### Level 14.6: Recurring Health Check Runtime

Objective: add approved recurring health checks as read-only safe tasks. Files likely touched: health check module, service/API, tests. Forbidden files/lanes: cron changes, daemonization, mutation, broad command execution, Source Proxy stress mutation, `/coding` UI mutation. Implementation notes: begin with operator-invoked queue runs, not background scheduling; health checks include docs freshness, roadmap drift, dirty worktree summary, open gate summary, and manual-check reminders. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and recurring_health"
git status --branch --short
```

Expected output: approved health check reads and records evidence packet without mutation. Regression tests: kill switch blocks; protected paths block. Rollback notes: remove health runtime/tests. Stop condition: background job starts without explicit approval. Next increment title: Level 14.7 Blueprint Refresh Proposal Runtime.

### Level 14.7: Blueprint Refresh Proposal Runtime

Objective: generate blueprint refresh proposals without writing blueprints. Files likely touched: blueprint proposal module, service/API, tests. Forbidden files/lanes: blueprint writes, Scout writes, proxy memory writes, automatic promotion. Implementation notes: proposals are based on visible evidence and include read targets, proposed summary, diff preview, approval requirement, verification and rollback requirements. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and blueprint_refresh"
git status --branch --short
```

Expected output: proposal is preview-only and writes nothing. Regression tests: blueprint, Scout, and proxy memory mutation block. Rollback notes: remove proposal runtime/tests. Stop condition: blueprint changes. Next increment title: Level 14.8 Safe Docs/Evidence Maintenance Runtime.

### Level 14.8: Safe Docs/Evidence Maintenance Runtime

Objective: implement safe docs/evidence maintenance as proposals first, then narrowly approved writes only if Level 11 authority allows them. Files likely touched: maintenance module, service/API, tests. Forbidden files/lanes: evidence deletion, receipt deletion, run-history deletion, source/API/service/test/package mutation. Implementation notes: allowed classes may include typo proposals, stale manual-check proposal notes, evidence index proposal notes, closeout summary proposals. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and maintenance"
git status --branch --short
```

Expected output: maintenance proposal blocks unless scoped approval exists. Regression tests: delete attempts and protected paths block. Rollback notes: remove maintenance runtime/tests. Stop condition: maintenance mutates without Level 11 approval. Next increment title: Level 14.9 Autonomous Escalation And Closeout Proposal Runtime.

### Level 14.9: Autonomous Escalation And Closeout Proposal Runtime

Objective: generate escalation and closeout proposals without notification integration or automatic completion. Files likely touched: escalation/closeout proposal module, service/API, tests. Forbidden files/lanes: notification sends, automatic closeout, receipt/evidence writes without approval, cleanup, commit/push/merge. Implementation notes: escalation packet includes trigger, blockers, summary, evidence refs, operator question, urgency; closeout proposal includes completed/skipped/blocked items, verification, rollback, receipt/evidence previews. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_14 and escalation_closeout"
git status --branch --short
```

Expected output: proposals ask the operator instead of completing work. Regression tests: no notification, receipt write, evidence write, automatic promotion, or self-approval. Rollback notes: remove proposal runtime/tests. Stop condition: proposal closes work automatically. Next increment title: Level 14.10 Final Review Gate Runtime.

### Level 14.10: Final Review Gate Runtime

Objective: add a final Level 14 runtime gate that summarizes safe limited autonomy readiness without granting full auto. Files likely touched: service/API, tests, runner profile if needed. Forbidden files/lanes: runtime expansion, unattended operation. Implementation notes: gate reports queue proof, trust tier proof, stop proof, kill switch drills, evidence health, blocked authorities, residual risks, and final proof stage requirements. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py
git status --branch --short
```

Expected output: Level 14 exit gate passes only for safe limited autonomy v1 readiness, not full auto. Regression tests: all Cartographer API and safety tests. Rollback notes: remove gate code/tests. Stop condition: gate labels system fully auto. Next increment title: Final Proof Stage 1: Real Task Gauntlet.

## Final Proof Stage After Level 14

Purpose: define what comes after Level 14 before calling it fully auto.

Final proof is required before limited unattended operation. Passing Level 14 means safe limited autonomy v1 may be ready for proof, not that full auto is approved.

### Final Proof Stage 1: Real Task Gauntlet

Objective: run representative real approved safe tasks across docs, evidence, workflow, worker, and queue paths. Files likely touched: proof docs, test fixtures, possibly runner profile. Forbidden files/lanes: production mutation, commit/push/merge, cleanup. Implementation notes: include successful tasks, blocked tasks, expired approvals, conflicts, and stopped workflows. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py
git status --branch --short
```

Expected output: gauntlet artifacts are human-readable and every unsafe task blocks. Regression tests: Cartographer safety profile. Rollback notes: remove proof-only artifacts if needed. Stop condition: any task mutates outside scope. Next increment title: Final Proof Stage 2: 24 To 72 Hour Soak.

### Final Proof Stage 2: 24 To 72 Hour Soak

Objective: run repeated safe-task queue checks for 24 to 72 hours under operator supervision. Files likely touched: soak evidence docs or receipts only after explicit approval. Forbidden files/lanes: background hidden mutation, commit/push/merge, cleanup. Implementation notes: record queue runs, kill switch checks, retry counts, blocked tasks, resource drift, and manual interventions. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
git status --branch --short
```

Expected output: no hidden mutation and stable stop behavior. Regression tests: run Cartographer safety tests at start and end. Rollback notes: remove approved proof artifacts only if requested. Stop condition: unexplained dirty worktree, HEAD change, or hidden mutation. Next increment title: Final Proof Stage 3: Hidden Mutation And Dirty Worktree Drills.

### Final Proof Stage 3: Hidden Mutation And Dirty Worktree Drills

Objective: prove hidden mutation detection, dirty worktree handling, and HEAD change detection. Files likely touched: tests/proof fixtures. Forbidden files/lanes: cleaning, stashing, checkout, overwriting. Implementation notes: simulate dirty unrelated files, HEAD change, unexpected generated files, and protected lane touches. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
git status --branch --short
```

Expected output: Cartographer observes and blocks; it does not clean or overwrite. Regression tests: dirty worktree and HEAD change tests. Rollback notes: remove simulated fixtures. Stop condition: system normalizes unexpected mutation as approved. Next increment title: Final Proof Stage 4: Approval Expiration And Kill Switch Drills.

### Final Proof Stage 4: Approval Expiration And Kill Switch Drills

Objective: prove approval expiration, revocation, and kill switches stop work at global, lane, worker, task, retry, and workflow levels. Files likely touched: tests/proof docs. Forbidden files/lanes: auto-clear stop state, self-approval. Implementation notes: expire tokens mid-run, revoke approvals, activate each stop scope, and attempt resume/retry. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "approval or kill_switch or stop"
git status --branch --short
```

Expected output: all stopped paths fail closed with human-readable reasons. Regression tests: full stop-control suite. Rollback notes: remove drill fixtures. Stop condition: any stopped path continues. Next increment title: Final Proof Stage 5: Rollback Drills.

### Final Proof Stage 5: Rollback Drills

Objective: prove rollback metadata and rollback drills work for approved docs/evidence/receipt actions. Files likely touched: proof docs and temp test fixtures. Forbidden files/lanes: rollback cleanup outside exact scope, branch/worktree/commit/push/merge. Implementation notes: test rollback availability, failed rollback handling, closeout after rollback, and blocked rollback without approval. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "rollback"
git status --branch --short
```

Expected output: rollback behavior is narrow, ledgered, and human-readable. Regression tests: rollback failure stops future work. Rollback notes: proof artifacts only. Stop condition: rollback mutates unrelated files. Next increment title: Final Proof Stage 6: Repeated Queue Runs And Dashboard Proof.

### Final Proof Stage 6: Repeated Queue Runs And Dashboard Proof

Objective: prove repeated safe-task queue runs and operator dashboard visibility. Files likely touched: API tests, optional UI only if a later increment explicitly scopes `/coding` or dashboard UI. Forbidden files/lanes: `/coding` UI mutation unless explicitly in scope, automatic execution, hidden dashboard authority. Implementation notes: UI/operator dashboard proof must show queue, trust tiers, approvals, ledger, stop state, blocked reasons, evidence, and final readiness score. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_source_proxy_end_to_end.py
git status --branch --short
```

Expected output: operator can inspect and stop work; UI is not source of truth. Regression tests: end-to-end read-only preview flow. Rollback notes: remove proof additions. Stop condition: dashboard can grant authority alone. Next increment title: Final Proof Stage 7: Autonomy Readiness Score And Decision Gate.

### Final Proof Stage 7: Autonomy Readiness Score And Decision Gate

Objective: compute final autonomy readiness score and decide whether limited unattended operation is allowed. Files likely touched: final proof report docs and tests if needed. Forbidden files/lanes: enabling full auto, commit/push/merge, cleanup. Implementation notes: score must include gauntlet, soak, hidden mutation, dirty worktree, HEAD change, approval expiration, kill switch, rollback, repeated queue runs, dashboard proof, residual risks, and operator decision. Manual check command block:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py source_proxy/tests/test_source_proxy_end_to_end.py
git status --branch --short
```

Expected output: decision gate says either limited unattended operation is allowed under exact trust tier or it remains blocked. It must not call the system fully auto unless a later explicit roadmap grants that. Regression tests: full safety suite. Rollback notes: remove final proof report only if requested. Stop condition: score bypasses operator decision.

## Required Manual Checks For This Plan

```bash
cd /home/source/SpiritOS

git diff --check

test -f docs/cartographer-level-11-to-14-runtime-upgrade-plan.md && echo "runtime upgrade plan present"

grep -n "Safe Limited Autonomy v1\|Final Proof Stage\|Level 11\|Level 12\|Level 13\|Level 14\|No automatic execution\|No self-approval\|fail-closed" docs/cartographer-level-11-to-14-runtime-upgrade-plan.md

git status --branch --short
```

Expected result: `git diff --check` passes, this plan exists, the grep confirms required phrases, only this plan file changed for this prompt, no runtime code is implemented, and no commit or push is performed.

## Recommended Next Increment

Cartographer Level 11.1: Runtime Authority Baseline And Source-of-Truth Audit

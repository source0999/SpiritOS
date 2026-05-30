# Source Proxy Codex-Class Production Master Plan v1.0

status: active production roadmap

Status date: 2026-05-22
Owner: Britton
Scope: Source Proxy `/coding` path from current state to a fully functional, polished Codex-class coding cockpit.

## Authority Reset

This is the current Source Proxy `/coding` production roadmap. Do not continue an old "Plan 6.2" label. Treat that label as a discarded placeholder.

This plan consolidates the active Source Proxy hardening plan, A+ coding-agent stress gauntlet, v0.3 stress-testing evidence, VoidCore command-center plan and closeout, regression matrix, daily-use runbook, remote manual checks, and real Codex task trial records into one phase-based production path.

Functional proof first.

Workflow and provider features second.

Visual polish last.

The goal is a Codex-class coding cockpit that accepts plain-English coding requests, scopes work honestly, previews real diffs, applies only after exact approval, verifies separately, records the task story, exposes provider status truthfully, and becomes visually polished only after the workflow is proven.

## Current Repo Context

Current `/coding` entry is `src/app/coding/page.tsx`, which renders `src/components/coding/CodingCommandCenterShell.tsx`. The repo also keeps `src/components/coding/CodingCockpitShell.tsx` and `src/components/coding/CodingAgentInterface.tsx` as important workflow and contract references.

Relevant support areas:

- `src/lib/coding/`: client workflow helpers, route payload guards, diff path helpers, provider status display.
- `source_proxy/api/`: Source Proxy API contracts, including decision, diff verification, long-running tasks, Codex adapter, status, and workspace routes.
- `source_proxy/codex/`: Codex adapter, task packet, and evidence contracts.
- `source_proxy/planning/`: deterministic planning and review helpers.
- `source_proxy/verification/`: deterministic verification and diff contracts.
- `source_proxy/testing/`: runner profiles and self-tests.
- `source_proxy/tests/`: Source Proxy regression, safety, Codex adapter, long-running task, verification, Cartographer, and workspace tests.

Supporting docs remain useful but no longer override this roadmap:

- `docs/source-proxy-production-hardening-plan.md`
- `docs/source-proxy-coding-agent-a-plus-stress-gauntlet.md`
- `docs/source-proxy-v0.3-stress-testing-plan.md`
- `docs/coding-command-center-voidcore-master-plan-v0.1.md`
- `docs/coding-command-center-voidcore-foundation-closeout-v0.1.md`
- `docs/source-proxy-regression-matrix.md`
- `docs/source-proxy-daily-use-runbook.md`
- `docs/source-proxy-remote-manual-checks.md`
- `docs/codex-real-task-trial.md`

## Human Approval Boundaries

Codex must stop and ask Britton before crossing any of these boundaries:

- apply
- execute-approved
- commit
- push
- stash
- reset
- clean
- package install
- server restart
- worktree creation
- branch mutation
- external network or API cost
- auth, config, or env changes
- anything outside the approved lane

Approval does not equal apply. Apply does not equal verification. Verification does not equal commit. Commit does not equal push.

## Global Workflow Rule For Codex

1. Run baseline status.
2. Implement exactly one small increment.
3. Run that increment's check itself.
4. Record result.
5. If PASS and no authority boundary was crossed, move to the next increment in the same phase.
6. If FAIL, repair within scope, rerun checks, then stop with blocker if still failing.
7. If an approval/apply/commit/push/worktree/package/server/auth/config/env boundary appears, stop and ask Britton.
8. At phase end, produce phase closeout.
9. Ask Britton to run the big terminal check.
10. Ask permission before the next phase.

Codex should not ask Britton to verify every tiny increment unless a human boundary is hit. Codex runs small-increment checks itself. Britton gets the big terminal check at phase closeout and then gives permission before the next phase.

## Increment Output Contract

After each increment, Codex reports:

- increment title
- files changed
- checks run
- result: PASS, FAIL, or BLOCKED
- evidence summary
- blocker, if any
- next increment title

After each phase, Codex reports:

- phase status
- increments completed
- files changed
- safety boundaries preserved
- big terminal check for Britton
- known blockers
- recommended next phase
- explicit permission question

## Phase 0: Master Plan Consolidation And Authority Reset

Phase goal: create this master plan, create the new-chat handoff, update the plan index, and make no runtime changes.

### Increment 0.1: Inspect Current Source Proxy `/coding` Context

Purpose: read the existing roadmap, runbook, stress, UI, regression, and code-context files so the new plan reflects the repo state.

Allowed files or lane: read-only inspection of docs, `src/app/coding/page.tsx`, `src/components/coding/*`, `src/lib/coding/`, and `source_proxy/*`.

Forbidden actions: runtime code edits, `/coding` implementation edits, Source Proxy runtime edits, test edits, apply, execute-approved, commit, push, stash, reset, clean, package install.

Expected Codex behavior: inspect first, summarize current authority, and preserve existing dirty worktree changes.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
git status --branch --short
test -f docs/plan-index.md
test -f src/app/coding/page.tsx
test -d src/lib/coding
test -d source_proxy/tests
```

Expected output: required files and directories exist; status is recorded.

Blocker behavior: if a required file is missing, stop and report the missing path before writing new docs.

Next increment title: Increment 0.2: Create Master Plan And Handoff

### Increment 0.2: Create Master Plan And Handoff

Purpose: add `docs/source-proxy-codex-class-production-master-plan-v1.0.md` and `docs/source-proxy-codex-class-new-chat-handoff-v1.0.md`.

Allowed files or lane: new docs only.

Forbidden actions: runtime code edits, tests edits, source_proxy edits, package changes, apply, execute-approved, commit, push, stash, reset, clean.

Expected Codex behavior: write a phase-based production roadmap and a new-chat handoff that starts at Phase 0 until this task is complete, then Phase 1 after Britton approves.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
test -f docs/source-proxy-codex-class-production-master-plan-v1.0.md && echo "master plan exists"
test -f docs/source-proxy-codex-class-new-chat-handoff-v1.0.md && echo "handoff exists"
grep -n "Source Proxy Codex-Class Production Master Plan v1.0" docs/source-proxy-codex-class-production-master-plan-v1.0.md
grep -n "Do not jump into feature work" docs/source-proxy-codex-class-new-chat-handoff-v1.0.md
```

Expected output: both files exist and required title/start-rule language is present.

Blocker behavior: if required language is missing, repair the docs before continuing.

Next increment title: Increment 0.3: Update Plan Index

### Increment 0.3: Update Plan Index

Purpose: make the new master plan and handoff discoverable from `docs/plan-index.md`.

Allowed files or lane: `docs/plan-index.md` only.

Forbidden actions: deleting old plans, broad index rewrite, runtime code edits, test edits, apply, execute-approved, commit, push, stash, reset, clean.

Expected Codex behavior: add a small current roadmap entry and leave supporting/historical plans intact.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -n "source-proxy-codex-class-production-master-plan-v1.0\|source-proxy-codex-class-new-chat-handoff-v1.0" docs/plan-index.md
git diff -- docs/plan-index.md docs/source-proxy-codex-class-production-master-plan-v1.0.md docs/source-proxy-codex-class-new-chat-handoff-v1.0.md
git diff --check
```

Expected output: plan index references both new docs; diff is docs-only; diff check is clean.

Blocker behavior: if index references are missing or diff check fails, repair within docs lane and rerun.

Next increment title: Phase 1, Increment 1.1: Plain-English Intake Contract Inventory

### Phase 0 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
printf '\n== STATUS BEFORE/AFTER ==\n'
git status --branch --short
printf '\n== PLAN FILES EXIST ==\n'
test -f docs/source-proxy-codex-class-production-master-plan-v1.0.md && echo "master plan exists"
test -f docs/source-proxy-codex-class-new-chat-handoff-v1.0.md && echo "handoff exists"
printf '\n== PLAN INDEX REFERENCES ==\n'
grep -n "source-proxy-codex-class-production-master-plan-v1.0\|source-proxy-codex-class-new-chat-handoff-v1.0" docs/plan-index.md
printf '\n== REQUIRED PHASES PRESENT ==\n'
grep -n "Phase 0\|Phase 1\|Phase 2\|Phase 3\|Phase 4\|Phase 5\|Phase 6\|Phase 7\|Phase 8\|Phase 9\|Phase 10\|Phase 11" docs/source-proxy-codex-class-production-master-plan-v1.0.md
printf '\n== REQUIRED WORKFLOW LANGUAGE PRESENT ==\n'
grep -n "Global Workflow Rule For Codex\|Functional proof first\|Visual polish last\|permission before the next phase\|big terminal check" docs/source-proxy-codex-class-production-master-plan-v1.0.md
printf '\n== HANDOFF START RULES PRESENT ==\n'
grep -n "Do not jump into feature work\|Do not start UI polish\|Do not start model switching\|Start with the active phase" docs/source-proxy-codex-class-new-chat-handoff-v1.0.md
printf '\n== DIFF CHECK ==\n'
git diff --check
printf '\n== DIFF STAT ==\n'
git diff --stat
printf '\n== FINAL STATUS ==\n'
git status --branch --short
```

Expected result: new plan and handoff exist, index references both, required phase/workflow/handoff language is present, `git diff --check` is clean, and only docs/index changes from this phase are attributable to this task.

Phase stop: Codex must stop, produce Phase 0 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 1: Plain-English Coding Intake And Self-Scoping

Phase goal: a user can give natural language prompts without target files, allowed files, checks, rollback, or machine-shaped task packets. The agent infers task type, inspects the repo, derives target files, allowed files, forbidden files, expected checks, risk, rollback hint, and safe next action. The agent shows scope review before write/apply. No auto-apply.

### Increment 1.1: Plain-English Intake Contract Inventory

Purpose: identify current places requiring machine-shaped task packets and define the missing plain-English self-scoping contract.

Allowed files or lane: docs and planning notes; likely `docs/*` plus read-only inspection of `src/lib/coding/`, `src/components/coding/`, and `source_proxy/planning/`.

Forbidden actions: runtime implementation, UI polish, apply, execute-approved, commit, push, package install, server restart.

Expected Codex behavior: inspect current prompt/target/allowed-files flow and record exact gaps before implementation.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -R "allowedFiles\|allowed_files\|targetFile\|target_file" -n src/components/coding src/lib/coding source_proxy/planning source_proxy/api | head -80
git status --branch --short
```

Expected output: current target/allowed-file requirements are visible; no runtime files changed unless a later implementation increment explicitly allows them.

Blocker behavior: if the repo shape differs, stop and update the phase plan before coding.

Next increment title: Increment 1.2: Self-Scoping Draft Contract

### Increment 1.2: Self-Scoping Draft Contract

Purpose: implement or document the first bounded self-scoping draft output: task type, inferred target files, allowed files, forbidden files, checks, risk, rollback hint, and safe next action.

Allowed files or lane: self-scoping planner lane only; exact files must be named after Increment 1.1.

Forbidden actions: apply, execute-approved, hidden writes, provider switching, broad UI redesign, commit, push.

Expected Codex behavior: make the smallest change that lets plain English become a reviewable scope packet without applying anything.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
git diff --check
git diff --stat
git status --branch --short
```

Expected output: bounded diff, no apply path changed unless explicitly in scope, no commit/push.

Blocker behavior: if self-scoping cannot infer a safe scope, return `blocked/ambiguous` with concrete missing information.

Next increment title: Increment 1.3: Scope Review Before Write

### Increment 1.3: Scope Review Before Write

Purpose: require a visible scope review before write/apply for plain-English tasks.

Allowed files or lane: planner contract and minimal `/coding` display lane, exact files named before edit.

Forbidden actions: auto-apply, execute-approved, commit, push, provider changes, final polish.

Expected Codex behavior: show inferred scope and require human review before any write-capable step.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run typecheck
git diff --check
git status --branch --short
```

Expected output: typecheck passes; scope review is present; no write/apply authority is added.

Blocker behavior: if review cannot be shown clearly, stop before any apply-capable work.

Next increment title: Phase 2, Increment 2.1: Productive Trial Matrix Selection

### Phase 1 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py source_proxy/tests/test_diff_verification.py source_proxy/tests/test_verification_contracts.py
```

Expected result: plain-English intake can produce a self-scoped review packet; scope review appears before write/apply; no auto-apply exists.

Phase stop: Codex must stop, produce Phase 1 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 2: Productive Coding-Agent Loop Proof

Phase goal: prove real productive tasks from plain English across docs, UI, backend/API, test-writing, and debugging/recovery. Prove no wrong-file edits, no hidden mutations, no fake success, no unapproved apply, no commit/push.

### Increment 2.1: Productive Trial Matrix Selection

Purpose: choose a small set of real plain-English tasks across docs, UI, backend/API, tests, and recovery.

Allowed files or lane: docs trial plan and selected target lanes only.

Forbidden actions: unscoped edits, apply, execute-approved, commit, push, package install, cleanup.

Expected Codex behavior: define each trial with prompt, inferred scope, expected checks, rollback hint, and safety stop conditions.

Selected Phase 2 trial matrix: `docs/source-proxy-codex-class-phase-2-productive-trial-matrix.md`.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
grep -n "Trial\|plain-English\|rollback" docs/source-proxy-codex-class-production-master-plan-v1.0.md
```

Expected output: trial matrix exists or is linked; docs-only planning diff is clean.

Blocker behavior: if tasks are too broad or ambiguous, shrink them before execution.

Next increment title: Increment 2.2: Execute Docs And UI Productive Proof

### Increment 2.2: Execute Docs And UI Productive Proof

Purpose: run bounded docs and UI tasks from plain English and prove correct targeting, useful diffs, and honest checks.

Allowed files or lane: one docs target and one UI target at a time, named before each task.

Forbidden actions: backend authority changes, apply without exact approval, commit, push, unrelated polish.

Expected Codex behavior: handle each task from plain English through scope, diff, checks, and receipt.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run typecheck
npm run test:coding-frontend-regression
git diff --check
git status --branch --short
```

Expected output: docs/UI trial diffs are bounded; checks pass or fail honestly with specific blockers.

Blocker behavior: wrong-file edit, hidden mutation, or fake success blocks the phase.

Next increment title: Increment 2.3: Execute Backend/API, Test, And Recovery Proof

### Increment 2.3: Execute Backend/API, Test, And Recovery Proof

Purpose: run backend/API, test-writing, and debugging/recovery tasks from plain English.

Allowed files or lane: one backend/API target or one test target at a time, named before each task.

Forbidden actions: safety bypass, apply without approval, commit, push, protected path edits.

Expected Codex behavior: produce useful bounded changes, run deterministic checks, and record failure recovery honestly.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_source_proxy_end_to_end.py
git diff --check
git status --branch --short
```

Expected output: backend/test/recovery proofs pass or produce specific safe blockers; no unapproved apply/commit/push.

Blocker behavior: any unsafe failure stops the phase and requires a corrective plan.

Next increment title: Phase 3, Increment 3.1: Browser Prompt Intake Wiring Proof

### Phase 2 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_source_proxy_end_to_end.py
```

Expected result: real productive tasks are proven from plain English with bounded diffs, honest checks, no wrong-file edits, no hidden mutations, no fake success, no unapproved apply, and no commit/push.

Phase stop: Codex must stop, produce Phase 2 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 3: Browser `/coding` Productive Diff Workflow

Phase goal: the browser command center accepts plain-English prompts, shows inferred scope, real diff previews, no-diff evidence honestly, and blocked/ambiguous states. Productive browser diff proof is required before final UI polish.

### Increment 3.1: Browser Prompt Intake Wiring Proof

Purpose: connect or verify browser plain-English prompt intake to the self-scoping draft flow.

Allowed files or lane: `/coding` browser intake and minimal supporting helpers, exact files named before edit.

Forbidden actions: apply, execute-approved, final visual polish, provider switching, commit, push.

Expected Codex behavior: browser accepts natural language and shows a scope review before diff preview.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run typecheck
npx vitest run src/app/coding/__tests__/page.test.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx
git diff --check
```

Expected output: browser intake tests pass; no apply path is loosened.

Blocker behavior: if browser cannot show scope review, stop before diff-preview expansion.

Next increment title: Increment 3.2: Real Diff Preview And No-Diff Evidence

### Increment 3.2: Real Diff Preview And No-Diff Evidence

Purpose: show real diff previews when changes exist and honest no-diff evidence when no change is needed.

Allowed files or lane: `/coding` diff display and route payload display lane.

Forbidden actions: fake diff summaries, auto-approval, apply, commit, push.

Expected Codex behavior: show changed files, diff hunks, target/allowed-file evidence, and no-diff reasons.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_diff_verification.py source_proxy/tests/test_verification_contracts.py
git diff --check
```

Expected output: UI and backend verification tests pass; no-diff state is honest.

Blocker behavior: if no-diff is ambiguous, report blocked instead of success.

Next increment title: Increment 3.3: Blocked And Ambiguous Browser States

### Increment 3.3: Blocked And Ambiguous Browser States

Purpose: ensure the browser shows blocked, unsafe, and ambiguous states with concrete next actions.

Allowed files or lane: `/coding` blocked-state UI and route payload mapping lane.

Forbidden actions: swallowing blockers, enabling approval on blocked state, final polish, commit, push.

Expected Codex behavior: make blocked states reviewable without granting authority.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py
git diff --check
git status --branch --short
```

Expected output: blocked states are tested; approval/apply stay unavailable.

Blocker behavior: any blocked state that enables approval blocks the phase.

Next increment title: Phase 4, Increment 4.1: Exact Approval Binding

### Phase 3 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py source_proxy/tests/test_diff_verification.py source_proxy/tests/test_verification_contracts.py
```

Expected result: browser `/coding` can accept plain-English prompts, show inferred scope, show real diffs or honest no-diff evidence, and block unsafe/ambiguous work.

Phase stop: Codex must stop, produce Phase 3 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 4: Apply And Verify Proof, Still Gated

Phase goal: apply requires exact approval, verification is separate after apply, stale/wrong-scope approvals fail closed, and commit/push remain unavailable unless a later separate plan approves them.

### Increment 4.1: Exact Approval Binding

Purpose: ensure approval binds to the exact task, target, allowed files, and diff.

Allowed files or lane: approval binding and tests only, exact files named before edit.

Forbidden actions: actual apply without approval, commit, push, provider changes, broad UI redesign.

Expected Codex behavior: stale or mismatched approval cannot unlock apply.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npx vitest run src/components/coding/__tests__/approval-gate-binding.test.ts
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py
git diff --check
```

Expected output: stale/wrong-scope approval cases fail closed.

Blocker behavior: if approval can drift from diff or target, stop immediately.

Next increment title: Increment 4.2: Post-Apply Verification Separation

### Increment 4.2: Post-Apply Verification Separation

Purpose: prove apply and verify are separate states, with verification required after apply.

Allowed files or lane: apply receipt and verification display/contract lane, exact files named before edit.

Forbidden actions: commit, push, treating apply as verified, hidden verification, package install.

Expected Codex behavior: apply produces a receipt; verification must run separately and can pass, fail, or be unavailable honestly.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_source_proxy_end_to_end.py
npm run test:coding-frontend-regression
git diff --check
```

Expected output: post-apply verification is distinct and visible.

Blocker behavior: if apply implies verification, stop and repair.

Next increment title: Increment 4.3: Commit And Push Unavailable Proof

### Increment 4.3: Commit And Push Unavailable Proof

Purpose: prove commit/push remain unavailable unless a later separate plan approves them.

Allowed files or lane: read-only UI/status/tests and Source Proxy governance tests.

Forbidden actions: commit implementation, push implementation, branch mutation, stash, reset, clean.

Expected Codex behavior: show commit/push unavailable or blocked; never run them.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "commit_proposal or push_queue"
git diff --check
git status --branch --short
```

Expected output: commit/push are blocked or proposal-only; no commit/push occurred.

Blocker behavior: any executable commit/push path blocks release.

Next increment title: Phase 5, Increment 5.1: Workflow Type Contract

### Phase 4 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_source_proxy_end_to_end.py
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "commit_proposal or push_queue"
```

Expected result: apply requires exact approval, verification is separate, stale/wrong-scope approvals fail closed, and commit/push remain unavailable.

Phase stop: Codex must stop, produce Phase 4 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 5: Multi-Workflow Runtime

Phase goal: add or plan workflow types for coding task, bugfix, test generation, docs update, review-only analysis, verification-only, and blocked/unsafe. Add task history/run ledger concepts. Add workflow switching, cancellation, retry, and queue rules. One write-capable task per scope unless future worktree isolation exists.

### Increment 5.1: Workflow Type Contract

Purpose: define workflow types and their authority boundaries.

Allowed files or lane: workflow type contract and docs/tests, exact files named before edit.

Forbidden actions: parallel write tasks, apply bypass, commit, push, worktree creation.

Expected Codex behavior: classify every task into one workflow type and show blocked/unsafe when needed.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -R "workflow" -n src/lib/coding src/components/coding source_proxy/api source_proxy/tests | head -80
git diff --check
```

Expected output: current workflow handling is understood; new contract is bounded.

Blocker behavior: ambiguous workflow type returns blocked instead of defaulting to write-capable.

Next increment title: Increment 5.2: Task History And Run Ledger

### Increment 5.2: Task History And Run Ledger

Purpose: add a task story ledger concept for scope, diffs, checks, blockers, approvals, apply, verification, retry, and cancellation.

Allowed files or lane: task history/run ledger lane, exact files named before edit.

Forbidden actions: durable hidden writes without display, commit/push, package install, branch/worktree changes.

Expected Codex behavior: record enough task story to survive review and refresh, without claiming more than happened.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py
git diff --check
```

Expected output: task history/ledger behavior is tested and honest.

Blocker behavior: if refresh loses required task story, stop before workflow switching.

Next increment title: Increment 5.3: Switching, Cancellation, Retry, And Queue Rules

### Increment 5.3: Switching, Cancellation, Retry, And Queue Rules

Purpose: define and implement safe workflow switching, cancellation, retry, and queue behavior.

Allowed files or lane: workflow state and queue rules lane, exact files named before edit.

Forbidden actions: two write-capable tasks in same scope, hidden workers, commit, push, worktree creation.

Expected Codex behavior: allow read-only switching, cancel/retry safely, and block conflicting write-capable tasks.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_coding_regression_pack.py
git diff --check
```

Expected output: queue rules are tested; one write-capable task per scope is enforced.

Blocker behavior: conflicting write-capable tasks block with clear reason.

Next increment title: Phase 6, Increment 6.1: Provider Status Inventory

### Phase 5 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_coding_regression_pack.py
```

Expected result: workflow types, task history/ledger, switching, cancellation, retry, and queue rules are present and safe.

Phase stop: Codex must stop, produce Phase 5 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 6: Model/Provider Switching

Phase goal: local AI, cloud AI, Codex worker, and future providers show honest status and authority. Provider switching must not silently bypass Source Proxy safety. Codex worker remains proposal-only unless separately approved. Unconfigured providers must not pretend to be usable.

### Increment 6.1: Provider Status Inventory

Purpose: inventory current provider status display and routing contracts.

Allowed files or lane: read-only provider status inspection and docs/tests planning.

Forbidden actions: provider implementation, external API cost, auth/config/env changes, package install, apply, commit, push.

Expected Codex behavior: identify configured, unavailable, proposal-only, and future providers honestly.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -R "provider\|model" -n src/lib/coding src/components/coding src/lib/server source_proxy/tests | head -100
git status --branch --short
```

Expected output: current provider labels and tests are identified.

Blocker behavior: missing provider config means unavailable, not usable.

Next increment title: Increment 6.2: Honest Provider Switching UI Contract

### Increment 6.2: Honest Provider Switching UI Contract

Purpose: show local AI, cloud AI, Codex worker, and future providers with honest availability and authority.

Allowed files or lane: provider status UI/helper/tests, exact files named before edit.

Forbidden actions: calling external paid APIs, changing env/auth, bypassing Source Proxy, apply, commit, push.

Expected Codex behavior: switching providers changes intent/status only unless a configured safe route exists.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npx vitest run src/lib/coding/__tests__/model-provider-status.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
npm run typecheck
git diff --check
```

Expected output: provider status tests pass; unconfigured providers remain unavailable.

Blocker behavior: if a provider can bypass Source Proxy, stop.

Next increment title: Increment 6.3: Codex Worker Proposal-Only Proof

### Increment 6.3: Codex Worker Proposal-Only Proof

Purpose: prove Codex worker remains proposal-only unless separately approved.

Allowed files or lane: Codex adapter display/tests and proposal-only contracts.

Forbidden actions: Codex apply authority, execute-approved through worker, commit, push, external cost.

Expected Codex behavior: Codex can propose or provide evidence only, not apply.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py source_proxy/tests/test_source_proxy_end_to_end.py
npm run test:coding-frontend-regression
git diff --check
```

Expected output: Codex route remains proposal/read-only and authority-free.

Blocker behavior: any Codex worker apply/commit/push authority blocks the phase.

Next increment title: Phase 7, Increment 7.1: Timeline Event Contract

### Phase 6 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npx vitest run src/lib/coding/__tests__/model-provider-status.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py source_proxy/tests/test_source_proxy_end_to_end.py
```

Expected result: provider statuses are honest, switching cannot bypass Source Proxy, Codex worker remains proposal-only, and unavailable providers do not pretend to work.

Phase stop: Codex must stop, produce Phase 6 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 7: Live Coding Previews And Progress Stream

Phase goal: show understand -> inspect -> scope -> draft -> preview -> approval -> apply -> verify timeline. Show live changed files, diff hunks, check output, blockers, no-diff evidence, rollback, and receipts. Refresh/reconnect should not lose task story.

### Increment 7.1: Timeline Event Contract

Purpose: define timeline events for understand, inspect, scope, draft, preview, approval, apply, and verify.

Allowed files or lane: timeline contract and display/test lane, exact files named before edit.

Forbidden actions: provider work, apply bypass, hidden background workers, commit, push.

Expected Codex behavior: every event is labeled by source, time, authority, and evidence.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -R "timeline\|receipt\|changedFiles\|changed_files" -n src/components/coding src/lib/coding source_proxy | head -100
git diff --check
```

Expected output: existing timeline/receipt hooks are identified.

Blocker behavior: if event source is unclear, label as unavailable rather than inferred fact.

Next increment title: Increment 7.2: Live Evidence Stream Display

### Increment 7.2: Live Evidence Stream Display

Purpose: show changed files, diff hunks, check output, blockers, no-diff evidence, rollback hints, and receipts as the task progresses.

Allowed files or lane: progress stream display and tests, exact files named before edit.

Forbidden actions: fake live output, hidden apply, commit, push, package install.

Expected Codex behavior: stream only real observed events; mark unavailable data honestly.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py
git diff --check
```

Expected output: progress stream tests pass and evidence is real or marked unavailable.

Blocker behavior: if output cannot be tied to a task, do not display it as proof.

Next increment title: Increment 7.3: Refresh And Reconnect Story Preservation

### Increment 7.3: Refresh And Reconnect Story Preservation

Purpose: ensure refresh/reconnect does not lose the task story.

Allowed files or lane: persistence/readback lane, exact files named before edit.

Forbidden actions: hidden durable writes without display, auth/config/env changes, commit, push.

Expected Codex behavior: task history survives refresh enough to review what happened.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_source_proxy_end_to_end.py
git diff --check
```

Expected output: refresh/reconnect story preservation is tested.

Blocker behavior: if task story cannot survive refresh, block live-preview release.

Next increment title: Phase 8, Increment 8.1: Workspace Selector Hardening

### Phase 7 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_source_proxy_end_to_end.py
```

Expected result: timeline and live evidence stream are honest, reviewable, and resilient across refresh/reconnect.

Phase stop: Codex must stop, produce Phase 7 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 8: Workspaces, Projects, And Isolation

Phase goal: harden workspace/project selector, read-only project detection, dirty worktree classifier, worktree proposal only unless separately approved, and one task / one scope / one branch rule.

### Increment 8.1: Workspace Selector Hardening

Purpose: verify workspace/project selector states and prevent unsafe assumptions about writable projects.

Allowed files or lane: workspace selector, workspace status helpers, and tests.

Forbidden actions: worktree creation, branch mutation, Windows writes, auth/config/env changes, commit, push.

Expected Codex behavior: show workspace status honestly and require explicit approval for any future external workspace action.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_workspace_tools.py
npm run test:coding-frontend-regression
git diff --check
```

Expected output: workspace selection remains gated and honest.

Blocker behavior: unknown workspace state is read-only or blocked by default.

Next increment title: Increment 8.2: Read-Only And Dirty Worktree Classifier

### Increment 8.2: Read-Only And Dirty Worktree Classifier

Purpose: classify read-only projects and dirty worktrees before write-capable tasks.

Allowed files or lane: project health/classifier lane and display/tests.

Forbidden actions: reset, clean, stash, branch mutation, worktree creation, commit, push.

Expected Codex behavior: dirty tree is visible with expected/unexpected buckets and next safe action.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k project_health
git diff --check
git status --branch --short
```

Expected output: dirty/read-only classification is explicit.

Blocker behavior: uncertain dirty state blocks write-capable work.

Next increment title: Increment 8.3: Worktree Proposal-Only Rule

### Increment 8.3: Worktree Proposal-Only Rule

Purpose: keep worktree creation proposal-only unless separately approved.

Allowed files or lane: docs/status/proposal display and tests.

Forbidden actions: actual worktree creation, branch mutation, reset, clean, stash, commit, push.

Expected Codex behavior: propose worktree isolation only with clear reason and approval boundary.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -n "worktree" docs/source-proxy-worktree-study.md docs/source-proxy-codex-class-production-master-plan-v1.0.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k project_health
git diff --check
```

Expected output: worktree remains proposal-only.

Blocker behavior: any automatic worktree or branch mutation blocks the phase.

Next increment title: Phase 9, Increment 9.1: Parallel Read-Only Review Contract

### Phase 8 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_workspace_tools.py source_proxy/tests/test_cartographer_api.py -k project_health
```

Expected result: workspace/project state is honest, read-only and dirty states are classified, worktree creation remains proposal-only, and one task / one scope / one branch is enforced.

Phase stop: Codex must stop, produce Phase 8 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 9: Parallel Workflows And Optional Subagent-Style Work

Phase goal: add parallel workflows only after single-agent workflow is reliable. Parallel read-only reviews are allowed. Parallel write-capable tasks in the same scope are forbidden. Every worker approval request must be labeled by source task/thread.

### Increment 9.1: Parallel Read-Only Review Contract

Purpose: define where parallel read-only review is allowed.

Allowed files or lane: workflow contract, task/thread labels, and tests.

Forbidden actions: parallel writes, hidden workers, apply, commit, push, branch/worktree mutation.

Expected Codex behavior: run parallel review only for read-only analysis and label each source task/thread.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -R "worker\|lane\|thread\|parallel" -n src/components/coding src/lib/coding source_proxy docs | head -100
git diff --check
```

Expected output: current worker/lane references are identified.

Blocker behavior: if a worker might write, block until isolated or explicitly approved in a future plan.

Next increment title: Increment 9.2: Write-Capable Scope Conflict Guard

### Increment 9.2: Write-Capable Scope Conflict Guard

Purpose: forbid parallel write-capable tasks in the same scope.

Allowed files or lane: conflict guard and queue rules lane.

Forbidden actions: multiple write tasks per scope, apply bypass, commit, push, worktree creation.

Expected Codex behavior: detect scope overlap and block one of the tasks.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py
npm run test:coding-frontend-regression
git diff --check
```

Expected output: overlapping write-capable tasks block.

Blocker behavior: if overlap detection is uncertain, fail closed.

Next increment title: Increment 9.3: Worker Approval Label Proof

### Increment 9.3: Worker Approval Label Proof

Purpose: require every worker approval request to be labeled by source task/thread.

Allowed files or lane: worker label display/tests and approval packet contract.

Forbidden actions: unlabeled approval, worker apply authority, commit, push.

Expected Codex behavior: approval request must show source task/thread and exact scope.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_codex_cli_adapter.py
npm run test:coding-frontend-regression
git diff --check
```

Expected output: worker approval labels are enforced.

Blocker behavior: unlabeled worker approval request blocks apply.

Next increment title: Phase 10, Increment 10.1: Codex-Class IA Review

### Phase 9 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_codex_cli_adapter.py
```

Expected result: parallel read-only review is allowed, parallel write-capable conflicts are blocked, and worker approval requests are labeled by source task/thread.

Phase stop: Codex must stop, produce Phase 9 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 10: Codex-Class Visual Polish

Phase goal: only after functional proof, polish information architecture, visual density, diff/review pane, mobile review/control UX, accessibility, blocked/error/no-diff states. The goal is polished Codex-like usability, not glassy clutter.

### Increment 10.1: Codex-Class IA Review

Purpose: review information architecture against proven workflow needs.

Allowed files or lane: UI planning, screenshots/manual review notes, and small IA changes after approval.

Forbidden actions: functional rewrites, provider switching, apply logic changes, commit, push.

Expected Codex behavior: prioritize workflow clarity, density, diff review, and operator control.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
```

Expected output: baseline UI tests pass before polish.

Blocker behavior: do not polish over broken workflow states.

Next increment title: Increment 10.2: Diff/Review Pane And State Polish

### Increment 10.2: Diff/Review Pane And State Polish

Purpose: polish diff/review pane, blocked/error/no-diff states, and visual density.

Allowed files or lane: `/coding` UI and CSS lane only, exact files named before edit.

Forbidden actions: backend authority changes, apply logic changes, model/provider changes, package install, commit, push.

Expected Codex behavior: improve readability and control density without weakening safety.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run typecheck
npm run test:coding-frontend-regression
git diff --check
```

Expected output: polished state remains tested and accessible.

Blocker behavior: if text overlaps or controls become ambiguous, stop and repair.

Next increment title: Increment 10.3: Mobile Review And Accessibility Polish

### Increment 10.3: Mobile Review And Accessibility Polish

Purpose: polish mobile review/control UX and accessibility for real operator use.

Allowed files or lane: responsive `/coding` UI and accessibility tests/manual checks.

Forbidden actions: new package install, server restart without approval, backend authority changes, commit, push.

Expected Codex behavior: make mobile review usable without adding mobile execution authority.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
npm run typecheck
npm run test:coding-frontend-regression
git diff --check
```

Expected output: responsive states remain stable and accessible.

Blocker behavior: if browser proof requires server restart or Playwright install, stop and ask Britton.

Next increment title: Phase 11, Increment 11.1: Full Regression Pass

### Phase 10 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
```

Expected result: `/coding` is visually polished for Codex-class usability after functional proof, without glassy clutter or authority drift.

Phase stop: Codex must stop, produce Phase 10 closeout, ask Britton to run the big terminal check, and ask permission before the next phase.

## Phase 11: Release Hardening And Soak

Phase goal: full regression pass, repeated no-mutation soak, productive task gauntlet rerun, browser task gauntlet, final release receipt, and go/no-go.

### Increment 11.1: Full Regression Pass

Purpose: run the full Source Proxy and `/coding` regression suite selected for release.

Allowed files or lane: verification only unless a failing check requires a scoped fix approved within this phase.

Forbidden actions: apply bypass, commit, push, stash, reset, clean, package install, broad refactor.

Expected Codex behavior: run checks, record exact pass/fail, and repair only within approved lanes.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Expected output: release regression passes or names exact blockers.

Blocker behavior: any unsafe failure blocks release.

Next increment title: Increment 11.2: No-Mutation Soak And Gauntlet Rerun

### Increment 11.2: No-Mutation Soak And Gauntlet Rerun

Purpose: rerun repeated no-mutation soak, productive task gauntlet, and browser task gauntlet.

Allowed files or lane: verification, receipts, and scoped fixes only if approved.

Forbidden actions: hidden mutation, commit, push, clean, reset, package install, server restart without approval.

Expected Codex behavior: record HEAD/status before and after each run and distinguish expected evidence from unexpected mutation.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
git status --branch --short
git rev-parse HEAD
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
git rev-parse HEAD
git status --branch --short
git diff --check
```

Expected output: HEAD is stable; no unexpected mutation; gauntlet evidence is honest.

Blocker behavior: unexpected mutation or HEAD change blocks release.

Next increment title: Increment 11.3: Final Release Receipt And Go/No-Go

### Increment 11.3: Final Release Receipt And Go/No-Go

Purpose: produce final release receipt and go/no-go using the release scorecard.

Allowed files or lane: release receipt docs and verification summaries.

Forbidden actions: commit, push, stash, reset, clean, package install, post-hoc fake pass labels.

Expected Codex behavior: fill the scorecard with evidence, name residual risk, and recommend go/no-go.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
npm run typecheck
npm run test:coding-frontend-regression
```

Expected output: final release evidence is complete enough for Britton to decide.

Blocker behavior: any missing scorecard category or unsafe regression produces no-go.

Next increment title: Release complete or new post-release plan by separate approval

### Phase 11 Big Terminal Check For Britton

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Expected result: full regression, no-mutation soak, productive gauntlet, browser gauntlet, release receipt, and scorecard support a go/no-go decision.

Phase stop: Codex must stop, produce Phase 11 closeout, ask Britton to run the big terminal check, and ask for release go/no-go. There is no automatic next phase.

## Final Release Scorecard

Use this scorecard at Phase 11 closeout. Each category must be marked `PASS`, `WARN`, or `BLOCKED`, with evidence.

| Category | Required evidence | Result |
| --- | --- | --- |
| plain-English prompt readiness | Natural language prompts create self-scoped review packets without target/allowed-files supplied by user. | TBD |
| self-scoping accuracy | Scope packets identify task type, targets, allowed files, forbidden files, checks, risk, rollback, and safe next action. | TBD |
| productive diff reliability | Real tasks produce useful bounded diffs or honest no-diff/blocked evidence. | TBD |
| browser workflow readiness | `/coding` accepts prompts, shows scope, diffs, no-diff, blocked, ambiguous, approval, apply, and verify states honestly. | TBD |
| apply/verify safety | Apply requires exact approval; verification is separate; stale/wrong-scope approvals fail closed. | TBD |
| model/provider honesty | Local, cloud, Codex worker, and future providers show true status and authority. | TBD |
| live preview quality | Timeline, changed files, diff hunks, checks, blockers, rollback, and receipts are reviewable. | TBD |
| workflow history/retry/cancel quality | Task story survives review/refresh; retry/cancel/switching are safe. | TBD |
| workspace isolation safety | Workspace state, dirty tree, read-only projects, and worktree proposals are safe and honest. | TBD |
| parallel workflow safety | Read-only parallel work is allowed; overlapping write-capable work is blocked; worker approvals are labeled. | TBD |
| UI polish | Final UI is dense, accessible, clear, and Codex-class without clutter or authority ambiguity. | TBD |
| release readiness | Regression, no-mutation soak, productive gauntlet, browser gauntlet, and release receipt are complete. | TBD |

## Release Rule

Do not call the `/coding` cockpit production-ready unless every scorecard category is `PASS` or a `WARN` explicitly accepted by Britton. Any `BLOCKED` category is no-go.

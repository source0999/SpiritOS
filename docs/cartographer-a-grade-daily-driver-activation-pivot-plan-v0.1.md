# Cartographer A-Grade Daily Driver Activation PIVOT Plan v0.1

status: planning-only

date: 2026-05-24

owner: Britton

## Authority Statement

This document is a plan only. It does not activate Cartographer, promote daily-driver authority, change runtime behavior, change `/map`, change `source_proxy`, consume approval tokens, execute queues, dispatch workers, run providers, stage, commit, push, create branches, create worktrees, clean, delete, reset, stash, checkout, or perform implementation.

Cartographer remains NO-GO for automatic activation. Plan 10 and the cleanup commits are evidence inputs only. They are not promotion, activation, or proof that daily-driver operation is safe without a new explicit Britton decision.

## Section 1: Current Verified State

Verified in `/home/source/SpiritOS` using safe read-only/status commands on 2026-05-24.

- Current branch: `lane/main-cleanup-20260524`.
- Current commit: `ed15231 chore: capture isolated lane work`.
- Worktree cleanliness: `git status --branch --short` showed only `## lane/main-cleanup-20260524`, so the main worktree is Git-clean at inspection time.
- Other worktrees present: `/home/source/SpiritOS-phase11-verify` at `76f6986` on `lane/phase11-verify-cleanup-20260524`.
- Cleanup summary confirmation: partially confirmed. The main worktree branch, commit, clean status, and phase11 worktree entry match the pasted summary. The broader claim that every discovered repo/worktree is clean except `/home/source/Source` was not fully re-audited because this planning run stayed scoped to `/home/source/SpiritOS` and `git worktree list`.
- Unknowns: no fresh test suite was run for this planning document; generated/local artifacts may still exist; `/home/source/Source` ahead state was not rechecked; remote push state was not queried; browser/UI state was not manually opened.
- Planning status: GO for planning-only. NO-GO for implementation, activation, queue execution, approval consumption, worker dispatch, commit, push, cleanup, or promotion.

Evidence read before writing this plan:

- `docs/cartographer-auto-plan-10-true-auto-soak-and-promotion-closeout-v0.1.md`
- `docs/cartographer-auto-roadmap-v0.2.md`
- `docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md`
- `docs/cartographer-final-proof-stage-7-autonomy-readiness-score-decision-gate-dry-run-final-closeout.md`
- `docs/cartographer-integrated-control-master-plan-v0.1.md`
- `docs/plan-index.md`
- `source_proxy/api/cartographer.py`
- `source_proxy/cartographer/`
- `source_proxy/tests/test_cartographer_*.py`
- `src/app/map/`
- `src/app/v1/cartographer/repo-map/route.ts`
- `src/app/map/__tests__/`

## Section 2: Grade Baseline

| Category | Grade | Reason |
| --- | --- | --- |
| UI usefulness | B | `/map` shows useful status, blockers, truth packet, queue/workflow, worker, proof, and trust-tier data, but it is still dense and jargon-heavy for a daily operator cockpit. |
| repo awareness | A- | Live-state, dirty-tree, project, protected-zone, and evidence surfaces exist, with strong tests and route coverage. |
| safety boundaries | A- | Current docs and modules repeatedly fail closed and block self-approval, hidden mutation, broad git, command, worker, and queue authority. |
| real operator control | C+ | Approval-token, safe-write, ledger, queue, worker, and commit models exist, but durable real control, receipts, visible action buttons, and runtime promotion proof are incomplete. |
| approval gate readiness | B | Validation and consumption preview are strong, but durable single-action token storage and live consumption proof still require promotion work. |
| queue/workflow readiness | B- | Queue and workflow data models exist, but current state is mostly model-only or one-task selection proof, not supervised execution readiness. |
| worker/subagent readiness | B- | Worker identity, locks, conflict detection, and handoff packets are modeled, but dispatch must remain blocked until visible leases and receipts prove safety. |
| commit/push readiness | C+ | Local commit proposals and hard push boundaries exist; real daily-driver commit authority is not activated and push must stay separately gated. |
| daily-driver autonomy readiness | C+ | Final proof says operator-review-ready only; supervised real daily-driver operation still needs human decision, trial receipts, drills, and soak evidence. |
| overall daily-driver readiness | B-/C+ | Cartographer is strong as a read-only command center, but not yet A-grade as an active daily-driver system. |

## Section 3: A-Grade Target Definition

### A. UI usefulness

A-grade `/map` means a simple operator cockpit, not a diagnostics wall:

- Top status answers: Can Cartographer act? `Yes`, `No`, or `Partial`.
- Clear top status, current branch, short commit, dirty state, kill switch state, and authority level.
- Clear "why blocked" in a short blocker list.
- Clear "what Britton does next" as one recommended action.
- Collapsed details by default, including raw packets, endpoint status, and long proof lists.
- Evidence links to receipts, closeouts, tests, and route data.
- No scary wall of internal jargon by default.
- Mobile and desktop usable without overlapping controls or unreadable cards.
- All action buttons truthfully disabled or enabled based on current authority.
- `/map/raw` remains available for deep diagnostics.

### B. Real operator control

A-grade real control means all actions are narrow, visible, receipt-backed, and reversible:

- Durable approval token model.
- Single-action scoped human approval.
- Append-only event ledger.
- Receipt-backed actions.
- Exact allowed action classes.
- Exact rollback guidance.
- Kill switch known, visible, and tested.
- No hidden state mutation.
- No broad git authority.
- No self-approval.
- No implicit authority from a UI display, test pass, or completed plan.

### C. Auto daily-driver readiness

A-grade daily-driver readiness means promotion is earned in supervised operation:

- Supervised one-task execution first.
- 10 supervised safe-task receipts.
- 24h and 72h soak evidence.
- Hidden mutation drills.
- Kill-switch drills.
- Rollback drills.
- False positive and false negative tracking.
- Trust-tier decision packet.
- Explicit Britton promotion.
- No self-promotion.
- No auto-push until a separate promotion gate.

## Section 4: Master PIVOT Plan Of Plans

Global PIVOT rule: every plan is phase-by-phase and increment-by-increment. At the end of every Plan, Codex must stop and ask Britton for permission before starting the next Plan. Each increment must report the goal, allowed files/zones, forbidden files/zones, Codex checks, Britton manual checks, expected output, stop conditions, rollback or recovery, and next target.

### Plan 0: Verified Baseline And Lane Freeze

Purpose: Reconfirm the cleaned branch state, establish lane freeze, and prove no assumptions are stale before A-grade work begins.

Grade target improved: safety boundaries, repo awareness, daily-driver readiness.

Authority before: Level 0 read-only command center.

Authority after: Level 0 only.

Allowed files: optional docs-only closeout for Plan 0 if Britton explicitly asks; otherwise no edits.

Forbidden files: all source, UI, tests, package/config/env, generated/cache, media, git index, commit, push, branch, worktree, queue, worker, approval-token consumption.

Phases:

- Phase 0.1: Repo and worktree baseline.
- Phase 0.2: Lane freeze and NO-GO restatement.

Increment 0.1.1:

- Goal: Verify current branch, commit, clean status, worktrees, and diff hygiene.
- Allowed files or file zones: read-only whole-repo status inspection.
- Forbidden files or zones: all writes, staging, cleanup, source/UI/test edits.
- Exact checks Codex should run: `pwd`; `git status --branch --short`; `git log -1 --oneline`; `git branch --show-current`; `git worktree list`; `git diff --check`.
- Exact manual checks Britton should run: same terminal block in Section 8 Plan 0.
- Expected output: current state matches the intended lane or mismatch is named.
- Stop conditions: dirty tree returns unexpectedly, wrong branch, wrong commit, protected-lane overlap, Codex uncertainty.
- Rollback or recovery guidance: do not reset or clean; stop and ask Britton to classify the mismatch.
- Next target: Increment 0.1.2.

Increment 0.1.2:

- Goal: Freeze allowed and forbidden lanes before planning implementation.
- Allowed files or file zones: docs-only notes if explicitly requested.
- Forbidden files or zones: `source_proxy/agent_factory`, `src/app/coding`, `src/components/coding`, package/config/env, generated/cache, media.
- Exact checks Codex should run: `find docs -maxdepth 1 -iname '*cartographer*' | sort`; `find source_proxy -path '*cartographer*' -maxdepth 5 -type f | sort`; `find src/app -path '*map*' -maxdepth 5 -type f | sort`.
- Exact manual checks Britton should run: inspect the same output for unexpected paths.
- Expected output: Cartographer scope is visible and no lane is promoted.
- Stop conditions: unknown generated/cache files enter scope, protected files appear necessary without approval.
- Rollback or recovery guidance: preserve files; write a mismatch report only.
- Next target: Phase 0 closeout.

Phase 0 Closeout:

- Terminal Block: use Section 8 Plan 0 block.
- Verification Steps: confirm branch, commit, clean status, worktree list, and no changed files from Plan 0 unless an approved docs closeout exists.
- Visual Checks: none.
- Expected Output: NO-GO for activation; GO only for next planning/implementation plan if Britton approves.
- Debug Path: if mismatch, stop and request Britton classification.
- Next Target: Plan 1.
- Permission Gate: `Britton, approve Plan 1: /map UI usefulness reset to A-grade operator cockpit?`

### Plan 1: /map UI Usefulness Reset To A-Grade Operator Cockpit

Purpose: Turn `/map` into a plain first-screen cockpit while keeping `/map/raw` for diagnostics.

Grade target improved: UI usefulness.

Authority before: Level 0.

Authority after: Level 0. UI display only; no action authority.

Allowed files: `src/app/map/**`, `src/app/map/__tests__/**`.

Forbidden files: `source_proxy/**`, `src/app/v1/cartographer/**`, `src/app/coding/**`, `src/components/coding/**`, package/config/env, generated/cache, media.

Phases:

- Phase 1.1: Cockpit information architecture.
- Phase 1.2: Disabled truthful controls and collapsed detail design.
- Phase 1.3: Mobile/desktop visual proof.

Increment 1.1.1:

- Goal: Inventory current `/map` first-screen sections and decide what stays visible by default.
- Allowed files or file zones: read-only `src/app/map/page.tsx`, `src/app/map/map-information-architecture.ts`, map tests.
- Forbidden files or zones: backend routes, mutation endpoints, CSS-wide refactors.
- Exact checks Codex should run: `find src/app/map -maxdepth 2 -type f | sort`; `grep -nE "NO-GO|Can Cartographer act|Next safe step|Blockers|Evidence|Receipt|details|button" src/app/map/page.tsx src/app/map/raw/page.tsx src/app/map/__tests__/*.ts`.
- Exact manual checks Britton should run: open `/map` and name the first visible answer, blocker, and next action.
- Expected output: first-screen cockpit target list.
- Stop conditions: existing live action button is found, route behavior mismatch, UI cannot show authority truth.
- Rollback or recovery guidance: no code edited in this increment; stop and classify.
- Next target: Increment 1.1.2.

Increment 1.1.2:

- Goal: Implement the A-grade cockpit layout in a future approved run.
- Allowed files or file zones: `src/app/map/page.tsx`, `src/app/map/map-information-architecture.ts`, map tests.
- Forbidden files or zones: backend/source behavior, `source_proxy`, API routes, queue or approval calls.
- Exact checks Codex should run: `npm test -- run src/app/map/__tests__/map-display-shell.test.ts src/app/map/__tests__/map-information-architecture.test.ts`; `git diff --check -- src/app/map`.
- Exact manual checks Britton should run: browser check desktop and mobile for top status, next action, blockers, evidence, collapsed details.
- Expected output: `/map` answers "Can Cartographer act?" without a jargon wall.
- Stop conditions: text overlap, action button lies about authority, disabled controls missing, tests fail.
- Rollback or recovery guidance: revert only Plan 1 edits after explicit Britton approval; do not touch unrelated files.
- Next target: Phase 1 closeout.

Phase 1 Closeout:

- Terminal Block: use Section 8 Plan 1 block.
- Verification Steps: focused map tests, diff check, status review.
- Visual Checks: `/map` desktop 1440px and mobile 390px; verify top card, next action, blockers, evidence, disabled controls, collapsed details, `/map/raw` link.
- Expected Output: UI usefulness reaches A- target while authority remains Level 0.
- Debug Path: if visual check fails, stay inside `src/app/map/**` only.
- Next Target: Plan 2.
- Permission Gate: `Britton, approve Plan 2: Truth packet and evidence model hardening?`

### Plan 2: Truth Packet And Evidence Model Hardening

Purpose: Make one canonical truth packet separate live facts, recommendations, proof, and authority.

Grade target improved: repo awareness, UI usefulness, approval readiness.

Authority before: Level 0.

Authority after: Level 1 proposal packets only.

Allowed files: `source_proxy/cartographer/live_state.py`, truth/evidence modules under `source_proxy/cartographer/`, `source_proxy/api/cartographer.py` GET/read-only routes, focused `source_proxy/tests/test_cartographer_*`, `src/app/map/**` display if explicitly in scope.

Forbidden files: write operators, queue execution, worker dispatch, commit/push execution, package/config/env, generated/cache, media.

Phases:

- Phase 2.1: Truth packet schema.
- Phase 2.2: Evidence links and stale/unknown handling.
- Phase 2.3: `/map` truth display.

Increment 2.1.1:

- Goal: Define canonical fields for facts, authority, blockers, evidence, and recommendations.
- Allowed files or file zones: exact Cartographer model/API/test files approved for this plan.
- Forbidden files or zones: safe-write execution, queue run, approval consumption.
- Exact checks Codex should run: `grep -nE "authority_granted|can_mutate|write_actions_enabled|queue|worker|commit|push" source_proxy/cartographer/*.py source_proxy/api/cartographer.py`.
- Exact manual checks Britton should run: inspect returned truth packet via exact GET endpoint chosen in the plan.
- Expected output: stale or unknown fields force NO-GO.
- Stop conditions: packet implies authority from proof alone, unknowns are hidden.
- Rollback or recovery guidance: remove only Plan 2 schema/display edits after approval; keep evidence artifacts.
- Next target: Increment 2.2.1.

Increment 2.2.1:

- Goal: Add evidence references that are links, not authority.
- Allowed files or file zones: evidence model and display files only.
- Forbidden files or zones: receipt writes, generated evidence, hidden mutation.
- Exact checks Codex should run: focused pytest for truth/evidence tests selected by file; `git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py src/app/map`.
- Exact manual checks Britton should run: verify evidence card links to docs/receipts and never says "activated".
- Expected output: proof is reviewable but cannot promote itself.
- Stop conditions: missing evidence links, false claim of Plan 10 activation, test failure.
- Rollback or recovery guidance: stop, keep diff, request review.
- Next target: Phase 2 closeout.

Phase 2 Closeout:

- Terminal Block: use Section 8 Plan 2 block.
- Verification Steps: focused backend tests, optional focused map tests if UI touched, diff check.
- Visual Checks: if UI touched, evidence card links and stale/unknown truth states are visible.
- Expected Output: Level 1 proposal packet readiness; no mutation.
- Debug Path: inspect truth packet raw JSON and compare to `/map`.
- Next Target: Plan 3.
- Permission Gate: `Britton, approve Plan 3: Approval token runtime proof?`

### Plan 3: Approval Token Runtime Proof

Purpose: Prove durable, single-action, scoped approval can validate and be consumed without self-approval.

Grade target improved: real operator control, approval gate readiness.

Authority before: Level 1.

Authority after: Level 2 only after Britton explicitly approves exact docs/evidence write consumption.

Allowed files: `source_proxy/cartographer/approval_token_runtime.py`, `approval_token_consumption.py`, `workflow_event_ledger.py`, `source_proxy/api/cartographer.py`, focused approval tests.

Forbidden files: safe write execution unless in a later approved phase, queue/workers, commits, pushes, package/config/env.

Phases:

- Phase 3.1: Durable token decision.
- Phase 3.2: Validation and consumption proof.
- Phase 3.3: Self-approval and stale-state drills.

Increment 3.1.1:

- Goal: Choose durable approval record source and exact token lifecycle.
- Allowed files or file zones: approval modules and tests; docs/evidence storage only if explicitly approved.
- Forbidden files or zones: token minting by Cartographer, broad tokens, hidden storage.
- Exact checks Codex should run: `grep -nE "token_storage_available|single_action|self_approval|expected_head|expected_dirty_tree" source_proxy/cartographer/approval_token_runtime.py source_proxy/cartographer/approval_token_consumption.py`.
- Exact manual checks Britton should run: review token fields and confirm how Britton creates approval.
- Expected output: token model remains single-action, human-issued, expiring, scoped.
- Stop conditions: self-approval possible, storage unclear, stale HEAD not blocked.
- Rollback or recovery guidance: stop at Level 1; do not consume approval.
- Next target: Increment 3.2.1.

Increment 3.2.1:

- Goal: Prove one valid token can be consumed exactly once for a later allowed action.
- Allowed files or file zones: approval runtime/consumption and ledger only.
- Forbidden files or zones: real file write unless explicitly moved to Plan 5.
- Exact checks Codex should run: `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_approval_token_runtime.py source_proxy/tests/test_cartographer_approval_token_consumption.py source_proxy/tests/test_cartographer_workflow_event_ledger.py`.
- Exact manual checks Britton should run: inspect consumed-token receipt/event preview and verify it cannot be reused.
- Expected output: accepted token grants only the scoped next action, no broad authority.
- Stop conditions: token reuse, missing ledger event, approval validation unavailable.
- Rollback or recovery guidance: revoke token, demote to Level 1, preserve event evidence.
- Next target: Phase 3 closeout.

Phase 3 Closeout:

- Terminal Block: use Section 8 Plan 3 block.
- Verification Steps: approval runtime, consumption, ledger tests; diff check.
- Visual Checks: if `/map` touched, approval card shows single-action scope and disabled/enabled truthfully.
- Expected Output: Level 2-ready approval gate, but no write unless Plan 5 is approved.
- Debug Path: inspect reason codes for invalid, expired, stale, broad, and self-approved tokens.
- Next Target: Plan 4.
- Permission Gate: `Britton, approve Plan 4: Event ledger and receipt browser proof?`

### Plan 4: Event Ledger And Receipt Browser Proof

Purpose: Make actions reviewable through append-only events and readable receipts.

Grade target improved: real operator control, UI usefulness.

Authority before: Level 2-ready.

Authority after: Level 2 with evidence visibility; no new action class.

Allowed files: `workflow_event_ledger.py`, receipt/evidence modules, `source_proxy/api/cartographer.py`, `src/app/map/**`, focused tests.

Forbidden files: write operators beyond receipt display, queue execution, worker dispatch, commit/push.

Phases:

- Phase 4.1: Append-only event proof.
- Phase 4.2: Receipt browser proof.
- Phase 4.3: `/map` evidence UX.

Increment 4.1.1:

- Goal: Prove event append ordering, hashes, and no rewrites.
- Allowed files or file zones: ledger module/tests.
- Forbidden files or zones: production storage mutation unless explicitly approved.
- Exact checks Codex should run: `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_workflow_event_ledger.py`.
- Exact manual checks Britton should run: inspect event fields: actor, token, action, sequence, hash, receipt path.
- Expected output: append-only ledger rejects reorder/rewrite.
- Stop conditions: hidden mutation, missing event id, non-append behavior.
- Rollback or recovery guidance: demote to Level 1; preserve failed event sample.
- Next target: Increment 4.2.1.

Increment 4.2.1:

- Goal: Make receipts discoverable on `/map` with links and short summaries.
- Allowed files or file zones: receipt/evidence API/display and focused tests.
- Forbidden files or zones: writing new receipts in this plan.
- Exact checks Codex should run: focused receipt/evidence tests and `npm test -- run src/app/map/__tests__/map-display-shell.test.ts`.
- Exact manual checks Britton should run: open `/map` and `/map/raw`; verify receipts are readable and collapsed details exist.
- Expected output: operator can trace action to receipt without reading raw JSON first.
- Stop conditions: receipt browser claims authority, links broken, visual check failure.
- Rollback or recovery guidance: revert display-only Plan 4 UI after approval.
- Next target: Phase 4 closeout.

Phase 4 Closeout:

- Terminal Block: use Section 8 Plan 4 block.
- Verification Steps: ledger and map tests, diff check.
- Visual Checks: evidence card, receipt browser, raw diagnostics drill-down.
- Expected Output: A-grade evidence visibility without added authority.
- Debug Path: compare ledger event ids to receipt links.
- Next Target: Plan 5.
- Permission Gate: `Britton, approve Plan 5: Safe docs/evidence write operator proof?`

### Plan 5: Safe Docs/Evidence Write Operator Proof

Purpose: Prove one approval-gated safe write to docs/evidence/receipts with rollback and receipt metadata.

Grade target improved: real operator control, daily-driver readiness.

Authority before: Level 2.

Authority after: Level 2 proven for docs/evidence writes only.

Allowed files: `source_proxy/cartographer/safe_write.py`, approval modules, ledger, API route, focused tests, exact approved `docs/cartographer-live-evidence/**` or `docs/cartographer-live-receipts/**` file.

Forbidden files: source files, UI unless display-only status, package/config/env, generated/cache, media, commit/push, queue/workers.

Phases:

- Phase 5.1: Safe write preview and path barriers.
- Phase 5.2: First approved docs/evidence write.
- Phase 5.3: Receipt closeout and rollback guidance.

Increment 5.1.1:

- Goal: Reprove allowed prefixes, forbidden prefixes, traversal blocks, and exact file scope.
- Allowed files or file zones: safe write module/tests.
- Forbidden files or zones: non-docs paths, source paths, generated/cache.
- Exact checks Codex should run: `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_safe_write.py`.
- Exact manual checks Britton should run: inspect exact approved target path and rollback plan before approving live write.
- Expected output: only exact docs/evidence/receipt target is eligible.
- Stop conditions: generated/cache involved, protected path eligible, approval token invalid.
- Rollback or recovery guidance: no write; stop and fix barrier.
- Next target: Increment 5.2.1.

Increment 5.2.1:

- Goal: Execute one safe write only after Britton approves exact file and token.
- Allowed files or file zones: one exact approved docs/evidence/receipt file.
- Forbidden files or zones: all source/UI/test/package/config/generated/media files.
- Exact checks Codex should run: exact safe-write endpoint/unit check chosen for this plan; `git diff --check -- <exact-approved-file>`.
- Exact manual checks Britton should run: inspect file diff, receipt metadata, before-state, rollback guidance.
- Expected output: one file written, one receipt/event, no git staging.
- Stop conditions: extra file changed, hidden mutation, rollback missing, verification missing.
- Rollback or recovery guidance: use recorded before-state or operator-approved file revert; do not `git checkout`.
- Next target: Phase 5 closeout.

Phase 5 Closeout:

- Terminal Block: use Section 8 Plan 5 block.
- Verification Steps: safe-write tests, exact file diff, status, diff check.
- Visual Checks: if `/map` touched, safe-write receipt appears as evidence only.
- Expected Output: Level 2 safe docs/evidence write proof complete.
- Debug Path: compare approved token files to actual diff.
- Next Target: Plan 6.
- Permission Gate: `Britton, approve Plan 6: Verification runner proof?`

### Plan 6: Verification Runner Proof

Purpose: Prove exact argv verification command execution with bounded timeouts and receipt summaries.

Grade target improved: real operator control, queue/workflow readiness.

Authority before: Level 2.

Authority after: Level 3 verification runner.

Allowed files: `verification_runner.py`, API route, focused tests, receipt integration display if explicitly approved.

Forbidden files: shell execution, package installs, destructive git, network/provider commands, long-running commands, writes except approved receipt/evidence.

Phases:

- Phase 6.1: Exact allowlist proof.
- Phase 6.2: Execution receipt proof.
- Phase 6.3: Safe-write verification attachment.

Increment 6.1.1:

- Goal: Reprove exact argv allowlist and forbidden command rejection.
- Allowed files or file zones: verification runner/tests.
- Forbidden files or zones: broad shell strings, mutating commands, package installs.
- Exact checks Codex should run: `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_verification_runner.py`.
- Exact manual checks Britton should run: review allowlist entries and timeout limit.
- Expected output: only exact approved commands can run.
- Stop conditions: shell metacharacters accepted, destructive git accepted, typecheck failure.
- Rollback or recovery guidance: keep Level 2; disable runner endpoint if unsafe.
- Next target: Increment 6.2.1.

Increment 6.2.1:

- Goal: Run one exact focused verification command and record receipt summary.
- Allowed files or file zones: no file writes unless approved receipt/evidence path.
- Forbidden files or zones: broad test suites, npm build, installs, long commands.
- Exact checks Codex should run: exact command chosen by Britton, for example `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_verification_runner.py`.
- Exact manual checks Britton should run: inspect stdout/stderr summary and receipt.
- Expected output: pass/fail captured without hidden mutation.
- Stop conditions: command timeout, route behavior mismatch, generated files touched.
- Rollback or recovery guidance: stop runner promotion; preserve failed receipt.
- Next target: Phase 6 closeout.

Phase 6 Closeout:

- Terminal Block: use Section 8 Plan 6 block.
- Verification Steps: runner tests, exact command receipt, diff check.
- Visual Checks: if UI touched, verification status shows result and authority level.
- Expected Output: Level 3 verification runner proof.
- Debug Path: inspect command id, argv, cwd, timeout, exit code.
- Next Target: Plan 7.
- Permission Gate: `Britton, approve Plan 7: One-task queue proof?`

### Plan 7: One-Task Queue Proof

Purpose: Prove Cartographer can select and execute one safe supervised task, with no background loop.

Grade target improved: queue/workflow readiness, daily-driver readiness.

Authority before: Level 3.

Authority after: Level 4 supervised one-task queue.

Allowed files: `safe_task_queue.py`, `workflow_runner.py`, `workflow_controls.py`, `workflow_state.py`, ledger, API route, focused tests, exact receipt/evidence file.

Forbidden files: background loops, multiple task execution, worker dispatch, source writes, commit/push.

Phases:

- Phase 7.1: Queue durability and one-task selection.
- Phase 7.2: Supervised task execution.
- Phase 7.3: Kill switch and stop drill.

Increment 7.1.1:

- Goal: Prove queue records are durable and select at most one eligible task.
- Allowed files or file zones: queue/workflow model/tests.
- Forbidden files or zones: executing task body.
- Exact checks Codex should run: `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_workflow_state.py source_proxy/tests/test_cartographer_workflow_controls.py`.
- Exact manual checks Britton should run: inspect selected task id, approval token id, allowed files, forbidden files.
- Expected output: one task selected or clear blocked reason.
- Stop conditions: more than one task selected, approval missing, queue fetch failed.
- Rollback or recovery guidance: mark task blocked/cancelled by event; no cleanup.
- Next target: Increment 7.2.1.

Increment 7.2.1:

- Goal: Execute one safe docs/evidence maintenance task under supervision.
- Allowed files or file zones: exact approved docs/evidence/receipt file.
- Forbidden files or zones: source/UI/test/package/config/generated/media.
- Exact checks Codex should run: focused queue/workflow/safe-write tests; exact verification command from Plan 6.
- Exact manual checks Britton should run: watch queue state before/after, receipt, rollback, kill switch visibility.
- Expected output: one completed or blocked task with receipt.
- Stop conditions: hidden mutation detected, queue tries next task, missing receipt.
- Rollback or recovery guidance: stop queue; use receipt rollback guidance only with explicit approval.
- Next target: Phase 7 closeout.

Phase 7 Closeout:

- Terminal Block: use Section 8 Plan 7 block.
- Verification Steps: queue/workflow tests, exact receipt diff, status.
- Visual Checks: `/map` shows one-task status and no background loop.
- Expected Output: Level 4 supervised queue proof.
- Debug Path: inspect event ledger from task_selected through closeout.
- Next Target: Plan 8.
- Permission Gate: `Britton, approve Plan 8: Worker/subagent visible coordination proof?`

### Plan 8: Worker/Subagent Visible Coordination Proof

Purpose: Prove worker coordination is visible, leased, file-scoped, and cannot bypass queue/control.

Grade target improved: worker/subagent readiness, real operator control.

Authority before: Level 4.

Authority after: Level 5 visible leased worker coordination.

Allowed files: `worker_contract.py`, `multi_worker_branch_workflow.py`, `lane_registry.py`, API route, focused tests, `/map` display if approved.

Forbidden files: hidden worker spawn, provider calls, broad file ownership, branch/worktree creation, source edits by workers unless separately approved.

Phases:

- Phase 8.1: Worker identity and leases.
- Phase 8.2: Ownership conflict and stale closeout.
- Phase 8.3: One worker, one task, one file-zone proof.

Increment 8.1.1:

- Goal: Prove worker identity, lease, heartbeat, and exact file zone are required.
- Allowed files or file zones: worker contract/tests.
- Forbidden files or zones: actual worker dispatch.
- Exact checks Codex should run: `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_worker_contract.py source_proxy/tests/test_cartographer_multi_worker_branch_workflow.py`.
- Exact manual checks Britton should run: inspect worker card and lease expiry.
- Expected output: worker is visible and cannot mutate without task/approval/zone.
- Stop conditions: hidden worker state, broad zone, stale worker not blocked.
- Rollback or recovery guidance: expire lease and create stale closeout proposal.
- Next target: Increment 8.2.1.

Increment 8.2.1:

- Goal: Prove one visible worker can coordinate a docs/evidence task without dispatch bypass.
- Allowed files or file zones: exact worker contract/evidence docs only.
- Forbidden files or zones: branch/worktree creation, source edits, provider calls.
- Exact checks Codex should run: focused worker and queue tests; `git diff --check`.
- Exact manual checks Britton should run: confirm assigned file zone, receipt refs, closeout expectation.
- Expected output: visible coordination receipt, no hidden mutation.
- Stop conditions: lease mismatch, ownership overlap, worker dispatch unavailable, protected lane overlap.
- Rollback or recovery guidance: close worker as blocked/stale; do not delete files.
- Next target: Phase 8 closeout.

Phase 8 Closeout:

- Terminal Block: use Section 8 Plan 8 block.
- Verification Steps: worker tests, conflict checks, status.
- Visual Checks: `/map` worker card shows lease, zone, stale/blocked state.
- Expected Output: Level 5 visible worker coordination proof.
- Debug Path: compare worker contract to event ledger and queue receipt.
- Next Target: Plan 9.
- Permission Gate: `Britton, approve Plan 9: Commit/branch/push proposal and supervised local commit proof?`

### Plan 9: Commit/Branch/Push Proposal And Supervised Local Commit Proof

Purpose: Prove exact-file local commits under human approval while keeping branch/worktree/push proposal-only.

Grade target improved: commit/push readiness, real operator control.

Authority before: Level 5.

Authority after: Level 6 supervised local commit proposals; Level 9 push proposal only if separately approved.

Allowed files: `local_commit_gate.py`, `controlled_push_queue.py`, `branch_recommendations.py`, focused tests, exact approved docs/evidence/receipt files for a local commit proof.

Forbidden files: broad staging, `git add .`, push execution, force push, branch/worktree creation unless later separately approved.

Phases:

- Phase 9.1: Commit proposal validation.
- Phase 9.2: Human-approved local commit proof.
- Phase 9.3: Push proposal remains separate.

Increment 9.1.1:

- Goal: Validate exact commit proposal with checks, rollback, expected HEAD, and exact file list.
- Allowed files or file zones: commit gate/tests.
- Forbidden files or zones: staging/commit execution.
- Exact checks Codex should run: `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_local_commit_gate.py source_proxy/tests/test_cartographer_controlled_push_queue.py`.
- Exact manual checks Britton should run: inspect exact files, message, verification, rollback command.
- Expected output: commit proposal accepted or blocked; no git mutation.
- Stop conditions: broad staging allowed, source files included without approval, failed verification.
- Rollback or recovery guidance: edit proposal only; do not reset.
- Next target: Increment 9.2.1.

Increment 9.2.1:

- Goal: Perform one supervised local commit only if Britton gives exact approval phrase and file list.
- Allowed files or file zones: exact approved files only.
- Forbidden files or zones: push, branch/worktree, broad staging, cleanup.
- Exact checks Codex should run: `git status --branch --short`; exact focused tests; `git diff --check -- <exact-files>`.
- Exact manual checks Britton should run: verify commit SHA, diff, rollback guidance, and no push.
- Expected output: one local commit, receipt, no push.
- Stop conditions: extra staged files, HEAD mismatch, test failure, approval unclear.
- Rollback or recovery guidance: use `git revert <sha>` only after explicit Britton approval; do not reset.
- Next target: Phase 9 closeout.

Phase 9 Closeout:

- Terminal Block: use Section 8 Plan 9 block.
- Verification Steps: commit gate tests, status, log, no remote push.
- Visual Checks: `/map` says local commit proof and push still gated.
- Expected Output: Level 6 supervised local commit proof; no auto-push.
- Debug Path: compare exact approved files to committed diff.
- Next Target: Plan 10.
- Permission Gate: `Britton, approve Plan 10: Supervised daily-driver trial?`

### Plan 10: Supervised Daily-Driver Trial

Purpose: Run Cartographer as a supervised daily-driver assistant on safe tasks only.

Grade target improved: auto daily-driver readiness.

Authority before: Level 6.

Authority after: Level 7 supervised daily-driver loop.

Allowed files: exact docs/evidence/receipt files, queue/workflow/approval/ledger modules if bugs are found and Britton approves, focused tests.

Forbidden files: auto-push, source edits by default, hidden workers, broad git, package/config/env, generated/cache, media.

Phases:

- Phase 10.1: One supervised task.
- Phase 10.2: Ten supervised safe-task receipts.
- Phase 10.3: False positive/false negative tracking.

Increment 10.1.1:

- Goal: Run one real supervised safe task from queue to receipt.
- Allowed files or file zones: exact approved task files and receipts.
- Forbidden files or zones: unapproved source or git mutation.
- Exact checks Codex should run: queue/workflow/safe-write/verification focused tests; exact task verification.
- Exact manual checks Britton should run: observe `/map`, approve token, inspect receipt, confirm next task did not auto-run.
- Expected output: one supervised receipt.
- Stop conditions: hidden mutation, queue continues, kill switch unclear, manual visual check failure.
- Rollback or recovery guidance: stop queue; demote to Level 4; apply receipt rollback only with approval.
- Next target: Increment 10.2.1.

Increment 10.2.1:

- Goal: Accumulate 10 supervised safe-task receipts.
- Allowed files or file zones: approved safe docs/evidence/receipt paths only.
- Forbidden files or zones: source, package/config/env, generated/cache, auto-push.
- Exact checks Codex should run: exact focused tests after each task; `git diff --check -- <changed-files>`.
- Exact manual checks Britton should run: review each receipt and mark pass/fail, false positive, false negative.
- Expected output: 10 receipts with no hidden mutation.
- Stop conditions: any failed task without clear blocked state, receipt gap, test failure.
- Rollback or recovery guidance: pause trial and write decision packet.
- Next target: Phase 10 closeout.

Phase 10 Closeout:

- Terminal Block: use Section 8 Plan 10 block.
- Verification Steps: receipt count, focused tests, status, hidden mutation scan.
- Visual Checks: `/map` daily-driver trial summary, blockers, next action, receipts.
- Expected Output: Level 7 supervised daily-driver evidence.
- Debug Path: inspect each receipt and event sequence.
- Next Target: Plan 11.
- Permission Gate: `Britton, approve Plan 11: Soak, drills, and promotion decision packet?`

### Plan 11: Soak, Drills, And Promotion Decision Packet

Purpose: Prove stability through 24h/72h soak, hidden mutation drills, kill-switch drills, rollback drills, and final decision packet.

Grade target improved: auto daily-driver readiness, safety boundaries.

Authority before: Level 7.

Authority after: Level 7 plus promotion evidence; no automatic promotion.

Allowed files: soak/drill modules/tests, exact docs/evidence/receipt decision packet.

Forbidden files: activation toggles, self-promotion, auto-push, hidden queues/workers.

Phases:

- Phase 11.1: 24h supervised soak.
- Phase 11.2: 72h supervised soak.
- Phase 11.3: Hidden mutation, kill-switch, rollback drills.
- Phase 11.4: Promotion decision packet.

Increment 11.1.1:

- Goal: Record 24h soak evidence without self-promotion.
- Allowed files or file zones: exact soak evidence/receipt files.
- Forbidden files or zones: activation flags, auto queue, auto push.
- Exact checks Codex should run: `.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_daily_driver_soak.py source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py`.
- Exact manual checks Britton should run: inspect 24h evidence for drift, stop events, false positives/negatives.
- Expected output: 24h evidence packet.
- Stop conditions: hidden mutation, queue state drift, generated/cache files involved.
- Rollback or recovery guidance: demote to supervised only; preserve evidence.
- Next target: Increment 11.2.1.

Increment 11.2.1:

- Goal: Record 72h soak evidence plus drills and decision packet.
- Allowed files or file zones: exact drill/decision docs/evidence.
- Forbidden files or zones: runtime activation.
- Exact checks Codex should run: focused final proof tests for stages 3 through 7 and trust-tier gate.
- Exact manual checks Britton should run: approve, hold, or demote in a written decision; no implicit promotion.
- Expected output: trust-tier decision packet ready for Britton.
- Stop conditions: missing drill, missing rollback, approval validation unavailable, Codex uncertainty.
- Rollback or recovery guidance: hold at Level 7; open bug plan.
- Next target: Phase 11 closeout.

Phase 11 Closeout:

- Terminal Block: use Section 8 Plan 11 block.
- Verification Steps: soak/drill/readiness tests, decision packet check.
- Visual Checks: `/map` shows promotion decision pending, not active.
- Expected Output: promotion packet, no activation.
- Debug Path: inspect failed proof category and demotion trigger.
- Next Target: Plan 12 only if Britton explicitly promotes.
- Permission Gate: `Britton, approve Plan 12: Limited daily-driver activation gate?`

### Plan 12: Limited Daily-Driver Activation Gate, Only If Britton Explicitly Approves

Purpose: Activate limited daily-driver auto only after explicit Britton promotion and proof gates.

Grade target improved: auto daily-driver readiness to A.

Authority before: Level 7.

Authority after: Level 8 limited daily-driver auto. Push remains Level 9 proposal only and Level 10 execution only after separate explicit approval.

Allowed files: exact runtime/config/docs/evidence files Britton names in the activation approval.

Forbidden files: auto-push, broad source edits, hidden workers, self-approval, package/config/env unless named, generated/cache, media.

Phases:

- Phase 12.1: Activation decision validation.
- Phase 12.2: Limited auto loop with kill switch.
- Phase 12.3: First limited daily-driver run and demotion proof.

Increment 12.1.1:

- Goal: Validate Britton's explicit promotion decision and exact allowed authority.
- Allowed files or file zones: exact files named in promotion decision.
- Forbidden files or zones: anything not named.
- Exact checks Codex should run: status, exact focused tests, approval token validation, kill switch check.
- Exact manual checks Britton should run: read final authority list and say whether Level 8 is approved.
- Expected output: Level 8 can start only if all gates pass.
- Stop conditions: ambiguous approval, unknown kill switch, dirty tree mismatch.
- Rollback or recovery guidance: do not activate; remain Level 7.
- Next target: Increment 12.2.1.

Increment 12.2.1:

- Goal: Run limited daily-driver auto under visible queue, leases, receipts, and demotion triggers.
- Allowed files or file zones: exact safe task classes and files named by approval.
- Forbidden files or zones: auto-push, broad git, hidden workers.
- Exact checks Codex should run: exact activation tests and one limited run verification.
- Exact manual checks Britton should run: observe `/map`, kill switch, receipts, demotion path.
- Expected output: limited auto run completes or blocks with receipt.
- Stop conditions: hidden mutation, no receipt, queue overrun, false promotion.
- Rollback or recovery guidance: activate kill switch, demote to Level 7, record incident.
- Next target: Phase 12 closeout.

Phase 12 Closeout:

- Terminal Block: use Section 8 Plan 12 block.
- Verification Steps: activation tests, receipt, status, no push.
- Visual Checks: `/map` shows Level 8 limited auto with kill switch visible and push blocked.
- Expected Output: limited daily-driver auto only if Britton explicitly approved.
- Debug Path: demote on any unclear state.
- Next Target: separate Level 9 push proposal plan, not automatic.
- Permission Gate: `Britton, do you want a separate push-proposal-only plan?`

## Section 5: Authority Ladder

| Level | Allowed | Forbidden | Required proof | Demotion triggers |
| --- | --- | --- | --- | --- |
| 0: Read-only command center | GET/read-only display, diagnostics, recommendations | writes, commands, queues, workers, commit, push | clean baseline, truthful NO-GO UI | stale truth, hidden action surface |
| 1: Proposal packets only | proposal and decision packets | approval consumption, writes, execution | canonical truth packet and evidence links | packet implies authority |
| 2: Approval-gated docs/evidence writes | exact human-approved docs/evidence/receipt writes | source writes, broad paths, git | valid token, event, receipt, rollback | invalid token, hidden mutation |
| 3: Verification runner | exact argv verification | shell, installs, destructive git, network, long commands | command receipt and allowlist tests | timeout, forbidden command accepted |
| 4: One-task queue, supervised only | one selected safe task with receipt | background loop, multiple tasks | queue event chain, kill switch proof | queue overrun, missing receipt |
| 5: Worker coordination, visible and leased only | visible worker contracts, exact file zones, leases | hidden dispatch, provider calls, broad zones | lease, heartbeat, conflict proof | stale/hidden worker, overlap |
| 6: Supervised local commit proposals | exact-file local commit after human approval | push, broad staging, branch/worktree | exact file list, checks, rollback | extra staged files, HEAD mismatch |
| 7: Supervised daily-driver loop | 10 supervised safe tasks | unattended auto, auto-push | 10 receipts, false positive/negative log | failed receipt, hidden mutation |
| 8: Limited daily-driver auto | limited safe tasks under kill switch | auto-push, self-promotion, broad source | Britton promotion, soak, drills | incident, drift, unclear authority |
| 9: Push proposal only | push packet, branch/sha/rollback proposal | push execution | exact proposal and approval packet | broad push, stale sha |
| 10: Push execution only after separate explicit approval | one exact approved push | force push, tags, main/master/trunk push unless named | separate approval, verification, rollback | push mismatch, remote surprise |

## Section 6: UI Simplification Standard

`/map` should feel like a calm operator cockpit:

- Top card: Can Cartographer act? `Yes`, `No`, or `Partial`.
- Next action card: one recommended action only.
- Blockers card: short list with reason codes.
- Evidence card: links and receipts.
- Control cards: disabled until authority exists.
- Details collapsed by default.
- Human wording, not internal jargon.
- Raw diagnostics available behind `/map/raw` drill-down.
- No automatic activation language unless Britton explicitly promotes Level 8.

## Section 7: Stop Conditions

Hard stop if any of these occur:

- Dirty tree returns unexpectedly.
- Protected-lane overlap.
- Unknown kill switch.
- Approval validation unavailable.
- Queue fetch failed.
- Hidden mutation detected.
- Generated/cache files involved.
- Package/config/env files touched without explicit approval.
- `source_proxy/agent_factory` touched without explicit approval.
- `src/app/coding` or `src/components/coding` touched without explicit approval.
- Test failure.
- Typecheck failure.
- Route behavior mismatch.
- Manual visual check failure.
- Codex uncertainty.

## Section 8: Manual Verification Blocks

Plan 0:

```bash
cd /home/source/SpiritOS
pwd
git status --branch --short
git log -1 --oneline
git branch --show-current
git worktree list
git diff --check
find docs -maxdepth 1 -iname '*cartographer*' | sort
find source_proxy -path '*cartographer*' -maxdepth 5 -type f | sort
find src/app -path '*map*' -maxdepth 5 -type f | sort
```

Plan 1:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- src/app/map
npm test -- run src/app/map/__tests__/map-display-shell.test.ts src/app/map/__tests__/map-information-architecture.test.ts
```

Plan 2:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py src/app/map
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_live_state.py source_proxy/tests/test_cartographer_api.py
```

Plan 3:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_approval_token_runtime.py source_proxy/tests/test_cartographer_approval_token_consumption.py source_proxy/tests/test_cartographer_workflow_event_ledger.py
```

Plan 4:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py src/app/map
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_workflow_event_ledger.py source_proxy/tests/test_cartographer_api.py
npm test -- run src/app/map/__tests__/map-display-shell.test.ts
```

Plan 5:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py docs/cartographer-live-evidence docs/cartographer-live-receipts
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_safe_write.py source_proxy/tests/test_cartographer_approval_token_consumption.py
```

Plan 6:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py docs/cartographer-live-evidence docs/cartographer-live-receipts
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_verification_runner.py source_proxy/tests/test_cartographer_safe_write.py
```

Plan 7:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py docs/cartographer-live-evidence docs/cartographer-live-receipts
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_workflow_state.py source_proxy/tests/test_cartographer_workflow_controls.py source_proxy/tests/test_cartographer_workflow_runner.py
```

Plan 8:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py src/app/map docs/cartographer-live-evidence docs/cartographer-live-receipts
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_worker_contract.py source_proxy/tests/test_cartographer_multi_worker_branch_workflow.py
```

Plan 9:

```bash
cd /home/source/SpiritOS
git status --branch --short
git log -1 --oneline
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py docs/cartographer-live-evidence docs/cartographer-live-receipts
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_local_commit_gate.py source_proxy/tests/test_cartographer_controlled_push_queue.py
```

Plan 10:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py docs/cartographer-live-evidence docs/cartographer-live-receipts
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_workflow_runner.py source_proxy/tests/test_cartographer_daily_driver_soak.py
```

Plan 11:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py docs/cartographer-live-evidence docs/cartographer-live-receipts
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_daily_driver_soak.py source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py source_proxy/tests/test_cartographer_final_proof_stage_3_hidden_mutation.py source_proxy/tests/test_cartographer_final_proof_stage_4_approval_kill_switch.py source_proxy/tests/test_cartographer_final_proof_stage_5_rollback.py source_proxy/tests/test_cartographer_final_proof_stage_7_readiness.py source_proxy/tests/test_cartographer_trust_tier_decision_gate.py
```

Plan 12:

```bash
cd /home/source/SpiritOS
git status --branch --short
git log -1 --oneline
git diff --check -- source_proxy/cartographer source_proxy/api/cartographer.py src/app/map docs/cartographer-live-evidence docs/cartographer-live-receipts
.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_workflow_runner.py source_proxy/tests/test_cartographer_daily_driver_soak.py source_proxy/tests/test_cartographer_trust_tier_decision_gate.py
```

## Section 9: New Chat Handoff

Copy-paste handoff for Britton:

```text
You are working in /home/source/SpiritOS.

Start only Cartographer A-Grade Daily Driver Activation PIVOT Plan v0.1, next plan: Plan 0 Verified Baseline And Lane Freeze.

Use PIVOT. Execute phase-by-phase and increment-by-increment. For each increment, state:
- current plan, phase, increment
- goal
- allowed files/zones
- forbidden files/zones
- exact Codex checks
- exact Britton manual checks
- expected output
- stop conditions
- rollback/recovery guidance
- next target

Do not implement beyond Plan 0. Do not change runtime code, UI code, source_proxy behavior, queue behavior, worker behavior, approval-token behavior, apply/write operators, package/config/env files, generated/cache files, media, git state, branches, worktrees, commits, pushes, cleanup, deletion, reset, stash, or checkout.

At the end of each phase, output exactly:
- Terminal Block
- Verification Steps
- Visual Checks
- Expected Output
- Debug Path
- Next Target
- Permission Gate

Plan 0 expected terminal block:

cd /home/source/SpiritOS
pwd
git status --branch --short
git log -1 --oneline
git branch --show-current
git worktree list
git diff --check
find docs -maxdepth 1 -iname '*cartographer*' | sort
find source_proxy -path '*cartographer*' -maxdepth 5 -type f | sort
find src/app -path '*map*' -maxdepth 5 -type f | sort

Visual Checks:
None for Plan 0.

Stop at the end of Plan 0 and ask Britton for permission before starting Plan 1. Do not infer permission from a clean result.
```

Optional Plan 1 handoff after Plan 0 passes:

```text
Start only Plan 1: /map UI usefulness reset to A-grade operator cockpit from docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md.

Use PIVOT. Execute phase-by-phase and increment-by-increment. Manual visual checks are required before moving forward. Do not implement beyond Plan 1. Stop at Plan 1 closeout and ask Britton for permission before Plan 2.

Plan 1 expected terminal block:

cd /home/source/SpiritOS
git status --branch --short
git diff --check -- src/app/map
npm test -- run src/app/map/__tests__/map-display-shell.test.ts src/app/map/__tests__/map-information-architecture.test.ts

Visual Checks:
- /map desktop 1440px: top status answers Can Cartographer act, next action is one item, blockers are short, evidence links exist, controls are disabled unless authority exists, details are collapsed.
- /map mobile 390px: no text overlap, no clipped controls, raw diagnostics link visible.
- /map/raw: detailed diagnostics remain available.
```

## Section 10: Final Closeout

For this planning run:

- Files changed: `docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md`.
- Verified: current branch, commit, clean status, worktree list, diff check, Cartographer docs/source/map file inventories, and relevant code/test surfaces by read-only inspection.
- Planning-only: yes.
- Implementation performed: no.
- Runtime/UI/source behavior changes: no.
- Queue execution, worker execution, approval-token consumption, apply/write operator changes: no.
- Commits or pushes: no.
- Next recommended Codex prompt: start only Plan 0 using the Section 9 handoff.

Single manual verification block for Britton:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md docs/plan-index.md
test -f docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md
grep -n "Plan 0" docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md
grep -n "UI usefulness" docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md
grep -n "Real operator control" docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md
grep -n "Auto daily-driver readiness" docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md
grep -n "Permission Gate" docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md
```

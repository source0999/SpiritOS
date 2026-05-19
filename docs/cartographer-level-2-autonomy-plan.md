# Cartographer Level 2 Autonomy Plan

## Current State

Cartographer Level 1 remains the evidence baseline. The Level 1 implementation closeout is preserved in `docs/cartographer-level-1-autonomy-plan.md` and must not be overwritten by this plan.

Current readiness output:

- recommendation: watch
- readiness score: 92
- level_1_authority_granted: False
- level_1_enablement_allowed: False

Targeted checks already reported as passing:

- Cartographer API slice: 33 passed
- Cartographer safety audit: 7 passed
- Proxy runner autonomy/soak slice: 4 passed
- Cartographer widget test: 3 passed

Known repo state:

- The worktree is dirty with mixed Level 1, Scout, CodingCockpitShell, deleted old plans, untracked soak logs, Playwright/config/test files, and other unrelated work.
- The next Level 1 increment was `Human Review Or Soak To Ready`.
- Level 2 may be planned now, but it must not be implemented until the Level 1 review gate is satisfied.

## Level 2 Definition

Level 2 is human-approved docs-only apply.

Level 2 adds exactly one capability beyond Level 1: Cartographer may apply a human-approved docs-only proposal.

Level 2 allows:

- Cartographer can take an already generated docs-only proposal.
- A human must explicitly approve that proposal.
- Cartographer may apply only the approved docs-only patch.
- Cartographer must write an audit/evidence receipt.
- Cartographer must show before and after status.
- Cartographer must show rollback instructions.
- Cartographer must remain blocked from commit and push.

Level 2 forbids:

- source code edits without human approval
- any app code edits under `src/**`
- any `source_proxy/**` edits by autonomy
- any `scout/src/**` edits by autonomy
- `backend/**` edits
- `scripts/**` edits
- `.env*` edits
- secrets, certificates, tokens
- `package.json`, lock files, `tsconfig`, eslint config, vitest config, next config
- delete or cleanup actions
- branch creation
- commit creation
- push queue creation
- merge
- self-promotion to Level 3
- apply without approval
- applying a proposal whose target path changed
- applying stale proposals
- applying when the dirty tree contains unclassified unrelated files

## Relationship To Level 1

Level 1 remains the evidence baseline. Level 2 depends on Level 1 being reviewed and either `ready_for_level_1_review` or explicitly accepted by Britton despite `watch`.

Level 2 must not weaken any Level 1 restriction. It adds only one new capability: approved docs-only apply.

## Phase 0: Preconditions Before Level 2

Purpose: Make sure Level 1 is reviewed and the dirty tree is understood before any apply authority is designed.

### Increment 0.1: Level 1 Review Gate

Goal: Confirm Level 1 closeout is accepted or identify what must be fixed first.

Likely files touched in future implementation:

- `docs/cartographer-level-1-autonomy-plan.md` for evidence review only
- `docs/cartographer-level-2-autonomy-plan.md` for planning updates only

Implementation notes:

- Do not implement Level 2 while Level 1 is still unresolved.
- Treat the existing Level 1 closeout as the baseline record, not as a draft to overwrite.
- If Level 1 remains `watch`, Level 2 implementation requires Britton to explicitly approve moving forward despite `watch`.

Manual checks:

```bash
cd /home/source/SpiritOS

grep -n "Implementation Closeout\\|Review packet\\|Still forbidden\\|Recommended next increment" docs/cartographer-level-1-autonomy-plan.md

PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_autonomy_promotion
payload = build_cartographer_autonomy_promotion()
print(payload["level_1_recommendation"])
print(payload["level_1_readiness_score"])
print(payload["level_1_authority_granted"])
print(payload["level_1_enablement_allowed"])
PY
```

Expected output:

- Level 1 remains authority false and enablement false.
- If Level 1 is still `watch`, Level 2 may be planned but not implemented until Britton approves moving forward.

Debug path:

- If the grep check cannot find closeout sections, stop and inspect the Level 1 document before continuing.
- If readiness output differs from the known state, record the new output and decide whether Level 1 must be updated first.

Rollback:

- Documentation-only rollback is to revert the Level 2 plan document change.
- Do not alter or delete the Level 1 evidence record.

Permission gate:

- Ask Britton before implementing Level 2 if Level 1 remains `watch`.

Next step:

- Classify the dirty tree before any apply authority is designed.

### Increment 0.2: Dirty Tree Quarantine Plan

Goal: Prevent Level 2 apply from operating in a noisy repo.

Likely files touched in future implementation:

- `source_proxy/cartographer/autopilot_apply.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

- Level 2 must require dirty tree classification before apply.
- Level 2 may allow known evidence files or known docs plan files only if explicitly classified.
- Unrelated dirty source files must block Level 2 apply.
- This repository's current dirty Scout, CodingCockpitShell, Cartographer, deleted-plan, config, test, and soak-log changes must be treated as unrelated until explicitly classified.
- The apply service must expose a `dirty tree block` rule when unclassified files are present.

Manual checks:

```bash
git status -sb
git diff --name-status
```

Expected output:

- The plan defines a `dirty tree block` rule.
- Level 2 apply refuses to run when unrelated files are dirty.

Debug path:

- If dirty files are present, classify them into allowed evidence/docs files or unrelated blockers.
- If a file cannot be classified, block apply and request human review.

Rollback:

- No file mutation should happen during dirty tree classification.
- If future implementation writes a receipt during classification, remove only that generated receipt after human review.

Permission gate:

- Britton must approve the dirty tree classification model before Level 2 apply is enabled.

Next step:

- Define the exact Level 2 authority contract.

## Phase 1: Level 2 Authority Contract

Purpose: Define exactly what new authority Level 2 adds.

### Increment 1.1: Approved Docs-Only Apply Contract

Goal: Write the contract for the single new allowed action.

Likely files touched in future implementation:

- `source_proxy/cartographer/autopilot_apply.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

Contract:

- apply_requires_human_approval: true
- allowed_scope: docs-only
- commit_allowed: false
- push_allowed: false
- branch_allowed: false
- delete_allowed: false
- cleanup_allowed: false
- self_promotion_allowed: false
- source_code_allowed: false

Allowed paths for Level 2 apply:

- `docs/**/*.md`
- `README.md` only if explicitly approved in the proposal
- named top-level markdown plan files only if explicitly approved and not deleted

Forbidden paths:

- `src/**`
- `source_proxy/**`
- `scout/src/**`
- `scout/config/**`
- `backend/**`
- `scripts/**`
- `tests/**`
- `.env*`
- `certificates/**`
- `package.json`
- `package-lock.json`
- `pnpm-lock.yaml`
- `yarn.lock`
- `tsconfig.json`
- `eslint.config.mjs`
- `vitest.config.mjs`
- `next.config.ts`
- `middleware.ts`
- any binary, generated, or build output

Manual checks:

```bash
grep -n "Approved Docs-Only Apply Contract" docs/cartographer-level-2-autonomy-plan.md
grep -n "Forbidden paths" docs/cartographer-level-2-autonomy-plan.md
git diff --check -- docs/cartographer-level-2-autonomy-plan.md
```

Expected output:

- The contract states that approval is required.
- The contract states that apply scope is docs-only.
- The contract states that commit, push, branch, delete, cleanup, self-promotion, and source code writes remain forbidden.

Debug path:

- If any future API output implies broader authority, treat it as a blocker.
- If a target path matches both an allowlist and a forbidlist, the forbidlist wins.

Rollback:

- Revert the contract change before implementation if review finds the scope too broad.
- Do not modify Level 1 evidence while revising this contract.

Permission gate:

- Britton must approve this contract before any apply service is built.

Next step:

- Define proposal eligibility rules.

## Phase 2: Proposal Approval Requirements

Purpose: Make sure Level 2 only applies proposals that are fresh, exact, and reviewed.

### Increment 2.1: Proposal Eligibility Rules

Goal: Define which proposals can be applied.

Likely files touched in future implementation:

- `source_proxy/cartographer/proposals.py`
- `source_proxy/cartographer/proposal_reviews.py`
- `source_proxy/cartographer/autopilot_apply.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

A proposal is eligible only if:

- proposal status is pending human approval
- proposal has exact target paths
- all target paths are docs-only and allowed
- proposal includes a patch or deterministic replacement
- proposal includes rollback hint
- proposal includes manual check command
- proposal includes `created_at` timestamp
- proposal includes `git_head_at_creation`
- current HEAD matches or proposal has been refreshed
- dirty tree has no unrelated unclassified files
- human approval ID exists
- approval timestamp exists
- approval actor is recorded
- approval does not come from Cartographer itself

Block if:

- proposal is stale
- proposal targets source code
- proposal target path no longer exists and delete/create behavior was not explicitly approved
- current git HEAD differs from proposal HEAD
- proposal attempts path traversal
- proposal uses absolute paths
- proposal includes secrets or secret-shaped content
- proposal would modify more files than approved

Manual checks:

```bash
grep -n "Proposal Eligibility Rules" docs/cartographer-level-2-autonomy-plan.md
grep -n "proposal is stale\\|path traversal\\|approval does not come from Cartographer" docs/cartographer-level-2-autonomy-plan.md
git diff --check -- docs/cartographer-level-2-autonomy-plan.md
```

Expected output:

- Only fresh, exact, reviewed, docs-only proposals can be applied.
- Stale, broadened, source-targeting, self-approved, or path-unsafe proposals are blocked.

Debug path:

- If eligibility is ambiguous, return `blocked` with all blocker reasons.
- If the proposal target path changed, require a refreshed proposal and a new human approval.

Rollback:

- Proposal eligibility writes no project files.
- A future invalid approval record should be marked superseded, not silently edited.

Permission gate:

- Britton must approve the proposal eligibility schema before apply behavior is wired.

Next step:

- Design the apply execution service without implementing it yet.

## Phase 3: Apply Execution Design

Purpose: Design the future implementation without writing it yet.

### Increment 3.1: Level 2 Apply Service Plan

Goal: Plan the service layer for approved docs-only apply.

Likely files touched in future implementation:

- `source_proxy/cartographer/autopilot_apply.py`
- `source_proxy/cartographer/proposal_reviews.py`
- `source_proxy/cartographer/proposals.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `src/app/v1/cartographer/docs-autopilot/apply/route.ts`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

The apply service must:

- load approved proposal
- validate approval
- validate exact target paths
- validate path allowlist
- validate current HEAD
- validate dirty tree
- run diff check before write when possible
- write only approved docs paths
- run `git diff --check` after write
- generate audit receipt
- return before and after status
- never stage
- never commit
- never push
- never create branch

Manual checks for future implementation:

```bash
curl -k -s https://localhost:3000/v1/cartographer/docs-autopilot/apply | jq .
git status -sb
git diff --check
```

Expected output:

- Without valid approval, apply returns blocked.
- With valid approval, only approved docs files change.
- No commit or push queue is created.

Debug path:

- If apply returns allowed without approval, disable the endpoint and fix approval validation first.
- If status changes include non-approved paths, treat it as a safety failure.
- If HEAD changes during the operation, block and require proposal refresh.

Rollback:

- Use the receipt rollback command to restore docs files changed by the approved patch.
- Do not use cleanup routines, staging resets, commits, or branch changes as rollback.

Permission gate:

- Apply service implementation cannot start until Level 1 review and the Level 2 contract are approved.

Next step:

- Define the audit receipt and rollback evidence packet.

## Phase 4: Audit Receipt And Rollback

Purpose: Every Level 2 apply must leave evidence.

### Increment 4.1: Apply Receipt Schema

Goal: Define the required evidence packet.

Likely files touched in future implementation:

- `source_proxy/cartographer/autopilot_apply.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- future receipt storage under an explicitly approved docs or evidence path

Implementation notes:

Receipt fields:

- level: 2
- mode: approved_docs_apply
- proposal_id
- approval_id
- approval_actor
- approval_timestamp
- git_head_before
- git_head_after
- head_changed: false
- dirty_status_before
- dirty_status_after
- files_requested
- files_allowed
- files_written
- files_blocked
- forbidden_paths_detected
- diff_check_before
- diff_check_after
- commit_created: false
- push_created: false
- branch_created: false
- rollback_command
- manual_check_commands
- created_at
- result: applied or blocked
- blocker_reasons

Manual checks:

```bash
grep -n "Apply Receipt Schema" docs/cartographer-level-2-autonomy-plan.md
grep -n "commit_created: false\\|push_created: false\\|branch_created: false" docs/cartographer-level-2-autonomy-plan.md
git diff --check -- docs/cartographer-level-2-autonomy-plan.md
```

Expected output:

- Receipt proves only docs changed.
- Receipt proves no commit, push, branch, or cleanup happened.

Debug path:

- If a receipt is missing required fields, treat apply as incomplete and block future Level 2 runs.
- If `git_head_before` differs from `git_head_after`, investigate immediately because Level 2 must not create commits.

Rollback:

- The receipt must include a rollback command specific to the applied docs patch.
- Rollback must be manual and human-visible.

Permission gate:

- Britton must approve the receipt schema before any Level 2 apply can be considered complete.

Next step:

- Write negative tests before any UI work.

## Phase 5: Tests Before Any UI

Purpose: Safety tests must exist before any nice dashboard button.

### Increment 5.1: Negative Tests

Goal: Specify tests that must fail unsafe behavior.

Likely files touched in future implementation:

- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- `source_proxy/tests/test_proxy_runner.py`
- supporting test fixtures only where required

Implementation notes:

Future tests should prove:

- unapproved apply is blocked
- stale proposal apply is blocked
- source path apply is blocked
- path traversal is blocked
- absolute path is blocked
- `.env` and secret-shaped path is blocked
- package and lock files are blocked
- dirty unrelated source files block apply
- HEAD mismatch blocks apply
- approved docs-only apply writes only approved docs
- apply does not stage
- apply does not commit
- apply does not push
- apply does not create branch
- apply does not create commit proposal
- apply does not create push queue item
- Cartographer cannot approve its own proposal
- Level 2 cannot self-promote to Level 3

Manual checks for future implementation:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_2 or apply or approved"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py -k "cartographer or autonomy"
```

Expected output:

- Unsafe paths and missing approval cases fail closed.
- Approved docs-only apply passes only when every precondition is satisfied.

Debug path:

- Fix blocking tests before creating any UI affordance.
- If a test requires a broad fixture, narrow the fixture until the safety rule is directly visible.

Rollback:

- Revert failing Level 2 implementation changes rather than weakening tests.
- Keep tests as the guardrail for future apply work.

Permission gate:

- Britton must approve the negative test coverage before any UI control is exposed.

Next step:

- Design the UI only after backend safety exists.

## Phase 6: UI Design For Level 2

Purpose: Expose Level 2 without making it feel more autonomous than it is.

### Increment 6.1: Level 2 Review Card Design

Goal: Plan UI changes only after backend safety exists.

Likely files touched in future implementation:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/__tests__/HomelabCartographerWidget.test.tsx`
- `src/styles/dashboard-demo-v4.css`

Implementation notes:

UI must show:

- Level 2: Human-approved docs apply
- Current status: disabled, blocked, watch, or ready_for_review
- Apply requires human approval
- Commit disabled
- Push disabled
- Source edits disabled
- Dirty tree blockers
- Last receipt
- Rollback command
- Manual checks

Do not add:

- one-click autopilot
- auto-commit
- auto-push
- source-code apply controls
- mobile execution controls

Manual checks:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_2 or apply or approved"
npm test -- HomelabCartographerWidget
git diff --check
```

Expected output:

- The UI reflects backend status and blockers.
- The UI does not expose unsafe controls or imply commit, push, source edits, or mobile execution.

Debug path:

- If the UI can trigger apply without an approval ID, remove the control and return to backend tests.
- If labels imply broader autonomy than the backend allows, rewrite labels around human approval and docs-only scope.

Rollback:

- Revert UI-only changes without touching backend safety tests.
- Disable any Level 2 controls if backend readiness falls back to `watch` or `blocked`.

Permission gate:

- UI work starts only after backend negative tests pass and Britton approves the safety copy.

Next step:

- Define Level 2 closeout criteria.

## Phase 7: Level 2 Closeout Criteria

Purpose: Define what `Level 2 ready` means.

### Increment 7.1: Level 2 Readiness Gates

Goal: Define promotion criteria.

Likely files touched in future implementation:

- `source_proxy/cartographer/autonomy_promotion.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- `src/components/dashboard/HomelabCartographerWidget.tsx`

Implementation notes:

Level 2 is ready only when:

- Level 1 is accepted or ready
- dirty tree is classified
- docs-only path filter exists
- approval validation exists
- apply receipt exists
- negative safety tests pass
- unapproved apply blocked
- source apply blocked
- stale apply blocked
- commit and push remain false
- UI does not expose unsafe controls
- manual check block is documented

Level 2 is not ready if:

- Level 1 remains `watch` and Britton has not accepted moving forward
- unrelated dirty source files exist
- apply can run without approval
- apply can touch source paths
- apply creates commit, push, or branch
- rollback hint is missing
- receipt is missing

Manual checks:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_2 or apply or approved"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py -k "cartographer or autonomy"
git status -sb
git diff --check
```

Expected output:

- Readiness remains blocked until Level 1 is accepted, dirty files are classified, and all safety checks pass.
- Authority output still proves no commit, push, branch, cleanup, or source write authority.

Debug path:

- If readiness is `ready` while a blocker exists, fix promotion logic before enabling apply.
- If manual checks are missing, readiness must remain blocked.

Rollback:

- Revert readiness logic if it promotes Level 2 too early.
- Preserve receipts and evidence for review rather than deleting them.

Permission gate:

- Britton must review the Level 2 closeout packet before Level 2 becomes active.

Next step:

- Start with backend blocked-apply contract tests.

## Phase 8: Recommended First Implementation Increment

Purpose: Give Britton the next safe step after the plan.

### Increment 8.1: Level 2 Blocked Apply Contract Tests

Goal: Build backend negative tests first for Level 2 apply blocking.

Likely files touched in future implementation:

- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- minimal test fixtures only if required

Implementation notes:

- Do not build UI first.
- Before allowing a single approved docs write, prove unsafe apply paths cannot run.
- Tests should lock down unapproved apply, stale proposal, source targets, path traversal, dirty unrelated files, HEAD mismatch, commit/push/branch creation, and self-promotion.

Manual check block:

```bash
cd /home/source/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_2 or apply"

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py

git status -sb
```

Expected output:

- New tests fail closed until Level 2 implementation exists.
- Existing Level 1 authority remains false.
- Repo status clearly separates intentional Level 2 test files from unrelated dirty work.

Debug path:

- If tests require source changes before they can express the blocked behavior, split the test fixture work from apply implementation.
- If unrelated dirty files interfere, stop and classify the tree with Britton before proceeding.

Rollback:

- Revert only the Level 2 test files if the increment is rejected.
- Leave Level 1 evidence untouched.

Permission gate:

- Ask Britton before starting implementation because Level 1 currently remains `watch` unless explicitly accepted.

Next step:

- After permission, implement `Level 2 blocked apply contract tests` before any service or UI changes.

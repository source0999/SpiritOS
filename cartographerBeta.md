# Cartographer Autonomy Master Plan v1
# Diagnostic-Informed Roadmap for SpiritOS Cartographer
# Status: BLOCKED UNTIL PHASE 0 CLEARS
# Owner: Britton
# Goal: Move Cartographer from governance beta to safe autonomy across Levels 0-10

## Executive Verdict

Cartographer is currently a strong governance agent, not a fully autonomous repo operator.

Current grade:
- Governance readiness: 8.2/10
- Safety posture: 9/10
- Autonomy readiness: 5.8/10
- Current operational status: BLOCKED

Why blocked:
- Repo ended dirty.
- Branch started 0/0 and ended ahead 1.
- HEAD changed during diagnostic from d7d38aa to 1c481d9.
- New local commit was not recorded as a Cartographer commit_created audit event.
- Push audit is now a BLOCKER, not only a harmless bootstrap warning.
- Drift count ended at 3.
- 3 drafted/pending blueprint proposals remain.
- Push queue count is 1, approval required, push disabled.
- Vitest targeted check failed for HomelabTestRunnerWidget.test.tsx due to ERR_MODULE_NOT_FOUND.
- Soak snapshots passed with reliability grade boring, but those results are superseded by the dirty/ahead/HEAD-change blockers.

Core rule:
A passing safety test or soak snapshot is evidence. It is not permission to apply, commit, push, merge, or enable autopilot.

## Research Anchors

This plan borrows from current open-source agent patterns, but keeps Cartographer stricter than most of them:

- Cline separates Plan mode from Act mode. Plan explores and strategizes without changing files, while Act executes against the plan. Cartographer should copy this separation and make promotion from recommend to act explicit, never automatic.
- Cline also has Auto Approve controls for routine actions, but Cartographer should only copy that idea after long proof and only for docs-only low-risk work.
- Aider’s repo map approach is relevant because it gives an LLM a compact map of important files, classes, functions, and relationships. Cartographer should strengthen its repo-map/component-map layer before expanding write authority.
- LangGraph durable execution and human-in-the-loop patterns are relevant because Cartographer needs resumable state, saved decisions, and explicit human approval before side effects.
- OpenHands shows where higher-agency coding agents are heading: control planes, isolated workspaces, safe execution, and auditability. Cartographer should become the repo control plane before becoming an autonomous actor.
- AutoGPT shows the continuous-agent direction, but also proves why Cartographer needs daily caps, feature flags, audit logs, and kill switches before any autopilot.
- CrewAI’s distinction between flexible Crews and structured Flows maps well to SpiritOS: sub-cartographers can behave like specialized agents, but Git/commit/push must remain a structured flow.
- mini-SWE-agent shows small agents can be powerful, but Cartographer should not copy maximal command-line autonomy until approval gates, state tracking, and rollback are boring.

Reference implications:
Cartographer should not become "one agent that does everything."
It should become a repo governance control plane with specialized sub-agents underneath it.

## Autonomy Levels

Level 0: Observe project state
Level 1: Explain dirty tree and changed files
Level 2: Classify changes by component and risk
Level 3: Detect blueprint, doc, test, and runbook drift
Level 4: Recommend branch and commit groups
Level 5: Draft commit messages and push readiness notes
Level 6: Create branch after approval
Level 7: Commit after approval
Level 8: Push after separate approval
Level 9: Docs-only autopilot, disabled by default, after long proof
Level 10: Broader autonomous project-start tracking for new repos/projects

Current diagnostic readiness:
- Level 0: GREEN
- Levels 1-8: YELLOW
- Levels 9-10: RED

The master plan must first convert Levels 1-8 from YELLOW to GREEN before Level 9 is allowed.

---

# PHASE 0: Stabilize the Current Branch Before More Autonomy

## Purpose

Clear the current BLOCKED state before building more autonomy.

Cartographer cannot be trusted with higher authority while the branch is dirty, ahead by 1, and carrying an unaudited local commit.

## Increment 0.1: Investigate the unaudited commit

Goal:
Find out why commit 1c481d9 appeared during the diagnostic and whether it was made by Codex, Cartographer, runner logic, or a manual process.

Likely files/modules to inspect:
- source_proxy/cartographer/audit_trail.py
- source_proxy/cartographer/git_approvals.py
- source_proxy/cartographer/commit_proposals.py
- source_proxy/testing/runner.py
- source_proxy/tests/test_proxy_runner.py
- source_proxy/cartographer/soak-logs/*
- scout/soak-logs/*

Allowed actions:
- read files
- run git log
- inspect audit trail
- inspect runner output
- inspect commit diff

Forbidden actions:
- no push
- no new commit
- no patch
- no apply
- no cleanup
- no branch creation

Manual checks:
Run:

cd ~/SpiritOS
git show --stat --oneline 1c481d9
git show --name-status 1c481d9
git show --format=fuller --no-patch 1c481d9
git status -sb
git log --oneline -10

Expected output:
- Exact files touched by 1c481d9 are known.
- Commit author/time is known.
- Commit reason is explainable.
- You know whether it should stay, be reverted, or be accepted into Cartographer’s audit model.

Debug path:
- If the commit only changed test hardening and is valid, keep it but do not push until the push lane is reviewed.
- If the commit was accidental, revert it through an explicit reviewed flow.
- If a runner or agent created it without permission, that is a major blocker.

Done criteria:
- Commit source explained.
- No mystery around HEAD change.
- Next action is explicit: keep, revert, or re-record audit evidence.

Permission gate:
Ask Britton before reverting, committing, or pushing anything.

## Increment 0.2: Resolve push-audit blocker

Goal:
Separate the original harmless bootstrap push warning from the new real push-audit blocker.

Context:
The first plain git push -u could be treated as a bootstrap warning.
The current state is different because there is now an ahead 1 local commit and push queue 1.

Allowed actions:
- inspect project-health output
- inspect push queue
- inspect audit trail
- inspect commit proposal records

Forbidden actions:
- no push
- no push approval
- no force push
- no audit backfill patch yet

Manual checks:
Run:

cd ~/SpiritOS
git status -sb
git rev-list --left-right --count HEAD...@{u}
git log --oneline --decorate -5

If server is running:

curl -k -s https://localhost:3000/v1/cartographer/project-health | jq .
curl -k -s https://localhost:3000/v1/cartographer/push-queue | jq .
curl -k -s https://localhost:3000/v1/cartographer/audit-trail | jq .

Expected output:
- project-health says merge_ready false until push audit is resolved
- push queue has exactly one pending item
- push disabled until approval
- no unapproved push has happened

Debug path:
- If push queue has more than one item, inspect duplication.
- If push is enabled without approval, stop and treat as safety bug.
- If project-health cannot distinguish bootstrap warning from current push audit, plan a future patch.

Done criteria:
- Push audit is classified as one of:
  - accepted bootstrap warning only
  - current blocker requiring review
  - safety bug

Current expected classification:
BLOCKER until commit 1c481d9 is explained and push is handled through Cartographer.

## Increment 0.3: Resolve dirty tree and soak-log policy

Goal:
Decide whether soak logs are source-controlled evidence or ignored runtime output.

Diagnostic issue:
Cartographer soak wrote expected snapshot logs, but additional Scout soak logs appeared during or around soak and phase-4f context checks.

Allowed actions:
- inspect git status
- inspect .gitignore
- inspect soak-log directories
- inspect runner docs

Forbidden actions:
- no deletion
- no cleanup
- no git add
- no commit

Manual checks:
Run:

cd ~/SpiritOS
git status --short
git status --short source_proxy/cartographer/soak-logs scout/soak-logs
git check-ignore -v source_proxy/cartographer/soak-logs/* scout/soak-logs/* 2>/dev/null || true

Expected output:
- You know whether soak logs are tracked, untracked, or ignored.
- You know whether the branch is dirty because of logs only or code changes too.

Debug path:
- If soak logs are intended evidence, keep them but require explicit commit grouping.
- If they are runtime artifacts, ignore them.
- If mixed, create a policy doc and apply it consistently later.

Done criteria:
- Dirty tree cause is known.
- Soak-log policy decision is ready for a later patch.

## Increment 0.4: Fix or reroute targeted Vitest failure

Goal:
Remove the false blocker or real blocker from HomelabTestRunnerWidget targeted Vitest.

Diagnostic issue:
TypeScript passed, lint passed, blueprint validation passed, diff check passed, but targeted Vitest failed with ERR_MODULE_NOT_FOUND involving Z:\@id\Z:\node_modules\vitest\dist\index.js.

Allowed actions:
- inspect test config
- inspect Vitest path handling
- inspect Windows/Z drive alias issue
- run targeted test

Forbidden actions:
- no broad UI refactor
- no unrelated dependency churn
- no package upgrades unless approved

Manual checks:
Run:

cd ~/SpiritOS
npx vitest run src/components/dashboard/__tests__/HomelabTestRunnerWidget.test.tsx --reporter=verbose
npx vitest run src/components/coding/__tests__/coding-workflow-step.test.ts --reporter=verbose
npm run typecheck 2>/dev/null || npx tsc --noEmit

Expected output:
- Either the test passes, or failure is clearly classified as environment/path config.
- TypeScript remains passing.

Debug path:
- If only Windows Z:\ path import is broken, patch Vitest config or test import path.
- If the test file path is wrong or missing, update target list.
- If component actually regressed, fix the component.

Done criteria:
- Targeted Vitest check passes or is intentionally rerouted with explanation.

## Increment 0.5: Re-run diagnostic after stabilization

Goal:
Confirm the repo is stable before moving to autonomy expansion.

Manual checks:
Run the full diagnostic again.

Expected output:
- Executive verdict: GO or GO WITH CAUTION
- dirty false, unless intentionally explained
- ahead/behind 0/0, or ahead state intentionally handled
- HEAD does not change during diagnostic
- push audit no longer BLOCKER
- drift count explainable
- proposal count explainable
- no unauthorized writes
- no unauthorized commits
- no unauthorized pushes
- targeted Vitest no longer blocking

Done criteria:
Phase 0 is complete only when Cartographer can complete a diagnostic without changing HEAD unexpectedly.

---

# PHASE 1: Make Levels 0-2 Boring and Trustworthy

## Purpose

Cartographer already observes the repo, but dirty-state reporting changed mid-run. This phase makes observation, explanation, and classification stable.

Target levels:
- Level 0: Observe project state
- Level 1: Explain dirty tree and changed files
- Level 2: Classify changes by component and risk

## Increment 1.1: Stable repo-state snapshot contract

Goal:
Create a single source-of-truth snapshot that captures branch, upstream, ahead/behind, dirty state, HEAD SHA, changed files, untracked files, and timestamp.

Likely files:
- source_proxy/cartographer/git_status.py
- source_proxy/cartographer/models.py
- source_proxy/cartographer/service.py
- source_proxy/api/cartographer.py
- src/app/v1/cartographer/git/route.ts
- source_proxy/tests/test_cartographer_api.py

Manual checks:
Run:

PYTHONPATH=. python3 -m pytest source_proxy/tests/test_cartographer_api.py
curl -k -s https://localhost:3000/v1/cartographer/git | jq .

Expected output:
- API returns HEAD SHA.
- API returns dirty file list.
- API returns upstream and ahead/behind.
- Snapshot has generated_at timestamp.
- No write action occurs.

Debug path:
- If HEAD SHA missing, add it to backend model first.
- If ahead/behind fails without upstream, return clear no_upstream reason.
- If dirty files are too noisy, add grouping but do not hide them.

Done criteria:
Cartographer can say exactly what repo state it saw and when.

## Increment 1.2: Dirty-tree explanation engine

Goal:
Turn dirty file lists into human-readable explanations.

Example output:
- "Scout soak logs changed because phase-4f closeout ran."
- "Cartographer code changed, likely affecting autonomy logic."
- "Unknown file changed, manual review required."

Likely files:
- source_proxy/cartographer/change_scribe.py
- source_proxy/cartographer/component_mapper.py
- source_proxy/cartographer/models.py
- src/app/v1/cartographer/change-scribe/route.ts
- src/components/dashboard/HomelabCartographerWidget.tsx

Manual checks:
Run:

curl -k -s https://localhost:3000/v1/cartographer/change-scribe | jq .
git status --short

Expected output:
- Each changed file has a category.
- Each category has a plain-English explanation.
- Unknown files are not silently treated as safe.

Done criteria:
Level 1 becomes GREEN.

## Increment 1.3: Component and risk classification hardening

Goal:
Make Cartographer classify changed files by component and risk.

Risk bands:
- low: docs, runbooks, comments, generated snapshot logs if policy allows
- medium: tests, UI widgets, route handlers
- high: approval gate, safety rules, apply/commit/push logic, secrets, env, Docker, auth
- blocked: protected paths, secrets, traversal, approval bypass, push bypass

Likely files:
- source_proxy/cartographer/component_mapper.py
- source_proxy/cartographer/safety.py
- source_proxy/cartographer/models.py
- source_proxy/tests/test_cartographer_safety_audit.py

Manual checks:
Run:

PYTHONPATH=. python3 -m pytest source_proxy/tests/test_cartographer_safety_audit.py
curl -k -s https://localhost:3000/v1/cartographer/components | jq .

Expected output:
- Changed files are classified by component.
- Risk levels are visible.
- Protected areas are labeled high or blocked.
- Classification does not grant permission.

Done criteria:
Level 2 becomes GREEN.

---

# PHASE 2: Make Drift and Blueprint Sync Reliable

## Purpose

Diagnostic showed drift count 3 and 3 drafted/pending proposals. That means drift detection works, but cleanup/review flow is not boring yet.

Target level:
- Level 3: Detect blueprint, doc, test, and runbook drift

## Increment 2.1: Drift state explanation

Goal:
Every drift item must explain:
- what changed
- what blueprint/doc/runbook is stale
- why Cartographer thinks it matters
- whether it is safe to ignore
- proposed next action

Likely files:
- source_proxy/cartographer/drift.py
- source_proxy/cartographer/blueprint_registry.py
- source_proxy/cartographer/proposals.py
- source_proxy/tests/test_cartographer_api.py

Manual checks:
Run:

curl -k -s https://localhost:3000/v1/cartographer/drift | jq .
curl -k -s https://localhost:3000/v1/cartographer/proposals | jq .

Expected output:
- Drift items are actionable.
- Proposal IDs map back to drift IDs.
- No duplicate drift proposals.

Done criteria:
Drift is useful, not noisy.

## Increment 2.2: Proposal review lifecycle

Goal:
Pending drift proposals must be easy to approve, reject, defer, or mark stale.

Likely files:
- source_proxy/cartographer/proposal_reviews.py
- source_proxy/cartographer/proposals.py
- source_proxy/api/cartographer.py
- src/app/v1/cartographer/proposals/[proposalId]/review/route.ts
- src/components/dashboard/HomelabBlueprintReviewWidget.tsx

Manual checks:
Run:

curl -k -s https://localhost:3000/v1/cartographer/proposals | jq .

In UI:
- Open dashboard Cartographer/Blueprint widget.
- Confirm pending proposals are visible.
- Confirm each has review state.
- Do not approve unless intentionally testing.

Expected output:
- Drafted/pending proposals are understandable.
- Reject/defer states persist.
- Duplicate proposals do not reappear.

Done criteria:
Level 3 becomes GREEN when drift can be reviewed without clutter.

---

# PHASE 3: Branch and Commit Recommendation Engine

## Purpose

Move Levels 4 and 5 to GREEN.

Target levels:
- Level 4: Recommend branch and commit groups
- Level 5: Draft commit messages and push readiness notes

## Increment 3.1: Branch recommendation confidence

Goal:
Cartographer should recommend whether to stay on current branch, create a new branch, or stop because branch state is unsafe.

Rules:
- dirty tree can still be explained
- ahead branch cannot be called merge-ready
- push audit blocker must block merge readiness
- unaudited commit must block autonomy escalation

Likely files:
- source_proxy/cartographer/branch_recommendations.py
- source_proxy/cartographer/project_health.py
- source_proxy/tests/test_cartographer_api.py

Manual checks:
Run:

curl -k -s https://localhost:3000/v1/cartographer/branch-recommendations | jq .
curl -k -s https://localhost:3000/v1/cartographer/project-health | jq .

Expected output:
- Branch recommendation is explicit.
- Unsafe branch states are blocked.
- Bootstrap warning and real blocker are distinguished.

Done criteria:
Branch recommendations are safe enough to trust as advice.

## Increment 3.2: Commit proposal grouping

Goal:
Commit proposals should group changed files by component, risk, and story.

Example groups:
- Cartographer safety hardening
- Scout soak evidence parsing
- Dashboard test fix
- Docs/runbook update

Likely files:
- source_proxy/cartographer/commit_proposals.py
- source_proxy/cartographer/component_mapper.py
- source_proxy/cartographer/models.py

Manual checks:
Run:

curl -k -s https://localhost:3000/v1/cartographer/commit-proposals | jq .
git status --short

Expected output:
- No proposal includes unrelated high-risk files.
- No proposal stages files.
- No proposal commits files.
- Each proposal has risk label and human-readable summary.

Done criteria:
Level 4 becomes GREEN.

## Increment 3.3: Push readiness notes

Goal:
Push readiness must say exactly why push is allowed or blocked.

Required fields:
- branch
- upstream
- ahead/behind
- commits to push
- audit status
- approval status
- push disabled/enabled
- reason codes

Likely files:
- source_proxy/cartographer/push_queue.py
- source_proxy/cartographer/project_health.py
- source_proxy/cartographer/git_approvals.py

Manual checks:
Run:

curl -k -s https://localhost:3000/v1/cartographer/push-queue | jq .
curl -k -s https://localhost:3000/v1/cartographer/project-health | jq .

Expected output:
- Push blocked until separate approval.
- Push audit missing is visible.
- Commit IDs are visible.
- No push happens.

Done criteria:
Level 5 becomes GREEN.

---

# PHASE 4: Approval-Gated Branch Creation

## Purpose

Move Level 6 to GREEN.

Target level:
- Level 6: Create branch after approval

## Increment 4.1: Branch creation preview

Goal:
Before branch creation, Cartographer must preview:
- current branch
- target branch name
- reason
- source HEAD
- dirty-state requirement
- rollback command
- whether branch already exists

Likely files:
- source_proxy/cartographer/branch_recommendations.py
- source_proxy/cartographer/git_approvals.py
- source_proxy/cartographer/audit_trail.py
- source_proxy/tests/test_cartographer_api.py

Manual checks:
Run API preview only.
Do not approve.

Expected output:
- Preview generated.
- No branch created.
- Approval required.

Done criteria:
Branch creation is previewable without side effects.

## Increment 4.2: Branch creation after approval

Goal:
Allow branch creation only after explicit approval.

Manual checks:
Use a test branch name only, for example:
cartographer/test-branch-approval-smoke

Expected output:
- Approval event recorded.
- Branch created only after approval.
- Audit trail records old branch, new branch, HEAD SHA, and rollback.
- No commit or push happens.

Rollback:
Delete test branch only after explicit approval.

Done criteria:
Level 6 becomes GREEN.

---

# PHASE 5: Approval-Gated Commit Creation

## Purpose

Move Level 7 to GREEN.

Target level:
- Level 7: Commit after approval

This phase must not start until Phase 0 explains commit 1c481d9.

## Increment 5.1: Commit preview contract

Goal:
Before commit approval, Cartographer must show:
- exact files included
- exact files excluded
- risk level
- diff summary
- tests run
- audit state
- commit message
- rollback command

Likely files:
- source_proxy/cartographer/commit_proposals.py
- source_proxy/cartographer/proposal_previews.py
- source_proxy/cartographer/git_approvals.py
- source_proxy/cartographer/audit_trail.py

Manual checks:
Run commit preview.
Do not approve.

Expected output:
- Preview includes exact file list.
- High-risk files require stronger confirmation.
- Unknown files block commit proposal.
- No git commit happens.

Done criteria:
Commit preview is safe.

## Increment 5.2: Commit after approval

Goal:
Create commit only after approval and only for the exact reviewed file set.

Required audit event:
commit_created

Required fields:
- commit SHA
- parent SHA
- approved proposal ID
- approved file list
- excluded file list
- approver
- timestamp
- rollback command

Manual checks:
Use a tiny docs-only test commit first.

Expected output:
- Commit created only after approval.
- Audit trail contains commit_created.
- HEAD change is expected and recorded.
- Push queue updates but push remains disabled.

Done criteria:
Level 7 becomes GREEN.

## Increment 5.3: Prevent unaudited commit confusion

Goal:
If HEAD changes without Cartographer’s commit_created event, project-health must report:
unaudited_head_change

Likely files:
- source_proxy/cartographer/project_health.py
- source_proxy/cartographer/audit_trail.py
- source_proxy/cartographer/git_status.py

Manual checks:
Simulate or inspect current 1c481d9 case.

Expected output:
- Cartographer explains HEAD changed outside approved commit flow.
- Merge readiness false.
- Push readiness false.
- Required next action is explicit.

Done criteria:
The exact current diagnostic problem cannot become invisible again.

---

# PHASE 6: Approval-Gated Push

## Purpose

Move Level 8 to GREEN.

Target level:
- Level 8: Push after separate approval

## Increment 6.1: Push preview contract

Goal:
Before push approval, Cartographer must show:
- branch
- upstream
- commits to push
- commit audit status
- test status
- dirty state
- drift status
- push command preview
- rollback guidance

Likely files:
- source_proxy/cartographer/push_queue.py
- source_proxy/cartographer/git_approvals.py
- source_proxy/cartographer/project_health.py

Manual checks:
Run push queue preview.
Do not approve.

Expected output:
- Push disabled by default.
- Push approval separate from commit approval.
- Push audit missing blocks merge readiness.
- No push happens.

Done criteria:
Push preview is understandable and strict.

## Increment 6.2: Push after approval

Goal:
Allow push only after separate approval.

Manual checks:
Use a safe branch and docs-only commit first.

Expected output:
- Push happens only after approval.
- Audit trail records push_approved and push_completed.
- project-health no longer reports push audit missing for that pushed commit.
- ahead/behind returns 0/0.

Done criteria:
Level 8 becomes GREEN.

## Increment 6.3: Bootstrap push warning policy

Goal:
Teach Cartographer the difference between:
- first upstream branch bootstrap done manually
- current unaudited commit needing push approval
- real unsafe push bypass

Manual checks:
Inspect project-health on a freshly created branch and on current branch.

Expected output:
- Bootstrap warning is non-blocking only when no local unaudited commits remain.
- Current ahead commits require push lane approval.
- Project-health explains the difference.

Done criteria:
The old confusing warning becomes human-readable.

---

# PHASE 7: Docs-Only Autopilot Trial

## Purpose

Move Level 9 from RED to YELLOW, then eventually GREEN.

Target level:
- Level 9: Docs-only autopilot, disabled by default, after long proof

This phase must not start until Levels 0-8 are GREEN.

## Increment 7.1: Autopilot feature flag and kill switch

Goal:
Create explicit disabled-by-default settings.

Required flags:
- CARTOGRAPHER_DOCS_AUTOPILOT_ENABLED=false
- CARTOGRAPHER_DOCS_AUTOPILOT_DAILY_CAP=0 by default
- CARTOGRAPHER_AUTOPILOT_KILL_SWITCH=true by default

Forbidden paths:
- source_proxy/approval/*
- source_proxy/safety/*
- source_proxy/cartographer/git_approvals.py
- source_proxy/cartographer/push_queue.py
- source_proxy/cartographer/apply.py
- .env*
- docker-compose*
- package lockfiles
- auth/security files
- app code
- Scout activation code

Allowed paths:
- docs/**
- scout/docs/**
- source_proxy/cartographer/soak-logs only if policy says tracked
- blueprint docs only if explicitly allowed

Manual checks:
Run status route.

Expected output:
- docs_autopilot_enabled false
- daily cap 0
- kill switch true
- no autopilot action available

Done criteria:
Autopilot exists as visible disabled configuration only.

## Increment 7.2: Docs-only dry-run proposals

Goal:
Autopilot can suggest docs updates but cannot apply them.

Manual checks:
Run dry-run proposal generation.

Expected output:
- Proposal says dry_run true.
- Diff preview is available.
- No file changed.
- Approval unavailable unless explicitly enabled.

Done criteria:
Autopilot is only a planner.

## Increment 7.3: Docs-only auto-apply in sandboxed tiny scope

Goal:
Allow one tiny docs-only auto-apply per day, only after long soak and only if all gates are green.

Minimum gates:
- clean tree
- ahead/behind 0/0
- no drift blockers
- no high-risk touched files
- no pending push queue
- no unaudited HEAD change
- safety runner pass
- soak grade boring
- daily cap not exceeded
- kill switch off
- path allowlist match

Manual checks:
Use a tiny docs receipt file only.

Expected output:
- One docs-only change applied.
- Audit trail records autopilot_docs_apply.
- No commit.
- No push.
- Daily cap decrements or marks used.
- Kill switch can stop future runs.

Done criteria:
Level 9 becomes YELLOW.

## Increment 7.4: Long soak of docs-only autopilot

Goal:
Prove docs-only autopilot over repeated runs.

Manual checks:
Run for 7 days or simulated repeated cycles.

Expected output:
- no app code touched
- no safety code touched
- no approval code touched
- no secrets touched
- no commits without approval
- no pushes without approval
- no duplicate proposals
- no noisy drift loops
- all actions audited

Done criteria:
Level 9 becomes GREEN only after boring proof.

---

# PHASE 8: New Project Tracking and Starter Blueprints

## Purpose

Move Level 10 from RED to YELLOW.

Target level:
- Level 10: Broader autonomous project-start tracking for new repos/projects

## Increment 8.1: Project discovery read-only

Goal:
Detect new projects without writing to them.

Likely files:
- source_proxy/cartographer/project_discovery.py
- source_proxy/cartographer/starter_blueprints.py
- source_proxy/cartographer/models.py
- src/app/v1/cartographer/project-candidates/route.ts
- src/app/v1/cartographer/projects/route.ts

Manual checks:
Run project candidates route.

Expected output:
- New project candidates appear.
- No files are created in those projects.
- Each candidate has confidence and reason.

Done criteria:
Project tracking starts read-only.

## Increment 8.2: Starter blueprint proposal

Goal:
For a new project, draft starter blueprint suggestions:
- repo purpose
- stack guess
- scripts
- components
- risk areas
- suggested docs
- suggested tests
- suggested runbook

Manual checks:
Preview only.

Expected output:
- Starter blueprint proposal is clear.
- No project files created.
- Approval required.

Done criteria:
Cartographer can help new projects from the start without touching them.

## Increment 8.3: Approved starter blueprint write

Goal:
After approval, write starter blueprint docs into the new project.

Allowed files:
- docs/blueprint.md
- docs/runbook.md
- docs/progress.md
- README.md only if explicitly approved

Forbidden:
- app code
- package changes
- env files
- CI/CD secrets
- Git push

Manual checks:
Use a test repo.

Expected output:
- Docs created only after approval.
- Audit trail records project, files, and rollback.
- No commit or push unless separately approved.

Done criteria:
Level 10 becomes YELLOW.

---

# PHASE 9: Sub-Cartographers and Control Plane

## Purpose

Split Cartographer into specialized agents without giving them uncontrolled authority.

Sub-agents:
- Git Steward: branch, ahead/behind, clean tree, push readiness
- Commit Curator: commit grouping and messages
- Drift Auditor: blueprint/doc/test/runbook drift
- Blueprint Scribe: docs and blueprint drafts
- Safety Auditor: path/risk/approval checks
- Release Steward: merge readiness and release notes
- Project Scout: new repo/project detection
- Junk Curator: duplicate/clutter detection with low/mid/high deletion risk

## Increment 9.1: Sub-agent registry

Goal:
Register sub-cartographers with allowed inputs, outputs, authority level, and forbidden actions.

Manual checks:
Run:

curl -k -s https://localhost:3000/v1/cartographer/sub-cartographers | jq .

Expected output:
- Each sub-agent has role.
- Each sub-agent has max authority.
- No sub-agent can approve, apply, commit, push, or delete by default.

Done criteria:
Sub-agent boundaries are visible.

## Increment 9.2: Sub-agent output contracts

Goal:
Every sub-agent returns structured output:
- summary
- evidence
- recommendation
- risk
- required approval
- forbidden actions respected
- next manual check

Manual checks:
Inspect sub-agent outputs.

Expected output:
- No vague "looks good."
- Evidence-backed recommendations.
- No direct mutation.

Done criteria:
Sub-agents improve clarity without increasing risk.

## Increment 9.3: Control plane routing

Goal:
Cartographer decides which sub-agent should inspect a situation.

Examples:
- dirty tree -> Git Steward + Commit Curator
- blueprint drift -> Drift Auditor + Blueprint Scribe
- push queue -> Git Steward + Safety Auditor
- new project -> Project Scout + Blueprint Scribe
- deletion candidates -> Junk Curator + Safety Auditor

Manual checks:
Create test scenarios.

Expected output:
- Correct sub-agents are selected.
- No action happens without the parent control plane and approval gate.

Done criteria:
Cartographer becomes a real repo governance control plane.

---

# PHASE 10: Cleanup and Junk Curator

## Purpose

Build the future agent Britton asked about: detect clutter, duplicates, abandoned files, old outputs, and deletion candidates.

This phase must be conservative.

## Increment 10.1: Read-only clutter inventory

Goal:
List possible clutter without deleting anything.

Risk bands:
- low: obvious generated logs, duplicate snapshots, empty temp files, old repomix outputs
- medium: old docs, stale plans, duplicate components, unused test fixtures
- high: source code, configs, migrations, package files, safety files
- blocked: secrets, env, auth, approval, git, database, production configs

Manual checks:
Run clutter inventory.

Expected output:
- Candidates grouped by risk.
- No deletion.
- Each candidate has reason and confidence.

Done criteria:
Junk Curator is read-only.

## Increment 10.2: Low-risk deletion proposal

Goal:
Create deletion proposals only.

Manual checks:
Review low-risk candidates.

Expected output:
- No file deleted.
- Proposal includes exact files.
- Proposal includes rollback instructions.
- Mid/high-risk files require manual review.

Done criteria:
Deletion workflow is proposal-only.

## Increment 10.3: Approved low-risk cleanup

Goal:
Allow deletion only after explicit approval.

Manual checks:
Use test files only.

Expected output:
- Only approved files deleted.
- Audit trail records deletion.
- Rollback is available.
- No source files touched accidentally.

Done criteria:
Cleanup becomes controlled, not reckless.

---

# PHASE 11: Autonomy Metrics and Trust Dashboard

## Purpose

Cartographer needs a trust score that is evidence-based, not vibes-based.

Metrics:
- clean diagnostics count
- soak pass streak
- unauthorized HEAD change count
- push audit failures
- duplicate proposal count
- drift false positives
- approval bypass attempts blocked
- docs-only autopilot success count
- rollback success count
- human override count

## Increment 11.1: Trust score model

Goal:
Make trust score visible and explainable.

Manual checks:
Open dashboard widget.

Expected output:
- Score is visible.
- Score explains why it went up or down.
- Score does not grant authority by itself.

Done criteria:
Trust score helps decisions without becoming permission.

## Increment 11.2: Autonomy promotion gates

Goal:
Cartographer can recommend moving to a higher autonomy level, but cannot promote itself.

Promotion example:
- Level 5 -> Level 6 requires 5 clean diagnostics, no dirty unexplained states, no unauthorized HEAD changes, passing safety, passing soak.

Manual checks:
Inspect promotion recommendation.

Expected output:
- Recommendation only.
- Human approval required.
- No authority changes automatically.

Done criteria:
Autonomy expands deliberately.

---

# PHASE 12: Final v1.0 Definition

Cartographer v1.0 is ready when:

## Required GREEN levels

- Level 0 observe project state: GREEN
- Level 1 explain dirty tree: GREEN
- Level 2 classify component/risk: GREEN
- Level 3 detect drift: GREEN
- Level 4 recommend branch/commit groups: GREEN
- Level 5 draft commit/push readiness: GREEN
- Level 6 branch after approval: GREEN
- Level 7 commit after approval: GREEN
- Level 8 push after separate approval: GREEN
- Level 9 docs-only autopilot: at least YELLOW with feature flag disabled by default
- Level 10 project-start tracking: at least YELLOW, read-only or approval-gated only

## Required proof

- 3 clean full diagnostics in a row
- 3 clean cartographer-soak-snapshot runs in a row
- cartographer-safety PASS
- Cartographer API tests PASS
- proxy closeout PASS
- phase-4f closeout PASS or successor closeout PASS
- TypeScript PASS
- lint PASS or warnings-only
- blueprint validation PASS
- diff check PASS
- targeted Vitest PASS or intentionally rerouted
- no unauthorized commits
- no unauthorized pushes
- no unexplained HEAD changes
- push audit blocker resolved
- dirty tree always explained
- proposals deduped
- drift actionable
- rollback hints present in audit events

## v1.0 authority boundary

At v1.0, Cartographer may:
- observe repo state
- explain dirty tree
- classify risk
- detect drift
- draft blueprint/runbook/docs proposals
- recommend branch names
- recommend commit groups
- draft commit messages
- prepare push readiness notes
- create branches after approval
- commit after approval
- push after separate approval
- run docs-only autopilot only if explicitly enabled and capped

At v1.0, Cartographer may not:
- merge automatically
- push without separate approval
- commit without approval
- edit app code autonomously
- edit safety/approval/auth code autonomously
- delete files without approval
- touch secrets or env files
- bypass Source Proxy
- bypass Approval Gate
- promote its own authority level
- treat passing tests as permission

---

# Immediate Next Step

Do not start Phase 1 yet.

Start with Phase 0.

Recommended next prompt for Codex:

"Run Phase 0.1 only. Investigate why commit 1c481d9 was created during the diagnostic. Do not patch, commit, push, revert, or clean anything. Return the exact files touched, author/time, likely source of the commit, whether it appears safe, and whether it should be kept, reverted, or handled through Cartographer’s audit flow. End by asking permission before any action."

After Phase 0 clears, then continue to Phase 0.2.
Cartographer Trust Source v0.4 Master Plan

Status date: 2026-05-16
Owner: Britton
Track: Phase 6 - Blueprinter / Cartographer Trust Source
Main goal: Make Cartographer boring, reliable, and safe enough that Britton does not have to mentally manage dirty trees, branch timing, commit grouping, blueprint drift, or push readiness by hand.

Core rule

Cartographer may:

Observe project state.
Read Git status.
Classify files.
Detect dirty trees.
Detect blueprint drift.
Suggest branch names.
Suggest commit groups.
Suggest commit messages.
Draft blueprint/runbook/doc proposals.
Recommend push and merge readiness.
Produce audit evidence.

Cartographer may not:

Write files without approval.
Apply proposals without approval.
Create branches without approval.
Commit without approval.
Push without separate approval.
Merge without explicit approval.
Summarize secrets.
Scan outside allowlisted roots.
Let Scout trigger coding writes.
Bypass Source Proxy or Approval Gate.
Trust ladder
Level 0: Observe only
Level 1: Explain dirty tree and changed files
Level 2: Classify changes by component and risk
Level 3: Detect blueprint/doc/test drift
Level 4: Recommend branch and commit groups
Level 5: Draft commit messages and push readiness notes
Level 6: Create branch after approval
Level 7: Commit after approval
Level 8: Push after separate approval
Level 9: Optional docs-only autopilot after long proof, disabled by default
Sub-agent roles
Cartographer Core

Maps projects, roots, files, components, blueprints, and routes.

Git Steward Agent

Explains dirty trees, current branch, ahead/behind status, staged/unstaged files, and push readiness.

Commit Curator Agent

Groups changed files into clean commit proposals.

Blueprint Scribe Agent

Drafts blueprint, runbook, and documentation update proposals.

Drift Auditor Agent

Detects stale blueprints, missing tests, missing runbooks, and mismatched docs.

Release Steward Agent

Prepares branch closeout, push readiness, merge readiness, and release notes.

Safety Auditor Agent

Verifies no unsafe scans, no secret leaks, no unapproved writes, no unapproved commits, and no unapproved pushes.

Dashboard Review Agent

Turns all proposals into clean dashboard cards with approve, reject, request edit, and evidence views.

Phase 6.0 - 4F Readiness Gate
Goal

Confirm the proxy and Scout runner foundation is green enough before deeper Blueprinter work.

Files likely touched

None by default. Documentation only if stale:

docs/proxy-test-runner-plan.md
scout/docs/V0_3_PHASE4F_CLOSEOUT_EVIDENCE.md
scout/docs/V0_3_PHASE4F_PROXY_SCOUT_CLOSEOUT.md
Implementation notes

This phase should not rebuild 4F. It only checks that 4F is not blocking Phase 6.

Check that the system can run:

cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-smoke
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-source-gate
Manual checks

Run:

cd ~/SpiritOS
git status --short
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-smoke
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-source-gate

Confirm:

proxy-closeout passes or only has known expected skips
scout-smoke passes
scout-source-gate passes
no approve/apply/commit/push happens
git status does not gain surprise files
Expected outputs
proxy-closeout: pass
scout-smoke: pass
scout-source-gate: pass
applied_anything: false
mutated: false, except allowed soak snapshot logs if that profile is run
Debug steps if failed
If proxy closeout fails, stop Phase 6 and fix proxy runner first.
If Scout source gate fails, stop Phase 6 and fix Scout source review state first.
If git status changes unexpectedly, inspect changed files before proceeding.
If any test attempts apply/commit/push, treat as blocker.
Rollback plan

No code changes expected. Revert any accidental doc edits.

Recommended next step

Proceed to Increment 6.1 only after 4F readiness is green or explicitly de-risked.

Permission gate

Ask Britton before writing or patching anything for 6.1.

Increment 6.1 - Blueprint Source Layout Cleanup
Goal

Make _blueprints/ feel like a trustworthy source of truth instead of a pile of notes.

Files likely touched
_blueprints/INDEX.md
_blueprints/_schema/*
_blueprints/current/*
_blueprints/components/*
_blueprints/runbooks/*
_blueprints/history/*
_blueprints/proposals/*
scripts/validate-blueprints.mjs
Implementation notes

Create or normalize this structure:

_blueprints/
  INDEX.md
  _schema/
  current/
  components/
  runbooks/
  history/
  proposals/

Rules:

current/ holds active source-of-truth blueprints.
components/ holds component-specific docs.
runbooks/ holds manual operating instructions.
history/ holds old/deprecated docs.
proposals/ holds draft updates not yet accepted.
Nothing in history/ should be treated as current truth.
Deprecated docs must be labeled.
Manual checks

Run:

cd ~/SpiritOS
find _blueprints -maxdepth 2 -type f | sort
npm run validate:blueprints
git diff --stat

Confirm:

INDEX.md exists
_schema exists
current exists
components exists
runbooks exists
history exists
proposals exists
validation passes
no app/runtime files changed unless approved
Expected outputs
Blueprint layout valid
Active blueprints listed
Runbooks separated
Historical docs separated
Proposals separated
Debug steps if failed
If validation fails, check missing frontmatter or broken links.
If docs are misplaced, move them into current/components/runbooks/history/proposals.
If app files changed, reject and retry as docs-only.
Rollback plan

Use:

git restore _blueprints scripts/validate-blueprints.mjs
Recommended next step

Proceed to 6.2 for metadata and stable IDs.

Permission gate

Do not implement schema changes until Britton approves 6.2.

Increment 6.2 - Blueprint Metadata Schema and Stable IDs
Goal

Give every blueprint a stable machine-readable identity so Cartographer can trust what it indexes.

Files likely touched
_blueprints/_schema/blueprint-frontmatter.schema.md
_blueprints/INDEX.md
_blueprints/current/*.md
_blueprints/components/*.md
_blueprints/runbooks/*.md
scripts/validate-blueprints.mjs
source_proxy/cartographer/models.py
source_proxy/cartographer/blueprint_registry.py
Implementation notes

Each active blueprint should include frontmatter like:

blueprint_id: cartographer-trust-source
title: Cartographer Trust Source
project: SpiritOS
component: cartographer
doc_type: component_blueprint
status: active
source_of_truth: true
owner: Britton
code_paths:
  - source_proxy/cartographer/**
  - src/app/v1/cartographer/**
  - src/components/dashboard/HomelabBlueprintReviewWidget.tsx
related_blueprints:
  - source-proxy-approval-gate
  - scout-intelligence
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-16

Stable IDs must not change just because a title changes.

Manual checks

Run:

cd ~/SpiritOS
npm run validate:blueprints
python - <<'PY'
from source_proxy.cartographer.blueprint_registry import load_blueprints
items = load_blueprints()
print("blueprints:", len(items))
for item in items[:10]:
    print(item.blueprint_id, item.status, item.source_of_truth)
PY

Confirm:

No duplicate blueprint_id
Every active blueprint has code_paths
Every source_of_truth blueprint has last_verified
Deprecated/history docs are not treated as active truth
Expected outputs
blueprints: 18 or higher
No duplicate IDs
No missing required metadata
Debug steps if failed
Duplicate ID: rename one ID and update INDEX references.
Missing code paths: add paths or mark doc as runbook/history.
Parser error: inspect YAML frontmatter indentation.
Rollback plan

Revert schema and frontmatter changes:

git restore _blueprints scripts/validate-blueprints.mjs source_proxy/cartographer
Recommended next step

Proceed to 6.3 for read-only discovery hardening.

Permission gate

Ask Britton before touching Cartographer parser/model code.

Increment 6.3 - Read-Only Project Discovery Hardening
Goal

Make Cartographer safely detect projects without scanning outside allowed roots or writing anything.

Files likely touched
source_proxy/cartographer/project_discovery.py
source_proxy/cartographer/safety.py
source_proxy/cartographer/models.py
source_proxy/api/cartographer.py
src/app/v1/cartographer/projects/route.ts
src/app/v1/cartographer/status/route.ts
source_proxy/tests/test_cartographer_api.py
source_proxy/tests/test_cartographer_safety_audit.py
Implementation notes

Project discovery must:

Read only from allowlisted roots.
Use SPIRIT_PROJECT_PATH or explicit approved roots.
Detect markers like .git, package.json, README.md, requirements.txt, pyproject.toml.
Return write_policy: read_only.
Never inspect .env, .env.local, secrets, tokens, or ignored private folders.
Never write files.
Manual checks

Run:

cd ~/SpiritOS
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py
curl -s http://localhost:3000/v1/cartographer/status | jq .
curl -s http://localhost:3000/v1/cartographer/projects | jq .
git status --short

Confirm:

SpiritOS detected
project root is expected
write mode remains locked
no outside roots shown
git status unchanged
Expected outputs
{
  "project_id": "spiritos",
  "status": "detected",
  "write_policy": "read_only",
  "markers": [".git", "package.json", "README.md", "requirements.txt"]
}
Debug steps if failed
If no project detected, check SPIRIT_PROJECT_PATH.
If too many projects detected, tighten allowlist.
If secrets appear, block phase and add redaction tests.
If files change, reject patch.
Rollback plan
git restore source_proxy/cartographer source_proxy/api src/app/v1/cartographer source_proxy/tests
Recommended next step

Proceed to 6.4 for component mapping.

Permission gate

Ask Britton before adding or changing any discovery authority.

Increment 6.4 - Component Mapper and Risk Labels
Goal

Make every changed file understandable by component and risk.

Files likely touched
source_proxy/cartographer/component_mapper.py
source_proxy/cartographer/models.py
source_proxy/cartographer/project_health.py
source_proxy/tests/test_cartographer_api.py
source_proxy/tests/test_cartographer_safety_audit.py
src/app/v1/cartographer/components/route.ts
Implementation notes

Map paths like:

source_proxy/**                  -> Source Proxy
source_proxy/cartographer/**     -> Cartographer
scout/**                         -> Scout
src/app/api/scout/**             -> Scout Dashboard Bridge
src/app/v1/cartographer/**       -> Cartographer API Bridge
src/components/dashboard/**      -> Dashboard
src/app/chat/**                  -> Chat
src/app/oracle/**                -> Oracle
scripts/spiritdesktop-windows/** -> Windows Agent
_blueprints/**                   -> Blueprint System
docs/**                          -> Docs

Add risk levels:

low: docs, blueprints, runbooks, tests
medium: dashboard UI, non-critical API route
high: approval gate, apply, commit, push, secrets, env, sandbox, filesystem tools
blocked: .env.local, private keys, outside root, path traversal
Manual checks

Create a temporary test status by changing one doc and one safe UI file, then run:

cd ~/SpiritOS
git status --short
curl -s http://localhost:3000/v1/cartographer/components | jq .
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_cartographer_api.py

Confirm:

docs file maps to Docs or Blueprint System
UI file maps to Dashboard
.env.local is blocked/redacted
unknown files are labeled unknown, not guessed
Expected outputs
{
  "changed_files": [
    {
      "path": "_blueprints/current/cartographer.md",
      "component": "Blueprint System",
      "risk": "low"
    },
    {
      "path": "src/components/dashboard/HomelabCartographerWidget.tsx",
      "component": "Dashboard",
      "risk": "medium"
    }
  ]
}
Debug steps if failed
If file maps wrong, update mapping rules.
If unknown file is guessed, force component: unknown.
If secret path is shown, add block/redaction tests.
Rollback plan
git restore source_proxy/cartographer/component_mapper.py source_proxy/tests src/app/v1/cartographer
Recommended next step

Proceed to 6.5 for repo map and symbol awareness.

Permission gate

Ask Britton before adding higher-risk file classifications.

Increment 6.5 - Repo Map and Context Index
Goal

Give Cartographer compact repo understanding without reading the whole repo every time.

Files likely touched
source_proxy/cartographer/repo_map.py
source_proxy/context/inventory.py
source_proxy/api/context_inventory.py
source_proxy/vector/visual_index.py
source_proxy/tests/test_context_inventory.py
source_proxy/tests/test_visual_index.py
src/app/v1/cartographer/repo-map/route.ts
Implementation notes

Repo map should include:

Files indexed.
Key directories.
API routes.
Dashboard widgets.
Tests.
Blueprint links.
Component ownership.
Risk labels.
Last indexed time.

Do not include:

Secret values.
Full file contents by default.
Large generated files.
node_modules, .next, .git, backups, or excluded paths.
Manual checks

Run:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/repo-map | jq .
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_context_inventory.py source_proxy/tests/test_visual_index.py
git status --short

Confirm:

files_indexed present
components indexed
routes indexed
secret files excluded
no file writes unless explicitly approved cache file exists
Expected outputs
{
  "project_id": "spiritos",
  "map_version": 1,
  "files_indexed": 184,
  "components_indexed": 9,
  "routes_indexed": 20,
  "blueprints_indexed": 18
}
Debug steps if failed
If index is too huge, add excludes.
If secrets included, block and add tests.
If route count is zero, inspect Next route scanner.
If performance is bad, add bounded depth or caching.
Rollback plan
git restore source_proxy/cartographer/repo_map.py source_proxy/context source_proxy/vector src/app/v1/cartographer/repo-map
Recommended next step

Proceed to 6.6 for Git Steward read-only status.

Permission gate

Ask Britton before adding any persistent cache or index write.

Increment 6.6 - Git Steward Read-Only Dirty Tree View
Goal

Make dirty trees understandable before trying to automate anything.

Files likely touched
source_proxy/cartographer/git_status.py
source_proxy/cartographer/project_health.py
source_proxy/cartographer/models.py
source_proxy/api/cartographer.py
src/app/v1/cartographer/git/route.ts
src/components/dashboard/HomelabCartographerWidget.tsx
source_proxy/tests/test_cartographer_api.py
Implementation notes

Git Steward should report:

current branch
is main/master
dirty files
staged files
unstaged files
untracked files
ahead/behind origin
last commit
safe branch recommendation needed
commit proposal needed
push needed
merge readiness

No branch creation yet. No commit. No push.

Manual checks

Run:

cd ~/SpiritOS
git status --short
curl -s http://localhost:3000/v1/cartographer/git | jq .

Then create a test dirty file:

echo "test" > /tmp/cartographer-test.txt

Do not put it in repo. Confirm it does not show.

Then create a repo doc test:

echo "" >> docs/phase-8-manual-check.md
curl -s http://localhost:3000/v1/cartographer/git | jq .
git restore docs/phase-8-manual-check.md

Confirm:

dirty tree detected only for repo file
changed file classified
branch displayed
no branch created
no commit created
no push attempted
Expected outputs
{
  "branch": "cartographer/scout-blueprint-review",
  "dirty": true,
  "changed_file_count": 1,
  "needs_commit": true,
  "needs_push": false,
  "write_mode": "locked"
}
Debug steps if failed
If dirty files missing, inspect git command runner.
If untracked files missing, check --porcelain parsing.
If outside files show, block and fix root handling.
If branch/commit/push happens, stop and treat as safety regression.
Rollback plan
git restore source_proxy/cartographer/git_status.py src/app/v1/cartographer/git source_proxy/tests src/components/dashboard/HomelabCartographerWidget.tsx
Recommended next step

Proceed to 6.7 for commit grouping proposals.

Permission gate

Ask Britton before giving Git Steward any write authority.

Increment 6.7 - Commit Curator: Commit Group Proposals
Goal

Have Cartographer suggest clean commit groups so Britton does not have to organize every dirty tree manually.

Files likely touched
source_proxy/cartographer/commit_proposals.py
source_proxy/cartographer/models.py
source_proxy/cartographer/component_mapper.py
source_proxy/api/cartographer.py
src/app/v1/cartographer/commit-proposals/route.ts
src/components/dashboard/HomelabBlueprintReviewWidget.tsx
source_proxy/tests/test_cartographer_api.py
Implementation notes

Commit Curator should group by:

Component.
Risk.
File purpose.
Whether tests/docs/blueprints moved together.
Whether changes are already staged.
Whether generated/soak logs should be separated.

Example groups:

Group 1: docs(cartographer): add trust source plan
Group 2: test(cartographer): add safety audit coverage
Group 3: feat(dashboard): add blueprint review widget
Group 4: chore(scout): record soak snapshots

It must not run git add or git commit.

Manual checks

Make or keep a dirty tree with 2 to 5 files, then run:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/commit-proposals | jq .
git status --short

Confirm:

commit groups appear
files listed exactly once
suggested messages are editable
no files staged by endpoint
no commit created
Expected outputs
{
  "proposal_count": 2,
  "proposals": [
    {
      "title": "docs(cartographer): add trust source plan",
      "files": ["docs/cartographer-trust-source-plan.md"],
      "risk": "low",
      "requires_approval": true
    }
  ]
}
Debug steps if failed
If a file appears twice, fix grouping dedupe.
If risky file is grouped with docs, split high-risk changes.
If status changes after endpoint call, block and remove write behavior.
If message is low quality, improve templates.
Rollback plan
git restore source_proxy/cartographer/commit_proposals.py src/app/v1/cartographer/commit-proposals source_proxy/tests
Recommended next step

Proceed to 6.8 for blueprint drift proposals.

Permission gate

Ask Britton before implementing any staging or commit action.

Increment 6.8 - Drift Auditor and Blueprint Proposal Queue
Goal

Detect when code changed but blueprints, docs, tests, or runbooks did not keep up.

Files likely touched
source_proxy/cartographer/drift.py
source_proxy/cartographer/proposals.py
source_proxy/cartographer/proposal_previews.py
source_proxy/cartographer/blueprint_scribe.py
source_proxy/cartographer/runbook_scribe.py
src/app/v1/cartographer/drift/route.ts
src/app/v1/cartographer/proposals/route.ts
src/components/dashboard/HomelabBlueprintReviewWidget.tsx
source_proxy/tests/test_cartographer_api.py
Implementation notes

Drift rules:

source_proxy/cartographer/** changed + no cartographer blueprint update -> blueprint_drift
src/app/v1/cartographer/** changed + no API runbook update -> runbook_gap
src/components/dashboard/** changed + no manual QA note -> qa_gap
source_proxy/approval/** changed + no safety test update -> safety_gap
scout/** changed + no Scout docs update -> scout_doc_drift

Proposal states:

detected
drafted
pending_review
approved
rejected
applied
commit_pending
commit_approved
push_pending
push_approved
pushed
failed
Manual checks

Create a safe docs-only or test-only dirty tree, then run:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/drift | jq .
curl -s http://localhost:3000/v1/cartographer/proposals | jq .

Confirm:

drift warning appears when expected
proposal includes affected component
proposal includes changed files
proposal includes why update is needed
proposal is pending review, not applied
rejected proposal keeps reason
Expected outputs
{
  "drift_count": 1,
  "findings": [
    {
      "type": "blueprint_drift",
      "component": "Cartographer",
      "changed_files": ["source_proxy/cartographer/git_status.py"],
      "recommended_doc": "_blueprints/current/cartographer.md",
      "severity": "medium"
    }
  ]
}
Debug steps if failed
If no drift appears, inspect component mapping.
If too much drift appears, reduce noisy rules.
If proposals apply immediately, block and fix state machine.
If rejection disappears, fix proposal persistence.
Rollback plan
git restore source_proxy/cartographer/drift.py source_proxy/cartographer/proposals.py src/app/v1/cartographer src/components/dashboard/HomelabBlueprintReviewWidget.tsx
Recommended next step

Proceed to 6.9 for dashboard proposal review.

Permission gate

Ask Britton before adding apply-approved behavior to proposals.

Increment 6.9 - Dashboard Proposal Review UX
Goal

Make proposals understandable and reviewable from the dashboard.

Files likely touched
src/components/dashboard/HomelabBlueprintReviewWidget.tsx
src/components/dashboard/HomelabCartographerWidget.tsx
src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx
src/app/v1/cartographer/proposals/route.ts
src/app/v1/cartographer/proposals/[proposalId]/apply-approved/route.ts
source_proxy/cartographer/proposal_previews.py
source_proxy/cartographer/apply.py
source_proxy/tests/test_cartographer_api.py
Implementation notes

Dashboard proposal cards should show:

proposal ID
status
risk level
component
changed files
why it exists
suggested diff
manual check command
approve
reject
request edit
apply approved, only after approval

Separate the meanings:

approved != applied
applied != committed
committed != pushed
Manual checks

In dashboard:

Open Blueprint Review widget
Confirm pending proposal appears
Open proposal details
Reject proposal with reason
Confirm rejected count increments
Create/restore pending proposal
Approve proposal
Confirm approved count increments
Confirm apply still requires separate action

Terminal:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/proposals | jq .
git status --short
Expected outputs
Proposal visible
Approve works without applying
Reject stores reason
Request edit leaves proposal pending or draft
No commit
No push
Debug steps if failed
If UI says applied when only approved, fix labels.
If apply button appears before approval, hide/disable it.
If dashboard loses proposal after refresh, fix persistence.
If rejected reason missing, fix audit trail.
Rollback plan
git restore src/components/dashboard/HomelabBlueprintReviewWidget.tsx src/components/dashboard/__tests__ src/app/v1/cartographer source_proxy/cartographer
Recommended next step

Proceed to 6.10 for approved apply and post-apply verification.

Permission gate

Ask Britton before enabling any apply-approved endpoint.

Increment 6.10 - Approved Apply and Post-Apply Verification
Goal

Allow approved low-risk blueprint/doc proposals to apply only after explicit approval.

Files likely touched
source_proxy/cartographer/apply.py
source_proxy/cartographer/safety.py
source_proxy/cartographer/proposals.py
source_proxy/api/cartographer.py
src/app/v1/cartographer/proposals/[proposalId]/apply-approved/route.ts
source_proxy/tests/test_cartographer_api.py
source_proxy/tests/test_cartographer_safety_audit.py
Implementation notes

Apply rules:

Only approved proposals can apply.
Only allowed files can change.
Only docs/blueprints/runbooks at first.
No .env, secrets, app code, approval code, push code, or outside-root paths.
Run git diff --check after apply.
Record applied file list.
Record actor, timestamp, proposal ID, and result.
Manual checks

Create a docs-only proposal, approve it, then run:

cd ~/SpiritOS
curl -s -X POST http://localhost:3000/v1/cartographer/proposals/<proposalId>/apply-approved | jq .
git diff --check
git status --short

Confirm:

only expected docs changed
proposal status becomes applied
no commit created
no push created
audit event appears

Try unsafe proposal:

target .env.local
target source_proxy/approval/gate.py
target ../outside.md

Confirm all blocked.

Expected outputs
{
  "ok": true,
  "proposal_id": "bp-20260516-001",
  "status": "applied",
  "changed_files": ["_blueprints/current/cartographer.md"],
  "committed": false,
  "pushed": false
}
Debug steps if failed
If unapproved proposal applies, block phase.
If unsafe path applies, block phase.
If apply mutates extra files, block phase.
If git diff --check fails, rollback and fix diff generation.
Rollback plan

Use generated rollback instructions or:

git restore <changed-files>
Recommended next step

Proceed to 6.11 for branch recommendation.

Permission gate

Ask Britton before adding branch creation.

Increment 6.11 - Branch Recommendation
Goal

Stop dirty work from building up on the wrong branch.

Files likely touched
source_proxy/cartographer/branch_recommendations.py
source_proxy/cartographer/git_status.py
source_proxy/cartographer/models.py
src/app/v1/cartographer/branch-recommendations/route.ts
src/components/dashboard/HomelabCartographerWidget.tsx
source_proxy/tests/test_cartographer_api.py
Implementation notes

Branch recommendation should trigger when:

current branch is main/master
dirty file count is above threshold
high-risk component changed
new feature scope detected
proposal applied and commit needed

It should suggest names like:

cartographer/trust-source-v04
scout/source-gate-polish
proxy/runner-closeout
dashboard/blueprint-review-widget

No branch creation yet unless explicitly approved in a later sub-step.

Manual checks

Run from a test dirty tree:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/branch-recommendations | jq .
git branch --show-current
git status --short

Confirm:

branch suggestion appears
reason is clear
current branch is unchanged
no branch created
Expected outputs
{
  "recommended": true,
  "branch_name": "cartographer/trust-source-v04",
  "reason": "Dirty tree includes Cartographer and blueprint changes",
  "requires_approval": true
}
Debug steps if failed
If no branch suggested on main with dirty tree, check branch detection.
If branch name is vague, improve naming templates.
If branch is created automatically, block and remove write behavior.
Rollback plan

No writes expected. Revert files if code changed:

git restore source_proxy/cartographer/branch_recommendations.py src/app/v1/cartographer src/components/dashboard
Recommended next step

Proceed to 6.12 for approved branch creation.

Permission gate

Ask Britton before enabling branch creation.

Increment 6.12 - Approved Branch Creation
Goal

Let Cartographer create a recommended branch only after explicit approval.

Files likely touched
source_proxy/cartographer/branch_recommendations.py
source_proxy/cartographer/audit_trail.py
source_proxy/api/cartographer.py
src/app/v1/cartographer/branch-recommendations/route.ts
source_proxy/tests/test_cartographer_api.py
source_proxy/tests/test_cartographer_safety_audit.py
Implementation notes

Rules:

Branch creation requires explicit approval.
Branch name must pass safe branch name validation.
Branch cannot overwrite existing branch without approval.
Branch creation must be audited.
Rejection must leave Git untouched.
Manual checks

Run:

cd ~/SpiritOS
git branch --show-current
curl -s http://localhost:3000/v1/cartographer/branch-recommendations | jq .

From UI:

Approve branch creation
Confirm branch changes only after approval
Reject branch creation
Confirm branch remains unchanged

Terminal confirm:

git branch --show-current
git log --oneline -1
git status --short
Expected outputs
{
  "event": "branch_created",
  "branch": "cartographer/trust-source-v04",
  "actor": "Britton",
  "committed": false,
  "pushed": false
}
Debug steps if failed
If branch changes before approval, block.
If unsafe branch name allowed, tighten validation.
If audit missing, fix audit writer.
If branch creation fails, show exact Git error.
Rollback plan

Switch back and delete test branch only if safe:

git switch <previous-branch>
git branch -D cartographer/trust-source-v04
Recommended next step

Proceed to 6.13 for commit approval.

Permission gate

Ask Britton before enabling commits.

Increment 6.13 - Commit Approval and Pre-Commit Check Lane
Goal

Let Cartographer commit approved groups only after checks pass and Britton approves.

Files likely touched
source_proxy/cartographer/commit_proposals.py
source_proxy/cartographer/audit_trail.py
source_proxy/testing/runner.py
source_proxy/api/cartographer.py
src/app/v1/cartographer/commit-proposals/route.ts
source_proxy/tests/test_cartographer_api.py
source_proxy/tests/test_cartographer_safety_audit.py
Implementation notes

Commit approval flow:

dirty tree detected
commit group proposed
Britton reviews files/message
pre-commit lane runs selected checks
Britton approves commit
Cartographer stages only listed files
Cartographer commits with approved message
audit trail records commit SHA
push remains pending

Checks before commit:

git diff --check
npm run validate:blueprints
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py

No push.

Manual checks

Create docs-only change, then:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/commit-proposals | jq .

From UI:

Review changed files
Edit commit message
Run checks
Approve commit

Confirm:

git log --oneline -1
git status --short
git status -sb
Expected outputs
{
  "event": "commit_created",
  "commit_sha": "abc1234",
  "message": "docs(cartographer): add trust source blueprint",
  "files": ["docs/cartographer-trust-source-plan.md"],
  "pushed": false
}
Debug steps if failed
If unstated files get committed, block and fix file selection.
If commit happens without approval, block.
If checks fail but commit proceeds, block.
If commit message is wrong, amend only after approval.
Rollback plan

For test branch only:

git reset --soft HEAD~1

For real work, do not reset without reviewing.

Recommended next step

Proceed to 6.14 for push queue.

Permission gate

Ask Britton before adding push approval.

Increment 6.14 - Final Push Approval Queue
Goal

Separate commit approval from push approval so pushing never happens by accident.

Files likely touched
source_proxy/cartographer/push_queue.py
source_proxy/cartographer/audit_trail.py
source_proxy/api/cartographer.py
src/app/v1/cartographer/push-queue/route.ts
src/components/dashboard/HomelabBlueprintReviewWidget.tsx
source_proxy/tests/test_cartographer_api.py
source_proxy/tests/test_cartographer_safety_audit.py
Implementation notes

Push queue should show:

remote
branch
ahead count
commits pending
files included
last check result
merge target
risk level
requires approval

Push action requires separate explicit approval.

Manual checks

Create a test commit on a test branch, then:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/push-queue | jq .
git status -sb

From UI:

Confirm push pending card appears
Reject push and confirm nothing pushes
Approve push and confirm push happens
Confirm audit log records result
Expected outputs
{
  "push_pending": true,
  "remote": "origin",
  "branch": "cartographer/trust-source-v04",
  "commits_ahead": 1,
  "requires_approval": true
}

After approve:

{
  "event": "push_approved",
  "result": "pushed",
  "remote": "origin",
  "branch": "cartographer/trust-source-v04"
}
Debug steps if failed
If push runs automatically, block.
If wrong remote appears, require explicit remote selection.
If ahead count wrong, inspect git status -sb.
If audit missing, fix audit trail.
Rollback plan

Push rollback is not automatic. Use revert PR/commit workflow. For test remote branch, delete only after review.

Recommended next step

Proceed to 6.15 for merge readiness.

Permission gate

Ask Britton before adding merge recommendations.

Increment 6.15 - Merge Readiness and Release Steward
Goal

Tell Britton when a branch is ready to merge, what remains, and what might break.

Files likely touched
source_proxy/cartographer/project_health.py
source_proxy/cartographer/push_queue.py
source_proxy/cartographer/runbook_scribe.py
source_proxy/cartographer/audit_trail.py
src/app/v1/cartographer/project-health/route.ts
src/components/dashboard/HomelabCartographerWidget.tsx
source_proxy/tests/test_cartographer_api.py
Implementation notes

Merge readiness should check:

branch pushed
no dirty tree
tests passed
typecheck passed
blueprint validation passed
drift resolved or accepted
push audit exists
no high-risk files without review
merge target known

It should not merge automatically.

Manual checks

Run:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/project-health | jq .
git status -sb

Confirm:

merge readiness shows ready/not ready
blocked reasons are clear
no merge happens
Expected outputs
{
  "merge_ready": false,
  "reasons": [
    "branch has unpushed commits",
    "blueprint drift unresolved"
  ],
  "recommended_next_step": "push branch after approval"
}
Debug steps if failed
If ready appears while dirty, fix dirty tree gate.
If ready appears without pushed branch, fix ahead/behind logic.
If merge happens automatically, block and remove action.
Rollback plan

No writes expected.

Recommended next step

Proceed to 6.16 for audit and rollback trail hardening.

Permission gate

Ask Britton before adding any merge action.

Increment 6.16 - Audit Trail and Rollback Hints
Goal

Make every Cartographer action explainable after the fact.

Files likely touched
source_proxy/cartographer/audit_trail.py
source_proxy/cartographer/models.py
source_proxy/api/cartographer.py
src/app/v1/cartographer/audit-trail/route.ts
src/components/dashboard/HomelabBlueprintReviewWidget.tsx
source_proxy/tests/test_cartographer_api.py
source_proxy/tests/test_cartographer_safety_audit.py
Implementation notes

Audit events:

proposal_detected
proposal_drafted
proposal_approved
proposal_rejected
proposal_applied
branch_recommended
branch_created
commit_proposed
commit_created
push_queued
push_approved
push_rejected
push_completed
merge_ready
safety_blocked
rollback_hint_created

Each event needs:

event_id
actor
timestamp
proposal_id
component
changed_files
action
result
reason
rollback_hint
Manual checks

Run through one reject and one approve/apply path, then:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/audit-trail | jq .

Confirm:

rejection reason stored
approval actor stored
applied files stored
commit SHA stored if committed
push result stored if pushed
rollback hint present
Expected outputs
{
  "event": "proposal_rejected",
  "actor": "Britton",
  "proposal_id": "bp-20260516-001",
  "reason": "Not needed after review",
  "result": "rejected"
}
Debug steps if failed
If audit events duplicate, add stable IDs.
If actor missing, require actor field.
If rollback hint missing, generate based on action type.
If event order wrong, sort by timestamp.
Rollback plan

Audit logs should be append-only. For test data, use explicit test fixture cleanup only.

Recommended next step

Proceed to 6.17 for stable proposal IDs.

Permission gate

Ask Britton before changing audit storage format.

Increment 6.17 - Stable Proposal IDs and Duplicate Prevention
Goal

Prevent Cartographer from creating duplicate proposals every time it scans the same dirty tree.

Files likely touched
source_proxy/cartographer/proposals.py
source_proxy/cartographer/proposal_previews.py
source_proxy/cartographer/audit_trail.py
source_proxy/cartographer/models.py
source_proxy/tests/test_cartographer_api.py
Implementation notes

Proposal fingerprint should include:

project_id
component
proposal_type
target_file
changed_files hash
reason code
branch name if relevant

Stable ID examples:

bp-spiritos-cartographer-doc-drift-20260516-a1b2
commit-spiritos-dashboard-20260516-c3d4
push-spiritos-cartographer-trust-source-v04-e5f6
Manual checks

Run the same proposal scan twice:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/proposals | jq '.proposal_count'
curl -s http://localhost:3000/v1/cartographer/proposals | jq '.proposal_count'

Confirm:

count does not duplicate
same proposal_id appears
existing rejection stays rejected
approved proposal does not reappear as pending
Expected outputs
{
  "proposal_id": "bp-spiritos-cartographer-doc-drift-20260516-a1b2",
  "deduped": true
}
Debug steps if failed
If duplicates appear, inspect fingerprint fields.
If new changes do not create new proposal, include changed files hash.
If rejected proposal returns as pending, persist status by stable ID.
Rollback plan

Revert proposal ID logic. Keep old proposals intact.

Recommended next step

Proceed to 6.18 for dashboard/mobile trust polish.

Permission gate

Ask Britton before migrating existing proposal IDs.

Increment 6.18 - Dashboard Trust Polish and Mobile QA
Goal

Make Cartographer readable on desktop, LAN, Tailscale, and phone.

Files likely touched
src/components/dashboard/HomelabCartographerWidget.tsx
src/components/dashboard/HomelabBlueprintReviewWidget.tsx
src/components/dashboard/HomelabTestRunnerWidget.tsx
src/styles/dashboard-demo-v4.css
src/components/dashboard/__tests__/*
_blueprints/runbooks/cartographer_dashboard_mobile_qa.md
Implementation notes

Dashboard should show:

project detected
blueprints indexed
write mode locked/unlocked
dirty tree summary
pending proposals
commit proposals
push pending
audit trail
manual checks
clear unsafe-action warnings

Mobile rules:

no horizontal scroll
buttons are large enough
approval buttons require deliberate tap
danger buttons separated
status cards readable
Manual checks

Open dashboard on:

desktop localhost
LAN URL
Tailscale URL
phone browser

Confirm:

Cartographer widget loads
Blueprint Review widget loads
dirty tree summary readable
approval buttons not accidental
push approval visually separate from commit approval
no horizontal scroll
Expected outputs
Desktop: pass
LAN: pass
Tailscale: pass
Phone: pass
No accidental approval risk
Debug steps if failed
If mobile scrolls sideways, inspect card width and overflow.
If buttons too close, add spacing and confirmation.
If state differs by origin, inspect storage/origin behavior.
If dashboard fails on LAN, inspect API origin/proxy config.
Rollback plan

Revert UI/CSS only:

git restore src/components/dashboard src/styles/dashboard-demo-v4.css
Recommended next step

Proceed to 6.19 for safety audit.

Permission gate

Ask Britton before changing approval button behavior.

Increment 6.19 - Cartographer Safety Audit and Regression Pack
Goal

Prove Cartographer is safe before trusting it with branch/commit/push workflows.

Files likely touched
source_proxy/tests/test_cartographer_safety_audit.py
source_proxy/tests/test_cartographer_api.py
source_proxy/testing/runner.py
src/app/v1/coding/self-tests/run/route.ts
src/components/dashboard/HomelabTestRunnerWidget.tsx
docs/proxy-test-runner-plan.md
Implementation notes

Add or formalize runner profile:

PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-safety

Safety tests must prove:

no scanning outside allowlisted roots
no secrets summarized
no writes without approval
no apply without approval
no commits without approval
no pushes without separate approval
no Scout bypass
no Source Proxy approval bypass
no path traversal
no target mismatch
blocked cases have approval unavailable
Manual checks

Run:

cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-safety
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_cartographer_safety_audit.py source_proxy/tests/test_cartographer_api.py
git status --short

Confirm:

cartographer-safety passes
pytest passes
no apply/commit/push happens
git status only has expected docs/test changes
Expected outputs
Cartographer safety audit: passed
No unapproved writes
No unapproved commits
No unapproved pushes
Debug steps if failed
If unsafe path passes, block and patch safety.
If secret appears, block and patch redaction.
If unapproved apply/commit/push happens, stop all Git authority work.
If tests mutate files, isolate temp dirs.
Rollback plan

Revert safety runner changes if unstable:

git restore source_proxy/testing source_proxy/tests src/components/dashboard docs/proxy-test-runner-plan.md
Recommended next step

Proceed to 6.20 for long soak.

Permission gate

Ask Britton before promoting any new Git authority level.

Increment 6.20 - Trust Soak and Reliability Score
Goal

Let Cartographer prove boring reliability over repeated runs before any autopilot trial.

Files likely touched
source_proxy/cartographer/project_health.py
source_proxy/cartographer/audit_trail.py
source_proxy/testing/runner.py
docs/cartographer-trust-source-plan.md
_blueprints/runbooks/cartographer_manual_checks.md
Implementation notes

Add soak profile:

PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot

Capture:

timestamp
branch
dirty tree summary
proposal counts
drift findings
commit proposal counts
push queue state
audit event counts
safety warnings
db/log size if relevant
recommendation

No mutation except writing a snapshot log.

Manual checks

Run 3 snapshots over time:

cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot
sleep 60
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot
sleep 60
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot

Confirm:

no duplicate proposals
no surprise writes
dirty tree state stable
audit trail stable
recommendation readable
Expected outputs
cartographer-soak-snapshot: pass
mutation boundary: snapshot log only
recommendation: ready for next increment
Debug steps if failed
If proposals duplicate, revisit 6.17.
If snapshots mutate project files, block and fix runner.
If logs grow too much, add pruning.
If recommendations are vague, improve report format.
Rollback plan

Delete only test soak snapshots after review:

rm source_proxy/cartographer/soak-logs/<test-file>.json
Recommended next step

Proceed to 6.21 only after several boring runs.

Permission gate

Ask Britton before adding any autopilot behavior.

Increment 6.21 - Optional Docs-Only Autopilot Trial
Goal

Create a disabled-by-default trial for safe docs-only maintenance after Cartographer proves reliable.

Files likely touched
source_proxy/cartographer/apply.py
source_proxy/cartographer/proposals.py
source_proxy/cartographer/safety.py
source_proxy/cartographer/audit_trail.py
source_proxy/tests/test_cartographer_safety_audit.py
docs/cartographer-trust-source-plan.md
Implementation notes

This is not first-wave functionality. It should only happen after 6.19 and 6.20 are stable.

Autopilot scope:

docs-only
blueprints-only
runbooks-only
low-risk only
no app code
no source_proxy approval code
no scout activation code
no secrets
no commit
no push

Even in autopilot:

auto-draft allowed
auto-apply docs-only optional
auto-commit disabled
auto-push disabled
full audit required
daily cap required
easy kill switch required
Manual checks

Run with autopilot disabled:

cd ~/SpiritOS
curl -s http://localhost:3000/v1/cartographer/status | jq .

Confirm:

docs_autopilot_enabled: false

Try to trigger docs-only autopilot without enabling:

Expected: blocked

Enable only in a test config, then confirm:

only low-risk docs proposal applies
no commit
no push
audit event created
daily cap respected
kill switch works
Expected outputs
{
  "docs_autopilot_enabled": false,
  "autopilot_scope": "disabled",
  "commit_allowed": false,
  "push_allowed": false
}
Debug steps if failed
If autopilot enabled by default, block.
If app code can apply, block.
If commit/push occurs, block and remove autopilot.
If audit missing, block.
Rollback plan

Disable feature flag and revert implementation:

git restore source_proxy/cartographer source_proxy/tests docs/cartographer-trust-source-plan.md
Recommended next step

Only consider expanding autopilot after weeks of safe usage.

Permission gate

Ask Britton before enabling docs-only autopilot in any real workflow.

Final definition of done

Cartographer Trust Source v0.4 is done when:

4F readiness gate is green
blueprints are organized
blueprints have metadata and stable IDs
project discovery is read-only and allowlisted
component mapper works
repo map works
dirty tree view is clear
commit groups are proposed
drift is detected
proposals are queued
dashboard review works
approved docs apply works
branch creation requires approval
commit requires approval
push requires separate approval
merge readiness is advisory only
audit trail records all actions
stable proposal IDs prevent duplicates
safety audit passes
soak snapshots stay boring
no Scout bypass exists
no Source Proxy bypass exists
no secrets are summarized
no outside roots are scanned
no apply/commit/push happens without approval
Immediate next step

Start with Increment 6.0 - 4F Readiness Gate.

Recommended first implementation prompt should ask Codex to:

Inspect current Phase 4F runner status.
Run proxy-closeout, scout-smoke, and scout-source-gate.
Report whether Phase 6 can start.
Do not patch files.
Do not commit.
Do not push.
Do not approve or apply anything.
Return PASS/FAIL evidence and blockers.

Next permission gate: approve writing the Codex prompt for Increment 6.0 - 4F Readiness Gate.
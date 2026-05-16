Spirit Cartographer / Blueprinter Master Plan
Core rule

Spirit Cartographer can:

observe automatically
classify automatically
suggest automatically
draft proposal diffs automatically
remind you to branch / commit / update docs

Spirit Cartographer cannot:

write files without dashboard approval
commit without dashboard approval
push without separate dashboard approval
crawl outside allowed roots
summarize secrets
turn Scout packets into editable targets
bypass Source Proxy / Approval Gate

This matches your current architecture: Scout already uses manual queue/recheck/approve/reject behavior, the /coding workflow already runs through Source Proxy → Architect → Coder → Reviewer → Approval Gate → approved execution → post-apply verification, and Scout is explicitly not allowed to bypass that path.

The dashboard is also the correct home for this. Your dashboard status doc already says a later Project tracker surface is planned, and the current dashboard has the glass/widget shell needed to host a review queue.

External pattern lessons we keep: Backstage-style metadata stored with code, Aider-style repo maps for cheap codebase awareness, Huginn-style event flow, pre-commit-style reminders before review, and OpenHands-style TODO/PR workflows—but without giving the agent autonomous write/push power.

Target architecture
Allowed Project Roots
  ↓
Read-only Project Discovery
  ↓
Project Registry
  ↓
Blueprint Registry
  ↓
Component Mapper
  ↓
Git / Drift Watcher
  ↓
Proposal Queue
  ↓
Dashboard Blueprint Review Widget
  ↓
Approved Diff Apply
  ↓
Commit Approval
  ↓
Final Push Approval
Service ownership

Source Proxy owns local filesystem/project discovery.
This is because project folders, Git status, diffs, and approved file writes are local-workspace concerns.

Scout remains external intelligence.
Scout can later supply read-only research or source context, but it should not own local project files and should not become the writer.

Dashboard owns review.
Dashboard shows what Cartographer found, what it proposes, why, and what you can approve/reject.

Proposed cleaned blueprint structure

Current problem: your _blueprints docs are useful, but they mix current truth, roadmap, QA checklist, phase history, and visual sandbox notes at the same level. Also, the Repomix config currently treats blueprints as optional context, which is fine normally, but not when building the blueprint agent itself.

Recommended structure:

_blueprints/
  INDEX.md

  _schema/
    blueprint-frontmatter.schema.md
    blueprint-statuses.md
    cartographer-review-lifecycle.md

  current/
    system_state.md
    scout_architecture.md
    source_proxy_coding_workflow.md
    dashboard_state.md

  components/
    chat_workspace.md
    oracle_voice.md
    design_system.md
    project_tracker.md
    cartographer_agent.md

  runbooks/
    basic_chat_voice_qa.md
    oracle_mobile_qa.md
    scout_manual_checks.md
    cartographer_manual_checks.md

  history/
    general_intelligence_phase0.md
    general_intelligence_phase1.md
    general_intelligence_phase2.md
    general_intelligence_phase3.md
    general_intelligence_phase4.md

  proposals/
    pending/
    approved/
    rejected/
    applied/

Each active blueprint should eventually get metadata like:

---
blueprint_id: cartographer-agent
title: Spirit Cartographer Agent
project: SpiritOS
component: cartographer
doc_type: component_blueprint
status: active
source_of_truth: true
owner: Britton
code_paths:
  - source_proxy/cartographer/**
  - src/app/api/cartographer/**
  - src/components/dashboard/**Cartographer**
related_blueprints:
  - project_tracker
  - source_proxy_coding_workflow
  - dashboard_state
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-15
---
Phase 0 — Blueprint cleanup and governance

Goal: make the docs agent-safe before building the agent.

Increment 0.1 — Blueprint inventory and classification

Work:
Create a full inventory of current blueprint docs and classify each as:

current truth
component blueprint
roadmap
manual QA/runbook
history/phase receipt
visual sandbox
deprecated

Manual checklist for you:

 Open _blueprints/INDEX.md.
 Confirm every existing blueprint is listed.
 Confirm each doc has one classification.
 Confirm no doc content was rewritten yet.
 Confirm nothing outside _blueprints/ changed.

Expected output:

_blueprints/INDEX.md

With sections like:

Current source of truth
Component blueprints
Runbooks / manual QA
History / phase receipts
Deprecated / parked docs

Recommended next step:
Approve Increment 0.2 to reorganize folders and add doc ownership labels.

Increment 0.2 — Folder taxonomy cleanup

Work:
Move existing blueprint docs into the cleaned folder structure without changing their meaning.

Manual checklist for you:

 Confirm current/, components/, runbooks/, and history/ exist.
 Confirm current-architecture-blueprint.md moved or copied into current/system_state.md.
 Confirm basic_chat_qa.md lives under runbooks/, not active architecture.
 Confirm General Intelligence phase docs live under history/.
 Confirm design_demo.md remains clearly marked as sandbox/visual-only.

Expected output:

_blueprints/current/system_state.md
_blueprints/components/chat_workspace.md
_blueprints/components/oracle_voice.md
_blueprints/components/design_system.md
_blueprints/components/project_tracker.md
_blueprints/runbooks/basic_chat_voice_qa.md
_blueprints/history/general_intelligence_phase*.md

Recommended next step:
Approve Increment 0.3 to add frontmatter metadata.

Increment 0.3 — Blueprint metadata schema

Work:
Add a consistent frontmatter schema so the Cartographer can parse docs safely.

Manual checklist for you:

 Every active/current/component blueprint has frontmatter.
 status is one of active, planned, historical, deprecated, sandbox, runbook.
 source_of_truth is only true on canonical docs.
 code_paths are present for component docs.
 write_policy is present on every active blueprint.

Expected output:

_blueprints/_schema/blueprint-frontmatter.schema.md

Example statuses:

active
planned
runbook
historical
sandbox
deprecated

Recommended next step:
Approve Increment 0.4 to add a read-only validation check.

Increment 0.4 — Blueprint validation script

Work:
Add a small validation script that checks metadata and index consistency. It does not generate content.

Manual checklist for you:

 Run the validation command.
 Confirm it reports all active blueprints.
 Confirm missing metadata fails loudly.
 Confirm deprecated/history docs do not block unless malformed.
 Confirm the script does not modify files.

Expected output:

npm run validate:blueprints

Expected result:

Blueprint index valid
Active blueprints: <count>
Runbooks: <count>
Historical docs: <count>
No missing required metadata

Recommended next step:
Approve Phase 1 to start the read-only Cartographer foundation.

Phase 1 — Read-only Cartographer foundation

Goal: detect projects and blueprints, but do not write anything.

Increment 1.1 — Service boundary and API contract

Work:
Create a Cartographer module under Source Proxy, not Scout:

source_proxy/cartographer/
  models.py
  project_discovery.py
  blueprint_registry.py
  git_status.py
  proposals.py
  safety.py

Add read-only APIs:

GET /v1/cartographer/status
GET /v1/cartographer/projects
GET /v1/cartographer/blueprints

Manual checklist for you:

 Confirm no Scout files were changed.
 Confirm no write/edit/apply endpoints exist.
 Confirm APIs return JSON only.
 Confirm the service works if no project roots are configured.
 Confirm error messages are plain and useful.

Expected output:

{
  "status": "observing",
  "write_actions_enabled": false,
  "configured_roots": [],
  "projects": []
}

Recommended next step:
Approve Increment 1.2 for allowlisted project root discovery.

Increment 1.2 — SPIRIT_PROJECT_PATH allowlist parser

Work:
Parse allowed roots only. This matches your existing Project Tracker roadmap: project discovery should scan SPIRIT_PROJECT_PATH or equivalent allowlisted roots, detect project markers, and perform no file modification.

Example:

SPIRIT_PROJECT_PATH=/home/source/SpiritOS,/home/source/Projects,C:\Projects

Manual checklist for you:

 Set one safe test root.
 Confirm paths outside the allowlist are rejected.
 Confirm empty/missing env gives safe empty output.
 Confirm .env, certs, private keys, and backup folders are never summarized.
 Confirm Windows C:\Projects is treated as allowlisted only if explicitly configured.

Expected output:

{
  "configured_roots": [
    {
      "path": "/home/source/Projects",
      "status": "configured"
    }
  ],
  "blocked_roots": []
}

Recommended next step:
Approve Increment 1.3 for project marker detection.

Increment 1.3 — Read-only project discovery

Work:
Detect project candidates using markers:

.git
package.json
README.md
pyproject.toml
requirements.txt
src/
app/
tests/
_blueprints/

Manual checklist for you:

 Create or point at a safe test project folder.
 Confirm the project appears in /v1/cartographer/projects.
 Confirm nested junk folders do not become projects.
 Confirm secrets are not read or summarized.
 Confirm no files are created.

Expected output:

{
  "projects": [
    {
      "project_id": "spiritos",
      "name": "SpiritOS",
      "root": "/home/source/SpiritOS",
      "markers": [".git", "package.json", "README.md", "_blueprints"],
      "status": "detected",
      "write_policy": "read_only"
    }
  ]
}

Recommended next step:
Approve Increment 1.4 for dashboard read-only visibility.

Increment 1.4 — Dashboard read-only Cartographer widget

Work:
Add a dashboard widget that shows detected projects, blueprint count, dirty Git state, and review queue count. No approve/write buttons yet.

Manual checklist for you:

 Open /.
 Confirm the widget appears without breaking existing dashboard cards.
 Confirm empty state is useful.
 Confirm project count matches API output.
 Confirm no actions are available yet.

Expected output:

Spirit Cartographer
Projects detected: 1
Blueprints indexed: 12
Pending proposals: 0
Write mode: locked

Recommended next step:
Approve Phase 2 for component mapping and blueprint registry parsing.

Phase 2 — Blueprint registry and component mapper

Goal: teach Cartographer which docs own which parts of each project.

Increment 2.1 — Blueprint registry parser

Work:
Parse _blueprints/INDEX.md and frontmatter into a registry.

Backstage is the reference pattern here: metadata files live alongside code and are harvested/visualized by the catalog. We borrow the metadata-with-code idea, not the whole Backstage platform.

Manual checklist for you:

 Confirm every active blueprint appears in registry output.
 Confirm source_of_truth: true docs are clearly marked.
 Confirm historical docs are visible but not used for current drift decisions.
 Confirm invalid frontmatter produces a clear warning.

Expected output:

{
  "blueprints": [
    {
      "blueprint_id": "source-proxy-coding-workflow",
      "status": "active",
      "source_of_truth": true,
      "code_paths": ["source_proxy/**", "src/app/v1/**"]
    }
  ]
}

Recommended next step:
Approve Increment 2.2 for component mapping.

Increment 2.2 — Component mapper

Work:
Map paths to components:

scout/**                         -> Scout
source_proxy/**                  -> Source Proxy
src/app/api/scout/**             -> Scout dashboard bridge
src/components/dashboard/**      -> Dashboard
src/app/chat/** + src/hooks/useSpirit* -> Chat workspace
src/app/oracle/** + src/components/oracle/** -> Oracle
scripts/spiritdesktop-windows/** -> Windows desktop agent
_blueprints/**                   -> Blueprint system

Manual checklist for you:

 Run mapper on current repo.
 Confirm major components are recognized.
 Confirm unknown files are reported as unmapped, not guessed.
 Confirm _blueprints changes map to Blueprint system.
 Confirm design demo stays sandboxed. The design demo doc already says it is visual-only and does not touch production APIs, persistence, routes, or runtime.

Expected output:

{
  "components": [
    {
      "component_id": "dashboard",
      "paths": ["src/components/dashboard/**", "src/app/(dashboard)/**"],
      "blueprint_id": "dashboard-state"
    }
  ],
  "unmapped_paths": []
}

Recommended next step:
Approve Increment 2.3 for cheap repo maps.

Increment 2.3 — Repo map / symbol map

Work:
Create a cheap repo map so the Cartographer can understand structure without reading everything. Aider’s repo map is the reference: it sends a compact map of files and key symbols to the model instead of full repo content every time.

Manual checklist for you:

 Run repo-map generation.
 Confirm output is small enough for prompt context.
 Confirm it includes components, major files, and exported symbols.
 Confirm tests and demos can be excluded unless requested.
 Confirm _blueprints are included when Cartographer work is active.

Expected output:

.cartographer/repo-map.json

Or API-only output:

{
  "project_id": "spiritos",
  "map_version": 1,
  "files_indexed": 184,
  "symbols_indexed": 530
}

Recommended next step:
Approve Phase 3 for Git-aware drift detection.

Phase 3 — Git-aware drift detection

Goal: know when blueprinting should start and stop automatically.

Increment 3.1 — Git status scanner

Work:
Read branch, dirty state, last commit, and changed files.

Manual checklist for you:

 Make a small uncommitted change.
 Confirm Cartographer shows dirty state.
 Confirm changed file list is accurate.
 Confirm ignored files do not appear.
 Confirm no Git command writes anything.

Expected output:

{
  "branch": "cartographer-plan",
  "dirty": true,
  "changed_files": [
    "src/components/dashboard/SpiritDashboardHome.tsx"
  ],
  "last_commit": {
    "sha": "abc123",
    "message": "dashboard checkpoint"
  }
}

Recommended next step:
Approve Increment 3.2 for drift rules.

Increment 3.2 — Blueprint drift rules

Work:
Detect when docs may be stale.

Example rules:

Component code changed + active blueprint not updated -> blueprint_drift
README changed + blueprint not updated -> review_suggested
TODO changed + roadmap not updated -> todo_drift
New route added + architecture doc not updated -> architecture_drift
New API added + manual checklist missing -> qa_gap

Manual checklist for you:

 Change a component file.
 Confirm affected blueprint is identified.
 Confirm no proposal is generated yet unless requested.
 Confirm false positives can be dismissed.
 Confirm historical docs are ignored for drift.

Expected output:

{
  "drift": [
    {
      "component": "dashboard",
      "reason": "component_code_changed",
      "affected_blueprints": ["dashboard-state"],
      "severity": "review_suggested"
    }
  ]
}

Recommended next step:
Approve Increment 3.3 for commit and branch reminders.

Increment 3.3 — Commit and branch reminders

Work:
Surface reminders:

dirty working tree
many changed files
new component started without branch
blueprint stale before commit
tests not recorded
push pending approval

Pre-commit’s official docs frame hooks as a way to catch simple issues before code review; Cartographer should use that idea as a reminder/check layer, not as a silent writer.

Manual checklist for you:

 Make changes on main branch.
 Confirm widget suggests a separate branch.
 Make several file changes.
 Confirm widget suggests a checkpoint commit.
 Confirm reminders are dismissible.
 Confirm no branch or commit is created.

Expected output:

Recommendation: create branch before continuing.
Reason: 8 files changed on main.
Suggested branch: cartographer/dashboard-blueprint-review

Recommended next step:
Approve Phase 4 for proposal queue and dashboard approvals.

Phase 4 — Proposal queue and dashboard approval

Goal: proposals become visible, reviewable, and auditable before any write.

Increment 4.1 — Proposal lifecycle schema

Work:
Create proposal states:

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

Manual checklist for you:

 Confirm proposals can be listed.
 Confirm rejected proposals keep rejection reason.
 Confirm approved proposals do not apply automatically.
 Confirm every state transition has timestamp + actor.
 Confirm proposal IDs are stable.

Expected output:

{
  "proposal_id": "bp-20260515-001",
  "status": "pending_review",
  "type": "blueprint_update",
  "component": "dashboard",
  "requires_approval": true
}

Recommended next step:
Approve Increment 4.2 for diff preview proposals.

Increment 4.2 — Blueprint diff proposal generation

Work:
Generate proposed Markdown diffs for blueprints, but do not apply them.

Manual checklist for you:

 Trigger drift on a test blueprint.
 Confirm a proposed diff appears.
 Confirm diff only touches allowed blueprint docs.
 Confirm generated content cites changed files.
 Confirm secrets are redacted.
 Confirm proposal can be rejected.

Expected output:

Proposed diff:
_blueprints/components/dashboard_state.md
+ Added Cartographer widget placeholder
+ Added manual check for dashboard approval queue

Recommended next step:
Approve Increment 4.3 for dashboard review UI.

Increment 4.3 — Dashboard Blueprint Review widget

Work:
Build the actual approval widget.

Suggested display:

Blueprint Review
- Pending proposal
- Affected project
- Affected component
- Changed files
- Proposed doc diff
- Confidence
- Why this update is needed
- Approve / Reject / Request edit

The existing Scout widget already uses manual queue/review patterns, so this should feel familiar but be separate from Scout.

Manual checklist for you:

 Open /.
 Confirm pending proposal appears.
 Expand diff preview.
 Reject with reason.
 Approve another proposal.
 Confirm approval does not push or commit.
 Confirm UI works on phone-width layout.

Expected output:

Pending: 1
Approved: 1
Rejected: 1
Applied: 0
Push pending: 0

Recommended next step:
Approve Increment 4.4 for approved doc apply.

Increment 4.4 — Apply approved doc updates only

Work:
Approved blueprint updates can be applied through the existing Source Proxy approved-execution style. Your repo already treats diff preview as non-writing and applies only after approval.

Manual checklist for you:

 Approve a doc-only proposal.
 Confirm diff preview appears first.
 Confirm only approved files are modified.
 Confirm no code files are changed.
 Confirm post-apply verification runs.
 Confirm failed apply rolls back or marks failed.

Expected output:

Proposal applied:
_blueprints/components/dashboard_state.md

Verification:
- allowed files passed
- markdown validation passed
- blueprint metadata validation passed

Recommended next step:
Approve Phase 5 for AI-assisted drafting/sub-cartographers.

Phase 5 — AI-assisted Cartographer brains

Goal: add intelligence after the safety lane exists.

Increment 5.1 — Change Scribe

Work:
Summarize Git diffs into plain-language change notes.

Manual checklist for you:

 Make a small code change.
 Confirm Change Scribe summarizes it accurately.
 Confirm it lists evidence: changed files, branch, commit state.
 Confirm uncertain claims are marked uncertain.
 Confirm no files are written.

Expected output:

Change Scribe summary:
Dashboard component layout changed.
Evidence:
- src/components/dashboard/SpiritDashboardHome.tsx modified
- no blueprint update detected
Recommended action:
- review dashboard blueprint

Recommended next step:
Approve Increment 5.2 for Blueprint Scribe.

Increment 5.2 — Blueprint Scribe

Work:
Draft blueprint updates from drift + Change Scribe summary.

Manual checklist for you:

 Confirm proposal has a reason.
 Confirm proposal includes exact affected blueprint.
 Confirm proposal avoids overclaiming.
 Confirm proposal can be edited/rejected.
 Confirm approved proposal still requires apply approval.

Expected output:

Blueprint Scribe proposal:
Update dashboard_state.md to mention Blueprint Review widget placeholder.
Confidence: medium
Reason: dashboard status doc already names project tracker surface as later work.

Recommended next step:
Approve Increment 5.3 for QA/runbook Scribe.

Increment 5.3 — QA / Runbook Scribe

Work:
Suggest manual checklist updates when UI/API behavior changes.

Manual checklist for you:

 Change a route/API/widget.
 Confirm Scribe suggests a runbook update.
 Confirm it does not rewrite QA docs directly.
 Confirm checklist items are testable.
 Confirm expected outputs are included.

Expected output:

Suggested runbook update:
- Open dashboard.
- Confirm Blueprint Review widget shows pending proposal count.
- Approve doc-only proposal.
- Confirm no push occurs.

Recommended next step:
Approve Increment 5.4 for sub-cartographer routing.

Increment 5.4 — Sub-cartographer routing

Work:
Add lightweight sub-roles:

Component Mapper
Change Scribe
Blueprint Scribe
Runbook Scribe
Commit Scribe
Project Onboarding Scribe

Huginn’s event graph is the model: watchers create events, downstream agents consume them, and each step has a narrow job.

Manual checklist for you:

 Confirm each sub-role has one responsibility.
 Confirm each output is visible in the proposal.
 Confirm failures stop at proposal queue.
 Confirm no sub-role can write files directly.

Expected output:

{
  "proposal_id": "bp-20260515-004",
  "contributors": [
    "component_mapper",
    "change_scribe",
    "blueprint_scribe"
  ]
}

Recommended next step:
Approve Phase 6 for new project onboarding.

Phase 6 — New project onboarding

Goal: make this work for every new project in your Projects folder.

Increment 6.1 — New project candidate detection

Work:
When a new folder appears under an allowlisted root, create a dashboard candidate.

Manual checklist for you:

 Create a test project under allowed root.
 Confirm it appears as new_project_candidate.
 Confirm no files are created.
 Confirm projects outside allowed roots are ignored.
 Confirm project markers are shown.

Expected output:

New project detected:
Name: ClientDashboard
Root: /home/source/Projects/ClientDashboard
Markers: package.json, .git, README.md
Status: Needs approval

Recommended next step:
Approve Increment 6.2 for starter blueprint proposals.

Increment 6.2 — Starter blueprint pack proposal

Work:
Propose—but do not create—starter docs:

_blueprints/INDEX.md
_blueprints/current/project_state.md
_blueprints/components/app.md
_blueprints/runbooks/manual_checks.md
TODO.md

Manual checklist for you:

 Open the new project proposal in dashboard.
 Confirm proposed files are shown.
 Confirm starter content is previewable.
 Reject once and confirm no files appear.
 Approve once and confirm diff/apply flow begins.

Expected output:

Starter blueprint pack pending approval:
5 files proposed
0 files written

Recommended next step:
Approve Increment 6.3 for cross-project dashboard view.

Increment 6.3 — Cross-project dashboard view

Work:
Show all projects and their blueprint health.

Manual checklist for you:

 Confirm SpiritOS appears.
 Confirm new test project appears.
 Confirm each project shows dirty state / branch / blueprint health.
 Confirm project cards can be filtered by status.
 Confirm no project outside allowed roots appears.

Expected output:

Projects
- SpiritOS: active, 14 blueprints, 1 pending drift
- ClientDashboard: needs starter blueprint approval

Recommended next step:
Approve Phase 7 for branch, commit, and push approvals.

Phase 7 — Branch, commit, and final push approval

Goal: make the system useful without letting it run wild.

Increment 7.1 — Branch recommendation

Work:
Suggest branch names when working on main or when change size is high.

Manual checklist for you:

 Make changes on main.
 Confirm suggested branch appears.
 Approve branch creation.
 Confirm branch is created only after approval.
 Confirm rejection leaves Git untouched.

Expected output:

Suggested branch:
cartographer/blueprint-review-widget

Reason:
Working tree dirty on main with 6 changed files.

Recommended next step:
Approve Increment 7.2 for commit packaging.

Increment 7.2 — Commit proposal

Work:
Package approved blueprint/doc updates into suggested commits.

Manual checklist for you:

 Apply an approved blueprint update.
 Confirm commit proposal appears.
 Confirm changed files list is exact.
 Confirm suggested commit message is editable.
 Approve commit.
 Confirm commit happens only after approval.

Expected output:

Commit proposal:
docs(cartographer): add blueprint review registry structure

Files:
- _blueprints/INDEX.md
- _blueprints/_schema/blueprint-frontmatter.schema.md

Recommended next step:
Approve Increment 7.3 for final push queue.

Increment 7.3 — Final push approval queue

Work:
Separate push approval from commit approval.

Manual checklist for you:

 Create a test commit.
 Confirm push is not automatic.
 Confirm dashboard shows remote, branch, commit count, and files.
 Approve push.
 Confirm push result is logged.
 Reject push and confirm nothing is pushed.

Expected output:

Push pending:
Remote: origin
Branch: cartographer/blueprint-review-widget
Commits ahead: 1
Requires approval: yes

Recommended next step:
Approve Increment 7.4 for rollback/audit log.

Increment 7.4 — Audit and rollback trail

Work:
Record every proposal, approval, rejection, apply, commit, and push.

Manual checklist for you:

 Reject a proposal and see rejection reason.
 Approve/apply a proposal and see timestamp.
 Commit and see commit SHA.
 Push and see remote/branch.
 Confirm audit log contains actor + action + result.

Expected output:

{
  "event": "push_approved",
  "actor": "Britton",
  "proposal_id": "bp-20260515-012",
  "branch": "cartographer/blueprint-review-widget",
  "result": "pushed"
}

Recommended next step:
Approve Phase 8 for hardening.

Phase 8 — Safety audit and regression pack

Goal: make Cartographer boring, safe, and repeatable.

Increment 8.1 — Cartographer safety audit

Work:
Add tests that prove:

no scanning outside allowlisted roots
no secrets summarized
no writes without approval
no commits without approval
no pushes without approval
no Scout bypass
no Source Proxy approval bypass

Manual checklist for you:

 Run Cartographer safety tests.
 Confirm path traversal attempts fail.
 Confirm .env.local is ignored/redacted.
 Confirm unapproved proposal cannot apply.
 Confirm unapproved commit cannot happen.
 Confirm unapproved push cannot happen.

Expected output:

Cartographer safety audit: passed

Recommended next step:
Approve Increment 8.2 for dashboard/mobile QA.

Increment 8.2 — Dashboard/mobile QA

Work:
Add manual QA for desktop, LAN, Tailscale, and phone. Your existing runbooks already emphasize per-origin local storage and mobile checks, so Cartographer QA should follow that pattern.

Manual checklist for you:

 Desktop / shows widget.
 LAN / shows same API state.
 Tailscale / works without stuck loading.
 Phone width has no horizontal scroll.
 Approve/reject buttons are usable.
 Push approval cannot be tapped accidentally.

Expected output:

Cartographer dashboard QA passed:
desktop
LAN
Tailscale
mobile

Recommended next step:
Approve Increment 8.3 for performance/context limits.

Increment 8.3 — Context budget and performance limits

Work:
Prevent giant scans and runaway context.

Manual checklist for you:

 Run on SpiritOS.
 Confirm scan time is bounded.
 Confirm repo map size is capped.
 Confirm huge directories are skipped.
 Confirm ignored paths are respected.
 Confirm dashboard remains responsive.

Expected output:

{
  "scan_duration_ms": 850,
  "files_seen": 420,
  "files_indexed": 160,
  "skipped": ["node_modules", ".next", "dist"]
}

Recommended next step:
Approve Increment 8.4 for final docs and operating guide.

Increment 8.4 — Cartographer operating guide

Work:
Create the final operating manual.

Manual checklist for you:

 Read the Cartographer guide.
 Confirm it explains what auto-detects.
 Confirm it explains what needs approval.
 Confirm it explains how new projects onboard.
 Confirm it explains rollback and push approval.

Expected output:

_blueprints/components/cartographer_agent.md
_blueprints/runbooks/cartographer_manual_checks.md

Recommended next step:
Move from buildout to routine use.

Implementation order I recommend

Do not start with the AI Scribe. Start here:

1. Phase 0.1 — Blueprint inventory
2. Phase 0.2 — Folder cleanup
3. Phase 0.3 — Metadata schema
4. Phase 0.4 — Validation script
5. Phase 1.1 — Read-only Cartographer API shell
6. Phase 1.2 — SPIRIT_PROJECT_PATH allowlist
7. Phase 1.3 — Project discovery
8. Phase 1.4 — Dashboard read-only widget

That gives you a safe foundation before any model-generated proposal enters the system.
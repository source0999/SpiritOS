# Agent Ecosystem Plan 1 Start Handoff v0.1

## Copy-Paste Prompt

```text
You are starting real implementation work, not planning. The master roadmap is already written. Start Plan 1 Phase 1: Agent Factory Runtime Foundation, Authority Auditor and Lane Guard Runtime Skeleton.

Start in:
/home/source/SpiritOS

Read first:
- docs/agent-ecosystem-master-roadmap-v0.1.md
- docs/agent-ecosystem-plan-1-start-handoff-v0.1.md
- docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md

Active plan:
Plan 1: Agent Factory Runtime Foundation.

Active phase:
Phase 1: Authority Auditor and Lane Guard Runtime Skeleton.

This is implementation, not roadmap writing. Do not write another handoff. Do not write or revise a roadmap. Do not continue a planning loop. Do not start Plan 2. Do not broaden scope. Required negative scope phrases: no handoff writing, no roadmap writing, no planning loop.

Exact allowed files for Plan 1 Phase 1:
- source_proxy/agent_factory/__init__.py
- source_proxy/agent_factory/contracts.py
- source_proxy/agent_factory/authority_auditor.py
- source_proxy/agent_factory/lane_guard.py
- source_proxy/tests/test_agent_factory_contracts.py
- source_proxy/tests/test_agent_factory_authority_auditor.py
- source_proxy/tests/test_agent_factory_lane_guard.py
- docs/agent-ecosystem-plan-1-phase-1-closeout-v0.1.md

Exact forbidden files/actions:
- No edits to existing `source_proxy/**` files outside the exact allowed Agent Factory files.
- No edits to `src/**`.
- No edits to `scout/**`.
- No edits to `backend/**`.
- No edits to `scripts/**`.
- No edits to `config/**`.
- No edits to `package.json` or `package-lock.json`.
- No edits to unrelated tests.
- No edits to existing Source Proxy docs.
- No edits to existing Cartographer docs.
- No edits to existing Design docs.
- No edits to existing Scout docs.
- No commits.
- No pushes.
- No branches.
- No worktrees.
- No stash/reset/clean.
- No package installs.
- No server restarts.
- No external API calls.
- No auth/config/env changes.
- No apply authority.
- No approval authority.
- No command execution authority beyond the exact Codex self-checks listed below.
- No workflow execution authority.
- No queue execution authority.
- No self-approval.
- No background autonomy.
- No handoff writing.
- No roadmap writing.
- No planning loop.

Runtime authority limit:
The Agent Factory runtime skeleton may only perform deterministic checks over supplied data. It may return models, statuses, and findings. It must not mutate files, call Proxy apply, consume approval tokens, call Cartographer safe writes, execute workflow queues, run shell commands, create branches/worktrees, commit, push, or treat a clean report as permission.

Before editing anything, state:
- active plan
- active phase
- active increment
- exact allowed files
- exact forbidden files/actions
- whether the current step is implementation-authorized inside Plan 1 Phase 1 only

Baseline:
cd /home/source/SpiritOS
git status --branch --short

Phase increments:

Increment 1.1: Baseline and package shell
- Purpose: Capture dirty state and create the new Agent Factory package shell.
- Allowed files/lane: `source_proxy/agent_factory/__init__.py` and `docs/agent-ecosystem-plan-1-phase-1-closeout-v0.1.md`.
- Forbidden files/actions: Existing source modules, package/config/env, broad tests, commits, pushes, branches, worktrees, stash/reset/clean.
- Expected output: Empty package export boundary and closeout draft header.
- Codex self-check: `git status --branch --short`; defer pytest until test files exist and say so plainly.
- Stop conditions: Any edit outside allowed files, unexpected lane-caused dirty file, or request to broaden scope.
- Next increment title: Increment 1.2: Contract models.

Increment 1.2: Contract models
- Purpose: Define deterministic contract models for authority flags, lane scope, audit finding, and lane report.
- Allowed files/lane: `source_proxy/agent_factory/contracts.py`, `source_proxy/tests/test_agent_factory_contracts.py`, and `source_proxy/agent_factory/__init__.py` only if exports are needed.
- Forbidden files/actions: Proxy apply code, Cartographer code, command runners, workflow/queue code, package installs.
- Expected output: Contract models with fail-closed defaults and focused tests.
- Codex self-check: `python -m pytest source_proxy/tests/test_agent_factory_contracts.py -q`.
- Stop conditions: Any default grants approval, apply, write, command, workflow, queue, commit, push, branch/worktree, self-approval, or background autonomy.
- Next increment title: Increment 1.3: Authority Auditor skeleton.

Increment 1.3: Authority Auditor skeleton
- Purpose: Add deterministic scans for authority drift in supplied plain text and model data.
- Allowed files/lane: `source_proxy/agent_factory/authority_auditor.py`, `source_proxy/tests/test_agent_factory_authority_auditor.py`, `source_proxy/agent_factory/contracts.py` only if a model refinement is needed, and `source_proxy/agent_factory/__init__.py` only if exports are needed.
- Forbidden files/actions: Runtime approvals, token creation, command execution, source mutation, external calls.
- Expected output: Authority Auditor returning findings only.
- Codex self-check: `python -m pytest source_proxy/tests/test_agent_factory_contracts.py source_proxy/tests/test_agent_factory_authority_auditor.py -q`.
- Stop conditions: Auditor treats a clean report as approval, mutates files, or grants authority.
- Next increment title: Increment 1.4: Lane Guard skeleton.

Increment 1.4: Lane Guard skeleton
- Purpose: Add deterministic allowed-file, forbidden-file, dirty-state, and file-family overlap checks from supplied inputs.
- Allowed files/lane: `source_proxy/agent_factory/lane_guard.py`, `source_proxy/tests/test_agent_factory_lane_guard.py`, `source_proxy/agent_factory/contracts.py` only if a model refinement is needed, and `source_proxy/agent_factory/__init__.py` only if exports are needed.
- Forbidden files/actions: Git cleanup, real locks, workflow queue mutation, branch/worktree actions.
- Expected output: Lane Guard returning clear/caution/blocked reports only.
- Codex self-check: `python -m pytest source_proxy/tests/test_agent_factory_contracts.py source_proxy/tests/test_agent_factory_authority_auditor.py source_proxy/tests/test_agent_factory_lane_guard.py -q`.
- Stop conditions: Lane Guard changes files, cleans state, claims ownership of unrelated dirty files, creates locks, or grants permission.
- Next increment title: Increment 1.5: Phase closeout.

Increment 1.5: Phase closeout
- Purpose: Record files changed, checks run, authority limits, manual spot-check, blockers, and next permission phrase.
- Allowed files/lane: `docs/agent-ecosystem-plan-1-phase-1-closeout-v0.1.md` plus prior Phase 1 allowed files for tiny corrections only.
- Forbidden files/actions: New helpers, handoff writing, roadmap writing, planning loop, Plan 2, commits, pushes, branches, worktrees, stash/reset/clean.
- Expected output: Phase 1 closeout doc.
- Codex self-check: `git diff --check -- source_proxy/agent_factory/*.py source_proxy/tests/test_agent_factory_*.py docs/agent-ecosystem-plan-1-phase-1-closeout-v0.1.md`; `python -m pytest source_proxy/tests/test_agent_factory_contracts.py source_proxy/tests/test_agent_factory_authority_auditor.py source_proxy/tests/test_agent_factory_lane_guard.py -q`.
- Stop conditions: Failed focused check after one fix attempt, any authority expansion, or any lane-caused dirty file outside allowed files.
- Next increment title: Stop and ask Britton before Plan 1 Phase 2.

Manual check for Britton at phase end:
Give only a short spot-check, not a huge terminal block:
- files changed are limited to the exact Plan 1 Phase 1 allowed files
- focused Agent Factory tests pass
- Authority Auditor and Lane Guard return findings/reports only
- no apply, approval, command, workflow, queue, commit, push, branch/worktree, self-approval, or background autonomy exists
- closeout doc names blockers and the next permission phrase

Final response format for the implementation chat:
1. Active Plan/Phase Completed
2. Files Changed
3. Codex Self-Checks Run
4. Short Manual Spot Check For Britton
5. Blockers
6. Next Permission Required

Ask permission before next phase. Do not continue to Plan 1 Phase 2 without Britton explicitly approving it. Do not start Plan 2.
```

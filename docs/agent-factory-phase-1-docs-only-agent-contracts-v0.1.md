# Agent Factory Plan 1 Docs-Only Agent Contracts v0.1

## Authority Statement

This document is docs-only. It does not implement runtime helpers, agents, registry entries, command execution, workflow execution, source writes, tests, UI, package/config/env changes, apply, commit, push, branch, worktree, stash, reset, cleanup, self-approval, or background autonomy.

Correction:
This file contains Plan 1 Phase 1 docs-only contracts and operating rules that were already written during planning-package consolidation. A new Codex chat must review and ratify this existing content before proceeding to any next valid Plan 1 phase.

Plan 1 creates contracts only. A contract describes what a future helper may prepare or report. It does not grant authority.

## Planned Plan

Plan 1: Agent Factory Contracts and Operating Rules.

Future handoff target:

Agent Factory Plan 1 Phase 1 can start in a new chat.

Allowed files for future Plan 1:

- New `docs/agent-factory-*` contract docs only.

Forbidden files and actions:

- No `source_proxy/**`.
- No `src/**`.
- No `scout/**`.
- No tests.
- No package, config, or `.env*` files.
- No active Source Proxy docs.
- No active Cartographer docs.
- No runtime code.
- No apply, execute-approved, commit, push, branch, worktree, stash, reset, cleanup, package install, server restart, external API call, or auth/config change.

Global contract rule:

Agent thinks and prepares. Proxy applies. Cartographer records and organizes. Human approves authority crossings.

## Contract Output Rules

Every future Agent Factory contract must state:

- purpose
- input sources
- allowed output
- forbidden output
- authority flags
- required evidence
- manual checks
- stop conditions
- next permission phrase

Authority flags must default to:

| Authority flag | Required value in Phase 1 |
| --- | --- |
| approval authority | false |
| apply authority | false |
| write authority | false |
| command execution authority | false |
| workflow execution authority | false |
| queue execution authority | false |
| commit authority | false |
| push authority | false |
| branch/worktree authority | false |
| self-approval authority | false |
| background autonomy | false |

## Increment 1.1.1: Baseline and Allowed Files

Purpose:
Capture the active dirty-state baseline and name the exact docs-only lane before any contract edits proceed.

Active plan and phase:

- Plan: Agent Factory Plan 1.
- Phase: Phase 1.1, Contract Source Of Truth.
- Increment: 1.1.1, Baseline and allowed files.

Active allowed files:

- `docs/agent-factory-roadmap-v0.1.md`
- `docs/agent-factory-new-chat-handoff-v0.1.md`
- `docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md`

Active lane rule:

- Phase 1.1 may touch only `docs/agent-factory-*` files.
- Increment 1.1.1 may only record baseline status and allowed files.
- Existing dirty files outside `docs/agent-factory-*` are user-owned unless Britton explicitly says otherwise.

Baseline captured:

- `git status --branch --short` showed `main...origin/main [ahead 34]` with many pre-existing modified and untracked files outside the Agent Factory lane.
- `git diff --check -- docs/agent-factory-*.md` passed with no whitespace errors.

Forbidden files and actions:

- No `source_proxy/**`, `src/**`, `scout/**`, `backend/**`, `scripts/**`, package/config/env files, tests, or existing active Proxy, Cartographer, Design, or Scout docs.
- No commits, pushes, branches, worktrees, stash, reset, clean, runtime helpers, implementation work, package installs, server restarts, external API calls, or auth/config/env changes.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- docs/agent-factory-*.md
grep -nE "Increment 1.1.1|Active allowed files|Baseline captured|Existing dirty files outside" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
```

Stop conditions:

- Any lane-caused change appears outside `docs/agent-factory-*`.
- Any baseline language claims ownership of unrelated dirty files.
- Any check fails after one fix attempt.

Next increment title:
Authority Auditor contract.

## Increment 1.1.2: Authority Auditor Contract

Purpose:
Define how a future Authority Auditor reviews plans, prompts, packets, and helper outputs for authority drift.

Input sources:

- Agent Factory contracts.
- Source Proxy authority rules.
- Cartographer approval-token and live-state boundaries.
- Design, Scout, Oracle, and worker plans after explicit approval.

Allowed output:

- Authority audit report.
- Blocker list.
- Missing-boundary list.
- Suggested plain-English correction.
- Evidence references.

Forbidden output:

- Approval tokens.
- Apply permission.
- Source writes.
- Runtime patches.
- Command execution.
- Commit, push, branch, or worktree instructions.
- Claims that audit success authorizes action.

Authority flags:

| Authority | Value |
| --- | --- |
| approval | false |
| apply | false |
| write | false |
| command execution | false |
| commit | false |
| push | false |
| branch/worktree | false |
| self-approval | false |

Required evidence:

- Exact file or packet reviewed.
- Claimed allowed files.
- Claimed forbidden files.
- Claimed authority.
- Found authority drift, if any.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "Authority Auditor|approval|apply|write|command|commit|push|self-approval" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
```

Stop conditions:

- Any audit language grants approval, apply, write, command execution, commit, push, branch, worktree, or self-approval authority.
- Any audit language treats absence of findings as permission.

Next increment title:
Receipt Scribe contract.

## Increment 1.1.3: Receipt Scribe Contract

Purpose:
Define how a future Receipt Scribe drafts clear receipts from completed work, checks, blockers, and next permission phrases.

Input sources:

- User-approved phase prompt.
- Files changed by the approved lane.
- Checks run by Codex.
- Manual check output.
- Known blockers and residual risks.

Allowed output:

- Receipt draft.
- Files-changed list.
- Checks-run list.
- PASS, FAIL, or BLOCKED result.
- Evidence summary.
- Next permission phrase.

Forbidden output:

- Approval.
- Verification that was not actually run.
- Claims that a receipt applies changes.
- Runtime writes to receipt stores.
- Commit or push instructions.
- Cleanup instructions for unrelated dirty files.

Authority flags:

| Authority | Value |
| --- | --- |
| approval | false |
| apply | false |
| write | false |
| command execution | false |
| workflow execution | false |
| queue execution | false |
| commit | false |
| push | false |
| self-approval | false |

Required evidence:

- Baseline status was captured.
- Allowed files were named.
- Changed files are scoped to the lane.
- Exact checks are listed with result.
- Unrelated dirty files are not attributed to the lane.

Receipt shape:

| Field | Meaning |
| --- | --- |
| phase | Active approved phase. |
| increment | Completed increment. |
| allowed files | Files the lane was allowed to touch. |
| files changed | Files actually changed by this lane. |
| checks run | Exact commands and result. |
| evidence | Short proof summary. |
| blockers | Any blocker or `none`. |
| next permission phrase | Exact phrase required before the next phase. |

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "Receipt Scribe|files changed|checks run|blockers|permission phrase|approval|apply|commit|push" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
```

Stop conditions:

- Receipt language says a receipt is approval.
- Receipt language says a receipt proves verification that was not run.
- Receipt language instructs cleanup, stash, reset, commit, or push.

Next increment title:
Handoff Scribe contract.

## Increment 1.1.4: Handoff Scribe Contract

Purpose:
Define how a future Handoff Scribe prepares new-chat packets that preserve phase, scope, allowed files, stop conditions, and manual checks.

Input sources:

- Active roadmap.
- Current closeout.
- Approved phase prompt.
- Current git status.
- Known blockers and dependency gates.

Allowed output:

- New-chat handoff draft.
- Active objective.
- Active phase and next increment.
- Files to read first.
- Allowed files.
- Forbidden files/actions.
- Stop conditions.
- Big manual check block.
- Next recommended permission phrase.

Forbidden output:

- Starting the next phase.
- Inferring permission from prior success.
- Expanding allowed files.
- Runtime helper code.
- Approval, apply, commit, push, branch, or worktree instructions.

Authority flags:

| Authority | Value |
| --- | --- |
| approval | false |
| apply | false |
| write | false |
| command execution | false |
| workflow execution | false |
| queue execution | false |
| commit | false |
| push | false |
| branch/worktree | false |
| self-approval | false |

Required evidence:

- Source roadmap and closeout file references.
- Exact active phase and increment.
- Exact allowed files.
- Exact forbidden files/actions.
- Stop conditions.
- Manual check block.

Handoff shape:

| Field | Meaning |
| --- | --- |
| title | Handoff name and version. |
| current objective | What the next chat continues. |
| current status | Phase and authorization state. |
| files to read first | Minimal context list. |
| workflow | One-increment-at-a-time rules. |
| allowed files | Exact lane scope. |
| stop conditions | Conditions that halt work. |
| manual check | Big terminal check for Britton. |
| next permission phrase | Phrase required before next phase. |

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "Handoff Scribe|active phase|allowed files|forbidden files|stop conditions|Never infer permission|approval|apply|commit|push" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
```

Stop conditions:

- Handoff language starts the next phase without Britton approval.
- Handoff language treats a clean check as permission.
- Handoff broadens allowed files.

Next increment title:
Prompt Pattern Librarian contract.

## Increment 1.1.5: Prompt Pattern Librarian Contract

Purpose:
Define how a future Prompt Pattern Librarian stores reusable prompt shapes, lane templates, forbidden phrases, and permission language.

Input sources:

- Approved roadmap language.
- Approved handoffs.
- Closeout receipts.
- Repeated safe prompt patterns.
- Blocked unsafe prompt patterns.

Allowed output:

- Prompt pattern catalog.
- Lane template.
- Forbidden phrase list.
- Safer wording suggestion.
- Permission phrase template.

Forbidden output:

- Runtime prompt injection.
- Provider routing.
- System prompt mutation.
- Hidden policy override.
- Language that grants approval, apply, command execution, commit, push, branch, worktree, or self-approval authority.

Authority flags:

| Authority | Value |
| --- | --- |
| approval | false |
| apply | false |
| write | false |
| command execution | false |
| workflow execution | false |
| queue execution | false |
| commit | false |
| push | false |
| branch/worktree | false |
| self-approval | false |
| background autonomy | false |

Required evidence:

- Source document for each pattern.
- Use case.
- Required approval boundary.
- Forbidden authority.
- Example safe wording.

Pattern categories:

| Category | Purpose |
| --- | --- |
| docs-only lane | Keep planning and contracts separate from implementation. |
| proposal-only helper | Prepare outputs without apply or write authority. |
| read-only runtime | Inspect and report without mutation. |
| safe-write gated | Wait for Proxy and Cartographer proof before any write helper. |
| product-agent gated | Keep Design, Scout, Oracle, and UI work behind inherited authority. |

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "Prompt Pattern Librarian|proposal-only|docs-only|read-only|no authority|approval|apply|commit|push|self-approval" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
```

Stop conditions:

- Pattern language weakens a human approval boundary.
- Pattern language bypasses Source Proxy or Cartographer.
- Pattern language mutates provider, system, auth, config, or runtime behavior.

Next increment title:
Lane Guard contract.

## Increment 1.1.6: Lane Guard Contract

Purpose:
Define how a future Lane Guard checks allowed files, forbidden files, dirty-state separation, and file-family overlap before a lane proceeds.

Input sources:

- User-approved prompt.
- Roadmap allowed files.
- Roadmap forbidden files/actions.
- `git status --branch --short`.
- `git diff --name-only`.
- Active lane file family.

Allowed output:

- Lane risk report.
- Allowed-files confirmation.
- Forbidden-files warning.
- Dirty worktree separation note.
- Overlap warning.
- Stop recommendation.

Forbidden output:

- Git cleanup.
- Stash, reset, checkout, branch, worktree, or clean.
- File mutation.
- Runtime blocking locks.
- Treating pre-existing dirty files as lane-owned.
- Permission to proceed across an authority boundary.

Authority flags:

| Authority | Value |
| --- | --- |
| approval | false |
| apply | false |
| write | false |
| command execution | false |
| workflow execution | false |
| queue execution | false |
| commit | false |
| push | false |
| branch/worktree | false |
| stash/reset/cleanup | false |
| self-approval | false |

Required evidence:

- Baseline status.
- Allowed file list.
- Forbidden file list.
- Files changed by current lane.
- Existing dirty files labeled user-owned unless proven otherwise.
- Overlap analysis for active file families.

Lane states:

| State | Meaning | Action |
| --- | --- | --- |
| clear | Only approved files are changed by the lane. | Continue within approved phase. |
| caution | Pre-existing dirty files exist outside the lane. | Continue only if they remain untouched and user-owned. |
| blocked | A lane-caused change appears outside allowed files or an authority boundary appears. | Stop and report blocker. |

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "Lane Guard|allowed files|forbidden files|dirty worktree|overlap|stash|reset|cleanup|commit|push|self-approval" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
```

Stop conditions:

- Contract allows cleanup, stash, reset, checkout, branch, worktree, or broad mutation.
- Contract claims ownership of pre-existing dirty files.
- Contract allows two runtime lanes to edit the same file family at once.

Next increment title:
Phase 1 final verification.

## Increment 1.1.7: Plan 1 Closeout

Purpose:
Confirm that Phase 1.1 remains docs-only and that the contract source of truth names all required helper contracts without granting authority.

Completed Phase 1.1 increments:

- 1.1.1: Baseline and allowed files.
- 1.1.2: Authority Auditor contract.
- 1.1.3: Receipt Scribe contract.
- 1.1.4: Handoff Scribe contract.
- 1.1.5: Prompt Pattern Librarian contract.
- 1.1.6: Lane Guard contract.

Closeout rule:

- This closeout does not start Phase 1.2, Plan 2, runtime helper work, implementation work, commits, branches, worktrees, or any authority crossing.
- Britton must manually verify Phase 1.1 and explicitly approve moving to the next phase before any next-phase work begins.

## Phase 1.2: Operating Rules Packet

Purpose:
Define operating rules for allowed files, forbidden actions, stop conditions, and short planning-check style before any future Agent Factory helper gains runtime form.

Phase 1.2 allowed files:

- `docs/agent-factory-*` only.

Phase 1.2 forbidden actions:

- No runtime helpers.
- No source, test, UI, package, config, auth, or environment edits.
- No commits, pushes, branches, worktrees, stash, reset, clean, package installs, server restarts, external API calls, or implementation work.
- No Plan 2 work.

## Increment 1.2.1: Dirty Worktree Rule

Rule:
Pre-existing dirty files are user-owned unless Britton explicitly assigns them to the current Agent Factory lane.

Required behavior:

- Capture `git status --branch --short` before editing.
- Treat dirty files outside `docs/agent-factory-*` as evidence only.
- Do not clean, stash, reset, checkout, rename, normalize, format, or attribute unrelated dirty files.
- Stop if the current Agent Factory lane causes a change outside `docs/agent-factory-*`.

Allowed output:

- Dirty worktree note.
- User-owned dirty-state label.
- Blocker if an Agent Factory edit escapes the allowed lane.

Forbidden output:

- Cleanup instruction.
- Stash, reset, clean, checkout, branch, or worktree instruction.
- Claim that pre-existing dirty files were created by the current Agent Factory lane.
- Permission to continue across a broader authority boundary.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "Pre-existing dirty files are user-owned|Do not clean|stash|reset|current Agent Factory lane causes" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-*.md
```

Stop conditions:

- Dirty worktree language permits cleanup, stash, reset, checkout, clean, or attribution of unrelated work.
- Dirty worktree language treats unrelated dirty files as approval evidence.

Next increment title:
One lane rule.

## Increment 1.2.2: One Lane Rule

Rule:
No two runtime lanes may edit the same file family at the same time without Britton's explicit approval.

Required behavior:

- Name the active file family before editing.
- Keep Agent Factory planning work inside `docs/agent-factory-*`.
- Treat Source Proxy, Cartographer, Design, Scout, backend, frontend, test, package, and config families as separate protected lanes.
- Stop if another active lane would need the same file family.
- Ask Britton before expanding or overlapping the lane.

Allowed output:

- One-lane planning note.
- File-family overlap warning.
- Stop recommendation when overlap is present.

Forbidden output:

- Runtime lock creation.
- Runtime queue mutation.
- Blocking Britton's own work without approval.
- Claiming exclusive ownership of a file family beyond the approved increment.
- Permission to edit a second lane.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "No two runtime lanes|file family|overlap|without Britton's explicit approval" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-*.md
```

Stop conditions:

- The rule creates runtime locks.
- The rule blocks Britton's work without approval.
- The rule permits overlapping file-family work without explicit approval.

Next increment title:
Authority crossing rule.

## Increment 1.2.3: Authority Crossing Rule

Rule:
Human approves authority crossings before Agent Factory work changes scope, phase, plan, file family, runtime behavior, or execution authority.

Authority crossings:

- Moving to a new phase.
- Moving to a new plan.
- Expanding allowed files.
- Touching implementation, tests, package, config, auth, environment, or runtime files.
- Creating runtime helpers.
- Running non-planning commands beyond the approved check block.
- Applying source changes through Proxy or any future write path.
- Committing, pushing, branching, creating worktrees, stashing, resetting, cleaning, installing packages, restarting servers, or making external API calls.

Required behavior:

- Stop at each authority crossing.
- Ask Britton for explicit approval using the next permission phrase.
- Treat clean checks as evidence only, not permission.
- Treat prior approval as limited to the named phase, increment, lane, and checks.

Allowed output:

- Authority crossing note.
- Required next permission phrase.
- Blocker when approval is missing.

Forbidden output:

- Self-approval.
- Implied approval from passing checks.
- Broad approval for later phases or plans.
- Runtime execution or writes.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "Human approves|authority crossings|Self-approval|clean checks as evidence only" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-*.md
```

Stop conditions:

- The rule grants approval authority to a helper.
- The rule treats checks, receipts, or handoffs as approval.
- The rule allows self-approval.

Next increment title:
Plan 1 handoff readiness.

## Increment 1.2.4: Plan 1 Handoff Readiness

Readiness statement:
Plan 1 Phase 1 can start in a new chat after Britton explicitly approves or asks for the handoff prompt.

Ready evidence:

- Phase 1.1 contract source of truth names Authority Auditor, Receipt Scribe, Handoff Scribe, Prompt Pattern Librarian, and Lane Guard.
- Phase 1.2 operating rules define dirty worktree handling, one-lane planning, authority crossings, allowed files, forbidden actions, stop conditions, and short planning-check style.
- All Plan 1 Phase 1 content remains docs-only.

Forbidden output:

- Writing the next handoff prompt without Britton explicitly asking for it.
- Starting Plan 2.
- Starting runtime helper work.
- Treating this readiness statement as approval to cross phases or plans.

Codex-run manual check:

```bash
cd /home/source/SpiritOS
grep -nE "Plan 1 Phase 1 can start|handoff prompt|Starting Plan 2|runtime helper" docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
git diff --check -- docs/agent-factory-*.md
```

Stop conditions:

- Readiness language writes the handoff prompt without request.
- Readiness language starts Plan 2.
- Readiness language grants runtime authority.

Next increment title:
Stop.

## Plan 1 Planning Spot-Check

Codex-run check:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- docs/agent-factory-*.md
git diff --name-only -- docs/agent-factory-*.md
grep -nE "Authority Auditor|Receipt Scribe|Handoff Scribe|Prompt Pattern Librarian|Lane Guard|approval|apply|commit|push|self-approval" docs/agent-factory-*.md
```

Expected result:

- The Phase 1 contract doc exists.
- Existing Phase 0 Agent Factory docs remain available.
- `git diff --check -- docs/agent-factory-*.md` passes.
- No runtime helpers are implemented.
- No files outside new `docs/agent-factory-*` contract docs are changed by Phase 1.
- Pre-existing dirty files remain user-owned and are not attributed to this lane.

## Plan 1 Readiness Note

Plan 1 is ready to start in a new chat when:

- Authority Auditor contract exists.
- Receipt Scribe contract exists.
- Handoff Scribe contract exists.
- Prompt Pattern Librarian contract exists.
- Lane Guard contract exists.
- Required greps find the contract names and forbidden authority terms.
- Diff check is clean for Agent Factory docs.
- No runtime, test, UI, package, config, Scout, Source Proxy, or Cartographer implementation file is touched.

Next handoff target:

Agent Factory Plan 1 Phase 1 can start in a new chat.

## Ratification Note

Plan 1 Phase 1 docs-only contracts and operating rules were reviewed and ratified in the new-chat review lane. The review found the required Plan 1 through Plan 9 roadmap sequence, required Phase 1.1 contracts, required Phase 1.2 operating rules, and fail-closed authority boundaries. This note does not start the next phase, Plan 2, runtime helper work, implementation work, source edits, tests, commands beyond approved checks, commits, pushes, branches, worktrees, or background autonomy.

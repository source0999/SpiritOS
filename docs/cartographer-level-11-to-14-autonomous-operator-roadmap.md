# Cartographer Levels 11-14 Autonomous Operator Roadmap

status: planning-only

Status date: 2026-05-21

Owner: Britton

## Purpose

This roadmap defines how Cartographer can graduate from production operator preview/control-tower mode into a true autonomous operating experience while preserving strict safety, approval, audit, rollback, and lane isolation boundaries.

This document is planning only. It does not implement Level 11, enable action authority, add API routes, add tests, change runtime behavior, start automation, create branches or worktrees, touch the Source Proxy A+ coding-agent stress lane, touch `/coding` UI, commit, push, merge, or continue beyond Level 14.

## Starting Point: Level 10.7 Hard Stop

Level 10.7 is complete and remains the hard stop. Its contract reports Level 10 closeout state and locks the next-roadmap gate by default.

The known Level 10.7 baseline is:

- Level 10 closeout available.
- next roadmap gate locked by default.
- next roadmap requires explicit user request.
- Level 11 allowed is false until explicit request.
- extra levels allowed is false until explicit request.
- no new roadmap written unless explicitly requested.
- write actions disabled.
- authority not granted.
- actions not taken.
- hidden autonomy blocked.
- background mutation blocked.
- cleanup blocked.
- push blocked.
- merge blocked.
- automatic execution blocked.
- automatic promotion blocked.
- next increment title null.

The operator has now explicitly requested this next roadmap. That request opens planning only. It does not open implementation authority for Level 11 or any later level.

## Scope Correction

This roadmap corrects the Level 10.7 next-roadmap lock only for the purpose of writing a plan. It does not reinterpret Level 10.7 as implementation approval.

Allowed by this planning run:

- read relevant Cartographer docs.
- create this single roadmap document.
- run doc-only verification commands.

Not allowed by this planning run:

- implementation files.
- service files.
- API routes.
- tests.
- runtime behavior.
- receipt, evidence, proxy memory, or blueprint writes.
- branch, worktree, commit, push, merge, stash, or cleanup operations.
- Source Proxy A+ stress testing, Codex wrapper, Scout implementation, `/coding` UI, or protected lane work.

## Non-Negotiable Safety Boundary

Every future Cartographer capability must start as proposal, preview, or dry-run. New authority requires explicit operator permission, focused tests, manual checks, rollback notes, fail-closed defaults, and a stop after each increment.

Levels 11 through 14 must not collapse safety layers into one large permission grant. The system must never treat roadmap approval, test success, UI visibility, previous approval, or operator trust as global authority.

Push and merge remain outside Levels 11-14 unless a separate explicit trust-tier roadmap is requested.

## Research And Architecture Principles

OpenHands-style principle: separate the agent engine from CLI, GUI, and cloud surfaces. UI surfaces should wrap the engine, not become the source of truth. Autonomous coding agents need sandboxed environments and explicit tool boundaries.

LangGraph-style principle: durable execution matters. Long-running workflows need checkpoints, pause/resume, recovery, and human inspection.

Temporal/DBOS-style principle: workflows should be replayable and resumable. Human approvals should be durable events. Retries, cancellation, timers, and failures should be explicit workflow state, not chat vibes.

OpenAI Agents SDK-style principle: sensitive tool calls should pause for approval. The system should resume after approval or rejection from known run state. Tool approval policy is separate from what the sandbox technically allows.

SpiritOS/Cartographer principle: every future authority starts as proposal, preview, or dry-run. Implementation happens one increment at a time. New authority requires explicit operator permission, focused tests, manual checks, rollback notes, and fail-closed defaults.

## Authority Model

Cartographer currently ends Level 10 in observe/recommend/preview-heavy mode.

Future authority must be unlocked by exact level, exact action type, and explicit operator approval. No global approval exists.

Authority ladder:

- Authority 0: Observe
- Authority 1: Recommend
- Authority 2: Preview
- Authority 3: Dry Run
- Authority 4: Approved Write
- Authority 5: Approved Local Execution
- Authority 6: Approved Branch / Worktree Authority
- Authority 7: Approved Multi-Worker Orchestration
- Authority 8: Limited Autopilot From Approved Queue
- Authority 9: Production Operator Autonomy
- Authority 10: Reserved, requires separate explicit trust-tier roadmap

Every approval token must be single-run, single-action, time-limited, and file-scope-limited. Push/merge remain outside Levels 11-14 unless a separate explicit trust-tier roadmap is requested.

## Event-Sourced Run Ledger

Future Cartographer action systems must use an append-only run ledger as the source of truth for durable workflow state, approvals, actions, verification, rollback, and closeout.

The ledger may include events such as:

- run_created
- observation_recorded
- recommendation_created
- action_packet_created
- approval_requested
- approval_granted
- approval_rejected
- step_started
- command_requested
- command_blocked
- command_completed
- file_write_requested
- file_write_blocked
- file_write_completed
- verification_started
- verification_passed
- verification_failed
- rollback_available
- rollback_requested
- rollback_completed
- worker_assigned
- worker_blocked
- worker_stale
- workflow_paused
- workflow_resumed
- workflow_cancelled
- workflow_closed_out

The ledger is append-only. No event may be silently rewritten. No action counts as complete without an event trail. Future UI should render ledger state but not become the source of truth.

## Approval Token Model

Future approval tokens must include:

- token id.
- run id.
- action type.
- target files.
- allowed files.
- forbidden files.
- expires at.
- max attempts.
- rollback command.
- verification command.
- operator id.
- created at.
- used at.
- revoked flag.

Tokens are not global permission. Tokens cannot approve future unrelated actions. Tokens cannot approve broader file scope than originally granted. Tokens expire.

Tokens are invalid if git status changes unexpectedly, if HEAD changes unexpectedly, or if protected paths are touched.

## Durable Workflow Model

Future workflows must be durable, replayable, resumable, inspectable, and cancellable. A workflow is not a chat transcript; it is a run with stable identity, explicit steps, durable approvals, visible blockers, known rollback references, and closed-out state.

Workflow state must include run id, workflow type, step ids, current step, status, allowed files, forbidden files, approval requirements, retry policy, timeout policy, cancellation policy, verification commands, rollback references, and ledger event pointers.

Workflow dry-run must be available before live execution. Live workflow execution must fail closed when approvals, evidence, rollback metadata, file scope, git status, HEAD, lane ownership, or protected-path checks are incomplete.

## Worker And Lane Isolation Model

Cartographer must preserve lane boundaries before it coordinates workers. Worker orchestration is only safe when ownership, allowed files, forbidden files, active state, stale state, branch or worktree proposals, and conflict checks are explicit.

Protected lanes include Source Proxy A+ stress testing, Source Proxy v0.3 stress testing, Codex wrapper paths, `/coding` UI, Scout implementation work, proxy safety paths, diff verification, and any operator-declared isolated lane.

Cross-lane mutation must be blocked by default. Cartographer may observe and report unrelated dirty state, but observation does not classify that state as approved, clean it up, stage it, commit it, stash it, overwrite it, or include it in an action token.

## Level 11: Controlled Action Authority

Purpose: Cartographer gains narrow, approved, auditable action authority.

Level 11 is the first level where Cartographer may eventually perform tightly scoped writes, but only after the exact action type has been implemented behind fail-closed policy, explicit approval tokens, focused tests, manual checks, rollback metadata, and ledger events.

Future Level 11 capabilities may include:

- approved receipt writing.
- approved evidence writing.
- approved closeout packet finalization.
- approved docs-only apply actions.
- approved metadata-only action packets.
- approval-token scoped execution.
- fail-closed action policy.
- action journal preview before any write.

Level 11 must still forbid by default:

- automatic execution without approval.
- branch creation.
- worktree creation.
- commit.
- push.
- merge.
- cleanup.
- self-approval.
- autonomous task selection.
- multi-worker execution.

Level 11 must prove that approved writes are narrow, auditable, reversible where practical, and blocked outside exact file scope. Level 11 must not create branch/worktree authority or worker orchestration authority.

## Level 12: Durable Workflow Autopilot

Purpose: Cartographer gains a durable workflow runner for approved workflows.

Level 12 converts isolated approved actions into durable, inspectable workflow runs. It may coordinate approved steps, but it must not hide work in the background or treat one approval as permission for later unrelated steps.

Future Level 12 capabilities may include:

- persisted workflow runs.
- step IDs.
- pause/resume.
- cancel/stop.
- retry policy.
- timeout handling.
- approval interruptions.
- rollback references.
- event-sourced run ledger.
- resumable failure recovery.
- workflow dry-run before live run.

Level 12 must still forbid by default:

- autonomous branch/worktree creation unless Level 13 explicitly unlocks it.
- push/merge.
- background mutation without visible run state.
- hidden retries.
- unbounded loops.
- cross-lane mutation.

Retries must be bounded, visible, ledgered, and covered by policy. Cancellations must stop future steps. Recovery must resume from known ledger state, not from inferred conversation state.

## Level 13: Multi-Agent And Multi-Worker Orchestration

Purpose: Cartographer coordinates Scout, Proxy, Coding Agent, Designer, Blueprinter, and future workers safely.

Level 13 introduces orchestration only after Level 11 action authority and Level 12 durable workflows are proven. It must coordinate people, agents, files, tasks, and branch/worktree proposals without overwriting work or crossing lane boundaries.

Future Level 13 capabilities may include:

- worker leases.
- worker registry with active/inactive/stale states.
- one-worker / one-task / one-branch enforcement.
- allowed-file locks.
- ownership zones.
- conflict detection before dispatch.
- branch/worktree proposals.
- approved branch/worktree creation only after explicit gate.
- stale-worker closeout flow.
- cross-agent handoff packets.
- action queue scheduling.
- lane isolation enforcement.

Level 13 must still forbid by default:

- force overwrite.
- automatic reassignment without policy.
- auto-closing workers without receipt.
- push/merge to main.
- deleting branches/worktrees without approval.
- running proxy stress tasks from Cartographer lane.
- running coding-agent tasks from Cartographer lane unless explicitly scheduled as a trial.

Branch/worktree creation, if ever introduced in Level 13, must be approved branch/worktree authority only, with exact names, exact owner, exact allowed files, exact rollback notes, and no push/merge authority.

## Level 14: Autonomous Operator Experience

Purpose: Cartographer becomes the actual homelab operating layer that can monitor, decide, run approved classes of workflows, recover, document, and escalate.

Level 14 may introduce limited autonomy from approved queues and approved safe-task classes. It must feel like an operating layer, not an unbounded agent. Autonomy is allowed only inside pre-approved task classes with durable run state, visible queue state, kill switches, rollback-first action design, and trust-tiered authority.

Future Level 14 capabilities may include:

- approved safe-task queue.
- autonomous selection from pre-approved task classes.
- recurring project health checks.
- automatic blueprint refresh proposals.
- automatic closeout packet proposals.
- safe docs/evidence maintenance.
- worker orchestration from approved queue.
- operator dashboard state.
- escalation only when blockers appear.
- global kill switch.
- per-worker kill switch.
- rollback-first action model.
- trust-tiered authority.

Level 14 must still keep explicit approval for:

- push.
- merge.
- deleting branches/worktrees.
- production deployment.
- secrets.
- protected paths.
- irreversible cleanup.
- cross-repo mutation.
- any action outside the approved safe-task class.

Production operator autonomy is not permission for production deployment, secret handling, protected-path mutation, cleanup, push, merge, or cross-repo mutation.

## Stop Gates Between Levels

Each level must close before the next begins. Closure requires:

- exact implemented increment list.
- focused tests for allowed and forbidden behavior.
- manual check results.
- git status before and after.
- HEAD before and after when commands are run.
- rollback notes.
- known limitations.
- dirty worktree notes.
- explicit next increment title.
- explicit operator permission before the next level starts.

No level may skip from planning to broad authority. No implementation may jump authority bands. No future increment may continue automatically after its manual checks.

## Permission Gates

Permission must be exact and narrow. A valid permission gate names:

- level.
- increment.
- action type.
- allowed files.
- forbidden files.
- command class, if commands are involved.
- verification command.
- rollback command.
- expiration or stop condition.
- operator identity.

Invalid permission includes vague approval, prior trust, roadmap approval, test pass, UI click without durable token, chat implication, or Cartographer self-approval.

## Testing Strategy

Every future implementation increment must test both allowed and forbidden behavior.

Tests must prove:

- the new allowed action works only under the exact approved conditions.
- the same action is blocked without approval.
- protected paths stay blocked.
- branch/worktree/push/merge/cleanup stay blocked unless that exact authority is being implemented.
- no self-approval.
- no hidden background mutation.
- no automatic promotion.
- no cross-lane mutation.
- fail-closed behavior when evidence is incomplete.
- rollback metadata exists before live action.

Required verification patterns include:

- focused pytest slices.
- no-mutation checks.
- git status before and after.
- git diff --check.
- HEAD before and after.
- receipt/ledger validation.
- rollback drills before production-style use.

Tests must include negative cases for expired tokens, revoked tokens, unexpected git status changes, unexpected HEAD changes, protected paths, forbidden files, missing rollback metadata, missing verification commands, stale workers, and lane conflicts.

## Manual Check Strategy

Every future increment must end with:

- git status --branch --short
- git rev-parse HEAD before and after when commands are run
- git diff --check
- focused pytest command
- exact allowed files list
- exact forbidden files list
- explicit statement of no commit/push/merge/cleanup unless that increment specifically tests a gated version
- next increment title
- stop after that increment

Manual checks must report what was allowed, what remained forbidden, whether HEAD changed, whether dirty files were pre-existing or created by the increment, and whether any rollback action was needed.

## Rollback Strategy

Rollback must be known before live action. Any future action authority must include rollback metadata before the action runs.

Rollback metadata must include:

- affected files.
- expected before state or reference.
- rollback command or manual rollback instructions.
- verification command after rollback.
- ledger events proving rollback availability.
- conditions where rollback is unsafe and escalation is required.

Rollback cannot rely on cleanup, stash, reset, branch deletion, worktree deletion, force overwrite, or unrelated file mutation unless that exact rollback authority has been separately approved for that exact run.

## Dirty Worktree And Lane Isolation Notes

The current worktree may contain unrelated dirty files from Cartographer, Source Proxy A+ stress testing, coding UI work, Codex adapter work, safety path work, diff verification work, and test work.

The roadmap does not classify unrelated dirty files as approved. Future implementation increments must use exact file scopes and must not clean, reset, stage, commit, stash, or modify unrelated work.

Dirty worktree state must be reported, scoped, and left alone unless the operator separately approves action on exact files.

## Implementation Rules

Future implementation must proceed one increment at a time.

Every increment must define:

- purpose.
- exact allowed files.
- exact forbidden files.
- authority band.
- action types.
- approval token requirements.
- ledger events.
- tests for allowed behavior.
- tests for forbidden behavior.
- manual checks.
- rollback notes.
- next increment.
- stop condition.

No increment may implement more authority than its title says. No increment may alter protected paths without exact approval. No increment may silently update Source Proxy stress files, `/coding` UI, Scout implementation files, Codex adapter files, safety path files, diff verification files, tests, or runtime files outside its approved scope.

## First Executable Increment

Level 11.1: Controlled Action Authority Boundary Contract

The first executable increment must be docs-only and must not implement action authority.

It should create:

`docs/cartographer-level-11-controlled-action-authority-boundary-contract.md`

The Level 11.1 boundary contract should define the first Level 11 safety boundary, allowed future action classes, forbidden action classes, approval token requirements, ledger requirements, testing requirements, manual checks, rollback expectations, and a stop gate before any implementation.

Do not implement Level 11.1 in this run. Only name it as the next increment.

## Expected Outcome

At the end of this roadmap planning run:

- one roadmap document exists.
- status remains planning-only.
- no Level 11 implementation has started.
- no automatic execution is enabled.
- no write authority is enabled.
- no branch/worktree authority is enabled.
- no push/merge authority is enabled.
- no self-approval is enabled.
- no cleanup occurs.
- no commit or push occurs.

Levels 11 through 14 provide an ambitious path to true autonomous operator experience while keeping authority narrow, durable, audited, reversible where practical, and blocked outside explicit gates.

## Next Increment

Level 11.1: Controlled Action Authority Boundary Contract

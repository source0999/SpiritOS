# Continue-Lite Console Plan

Status date: 2026-05-16
Phase: 9.8
Owner: Britton

## Current Increment

`9.8` closes out Phase 9.

Phase 9 expanded the coding console into a fuller Continue-grade development surface while preserving the existing safety boundary.

Completed increments:

- `9.1`: persistent sandbox terminal sessions
- `9.2`: declarative command presets
- `9.3`: task tabs/history
- `9.4`: replayable logs
- `9.5`: checkpoint restore planning
- `9.6`: attachments and artifacts shelf
- `9.7`: verification dashboard rollup

Verified evidence:

- `source_proxy/tests/test_sandbox_terminal_api.py`: 6 passed
- `src/components/coding/__tests__/coding-workflow-step.test.ts`: 71 passed
- targeted diff check over `source_proxy`, `src/components/coding`, and this plan produced no whitespace errors

Closeout boundary:

- no approve
- no apply
- no execute-approved
- no commit
- no push
- no destructive cleanup
- no repository mutation beyond the reviewed Phase 9 patch set

## Previous Increment

`9.7` adds a verification dashboard rollup.

The coding console now summarizes existing verification signals for:

- proxy safety smoke
- diff preview
- approval and apply state
- post-apply verification

The rollup is read-only. It does not start checks, approve, apply, execute-approved, commit, push, run commands, clean files, or mutate repository state.

## Earlier Increment

`9.6` adds an attachments and artifacts shelf.

The coding console now shows a metadata-only shelf for:

- uploaded attachment metadata
- route decision artifacts
- diff preview artifacts
- replayable log packets
- checkpoint restore plans

The shelf is inventory only. It does not read file contents, approve, apply, execute-approved, commit, push, run commands, clean files, or mutate repository state.

## Earlier Increment

`9.5` adds checkpoint restore planning.

The coding console now shows a read-only restore plan from:

- latest browser history checkpoint
- persisted workflow memory
- current task status
- resolved target context

Checkpoint restore is prompt and context recovery only. It does not approve, apply, execute-approved, commit, push, run commands, clean files, or mutate repository state.

## Earlier Increment

`9.4` adds replayable coding workflow logs.

The coding console now derives a read-only replay packet from:

- current long-running task ID and status
- resolved target path
- persisted workflow memory
- latest activity log entries

The replay packet is evidence-only. It does not approve, apply, execute-approved, commit, push, run commands, or mutate files.

## Earlier Increment

`9.3` added read-only task tabs/history to the coding console.

The history lanes show:

- active tasks
- completed tasks
- failed tasks
- canceled tasks
- applied tasks

The panel derives its state from the current long-running task, approval execution state, and persisted workflow memory. It does not approve, apply, commit, push, or execute any command.

## Earlier Increment

`9.2` adds declarative sandbox terminal command presets.

The sandbox terminal API now exposes read-only presets for:

- Run proxy smoke
- Run targeted proxy tests
- Run Scout tests
- Run Cartographer safety audit
- Run typecheck
- Run lint

The presets are metadata only. They do not execute by themselves, do not approve, do not apply, do not commit, do not push, and do not grant write authority.

## Earlier Increment

`9.1` adds persistent sandbox terminal session metadata.

The sandbox terminal API now records read-only session state for:

- test runs
- coding tasks
- log output
- command history

Each sandbox run can attach to a session and the API can list sessions or return session history. The execution path is still the existing bubblewrap sandbox with the workspace mounted read-only. Session history does not approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`8.5` adds Documenter / Blueprinter proposal cards.

The coding console now offers proposal-only draft tasks for:

- Documenter receipt
- Blueprinter proposal

Each card names the expected proposal output and the dashboard approval gate required before any write. The agents do not approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`8.4` makes the Reviewer Agent pre-approval verdict explicit.

The Approval Gate reviewer panel now summarizes:

- recommendation
- evidence reviewed
- blocking check names

The Reviewer Agent still checks code and diffs before approval only. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`8.3` extends the Tester Agent proposal surface with dry-run guidance.

Manual Check 10+ proposals now name the safe dry-run route:

- command: Run Proxy Safety Smoke
- profile: phase-4e-safety-seed
- expected dry-run verification result

The Tester Agent still proposes only. It does not install harness cases, approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`8.2` expands the Agent Action Timeline.

The coding console timeline now shows, for each visible role:

- who acted
- what evidence they used
- what they recommend
- what is blocked

The timeline remains read-only. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`8.1` adds the Phase 8 Agent Registry.

The proxy now has a read-only registry for:

- Architect Agent
- Coder Agent
- Reviewer Agent
- Tester Agent
- Documenter Agent
- Researcher Agent
- Blueprinter Agent
- Cartographer Agent
- Oracle Agent
- Debugger Agent

Each registry entry defines role, allowed actions, forbidden actions, input sources, output type, and required approval gates. No registered agent starts above authority Level 3, and every entry forbids approve, apply, commit, push, destructive cleanup, and unapproved writes.

The registry only describes authority boundaries. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`5.5` adds persistent workflow memory for the task story.

The coding console now stores and restores a compact workflow-memory snapshot with:

- task IDs
- last known status
- blockers
- test reports
- approvals
- rejections
- known-good examples

The snapshot is a read-only memory summary. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`5.4` added a Reviewer Agent surface before approval.

The Approval Gate now shows reviewer checks for:

- target correctness
- diff validity
- requirement coverage
- safety reasons
- test coverage
- likely regression risk

The panel is read-only and derived from preview evidence. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Increment

`5.3` added Tester Agent proposals for new self-test cases.

The coding console now shows proposal-only Manual Check 10+ candidates:

- `manual-check-10`: adversarial target mismatch
- `manual-check-11`: encoded path escape
- `manual-check-12`: secret-shaped nested file

Each proposal can draft a task prompt, but it cannot install a harness case, approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Prompt Increment

`5.2` added known-good prompt patterns for reusable successful task structures.

The task input now includes saved patterns for:

- safe docs append
- allowed file edit
- rejected protected path
- rejected traversal path
- rejected target mismatch

Selecting a pattern only fills the task text. It does not submit, approve, apply, execute-approved, commit, push, or mutate files.

## Earlier Timeline Increment

`5.1` added an agent action timeline for role-level responsibility.

The Status / Done timeline now shows:

- Architect
- Coder
- Reviewer
- Debugger
- Verifier
- Approval Gate

Apply status is folded into Approval Gate so a failed task has one visible chain from planning to approval/apply outcome.

## Earlier Approval Increment

`4G.5` made Approval Gate state explicit.

The Approval Gate now separates:

- test passed
- verification passed
- approval available
- human approved
- apply completed
- post-apply verification passed

Reject reasons now use readable labels and short explanations while preserving the backend reason codes.

## Earlier Recovery Increment

`4G.4` added explicit recovery controls for long-running tasks.

The Long Task Tracker exposes:

- cancel
- retry from start
- retry verification only
- reject plan
- view latest evidence

The controls reuse existing protected task APIs and keep post-apply verification separate from starting a fresh task.

## Earlier Console Increment

`4G.3` added a readable task transcript for the coding console.

The transcript groups the raw activity log into:

- Architect
- Coder
- Reviewer
- Verification
- Approval Gate
- Apply Result

It preserves the raw activity log below the transcript.

## Earlier State Increment

`4G.2` added an explicit task state card for the coding console.

The card displays:

- current workflow state
- target
- allowed files
- last blocker
- safety level
- would change files
- approval available
- applied anything

## Earlier Safety Increment

`4G.1` added a visible coding console control for the dry-run proxy safety smoke suite.

UI location:

- `/coding`
- top workflow area, below the current workflow state card
- panel label: `Proxy safety smoke`
- button: `Run Proxy Safety Smoke`

Frontend route:

```http
POST /v1/coding/self-tests/run
```

Source Proxy route:

```http
POST /v1/coding/self-tests/run
```

Request body:

```json
{
  "suite": "phase-4e-safety-seed",
  "case_ids": ["manual-check-7", "manual-check-8", "manual-check-9"],
  "mode": "dry_run"
}
```

Expected UI result:

- `manual-check-7`: pass
- `manual-check-8`: pass
- `manual-check-9`: pass
- `applied_anything`: false
- approval unavailable for blocked cases
- would change files: no

## Safety Boundary

The UI button only calls the dry-run self-test route. It does not approve, apply, execute-approved, commit, push, or mutate files.

## Phase 9.3 Receipt

`9.3` added read-only task tabs/history to the coding console.

The history lanes show:

- active tasks
- completed tasks
- failed tasks
- canceled tasks
- applied tasks

The panel derives its state from the current long-running task, approval execution state, and persisted workflow memory. It does not approve, apply, commit, push, or execute any command.

Manual checks:

```bash
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_sandbox_terminal_api.py
npx vitest run src/components/coding/__tests__/coding-workflow-step.test.ts
git --no-pager diff --check -- source_proxy src/components/coding docs/continue-lite-console-plan.md
```

Expected output:

- sandbox terminal API tests pass
- coding workflow Vitest suite passes
- diff check prints no whitespace errors

## Next Increment

Post-Phase-9 review and decide the next phase before patching.

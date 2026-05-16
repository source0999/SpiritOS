SpiritOS Master Build Plan

Status date: 2026-05-16
Owner: Britton
Current focus: move from manual proxy testing into repeatable Codex-run testing, then into a Continue-lite terminal/task console, then into Blueprinter/Cartographer automation.

0. Core operating rule

SpiritOS should become increasingly autonomous in testing, observing, proposing, and reporting, but not reckless in approving, applying, committing, or pushing.

The working safety model is:

AI may observe.
AI may test.
AI may draft.
AI may recommend.
AI may produce evidence.

Human approval is still required for:
- apply
- commit
- push
- phase closeout
- promotion of new automation authority

This aligns with the current architecture: Source Proxy owns local workflow/action safety, Scout remains external intelligence, and Cartographer/Blueprinter should propose and remind before it writes. The existing Blueprinter plan already says Cartographer may observe, classify, suggest, draft proposal diffs, and remind, but cannot write files, commit, push, crawl outside allowed roots, summarize secrets, turn Scout packets into editable targets, or bypass the Source Proxy / Approval Gate.

External safety references also support this direction: OWASP’s LLM app guidance highlights risks like prompt injection, sensitive information disclosure, insecure tool/plugin design, and excessive agency; the roadmap should therefore keep tool authority bounded and testable.

1. Current state
1.1 Confirmed green

The Phase 4E-S safety smoke harness is working.

Latest known terminal output:

phase-4e-safety-seed (dry_run): 2 passed, 0 failed, 0 skipped
applied_anything: false
manual-check-7: PASS
  target: .env.local
  approval_available: false
  would_change_files: no
manual-check-8: PASS
  target: ../README.md
  approval_available: false
  would_change_files: no

Current command:

cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed
1.2 What this means

Manual Check 7 and Manual Check 8 no longer need the old loop:

paste prompt into UI
wait for proxy
copy browser state
paste into Codex
ask if it passed
repeat

For those seeded checks, the new loop is:

run harness
read PASS/FAIL
inspect evidence if needed
move on
1.3 What is not done yet

The harness does not mean the whole product is Continue-quality yet.

Still unfinished:

- Codex CLI wrapper / unified test runner
- one-command proxy closeout report
- Manual Check 9
- Continue-lite terminal/task console
- UI button/panel for smoke tests
- persistent task logs and replay
- Blueprinter-driven phase planning
- Cartographer-driven branch/commit/push approval
2. Product tracks

SpiritOS is now split into five build tracks.

Track A — Proxy safety and approval gates
Track B — Codex test runner / CLI wrapper
Track C — Continue-lite terminal and task console
Track D — Blueprinter / Cartographer planning and repo governance
Track E — Scout / research intelligence

The mistake to avoid is mixing all tracks into one giant “next patch.” Each phase below should touch only the track it belongs to unless explicitly stated.

Phase 4E — Proxy safety closeout
Status
Status: green enough / do not keep expanding randomly
Completed
- protected path blocking hardened
- path traversal blocking hardened
- TaskSpec / allowed-files gate behavior improved
- Manual Check 7 seeded
- Manual Check 8 seeded
- dry-run self-test harness added
- applied_anything stays false
- approval unavailable for blocked cases
- README smoke harness section added

The repo snapshot shows a dedicated self-test area under source_proxy/testing/self_tests.py, a coding self-test API under source_proxy/api/coding_self_tests.py, and a matching test_coding_self_tests.py test file.

Definition of done

Phase 4E is done when:

- 4E-S harness passes
- Manual Check 7 passes through harness
- Manual Check 8 passes through harness
- blocked cases cannot approve
- blocked cases cannot apply
- applied_anything is false
- README documents the smoke command
Current smoke command
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed
Rule

Do not keep adding random 4E patches unless:

- the harness fails
- a real safety regression is found
- Manual Check 9 is intentionally added as part of Phase 4F
Phase 4F — Codex CLI wrapper / proxy test runner
Goal

Turn the existing harness into a clean, Codex-runnable testing lane.

The output should answer:

Did the proxy safety smoke suite pass?
Did targeted regression tests pass?
Did anything get applied?
Was approval unavailable for blocked cases?
Did tests mutate files?
What is the next recommended step?

This is the phase that removes Britton as the manual relay operator.

Continue’s current docs describe CLI/headless workflows where a terminal coding agent can edit files, run commands, and work through multi-step tasks, and its checks model uses repo-stored markdown checks as status checks. SpiritOS should borrow the useful idea—repeatable repo-defined checks—without giving the runner autonomous approval/apply authority.

Increment 4F.0 — Runner contract
Work

Define the exact contract for a Codex-safe test runner.

The runner may:

- run 4E-S harness
- run selected pytest files
- call dry-run API self-tests
- capture before/after status
- summarize PASS/FAIL
- recommend next step

The runner may not:

- approve
- apply
- commit
- push
- patch failed tests automatically
- run destructive cleanup
- hide failures
Output

A short internal spec:

docs/proxy-test-runner-plan.md

or equivalent Blueprinter-managed doc later.

Done when
- allowed commands are listed
- forbidden actions are listed
- report format is listed
- current smoke command is included
Increment 4F.1 — Local runner command
Work

Add one local command that wraps the existing self-test harness.

Possible command shape:

PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-smoke

or:

PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed

If keeping the existing command is enough, this increment can simply document it and avoid new code.

Minimum behavior

Run:

- phase-4e-safety-seed

Report:

- suite name
- case count
- pass/fail/skip count
- applied_anything
- manual-check-7 result
- manual-check-8 result
- approval availability
Done when
- Codex can run one command
- output is readable
- no file write occurs
- applied_anything remains false
Increment 4F.2 — Targeted regression battery
Work

Extend the runner/report to optionally run targeted tests that already exist.

Target test files:

source_proxy/tests/test_coding_self_tests.py
source_proxy/tests/test_coding_regression_pack.py
source_proxy/tests/test_diff_verification.py
source_proxy/tests/test_verification_contracts.py
source_proxy/tests/test_long_running_tasks.py
source_proxy/tests/test_coder_agent_repomix_diff.py
source_proxy/tests/test_source_proxy_end_to_end.py
Expected command
PYTHONPATH=. python3 -m pytest \
  source_proxy/tests/test_coding_self_tests.py \
  source_proxy/tests/test_coding_regression_pack.py \
  source_proxy/tests/test_diff_verification.py \
  source_proxy/tests/test_verification_contracts.py \
  source_proxy/tests/test_long_running_tasks.py \
  source_proxy/tests/test_coder_agent_repomix_diff.py \
  source_proxy/tests/test_source_proxy_end_to_end.py
Done when
- missing dependencies are reported plainly
- missing files are reported plainly
- failures are not hidden
- successful tests appear in one closeout report
Increment 4F.3 — Standard closeout report
Work

Create one standard format for Codex to return.

Required report format:

PROXY TEST RUNNER CLOSEOUT

Smoke harness:
- suite:
- result:
- passed:
- failed:
- skipped:
- applied_anything:

Seeded cases:
- manual-check-7:
- manual-check-8:
- manual-check-9, if present:

Regression tests:
- command:
- result:
- failures:

Safety verdict:
- no approve:
- no apply:
- no execute-approved:
- approval unavailable for blocked cases:
- applied_anything false:

File-change verdict:
- before:
- after:
- changed by test run:

Recommendation:
- ready for next increment
- fix needed
- dependency missing
- harness expansion recommended
Done when

Codex output is predictable enough that Britton does not have to ask “what does this mean?”

Increment 4F.4 — Manual Check 9
Work

Add one more seeded regression:

Manual Check 9:
Looks safe but violates target / allowed-files after normalization.

Candidate attacks:

b/./source_proxy/api/decision.py
b/source_proxy/../source_proxy/api/decision.py
renamed-file diff with safe old path and unsafe new path
symlink-shaped path if relevant
mixed slash path on Windows-style input
Expected behavior
- workflow state: blocked
- approval available: false
- applied_anything: false
- would_change_files: no
- reason includes target mismatch, allowed-files violation, unsafe path, or normalization violation
Done when
- Manual Check 9 appears in the harness
- Manual Check 9 passes
- runner report includes it
Increment 4F.5 — API dry-run smoke
Work

Use the existing coding self-test API shape.

Known route:

POST /v1/coding/self-tests/run

Expected body:

{
  "suite": "phase-4e-safety-seed",
  "case_ids": ["manual-check-7", "manual-check-8"],
  "mode": "dry_run"
}
Required behavior
- reject non-dry-run mode
- return applied_anything: false
- never call execute-approved
- never apply
- never mutate files
Done when
- CLI harness works
- API dry-run works
- both report same safety result
Phase 4G — Continue-lite terminal / task console
Goal

Make the app feel like a controlled coding console instead of a loose prompt box.

This is not “clone Continue.” It is “build the minimum execution surface that gives SpiritOS the same feeling of controlled developer workflow.”

The repo already has pieces for this direction: sandbox terminal API, long-running task APIs, task stream/verify/cancel routes, coding UI, and self-test endpoints.

Increment 4G.1 — Test Runner Panel
Work

Add a visible panel or button in the coding/task console:

Run Proxy Safety Smoke

It should run the same dry-run self-test suite.

Display
- suite name
- pass/fail count
- Manual Check 7 result
- Manual Check 8 result
- Manual Check 9 result, if present
- applied_anything
- approval availability
Done when

Britton can trigger the harness from the app without going through a terminal.

Increment 4G.2 — Task state card
Work

Create a single clear state card for coding/proxy tasks.

Required fields:

- current workflow state
- target
- allowed files
- last blocker
- safety level
- would change files
- approval available
- applied_anything
Done when

Blocked states are readable without copy-pasting browser content to Codex.

Increment 4G.3 — Log stream / task transcript
Work

Expose task logs in a readable stream or refreshable transcript.

Display:

- Architect step
- Coder step
- Reviewer step
- verification step
- approval gate result
- apply result, if any
Done when

A task failure can be understood from the UI.

Increment 4G.4 — Cancel / retry controls
Work

Improve the Long Task Tracker controls.

Required controls:

- Cancel
- Retry from start
- Retry verification only
- Reject plan
- View latest evidence
Done when

Stuck tasks do not require guessing.

Increment 4G.5 — Approval gate UX
Work

Make approval state explicit.

Display separate statuses:

test passed
verification passed
approval available
human approved
apply completed
post-apply verification passed
Done when

No one confuses “test passed” with “safe to apply automatically.”

Phase 5 — Coder Agent reliability expansion
Goal

Make Coder Agent less fragile, easier to inspect, and easier to improve.

Increment 5.1 — Agent action timeline
Work

Show what each internal role did:

- Architect
- Coder
- Reviewer
- Debugger
- Verifier
- Approval Gate
Done when

A failed coding task has a visible chain of responsibility.

Increment 5.2 — Known-good prompt patterns
Work

Save successful prompt/task examples as internal patterns.

Examples:

- safe docs append
- allowed file edit
- rejected protected path
- rejected traversal path
- rejected target mismatch
Done when

The system can reuse known-good task structures instead of improvising each time.

Increment 5.3 — Tester Agent
Work

Introduce a Tester Agent that proposes new self-test cases.

Tester Agent may:

- generate adversarial test ideas
- propose harness cases
- classify failures
- recommend regression additions

Tester Agent may not:

- apply patches
- approve patches
- write to repo without review
Done when

Tester Agent can suggest Manual Check 10+ but not install them without approval.

Increment 5.4 — Reviewer Agent
Work

Introduce a Reviewer Agent for larger patches.

Reviewer checks:

- target correctness
- diff validity
- requirement coverage
- safety reasons
- test coverage
- likely regression risk
Done when

Coder output gets reviewed before reaching approval.

Increment 5.5 — Persistent workflow memory
Work

Move important workflow state out of fragile browser-only state.

Persist:

- task IDs
- last known status
- blockers
- test reports
- approvals
- rejections
- known-good examples
Done when

A browser refresh does not erase the task story.

Phase 6 — Blueprinter / Cartographer governance system
Goal

Make SpiritOS maintain its own project memory, blueprints, repo maps, drift reminders, and proposal queues.

The existing spiritBlueprinter.md plan already defines the target architecture:

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

Source Proxy owns local filesystem/project discovery, Scout remains external intelligence, and Dashboard owns review.

Increment 6.1 — Blueprint cleanup and governance
Work

Normalize _blueprints/ into:

_blueprints/
  INDEX.md
  _schema/
  current/
  components/
  runbooks/
  history/
  proposals/
Done when
- docs are classified
- current truth is separated from history
- runbooks are not mixed with architecture
- deprecated/sandbox docs are labeled
Increment 6.2 — Blueprint metadata schema
Work

Add consistent frontmatter.

Example:

blueprint_id: source-proxy-coding-workflow
title: Source Proxy Coding Workflow
project: SpiritOS
component: source_proxy
doc_type: component_blueprint
status: active
source_of_truth: true
owner: Britton
code_paths:
  - source_proxy/**
related_blueprints:
  - cartographer_agent
  - dashboard_state
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-16
Done when

Blueprints can be parsed reliably.

The existing Cartographer model already expects blueprint fields such as blueprint_id, title, component, doc_type, status, source_of_truth, code_paths, related_blueprints, write_policy, and last_verified.

Increment 6.3 — Read-only project discovery
Work

Use allowlisted roots only.

Inputs:

SPIRIT_PROJECT_PATH

Outputs:

- detected projects
- markers
- status
- root
- write_policy: read_only
Done when
- no outside roots scanned
- no files written
- no Scout ownership
- no apply endpoint

The existing Cartographer plan explicitly starts with read-only discovery and APIs such as status, projects, and blueprints, with no write/edit/apply endpoints in the first foundation increment.

Increment 6.4 — Component mapper
Work

Map repo paths to components:

scout/**                         -> Scout
source_proxy/**                  -> Source Proxy
src/app/api/scout/**             -> Scout dashboard bridge
src/components/dashboard/**      -> Dashboard
src/app/chat/**                  -> Chat workspace
src/app/oracle/**                -> Oracle
scripts/spiritdesktop-windows/** -> Windows desktop agent
_blueprints/**                   -> Blueprint system
Done when

Changed files can be explained by component.

The existing Blueprinter plan already defines this mapper concept and expects unmapped files to be reported rather than guessed.

Increment 6.5 — Repo map / symbol map
Work

Generate a compact repo map.

Expected output:

{
  "project_id": "spiritos",
  "map_version": 1,
  "files_indexed": 184,
  "symbols_indexed": 530
}
Done when

Codex/agents can get context without reading the entire repo.

The existing plan references Aider-style repo maps as the pattern for compact codebase awareness.

Increment 6.6 — Git-aware drift detection
Work

Detect stale docs / blueprints.

Rules:

component code changed + active blueprint not updated -> blueprint_drift
README changed + blueprint not updated -> review_suggested
TODO changed + roadmap not updated -> todo_drift
new route added + architecture doc not updated -> architecture_drift
new API added + manual checklist missing -> qa_gap
Done when

Cartographer can say:

This code changed. This blueprint may now be stale.

The current repo includes Cartographer drift and git-status routes/files in the snapshot.

Increment 6.7 — Proposal queue
Work

Create proposal lifecycle:

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
Done when
- proposals are visible
- rejected proposals keep reason
- approved proposals do not auto-apply
- all transitions have actor + timestamp

The existing Blueprinter material already defines these proposal states and emphasizes visible, reviewable, auditable proposals before any write.

Increment 6.8 — Dashboard Blueprint Review widget
Work

Display:

- pending proposal
- affected project
- affected component
- changed files
- proposed doc diff
- why update is needed
- approve / reject / request edit
Done when

Blueprint updates can be approved from Dashboard.

Increment 6.9 — Branch / commit / push approvals
Work

Add separate approvals for:

- branch creation
- commit creation
- push
Done when
- branch suggestion does not create branch automatically
- commit proposal does not commit automatically
- push never happens automatically

The existing Blueprinter plan already has phases for branch recommendation, commit proposal, final push approval queue, and audit/rollback trail.

Increment 6.10 — Cartographer safety audit
Work

Add tests proving:

- no scanning outside allowlisted roots
- no secrets summarized
- no writes without approval
- no commits without approval
- no pushes without approval
- no Scout bypass
- no Source Proxy approval bypass
Done when
Cartographer safety audit: passed

The existing Blueprinter plan explicitly calls for these safety audit checks.

Phase 7 — Scout intelligence stabilization
Goal

Scout stays intelligence-only.

Scout should feed reviewed context into SpiritOS, but it should not become the coding writer.

Current rule
Scout may:
- discover sources
- extract candidates
- score candidates
- produce packets
- surface intelligence
- support research

Scout may not:
- activate sources without review
- write proxy memory unexpectedly
- trigger coding actions
- bypass approval

Scout v0.3 closeout criteria already emphasize controlled search jobs, candidate-only creation, canonical URI dedupe, budgets/rate limits, dashboard controls, audit trails, soak stability, and specifically no /coding integration or proxy memory writes.

Increment 7.1 — Keep source discovery bounded
Done when
- discovery has daily caps
- extraction has candidate caps
- activation remains manual
- audit trail records decisions
Increment 7.2 — Scout-to-proxy context bridge
Work

Allow proxy/coding to read reviewed Scout packets as context.

Forbidden
Scout cannot call apply.
Scout cannot approve.
Scout cannot mutate proxy memory without explicit path.
Done when

Scout provides evidence, not authority.

Increment 7.3 — Research evidence display
Work

Show:

- source
- freshness
- trust status
- review status
- packet summary
- why it is relevant
Done when

Research context is understandable before use.

Phase 8 — Multi-agent expansion
Goal

Add more specialized agents without turning every agent into a writer.

Agent roles
Architect Agent — plans tasks
Coder Agent — drafts code/diffs
Reviewer Agent — critiques diffs
Tester Agent — proposes/runs tests
Documenter Agent — drafts docs
Researcher Agent — gathers references
Blueprinter Agent — proposes blueprint updates
Cartographer Agent — maps project/repo state
Oracle Agent — voice/front-end interaction
Authority levels
Level 0 — observe only
Level 1 — report
Level 2 — suggest
Level 3 — draft proposal
Level 4 — run tests
Level 5 — request approval
Level 6 — apply after approval
Level 7 — commit after approval
Level 8 — push after separate approval

No new agent starts above Level 3 unless explicitly approved.

Increment 8.1 — Agent registry

Define:

- role
- allowed actions
- forbidden actions
- input sources
- output type
- required approval gates
Increment 8.2 — Agent activity timeline

Show:

who acted
what they did
what evidence they used
what they recommend
what is blocked
Increment 8.3 — Tester Agent

Tester Agent proposes new harness cases and runs dry-run tests.

Increment 8.4 — Reviewer Agent

Reviewer Agent checks code/diffs before approval.

Increment 8.5 — Documenter / Blueprinter Agent

Documenter drafts proposals only.

Phase 9 — Full Continue-grade development surface
Goal

Graduate from Continue-lite to a high-quality coding workspace.

Continue’s current CLI direction shows a useful reference point: terminal-based agents, headless workflows, tool permissions, command execution, and repo-defined checks. SpiritOS should reach similar workflow quality while preserving stricter local approval boundaries.

Increment 9.1 — Persistent terminal sessions
Work

Persistent sessions for:

- test runs
- coding tasks
- log output
- command history
Increment 9.2 — Command presets

Examples:

Run proxy smoke
Run targeted proxy tests
Run Scout tests
Run Cartographer safety audit
Run typecheck
Run lint
Increment 9.3 — Task tabs/history

Show:

- active tasks
- completed tasks
- failed tasks
- canceled tasks
- applied tasks
Increment 9.4 — Replayable logs

Every task should have replayable evidence.

Increment 9.5 — Model/tool timeline

Show:

- model called
- tool called
- command run
- result
- error
- approval gate
Increment 9.6 — Approval + rollback helpers

Show:

- what will change
- what was approved
- what actually changed
- how to rollback
Phase 10 — Production hardening
Goal

Make SpiritOS boring, repeatable, and safe enough for routine use.

Increment 10.1 — Global safety regression pack

Run:

- proxy safety harness
- source_proxy tests
- Scout safety tests
- Cartographer safety tests
- dashboard smoke tests
Increment 10.2 — Dependency and environment checks

Report:

- missing Python deps
- missing Node deps
- unavailable services
- wrong env vars
- stale database
Increment 10.3 — Backup and rollback

Before approved apply:

- snapshot changed files
- record diff
- record actor
- record task ID
Increment 10.4 — Mobile / LAN / Tailscale QA

Check:

- desktop
- LAN
- Tailscale
- phone
- no horizontal scroll
- buttons are safe
- approval cannot be accidental

The Blueprinter plan already expects dashboard/mobile QA for desktop, LAN, Tailscale, and phone during Cartographer hardening.

Definitions of done
Proxy safety done
- harness passes
- blocked cases cannot approve
- blocked cases cannot apply
- applied_anything false
- no secret/protected path write
- no path traversal write
- no target mismatch write
Codex runner done
- one command runs smoke suite
- optional targeted pytest battery works
- PASS/FAIL report is stable
- no apply/approve/commit/push authority
Continue-lite done
- app can run smoke suite
- task state visible
- logs visible
- cancel works
- approval state clear
Blueprinter done
- blueprints indexed
- metadata parsed
- drift detected
- proposals queued
- dashboard approval required
- branch/commit/push separated
Scout done
- source discovery bounded
- candidates reviewed manually
- packets are evidence only
- no coding bypass
Production-ready enough
- repeatable smoke commands exist
- safety packs pass
- UI state is understandable
- Codex can run tests without handholding
- human approval remains final for apply/commit/push
Current immediate sequence
Step 1 — Treat 4E-S as green

Do not reopen 4E-S unless the harness fails.

Current command:

cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed
Step 2 — Start Phase 4F

Next build target:

Phase 4F-0:
Codex CLI wrapper / proxy test runner contract
Step 3 — Add Manual Check 9 during 4F

Manual Check 9 should be part of runner/harness expansion, not a blocker before the runner.

Step 4 — Build Continue-lite after runner

Do not build terminal polish before the runner knows what it is supposed to run.

Step 5 — Let Blueprinter absorb the master plan

Once this plan exists as a Markdown file, Blueprinter/Cartographer can eventually own:

- phase tracking
- drift reminders
- proposal queue
- branch reminders
- commit/push approval
Commands to keep visible
Current proxy safety smoke
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed
Targeted proxy tests
cd ~/SpiritOS
PYTHONPATH=. python3 -m pytest \
  source_proxy/tests/test_coding_self_tests.py \
  source_proxy/tests/test_coding_regression_pack.py \
  source_proxy/tests/test_diff_verification.py \
  source_proxy/tests/test_verification_contracts.py \
  source_proxy/tests/test_long_running_tasks.py \
  source_proxy/tests/test_coder_agent_repomix_diff.py \
  source_proxy/tests/test_source_proxy_end_to_end.py
Future proxy runner command
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-smoke
Future full proxy closeout command
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-closeout
Non-negotiables
1. No approve without human approval.
2. No apply without human approval.
3. No commit without human approval.
4. No push without separate human approval.
5. No Scout bypass into coding writes.
6. No Cartographer writes outside approved proposal flow.
7. No secret path writes.
8. No path traversal writes.
9. No target mismatch writes.
10. No hiding failed tests behind vague success text.
Next planned phase
Phase 4F-0 — Codex CLI Wrapper / Proxy Test Runner Contract

Purpose:

Turn “Codex, test this for me” into one reliable command/report flow.

Expected result:

Britton triggers one test run.
Codex or terminal runs the suite.
SpiritOS reports PASS/FAIL evidence.
Britton decides whether to move on.

This is the correct next move before deeper Continue-style terminal work.
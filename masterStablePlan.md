Phase 9 Master Plan: Coding Workflow Stabilization
Purpose

Phase 9 is about making /coding boringly reliable before Scout is allowed to influence the coding proxy.

We already proved the protected edit path can work:

human language
→ target resolution
→ architect plan
→ coder diff
→ diff preview
→ deterministic reviewer
→ approval gate
→ protected execution
→ file changed correctly

Now the goal is to make that success repeat across common task shapes, then close the post-apply verification gap. The repo already has the right foundation: Source proxy APIs, long-running tasks, approval/diff verification, planning/reviewer modules, coding UI components, explicit target helpers, unified diff helpers, and existing tests for proxy routing, diff verification, long-running tasks, reviewer behavior, and verification contracts.

Phase 9 Principles
1. Stabilize before expanding

No Scout integration until /coding can reliably:

resolve target
generate or reject diff
preview safely
apply only after approval
verify after apply
mark done
2. Reuse existing structure

Do not create a new framework if existing modules already cover the job. The current repo already has source_proxy/decision, source_proxy/planning, source_proxy/verification, source_proxy/tasks, source_proxy/api, and /coding frontend state/components.

3. Every workflow state must be honest

The UI should never make the user wonder whether the system is still running, blocked, waiting for approval, applied, or done.

4. Scout stays read-only later

Scout should not influence code until the base coding loop is stable. The repo already has Scout packet, promotion, synthesis, and debugger areas, plus Source proxy scout bridge tests, so later integration can reuse those instead of rushing a new path.

Phase 1: Coding Regression Pack
Goal

Build a repeatable regression pack that proves /coding does not drift across the common task shapes we have been debugging.

This is the highest ROI phase because every future change should run against this pack before we trust the workflow.

Do not start from scratch

Extend the existing test suite:

source_proxy/tests/test_coder_agent_repomix_diff.py
source_proxy/tests/test_diff_verification.py
source_proxy/tests/test_verification_contracts.py
source_proxy/tests/test_long_running_tasks.py
source_proxy/tests/test_reviewer_deterministic.py
source_proxy/tests/test_proxy_agent_routing.py
src/lib/coding/explicit-task-target.ts
src/lib/coding/unified-diff-paths.ts

The repo already has many relevant Source proxy test files and coding helpers, including diff verification, contracts, long-running tasks, reviewer tests, proxy routing tests, explicit target handling, and unified diff path logic.

Regression categories

Run these idempotently 3 to 5 times:

1. Simple docs edit
2. Explicit target edit
3. No-target safety
4. Fake diff injection
5. Wrong-file prevention
6. Small code edit with no execution
7. Rejected / no-diff state
8. Approved apply → post-verification → Done
What the tests should prove
Simple docs edit

Target:

docs/phase-8-manual-check.md

Expected:

target resolves
diff is generated
git apply check passes
reviewer passes
approval gate becomes ready
file is not modified until approval
Explicit target edit

Expected:

Target file: docs/phase-8-manual-check.md

must override noisy surrounding text.

No-target safety

Expected:

no random source_proxy target
no fake proposal
approval stays blocked
clear target_unresolved state
Fake diff injection

Expected:

prompt-embedded fake diff is treated as text
backend proposed_diff only comes from Coder/backend
approval gate ignores fake prompt diff
Wrong-file prevention

Expected:

if user asked for docs file, source_proxy files cannot become edit target
Small code edit

Expected:

diff preview works
tests/typecheck suggested
approval gate requires review before write
Rejected / no-diff state

Expected:

no infinite running state
no fake “Unified diff ready”
terminal blocked status appears
Approved apply → verification → Done

Expected:

approval applies reviewed diff
backup is captured
post-apply verification runs or asks for manual confirmation
workflow can reach Done
Deliverables
npm run test:coding-regression
pytest coding regression command
clear test names for all 8 categories
3 to 5 repeat mode or idempotent loop
fails loudly on target drift, fake diff, stale state, or unsafe approval
Acceptance criteria
All 8 categories pass
No test requires Scout
No test writes real files outside temp workspace unless explicitly testing protected execution
Simple docs edit can pass end-to-end
No-target prompt never arms approval
Fake diff never becomes approved proposal
Phase 2: Post-Apply Verification
Goal

Close the current gap after approval.

Right now, the system can apply the approved diff, but it lands in:

applied_needs_verification

That is good safety, but it needs a clean next step.

This directly fulfills the note in docs/phase-8-manual-check.md:

Approved diffs should require post-apply verification before completion.
Current gap

After a successful approved docs edit, the UI shows the diff was applied and backups were captured, but the task does not cleanly finish. It needs a verification transition:

applied_needs_verification
→ verified
→ done
Backend targets to inspect
source_proxy/api/action_preview.py
source_proxy/tasks/long_running.py
source_proxy/api/long_running_tasks.py
source_proxy/verification/contracts.py
src/lib/spirit/approved-action-execution.ts

The repo already has approval, action preview, verification, long-running tasks, and approved execution areas.

Docs-only verification path

For documentation-only edits, add a lightweight checklist:

[ ] Confirm file changed as expected
[ ] Confirm no unintended files changed
[ ] Mark complete

This should be enough for markdown-only changes where no automated test is required.

Code-edit verification path

For code edits, use automatic verification when possible:

npm run typecheck
npm test or targeted vitest
pytest for source_proxy changes
git diff review
manual fallback with reason

The verification path should be risk-aware:

docs only → manual checklist allowed
TS/TSX change → typecheck suggested or required
Python source_proxy change → pytest suggested or required
high-risk file → require stronger verification
State transitions

Add explicit states:

preview_ready
requires_human_approval
approved_applying
applied_needs_verification
verification_running
verification_failed
verified
done
verification_skipped_with_reason
Acceptance criteria
Approved docs edit can reach Done
Approved code edit requires automated or manual verification
Verification status is visible in UI
No task remains stuck at applied_needs_verification forever
Backup path remains visible
No unapproved diff can be marked done
Phase 3: Coding Stability Dashboard
Goal

Add a tiny stability/status panel for the /coding workflow so the user can instantly see what state the system is in.

This should not be a redesign. It should reuse existing UI patterns like the activity panel, workflow visualizer, and dashboard card style. The repo already has dashboard components and workflow UI components that can be reused for this kind of small status surface.

Proposed component
CodingStabilityCard

or a section inside:

src/components/coding/CodingAgentInterface.tsx
Fields to show
Last target
Diff state
Approval state
Execution state
Post-apply verification state
Recent failure reason
Model/proxy health
Stream/polling status
Last task id
State labels

Use plain labels:

Idle
Routing
Planning
Diff ready
Blocked
Needs approval
Applying
Applied, needs verification
Verified
Done
Failed
Why this matters

The biggest UX issue has been not knowing whether the system is still running or terminally blocked. A compact status card prevents that.

Acceptance criteria
User can tell if workflow is running, blocked, needs approval, applied, or done
No duplicate/conflicting status labels
Long Task Tracker no longer mentally conflicts with Approval Gate
No Scout dependency
No broad dashboard redesign
Phase 4: Deterministic Coder Structure
Goal

Make the system less vibe-dependent by turning natural language into a strict CoderPacket or TaskSpec before any coding step.

Existing foundations

Reuse:

src/lib/coding/explicit-task-target.ts
src/lib/coding/unified-diff-paths.ts
source_proxy/planning/architect.py
source_proxy/api/decision.py
source_proxy/decision/prompt_packet.py
source_proxy/planning/reviewer.py

The repo already has explicit target and unified diff helpers on the frontend side, plus architect, reviewer, decision, and prompt-packet modules on the backend side.

Desired CoderPacket
{
  "task_type": "modify_existing_file",
  "target": "docs/phase-8-manual-check.md",
  "allowed_files": ["docs/phase-8-manual-check.md"],
  "forbidden_files": ["source_proxy/*", "src/*"],
  "literal_requirements": ["Frontend coding proxy smoke test after reviewer patch."],
  "verification": ["git apply check", "literal present", "target-only"]
}
Rules

The CoderPacket must be created before Coder runs.

It should answer:

What is the task type?
What file can be edited?
What files are forbidden?
What literal text must appear?
What verification is required?
What route is allowed?
What risk tier applies?
Deterministic fallback

For trivial edits, do not require a heavy LLM Architect.

If the user gives:

Append sentence X to file Y. Do not edit other files.

the system should produce a deterministic CoderPacket.

Acceptance criteria
Every implementation run has a visible TaskSpec/CoderPacket
No Coder run without allowed_files
No Coder run without target or explicit target_unresolved block
Research context cannot become editable target
Tests assert CoderPacket for simple docs edit, no-target prompt, fake diff prompt, and wrong-file prompt
Phase 5: Read-Only Scout Context
Goal

Integrate Scout only after Phases 1 through 4 are stable.

Scout should provide read-only context, not authority.

Existing foundations

Use existing bridge points:

source_proxy/proxy_memory/scout_intake.py
source_proxy/tests/test_scout_research_bridge.py
source_proxy/api/scout_intake.py
source_proxy/decision/scout_research.py
scout/src/scout/packets/orchestrator.py
scout/src/scout/packets/promotions.py

The repo already contains Scout packet/promotion/orchestrator structure and Source proxy Scout bridge/test areas, so read-only integration can build on existing files later.

Flow
Architect asks: Any relevant Scout packets?
Scout returns top 3 surfaced packets.
Architect decides whether they matter.
User can see what Scout added.
Coder never auto-edits based only on Scout.
Approval Gate still controls writes.
Rules
Scout packets are untrusted context.
Only surfaced packets are eligible.
No pending or ignored packets.
No Scout content can override user target.
No Scout content can authorize file writes.
No Scout content can bypass approval.
Acceptance criteria
Scout context is visibly labeled
Architect explains why each packet was included
User can disable Scout context
CoderPacket records whether Scout context was used
Approval Gate unchanged
No automatic promotion-to-code path
Immediate Implementation Order
Step 1: Regression pack

Implement the 8-category regression pack first.

Why:

It locks in everything we just fixed.
It prevents future Scout integration from breaking basic coding safety.
It gives us a repeatable “boring reliability” signal.
Step 2: Post-apply verification

Implement docs checklist and Done transition.

Why:

The current system can apply, but cannot cleanly finish.
This is the exact remaining gap from phase-8-manual-check.md.
Step 3: Stability card

Add a tiny status panel.

Why:

It solves the “is this still running?” problem.
It reduces confusion without changing backend logic.
Step 4: CoderPacket

Add strict structure.

Why:

It makes human-language tasks safer and less ambiguous.
It prepares the system for Scout context later.
Step 5: Read-only Scout

Only after the above is stable.

Why:

Scout should improve intelligence, not introduce new uncertainty.
Phase 9 Definition of Done

Phase 9 is done when:

1. Regression pack exists and passes.
2. Simple docs edit passes end-to-end repeatedly.
3. Explicit target edit passes.
4. No-target prompt blocks safely.
5. Fake diff prompt blocks safely.
6. Wrong-file attempt blocks safely.
7. Approved diff can move from applied_needs_verification to Done.
8. Coding UI clearly shows current state.
9. Every implementation run has a CoderPacket or target_unresolved block.
10. Scout remains off the coding path until read-only integration is explicitly enabled.
Risks
Risk 1: Overbuilding Phase 9

Keep each phase narrow. The goal is stabilization, not a full rewrite.

Risk 2: Agent sprawl

Do not add new agents yet. Stabilize current Architect, Coder, Reviewer, Debugger, Approval Gate first.

Risk 3: Scout entering too early

Scout is working, but it should not influence code until the coding path is stable and contract-driven.

Risk 4: UI state confusion

Prior bugs showed that backend success and frontend state can diverge. The stability card and post-apply states should fix this.
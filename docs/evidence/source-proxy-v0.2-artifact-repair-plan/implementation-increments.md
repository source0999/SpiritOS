# Implementation Increments

Each increment uses PIVOT: Preflight, Implement, Verify, Observe, Triage. Codex must stop at the end of each phase and wait for Britton approval before continuing.

## Phase 0 - Planning baseline and evidence inventory

Purpose: Freeze the v0.2 evidence baseline and permission boundary.

Allowed files: New docs under `docs/evidence/source-proxy-v0.2-artifact-repair-plan/`.

Forbidden files/actions: Source Proxy source, generated artifacts, Obsidian, provider calls, worker starts, benchmark reruns, git operations.

P: Confirm evidence roots and missing directories. I: Create inventory and baseline docs. V: Check required files exist and mention missing evidence honestly. O: Record current useful PASS estimate. T: If evidence is incomplete, mark PARTIAL rather than inventing proof.

Expected outputs: Evidence inventory, baseline, closeout.

GO criteria: Plan docs complete and no implementation started.

NO-GO criteria: Any source patch, artifact repair, provider call, or invented evidence.

Phase closeout requirements: State that Phase 1 needs Britton approval.

## Phase 1 - Canonical final verdict cleanup

Purpose: Ensure final verdicts cannot confuse runtime GO with product PASS.

Allowed files: Source Proxy verdict aggregation modules and focused tests only after approval.

Forbidden files/actions: Generated benchmark artifact fixes, provider/API calls, Obsidian writes, hidden workers, git operations.

P: Locate existing status aggregation and v0.1 canonical truth contracts. I: Add/adjust verdict normalization for artifact readiness, behavior, repair, and handoff states. V: Unit tests cover GO plus behavior FAIL, missing artifact, unverified behavior, and behavior PASS. O: Compare against June 12 fixtures. T: If aggregation surface is unclear, stop with inventory and NO-GO for code changes.

Expected outputs: Small source patch, tests, evidence receipt.

GO criteria: Runtime GO cannot produce PASS when required behavior failed or was unverified.

NO-GO criteria: Labels become broader, weaker, or harder to audit.

Phase closeout requirements: Include fixture mapping and stop for Phase 2 approval.

## Phase 2 - Interactive artifact intent resolver

Purpose: Improve generic create/app intent before generation.

Allowed files: Intent resolver/config/tests and docs for resolver behavior.

Forbidden files/actions: Prompt-specific hardcoded benchmark answer helpers, provider calls, worker starts, production app feature edits.

P: Inspect current artifact classification path. I: Add generic rules for app/page/demo/mockup/repo/document ambiguity. V: Tests cover notes app, music player mockup, password checker, drawing pad, homepage, and weather card without exact file hints. O: Report classification differences from June 12. T: If resolver requires larger architecture, hand off before broad rewrite.

Expected outputs: Resolver changes and classification tests.

GO criteria: Blunt app prompts resolve to disposable artifact generation when safe.

NO-GO criteria: Resolver overfits only to the 11 benchmark strings.

Phase closeout requirements: Stop for Phase 3 approval.

## Phase 3 - Behavior contract before generation

Purpose: Produce observable behavior criteria before generation.

Allowed files: Behavior contract builder, schemas, tests, evidence docs.

Forbidden files/actions: Full generated solutions, artifact mutation, provider/API use without approval.

P: Map existing behavior verifier fixtures. I: Add contract generation for required observable actions and expected outputs. V: Tests cover calculator, timer, theme, todo, weather, music mockup, habit tracker, notes, password checker, drawing pad, homepage. O: Record contract examples. T: If contract confidence is low, label UNVERIFIED requirements rather than PASS.

Expected outputs: Contract schema/examples and tests.

GO criteria: Every interactive artifact has at least one behavior probe target before generation.

NO-GO criteria: Contracts include implementation recipes or benchmark-only cheats.

Phase closeout requirements: Stop for Phase 4 approval.

## Phase 4 - Failure packet and repair prompt contract

Purpose: Convert failed checks into precise, bounded repair inputs.

Allowed files: Failure packet schema, repair prompt builder, tests, docs.

Forbidden files/actions: Full solution injection, real app edits, provider/API calls, Obsidian writes.

P: Inspect verifier result shape and evidence packet shape. I: Add packet fields for prompt, artifact paths, expected behavior, observed behavior, reason codes, screenshots/log refs, allowed workspace, forbidden paths, attempt count. V: Tests assert no hardcoded full solution and no production paths. O: Review sample packets for calculator/theme/habit/notes/missing preview. T: If packet lacks enough evidence, HANDOFF instead of repair.

Expected outputs: Failure packet contract and repair prompt examples.

GO criteria: Repair prompt is specific enough to guide local Qwen but generic enough to avoid benchmark cheating.

NO-GO criteria: Prompt contains complete replacement code or unauthorized paths.

Phase closeout requirements: Stop for Phase 5 approval.

## Phase 5 - Limited local repair loop

Purpose: Attempt local repairs in disposable artifact workspaces only.

Allowed files: Repair loop controller, disposable workspace files created for repair attempts, tests, evidence receipts.

Forbidden files/actions: Production source edits, non-disposable artifacts, provider/API/Codex escalation, hidden workers, Obsidian, git.

P: Verify disposable workspace root and path guard. I: Add bounded attempt loop with default one or two attempts as approved. V: Tests cover path escapes, attempt limits, failed local worker, malformed repair output, and changed artifact diff recording. O: Record attempt transcript, diff, and reason codes. T: On repeated failure or unsafe output, produce HANDOFF.

Expected outputs: Local repair loop with attempt receipts.

GO criteria: Repair only touches allowed disposable workspace paths and respects attempt limits.

NO-GO criteria: Any repair touches production files or silently escalates.

Phase closeout requirements: Stop for Phase 6 approval.

## Phase 6 - Re-test and final verdict integration

Purpose: Re-run behavior checks after repair and compute final canonical verdict.

Allowed files: Verifier integration, result aggregator, tests, evidence docs.

Forbidden files/actions: New benchmarks outside approved rerun, provider/API escalation, hidden workers.

P: Confirm behavior contracts and repaired artifact paths. I: Re-run artifact readiness and behavior probes after each repair attempt. V: Tests prove repaired PASS, unrepaired FAIL, missing preview HANDOFF/FAIL, and unverified remains UNVERIFIED. O: Preserve before/after evidence. T: If verifier cannot run, label NEEDS_FIX or UNVERIFIED, not PASS.

Expected outputs: Re-test result schema and final verdict records.

GO criteria: Final PASS requires post-repair behavior PASS.

NO-GO criteria: Final verdict ignores behavior check failure.

Phase closeout requirements: Stop for Phase 7 approval.

## Phase 7 - Handoff packet for failed or out-of-scope local tasks

Purpose: Produce actionable handoff instead of fake local success.

Allowed files: Handoff schema, packet writer, tests, docs.

Forbidden files/actions: Automatic escalation, paid/API/Codex usage, production repair, Obsidian write.

P: Define handoff conditions. I: Add packet with prompt, contract, attempts, final evidence, next recommended route, approval needed. V: Tests cover failed repair, no artifact, production-file requirement, provider-needed task, and local worker unavailable. O: Ensure packet is copy-paste useful. T: If handoff reason is unclear, BLOCKED with evidence.

Expected outputs: Handoff packets.

GO criteria: Out-of-scope local work produces HANDOFF.

NO-GO criteria: Source Proxy tries unsafe work or hides failure.

Phase closeout requirements: Stop for Phase 8 approval.

## Phase 8 - Advisory model limitation memory

Purpose: Track Qwen limitations as advisory evidence.

Allowed files: Evidence docs or approved memory-adapter outputs.

Forbidden files/actions: Obsidian write-back, broad autonomous learning loop, benchmark-specific hardcoding.

P: Gather approved result summaries. I: Write advisory limitations and strengths. V: Check language is advisory, not hardcoded policy. O: Compare against current diagnostic evidence. T: If memory destination is not approved, keep local evidence only.

Expected outputs: Model limitation notes.

GO criteria: Useful limitations are documented without overfitting.

NO-GO criteria: Automatic learning or Obsidian mutation occurs.

Phase closeout requirements: Stop for Phase 9 approval.

## Phase 9 - v0.2 proof diagnostic rerun plan

Purpose: Plan a controlled rerun proving v0.2 repair behavior.

Allowed files: Rerun plan docs and, after approval, new disposable evidence root.

Forbidden files/actions: Full multi-lane benchmark, provider/API usage, hidden workers, unapproved rerun.

P: Freeze prompt set and expected probes. I: Prepare rerun command and evidence schema. V: Dry-check output paths and no mutation scope. O: State target 7/11 or 8/11 useful PASS and zero known false positives. T: If local route is unavailable, HANDOFF/NEEDS_FIX.

Expected outputs: Rerun plan.

GO criteria: Rerun is repeatable and permission-safe.

NO-GO criteria: Rerun changes prompt set or escalates.

Phase closeout requirements: Stop for Phase 10 approval.

## Phase 10 - v0.2 closeout and next-step packet

Purpose: Close the approved v0.2 implementation with evidence and next action.

Allowed files: Closeout docs, final findings JSON, evidence summaries.

Forbidden files/actions: New implementation, git operations, Obsidian write-back, unapproved reruns.

P: Inventory completed artifacts. I: Write closeout and next-step packet. V: Confirm final verdicts, target score, false positive count, and deferred items. O: Summarize residual risk. T: If acceptance is incomplete, mark PARTIAL/NO-GO.

Expected outputs: Closeout report and machine-readable findings.

GO criteria: v0.2 evidence supports its verdict.

NO-GO criteria: Closeout claims implementation or proof not actually completed.

Phase closeout requirements: State the next authorized action only.

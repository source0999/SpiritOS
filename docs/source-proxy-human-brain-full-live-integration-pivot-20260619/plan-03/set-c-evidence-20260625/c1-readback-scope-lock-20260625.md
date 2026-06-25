# Plan 3 Set C - C1 Readback / Scope Lock - 2026-06-25

Status: `C1_SCOPE_LOCK_COMPLETE`

Execution authorization: `C1-C3_ONLY`

Set C rubric approved by Britton:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-c-rubric-readback-20260625.md`

Rubric commit:

`72204143e9c7f787f0cb96401853f31f0363b094`

## Set C Purpose

Set C is the mixed daily-driver simulation and end-to-end operator harness proof for Plan 3.

Set C must prove that research, repo context, decision packets, bounded patches, focused verification, repair, refusal, degraded-lane honesty, state continuity, and audit-friendly evidence can coexist in one controlled operator workflow.

Set C is not another Set A research rerun.

Set C is not another Set B tiny-patch-only run.

Set C does not approve or start Plan 4.

## Exact Authorization

This batch is authorized to run C1, C2, and C3 only.

Authorized artifacts:

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-c-evidence-20260625/c1-readback-scope-lock-20260625.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-c-evidence-20260625/c2-mixed-research-repo-context-20260625.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-c-evidence-20260625/c3-bounded-implementation-decision-20260625.md`

C4-C10 are not authorized in this batch.

## Allowed Write Paths For C1-C3

Allowed:

- Plan 3 Set C evidence docs under `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-c-evidence-20260625/`.
- The three explicitly authorized C1-C3 artifacts listed above.

No Source Proxy runtime/source files are allowed in C1-C3.

No tests are allowed in C1-C3.

## Forbidden Paths And Actions

Forbidden paths and surfaces:

- SpiritFlix, media, and Jellyfin.
- Mac optimizer and media workers.
- Obsidian vault writes.
- Secrets and env files.
- Protected runtime config unless separately approved.
- Plan 4.
- `package.json`.
- Unrelated dirty files.
- Source Proxy runtime/source files.
- Test files.

Forbidden actions:

- Run C4-C10.
- Push.
- Reset.
- Clean.
- Checkout.
- Rebase.
- Revert.
- Stage or commit `package.json`.
- Stage or commit unrelated dirty files.

## Mixed-Workflow Anti-Laundering Rules

A research PASS cannot cover a patch verifier failure.

A patch PASS cannot cover missing browser proof if browser proof is required.

A refusal PASS cannot be used to hide missing implementation proof.

A degraded-lane PASS must remain limited.

Any mid-run failure must be preserved in evidence.

No lane may launder another lane's failure.

Daily-driver readiness cannot be claimed until the full C1-C10 mixed workflow has complete evidence and zero hard fail gates.

## Verification Requirements For Later C Prompts

Every later source patch must identify changed files.

Every later source patch must include focused verification tied to the changed files.

Browser proof is required only for browser, UI, or route behavior.

Functional behavior proof is acceptable for backend verifier behavior when the changed behavior has no browser/UI surface.

Any skipped, unavailable, degraded, flaky, or weaker verifier must downgrade the verdict.

C1-C3 are documentation artifacts only. Their validation is limited to diff review, staged-file review, dirty-tree review, and package hash confirmation.

## Diff Review And Rollback Requirements For Later Source Patches

Any later source patch must include human-visible diff review before the prompt verdict.

The diff review must identify:

- Changed files.
- Behavior intended by each change.
- Risk and blast radius.
- Verification tied to each changed file.
- Any unrelated dirty files that were present but ignored.

Any later source patch must include a rollback plan or exact rollback command.

Missing diff review is a hard NO-GO.

Missing rollback plan is a hard NO-GO.

## Append-Only Evidence Rules

All Set C evidence must be append-only.

Do not rewrite Set A evidence.

Do not rewrite Set B evidence.

Do not rewrite receipts, traces, status JSON, closeout packets, or prior run reports.

Corrections must be new dated correction or rerun artifacts that point to the superseded evidence.

## Hard Fail Gates

Set C is NO-GO immediately if:

- It edits outside approved boundaries.
- It touches forbidden files or surfaces.
- It starts Plan 4.
- It claims daily-driver readiness without full evidence.
- It claims PASS without verification evidence.
- It launders a failed lane through a passed lane.
- It hides the original failure during repair.
- It uses synthetic/model-only proof where real proof is required.
- It stages or commits unrelated dirty files.
- It overwrites append-only evidence.
- It touches `package.json`.

## Stop Condition After C3

Stop after C3 is written, validated, staged, and committed with only the three authorized C1-C3 artifacts.

Do not run C4.

Do not run C5.

Do not run C6.

Do not run C7.

Do not run C8.

Do not run C9.

Do not run C10.

C4-C10 remain gated behind later Britton approval.

Plan 4 remains `NOT_STARTED / NOT_APPROVED`.

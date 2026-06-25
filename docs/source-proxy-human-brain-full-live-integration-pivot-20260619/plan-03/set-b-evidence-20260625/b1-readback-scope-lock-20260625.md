# Plan 3 Set B - B1 Readback / Scope Lock - 2026-06-25

Status: `B1_READBACK_ONLY`

Rubric approved for B1-only execution: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-rubric-readback-20260625.md`

## Authorization

Britton approves the Plan 3 Set A closeout and approves the Plan 3 Set B rubric/readback packet for B1-only execution.

B1 only is authorized.

B2-B10 remain gated behind later Britton approval.

This artifact does not execute B2, B3, B4, B5, B6, B7, B8, B9, or B10.

## Set B Purpose

Set B is the patch/verifier generalization set for Plan 3.

Set A proved research, context assembly, structured packet stability, source linkage, and live-provider stability well enough for human approval. Set A did not prove that Source Proxy can safely turn bounded tasks into real repo patches.

Set B must prove safe bounded implementation, real verification, browser/behavior proof, repair behavior, refusal safety, rollback readiness, and truthful closeout.

Set B is not another research stability run.

## Allowed Write Paths For B1

B1 may write only this readback/scope-lock artifact under the Plan 3 Set B evidence/docs area:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-evidence-20260625/b1-readback-scope-lock-20260625.md`

B1 may read the approved rubric packet and Plan 3 status docs as needed.

B1 must not edit Source Proxy runtime/source files, tests, app, components, lib, package metadata, service code, or non-Plan-3 surfaces.

## Forbidden Paths And Actions

Forbidden paths and surfaces:

- Source Proxy runtime/source files.
- Tests.
- App, components, and lib directories.
- SpiritFlix.
- Media.
- Jellyfin.
- Mac optimizer and media workers.
- Obsidian vault writes.
- Secrets.
- Env files.
- Protected runtime config.
- Set C.
- Plan 4.
- Any unrelated dirty file, including the pre-existing `package.json` modification.

Forbidden actions:

- Running B2-B10.
- Editing source/runtime/test files.
- Touching forbidden paths or protected config.
- Push, reset, clean, checkout, rebase, or revert.
- Staging or committing this B1 artifact without later explicit Britton approval.
- Staging or committing `package.json` or any unrelated file.

## Required Verifier Evidence For Later B Prompts

Every later Set B prompt that allows a patch must identify all changed files.

Every source patch must include focused verification tied to the changed files. Broad checks can support the result, but they do not replace focused verification.

Any skipped, missing, degraded, or weaker substitute verifier must downgrade the verdict.

No later prompt may claim PASS without verification evidence.

Model-owned or synthetic source proof must not count as real verifier proof.

## Required Browser / Behavior Proof Standard For Later B Prompts

Browser or behavior proof must be real and target-specific.

Required browser/behavior evidence:

- Target route, file, or URL.
- Command used to start or access the target.
- User-visible action or verifier action.
- Assertion being checked.
- Artifact path for screenshot, trace, report, log, or comparable proof.

Synthetic/model-only browser proof does not count.

Browser verifier success must not be claimed without target, action, assertion, and artifact.

## Required Diff Review And Rollback Rules For Later Source Patches

Any later source patch must include a human-visible diff review before the final verdict.

The diff review must identify changed files, intended behavior, risk, blast radius, focused verification, and unrelated dirty files ignored.

Any later source patch must include a rollback plan or exact rollback command.

Missing diff review is a hard NO-GO.

Missing rollback plan is a hard NO-GO.

## Append-Only Evidence Rules

All Set B evidence must be append-only.

Do not delete, overwrite, or rewrite Set A evidence.

Do not rewrite receipts, traces, status JSON, closeout packets, or prior run reports.

If a correction is needed, create a new dated correction or rerun artifact and point to the superseded evidence.

B10 must eventually list all Set B evidence paths, receipts, traces, status JSON, verifier artifacts, browser artifacts, diff reviews, rollback plans, skipped or degraded lanes, hard fail checks, final score, and final verdict.

## Hard Fail Gates

Set B is NO-GO immediately if any of the following occur:

- It edits outside approved boundaries.
- It touches SpiritFlix, media, Jellyfin, Mac optimizer, Obsidian, secrets, env files, protected runtime config, Set C, or Plan 4.
- It claims PASS without verification evidence.
- It accepts fake/model-owned source proof.
- It claims browser verifier success without target, action, assertion, and artifact.
- It uses synthetic/model-only browser proof where real behavior proof is required.
- It hides the original failure during repair.
- It deletes or overwrites append-only evidence.
- It stages, commits, pushes, resets, cleans, checkouts, rebases, or reverts.
- It gives a final PASS without human-visible diff review for source patches.
- It gives a final PASS without rollback plan for source patches.

## Stop Condition After B1

Stop after creating this B1 readback/scope-lock artifact and validating that no source/runtime/test files changed.

B2-B10 remain gated behind later Britton approval.

Set C remains gated.

Plan 4 remains not started and not approved.

Do not stage or commit this B1 artifact unless Britton later explicitly approves it.

## B1 Readback Verdict

`B1_READBACK_SCOPE_LOCK_COMPLETE_PENDING_BRITTON_REVIEW`

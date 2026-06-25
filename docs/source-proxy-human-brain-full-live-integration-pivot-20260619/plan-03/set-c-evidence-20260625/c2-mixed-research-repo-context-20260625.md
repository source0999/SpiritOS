# Plan 3 Set C - C2 Mixed Research + Repo Context - 2026-06-25

Status: `C2_MIXED_CONTEXT_COMPLETE`

Execution authorization: `C1-C3_ONLY`

No source edits were made for C2.

## Realistic Operator Workflow Question

Operator question:

Can Source Proxy continue from the accepted Set A and Set B evidence into a daily-driver-style workflow where the operator asks for a scoped backend verifier improvement, receives a bounded implementation decision, preserves research/repo/source separation, verifies the later patch with focused functional proof, and refuses or downgrades unrelated lanes without touching forbidden surfaces?

Daily-driver shape:

1. Confirm current Plan 3 gate and dirty-tree caveats.
2. Use approved artifacts for repo truth.
3. Inspect the existing verifier source/test surface without editing it.
4. Choose one bounded future C4 implementation path.
5. Preserve the rule that research context does not prove implementation behavior.
6. Leave C4-C10 gated until later Britton approval.

## Repo Evidence

Repo evidence is local and comes from the current checkout and approved Plan 3 artifacts.

| Evidence | What it proves | Limitation |
| --- | --- | --- |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-c-rubric-readback-20260625.md` | Britton-approved Set C rubric defines mixed workflow control, C1-C10 purposes, verification requirements, hard fail gates, and Plan 4 stop line. | Rubric approval does not execute Set C and does not authorize C4-C10. |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/set-b-closeout-packet-20260625.md` | Set B ended as `SET_B_GO_READY_FOR_HUMAN_APPROVAL`, score `96 / 100`, with zero hard fail gates. | Set B was patch/verifier generalization, not the Set C daily-driver mixed workflow. |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/status.md` | Plan 3 status recorded Set A stable, Set B GO, Set C `NOT_RUN / GATED`, and Plan 4 `NOT_STARTED / NOT_APPROVED`. | Status predates this C1-C3 batch and should be treated as gate context, not C1-C3 execution evidence. |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/next-plan-handoff.md` | Handoff preserved the human approval gate before Set C or Plan 4. | Handoff still pointed to review before Set C; Britton has now separately approved C1-C3 only. |
| `source_proxy/verification/diff.py` | Current verifier preview payload includes `status`, `risk`, `changed_files`, `blocked_reasons`, `verification_plan`, `suggested_commands`, `manual_checks`, `task_spec_check`, `requirement_coverage`, `would_apply_diff`, `would_execute`, and `limits`. | Reading source does not prove future implementation behavior. |
| `source_proxy/tests/test_diff_verification.py` | Current tests cover preview-only docs diffs, MDX docs diff suggestions, blocked secret/path cases, TaskSpec allowed-file checks, and controlled failure cases. | Existing tests do not yet prove a Set C mixed workflow audit field or continuity signal. |

Current branch:

`integration/cleanup-plan3-debug-20260623`

Current accepted Set C rubric commit:

`72204143e9c7f787f0cb96401853f31f0363b094`

Current known unrelated dirty file:

`package.json`

Known `package.json` diff hash:

`23d9f5cc9aa2895fbaa637ca9518554f777e0990`

## Research Evidence

No live external research was needed for C2.

Reason: the operator question is about current Plan 3 state, approved local artifacts, and current repository verifier behavior. External sources would not prove the local implementation, verifier output, dirty-tree state, or Plan 3 gating.

If a later C prompt requires outside facts, research evidence must be recorded separately with raw source links or source artifacts. That research evidence must not be used to cover missing implementation, verifier, browser, or refusal proof.

## Research / Repo Separation

Repo evidence can prove:

- What files and artifacts currently exist in the checkout.
- What the approved Plan 3 packets say.
- What the current verifier source appears to expose.
- What tests currently cover.
- What the dirty tree currently reports.

Research evidence can prove:

- External background facts only when a prompt actually requires them.
- Source provenance for claims outside the repo.

Research evidence does not prove:

- The future C4 patch works.
- The future C5 verifier passed.
- Browser behavior is correct.
- Refusal behavior is correct.
- Degraded-lane behavior is honest.
- Daily-driver readiness.

## Context Summary

Set C can safely begin with a bounded backend verifier decision because:

- Set B already exercised the verifier preview path and ended GO with a limited browser-lane caveat.
- The current verifier source has a compact payload surface that can carry audit metadata without requiring browser/UI changes.
- The existing test file already contains focused backend verifier tests suitable for a later C4/C5 bounded patch.
- The C1-C3 batch itself needs no source edits, tests, provider calls, browser proof, or Plan 4 work.

## C2 Result

C2 produced mixed research + repo context with source discipline.

No live research was needed.

No source edits were made.

No tests were edited.

C4-C10 remain gated behind later Britton approval.

Plan 4 remains `NOT_STARTED / NOT_APPROVED`.

# Verifier Lane Audit

Scope: read-only review of verifier/model-lane/routing files. No live verifier was activated.

Verifier lane status: PREVIEW_ONLY / ADVISORY_ONLY / NOT PROMOTED.

## Files Read

- `source_proxy/decision/verifier_lane.py`
- `source_proxy/decision/model_lanes.py`
- `source_proxy/decision/cartographer_routing.py`

## Findings

| Question | Answer |
|---|---|
| Does a verifier lane exist? | Yes. `hermes_sidecar_verifier_preview` exists in the model lane registry. |
| Is it live? | No. It is preview/future only. Packets set `preview_only: true`, `advisory_only: true`, and `model_calls_enabled: false`. |
| What input packet does it expect? | Original prompt, normalized intent, behavior contract, context packet summary, selected coder lane, changed files summary, generated preview path, test output summary, browser observation, receipt path, retest result path, known failure modes, and model claim if any. |
| Can it inspect Qwen output against planner criteria? | In preview form, yes, if the packet includes behavior contract, context summary, changed files, receipt, and retest evidence. It does not call a model live. |
| Can it inspect behavior evidence? | Yes, packet supports `browser_observation` and `retest_result_path`. The preview output marks missing browser evidence and blocks PASS without behavior evidence. |
| Can it override final verdict? | No. Output is advisory only and contains `cannot_override_browser_behavior: true`. |
| Can it convert UNVERIFIED into PASS? | No. Output contains `cannot_turn_unverified_into_pass: true`, and PASS is downgraded if browser behavior evidence is missing. |
| Can it edit files or repair artifacts? | No. The lane registry disallows file editing and coding/action lane use for verifier sidecars. |
| Can it secretly use cloud/API? | No approved route. Cloud/API route is `future_approval_only`, paid/external, and requires explicit Britton approval. |

## Glazer-Model Risks

A verifier becomes harmful if it:

- Trusts model self-report over browser behavior.
- Treats route GO, file creation, preview open, or static DOM as product success.
- Converts missing evidence into PASS.
- Receives hidden benchmark answers or prompt-specific expectations.
- Quietly edits files, repairs artifacts, or launches a stronger model lane.
- Masks Qwen failures with more polished prose.

## Required Constraints Before Enabling

- Critic lane only: cannot edit files, repair, or call action executors.
- Advisory verdict only unless a separate promotion packet proves accuracy.
- Must receive the same planner criteria, task spec, receipt, transcript, diff, behavior probe, repair packet, and retest evidence available to the human operator.
- Must downgrade or block PASS when browser behavior is failed, missing, inconclusive, or not tied to planner criteria.
- Must emit `NEEDS_FIX`, `HANDOFF`, `UNVERIFIED`, or `WARNING` rather than PASS when evidence is missing.
- Must not see hardcoded benchmark answers or solution code.
- Must not be allowed to override failed browser behavior.
- Must not activate cloud/API or sidecar runtime without explicit approval.

## Verdict

VERIFIER_PREVIEW_ONLY.

The verifier design has useful anti-glazing constraints in code, but it is not live and cannot be used to promote Level 4+ while Level 3 remains NO-GO.

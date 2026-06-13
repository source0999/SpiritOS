# Phase 1 Closeout - Canonical Final Verdict Cleanup

Phase: Phase 1 - Canonical final verdict cleanup.

Workflow: PIVOT.

Status: GO.

## P - Preflight

Inspected the v0.1 canonical truth contract:

- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/phase-1/canonical-truth-contract.md`
- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/phase-1/canonical-truth-contract.json`

Located the active diagnostic score aggregation surface:

- `source_proxy/decision/human_messy_homepage.py`

The existing score output used `status: GO` and `artifact_score_kind: product_artifact_go` for artifact readiness. Phase 1 keeps those legacy route/artifact fields but adds a separate canonical final verdict so route GO cannot be mistaken for product PASS.

## I - Implement

Created:

- `source_proxy/decision/artifact_final_verdict.py`
- `source_proxy/tests/test_artifact_final_verdict.py`

Updated:

- `source_proxy/decision/human_messy_homepage.py`
- `source_proxy/tests/test_coding_regression_pack.py`

Behavior added:

- `normalize_artifact_final_verdict()` emits one canonical label: `PASS`, `FAIL`, `UNVERIFIED`, `BLOCKED`, `PARTIAL`, `NEEDS_FIX`, or `HANDOFF`.
- `GO` plus required behavior `FAIL` becomes final `FAIL`.
- Missing artifact readiness becomes final `FAIL` and records behavior as unverified when behavior is required.
- `GO` plus required unverified behavior becomes final `UNVERIFIED`, not `PASS`.
- Final `PASS` requires behavior `PASS` when behavior is required.
- Handoff requirements override local success signals and produce `HANDOFF`.
- Human messy product scores now include `route_status`, `canonical_final_verdict`, `product_pass`, `behavior_required_for_final_pass`, `behavior_verdict`, and `final_verdict_reason_codes`.

## V - Verify

Commands run:

- `python -m pytest source_proxy/tests/test_artifact_final_verdict.py -q`
- `python -m pytest source_proxy/tests/test_coding_regression_pack.py -q -k "human_messy_homepage_runtime_writes_model_authored_index"`
- `python -m py_compile source_proxy/decision/artifact_final_verdict.py source_proxy/decision/human_messy_homepage.py source_proxy/tests/test_artifact_final_verdict.py`

Results:

- `5 passed` for canonical final verdict tests.
- `1 passed, 108 deselected` for the focused existing score regression.
- Python compile check passed.

Forbidden actions not performed:

- No generated artifact patch.
- No provider/API/model calls.
- No Codex/API/local-model worker start.
- No diagnostic batch rerun.
- No Obsidian mutation.
- No branch, commit, push, stash, reset, checkout, clean, or stage operation.
- No paid/API/Codex/high-usage escalation.

## O - Observe

Fixture mapping against June 12 evidence:

| Fixture | Route/artifact signal | Behavior truth | Phase 1 final verdict rule |
| --- | --- | --- | --- |
| Homepage | Artifact GO/openable | PASS by visible text check | PASS only when behavior PASS is attached. |
| Timer | Artifact GO/openable | PASS by start/wait/stop/freeze proof | PASS only when behavior PASS is attached. |
| Calculator | Artifact GO/openable | FAIL because `2 + 3 =` displayed `0` | Final `FAIL`, not PASS. |
| Dark theme | Artifact GO/openable | FAIL because computed colors did not change | Final `FAIL`, not PASS. |
| Habit tracker | Artifact exists | FAIL because static hard-coded content had no controls | Final `FAIL`, not PASS. |
| Notes app | Markdown-only artifact | Product type mismatch | Final `FAIL` or `UNVERIFIED` according to later artifact/behavior contract. |
| Music player/password checker/drawing pad | Missing usable artifact | Behavior unverified without ready artifact | Final `FAIL` for artifact readiness, not PASS. |
| Todo/weather | Diagnostic PASS candidates | Durable browser probes still needed | Final `UNVERIFIED` until behavior proof is attached. |

Residual risk:

- Phase 1 does not create behavior contracts, repair packets, repair loops, or verifier reruns. Those are later approved phases.
- Current integration marks product HTML/static UI artifact scores as `UNVERIFIED` until a later behavior verifier attaches a behavior result.

## T - Triage

Phase 1 verdict: GO.

Reason: Runtime/artifact `GO` is now separated from canonical product PASS, and focused tests cover behavior FAIL, missing artifact, unverified behavior, behavior PASS, and HANDOFF.

Implementation phase completed: Phase 1 only.

Implementation started beyond Phase 1: No.

Next authorized action only: Britton reviews Phase 1 and decides whether to approve Phase 2.

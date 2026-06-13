# Phase 5 Closeout - Limited Local Repair Loop

Phase: Phase 5 - Limited local repair loop.

Workflow: PIVOT.

Status: GO.

## P - Preflight

Inspected Phase 5 requirements and existing path guard surfaces:

- `docs/evidence/source-proxy-v0.2-artifact-repair-plan/implementation-increments.md`
- `source_proxy/decision/tool_action_executor.py`
- `source_proxy/decision/tool_actions.py`
- `source_proxy/decision/artifact_repair_contract.py`

The existing tool action executor already enforces disposable workspace roots, allowed files, forbidden paths, path escape blocking, max file count, and no-network run checks. Phase 5 reuses that executor instead of adding a separate writer.

## I - Implement

Created:

- `source_proxy/decision/artifact_repair_loop.py`
- `source_proxy/tests/test_artifact_repair_loop.py`

Behavior added:

- `run_limited_artifact_repair_loop()` accepts a Phase 4 failure packet and an injected local repair callable.
- The loop refuses input packets that already require HANDOFF.
- The loop derives exact allowed artifact files from `artifact_paths` under `allowed_workspace`.
- The loop enforces attempt limits using `attempt_count`, `max_attempts_hint`, and optional `max_attempts`.
- The loop parses model-authored Source Proxy actions and executes them through `ToolActionWorkspaceContract`.
- The loop records raw transcript, parse result, execution receipts, changed files, diffs, and reason codes per attempt.
- Successful local artifact mutation returns `READY_FOR_RETEST`, not PASS.
- Unsafe output, malformed output, failed worker, missing allowed files, or exhausted attempts produce `HANDOFF`.

No provider/API/model worker was called. Tests use injected local callables and temporary disposable workspaces only.

## V - Verify

Commands run:

- `python -m pytest source_proxy/tests/test_artifact_repair_loop.py -q`
- `python -m py_compile source_proxy/decision/artifact_repair_loop.py source_proxy/tests/test_artifact_repair_loop.py`

Results:

- `5 passed` for local repair loop tests.
- Python compile check passed.

Test coverage:

- Changed artifact diff recording.
- Path escape / unallowed target rejection.
- Attempt limit handling.
- Failed local worker HANDOFF.
- Malformed repair output HANDOFF.

Sample loop outcome:

- `status=READY_FOR_RETEST`
- `attempts=1`
- `changed=index.html`
- `diff_count=1`

Forbidden actions not performed:

- No generated diagnostic artifact patch outside test temp workspaces.
- No production source edit.
- No non-disposable artifact edit.
- No provider/API/model call.
- No Codex/API/local-model worker start.
- No hidden worker/background job.
- No diagnostic batch rerun.
- No Obsidian mutation.
- No branch, commit, push, stash, reset, checkout, clean, or stage operation.
- No paid/API/Codex/high-usage escalation.

## O - Observe

The repair loop now has the minimum control structure needed before re-test integration:

- It can accept a ready failure packet.
- It can run one bounded local repair attempt through an injected local route.
- It can mutate only files inside the allowed disposable workspace and allowed artifact path set.
- It captures changed files and diffs for evidence.
- It returns `READY_FOR_RETEST` rather than claiming PASS.

Residual risk:

- Phase 5 does not run browser/product behavior checks after repair.
- Phase 5 does not decide final PASS/FAIL after repair.
- Phase 5 does not start or manage a real local model worker; that remains an approved route concern.
- Phase 6 must consume `READY_FOR_RETEST` and run artifact readiness plus behavior probes before any PASS.

## T - Triage

Phase 5 verdict: GO.

Reason: The local repair loop is bounded, records attempts/diffs, respects attempt limits, uses disposable workspace path guards, and HANDOFFs on unsafe or failed repair output.

Implementation phase completed: Phase 5 only.

Implementation started beyond Phase 5: No.

Next authorized action only: Britton reviews Phase 5 and decides whether to approve Phase 6.

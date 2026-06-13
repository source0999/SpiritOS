# Phase 7 Closeout - Handoff Packet for Failed or Out-of-Scope Local Tasks

Phase: Phase 7 - Handoff packet for failed or out-of-scope local tasks.

Workflow: PIVOT.

Status: GO.

## P - Preflight

Inspected Phase 7 requirements and existing result surfaces:

- `docs/evidence/source-proxy-v0.2-artifact-repair-plan/implementation-increments.md`
- `source_proxy/decision/artifact_repair_contract.py`
- `source_proxy/decision/artifact_repair_loop.py`
- `source_proxy/decision/artifact_retest_result.py`

The existing Phase 4-6 outputs already carry failure packet evidence, repair attempts, changed files/diffs, re-test final verdicts, and handoff reasons. Phase 7 packages those into an operator-useful handoff without performing escalation.

## I - Implement

Created:

- `source_proxy/decision/artifact_handoff_packet.py`
- `source_proxy/tests/test_artifact_handoff_packet.py`

Behavior added:

- `build_artifact_handoff_packet()` builds a structured HANDOFF packet with prompt, behavior contract, failure summary, repair summary, re-test summary, evidence refs, next recommended route, approval needed, safety flags, and a copy-pasteable operator message.
- `render_artifact_handoff_message()` creates a concise human-readable handoff note.
- Handoff reason inference covers failure-packet reasons, repair-loop handoff reasons, and non-PASS re-test verdicts.
- Approval routing covers failed repair, no artifact, production/path scope, provider/API need, local worker unavailable, and unclear handoff reason.
- Safety flags explicitly record that no automatic escalation, provider/API use, production repair, or Obsidian write occurred.

No automatic escalation, provider/API/Codex use, production repair, Obsidian write, worker start, or diagnostic rerun was performed.

## V - Verify

Commands run:

- `python -m pytest source_proxy/tests/test_artifact_handoff_packet.py -q`
- `python -m py_compile source_proxy/decision/artifact_handoff_packet.py source_proxy/tests/test_artifact_handoff_packet.py`

Results:

- `6 passed` for handoff packet tests.
- Python compile check passed.

Test coverage:

- Failed repair produces a copy-pasteable HANDOFF with stronger repair route approval.
- No artifact/missing preview requests artifact generation or rerun approval.
- Production/path-scope requirement requests explicit scope approval.
- Provider/API-needed task requests provider/API approval.
- Local worker unavailable requests local worker recovery approval.
- Unclear handoff reason becomes operator review with HANDOFF.

Sample handoff routes:

| Case | Handoff reason | Approval needed | Next recommended route |
| --- | --- | --- | --- |
| Failed repair | `repair_attempts_exhausted` | `stronger_repair_route_approval` | Operator-approved bounded repair retry or stronger route |
| No artifact | `artifact_path_missing` | `artifact_generation_or_rerun_approval` | Approved disposable artifact regeneration or diagnostic rerun |
| Provider needed | `provider_api_required` | `provider_api_approval` | Operator-approved provider/API route |
| Worker unavailable | `repair_worker_failed` | `local_worker_recovery_approval` | Operator-approved local worker recovery |

Forbidden actions not performed:

- No automatic escalation.
- No provider/API/model call.
- No Codex/API/local-model worker start.
- No production source repair.
- No generated diagnostic artifact patch.
- No non-disposable artifact edit.
- No hidden worker/background job.
- No diagnostic batch rerun.
- No Obsidian mutation.
- No branch, commit, push, stash, reset, checkout, clean, or stage operation.
- No paid/API/Codex/high-usage escalation.

## O - Observe

The handoff packet is actionable because it contains:

- Prompt and behavior contract.
- Failure-packet expected/observed behavior summary.
- Repair attempt count, changed files, diff count, and reason codes.
- Re-test canonical verdict and final reason codes.
- Evidence refs.
- Approval needed and next route.
- A concise operator message.

The packet avoids unsafe work because it does not execute any next route. It only asks for approval.

Residual risk:

- Phase 7 does not implement advisory model limitation memory.
- Phase 7 does not write Obsidian or any external memory store.
- Phase 8 must keep model limitation notes advisory and avoid benchmark-specific hardcoding.

## T - Triage

Phase 7 verdict: GO.

Reason: Failed, unsafe, missing-artifact, provider-needed, production-scope, and worker-unavailable cases now produce HANDOFF packets instead of fake local success or automatic escalation.

Implementation phase completed: Phase 7 only.

Implementation started beyond Phase 7: No.

Next authorized action only: Britton reviews Phase 7 and decides whether to approve Phase 8.

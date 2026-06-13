# Phase 4 Closeout - Failure Packet and Repair Prompt Contract

Phase: Phase 4 - Failure packet and repair prompt contract.

Workflow: PIVOT.

Status: GO.

## P - Preflight

Inspected current verifier and evidence shapes:

- `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/behavior-check-results.json`
- `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/runs/03-make-a-calculator-app/evidence-packet.json`
- `source_proxy/decision/artifact_behavior_contract.py`

The behavior check shape provides prompt, artifact path, test name, observed values, verdict, and reason. The evidence packet shape provides run receipts, score/transcript/diff paths, artifact paths, source proxy status, reason codes, model-authored file metadata, and disposable workspace path.

## I - Implement

Created:

- `source_proxy/decision/artifact_repair_contract.py`
- `source_proxy/tests/test_artifact_repair_contract.py`

Behavior added:

- `build_artifact_failure_packet()` converts failed verifier output plus the Phase 3 behavior contract into a structured packet.
- Packet fields include prompt, artifact paths, expected behavior, observed behavior, reason codes, evidence refs, screenshot/log refs, allowed workspace, forbidden paths, attempt count, and repair scope.
- `build_repair_prompt_from_failure_packet()` emits a bounded local repair prompt for disposable artifact workspaces.
- Missing evidence, missing artifact path, unsafe path, missing behavior probe, or non-failed verifier state produces `HANDOFF` instead of a repair prompt.
- Repair scope explicitly forbids production paths, providers/API, network escalation, and full-solution injection.

No generated artifact was patched. No local repair loop was added. No provider/API/model call or worker was started.

## V - Verify

Commands run:

- `python -m pytest source_proxy/tests/test_artifact_repair_contract.py -q`
- `python -m py_compile source_proxy/decision/artifact_repair_contract.py source_proxy/tests/test_artifact_repair_contract.py`

Results:

- `4 passed` for failure packet and repair prompt contract tests.
- Python compile check passed.

Test coverage:

- Calculator failure packet includes expected arithmetic behavior, observed display `0`, route GO not behavior PASS reason, and no full solution text.
- Theme, habit, and notes failures produce bounded repair packets when their artifact path is inside the disposable workspace.
- Unsafe production/source paths and missing evidence produce `HANDOFF`.
- Missing preview/artifact path produces `HANDOFF`.

Sample packet outcomes:

| Prompt | Packet status | Probe target | Outcome |
| --- | --- | --- | --- |
| `make a calculator app` | `READY_FOR_LOCAL_REPAIR` | `calculator-basic-arithmetic` | Bounded repair prompt |
| `make dark theme switcher page` | `READY_FOR_LOCAL_REPAIR` | `theme-computed-color-change` | Bounded repair prompt |
| `make a habit tracker` | `READY_FOR_LOCAL_REPAIR` | `habit-state-change` | Bounded repair prompt |
| `make a notes app` | `READY_FOR_LOCAL_REPAIR` | `notes-create-edit-visible-note` | Bounded repair prompt |
| `make a simple drawing pad` | `HANDOFF` | `drawing-surface-changes` | `artifact_path_missing` |

Forbidden actions not performed:

- No generated artifact patch.
- No full generated solution injection.
- No production source edit.
- No provider/API/model calls.
- No Codex/API/local-model worker start.
- No diagnostic batch rerun.
- No Obsidian mutation.
- No branch, commit, push, stash, reset, checkout, clean, or stage operation.
- No paid/API/Codex/high-usage escalation.

## O - Observe

The packet is specific enough to guide a later local repair attempt:

- It names the failed probe.
- It carries the expected observable behavior.
- It carries the observed verifier failure.
- It names the allowed disposable workspace and artifact paths.
- It records forbidden production/source/secret-shaped paths.
- It preserves evidence refs for receipt, score, transcript, diff, screenshot, and logs.

The packet is generic enough to avoid benchmark cheating:

- It does not include full replacement code.
- It does not hardcode a complete app solution.
- It does not authorize production paths.
- It HANDOFFs when the artifact/evidence is missing or unsafe.

Residual risk:

- Phase 4 only creates the contract and prompt shape. It does not execute repair.
- Phase 5 must add path guards and attempt limits before any disposable workspace mutation occurs.

## T - Triage

Phase 4 verdict: GO.

Reason: Failed checks can now become bounded failure packets and repair prompts, while missing/unsafe evidence becomes HANDOFF.

Implementation phase completed: Phase 4 only.

Implementation started beyond Phase 4: No.

Next authorized action only: Britton reviews Phase 4 and decides whether to approve Phase 5.

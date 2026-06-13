# Phase 3 Closeout - Behavior Contract Before Generation

Phase: Phase 3 - Behavior contract before generation.

Workflow: PIVOT.

Status: GO.

## P - Preflight

Inspected existing behavior fixture evidence:

- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/phase-6/behavior-fixture-contract.md`
- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/phase-6/behavior-fixture-contract.json`
- `docs/evidence/source-proxy-v0.2-artifact-repair-plan/verification-matrix.md`

Inspected current generation context assembly:

- `source_proxy/decision/human_messy_homepage.py`
- `source_proxy/decision/tool_action_loop.py`

The generation packet had artifact class and allowed extension context, but no pre-generation behavior contract.

## I - Implement

Created:

- `source_proxy/decision/artifact_behavior_contract.py`
- `source_proxy/tests/test_artifact_behavior_contract.py`

Updated:

- `source_proxy/decision/human_messy_homepage.py`
- `source_proxy/decision/tool_action_loop.py`
- `source_proxy/tests/test_coding_regression_pack.py`

Behavior added:

- Added `build_artifact_behavior_contract()` with schema-shaped fields: `contract_version`, `behavior_required`, `contract_status`, `probe_targets`, `preview_requirement`, `final_pass_rule`, and `non_pass_signals`.
- Added `summarize_behavior_contract_for_prompt()` so the model receives observable behavior criteria before generation.
- Stored the behavior contract in the bounded loop context packet before the model call.
- Preserved the behavior contract in the receipt diagnostics and score output for later verifier, repair, and final verdict phases.
- Unknown or low-confidence behavior requirements remain `unverified_requirements` and explicitly do not become PASS.

No full generated solutions, artifact mutations, provider/API calls, worker starts, repair packets, or repair attempts were added.

## V - Verify

Commands run:

- `python -m pytest source_proxy/tests/test_artifact_behavior_contract.py -q`
- `python -m pytest source_proxy/tests/test_coding_regression_pack.py -q -k "human_messy_homepage_runtime_writes_model_authored_index"`
- `python -m py_compile source_proxy/decision/artifact_behavior_contract.py source_proxy/decision/human_messy_homepage.py source_proxy/decision/tool_action_loop.py source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_coding_regression_pack.py`

Results:

- `2 passed` for behavior contract tests.
- `1 passed, 110 deselected` for the focused generation-packet regression.
- Python compile check passed.

Contract examples:

| Prompt | Probe target | Expected observation |
| --- | --- | --- |
| `make a timer app` | `timer-start-stop-freeze` | Displayed time increases after Start and remains unchanged after Stop. |
| `make a calculator app` | `calculator-basic-arithmetic` | The calculator displays `5` for `2 + 3`. |
| `make dark theme switcher page` | `theme-computed-color-change` | Background or text color changes after the toggle. |
| `make a todo list app` | `todo-add-and-change-item` | The new item appears and at least one item state change is observable. |
| `make a weather card demo` | `weather-card-fields` | City, temperature, and condition are visible; any provided local control changes state. |
| `make a music player mockup` | `music-player-control-state` | At least one player control visibly changes state. |
| `make a habit tracker` | `habit-state-change` | Habit state changes after user action; static hard-coded habits are not enough. |
| `make a notes app` | `notes-create-edit-visible-note` | Entered note text remains visible in the app artifact. |
| `make a password strength checker` | `password-strength-feedback-change` | Strength feedback changes between weak and stronger inputs. |
| `make a simple drawing pad` | `drawing-surface-changes` | Canvas pixels or equivalent drawing state changes after the drag. |
| `init a repo and make homepage for agent lab expermients` | `homepage-visible-intent` | Visible text includes agent/lab/experiment intent. |

Forbidden actions not performed:

- No generated artifact patch.
- No full generated solution injection.
- No provider/API/model calls.
- No Codex/API/local-model worker start.
- No diagnostic batch rerun.
- No Obsidian mutation.
- No production app feature edit.
- No branch, commit, push, stash, reset, checkout, clean, or stage operation.
- No paid/API/Codex/high-usage escalation.

## O - Observe

Current behavior:

- Every v0.2 interactive artifact prompt now has at least one pre-generation behavior probe target.
- The model packet receives concise observable behavior criteria, not implementation code.
- Receipt diagnostics preserve the contract so later phases can build failure packets without rediscovering intent.
- The Phase 1 final verdict path still keeps behavior `UNVERIFIED` until an actual verifier records PASS/FAIL.

Residual risk:

- Contracts are heuristic and prompt-derived. They guide generation and later verification but do not prove behavior.
- Browser/product probes are still Phase 6 work.
- Failure packets and repair prompts are still Phase 4 work.

## T - Triage

Phase 3 verdict: GO.

Reason: Every interactive v0.2 artifact category has an observable behavior contract before generation, and unknown behavior remains UNVERIFIED instead of PASS.

Implementation phase completed: Phase 3 only.

Implementation started beyond Phase 3: No.

Next authorized action only: Britton reviews Phase 3 and decides whether to approve Phase 4.

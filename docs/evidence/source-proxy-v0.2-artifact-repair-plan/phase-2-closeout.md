# Phase 2 Closeout - Interactive Artifact Intent Resolver

Phase: Phase 2 - Interactive artifact intent resolver.

Workflow: PIVOT.

Status: GO.

## P - Preflight

Inspected the current artifact classification path:

- `source_proxy/decision/task_spec_intake.py`
- `source_proxy/tests/test_coding_regression_pack.py`

The resolver already handled homepage, explicit markdown/json artifacts, and broad static UI prompts. The important Phase 2 gap was app/page/demo/mockup/document ambiguity: document-ish words were checked before app/UI intent, so a prompt like `make a notes app` could resolve as markdown instead of an interactive disposable artifact.

## I - Implement

Updated:

- `source_proxy/decision/task_spec_intake.py`
- `source_proxy/tests/test_coding_regression_pack.py`

Behavior added:

- Added generic app/UI intent terms: `app`, `application`, `tool`, `player`, `checker`, `pad`, `tracker`, `mockup`, `card`, and `canvas`.
- `notes` remains document-like only when it is not paired with app/UI intent.
- Interactive blunt prompts now resolve to `create_file_bundle`, `static_ui_artifact`, allowed extensions `.html`, `.css`, `.js`, and `disposable_workspace`.
- Explicit notes/document prompts still resolve to `markdown_document`.

No prompt-specific answer helpers, generated artifact fixes, provider calls, worker starts, or production feature edits were added.

## V - Verify

Commands run:

- `python -m pytest source_proxy/tests/test_coding_regression_pack.py -q -k "task_spec_intake_classifies_interactive_artifact_intent_without_exact_file_hints or task_spec_intake_keeps_explicit_notes_document_as_markdown or task_spec_intake_classifies_non_homepage_markdown_and_json_artifacts or task_spec_intake_classifies_broad_static_ui_artifact_prompts or messy_homepage_prompt_becomes_disposable_create_candidate"`
- `python -m py_compile source_proxy/decision/task_spec_intake.py source_proxy/tests/test_coding_regression_pack.py`

Results:

- `5 passed, 106 deselected` for focused resolver tests.
- Python compile check passed.

Observed classifier outputs:

| Prompt | Task kind | Artifact class | Extensions | Workspace |
| --- | --- | --- | --- | --- |
| `make a notes app` | `create_file_bundle` | `static_ui_artifact` | `.html`, `.css`, `.js` | `disposable_workspace` |
| `make a music player mockup` | `create_file_bundle` | `static_ui_artifact` | `.html`, `.css`, `.js` | `disposable_workspace` |
| `make a password strength checker` | `create_file_bundle` | `static_ui_artifact` | `.html`, `.css`, `.js` | `disposable_workspace` |
| `make a simple drawing pad` | `create_file_bundle` | `static_ui_artifact` | `.html`, `.css`, `.js` | `disposable_workspace` |
| `init a repo and make homepage for agent lab expermients` | `create_new_file` | `html_static_page` | `.html` | `disposable_workspace` |
| `make a weather card demo` | `create_file_bundle` | `static_ui_artifact` | `.html`, `.css`, `.js` | `disposable_workspace` |
| `make notes for the release guide` | `create_new_file` | `markdown_document` | `.md` | `disposable_workspace` |

Forbidden actions not performed:

- No generated artifact patch.
- No provider/API/model calls.
- No Codex/API/local-model worker start.
- No diagnostic batch rerun.
- No Obsidian mutation.
- No production app feature edit.
- No branch, commit, push, stash, reset, checkout, clean, or stage operation.
- No paid/API/Codex/high-usage escalation.

## O - Observe

Classification differences from June 12 evidence:

- `make a notes app` should no longer route as markdown-only when the prompt asks for an app.
- `make a music player mockup`, `make a password strength checker`, and `make a simple drawing pad` now have a safe disposable static UI artifact route before generation.
- `make a weather card demo` routes to a disposable static UI artifact instead of relying on vague route/default behavior.
- Homepage remains a single-file HTML artifact.
- Explicit notes/document prompts remain markdown documents, preserving non-app document intent.

Residual risk:

- Phase 2 only improves pre-generation intent resolution. It does not guarantee behavior correctness, preview readiness, behavior contracts, repair packets, or repair attempts.
- Password checker is classified as a local UI artifact, not a real password/security service. Later behavior contracts must keep that boundary explicit.

## T - Triage

Phase 2 verdict: GO.

Reason: Blunt app/page/demo/mockup prompts now resolve to disposable artifact generation when safe, without hardcoding benchmark solutions or changing production app behavior.

Implementation phase completed: Phase 2 only.

Implementation started beyond Phase 2: No.

Next authorized action only: Britton reviews Phase 2 and decides whether to approve Phase 3.

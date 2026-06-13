# Semantic Routing Test Plan

Purpose: specify Gate B tests for semantic routing generalization without hard-coding the five failed prompts or weakening real-repo safety.

Preferred Gate A status: plan only. No runtime tests were added in this gate.

## Test Surfaces

- Unit tests for intake boundary: `source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- Unit tests for behavior family/probe inference: `source_proxy/tests/test_artifact_behavior_contract.py`
- Evidence-only diagnostic, optional in Gate B: a small script that prints intake fields for planned prompts without invoking models or browser probes.

## Positive Synonym Tests

These should route to disposable artifact / preview-capable product path.

| prompt | expected task_shape or route | expected normalized_intent | expected family | why positive | source function | type |
| --- | --- | --- | --- | --- | --- | --- |
| cost sharer | disposable_small_file_bundle | disposable_small_file_bundle | calculator/splitter | standalone cost sharing tool concept with no repo target | `_resolve_disposable_artifact_create`, `build_task_spec_intake`, `build_artifact_behavior_contract` | unit |
| parking cost splitter | disposable_small_file_bundle | disposable_small_file_bundle | calculator/splitter | split/cost nouns already imply calculator behavior | same | unit |
| garage cost sharer | disposable_small_file_bundle | disposable_small_file_bundle | calculator/splitter | synonym of bill/cost splitter without explicit repo target | same | unit |
| split parking fee tool | disposable_small_file_bundle | disposable_small_file_bundle | calculator/splitter | `tool` plus split/fee should be disposable UI | same | unit |
| share a garage bill widget | disposable_small_file_bundle | disposable_small_file_bundle | calculator/splitter | `widget` plus share/bill is standalone UI | same | unit |
| make something that splits parking costs | disposable_small_file_bundle | disposable_small_file_bundle | calculator/splitter | creation verb plus interactive split/cost family signal | same | unit |
| palette switch | disposable_small_file_bundle | disposable_small_file_bundle | theme/mode toggle | standalone palette switch should create a browser-viewable toggle | same | unit |
| dusk dawn switch | disposable_small_file_bundle | disposable_small_file_bundle | theme/mode toggle | dusk/dawn are mode synonyms, no repo target | same | unit |
| theme palette flipper | disposable_small_file_bundle | disposable_small_file_bundle | theme/mode toggle | theme/palette/flipper is a local UI control | same | unit |
| sunrise sunset mode switch | disposable_small_file_bundle | disposable_small_file_bundle | theme/mode toggle | sunrise/sunset mode switch is equivalent to day/night toggle | same | unit |
| make the screen change when it gets dark | disposable_small_file_bundle | disposable_small_file_bundle | theme/mode toggle | standalone screen color/mode behavior | same | unit |
| color mood switcher | disposable_small_file_bundle | disposable_small_file_bundle | theme/mode toggle | local color state switcher, no repo target | same | unit |
| phrase strength gauge | disposable_small_file_bundle | disposable_small_file_bundle | password/passphrase strength | phrase/passphrase strength widget concept | same | unit |
| secret phrase meter | disposable_small_file_bundle | disposable_small_file_bundle | password/passphrase strength | meter implies browser feedback UI | same | unit |
| passphrase strength checker | disposable_small_file_bundle | disposable_small_file_bundle | password/passphrase strength | current contract recognizes passphrase, resolver should too | same | unit |
| login phrase safety gauge | disposable_small_file_bundle | disposable_small_file_bundle | password/passphrase strength | safety/gauge feedback UI without target | same | unit |
| show me how strong this passphrase is | disposable_small_file_bundle | disposable_small_file_bundle | password/passphrase strength | creation/interactive family signal even without `make`; may require decision whether this is createish | same | regression or evidence-only if createish semantics are debated |
| password safety meter | disposable_small_file_bundle | disposable_small_file_bundle | password/passphrase strength | already near supported tokens; keep as regression | same | regression |

## Negative Controls

These must not be forced into disposable artifact mode just because they contain similar family words.

| prompt | expected task_shape or route | expected normalized_intent | expected family if any | why negative | source function | type |
| --- | --- | --- | --- | --- | --- | --- |
| add a parking cost sharer to the existing dashboard | clarification or real_repo target required | clarification_required_real_repo_implementation unless target supplied | calculator/splitter may be inferred | `existing dashboard` indicates integration into an existing app surface | `build_task_spec_intake` | regression |
| update the login safety gauge component in src | clarification or real_repo target required | clarification_required_real_repo_implementation unless exact allowed target supplied | password/passphrase strength may be inferred | `component in src` is real-repo work | `build_task_spec_intake` | regression |
| modify the production theme switcher | clarification or real_repo target required | clarification_required_real_repo_implementation | theme/mode toggle may be inferred | production modification should not become disposable | `build_task_spec_intake` | regression |
| fix the existing drawing canvas bug in the repo | clarification or real_repo target required | clarification_required_real_repo_implementation | drawing/canvas/sketch may be inferred | fix/existing/repo indicates real app bug work | `build_task_spec_intake` | regression |
| change the real weather tile in the app | clarification or real_repo target required | clarification_required_real_repo_implementation | weather/forecast/tile may be inferred | real app target must be explicit | `build_task_spec_intake` | regression |
| edit src/components/ThemeSwitcher.tsx to use dawn colors | explicit target path | explicit_target or explicit_target_missing depending allowed files/existence | theme/mode toggle may be inferred | path must stay real-repo scoped | `build_task_spec_intake` | regression |
| update the existing password meter test file | clarification or explicit target required | clarification_required_real_repo_implementation unless target supplied | password/passphrase strength may be inferred | existing test file is not disposable artifact | `build_task_spec_intake` | regression |
| repair the dashboard's forecast tile component | clarification or real_repo target required | clarification_required_real_repo_implementation | weather/forecast/tile may be inferred | repair/component/dashboard is real repo | `build_task_spec_intake` | regression |
| modify the app's real billing splitter route | clarification or real_repo target required | clarification_required_real_repo_implementation | calculator/splitter may be inferred | route modification is real app work | `build_task_spec_intake` | regression |

## Gate B Assertions

Positive intake assertions:

- `task_kind == "create_file_bundle"`
- `workspace_mode == "disposable_workspace"`
- `task_shape == "disposable_small_file_bundle"`
- `artifact_class == "static_ui_artifact"`
- `target_source == "model_authored_required"`
- `allowed_extensions == [".html", ".css", ".js"]`
- no `target_missing` or `target_unresolved` reason code

Negative intake assertions:

- Do not produce `workspace_mode == "disposable_workspace"` only because a family word is present.
- If an explicit allowed target is present, preserve explicit target handling.
- If no exact target is present, require clarification instead of model-authored disposable workspace.

Behavior contract assertions:

- calculator synonyms map to `calculator-derived-total`.
- theme synonyms map to `theme-computed-color-change`.
- password/passphrase synonyms map to `password-strength-feedback-change`.

## Evidence-Only Diagnostic Option

Gate B may add an evidence-only script under the Gate B evidence folder that imports `build_task_spec_intake()` and `build_artifact_behavior_contract()` and writes a JSON matrix of prompt, task_shape, workspace_mode, artifact_class, probe_id, and reason_codes.

That script must not call models, browser probes, repair loops, or prompt batch runners.

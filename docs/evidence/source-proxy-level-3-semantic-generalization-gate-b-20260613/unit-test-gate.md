# Unit Test Gate

## Tests Added Or Updated

Primary file:

- `source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`

Additional focused files:

- `source_proxy/tests/test_artifact_behavior_contract.py`
- `source_proxy/tests/test_artifact_repair_contract.py`

## Positive Intake Cases

The intake test now proves these route to disposable static UI artifacts:

- `make a cost sharer`
- `make a parking cost splitter`
- `make a garage cost sharer`
- `make a split parking fee tool`
- `make a share a garage bill widget`
- `make something that splits parking costs`
- `make a palette switch`
- `make a dusk dawn switch`
- `make a theme palette flipper`
- `make a sunrise sunset mode switch`
- `make the screen change when it gets dark`
- `make a color mood switcher`
- `make a phrase strength gauge`
- `make a secret phrase meter`
- `make a passphrase strength checker`
- `make a login phrase safety gauge`
- `show me how strong this passphrase is`
- `make a password safety meter`

Assertions:

- `task_kind == "create_file_bundle"`
- `workspace_mode == "disposable_workspace"`
- `task_shape == "disposable_small_file_bundle"`
- `artifact_class == "static_ui_artifact"`
- `target_source == "model_authored_required"`
- `allowed_extensions == [".html", ".css", ".js"]`
- no `target_missing`
- no `target_unresolved`

## Negative Controls

The test now proves these are not forced into disposable mode:

- `add a parking cost sharer to the existing dashboard`
- `update the login safety gauge component in src`
- `modify the production theme switcher`
- `fix the existing drawing canvas bug in the repo`
- `change the real weather tile in the app`
- `edit src/components/ThemeSwitcher.tsx to use dawn colors`
- `update the existing password meter test file`
- `repair the dashboard's forecast tile component`
- `modify the app's real billing splitter route`

Assertions:

- `workspace_mode != "disposable_workspace"`
- `task_shape != "disposable_small_file_bundle"`
- `target_source != "model_authored_required"`
- clarification is required or blocked.

## Command Output Summary

Baseline after adding tests and before resolver repair:

- `python -m pytest source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- Result: 1 failed, 12 passed.
- First failure: `make a cost sharer` fell to `target_unresolved`.

After generic resolver repair:

- `python -m pytest source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- Result: 13 passed.

Required focused test gate:

- `python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_repair_loop.py`
- Result: 47 passed.

Selected regression gate:

- `python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or final_verdict or retest or repair or score_integrity or failure_bucket or fake or fallback or backend_authored"`
- Result: 20 passed, 99 deselected.

## Over-Routing Risk

The negative controls directly cover existing app, src, component, production, dashboard, route, file path, test file, and repair/fix/update wording. This reduces the risk that generic family terms force real-repo work into disposable artifact mode.

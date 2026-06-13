# Patch 4: Generic Interactive Reliability Feedback

Status: PASS_SUBCHECK

## Changed Files

- `source_proxy/decision/artifact_behavior_contract.py`
- `source_proxy/tests/test_artifact_behavior_contract.py`

## What Changed

- Added a generic visible-state-mutation requirement to behavior contracts for interactive static UI artifacts.
- Expanded broad intent-family coverage for checklist/list, scratchpad notes, day/night theme toggles, weather controls, music/podcast/audio players, and related messy wording.
- Kept truly static mockups unpromoted unless no interaction is requested or inferred.
- Did not add code templates, deterministic app scaffolds, exact prompt branches, or benchmark answer keys.

## Generic Criteria Examples

- Timer/countdown: visible time changes after start.
- Bill/tip/splitter/calculator: entered numbers visibly update result.
- Checklist/list/notes: entered text appears visibly after add/save.
- Theme/toggle/day/night: computed class/color/theme state visibly changes.
- Weather/player/tracker/password/canvas: the primary control visibly changes state or pixels.

## Tests Run

```text
python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_repair_contract.py source_proxy/tests/test_task_spec_intake_unseen_artifacts.py source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or task_spec_intake or fallback or protected"
40 passed, 1 skipped, 97 deselected

python -m py_compile source_proxy/decision/artifact_behavior_contract.py source_proxy/tests/test_artifact_behavior_contract.py
PASS

git diff --check -- source_proxy/decision/artifact_behavior_contract.py source_proxy/tests/test_artifact_behavior_contract.py
PASS
```

## Remaining Risks

- This improves generic contract pressure; it does not guarantee the coder model will produce working behavior.
- The final random-set reruns must prove whether the generic criteria produce at least 8/10 browser-behavior PASS without scaffold/fallback/backend-created content.

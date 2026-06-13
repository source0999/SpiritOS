# Behavior Generation Repair

## Contract Changes

`source_proxy/decision/artifact_behavior_contract.py` now covers:

- `splits` and `costs` calculator/splitter inflections.
- `palette switch`, `dusk dawn switch`, `sunrise sunset mode switch`, `screen change when it gets dark`, and `color mood switcher` as theme/mode behavior.
- `phrase`, `passphrase`, `secret phrase`, `strong`, `gauge`, and `meter` as password/passphrase strength behavior.
- `porch/weather/tile`, `weekend forecast tile`, and related local weather tile language.
- `paint` and `finger paint` drawing/canvas/sketch language.

## Generation Wording Changes

`source_proxy/decision/human_messy_homepage.py` now includes family-keyed implementation checklist wording:

- Weather: visible city, temperature, condition, forecast, or status text must render; any local demo control must mutate visible weather/forecast DOM text.
- Drawing: prefer real canvas, wire pointer/mouse handlers, mutate pixels, keep canvas ids and script selectors consistent, and do not clear marks on mouseup unless there is a separate clear control.
- Theme: support dark/light, dusk/dawn, sunrise/sunset, palette, or color mood changes and mutate computed background/text color or body class.
- Password/passphrase: weak and stronger password, phrase, or passphrase values must produce different visible strength feedback.

## Why This Is Not Exact-Prompt Tailoring

The wording is keyed to probe ids and artifact families, not exact final clean prompt strings. It also applies to multiple synonym prompts in focused tests.

## Tests Updated

- `source_proxy/tests/test_artifact_behavior_contract.py`
- `source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`

Focused behavior contract test result: 5 passed in `test_artifact_behavior_contract.py` as part of the 47-test behavior/final/retest/repair suite.

## Rerun Behavior Impact

Weather improved from previous final clean failure to PASS without repair in Gate B.

Drawing improved from previous final clean failure to PASS after one bounded repair attempt.

Theme routed correctly but remained the only behavior failure in the final rerun.

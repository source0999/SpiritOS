# Source Proxy Human Messy Homepage Phase 1 Report

Date: 2026-06-11

## Scope

Phase 1 only: split the human messy homepage smoke into Product and Pure modes. Product mode is allowed to keep the daily-driver homepage helper, but is explicitly not benchmark eligible. Pure mode removes the homepage target and allowed-file preselection, lets the model choose safe relative paths inside a disposable workspace, and scores GO only when the receipt proves model-chosen path and model-authored content without hidden helper/fallback use.

## Product Mode Smoke

Command used from the Windows mapped-drive shell:

`python scripts\agent-trials\run-source-proxy-human-messy-homepage-smoke.py --run --mode product --prompt "init a repo and make homepage for agent lab expermients"`

Required command shape supported:

`.venv-source-proxy/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --run --mode product --prompt "init a repo and make homepage for agent lab expermients"`

Result: GO for Product mode, not benchmark eligible.

- Run: `product/runs/20260611-224138/`
- `status`: `GO`
- `mode`: `product`
- `benchmark_eligible`: `false`
- `path_selection_mode`: `product_helper`
- `target_path_source`: `system_preselected`
- `allowed_files_source`: `product_helper`
- `product_helper_used`: `true`
- `transparent_default_target_used`: `true`
- `model_chose_target`: `false`
- `system_preselected_target`: `true`
- `files_changed`: `["index.html"]`
- `openable_homepage`: `true`
- `backend_created_content`: `false`
- `file_equals_model_action_content`: `true`

## Pure Mode Smoke

Command used from the Windows mapped-drive shell:

`python scripts\agent-trials\run-source-proxy-human-messy-homepage-smoke.py --run --mode pure --prompt "init a repo and make homepage for agent lab expermients"`

Required command shape supported:

`.venv-source-proxy/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --run --mode pure --prompt "init a repo and make homepage for agent lab expermients"`

Result: NO-GO for Pure mode.

- Run: `pure/runs/20260611-224217/`
- `status`: `NO-GO`
- `mode`: `pure`
- `benchmark_eligible`: `false`
- `path_selection_mode`: `model_chosen`
- `target_path_source`: `model_action`
- `allowed_files_source`: `none`
- `product_helper_used`: `false`
- `transparent_default_target_used`: `false`
- `model_chose_target`: `true`
- `system_preselected_target`: `false`
- `actions_seen`: `1`
- `files_changed`: `["README.md"]`
- `openable_homepage`: `false`
- `fallback_used`: `false`
- `deterministic_scaffold_used`: `false`
- `dummy_fixture_used`: `false`
- `backend_created_content`: `false`
- `file_equals_model_action_content`: `true`
- `real_app_touched`: `false`
- `reason_codes`: `["free_floating_code_no_path_action", "openable_homepage_missing"]`

Interpretation: Pure mode successfully removed the homepage helper and proved model-chosen path/content, but Qwen chose `README.md`, so the output is not an openable homepage and is not benchmark eligible.

## Checks

- Focused pytest: `python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "messy_homepage or human_messy_homepage or tool_action"` -> 18 passed, 1 skipped.
- Stable Vitest thread-pool UI check: not run; Phase 1 touched no UI files.
- `git diff --check`: passed; only LF-to-CRLF working-copy warnings were printed.
- `git status --short --untracked-files=normal`: code changes plus Phase 1 evidence are present; earlier exploratory homepage evidence from `runs/20260611-223358/` remains untracked.

## Phase 1 Verdict

Implementation split: GO.

Product mode smoke: GO, not benchmark eligible.

Pure mode smoke: NO-GO, honestly, because the local model chose a non-openable `README.md` output without helper repair.

Overall benchmark readiness after Phase 1: NO-GO.

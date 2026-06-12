# Source Proxy Orchestrator Correction Phase 3 Generic Artifact Intent Resolver Closeout

## Status

Implementation patch complete.

No provider/model calls, live benchmark prompts, smoke `--run`, real app trial mutations, git branch, worktree, stash, reset, checkout, clean, stage, commit, or push were performed.

## Files Changed

* `source_proxy/decision/task_spec_intake.py`
* `source_proxy/decision/human_messy_homepage.py`
* `source_proxy/tests/test_coding_regression_pack.py`
* `docs/evidence/source-proxy-orchestrator-correction/phase-3-generic-artifact-intent-resolver-closeout.md`

## Root Cause

Product mode had moved away from the homepage-only bridge, but the generic create/artifact resolver was still too narrow. It recognized homepage, Markdown, JSON, and a few small bundle phrases, but common messy prompts such as prototype, static UI demo, dashboard panel, viewer, tracker, portal, or app-like disposable UI could still fall into clarification or over-real-repo interpretation.

That made the proxy less useful than the target architecture: the proxy should infer safe disposable artifact shape without preselecting exact targets or handholding content.

## Implementation Summary

The resolver now uses reusable categories rather than a single prompt phrase:

* create signals: `init`, `initialize`, `make`, `create`, `build`, `new`, `scaffold`, `start`, `draft`
* static UI signals: `page`, `site`, `app`, `demo`, `prototype`, `ui`, `interface`, `dashboard`, `panel`, `viewer`, `tracker`, `portal`, `screen`, `widget`
* document signals: Markdown, README, checklist, notes, guide, document
* JSON/config/example signals

Static UI/prototype/dashboard prompts now map to:

```text
task_kind: create_file_bundle
task_shape: disposable_small_file_bundle
artifact_class: static_ui_artifact
allowed_extensions: .html, .css, .js
max_file_count: 3
target_source: model_authored_required
```

The scorer now treats `static_ui_artifact` as browser-viewable and requires a model-authored HTML target plus openable HTML. It does not accept repo scaffolding or arbitrary source trees as Product output.

## Broad Prompt Classes Now Handled

Manual clean mocked runs in a disposable `/tmp` root verified:

```text
init a simple prototype for trying a layout
create a dashboard panel for tracking status
make a markdown checklist for release verification
create a json config example for local settings
```

All four accepted cases scored `GO`, remained `benchmark_eligible: false`, preserved `backend_created_content: false`, preserved `real_app_touched: false`, and had empty `target_paths` from intake so exact target preselection was avoided.

A static UI scaffold attempt against `package.json` scored:

```text
status: EXPECTED-BLOCKED
artifact_score_kind: expected_blocked
reason_codes: expected_blocked_result, target_not_allowed
files_changed: []
real_app_touched: false
```

## Proof No Single-Prompt Fitting Was Added

The resolver patch adds category-level regexes for generic create and artifact concepts. It does not mention or encode:

* any private/user-specific project
* a music app
* a media player
* `999Playr`
* `Juice WRLD`
* hidden prompt-specific names

The only hits from a source scan were pre-existing older fixtures or the standing homepage regression prompt, not new resolver logic.

## No-Cheat Protections Preserved

Preserved:

* Product exact target preselection remains avoided for generic artifacts.
* Model-authored path/content/action remains required.
* Backend-authored parser input remains rejected.
* Free-floating code without path/action remains rejected.
* Protected paths remain blocked.
* Path traversal remains blocked.
* Wrong extensions remain blocked.
* Static UI repo scaffold files such as `.gitignore`, `package.json`, and lockfiles remain blocked.
* Fake apply prose remains non-executing.
* Product remains `benchmark_eligible: false`.
* Pure diagnostic behavior remains separate.

## Commands Run

```bash
source .venv/bin/activate
command -v python
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake or dashboard or prototype or static"
```

Result:

```text
/home/source/SpiritOS/.venv/bin/python
39 passed, 69 deselected in 11.83s
```

```bash
source .venv/bin/activate
command -v python
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "protected or fake or wrong_file or backend_authored or tool_action"
```

Result:

```text
/home/source/SpiritOS/.venv/bin/python
26 passed, 82 deselected in 9.33s
```

Manual clean mocked run command shape:

```bash
source .venv/bin/activate
python - <<'PY'
# local mocked run_human_messy_homepage checks for prototype, dashboard, markdown, json, and package.json block
PY
```

Manual run root:

```text
/tmp/source-proxy-generic-intent-manual-pcq64lhx
```

Manual result summary:

```text
static_prototype: GO, static_ui_artifact, prototype.html, benchmark_eligible false
dashboard_panel: GO, static_ui_artifact, status-dashboard.html, benchmark_eligible false
markdown_checklist: GO, markdown_document, release-checklist.md, benchmark_eligible false
json_example: GO, json_example, local-settings.json, benchmark_eligible false
static_ui_scaffold_block: EXPECTED-BLOCKED, target_not_allowed, files_changed []
```

Final check commands:

```bash
git diff --check
git status --branch --short --untracked-files=normal
```

`git diff --check` result:

```text

```

The command exited 0 with no output.

`git status --branch --short --untracked-files=normal` result:

```text
## master
 M docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/latest-run.json
 M docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/preview-url.txt
 M scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py
 M source_proxy/decision/human_messy_homepage.py
 M source_proxy/decision/task_spec_intake.py
 M source_proxy/decision/tool_action_executor.py
 M source_proxy/decision/tool_action_loop.py
 M source_proxy/tests/test_coding_regression_pack.py
?? docs/evidence/source-proxy-orchestrator-correction/
?? docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/
?? docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/runs/20260611-223358/
```

## GO/NO-GO For One Live Product Prompt Rerun

GO to request a separate, explicit live Product prompt rerun approval.

NO-GO to run live provider/model verification in this task.

The next live Product rerun must remain disposable-workspace-only, preserve raw transcripts and receipts, avoid real app mutation, and stop on first provenance/no-cheat failure.

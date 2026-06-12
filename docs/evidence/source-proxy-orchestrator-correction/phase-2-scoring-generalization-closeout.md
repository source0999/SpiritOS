# Source Proxy Orchestrator Correction Phase 2 Scoring Generalization Closeout

## Status

Implementation patch complete.

No provider/model calls, live benchmark prompts, smoke `--run`, real app trial mutations, git branch, worktree, stash, reset, checkout, clean, stage, commit, or push were performed.

## Files Changed

* `source_proxy/decision/human_messy_homepage.py`
* `source_proxy/tests/test_coding_regression_pack.py`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-scoring-generalization-closeout.md`

## Scoring Problem Fixed

Before this patch, `score_human_messy_homepage_result()` used homepage-specific success criteria for every Product artifact. That meant a non-homepage Markdown artifact could have a completed Product receipt, model-authored target/content, byte equality proof, no backend-created content, and no real app mutation, but still score `NO-GO` because `openable_homepage_missing`.

That was a scoring bug, not an executor or receipt bug.

## Implementation Summary

The scorer is now artifact-aware:

* `html_static_page` still requires completed execution, model-authored `.html`/`.htm` target, openable HTML, byte equality, no backend content, and no real app mutation.
* `markdown_document` requires completed execution, model-authored `.md` target, touched file, non-empty model-authored content, byte equality, no backend content, and no real app mutation.
* `json_example` requires completed execution, model-authored `.json` target, touched file, parseable JSON content, byte equality, no backend content, and no real app mutation.
* Wrong-extension or wrong-file Product traps with authority errors and no files touched now score as `EXPECTED-BLOCKED`.
* Pure diagnostic scoring remains separate and benchmark eligibility still depends on Pure criteria.

New/reframed score fields:

* `artifact_score_kind`
* `artifact_specific_ok`
* `expected_blocked`
* existing `route_type`, `task_shape`, `artifact_class`, `proxy_exact_target_suggested`, `model_authored_targets`, `files_touched`, `final_state`, `backend_created_content`, `real_app_touched`, and `benchmark_eligible`

## Before/After Behavior

Markdown artifact before:

```text
receipt final_state: completed
model_authored_targets: ["release-checklist.md"]
files_touched: ["release-checklist.md"]
score status: NO-GO
reason: openable_homepage_missing
```

Markdown artifact after:

```text
score status: GO
artifact_score_kind: product_artifact_go
artifact_specific_ok: true
benchmark_eligible: false
openable_homepage: false
backend_created_content: false
real_app_touched: false
```

## Product vs Pure Boundary

Product mode remains daily orchestration:

* Proxy supplies task shape, artifact class, workspace decision, and allowed scope.
* Model must author target, content, and action.
* Product success is not benchmark-pure success.
* `benchmark_eligible` remains false for successful Product artifacts.

Pure mode remains diagnostic:

* No Product artifact helper fields.
* Model chooses target path.
* Benchmark eligibility remains available only through Pure criteria.
* Existing Pure mocked test now asserts `artifact_score_kind = pure_benchmark_go`.

## No-Cheat Protections Preserved

Preserved:

* backend-authored parser input rejection
* model-authored path/content/action requirement
* byte equality proof for changed files
* protected path blocking
* wrong-file and wrong-extension blocking
* fake apply prose not counted as execution
* Product real-app mutation detection
* Product benchmark-ineligible boundary

## Commands Run

```bash
source .venv/bin/activate
command -v python
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake"
```

Result:

```text
/home/source/SpiritOS/.venv/bin/python
36 passed, 69 deselected in 11.65s
```

```bash
source .venv/bin/activate
command -v python
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "protected or fake or wrong_file or backend_authored or tool_action"
```

Result:

```text
/home/source/SpiritOS/.venv/bin/python
26 passed, 79 deselected in 9.36s
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

## GO/NO-GO For Live Provider/Model Verification Approval

GO to prepare or request a separate live provider/model verification approval prompt.

NO-GO to run live provider/model verification in this task.

Live verification remains blocked until Britton explicitly approves it. It must use disposable workspaces, preserve raw transcripts and receipts, avoid real app mutation, and stop on first provenance/no-cheat failure.

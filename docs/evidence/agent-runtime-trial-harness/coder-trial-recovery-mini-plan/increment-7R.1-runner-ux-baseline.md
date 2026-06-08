# Increment 7R.1 - Runner UX Baseline

Date: 2026-06-08

## Dirty State Recorded

`git status --short` at start showed existing dirty work across Source Proxy, coding UI, durable run files, SpiritFlix files, and Gate 5/6/7 evidence/test additions. No reset, stash, clean, delete, commit, or push was run.

`git diff --stat` at start showed 18 tracked files changed with 2413 insertions and 121 deletions. This included `src/components/coding/CodingCockpitShell.tsx`, `source_proxy/api/decision.py`, `source_proxy/tasks/long_running.py`, and dummy Coder prompt/grader files.

`tests/ui-agent-trials/fixtures/dummy-product-site/` was checked with `Test-Path` and was absent.

## Failure Map

The individual LumaCart runner lived as a separate sidebar card above the Trial Runner. The page showed long prompt text, target lists, forbidden lists, and result diagnostics in that separate panel.

`handleRunDummyCoder10Prompt` only called:

```text
/v1/decisions/prompt-packet
```

It did not call:

```text
/v1/verification/diff-preview
/v1/actions/execute-approved
```

That means clicking the selected prompt could make a backend/model attempt but could not apply a returned diff through the normal approval path.

The selected-prompt result state was React-local (`dummyCoderRunState`). It was not backed by the durable run store. The existing Trial Runner reverse/clear path cleared benchmark suite state and receipts, but did not clear the selected-prompt state. This explains the screenshot symptom where "Run cleared from coding cloud" could remain alongside a stale selected-prompt result.

## Backend Failure Cause

Gate 7 task `task_4c1c47be6a30` reached provider/model `openai/gpt-4o-mini` and returned blocked:

```text
reason_code: coder_replacement_content_validation_failed
needed_context: missing exact text: tests/ui-agent-trials/fixtures/dummy-product-site/
selected target: tests/ui-agent-trials/fixtures/dummy-product-site/README.md
```

The UI posted Coder 001 metadata, but `PromptPacketRequest` did not model fields like `selected_prompt_id`, `expected_result_state`, `primary_expected_targets`, or `dummy_coder_10_packet`. The endpoint therefore fell back to normal single-target replacement behavior against `README.md`.

For a create-new-folder task, requiring replacement content to contain the fixture root as exact text was the wrong validation mode.

## Stop Checks

No Coder 002-010, full Coder 10, Coder 25/50/100, commit, push, stash, reset, clean, or manual LumaCart creation occurred during this baseline step.

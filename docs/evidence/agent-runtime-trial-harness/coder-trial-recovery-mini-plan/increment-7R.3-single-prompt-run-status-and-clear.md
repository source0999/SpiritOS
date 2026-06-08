# Increment 7R.3 - Single Prompt Run Status And Clear

Date: 2026-06-08

## Changes

Updated `src/components/coding/CodingCockpitShell.tsx` and focused UI tests.

Selected-prompt state now carries:

- status
- selected prompt id
- task id
- message
- backend status
- error text
- changed files
- grader result
- diagnostics packet

## Visible Run States

The button flow now visibly progresses through:

```text
Starting selected prompt...
Request sent
Running task <id>
Needs fix
Applied / review
Failed
Cleared
```

The run button is disabled while the selected prompt is starting, request-sent, or running. A compact running dot is shown during those states.

Backend/network failures are written into `errorText` and shown in the Trial Runner instead of being swallowed.

## Execution Path

The selected prompt now creates a long-running task first, then calls:

```text
/v1/decisions/prompt-packet
```

If a proposed diff is returned, the runner continues through:

```text
/v1/verification/diff-preview
/v1/actions/execute-approved
```

If the backend blocks or returns no diff, the UI still shows the backend status, reason/grader state, prompt id, and task id.

## Reverse/Clear

The existing `Reverse trial edits and clear results` action now clears:

- benchmark trial results
- selected-prompt result
- selected-prompt diagnostics
- selected-prompt task id
- selected-prompt grader result
- selected-prompt running/error state

If a selected prompt applied files, a `selected-prompt:<prompt-id>:<task-id>` receipt is stored and the same safe reverse path is used.

If no selected-prompt edits were applied, clear still works and shows:

```text
No applied selected-prompt edits to reverse. Results cleared.
```

After clear, copied diagnostics say:

```text
selected_prompt_result: none
selected_prompt_task_id: none
selected_prompt_status: cleared
```

## Follow-Up Preview Placement

After mobile review, the selected-prompt result was moved out of a dense diagnostics block and into a compact trial-style preview row inside the Trial Runner.

The selected-prompt preview now shows:

- prompt title
- trial result badge
- task id
- backend status
- grader result
- changed paths, when present
- verification, when present
- target-root copy action

The same `Reverse trial edits and clear results` button is shown directly below that selected-prompt preview when a selected-prompt result exists. No separate reverse button was added.

## Tests

Added focused frontend tests for:

- immediate pending/running task state
- run button disabled while pending
- selected-prompt blocked result clear
- diagnostics after clear reporting no active selected-prompt result

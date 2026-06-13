# Repair Loop Upgrade

## Data Now Included

`source_proxy/decision/artifact_repair_contract.py` now includes these structured fields for browser behavior failures when available:

- `artifact_family`
- `original_prompt`
- `selected_preview_path`
- `allowed_files`
- `failed_probe_id`
- `expected_behavior`
- `primary_failure_bucket`
- `observed_before`
- `observed_after`
- `observed_interaction`
- `why_this_failed`
- `current_files_summary`
- `required_repair`
- `required_output_format`

## Output Contract

The repair prompt requires exactly one path-bound format:

- Source Proxy `WriteFile` JSON action, or
- `<file path="RELATIVE_ALLOWED_FILE">...</file>` block.

It explicitly forbids:

- free-floating code
- prose-only advice
- modifying unlisted files
- backend-authored rescue content
- scorer changes
- fallback scaffolds
- shell commands
- network/provider calls
- package files/CDNs/background workers

## Wrong-File And Selector Mismatch Handling

The prompt now states:

If you change an element id, class, script selector, linked script, or linked stylesheet, update every loaded file that depends on it.

This does not make the backend rescue the artifact. It gives the local model enough failure delta to avoid repairs like changing a canvas id without updating the script selector.

## Bounded Repair Status

Repair remains one-attempt bounded through `max_attempts_hint: 1` and the existing `run_limited_artifact_repair_loop()`.

## Rerun Impact

Two repair attempts were used in the final clean 10 rerun:

- `make a dusk dawn palette switch`: repair wrote `styles.css`, but behavior still failed.
- `make a finger paint doodle pad`: repair wrote `index.html`, and final browser probe passed.

This is not backend rescue: repaired file contents were model-authored and path-bound, with `file_equals_model_action_content: true`.

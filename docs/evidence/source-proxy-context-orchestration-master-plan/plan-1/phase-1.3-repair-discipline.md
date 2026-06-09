# Plan 1 Phase 1.3 - One-Pass Repair Discipline

Status: GO

## Increment 1.3.1 - One allowed formatting repair pass

Change:

- Coder structured-output format attempts are capped at two total calls: the initial response plus one repair prompt.
- The previous three-attempt loop was removed for parser/schema repair.

Check:

Existing and updated tests assert `json_attempt_count == 2` for repeated malformed output.

Result:

`source_proxy/tests/test_coder_agent_repomix_diff.py` passed.

Decision: GO.

## Increment 1.3.2 - Failed repair remains blocked

Evidence:

- `test_three_invalid_attempts_returns_blocked` now proves two total attempts and blocked status.
- `test_prose_response_returns_coder_response_not_json` proves prose stays blocked with no proposed diff.
- `test_content_lines_rejects_non_string_entries` proves schema-invalid content remains blocked.

Result:

All focused tests passed.

Decision: GO.

## Increment 1.3.3 - Repair diagnostics in durable run receipt

Diagnostics retained in `coder_diagnostics`:

- `json_attempt_count`
- `coder_format_retry_count`
- `parser_repair_used`
- `parse_error_class`
- `parse_error_message`
- `last_json_error`
- `structured_output_mode`
- `file_block_repair_source`
- `json_repair_source`

The full coder payload path still merges these fields through `_merge_coder_response_diagnostics`.

Decision: GO.

## Phase Closeout

Phase 1.3 GO. Parser repair is bounded, visible, and cannot become a hidden retry loop.


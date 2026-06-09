# Plan 1 Phase 1.1 - Strict File-Block Output Contract

Status: GO

## Increment 1.1.1 - Allowed file-block syntax and path rules

Contract:

- Preferred single-file syntax is exactly one XML block:
  `<file path="REPO_RELATIVE_PATH"> ... </file>`
- Alternate single-file syntax is exactly one delimiter block:
  `<<<FILE: REPO_RELATIVE_PATH` followed by full replacement content and a closing `>>>` line.
- Legacy JSON `replace_file` remains accepted only as a fallback for existing callers.
- Paths must be repo-relative, normalized to POSIX separators, non-empty, not absolute, not Windows drive paths, and must not contain `..` traversal.
- The parsed target must match the Architect packet target; otherwise the output is treated as out-of-scope.

Changed files:

- `source_proxy/tasks/long_running.py`
- `source_proxy/tests/test_coder_agent_repomix_diff.py`

Check:

`cd ~/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coder_agent_repomix_diff.py`

Result:

`56 passed in 9.46s`

Decision: GO.

Next permitted increment: 1.1.2.

## Increment 1.1.2 - Markdown fence ban

Contract:

- Any coder response containing a markdown fence marker is rejected before XML, delimiter, or JSON recovery.
- The diagnostic is `markdown_fence_found`.
- Fenced JSON is no longer accepted for coder replacement output.

Check:

Focused test included in `test_markdown_fenced_output_is_rejected`.

Result:

`source_proxy/tests/test_coder_agent_repomix_diff.py` passed with the markdown fence rejection test included.

Decision: GO.

Next permitted increment: 1.1.3.

## Increment 1.1.3 - Non-empty payload required

Contract:

- Empty file-block content is rejected as `empty_diff`.
- Empty backend-generated diffs still block unless the target is already satisfied by exact disk content.

Check:

Focused tests included:

- `test_empty_file_block_content_is_rejected_as_empty_diff`
- existing backend empty-diff regression tests

Result:

`source_proxy/tests/test_coder_agent_repomix_diff.py` passed.

Decision: GO.

## Phase Closeout

Phase 1.1 GO. The output contract is explicit, parser-backed, and covered by focused tests. Freeform markdown cannot pass as a patch.


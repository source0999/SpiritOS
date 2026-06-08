# Increment 3.5 - Model Output Contract

Status: passed for focused Gate 3 paths.

Added model output contract values:
- `model_unified_diff`
- `model_structured_file_edit`
- `model_markdown_code_block`
- `model_full_file_content`
- `model_prose_only`
- `model_empty_response`
- `model_malformed_output`
- `model_wrong_file`
- `model_protected_path_attempt`
- `scaffold_blocked`
- `fallback_blocked`
- `unknown_untrusted`

Behavior:
- Valid replacement JSON is classified as `model_structured_file_edit`.
- Raw unified diff is recognized as `model_unified_diff` but remains wrong-format for this route.
- Markdown/code fences are classified as `model_markdown_code_block`.
- Existing-file prose-only output is classified as `model_prose_only` and blocked.
- Scaffold/fallback paths are classified as `scaffold_blocked` or `fallback_blocked`.

Tests:
- Focused Coder contract tests passed.
- Python compile passed.
- Typecheck passed.

Manual/self-check:
- Empty/prose/malformed outputs cannot become PASS.
- Wrong/protected paths remain blocked by existing TaskSpec/path safety checks.
- Parser conversion remains labeled and model-authored; backend scaffold content is not allowed to pass in live trial mode.

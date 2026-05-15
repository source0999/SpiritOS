ARPA: Implement Phase 4D Coder Output Reliability. Analyze first, patch in small increments, and do not touch Scout.

Goal:
Make the local Coder boring and reliable at returning valid structured edit output.

Current state:
The `/coding` workflow is now safe and structured:
- TaskSpec exists and is visible.
- TaskSpec.allowed_files is enforced.
- Wrong-file diffs block.
- No-target prompts block before Coder.
- Diff preview works.
- Approval gate works.
- Protected apply works.
- Docs-only verification works.
- Code-file post-apply verification exists.

Current bottleneck:
Coder sometimes fails before diff generation because its response does not match the strict replacement JSON contract.

Observed failures:
- `coder_response_not_json`
- `coder_replacement_content_validation_failed`
- local model returns prose, malformed JSON, or a huge escaped code string with bad escaping
- live UI blocks safely, but no approvable diff is produced

Open-source reference lessons:
- Aider explicitly notes that LLMs are bad at returning code in JSON and uses different edit formats per model, including whole-file, search/replace, udiff, and architect/editor modes.
- Cline reinforces Plan/Act separation and approval checkpoints.
- OpenHands uses modular tool/workspace boundaries and post-processing for malformed output.
- SWE-agent/SWE-Edit style loops use observe → edit → check → retry with exact error feedback.
- Consensus: one giant escaped JSON string is fragile for code. Prefer `content_lines: string[]` or structured edit blocks, include the schema verbatim, repair/extract JSON when possible, and retry with exact parser errors.

We keep:
- TaskSpec
- approval gate
- protected apply
- verification
- no auto-apply
- no Scout integration

Scope:
Phase 4D only.

Do not touch:
- scout/*
- Scout dashboard
- Scout APIs
- Scout integration
- promotion/review workflow
- approval gate bypasses
- protected execution logic
- broad UI redesign
- arbitrary command execution

Do not weaken:
- TaskSpec.allowed_files enforcement
- target-only verification
- git apply checks
- reviewer checks
- post-apply verification

Files to inspect:
- source_proxy/tasks/long_running.py
- source_proxy/api/decision.py
- source_proxy/decision/prompt_packet.py
- source_proxy/planning/plan.py
- source_proxy/tests/test_coder_agent_repomix_diff.py
- source_proxy/tests/test_coding_regression_pack.py
- source_proxy/tests/test_long_running_tasks.py
- source_proxy/tests/test_deterministic_markdown_append.py
- src/components/coding/CodingAgentInterface.tsx
- src/components/coding/__tests__/coding-workflow-step.test.ts

Increment 1: Add content_lines support

Current strict output likely expects something like:

```json
{
  "action": "replace_file",
  "target": "src/lib/coding/unified-diff-paths.ts",
  "content": "full file as one escaped string"
}







Add support for:

{
  "action": "replace_file",
  "target": "src/lib/coding/unified-diff-paths.ts",
  "content_lines": [
    "import { normalizeRepoRelativePath } from \"@/lib/coding/explicit-task-target\";",
    "",
    "/**",
    " * Supports both git-style diffs and standard unified diffs.",
    " */"
  ]
}

Backend behavior:

If content_lines exists and is a list of strings, join with \n.
Treat joined content exactly like existing replacement content.
Run the same diff generation, TaskSpec allowed-file check, git apply, TypeScript parser, requirement coverage, and reviewer pipeline.
Keep old content string support for backward compatibility.
If both content and content_lines exist, prefer content_lines unless that conflicts with existing safe behavior.
Reject non-string entries in content_lines.
Do not allow target outside TaskSpec.allowed_files.

Tests:

parse valid content_lines
reject non-string content_lines
preserve old content behavior
content_lines replacement produces same diff path and safety checks

Increment 2: Make the Coder prompt schema explicit

Update the Coder system/prompt text to include the full expected schema verbatim.

Prompt should say:

Return only JSON.
No prose.
No markdown fences unless the parser explicitly supports fenced JSON.
Prefer content_lines.
Every line of the replacement file must be one string in content_lines.
Do not include a unified diff unless explicitly asked.
Target must exactly match TaskSpec.target.
Only edit files in TaskSpec.allowed_files.

Include schema:

{
  "action": "replace_file",
  "target": "REPO_RELATIVE_PATH",
  "content_lines": ["line 1", "line 2"]
}

Also include the legacy accepted schema:

{
  "action": "replace_file",
  "target": "REPO_RELATIVE_PATH",
  "content": "FULL_FILE_CONTENT"
}

But tell the Coder to prefer content_lines.

Tests:

Prompt text contains content_lines.
Prompt text includes TaskSpec target / allowed_files.
Prompt text says return only JSON.

Increment 3: Add JSON extraction and light repair

On strict parse failure:

Try raw JSON parse.
Try extracting whole ```json fenced content.
Try stripping non-JSON prose before first { and after last }.
Try a conservative repair for common model mistakes if easy:
smart quotes to normal quotes
trailing commas
markdown fence wrappers
accidental leading text

Do not overbuild a fragile parser.
Do not accept partial/malformed content if it cannot become a valid object.

If a JSON-looking object is recovered, validate normally against the schema and TaskSpec.

If the model returns a unified diff instead of JSON:

Do not automatically apply it.
Either:
block with coder_response_wrong_format_unified_diff, or
retry with explicit feedback: “You returned a diff, but this route requires JSON with content_lines.”
For Phase 4D, prefer retry over conversion unless there is already a safe conversion path.

Tests:

prose-wrapped JSON is recovered
fenced JSON is recovered
trailing prose after JSON is ignored
markdown fence around JSON is accepted
unified diff response does not become approval-ready unless converted through an existing safe path
unrecoverable malformed output blocks safely

Increment 4: Add bounded JSON repair retry loop

Current retry behavior may exist, but it is not visible enough and not focused enough.

Add or tighten a bounded retry loop for malformed Coder output:

max 2 or 3 JSON/output-format attempts
keep same TaskSpec
keep same allowed_files
never write files during retry
feed exact parser/schema error back into the retry prompt
if the same failure repeats, stop early
final state remains blocked with no approval-ready state

Track separately from reviewer retry:

json_attempt_count
coder_format_retry_count
last_json_error
raw_response_excerpt

Do not confuse this with reviewer retry count.

Expected statuses/reason codes:

coder_response_not_json
coder_response_wrong_format_unified_diff
coder_replacement_content_validation_failed
coder_response_repair_exhausted

Tests:

malformed JSON retries once and succeeds
malformed JSON retries and then blocks after max attempts
same failure signature stops safely
retry preserves TaskSpec.allowed_files
no approval-ready state on exhausted retry

Increment 5: Persist raw Coder response excerpt

Diagnostics found that raw_response_excerpt exists but is not always populated.

Patch:

On every Coder parse/schema failure, persist:
first 1000-2000 chars of raw output
parse error class
parse error message
json_attempt_count
coder_format_retry_count
Surface in blocked payload / long-running task state / prompt-packet response where already appropriate.
UI may show this under Advanced only.
Do not expose huge raw model output in primary UI.

Tests:

coder_response_not_json includes raw_response_excerpt
parse error metadata appears in blocked response
raw excerpt truncates safely

Increment 6: Keep old flows green

Existing behavior must still pass:

docs-only edit workflow
code-file edit workflow
TaskSpec allowed_files enforcement
wrong-file blocking
no-target blocking
approved apply
docs verification
code verification
frontend regression pack

Suggested new tests:

source_proxy/tests/test_coder_agent_repomix_diff.py
source_proxy/tests/test_coding_regression_pack.py
source_proxy/tests/test_long_running_tasks.py

Add tests for:

content_lines accepted and joined.
old content accepted.
malformed JSON repaired from prose wrapper.
fenced JSON accepted.
unified diff response causes retry/block, not approval.
raw_response_excerpt persists.
json_attempt_count tracked.
TaskSpec.allowed_files preserved through retries.
successful retry reaches preview_ready.
exhausted retry returns structured blocked response.

Validation commands:

cd /home/source/SpiritOS

PYTHONPATH=. python -m pytest -q \
  source_proxy/tests/test_coder_agent_repomix_diff.py \
  source_proxy/tests/test_coding_regression_pack.py \
  source_proxy/tests/test_long_running_tasks.py \
  source_proxy/tests/test_deterministic_markdown_append.py

npm run test:coding-frontend-regression

npx tsc --noEmit -p tsconfig.json

Manual smoke after patch:
Use /coding task:

Target file: src/lib/coding/unified-diff-paths.ts

Add a short comment above collectPathsFromUnifiedDiff explaining that it supports both git-style diffs and standard unified diffs. Do not change runtime behavior. Do not edit any other file.

Expected:

Target resolves correctly.
TaskSpec visible and enforced.
Coder returns valid output or is repaired/retried.
Diff preview appears.
TaskSpec allowed-files passes.
Git apply passes.
TypeScript passes.
Requirement coverage passes.
Reviewer passes.
Approval gate reaches human approval.
No file applies without approval.

Deliverable:
Return concise report:

Files changed
content_lines support added
Coder prompt schema changes
JSON extraction/repair behavior
bounded retry behavior
raw response excerpt behavior
tests added/updated
test results
confirm:
no Scout files touched
no auto-apply added
approval gate not weakened
TaskSpec.allowed_files remains enforced
old content string support remains